"""Dashboard API routes."""
from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta

from models import Project, Registration, VolunteerRecord, User

bp = Blueprint('api_dashboard', __name__)


@bp.route('/api/v1/users/me/dashboard', methods=['GET'])
@login_required
def api_users_me_dashboard():
    """Get current user's dashboard data."""
    user_type = current_user.user_type
    
    if user_type == 'participant':
        # Get registrations for the user
        user_registrations = Registration.query.filter_by(user_id=current_user.id).order_by(Registration.created_at.desc()).all()
        registration_payload = []
        for registration in user_registrations:
            project = registration.project
            status_label = registration.status.replace('_', ' ').title()
            progress = 0
            if registration.status == 'completed':
                progress = 100
            elif registration.status == 'in_progress':
                progress = 75
            elif registration.status == 'approved':
                progress = 50
            elif registration.status == 'registered':
                progress = 25

            registration_payload.append({
                'id': project.id,
                'registration_id': registration.id,
                'title': project.title,
                'organization_name': project.organization.display_name or project.organization.username if project.organization else None,
                'date': project.date.strftime('%Y-%m-%d'),
                'status': status_label,
                'progress': progress
            })

        # Calculate statistics
        approved_records = VolunteerRecord.query.filter_by(user_id=current_user.id, status='approved').all()
        total_hours = sum(r.hours for r in approved_records)
        total_points = sum(r.points for r in approved_records)
        completed_count = len(approved_records)
        upcoming_count = Registration.query.join(Project).filter(
            Registration.user_id == current_user.id,
            Registration.status.in_(('registered', 'approved')),
            Project.date >= datetime.utcnow().date()
        ).count()

        return jsonify({
            'user': {
                'display_name': current_user.display_name or current_user.username
            },
            'statistics': {
                'total_hours': total_hours,
                'total_points': total_points,
                'completed': completed_count,
                'upcoming': upcoming_count
            },
            'registrations': registration_payload
        })
    
    elif user_type == 'organization':
        # Get organization's projects
        projects = Project.query.filter_by(organization_id=current_user.id).all()
        
        active_projects = sum(1 for p in projects if p.status in ('approved', 'in_progress'))
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
        
        # Get recent projects from the last week
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_projects = Project.query.filter(
            Project.organization_id == current_user.id,
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
    
    elif user_type == 'admin':
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
        
        # All users (exclude admin users)
        users = User.query.filter(User.user_type != 'admin').order_by(User.created_at.desc()).limit(100).all()
        users_payload = []
        for u in users:
            users_payload.append({
                'id': u.id,
                'username': u.username,
                'display_name': u.display_name,
                'email': u.email,
                'user_type': u.user_type,
                'is_active': u.is_active if hasattr(u, 'is_active') else True,
                'ban_reason': getattr(u, 'ban_reason', None),
                'ban_until': u.ban_until.isoformat() if getattr(u, 'ban_until', None) else None,
                'created_at': u.created_at.strftime('%Y-%m-%d') if u.created_at else None
            })
        
        return jsonify({
            'pending_projects': projects_payload,
            'pending_records': records_payload,
            'users': users_payload
        })
    
    return jsonify({'error': 'Invalid user type'}), 400
