from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, current_app, send_file
from sqlalchemy import or_
from datetime import datetime, timedelta
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill

from models import db, User, Project, Registration, VolunteerRecord, Badge, UserBadge
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
    # Get registration count (only active registrations)
    active_statuses = ('registered', 'approved')
    registration_count = Registration.query.filter(
        Registration.project_id == project.id,
        Registration.status.in_(active_statuses)
    ).count()
    # Get comments/registrations for display
    registrations = Registration.query.filter_by(project_id=project.id).limit(5).all()
    
    # Check if current user is registered
    is_registered = False
    if 'user_id' in session:
        existing_reg = Registration.query.filter(
            Registration.user_id == session['user_id'],
            Registration.project_id == project.id,
            Registration.status.in_(active_statuses + ('completed',))
        ).first()
        is_registered = existing_reg is not None
    
    return render_template('project_detail.html', 
                         project=project, 
                         organization=organization,
                         registration_count=registration_count,
                         registrations=registrations,
                         is_registered=is_registered)

@bp.route('/demo/project')
def demo_project_detail():
    """Demo route showing project detail page with seeded database data."""
    project = Project.query.filter_by(status='approved').order_by(Project.date.asc()).first()
    if not project:
        return redirect(url_for('main.index'))

    organization = User.query.get(project.organization_id)
    registration_count = Registration.query.filter(
        Registration.project_id == project.id,
        Registration.status != 'cancelled'
    ).count()
    registrations = Registration.query.filter_by(project_id=project.id)\
        .order_by(Registration.created_at.desc())\
        .limit(5)\
        .all()

    comments = []
    for registration in registrations:
        participant = registration.user
        comments.append({
            'user_name': participant.display_name or participant.username,
            'user_type': participant.user_type.title(),
            'comment': f"Looking forward to {project.title}!",
            'created_at': registration.created_at.strftime('%Y-%m-%d %H:%M'),
            'reply': None
        })

    return render_template(
        'project_detail.html',
        project=project,
        organization=organization,
        registration_count=registration_count,
        comments=comments,
        is_demo=True
    )

@bp.route('/volunteer-record')
def volunteer_record():
    if 'user_id' not in session or session.get('user_type') != 'participant':
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    records = VolunteerRecord.query.filter_by(user_id=user.id).order_by(VolunteerRecord.completed_at.desc()).all()
    
    # Calculate statistics
    total_hours = sum(r.hours for r in records if r.status == 'approved')
    total_points = sum(r.points for r in records if r.status == 'approved')
    completed_count = len([r for r in records if r.status == 'approved'])
    
    # Prepare records data with project and organization info
    records_data = []
    years_set = set()
    categories_set = set()
    
    for record in records:
        project = record.project
        organization = project.organization if project else None
        
        # Collect years and categories for filters
        if record.completed_at:
            years_set.add(record.completed_at.year)
        if project and project.category:
            categories_set.add(project.category)
        
        records_data.append({
            'record': {
                'id': record.id,
                'hours': record.hours,
                'points': record.points,
                'status': record.status,
                'completed_at': record.completed_at.strftime('%Y-%m-%d') if record.completed_at else None
            },
            'project': {
                'id': project.id if project else None,
                'title': project.title if project else 'Unknown Project',
                'category': project.category if project else None
            } if project else None,
            'organization': {
                'display_name': organization.display_name if organization else None,
                'username': organization.username if organization else None
            } if organization else None
        })
    
    return render_template('volunteer_record.html', 
                         user=user, 
                         records_data=records_data,
                         total_hours=total_hours,
                         total_points=total_points,
                         completed_count=completed_count,
                         available_years=sorted(years_set, reverse=True),
                         available_categories=sorted(categories_set))


