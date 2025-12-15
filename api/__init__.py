"""API package - registers all API and view blueprints."""
from flask import Flask

from utils.auth import bp as auth_bp
from api.views import bp as views_bp
from api.api_projects import bp as api_projects_bp
from api.api_registrations import bp as api_registrations_bp
from api.api_records import bp as api_records_bp
from api.api_users import bp as api_users_bp
from api.api_comments import bp as api_comments_bp
from api.api_admin import bp as api_admin_bp
from api.api_dashboard import bp as api_dashboard_bp


def register_blueprints(app: Flask) -> None:
    """Register all blueprints with the Flask application."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(views_bp)
    app.register_blueprint(api_projects_bp)
    app.register_blueprint(api_registrations_bp)
    app.register_blueprint(api_records_bp)
    app.register_blueprint(api_users_bp)
    app.register_blueprint(api_comments_bp)
    app.register_blueprint(api_admin_bp)
    app.register_blueprint(api_dashboard_bp)













