"""Volunteer Records API routes."""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, send_file, current_app
from flask_login import login_required, current_user
import logging

from models import db, Project, VolunteerRecord
from utils import generate_excel_from_records

bp = Blueprint('api_records', __name__)
logger = logging.getLogger(__name__)


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
    
    old_status = record.status
    
    if 'status' in data:
        allowed_statuses = {'pending', 'approved', 'rejected'}
        if data['status'] not in allowed_statuses:
            return jsonify({'error': 'Invalid status'}), 400
        record.status = data['status']
    
    db.session.commit()
    current_app.logger.info(f'Record status updated id={record.id} from={old_status} to={record.status} by admin={current_user.id}')
    
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
    current_app.logger.info(f'Records batch updated count={updated_count} status={new_status} by admin={current_user.id}')
    
    return jsonify({
        'updated_count': updated_count,
        'total_requested': len(record_ids),
        'status': new_status,
        'message': f'Successfully updated {updated_count} record(s)'
    })


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

