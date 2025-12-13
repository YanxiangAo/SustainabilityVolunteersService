"""Projects API routes."""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import logging

from models import db, Project, Registration, SystemSettings

bp = Blueprint('api_projects', __name__)
logger = logging.getLogger(__name__)

def validate_project_data(data, is_update=False):
    """
    Validate project input data.
    Returns (is_valid, error_message, validated_data)
    """
    errors = []
    validated = {}
    
    # Required fields for creation
    required_fields = ['title', 'date', 'location', 'description']
    if not is_update:
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Missing required field: {field}")
    
    # Title validation
    if 'title' in data:
        title = data['title'].strip()
        if len(title) < 3:
            errors.append("Title must be at least 3 characters")
        validated['title'] = title
        
    # Numeric fields validation
    try:
        if 'max_participants' in data:
            val = int(data['max_participants'])
            if val < 1: errors.append("Max participants must be at least 1")
            validated['max_participants'] = val
            
        if 'duration' in data:
            val = float(data['duration'])
            if val <= 0: errors.append("Duration must be positive")
            validated['duration'] = val
            
        if 'points' in data:
            val = int(data['points'])
            if val < 0: errors.append("Points cannot be negative")
            validated['points'] = val
            
    except (ValueError, TypeError):
        errors.append("Invalid numeric format for participants, duration or points")

    # Date validation
    if 'date' in data and data['date']:
        try:
            if isinstance(data['date'], str):
                date_obj = datetime.strptime(data['date'], '%Y-%m-%d').date()
                validated['date'] = date_obj
        except ValueError:
            errors.append("Invalid date format, expected YYYY-MM-DD")
            
    # Other fields
    for field in ['description', 'category', 'location', 'requirements']:
        if field in data:
            validated[field] = data[field]
            
    return len(errors) == 0, "; ".join(errors), validated


@bp.route('/api/v1/projects', methods=['GET'])
def api_projects_list():
    """Get all approved/in_progress projects (for homepage, exclude expired projects)."""
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
    
    # Exclude projects that the current user has already registered for
    # Only apply this filter if user is authenticated and is a participant
    if current_user.is_authenticated and current_user.user_type == 'participant':
        # Get project IDs that the user has registered for (excluding cancelled)
        registered_project_ids = db.session.query(Registration.project_id).filter_by(
            user_id=current_user.id
        ).filter(
            Registration.status != 'cancelled'
        ).distinct().all()
        registered_project_ids = [pid[0] for pid in registered_project_ids]
        if registered_project_ids:
            query = query.filter(~Project.id.in_(registered_project_ids))
    
    projects = query.order_by(Project.date.asc()).all()
    
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
    """Create a new project with validation."""
    if current_user.user_type != 'organization':
        return jsonify({'error': 'Only organizations can create projects'}), 403
    
    data = request.form.to_dict() if request.form else request.get_json()
    
    # Input Validation
    is_valid, error_msg, validated_data = validate_project_data(data)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # Check if project requires review
    requires_review = SystemSettings.get_setting('project_requires_review', 'true')
    initial_status = 'pending' if requires_review.lower() == 'true' else 'approved'
    
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
    
    return jsonify({
        'id': project.id,
        'status': project.status,
        'message': f'Project {status} successfully'
    })


@bp.route('/api/v1/projects/<int:project_id>', methods=['PATCH'])
@login_required
def api_projects_update(project_id):
    """Update a project (status, etc.)."""
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
            
        is_valid, error_msg, validated_data = validate_project_data(data, is_update=True)
        if not is_valid:
            return jsonify({'error': error_msg}), 400

        # Apply updates
        for key, value in validated_data.items():
            setattr(project, key, value)
            
    else:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.commit()
    return jsonify({
        'id': project.id,
        'status': project.status,
        'message': 'Project updated successfully'
    })
