"""Notifications API routes."""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from models import db, Notification, User

bp = Blueprint('api_notifications', __name__)


def create_notification(user_id, notification_type, title, message):
    """Helper function to create a notification for a user."""
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        message=message
    )
    db.session.add(notification)
    db.session.commit()
    return notification


@bp.route('/api/v1/notifications', methods=['GET'])
@login_required
def api_notifications_list():
    """Get current user's notifications."""
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc()).limit(50).all()
    
    result = []
    for n in notifications:
        result.append({
            'id': n.id,
            'type': n.type,
            'title': n.title,
            'message': n.message,
            'is_read': n.is_read,
            'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S') if n.created_at else None
        })
    
    return jsonify({
        'notifications': result,
        'unread_count': sum(1 for n in notifications if not n.is_read)
    })


@bp.route('/api/v1/notifications/<int:notification_id>', methods=['PATCH'])
@login_required
def api_notification_update(notification_id):
    """Mark notification as read."""
    notification = Notification.query.get_or_404(notification_id)
    
    # Check permission
    if notification.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json() or {}
    if 'is_read' in data:
        notification.is_read = bool(data['is_read'])
    
    db.session.commit()
    
    return jsonify({
        'id': notification.id,
        'is_read': notification.is_read,
        'message': 'Notification updated'
    })


@bp.route('/api/v1/notifications/<int:notification_id>', methods=['DELETE'])
@login_required
def api_notification_delete(notification_id):
    """Delete a notification."""
    notification = Notification.query.get_or_404(notification_id)
    
    # Check permission
    if notification.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(notification)
    db.session.commit()
    
    return jsonify({'message': 'Notification deleted'})


@bp.route('/api/v1/notifications/mark-all-read', methods=['POST'])
@login_required
def api_notifications_mark_all_read():
    """Mark all notifications as read for current user."""
    Notification.query.filter_by(user_id=current_user.id, is_read=False)\
        .update({'is_read': True})
    db.session.commit()
    
    return jsonify({'message': 'All notifications marked as read'})


@bp.route('/api/v1/admin/notifications/broadcast', methods=['POST'])
@login_required
def api_admin_broadcast_notification():
    """Admin broadcast notification to all users or specific user types."""
    if current_user.user_type != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    message = data.get('message', '').strip()
    target_type = data.get('target_type', 'all')  # all, participant, organization
    
    if not title or not message:
        return jsonify({'error': 'Title and message are required'}), 400
    
    # Get target users
    if target_type == 'all':
        users = User.query.filter(User.user_type != 'admin').all()
    elif target_type in ('participant', 'organization'):
        users = User.query.filter_by(user_type=target_type).all()
    else:
        return jsonify({'error': 'Invalid target type'}), 400
    
    # Create notifications for all target users
    count = 0
    for user in users:
        notification = Notification(
            user_id=user.id,
            type='system',
            title=title,
            message=message
        )
        db.session.add(notification)
        count += 1
    
    db.session.commit()
    
    return jsonify({
        'message': f'Notification sent to {count} users',
        'count': count
    })
