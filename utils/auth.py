"""Authentication routes (login, register, logout).

This blueprint handles:
- Rendering combined login / register page
- WTForms-based server-side validation
- Account creation for participant / organization users
- Session management via Flask-Login
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, make_response, current_app
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_

from models import db, User
from forms import LoginForm, RegisterForm

bp = Blueprint('auth', __name__)


def _format_form_errors(form) -> str:
    if not form.errors:
        return 'Invalid input. Please check your entries.'
    parts = []
    for field, messages in form.errors.items():
        label = getattr(form, field).label.text if hasattr(form, field) else field
        parts.append(f"{label}: {', '.join(messages)}")
    return '; '.join(parts)


def _render_login_template(**context):
    defaults = {'error': None, 'form_errors': None, 'initial_tab': 'login'}
    defaults.update(context)
    return render_template('login.html', **defaults)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        form = LoginForm(request.form)
        if not form.validate():
            current_app.logger.warning("Login validation failed: %s", form.errors)
            return _render_login_template(
                error=_format_form_errors(form),
                form_errors=form.errors,
            )

        identifier = form.username.data or ''
        user_type = (form.user_type.data or '').lower()
        user = User.query.filter(
            User.user_type == user_type,
            or_(User.username == identifier, User.email == identifier)
        ).first()

        if user and user.check_password(form.password.data or ''):
            # Check if user is banned/disabled
            if hasattr(user, 'is_active') and not user.is_active:
                # Check if temporary ban has expired
                if hasattr(user, 'ban_until') and user.ban_until:
                    from datetime import datetime
                    if datetime.utcnow() >= user.ban_until:
                        # Ban expired, reactivate user
                        user.is_active = True
                        user.ban_reason = None
                        user.ban_until = None
                        db.session.commit()
                    else:
                        # Still banned, show remaining time
                        remaining = user.ban_until - datetime.utcnow()
                        days = remaining.days
                        hours = remaining.seconds // 3600
                        reason = user.ban_reason or 'No reason provided'
                        if days > 0:
                            time_str = f'{days} day(s) and {hours} hour(s)'
                        else:
                            time_str = f'{hours} hour(s)'
                        return _render_login_template(
                            error=f'Your account is temporarily suspended. Reason: {reason}. Time remaining: {time_str}'
                        )
                else:
                    # Permanent ban
                    reason = getattr(user, 'ban_reason', None) or 'No reason provided'
                    return _render_login_template(
                        error=f'Your account has been permanently disabled. Reason: {reason}. Please contact an administrator.'
                    )
            
            # Use Flask-Login to log in the user
            login_user(user, remember=bool(form.remember.data))

            # Ensure we don't persist the session unless the user requested it
            session.permanent = False
            if not form.remember.data:
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
            current_app.logger.warning(
                "Login failed: invalid credentials identifier=%s user_type=%s",
                form.username.data,
                form.user_type.data,
            )
            return _render_login_template(error='Invalid credentials')
    
    return _render_login_template()


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        form = RegisterForm(request.form)
        if not form.validate():
            current_app.logger.warning("Register validation failed: %s", form.errors)
            return _render_login_template(
                error=_format_form_errors(form),
                form_errors=form.errors,
                initial_tab='register',
            )

        current_app.logger.info(
            "Register POST received: user_type=%s, username=%s, email=%s",
            form.user_type.data,
            form.username.data,
            form.email.data,
        )

        # Validate user_type
        user_type = (form.user_type.data or '').lower()
        if user_type not in ('participant', 'organization'):
            current_app.logger.warning("Register failed: invalid user_type=%s", user_type)
            return _render_login_template(error='Invalid user type', initial_tab='register')
        
        # Check if user already exists
        if User.query.filter_by(username=form.username.data).first():
            current_app.logger.warning("Register failed: username exists username=%s", form.username.data)
            return _render_login_template(error='Username already exists', initial_tab='register')
        
        if User.query.filter_by(email=form.email.data).first():
            current_app.logger.warning("Register failed: email exists email=%s", form.email.data)
            return _render_login_template(error='Email already exists', initial_tab='register')
        
        # Create new user
        try:
            user = User()
            user.username = form.username.data
            user.email = form.email.data
            user.user_type = user_type
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            current_app.logger.info(f"Register success: id={user.id}, username={user.username}, type={user.user_type}")
        except Exception as e:
            current_app.logger.exception("Register failed")
            db.session.rollback()
            return render_template('login.html', error=f'Register failed: {str(e)}', initial_tab='register')
        
        return redirect(url_for('auth.login'))
    
    return _render_login_template(initial_tab='register')


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



