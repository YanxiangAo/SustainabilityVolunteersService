"""Projects API routes.

This module exposes JSON APIs for:
- Listing/filtering projects for the homepage and dashboards
- Creating/updating/deleting projects for organizations
- Admin operations such as reviewing and rating projects

All user-provided project data is validated with Marshmallow schemas
defined in `schemas.py` before being persisted.
"""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, current_app
from flask_login import login_required, current_user
from datetime import datetime
import logging

from models import db, Project, Registration, Comment, VolunteerRecord, User
from marshmallow import ValidationError
from schemas import ProjectCreateSchema, ProjectUpdateSchema

bp = Blueprint('api_projects', __name__)
logger = logging.getLogger(__name__)

@bp.route('/api/v1/projects', methods=['GET'])
def api_projects_list():
    """Get projects for the homepage / dashboards with optional filters."""
    # Support query parameters
    status = request.args.get('status')  # None means all registrable statuses
    available = request.args.get('available', 'false').lower() == 'true'
    all_projects = request.args.get('all', 'false').lower() == 'true'
    today = datetime.utcnow().date()
    
    query = Project.query
    
    # Filter logic
    if all_projects:
        # If 'all' is requested, only admin can see everything, organizations see their own?
        # For now, let's assume this parameter is for admin use cases where they need to see pending
        if not current_user.is_authenticated or current_user.user_type != 'admin':
           pass # Could restrict here, but keeping flexible for now as per requirements
        
        if status:
            query = query.filter_by(status=status)
            
    elif status:
        query = query.filter_by(status=status)
    elif available:
        # For available projects, include both approved and in_progress
        query = query.filter(Project.status.in_(('approved', 'in_progress')))
    
    if available:
        query = query.filter(Project.date >= today)
        
        # Exclude projects that the user has already registered for (any status)
        # This ensures users don't see projects they've already interacted with
        if current_user.is_authenticated and current_user.user_type == 'participant':
            registered_project_ids = [
                r.project_id for r in Registration.query.filter_by(user_id=current_user.id).all()
            ]
            if registered_project_ids:
                query = query.filter(~Project.id.in_(registered_project_ids))
    
    projects = query.order_by(Project.date.asc()).all()
    
    # Get user's registrations if authenticated participant (for non-available queries)
    user_registrations = {}
    if current_user.is_authenticated and current_user.user_type == 'participant' and not available:
        registrations = Registration.query.filter_by(user_id=current_user.id).all()
        user_registrations = {r.project_id: r.status for r in registrations}
    
    result = []
    for p in projects:
        current_participants = sum(1 for r in p.registrations if r.status != 'cancelled')
        project_data = {
            'id': p.id,
            'title': p.title,
            'category': p.category,
            'date': p.date.strftime('%Y-%m-%d') if p.date else None,
            'location': p.location,
            'rating': p.rating,
            'max_participants': p.max_participants,
            'current_participants': current_participants,
            'status': p.status,
            'organization_name': p.organization.display_name or p.organization.username if p.organization else None,
            'description': p.description, 
            'created_at': p.created_at.strftime('%Y-%m-%d') if hasattr(p, 'created_at') and p.created_at else None,
            'organization': {
                'id': p.organization_id,
                'name': p.organization.display_name or p.organization.username if p.organization else None
            }
        }
        # Include user's registration status if exists (only for non-available queries)
        if p.id in user_registrations:
            project_data['user_registration_status'] = user_registrations[p.id]
        
        # Only include if not expired when available=true
        if not available or (p.date and p.date >= today):
            result.append(project_data)
    
    return jsonify(result)


