from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, current_app
from sqlalchemy import or_
from datetime import datetime

from models import db, User, Project, Registration, VolunteerRecord
from forms import parse_login_form, parse_register_form

bp = Blueprint('main', __name__)

# Routes
@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        form = parse_login_form(request)
        user = User.query.filter(
            User.user_type == form.user_type,
            or_(User.username == form.username_or_email, User.email == form.username_or_email)
        ).first()

        if user and user.check_password(form.password):
            session['user_id'] = user.id
            session['user_type'] = user.user_type
            session['username'] = user.username
            
            if user.user_type == 'participant':
                return redirect(url_for('main.participant_dashboard'))
            elif user.user_type == 'organization':
                return redirect(url_for('main.organization_dashboard'))
            elif user.user_type == 'admin':
                return redirect(url_for('main.admin_panel'))
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
            user = User(username=form.username, email=form.email, user_type=form.user_type)
            user.set_password(form.password)
            db.session.add(user)
            db.session.commit()
            current_app.logger.info(f"Register success: id={user.id}, username={user.username}, type={user.user_type}")
        except Exception as e:
            current_app.logger.exception("Register failed")
            db.session.rollback()
            return render_template('login.html', error=f'Register failed: {str(e)}')
        
        return redirect(url_for('main.login'))
    
    return render_template('login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))

@bp.route('/participant/dashboard')
def participant_dashboard():
    if 'user_id' not in session or session.get('user_type') != 'participant':
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    return render_template('participant_dashboard.html', user=user)

@bp.route('/organization/dashboard')
def organization_dashboard():
    if 'user_id' not in session or session.get('user_type') != 'organization':
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    return render_template('organization_dashboard.html', user=user)

@bp.route('/admin/panel')
def admin_panel():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    return render_template('admin_panel.html', user=user)

@bp.route('/project/<int:project_id>')
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    # Get organization info
    organization = User.query.get(project.organization_id)
    # Get registration count
    registration_count = Registration.query.filter_by(project_id=project.id).count()
    # Get comments/registrations for display
    registrations = Registration.query.filter_by(project_id=project.id).limit(5).all()
    
    return render_template('project_detail.html', 
                         project=project, 
                         organization=organization,
                         registration_count=registration_count,
                         registrations=registrations)

@bp.route('/demo/project')
def demo_project_detail():
    """Demo route showing project detail page with mock data"""
    from datetime import date, timedelta
    
    # Create mock data
    # Create a mock project object with all required attributes
    class MockProject:
        def __init__(self):
            self.id = 1
            self.title = 'Community Waste Sorting Campaign'
            self.description = 'This activity aims to raise community residents\' environmental awareness and promote waste sorting knowledge. Volunteers will help residents understand the importance and correct methods of waste sorting through distributing brochures, on-site explanations, and interactive games. The activity will cover multiple communities, contributing to building a beautiful home.'
            self.category = 'Environmental'
            self.date = date(2025, 11, 15)
            self.location = 'Sunshine Community Activity Center'
            self.max_participants = 20
            self.duration = 4.0
            self.points = 80
            self.rating = 4.8
            self.status = 'approved'
            self.requirements = 'Love environmental protection, have good communication skills, and be able to participate in the entire activity'
    
    mock_project = MockProject()
    
    # Create a mock organization object
    class MockOrganization:
        def __init__(self):
            self.username = 'Green Earth Environmental'
            self.description = 'Dedicated to environmental advocacy and practice, has conducted over 100 environmental activities'
    
    mock_organization = MockOrganization()
    
    # Mock registration data
    mock_registration_count = 15
    mock_comments = [
        {
            'user_name': 'Emma Wilson',
            'user_type': 'Participant',
            'comment': 'Very meaningful activity, looking forward to participating! Do I need to bring my own promotional materials?',
            'created_at': '2025-11-03 10:30',
            'reply': 'The organization will provide brochures and other materials. Just arrive on time.'
        },
        {
            'user_name': 'Michael Chen',
            'user_type': 'Participant',
            'comment': 'Participated in similar activities before, learned a lot. How long will this activity last?',
            'created_at': '2025-11-02 15:20',
            'reply': 'The activity is expected to last 4 hours, from 9:00 AM to 1:00 PM.'
        }
    ]
    
    return render_template('project_detail.html',
                         project=mock_project,
                         organization=mock_organization,
                         registration_count=mock_registration_count,
                         comments=mock_comments,
                         is_demo=True)

@bp.route('/volunteer-record')
def volunteer_record():
    if 'user_id' not in session or session.get('user_type') != 'participant':
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    records = VolunteerRecord.query.filter_by(user_id=user.id).all()
    return render_template('volunteer_record.html', user=user, records=records)

# API Routes for AJAX calls
@bp.route('/api/projects')
def api_projects():
    projects = Project.query.filter_by(status='approved').all()
    return jsonify([{
        'id': p.id,
        'title': p.title,
        'category': p.category,
        'date': p.date.strftime('%Y-%m-%d'),
        'location': p.location,
        'rating': p.rating,
        'max_participants': p.max_participants
    } for p in projects])

@bp.route('/api/register-project', methods=['POST'])
def api_register_project():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    registration = Registration(
        user_id=session['user_id'],
        project_id=data['project_id']
    )
    db.session.add(registration)
    db.session.commit()
    
    return jsonify({'success': True})

# Development-only: list users to help debug login issues
@bp.route('/dev/users')
def dev_users():
    if not current_app.debug and current_app.config.get('ENV') != 'development':
        return jsonify({'error': 'Not available'}), 403
    q = User.query
    user_type = request.args.get('user_type')
    if user_type:
        q = q.filter(User.user_type == user_type.strip().lower())
    users = q.order_by(User.id.desc()).limit(100).all()
    return jsonify([
        {
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'user_type': u.user_type,
            'created_at': u.created_at.isoformat() if u.created_at else None
        } for u in users
    ])
