"""Admin API routes (logs, dev helpers)."""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from models import User

bp = Blueprint('api_admin', __name__)

@bp.route('/api/v1/admin/logs', methods=['GET'])
@login_required
def api_get_logs():
    """
    Get application logs with pagination.
    Admin only endpoint for viewing server logs.
    Query params:
      - page: page number (1-based), default 1
      - page_size: items per page, default 100
      - level: optional level filter (INFO/WARNING/ERROR)
    """
    if current_user.user_type != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    import os
    from config import Config
    
    log_file = Config.LOG_FILE
    page = max(int(request.args.get('page', 1) or 1), 1)
    page_size = int(request.args.get('page_size', 100) or 100)
    if page_size <= 0:
        page_size = 100
    level_filter = request.args.get('level', '').upper()  # Optional: INFO, WARNING, ERROR
    
    # Ensure log file exists each startup (create empty if missing)
    if not os.path.exists(log_file):
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write('')
        except Exception as e:
            return jsonify({'error': f'Failed to create log file: {str(e)}'}), 500
    
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            all_lines = f.readlines()
        
        log_lines = all_lines
        # Filter by level if specified (simple substring match)
        if level_filter:
            log_lines = [line for line in log_lines if level_filter in line]

        # Newest first ordering
        log_lines = list(reversed(log_lines))

        total = len(log_lines)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        if page > total_pages:
            page = total_pages
        start = (page - 1) * page_size
        end = start + page_size
        page_lines = log_lines[start:end]

        return jsonify({
            'logs': page_lines,
            'page': page,
            'page_size': page_size,
            'total': total,
            'total_pages': total_pages,
            'original_total_lines': len(all_lines)
        })
    except Exception as e:
        return jsonify({'error': f'Failed to read logs: {str(e)}'}), 500
