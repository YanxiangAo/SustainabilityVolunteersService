"""Page view routes (dashboards)."""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

bp = Blueprint('views', __name__)


@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/participant/dashboard')
@login_required
def participant_dashboard():
    if current_user.user_type != 'participant':
        return redirect(url_for('auth.login'))
    
    return render_template('participant_dashboard.html', user=current_user)


@bp.route('/organization/dashboard')
@login_required
def organization_dashboard():
    if current_user.user_type != 'organization':
        return redirect(url_for('auth.login'))
    
    return render_template('organization_dashboard.html', user=current_user)


@bp.route('/admin/panel')
@login_required
def admin_panel():
    if current_user.user_type != 'admin':
        return redirect(url_for('auth.login'))
    
    return render_template('admin_panel.html', user=current_user)