@bp.route('/api/v1/projects/<int:project_id>', methods=['GET'])
def api_project_detail(project_id):
    """Get a single project by ID."""
    project = Project.query.get_or_404(project_id)
    organization = project.organization
    
    return jsonify({
        'id': project.id,
        'title': project.title,
        'description': project.description,
        'category': project.category,
        'date': project.date.strftime('%Y-%m-%d') if project.date else None,
        'location': project.location,
        'rating': project.rating,
        'max_participants': project.max_participants,
        'current_participants': sum(1 for r in project.registrations if r.status != 'cancelled'),
        'duration': project.duration,
        'points': project.points,
        'status': project.status,
        'requirements': project.requirements,
        'organization': {
            'id': organization.id if organization else None,
            'name': organization.display_name or organization.username if organization else None,
            'email': organization.email if organization else None
        } if organization else None
    })


@bp.route('/api/v1/projects', methods=['POST'])
@login_required
def api_projects_create():
    """Create a new project with validation.

    Request body comes from the organization dashboard publish form.
    We support both form-data (HTML form) and JSON payloads.
    """
    if current_user.user_type != 'organization':
        return jsonify({'error': 'Only organizations can create projects'}), 403
    
    data = request.form.to_dict() if request.form else (request.get_json() or {})
    
    # Input Validation using Marshmallow
    # Validate and normalize incoming data with Marshmallow
    schema = ProjectCreateSchema()
    try:
        validated_data = schema.load(data)
    except ValidationError as err:
        error_msg = "; ".join(
            [f"{field}: {', '.join(msgs)}" for field, msgs in err.messages.items()]
        )
        current_app.logger.warning('Project creation validation failed: %s', err.messages)
        return jsonify({'error': error_msg, 'details': err.messages}), 400
    
    # Require review by default (SystemSettings removed)
    requires_review = 'true'
    initial_status = 'pending' if requires_review == 'true' else 'approved'
    
    project = Project(
        title=validated_data.get('title'),
        description=validated_data.get('description'),
        category=validated_data.get('category'),
        organization_id=current_user.id,
        date=validated_data.get('date'),
        location=validated_data.get('location'),
        max_participants=validated_data.get('max_participants', 10),
        duration=validated_data.get('duration', 0),
        points=validated_data.get('points', 0),
        status=initial_status,
        requirements=validated_data.get('requirements', ''),
        created_at=datetime.utcnow()
    )
    db.session.add(project)
    db.session.commit()
    logger.info(f'Project created id={project.id} status={initial_status} org={current_user.id}')
    
    message = 'Project created successfully'
    if initial_status == 'approved':
        message = 'Project created and auto-approved'
    
    return jsonify({
        'id': project.id,
        'title': project.title,
        'status': project.status,
        'message': message
    }), 201


@bp.route('/api/v1/projects/<int:project_id>/review', methods=['PATCH'])
@login_required
def api_projects_review(project_id):
    """Admin endpoint to review (approve/reject) a project."""
    if current_user.user_type != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    project = Project.query.get_or_404(project_id)
    data = request.get_json() or {}
    status = data.get('status')
    
    if status not in ['approved', 'rejected']:
        return jsonify({'error': 'Invalid status'}), 400
        
    project.status = status
    db.session.commit()
    logger.info(f'Project review id={project.id} status={status} admin={current_user.id}')
    
    return jsonify({
        'id': project.id,
        'status': project.status,
        'message': f'Project {status} successfully'
    })


@bp.route('/api/v1/projects/<int:project_id>/rating', methods=['PATCH'])
@login_required
def api_projects_set_rating(project_id):
    """Admin endpoint to set/update project rating (0–5 scale)."""
    if current_user.user_type != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    project = Project.query.get_or_404(project_id)
    data = request.get_json() or {}

    try:
        rating = float(data.get('rating', 0))
    except (TypeError, ValueError):
        current_app.logger.warning('Project rating validation failed: invalid rating value payload=%s', data)
        return jsonify({'error': 'Invalid rating value'}), 400

    if rating < 0 or rating > 5:
        current_app.logger.warning('Project rating validation failed: out of range rating=%s', rating)
        return jsonify({'error': 'Rating must be between 0 and 5'}), 400

    project.rating = rating
    db.session.commit()
    logger.info(f'Project rating updated id={project.id} rating={project.rating} admin={current_user.id}')

    return jsonify({
        'id': project.id,
        'rating': project.rating,
        'message': 'Project rating updated successfully'
    })