def _generate_excel_from_records(records, filename_prefix="volunteer_records", user_display_name=None):
    """Helper function to generate Excel file from VolunteerRecord list."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Volunteer Records"
    
    # Header row
    headers = ['Project Name', 'Category', 'Organization', 'Date', 'Certified Hours', 'Points Earned', 'Status']
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # Data rows
    for row_idx, record in enumerate(records, start=2):
        project = record.project
        organization = project.organization if project else None
        
        ws.cell(row=row_idx, column=1, value=project.title if project else 'Unknown Project')
        ws.cell(row=row_idx, column=2, value=project.category if project else 'N/A')
        ws.cell(row=row_idx, column=3, value=organization.display_name or organization.username if organization else 'Unknown Organization')
        ws.cell(row=row_idx, column=4, value=record.completed_at.strftime('%Y-%m-%d') if record.completed_at else 'N/A')
        ws.cell(row=row_idx, column=5, value=record.hours)
        ws.cell(row=row_idx, column=6, value=record.points)
        
        # Status mapping
        status_display = {
            'approved': 'Certified',
            'pending': 'Pending',
            'rejected': 'Rejected'
        }
        ws.cell(row=row_idx, column=7, value=status_display.get(record.status, record.status))
    
    # Auto-adjust column widths
    column_widths = [30, 15, 25, 12, 15, 15, 12]
    for col_idx, width in enumerate(column_widths, start=1):
        ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = width
    
    # Save to BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    # Generate filename with user display_name at the front
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if user_display_name:
        # Sanitize display_name for filename (remove invalid characters)
        safe_name = "".join(c for c in user_display_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        filename = f"{safe_name}_{filename_prefix}_{timestamp}.xlsx"
    else:
        filename = f"{filename_prefix}_{timestamp}.xlsx"
    
    return output, filename


@bp.route('/api/participant/export-all-records')
def api_export_all_records():
    """Export all volunteer records for the current participant."""
    if 'user_id' not in session or session.get('user_type') != 'participant':
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get all records
    records = VolunteerRecord.query.filter_by(user_id=user.id).order_by(VolunteerRecord.completed_at.desc()).all()
    
    # Get user display_name (fallback to username if not set)
    user_display_name = user.display_name or user.username
    
    output, filename = _generate_excel_from_records(records, "all_volunteer_records", user_display_name)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


@bp.route('/api/participant/export-filtered-records', methods=['POST'])
def api_export_filtered_records():
    """Export filtered volunteer records for the current participant."""
    if 'user_id' not in session or session.get('user_type') != 'participant':
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    year_filter = data.get('year')
    category_filter = data.get('category')
    
    # Get all records
    records = VolunteerRecord.query.filter_by(user_id=user.id).order_by(VolunteerRecord.completed_at.desc()).all()
    
    # Apply filters
    filtered_records = []
    for record in records:
        # Year filter
        if year_filter:
            if not record.completed_at or record.completed_at.year != int(year_filter):
                continue
        
        # Category filter
        if category_filter:
            if not record.project or record.project.category != category_filter:
                continue
        
        filtered_records.append(record)
    
    # Get user display_name (fallback to username if not set)
    user_display_name = user.display_name or user.username
    
    output, filename = _generate_excel_from_records(filtered_records, "filtered_volunteer_records", user_display_name)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

# API Routes for AJAX calls
@bp.route('/api/projects')
def api_projects():
    """Get all approved projects (for homepage, exclude expired projects)."""
    today = datetime.utcnow().date()
    projects = Project.query.filter_by(status='approved').filter(Project.date >= today).order_by(Project.date.asc()).all()
    return jsonify([{
        'id': p.id,
        'title': p.title,
        'category': p.category,
        'date': p.date.strftime('%Y-%m-%d'),
        'location': p.location,
        'rating': p.rating,
        'max_participants': p.max_participants,
        'organization_name': p.organization.display_name or p.organization.username if p.organization else None,
        'current_participants': sum(1 for r in p.registrations if r.status != 'cancelled')
    } for p in projects])


@bp.route('/api/participant/available-projects')
def api_participant_available_projects():
    """Get available projects for the current participant (filtered)."""
    if 'user_id' not in session or session.get('user_type') != 'participant':
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get all approved projects
    all_projects = Project.query.filter_by(status='approved').order_by(Project.date.asc()).all()
    
    # Get user's existing registrations (both approved and cancelled should be excluded)
    user_registration_project_ids = {
        reg.project_id for reg in Registration.query.filter_by(user_id=user.id).all()
    }
    
    today = datetime.utcnow().date()
    available_projects = []
    
    for project in all_projects:
        # Filter 1: Skip if user has already registered (regardless of status)
        if project.id in user_registration_project_ids:
            continue
        
        # Filter 2: Skip if project date has passed
        if project.date < today:
            continue
        
        # Filter 3: Skip if project is full
        current_participants = sum(1 for r in project.registrations if r.status != 'cancelled')
        if current_participants >= project.max_participants:
            continue
        
        # Project is available
        available_projects.append({
            'id': project.id,
            'title': project.title,
            'category': project.category,
            'date': project.date.strftime('%Y-%m-%d'),
            'location': project.location,
            'rating': project.rating,
            'max_participants': project.max_participants,
            'organization_name': project.organization.display_name or project.organization.username if project.organization else None,
            'current_participants': current_participants
        })
    
    return jsonify(available_projects)


@bp.route('/api/participant/dashboard-data')
def api_participant_dashboard_data():
    if 'user_id' not in session or session.get('user_type') != 'participant':
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Removed recommended_projects - no longer needed

    # Registrations for the user
    user_registrations = Registration.query.filter_by(user_id=user.id).order_by(Registration.created_at.desc()).all()
    registration_payload = []
    for registration in user_registrations:
        project = registration.project
        status_label = registration.status.replace('_', ' ').title()
        progress = 0
        if registration.status == 'completed':
            progress = 100
        elif registration.status == 'in_progress':
            progress = 40
        elif registration.status == 'approved':
            progress = 60

        registration_payload.append({
            'id': project.id,
            'title': project.title,
            'organization_name': project.organization.display_name or project.organization.username if project.organization else None,
            'date': project.date.strftime('%Y-%m-%d'),
            'status': status_label,
            'progress': progress
        })

    # Badge data
    all_badges = Badge.query.order_by(Badge.id.asc()).all()
    user_badges = {ub.badge_id: ub for ub in UserBadge.query.filter_by(user_id=user.id).all()}

    badges_payload = []
    for badge in all_badges:
        user_badge = user_badges.get(badge.id)
        badges_payload.append({
            'code': badge.code,
            'name': badge.name,
            'description': badge.description,
            'earned': bool(user_badge and user_badge.earned),
            'accent_color': badge.accent_color,
            'background_color': badge.background_color,
            'icon': badge.icon
        })

    # Calculate statistics
    # 使用与 volunteer_record 页面相同的逻辑：统计已审核通过的 VolunteerRecord
    approved_records = VolunteerRecord.query.filter_by(user_id=user.id, status='approved').all()
    total_hours = sum(r.hours for r in approved_records)
    total_points = sum(r.points for r in approved_records)
    completed_count = len(approved_records)  # 与 Hour Records 页面保持一致
    upcoming_count = Registration.query.join(Project).filter(
        Registration.user_id == user.id,
        Registration.status.in_(('registered', 'approved')),
        Project.date >= datetime.utcnow().date()
    ).count()

    return jsonify({
        'user': {
            'display_name': user.display_name or user.username
        },
        'statistics': {
            'total_hours': total_hours,
            'total_points': total_points,
            'completed': completed_count,
            'upcoming': upcoming_count
        },
        'registrations': registration_payload,
        'badges': badges_payload
    })

@bp.route('/api/register-project', methods=['POST'])
def api_register_project():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    project_id = data.get('project_id')
    
    if not project_id:
        return jsonify({'error': 'Project ID required'}), 400
    
    # Check if already registered
    existing = Registration.query.filter_by(
        user_id=session['user_id'],
        project_id=project_id
    ).first()
    
    if existing:
        return jsonify({'error': 'Already registered for this project'}), 400
    
    # Check if project is full
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    current_registrations = Registration.query.filter(
        Registration.project_id == project_id,
        Registration.status.in_(('registered', 'approved'))
    ).count()
    
    if current_registrations >= project.max_participants:
        return jsonify({'error': 'Project is full'}), 400
    
    registration = Registration(
        user_id=session['user_id'],
        project_id=project_id,
        status='registered'
    )
    db.session.add(registration)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Successfully registered for project'})

@bp.route('/api/organization/dashboard-data')
def api_organization_dashboard_data():
    if 'user_id' not in session or session.get('user_type') != 'organization':
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get organization's projects
    projects = Project.query.filter_by(organization_id=user.id).all()
    
    active_projects = sum(1 for p in projects if p.status == 'approved')
    active_registration_statuses = ('registered', 'approved')
    total_participants = sum(
        Registration.query.filter(
            Registration.project_id == p.id,
            Registration.status.in_(active_registration_statuses)
        ).count()
        for p in projects
    )
    completed_projects = sum(1 for p in projects if p.status == 'completed')
    pending_projects = sum(1 for p in projects if p.status == 'pending')
    
    projects_payload = []
    for project in projects:
        registrations = Registration.query.filter_by(project_id=project.id).all()
        projects_payload.append({
            'id': project.id,
            'title': project.title,
            'status': project.status,
            'date': project.date.strftime('%Y-%m-%d') if project.date else None,
            'location': project.location,
            'max_participants': project.max_participants,
            'current_participants': sum(1 for r in registrations if r.status in active_registration_statuses),
            'rating': project.rating
        })
    
    # Get recent projects from the last week (created in the last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_projects = Project.query.filter(
        Project.organization_id == user.id,
        Project.created_at >= week_ago,
        Project.status == 'approved'
    ).order_by(Project.created_at.desc()).limit(8).all()
    
    recent_projects_payload = []
    for project in recent_projects:
        registrations = Registration.query.filter_by(project_id=project.id).all()
        recent_projects_payload.append({
            'id': project.id,
            'title': project.title,
            'status': project.status,
            'date': project.date.strftime('%Y-%m-%d') if project.date else None,
            'location': project.location,
            'created_at': project.created_at.strftime('%Y-%m-%d') if project.created_at else None,
            'current_participants': sum(1 for r in registrations if r.status in active_registration_statuses),
            'max_participants': project.max_participants,
            'rating': project.rating,
            'organization_name': project.organization.display_name or project.organization.username if project.organization else None
        })
    
    return jsonify({
        'statistics': {
            'active_projects': active_projects,
            'total_participants': total_participants,
            'completed': completed_projects,
            'pending': pending_projects
        },
        'projects': projects_payload,
        'recent_projects': recent_projects_payload
    })

@bp.route('/api/organization/registrations/<int:project_id>')
def api_organization_registrations(project_id):
    if 'user_id' not in session or session.get('user_type') != 'organization':
        return jsonify({'error': 'Not authenticated'}), 401
    
    project = Project.query.get_or_404(project_id)
    if project.organization_id != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    registrations = Registration.query.filter_by(project_id=project_id).all()
    registrations_payload = []
    for reg in registrations:
        participant = reg.user
        registrations_payload.append({
            'id': reg.id,
            'participant_name': participant.display_name or participant.username,
            'participant_email': participant.email,
            'registration_date': reg.created_at.strftime('%Y-%m-%d') if reg.created_at else None,
            'status': reg.status
        })
    
    return jsonify({
        'project_title': project.title,
        'registrations': registrations_payload
    })


@bp.route('/api/organization/all-registrations')
def api_organization_all_registrations():
    """Get all registrations for all projects of the current organization."""
    if 'user_id' not in session or session.get('user_type') != 'organization':
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get all projects for this organization
    projects = Project.query.filter_by(organization_id=user.id).all()
    
    projects_with_registrations = []
    for project in projects:
        registrations = Registration.query.filter_by(project_id=project.id).all()
        registrations_payload = []
        for reg in registrations:
            participant = reg.user
            registrations_payload.append({
                'id': reg.id,
                'participant_name': participant.display_name or participant.username,
                'participant_email': participant.email,
                'registration_date': reg.created_at.strftime('%Y-%m-%d') if reg.created_at else None,
                'status': reg.status
            })
        
        projects_with_registrations.append({
            'project_id': project.id,
            'project_title': project.title,
            'project_status': project.status,
            'registrations': registrations_payload,
            'total_registrations': len(registrations_payload)
        })
    
    return jsonify({
        'projects': projects_with_registrations
    })

def _check_and_auto_complete_project(project):
    """Check if all participants are completed or cancelled, and auto-complete the project if so."""
    if project.status == 'completed':
        return False  # Already completed
    
    # Get all registrations for this project
    all_registrations = Registration.query.filter_by(project_id=project.id).all()
    
    if not all_registrations:
        return False  # No registrations, can't complete
    
    # Check if all registrations are either 'completed' or 'cancelled'
    all_finalized = all(
        reg.status in ('completed', 'cancelled') 
        for reg in all_registrations
    )
    
    if not all_finalized:
        return False  # Not all participants are finalized
    
    # Auto-complete the project
    project.status = 'completed'
    
    # Ensure volunteer records exist for completed participants
    records_created = 0
    for registration in all_registrations:
        if registration.status == 'completed':
            # Check if volunteer record already exists
            existing_record = VolunteerRecord.query.filter_by(
                user_id=registration.user_id,
                project_id=project.id
            ).first()
            
            if not existing_record:
                # Create volunteer record for confirmed participants
                volunteer_record = VolunteerRecord(
                    user_id=registration.user_id,
                    project_id=project.id,
                    hours=project.duration,
                    points=project.points,
                    status='pending',  # Wait for admin approval
                    completed_at=datetime.utcnow()
                )
                db.session.add(volunteer_record)
                records_created += 1
    
    db.session.commit()
    return True  # Project was auto-completed


@bp.route('/api/organization/registration/<int:registration_id>/status', methods=['POST'])
def api_organization_update_registration_status(registration_id):
    if 'user_id' not in session or session.get('user_type') != 'organization':
        return jsonify({'error': 'Not authenticated'}), 401
    
    registration = Registration.query.get_or_404(registration_id)
    project = registration.project
    if not project or project.organization_id != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json(silent=True) or request.form or {}
    new_status = (data.get('status') or '').strip().lower()
    allowed_statuses = {'registered', 'approved', 'cancelled', 'completed'}
    if new_status not in allowed_statuses:
        return jsonify({'error': 'Invalid status'}), 400
    
    registration.status = new_status
    
    # 如果组织确认参与者完成项目，自动创建待审核的工时记录
    if new_status == 'completed':
        # 检查是否已经存在该参与者的工时记录
        existing_record = VolunteerRecord.query.filter_by(
            user_id=registration.user_id,
            project_id=registration.project_id
        ).first()
        
        if not existing_record:
            # 创建新的工时记录，状态为 pending，等待管理员审核
            volunteer_record = VolunteerRecord(
                user_id=registration.user_id,
                project_id=registration.project_id,
                hours=project.duration,  # 使用项目的时长
                points=project.points,  # 使用项目的积分
                status='pending',  # 待管理员审核
                completed_at=datetime.utcnow()
            )
            db.session.add(volunteer_record)
    
    db.session.commit()
    
    # Check if project should be auto-completed
    project_auto_completed = _check_and_auto_complete_project(project)
    
    response_data = {
        'success': True, 
        'status': new_status
    }
    if project_auto_completed:
        response_data['project_auto_completed'] = True
        response_data['message'] = 'Registration status updated. Project has been automatically marked as completed since all participants are finalized.'
    
    return jsonify(response_data)


@bp.route('/api/organization/project/<int:project_id>/complete', methods=['POST'])
def api_organization_complete_project(project_id):
    """Mark a project as completed. Only participants with status='completed' will have volunteer records."""
    if 'user_id' not in session or session.get('user_type') != 'organization':
        return jsonify({'error': 'Not authenticated'}), 401
    
    project = Project.query.get_or_404(project_id)
    if project.organization_id != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if project is already completed
    if project.status == 'completed':
        return jsonify({'error': 'Project is already completed'}), 400
    
    # Mark project as completed
    project.status = 'completed'
    
    # Get all registrations for this project
    all_registrations = Registration.query.filter_by(project_id=project.id).all()
    
    # For participants who have already been confirmed as completed (status='completed'),
    # ensure they have volunteer records. Others are marked as not completed (cancelled).
    completed_registrations = []
    not_completed_count = 0
    
    for registration in all_registrations:
        if registration.status == 'completed':
            # These participants have been confirmed as completed
            completed_registrations.append(registration)
        else:
            # Mark all other participants (approved, registered) as not completed (cancelled)
            if registration.status in ('approved', 'registered'):
                registration.status = 'cancelled'
                not_completed_count += 1
    
    records_created = 0
    for registration in completed_registrations:
        # Check if volunteer record already exists
        existing_record = VolunteerRecord.query.filter_by(
            user_id=registration.user_id,
            project_id=project.id
        ).first()
        
        if not existing_record:
            # Create volunteer record for confirmed participants
            volunteer_record = VolunteerRecord(
                user_id=registration.user_id,
                project_id=project.id,
                hours=project.duration,
                points=project.points,
                status='pending',  # Wait for admin approval
                completed_at=datetime.utcnow()
            )
            db.session.add(volunteer_record)
            records_created += 1
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Project marked as completed. {records_created} volunteer record(s) created for confirmed participants. {not_completed_count} participant(s) marked as not completed.',
        'records_created': records_created,
        'not_completed_count': not_completed_count
    })

@bp.route('/api/admin/dashboard-data')
def api_admin_dashboard_data():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Pending projects for review
    pending_projects = Project.query.filter_by(status='pending').order_by(Project.created_at.desc()).all()
    projects_payload = []
    for project in pending_projects:
        org = project.organization
        projects_payload.append({
            'id': project.id,
            'title': project.title,
            'organization_name': org.display_name or org.username if org else 'Unknown',
            'organization_email': org.email if org else None,
            'date': project.date.strftime('%Y-%m-%d') if project.date else None,
            'location': project.location,
            'max_participants': project.max_participants,
            'rating': project.rating,
            'description': project.description,
            'submitted_date': project.created_at.strftime('%Y-%m-%d') if project.created_at else None
        })
    
    # Pending volunteer records for review
    pending_records = VolunteerRecord.query.filter_by(status='pending').order_by(VolunteerRecord.completed_at.desc()).all()
    records_payload = []
    for record in pending_records:
        participant = record.user
        project = record.project
        org = project.organization if project else None
        records_payload.append({
            'id': record.id,
            'participant_name': participant.display_name or participant.username,
            'project_name': project.title if project else 'Unknown',
            'organization_name': org.display_name or org.username if org else 'Unknown',
            'hours': record.hours,
            'points': record.points,
            'completion_date': record.completed_at.strftime('%Y-%m-%d') if record.completed_at else None
        })
    
    # All users
    users = User.query.order_by(User.created_at.desc()).limit(100).all()
    users_payload = []
    for u in users:
        users_payload.append({
            'id': u.id,
            'username': u.username,
            'display_name': u.display_name,
            'email': u.email,
            'user_type': u.user_type,
            'created_at': u.created_at.strftime('%Y-%m-%d') if u.created_at else None
        })
    
    return jsonify({
        'pending_projects': projects_payload,
        'pending_records': records_payload,
        'users': users_payload
    })

@bp.route('/api/admin/approve-project/<int:project_id>', methods=['POST'])
def api_admin_approve_project(project_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return jsonify({'error': 'Not authenticated'}), 401
    
    project = Project.query.get_or_404(project_id)
    project.status = 'approved'
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/api/admin/reject-project/<int:project_id>', methods=['POST'])
def api_admin_reject_project(project_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return jsonify({'error': 'Not authenticated'}), 401
    
    project = Project.query.get_or_404(project_id)
    project.status = 'rejected'
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/api/admin/approve-record/<int:record_id>', methods=['POST'])
def api_admin_approve_record(record_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return jsonify({'error': 'Not authenticated'}), 401
    
    record = VolunteerRecord.query.get_or_404(record_id)
    record.status = 'approved'
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/api/admin/reject-record/<int:record_id>', methods=['POST'])
def api_admin_reject_record(record_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return jsonify({'error': 'Not authenticated'}), 401
    
    record = VolunteerRecord.query.get_or_404(record_id)
    record.status = 'rejected'
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/api/organization/create-project', methods=['POST'])
def api_organization_create_project():
    if 'user_id' not in session or session.get('user_type') != 'organization':
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.form if request.form else request.get_json()
    
    project = Project(
        title=data.get('title'),
        description=data.get('description'),
        category=data.get('category'),
        organization_id=session['user_id'],
        date=datetime.strptime(data.get('date'), '%Y-%m-%d').date() if data.get('date') else None,
        location=data.get('location'),
        max_participants=int(data.get('max_participants', 0)),
        duration=float(data.get('duration', 0)),
        points=int(data.get('points', 0)),
        status='pending',
        requirements=data.get('requirements', '')
    )
    db.session.add(project)
    db.session.commit()
    
    return jsonify({'success': True, 'project_id': project.id})

@bp.route('/api/project/<int:project_id>/comment', methods=['POST'])
def api_project_comment(project_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # For now, we'll use registrations as comments
    # In a full implementation, you'd have a separate Comment model
    data = request.get_json()
    comment_text = data.get('comment', '').strip()
    
    if not comment_text:
        return jsonify({'error': 'Comment cannot be empty'}), 400
    
    # Check if user is registered for this project
    registration = Registration.query.filter_by(
        user_id=session['user_id'],
        project_id=project_id
    ).first()
    
    if not registration:
        return jsonify({'error': 'You must be registered for this project to comment'}), 403
    
    # Store comment in registration (temporary solution)
    # In production, create a Comment model
    return jsonify({'success': True, 'message': 'Comment functionality will be implemented with Comment model'})

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
