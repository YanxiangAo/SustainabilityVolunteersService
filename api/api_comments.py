"""Comments API routes."""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from models import db, Project, Registration, Comment

bp = Blueprint('api_comments', __name__)


@bp.route('/api/v1/projects/<int:project_id>/comments', methods=['GET'])
def api_project_comments_list(project_id):
    """Get comments for a project."""
    project = Project.query.get_or_404(project_id)
    
    comments = Comment.query.filter_by(project_id=project_id).order_by(Comment.created_at.desc()).all()
    
    comments_data = []
    for comment in comments:
        comments_data.append({
            'id': comment.id,
            'user_id': comment.user_id,
            'user_name': comment.user.display_name or comment.user.username if comment.user else 'Unknown',
            'user_type': comment.user.user_type.title() if comment.user else 'Unknown',
            'comment': comment.content,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M') if comment.created_at else None
        })
    
    return jsonify(comments_data)


@bp.route('/api/v1/projects/<int:project_id>/comments', methods=['POST'])
@login_required
def api_project_comments_create(project_id):
    """Create a comment on a project."""
    # Admin users are not allowed to comment on projects
    if current_user.user_type == 'admin':
        return jsonify({'error': 'Admin users cannot comment on projects'}), 403
    
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    comment_text = data.get('comment', '').strip()
    
    if not comment_text:
        return jsonify({'error': 'Comment cannot be empty'}), 400
    
    # Check permissions: participants must be registered, organizations can comment on their own projects
    can_comment = False
    if current_user.user_type == 'participant':
        # Participant must be registered for the project
        registration = Registration.query.filter(
            Registration.user_id == current_user.id,
            Registration.project_id == project_id,
            Registration.status.in_(('registered', 'approved', 'completed'))
        ).first()
        can_comment = registration is not None
    elif current_user.user_type == 'organization':
        # Organization can comment on their own projects
        can_comment = (project.organization_id == current_user.id)
    
    if not can_comment:
        if current_user.user_type == 'participant':
            return jsonify({'error': 'You must be registered for this project to comment'}), 403
        else:
            return jsonify({'error': 'You can only comment on your own projects'}), 403
    
    # Create comment
    comment = Comment(
        project_id=project_id,
        user_id=current_user.id,
        content=comment_text
    )
    db.session.add(comment)
    db.session.commit()
    
    return jsonify({
        'id': comment.id,
        'project_id': project_id,
        'user_name': current_user.display_name or current_user.username,
        'user_type': current_user.user_type.title(),
        'comment': comment.content,
        'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M') if comment.created_at else None,
        'message': 'Comment posted successfully'
    }), 201

