"""Volunteer Records API routes."""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from models import db, Project, VolunteerRecord

bp = Blueprint('api_records', __name__)


@bp.route('/api/v1/records', methods=['GET'])
@login_required
def api_records_list():
    """Get volunteer records."""
    # Support query parameters
    status = request.args.get('status')
    user_id = request.args.get('user_id', type=int)
    
    query = VolunteerRecord.query
    
    # Permission checks
    if current_user.user_type == 'participant':
        # Participants can only see their own records
        query = query.filter_by(user_id=current_user.id)
    elif current_user.user_type == 'organization':
        # Organizations can see records for their projects
        query = query.join(Project).filter(Project.organization_id == current_user.id)
    elif current_user.user_type != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    if status:
        query = query.filter_by(status=status)
    if user_id and current_user.user_type == 'admin':
        query = query.filter_by(user_id=user_id)
    
    records = query.order_by(VolunteerRecord.completed_at.desc()).all()
    
    result = []
    for record in records:
        project = record.project
        participant = record.user
        organization = project.organization if project else None
        
        result.append({
            'id': record.id,
            'user_id': record.user_id,
            'project_id': record.project_id,
            'hours': record.hours,
            'points': record.points,
            'status': record.status,
            'completed_at': record.completed_at.strftime('%Y-%m-%d') if record.completed_at else None,
            'project': {
                'id': project.id,
                'title': project.title,
                'category': project.category
            } if project else None,
            'participant': {
                'id': participant.id,
                'name': participant.display_name or participant.username
            } if participant else None,
            'organization': {
                'id': organization.id,
                'name': organization.display_name or organization.username
            } if organization else None
        })
    
    return jsonify(result)


@bp.route('/api/v1/records/<int:record_id>', methods=['GET'])
@login_required
def api_record_detail(record_id):
    """Get a single volunteer record."""
    record = VolunteerRecord.query.get_or_404(record_id)
    
    # Check permissions
    if current_user.user_type == 'participant' and record.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    elif current_user.user_type == 'organization':
        project = record.project
        if not project or project.organization_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
    
    project = record.project
    participant = record.user
    organization = project.organization if project else None
    
    return jsonify({
        'id': record.id,
        'user_id': record.user_id,
        'project_id': record.project_id,
        'hours': record.hours,
        'points': record.points,
        'status': record.status,
        'completed_at': record.completed_at.strftime('%Y-%m-%d') if record.completed_at else None,
        'project': {
            'id': project.id,
            'title': project.title,
            'category': project.category
        } if project else None,
        'participant': {
            'id': participant.id,
            'name': participant.display_name or participant.username,
            'email': participant.email
        } if participant else None,
        'organization': {
            'id': organization.id,
            'name': organization.display_name or organization.username
        } if organization else None
    })


@bp.route('/api/v1/records/<int:record_id>', methods=['PATCH'])
@login_required
def api_record_update(record_id):
    """Update a volunteer record (status)."""
    if current_user.user_type != 'admin':
        return jsonify({'error': 'Only admins can update records'}), 403
    
    record = VolunteerRecord.query.get_or_404(record_id)
    data = request.get_json() or {}
    
    if 'status' in data:
        allowed_statuses = {'pending', 'approved', 'rejected'}
        if data['status'] not in allowed_statuses:
            return jsonify({'error': 'Invalid status'}), 400
        record.status = data['status']
    
    db.session.commit()
    return jsonify({
        'id': record.id,
        'status': record.status,
        'message': 'Record updated successfully'
    })


@bp.route('/api/v1/records/batch', methods=['PATCH'])
@login_required
def api_records_batch_update():
    """Batch update volunteer records."""
    if current_user.user_type != 'admin':
        return jsonify({'error': 'Only admins can batch update records'}), 403
    
    data = request.get_json() or {}
    record_ids = data.get('record_ids', [])
    new_status = data.get('status')
    
    if not record_ids:
        return jsonify({'error': 'No record IDs provided'}), 400
    
    if not isinstance(record_ids, list):
        return jsonify({'error': 'record_ids must be a list'}), 400
    
    if new_status not in ('pending', 'approved', 'rejected'):
        return jsonify({'error': 'Invalid status'}), 400
    
    # Get all records that match the IDs and are pending (for approve action)
    if new_status == 'approved':
        records = VolunteerRecord.query.filter(
            VolunteerRecord.id.in_(record_ids),
            VolunteerRecord.status == 'pending'
        ).all()
    else:
        records = VolunteerRecord.query.filter(VolunteerRecord.id.in_(record_ids)).all()
    
    if not records:
        return jsonify({'error': 'No records found'}), 404
    
    # Update all records
    updated_count = 0
    for record in records:
        record.status = new_status
        updated_count += 1
    
    db.session.commit()
    
    return jsonify({
        'updated_count': updated_count,
        'total_requested': len(record_ids),
        'status': new_status,
        'message': f'Successfully updated {updated_count} record(s)'
    })

