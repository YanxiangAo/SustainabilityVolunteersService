"""Comments API routes."""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from models import db, Project, Registration, Comment, RegistrationStatus

bp = Blueprint('api_comments', __name__)


@bp.route('/api/v1/projects/<int:project_id>/comments', methods=['GET'])
def api_project_comments_list(project_id):
    """Get comments for a project."""
    project = Project.query.get_or_404(project_id)
    
    # Get all comments (including replies)
    comments = Comment.query.filter_by(project_id=project_id).order_by(Comment.created_at.desc()).all()
    
    # Build a dictionary of comments by ID for easy lookup
    comments_dict = {}
    root_comments = []
    
    for comment in comments:
        comment_data = {
            'id': comment.id,
            'user_id': comment.user_id,
            'user_name': comment.user.display_name or comment.user.username if comment.user else 'Unknown',
            'user_type': comment.user.user_type.title() if comment.user else 'Unknown',
            'comment': comment.content,
            'parent_id': comment.parent_id,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M') if comment.created_at else None,
            'replies': []
        }
        comments_dict[comment.id] = comment_data
        
        if comment.parent_id is None:
            root_comments.append(comment_data)
    
    # Attach replies to their parent comments
    for comment in comments:
        if comment.parent_id is not None and comment.parent_id in comments_dict:
            parent_data = comments_dict[comment.parent_id]
            parent_data['replies'].append(comments_dict[comment.id])
    
    # Sort replies by created_at (oldest first)
    for comment_data in comments_dict.values():
        comment_data['replies'].sort(key=lambda x: x['created_at'] or '')
    
    return jsonify(root_comments)


@bp.route('/api/v1/projects/<int:project_id>/comments', methods=['POST'])
@login_required
def api_project_comments_create(project_id):
    """Create a comment on a project (or reply to an existing comment)."""
    # Admin users are not allowed to comment on projects
    if current_user.user_type == 'admin':
        return jsonify({'error': 'Admin users cannot comment on projects'}), 403
    
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    comment_text = data.get('comment', '').strip()
    parent_id = data.get('parent_id', None)
    
    if not comment_text:
        return jsonify({'error': 'Comment cannot be empty'}), 400
    
    # If replying to a comment, verify the parent comment exists and belongs to the same project
    if parent_id is not None:
        parent_comment = Comment.query.get(parent_id)
        if not parent_comment:
            return jsonify({'error': 'Parent comment not found'}), 404
        if parent_comment.project_id != project_id:
            return jsonify({'error': 'Parent comment does not belong to this project'}), 400
    
    # Check permissions: participants must be registered, organizations can comment on their own projects
    can_comment = False
    if current_user.user_type == 'participant':
        # Participant must be registered for the project
        registration = Registration.query.filter(
            Registration.user_id == current_user.id,
            Registration.project_id == project_id,
            Registration.status.in_(
                (
                    RegistrationStatus.REGISTERED.value,
                    RegistrationStatus.APPROVED.value,
                    RegistrationStatus.COMPLETED.value,
                )
            ),
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
    
    # Create comment (or reply)
    comment = Comment(
        project_id=project_id,
        user_id=current_user.id,
        content=comment_text,
        parent_id=parent_id
    )
    db.session.add(comment)
    db.session.commit()
    
    return jsonify({
        'id': comment.id,
        'project_id': project_id,
        'user_name': current_user.display_name or current_user.username,
        'user_type': current_user.user_type.title(),
        'comment': comment.content,
        'parent_id': comment.parent_id,
        'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M') if comment.created_at else None,
        'message': 'Comment posted successfully'
    }), 201

