"""Users API routes."""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user, logout_user
from datetime import datetime, timedelta

from models import db, User, Registration, VolunteerRecord, UserBadge, Notification, Comment, Project

bp = Blueprint('api_users', __name__)


@bp.route('/api/v1/users', methods=['GET'])
@login_required
def api_users_list():
    """
    Get users list.
    Only accessible by admins.
    Excludes other admin users to prevent accidental modification of peer admins in this basic view.
    """
    if current_user.user_type != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Retrieve non-admin users, ordered by creation date desc
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
            'ban_reason': getattr(u, 'ban_reason', None),
            'ban_until': u.ban_until.isoformat() if getattr(u, 'ban_until', None) else None,
            'created_at': u.created_at.strftime('%Y-%m-%d') if u.created_at else None
        })
    
    return jsonify(result)


@bp.route('/api/v1/users', methods=['POST'])
@login_required
def api_create_admin():
    """
    Create a new administrator account.
    Only accessible by existing admins.
    """
    if current_user.user_type != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json() or {}
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({'error': 'Username, email and password are required'}), 400
        
    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({'error': 'User already exists'}), 400
        
    new_admin = User(
        username=username, 
        email=email, 
        user_type='admin',
        display_name=data.get('display_name', username)
    )
    new_admin.set_password(password)
    
    # Set active by default
    if hasattr(new_admin, 'is_active'):
        new_admin.is_active = True
        
    db.session.add(new_admin)
    db.session.commit()
    
    return jsonify({'message': 'Admin user created successfully', 'id': new_admin.id}), 201


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
        'ban_reason': getattr(current_user, 'ban_reason', None),
        'ban_until': current_user.ban_until.isoformat() if getattr(current_user, 'ban_until', None) else None,
        'created_at': current_user.created_at.strftime('%Y-%m-%d') if current_user.created_at else None
    })


@bp.route('/api/v1/users/<int:user_id>', methods=['GET'])
@login_required
def api_user_detail(user_id):
    """Get a single user details."""
    user = User.query.get_or_404(user_id)
    
    # Permission check: Users can only view themselves unless they are admin
    # Exception: basic profile info might be public in future, but for now restricted.
    if current_user.user_type != 'admin':
        if current_user.id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'display_name': user.display_name,
        'email': user.email,
        'user_type': user.user_type,
        'is_active': user.is_active if hasattr(user, 'is_active') else True,
        'ban_reason': getattr(user, 'ban_reason', None),
        'ban_until': user.ban_until.isoformat() if getattr(user, 'ban_until', None) else None,
        'created_at': user.created_at.strftime('%Y-%m-%d') if user.created_at else None
    })


@bp.route('/api/v1/users/<int:user_id>', methods=['PATCH'])
@login_required
def api_user_update(user_id):
    """
    Update a user.
    - Admins can update status (ban/unban).
    - Users can update their own display name or description.
    """
    user = User.query.get_or_404(user_id)
    data = request.get_json() or {}
    
    # Prevent modifying admin users via this API (safety measure)
    if user.user_type == 'admin':
        return jsonify({'error': 'Cannot modify admin user via this endpoint'}), 403
    
    # Admin Logic
    if current_user.user_type == 'admin':
        # Admin can update is_active with ban details
        if 'is_active' in data:
            if hasattr(user, 'is_active'):
                user.is_active = bool(data['is_active'])
                
                if not user.is_active:
                    # Setting ban - capture reason and duration
                    user.ban_reason = data.get('ban_reason', 'Violated community guidelines')
                    ban_hours = data.get('ban_hours', 0)  # 0 = permanent
                    if ban_hours and int(ban_hours) > 0:
                        user.ban_until = datetime.utcnow() + timedelta(hours=int(ban_hours))
                    else:
                        user.ban_until = None  # Permanent ban
                else:
                    # Unbanning - clear ban fields
                    user.ban_reason = None
                    user.ban_until = None
            else:
                return jsonify({'error': 'User status feature not available.'}), 500
    
    # Self-Update Logic
    elif current_user.id == user_id:
        if 'is_active' in data:
            return jsonify({'error': 'Cannot modify your own status'}), 403
        
        # Allow profile fields update
        for key in ['display_name', 'description']:
            if key in data:
                setattr(user, key, data[key])
    else:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.commit()
    
    return jsonify({
        'id': user.id,
        'is_active': user.is_active if hasattr(user, 'is_active') else True,
        'ban_reason': getattr(user, 'ban_reason', None),
        'ban_until': user.ban_until.isoformat() if getattr(user, 'ban_until', None) else None,
        'message': 'User updated successfully'
    })


@bp.route('/api/v1/users/me', methods=['DELETE'])
@login_required
def api_user_delete_self():
    """Delete current user's account and all associated data."""
    return _delete_user(current_user)


@bp.route('/api/v1/users/<int:user_id>', methods=['DELETE'])
@login_required
def api_user_delete_admin(user_id):
    """
    Admin endpoint to delete any user account.
    """
    if current_user.user_type != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    user = User.query.get_or_404(user_id)
    if user.user_type == 'admin':
        return jsonify({'error': 'Cannot delete admin users'}), 403
        
    return _delete_user(user, is_admin_action=True)


def _delete_user(user, is_admin_action=False):
    """Helper function to perform user deletion logic."""
    user_id = user.id
    
    # For organizations, check if they have projects
    if user.user_type == 'organization':
        project_count = Project.query.filter_by(organization_id=user_id).count()
        if project_count > 0:
            return jsonify({
                'error': f'Cannot delete account: User has {project_count} project(s). Please delete or transfer projects first.'
            }), 400
    
    # Cascade delete all associated data
    try:
        Comment.query.filter_by(user_id=user_id).delete()
        Notification.query.filter_by(user_id=user_id).delete()
        UserBadge.query.filter_by(user_id=user_id).delete()
        VolunteerRecord.query.filter_by(user_id=user_id).delete()
        Registration.query.filter_by(user_id=user_id).delete()
        
        # If user is deleting themselves, logout first
        if not is_admin_action:
            logout_user()
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'message': 'Account deleted successfully',
            'redirect': '/' if not is_admin_action else None
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete user: {str(e)}'}), 500
