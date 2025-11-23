"""Users API routes."""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from models import db, User

bp = Blueprint('api_users', __name__)


@bp.route('/api/v1/users', methods=['GET'])
@login_required
def api_users_list():
    """Get users list (admin only, excludes admin users)."""
    if current_user.user_type != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Exclude admin users
    users = User.query.filter(User.user_type != 'admin').order_by(User.created_at.desc()).limit(100).all()
    
    result = []
    for u in users:
        result.append({
            'id': u.id,
            'username': u.username,
            'display_name': u.display_name,
            'email': u.email,
            'user_type': u.user_type,
            'is_active': u.is_active if hasattr(u, 'is_active') else True,
            'created_at': u.created_at.strftime('%Y-%m-%d') if u.created_at else None
        })
    
    return jsonify(result)


@bp.route('/api/v1/users/me', methods=['GET'])
@login_required
def api_users_me():
    """Get current user information."""
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'display_name': current_user.display_name,
        'email': current_user.email,
        'user_type': current_user.user_type,
        'is_active': current_user.is_active if hasattr(current_user, 'is_active') else True,
        'created_at': current_user.created_at.strftime('%Y-%m-%d') if current_user.created_at else None
    })


@bp.route('/api/v1/users/<int:user_id>', methods=['GET'])
@login_required
def api_user_detail(user_id):
    """Get a single user."""
    user = User.query.get_or_404(user_id)
    
    # Check permissions
    if current_user.user_type == 'participant' and current_user.id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    elif current_user.user_type == 'organization' and current_user.id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'display_name': user.display_name,
        'email': user.email,
        'user_type': user.user_type,
        'is_active': user.is_active if hasattr(user, 'is_active') else True,
        'created_at': user.created_at.strftime('%Y-%m-%d') if user.created_at else None
    })


@bp.route('/api/v1/users/<int:user_id>', methods=['PATCH'])
@login_required
def api_user_update(user_id):
    """Update a user (admin only for status changes)."""
    user = User.query.get_or_404(user_id)
    data = request.get_json() or {}
    
    # Prevent modifying admin users
    if user.user_type == 'admin':
        return jsonify({'error': 'Cannot modify admin user'}), 403
    
    # Check permissions
    if current_user.user_type == 'admin':
        # Admin can update is_active
        if 'is_active' in data:
            if hasattr(user, 'is_active'):
                user.is_active = bool(data['is_active'])
            else:
                return jsonify({'error': 'User status feature not available. Database migration required.'}), 500
    elif current_user.id == user_id:
        # Users can update their own profile (but not is_active)
        if 'is_active' in data:
            return jsonify({'error': 'Cannot modify your own status'}), 403
        # Allow other profile updates
        for key in ['display_name', 'description']:
            if key in data:
                setattr(user, key, data[key])
    else:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.commit()
    
    return jsonify({
        'id': user.id,
        'is_active': user.is_active if hasattr(user, 'is_active') else True,
        'message': 'User updated successfully'
    })

