"""Projects API routes."""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from models import db, Project, Registration

bp = Blueprint('api_projects', __name__)


@bp.route('/api/v1/projects', methods=['GET'])
def api_projects_list():
    """Get all approved projects (for homepage, exclude expired projects)."""
    # Support query parameters
    status = request.args.get('status', 'approved')
    available = request.args.get('available', 'false').lower() == 'true'
    today = datetime.utcnow().date()
    
    query = Project.query
    if status:
        query = query.filter_by(status=status)
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
    """Create a new project."""
    if current_user.user_type != 'organization':
        return jsonify({'error': 'Only organizations can create projects'}), 403
    
    data = request.form if request.form else request.get_json()
    
    project = Project(
        title=data.get('title'),
        description=data.get('description'),
        category=data.get('category'),
        organization_id=current_user.id,
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
    
    return jsonify({
        'id': project.id,
        'title': project.title,
        'status': project.status,
        'message': 'Project created successfully'
    }), 201


@bp.route('/api/v1/projects/<int:project_id>', methods=['PATCH'])
@login_required
def api_projects_update(project_id):
    """Update a project (status, etc.)."""
    project = Project.query.get_or_404(project_id)
    data = request.get_json() or {}
    
    # Check permissions
    if current_user.user_type == 'admin':
        # Admin can update status
        if 'status' in data:
            project.status = data['status']
    elif current_user.user_type == 'organization' and project.organization_id == current_user.id:
        # Organization can update their own projects (but not status to approved/rejected)
        if 'status' in data and data['status'] in ('approved', 'rejected'):
            return jsonify({'error': 'Cannot change status to approved/rejected'}), 403
        # Allow other updates
        for key in ['title', 'description', 'category', 'location', 'max_participants', 'duration', 'points', 'requirements']:
            if key in data:
                setattr(project, key, data[key])
    else:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.commit()
    return jsonify({
        'id': project.id,
        'status': project.status,
        'message': 'Project updated successfully'
    })

