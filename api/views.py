"""Page view routes (dashboards, project detail, volunteer records)."""
from flask import Blueprint, render_template, request, redirect, url_for, send_file
from flask_login import login_required, current_user
from datetime import datetime

from models import Project, Registration, VolunteerRecord, User, Comment
from utils import require_user_type, generate_excel_from_records

bp = Blueprint('views', __name__)


@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/participant/dashboard')
@login_required
def participant_dashboard():
    if current_user.user_type != 'participant':
        return redirect(url_for('auth.login'))
    
    return render_template('participant_dashboard.html', user=current_user)


@bp.route('/organization/dashboard')
@login_required
def organization_dashboard():
    if current_user.user_type != 'organization':
        return redirect(url_for('auth.login'))
    
    return render_template('organization_dashboard.html', user=current_user)


@bp.route('/admin/panel')
@login_required
def admin_panel():
    if current_user.user_type != 'admin':
        return redirect(url_for('auth.login'))
    
    return render_template('admin_panel.html', user=current_user)


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
    # Get comments for display
    comments = Comment.query.filter_by(project_id=project.id).order_by(Comment.created_at.desc()).limit(20).all()
    comments_data = []
    for comment in comments:
        comments_data.append({
            'id': comment.id,
            'user_name': comment.user.display_name or comment.user.username if comment.user else 'Unknown',
            'user_type': comment.user.user_type.title() if comment.user else 'Unknown',
            'comment': comment.content,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M') if comment.created_at else None
        })
    
    # Check if current user is registered or is the organization owner
    is_registered = False
    can_comment = False
    user_type = None
    if current_user.is_authenticated:
        user_type = current_user.user_type
        # Check if user is registered (for participants)
        if user_type == 'participant':
            existing_reg = Registration.query.filter(
                Registration.user_id == current_user.id,
                Registration.project_id == project.id,
                Registration.status.in_(active_statuses + ('completed',))
            ).first()
            is_registered = existing_reg is not None
            can_comment = is_registered
        # Organization owner can always comment on their own projects
        elif user_type == 'organization':
            can_comment = (project.organization_id == current_user.id)
    
    return render_template('project_detail.html', 
                         project=project, 
                         organization=organization,
                         registration_count=registration_count,
                         comments=comments_data,
                         is_registered=is_registered,
                         can_comment=can_comment,
                         user_type=user_type)


@bp.route('/demo/project')
def demo_project_detail():
    """Demo route showing project detail page with seeded database data."""
    project = Project.query.filter_by(status='approved').order_by(Project.date.asc()).first()
    if not project:
        return redirect(url_for('views.index'))

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
@login_required
def volunteer_record():
    if current_user.user_type != 'participant':
        return redirect(url_for('auth.login'))
    
    records = VolunteerRecord.query.filter_by(user_id=current_user.id).order_by(VolunteerRecord.completed_at.desc()).all()
    
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
                         user=current_user, 
                         records_data=records_data,
                         total_hours=total_hours,
                         total_points=total_points,
                         completed_count=completed_count,
                         available_years=sorted(years_set, reverse=True),
                         available_categories=sorted(categories_set))


@bp.route('/api/participant/export-all-records')
@login_required
def api_export_all_records():
    """Export all volunteer records for the current participant."""
    if current_user.user_type != 'participant':
        from flask import jsonify
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Get all records
    records = VolunteerRecord.query.filter_by(user_id=current_user.id).order_by(VolunteerRecord.completed_at.desc()).all()
    
    # Get user display_name (fallback to username if not set)
    user_display_name = current_user.display_name or current_user.username
    
    output, filename = generate_excel_from_records(records, "all_volunteer_records", user_display_name)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


@bp.route('/api/participant/export-filtered-records', methods=['POST'])
@login_required
def api_export_filtered_records():
    """Export filtered volunteer records for the current participant."""
    if current_user.user_type != 'participant':
        from flask import jsonify
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    year_filter = data.get('year')
    category_filter = data.get('category')
    
    # Get all records
    records = VolunteerRecord.query.filter_by(user_id=current_user.id).order_by(VolunteerRecord.completed_at.desc()).all()
    
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
    user_display_name = current_user.display_name or current_user.username
    
    output, filename = generate_excel_from_records(filtered_records, "filtered_volunteer_records", user_display_name)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

