"""Authentication routes (login, register, logout)."""
from flask import Blueprint, render_template, request, redirect, url_for, session, make_response, current_app
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_

from models import db, User
from forms import parse_login_form, parse_register_form

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        form = parse_login_form(request)
        user = User.query.filter(
            User.user_type == form.user_type,
            or_(User.username == form.username_or_email, User.email == form.username_or_email)
        ).first()

        if user and user.check_password(form.password):
            # Check if user is active
            if hasattr(user, 'is_active') and not user.is_active:
                return render_template('login.html', error='Your account has been disabled. Please contact an administrator.')
            
            # Use Flask-Login to log in the user
            login_user(user, remember=form.remember)

            # Ensure we don't persist the session unless the user requested it
            session.permanent = False
            if not form.remember:
                session['_remember'] = 'clear'
                session.pop('_remember_seconds', None)
            
            # Keep session data for backward compatibility
            session['user_type'] = user.user_type
            session['username'] = user.username
            
            if user.user_type == 'participant':
                return redirect(url_for('views.participant_dashboard'))
            elif user.user_type == 'organization':
                return redirect(url_for('views.organization_dashboard'))
            elif user.user_type == 'admin':
                return redirect(url_for('views.admin_panel'))
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        form = parse_register_form(request)
        current_app.logger.info(f"Register POST received: user_type={form.user_type}, username={form.username}, email={form.email}")

        # Validate user_type
        if form.user_type not in ('participant', 'organization'):
            return render_template('login.html', error='Invalid user type')
        
        # Check if user already exists
        if User.query.filter_by(username=form.username).first():
            return render_template('login.html', error='Username already exists')
        
        if User.query.filter_by(email=form.email).first():
            return render_template('login.html', error='Email already exists')
        
        # Create new user
        try:
            user = User()
            user.set_password(form.password)
            db.session.add(user)
            db.session.commit()
            current_app.logger.info(f"Register success: id={user.id}, username={user.username}, type={user.user_type}")
        except Exception as e:
            current_app.logger.exception("Register failed")
            db.session.rollback()
            return render_template('login.html', error=f'Register failed: {str(e)}')
        
        return redirect(url_for('auth.login'))
    
    return render_template('login.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    # Ensure remember-me cookies/session flags are cleared
    session.pop('_remember', None)
    session.pop('_remember_seconds', None)
    session.clear()
    
    response = make_response(redirect(url_for('views.index')))
    remember_cookie_name = current_app.config.get('REMEMBER_COOKIE_NAME', 'remember_token')
    response.delete_cookie(remember_cookie_name)
    return response


