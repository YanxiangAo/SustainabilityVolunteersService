"""Admin API routes (system settings, etc.)."""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from models import SystemSettings, User

bp = Blueprint('api_admin', __name__)


@bp.route('/api/v1/admin/settings', methods=['GET'])
@login_required
def api_get_settings():
    """Get system settings."""
    if current_user.user_type != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    settings = {
        'points_per_hour': SystemSettings.get_setting('points_per_hour', '20'),
        'auto_approve_under_hours': SystemSettings.get_setting('auto_approve_under_hours', 'false'),
        'project_requires_review': SystemSettings.get_setting('project_requires_review', 'true')
    }
    
    return jsonify(settings)


@bp.route('/api/v1/admin/settings', methods=['POST'])
@login_required
def api_save_settings():
    """
    Save system settings.
    Validates all input values before saving.
    Admin only endpoint.
    """
    if current_user.user_type != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json() or {}
    
    # Validate and save points per hour
    if 'points_per_hour' in data:
        try:
            points = int(data['points_per_hour'])
            if points < 1:
                return jsonify({'error': 'Points per hour must be at least 1'}), 400
            if points > 1000:
                return jsonify({'error': 'Points per hour cannot exceed 1000'}), 400
            SystemSettings.set_setting('points_per_hour', str(points))
        except (TypeError, ValueError):
            return jsonify({'error': 'Points per hour must be a valid number'}), 400
    
    # Validate and save auto-approve setting (must be boolean-like)
    if 'auto_approve_under_hours' in data:
        value = data['auto_approve_under_hours']
        if not isinstance(value, bool) and str(value).lower() not in ('true', 'false'):
            return jsonify({'error': 'auto_approve_under_hours must be true or false'}), 400
        SystemSettings.set_setting('auto_approve_under_hours', str(value).lower())
    
    # Validate and save project review requirement (must be boolean-like)
    if 'project_requires_review' in data:
        value = data['project_requires_review']
        if not isinstance(value, bool) and str(value).lower() not in ('true', 'false'):
            return jsonify({'error': 'project_requires_review must be true or false'}), 400
        SystemSettings.set_setting('project_requires_review', str(value).lower())
    
    return jsonify({
        'message': 'Settings saved successfully',
        'settings': {
            'points_per_hour': SystemSettings.get_setting('points_per_hour', '20'),
            'auto_approve_under_hours': SystemSettings.get_setting('auto_approve_under_hours', 'false'),
            'project_requires_review': SystemSettings.get_setting('project_requires_review', 'true')
        }
    })


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


@bp.route('/api/v1/admin/logs', methods=['GET'])
@login_required
def api_get_logs():
    """
    Get application logs.
    Admin only endpoint for viewing server logs.
    """
    if current_user.user_type != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    import os
    from config import Config
    
    log_file = Config.LOG_FILE
    lines = int(request.args.get('lines', 100))  # Default to last 100 lines
    level_filter = request.args.get('level', '').upper()  # Optional: INFO, WARNING, ERROR
    
    if not os.path.exists(log_file):
        return jsonify({
            'logs': [],
            'message': 'No log file found. Logs will appear after server activity.'
        })
    
    try:
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
        
        # Get last N lines
        log_lines = all_lines[-lines:]
        
        # Filter by level if specified
        if level_filter:
            log_lines = [line for line in log_lines if level_filter in line]
        
        return jsonify({
            'logs': log_lines,
            'total_lines': len(all_lines),
            'showing': len(log_lines)
        })
    except Exception as e:
        return jsonify({'error': f'Failed to read logs: {str(e)}'}), 500
