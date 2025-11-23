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
    """Save system settings."""
    if current_user.user_type != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json() or {}
    
    # Save points per hour
    if 'points_per_hour' in data:
        points = int(data['points_per_hour'])
        if points < 1:
            return jsonify({'error': 'Points per hour must be at least 1'}), 400
        SystemSettings.set_setting('points_per_hour', points)
    
    # Save auto-approve setting
    if 'auto_approve_under_hours' in data:
        SystemSettings.set_setting('auto_approve_under_hours', str(data['auto_approve_under_hours']).lower())
    
    # Save project review requirement
    if 'project_requires_review' in data:
        SystemSettings.set_setting('project_requires_review', str(data['project_requires_review']).lower())
    
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