@bp.route('/api/v1/projects/<int:project_id>', methods=['PATCH'])
@login_required
def api_projects_update(project_id):
    """Update a project (status, etc.).

    For organization owners this is used to edit project details.
    For admins this is mostly used to update project status.
    """
    project = Project.query.get_or_404(project_id)
    data = request.get_json() or {}
    
    # Check permissions
    if current_user.user_type == 'admin':
        # Admin can update status directly
        if 'status' in data:
            project.status = data['status']
            
    elif current_user.user_type == 'organization' and project.organization_id == current_user.id:
        # Organization can update their own projects (but not status to approved/rejected)
        if 'status' in data and data['status'] in ('approved', 'rejected'):
            return jsonify({'error': 'Cannot change status to approved/rejected'}), 403
            
        # Validate partial update payload using Marshmallow
        schema = ProjectUpdateSchema(partial=True)
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            error_msg = "; ".join(
                [f"{field}: {', '.join(msgs)}" for field, msgs in err.messages.items()]
            )
            current_app.logger.warning('Project update validation failed: %s', err.messages)
            return jsonify({'error': error_msg, 'details': err.messages}), 400

        # Apply updates
        for key, value in validated_data.items():
            setattr(project, key, value)
            
    else:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.commit()
    logger.info(f'Project updated id={project.id} by user={current_user.id} status={project.status}')
    return jsonify({
        'id': project.id,
        'status': project.status,
        'message': 'Project updated successfully'
    })


@bp.route('/api/v1/projects/<int:project_id>', methods=['DELETE'])
@login_required
def api_projects_delete(project_id):
    """Delete a project. Only organization owners can delete their own projects."""
    project = Project.query.get_or_404(project_id)
    
    # Check permissions: only organization owners can delete their own projects
    if current_user.user_type != 'organization' or project.organization_id != current_user.id:
        return jsonify({'error': 'Unauthorized. You can only delete your own projects.'}), 403
    
    try:
        pid = project.id
        
        # Delete all comments on this project (including replies)
        # First, get all comment IDs from this project
        project_comments = Comment.query.filter_by(project_id=pid).all()
        project_comment_ids = [c.id for c in project_comments]
        
        # Delete all replies to comments on this project (must delete replies first due to foreign key)
        if project_comment_ids:
            Comment.query.filter(Comment.parent_id.in_(project_comment_ids)).delete(synchronize_session=False)
        
        # Delete all comments on this project
        Comment.query.filter_by(project_id=pid).delete(synchronize_session=False)
        
        # Delete all registrations for this project
        Registration.query.filter_by(project_id=pid).delete(synchronize_session=False)
        
        # Delete all volunteer records for this project
        VolunteerRecord.query.filter_by(project_id=pid).delete(synchronize_session=False)
        
        # Delete the project itself
        db.session.delete(project)
        db.session.commit()
        current_app.logger.info(f'Project deleted id={pid} by org={current_user.id}')
        
        return jsonify({
            'message': 'Project deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting project {project_id}: {str(e)}', exc_info=True)
        return jsonify({'error': f'Failed to delete project: {str(e)}'}), 500


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
    registration_status = None  # Track registration status for cancelled/rejected cases
    if current_user.is_authenticated:
        user_type = current_user.user_type
        # Check if user is registered (for participants)
        if user_type == 'participant':
            existing_reg = Registration.query.filter(
                Registration.user_id == current_user.id,
                Registration.project_id == project.id
            ).first()
            if existing_reg:
                registration_status = existing_reg.status
                # Check if registered with active status
                if existing_reg.status in active_statuses + ('completed',):
                    is_registered = True
                    can_comment = True
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
                         user_type=user_type,
                         registration_status=registration_status)
