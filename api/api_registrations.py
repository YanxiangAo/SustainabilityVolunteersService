"""Registrations API routes."""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from models import db, Project, Registration, VolunteerRecord

bp = Blueprint('api_registrations', __name__)


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


@bp.route('/api/v1/projects/<int:project_id>/registrations', methods=['GET'])
@login_required
def api_project_registrations_list(project_id):
    """Get all registrations for a project."""
    project = Project.query.get_or_404(project_id)
    
    # Check permissions
    if current_user.user_type == 'organization' and project.organization_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    elif current_user.user_type == 'participant':
        # Participants can only see their own registrations
        registrations = Registration.query.filter_by(
            project_id=project_id,
            user_id=current_user.id
        ).all()
    else:
        # Admin or organization owner can see all
        registrations = Registration.query.filter_by(project_id=project_id).all()
    
    result = []
    for reg in registrations:
        participant = reg.user
        result.append({
            'id': reg.id,
            'user_id': reg.user_id,
            'project_id': reg.project_id,
            'status': reg.status,
            'created_at': reg.created_at.strftime('%Y-%m-%d %H:%M:%S') if reg.created_at else None,
            'participant': {
                'id': participant.id,
                'name': participant.display_name or participant.username,
                'email': participant.email
            } if participant else None
        })
    
    return jsonify(result)


@bp.route('/api/v1/projects/<int:project_id>/registrations', methods=['POST'])
@login_required
def api_project_registrations_create(project_id):
    """Register for a project."""
    # Admin and organization users are not allowed to register for projects
    if current_user.user_type == 'admin':
        return jsonify({'error': 'Admin users cannot register for projects', 'requires_login': True}), 403
    if current_user.user_type == 'organization':
        return jsonify({'error': 'Organization users cannot register for projects', 'requires_login': True}), 403
    
    project = Project.query.get_or_404(project_id)
    
    # Check if already registered
    existing = Registration.query.filter_by(
        user_id=current_user.id,
        project_id=project_id
    ).first()
    
    if existing:
        return jsonify({'error': 'Already registered for this project'}), 400
    
    # Check if project is full
    current_registrations = Registration.query.filter(
        Registration.project_id == project_id,
        Registration.status.in_(('registered', 'approved'))
    ).count()
    
    if current_registrations >= project.max_participants:
        return jsonify({'error': 'Project is full'}), 400
    
    registration = Registration(
        user_id=current_user.id,
        project_id=project_id,
        status='registered'
    )
    db.session.add(registration)
    db.session.commit()
    
    return jsonify({
        'id': registration.id,
        'project_id': project_id,
        'status': registration.status,
        'message': 'Successfully registered for project'
    }), 201


@bp.route('/api/v1/registrations/<int:registration_id>', methods=['GET'])
@login_required
def api_registration_detail(registration_id):
    """Get a single registration."""
    registration = Registration.query.get_or_404(registration_id)
    
    # Check permissions
    if current_user.user_type == 'participant' and registration.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    elif current_user.user_type == 'organization':
        project = registration.project
        if not project or project.organization_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
    
    participant = registration.user
    project = registration.project
    
    return jsonify({
        'id': registration.id,
        'user_id': registration.user_id,
        'project_id': registration.project_id,
        'status': registration.status,
        'created_at': registration.created_at.strftime('%Y-%m-%d %H:%M:%S') if registration.created_at else None,
        'participant': {
            'id': participant.id,
            'name': participant.display_name or participant.username,
            'email': participant.email
        } if participant else None,
        'project': {
            'id': project.id,
            'title': project.title
        } if project else None
    })


@bp.route('/api/v1/registrations/<int:registration_id>', methods=['PATCH'])
@login_required
def api_registration_update(registration_id):
    """Update registration status."""
    registration = Registration.query.get_or_404(registration_id)
    project = registration.project
    
    # Check permissions
    if current_user.user_type == 'organization':
        if not project or project.organization_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
    elif current_user.user_type != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json(silent=True) or request.form or {}
    new_status = (data.get('status') or '').strip().lower()
    allowed_statuses = {'registered', 'approved', 'cancelled', 'completed'}
    
    if new_status not in allowed_statuses:
        return jsonify({'error': 'Invalid status'}), 400
    
    registration.status = new_status
    
    # If organization confirms participant completed project, auto-create pending volunteer record
    if new_status == 'completed':
        existing_record = VolunteerRecord.query.filter_by(
            user_id=registration.user_id,
            project_id=registration.project_id
        ).first()
        
        if not existing_record:
            volunteer_record = VolunteerRecord(
                user_id=registration.user_id,
                project_id=registration.project_id,
                hours=project.duration,
                points=project.points,
                status='pending',
                completed_at=datetime.utcnow()
            )
            db.session.add(volunteer_record)
    
    db.session.commit()
    
    # Check if project should be auto-completed
    project_auto_completed = _check_and_auto_complete_project(project)
    
    response_data = {
        'id': registration.id,
        'status': new_status,
        'message': 'Registration status updated successfully'
    }
    if project_auto_completed:
        response_data['project_auto_completed'] = True
        response_data['message'] = 'Registration status updated. Project has been automatically marked as completed.'
    
    return jsonify(response_data)


@bp.route('/api/v1/registrations/<int:registration_id>', methods=['DELETE'])
@login_required
def api_registration_delete(registration_id):
    """Cancel/delete a registration."""
    registration = Registration.query.get_or_404(registration_id)
    
    # Check permissions
    if current_user.user_type == 'participant' and registration.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    elif current_user.user_type == 'organization':
        project = registration.project
        if not project or project.organization_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
    
    # Instead of deleting, mark as cancelled
    registration.status = 'cancelled'
    db.session.commit()
    
    return jsonify({'message': 'Registration cancelled successfully'}), 200


@bp.route('/api/organization/registrations/<int:project_id>')
@login_required
def api_organization_registrations(project_id):
    if current_user.user_type != 'organization':
        return jsonify({'error': 'Not authenticated'}), 401
    
    project = Project.query.get_or_404(project_id)
    if project.organization_id != current_user.id:
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
@login_required
def api_organization_all_registrations():
    """Get all registrations for all projects of the current organization."""
    if current_user.user_type != 'organization':
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Get all projects for this organization
    projects = Project.query.filter_by(organization_id=current_user.id).all()
    
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

