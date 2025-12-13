# Flask Backend for Sustainable Volunteer Service Platform

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
from models import db, User, Project, Badge, UserBadge, Registration, VolunteerRecord, SystemSettings, Comment, Notification
from sqlalchemy import text
from datetime import date, datetime

# Import blueprints
from api import register_blueprints

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Initialize Flask-Migrate
migrate = Migrate()


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return User.query.get(int(user_id))


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    register_blueprints(app)

    # Logging Configuration
    # Ensure logs directory exists
    if not os.path.exists('logs'):
        os.mkdir('logs')

    # Configure File Handler for Logging
    file_handler = RotatingFileHandler(
        app.config.get('LOG_FILE', 'logs/app.log'), 
        maxBytes=102400, 
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    # Set log level based on config
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper(), logging.INFO)
    file_handler.setLevel(log_level)
    
    app.logger.addHandler(file_handler)
    app.logger.setLevel(log_level)
    app.logger.info('Sustainability Volunteer Service startup')

    # Ensure logs show up in console even when debug is off (e.g. for container logs)
    try:
        if not app.debug:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(log_level)
            app.logger.addHandler(stream_handler)
    except Exception:
        pass

    # Improve SQLite concurrency
    with app.app_context():
        try:
            db.session.execute(text("PRAGMA journal_mode=WAL;"))
            db.session.execute(text("PRAGMA busy_timeout=30000;"))
            db.session.commit()
        except Exception:
            db.session.rollback()

    # Initialize database and seed admin/data
    init_db(app)

    return app


def init_db(app: Flask) -> None:
    """Initialize the database schema and seed initial data."""
    with app.app_context():
        db.create_all()

        # Initialize default system settings if they don't exist
        if not SystemSettings.query.filter_by(key='points_per_hour').first():
            SystemSettings.set_setting('points_per_hour', '20')
        if not SystemSettings.query.filter_by(key='auto_approve_under_hours').first():
            SystemSettings.set_setting('auto_approve_under_hours', 'false')
        if not SystemSettings.query.filter_by(key='project_requires_review').first():
            SystemSettings.set_setting('project_requires_review', 'true')

        # Create admin user if it doesn't exist
        # Security: Read credentials from environment variables to avoid hardcoded secrets
        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        admin = User.query.filter_by(username=admin_username).first()
        
        if not admin:
            admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
            admin_password = os.environ.get('ADMIN_PASSWORD')
            
            # SECURITY: If no password in env, generate a secure random one
            if not admin_password:
                import secrets
                import string
                alphabet = string.ascii_letters + string.digits + "!@#$%"
                admin_password = ''.join(secrets.choice(alphabet) for _ in range(16))
                app.logger.warning("=" * 60)
                app.logger.warning("SECURITY WARNING: No ADMIN_PASSWORD set in environment!")
                app.logger.warning(f"Generated temporary admin password: {admin_password}")
                app.logger.warning("Please set ADMIN_PASSWORD environment variable in production!")
                app.logger.warning("=" * 60)
                print("=" * 60)
                print(f"ADMIN PASSWORD (save this!): {admin_password}")
                print("=" * 60)
            
            admin = User(username=admin_username, email=admin_email, user_type='admin')
            admin.set_password(admin_password)
            
            # Set is_active for new admin user
            if hasattr(admin, 'is_active'):
                admin.is_active = True
                
            db.session.add(admin)
            db.session.commit()
            app.logger.info(f"Admin user '{admin_username}' created.")

        # Seed sample data only if explicitly requested or if database seems empty/dev mode
        # For this demo, we check if any projects exist
        if Project.query.count() == 0:
            seed_sample_data(app)

def seed_sample_data(app: Flask) -> None:
    """Populate the database with initial sample data for demonstration purposes."""
    
    app.logger.info("Seeding sample data...")
    
    # Remove existing data to ensure clean state for demo
    # Note: In production, one should be very careful with this!
    Registration.query.delete()
    VolunteerRecord.query.delete()
    UserBadge.query.delete()
    Comment.query.delete()
    db.session.commit()
    
    # Helper utilities to fetch or create users
    def _get_or_create_user(username: str, email: str, user_type: str, display_name: str = None) -> User:
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(
                username=username,
                email=email,
                user_type=user_type,
                display_name=display_name or username
            )
            # Use environment variable or simple default for demo users
            # Note: Demo users always have same simple password for ease of testing
            user.set_password('Volunteer123!' if user_type == 'participant' else 'OrgPass123!')
            db.session.add(user)
            db.session.commit()
        return user
    
    def _get_or_create_project(title: str, org_user: User, **kwargs) -> Project:
        project = Project.query.filter_by(title=title).first()
        if not project:
            project = Project(
                title=title,
                organization_id=org_user.id,
                status='approved',
                **kwargs
            )
            db.session.add(project)
            db.session.commit()
        else:
            if 'status' in kwargs and kwargs['status'] == 'approved':
                project.status = 'approved'
                db.session.add(project)
                db.session.commit()
        return project
    
    # Create sample users
    greenearth = _get_or_create_user("greenearth", "contact@greenearth.org", "organization", "Green Earth Environmental")
    emma = _get_or_create_user("emma", "emma@example.com", "participant", "Emma Wilson")
    
    # Create sample projects covering various states
    projects = {
        "pending_project": _get_or_create_project(
            "Community Garden Initiative", greenearth,
            date=date(2025, 12, 1), location="Community Center",
            category="Environmental", description="Establish a community garden to promote sustainable living and local food production.",
            max_participants=15, duration=6.0, points=100, rating=0.0,
            requirements="Interest in gardening and sustainable practices."
        ),
        "registered_project": _get_or_create_project(
            "Beach Cleanup Action", greenearth,
            date=date(2025, 12, 5), location="Golden Coast",
            category="Environmental", description="Join a community effort to remove debris from the shoreline and protect marine ecosystems.",
            max_participants=25, duration=4.5, points=70, rating=4.6,
            requirements="Able to walk on sandy terrain and handle cleanup tools."
        ),
        "approved_registration_project": _get_or_create_project(
            "River Conservation Program", greenearth,
            date=date(2025, 12, 8), location="Riverside Park",
            category="Environmental", description="Monitor water quality and clean up riverbanks to protect aquatic ecosystems.",
            max_participants=20, duration=5.0, points=75, rating=4.7,
            requirements="Comfortable working near water and able to use testing equipment."
        ),
        "cancelled_registration_project": _get_or_create_project(
            "Wildlife Habitat Restoration", greenearth,
            date=date(2025, 12, 12), location="Nature Reserve",
            category="Environmental", description="Restore native habitats and create safe spaces for local wildlife.",
            max_participants=18, duration=4.0, points=65, rating=4.5,
            requirements="Physical fitness and respect for wildlife."
        ),
        "rejected_project": _get_or_create_project(
            "Night Market Setup", greenearth,
            date=date(2025, 12, 10), location="Downtown Square",
            category="Education", description="Help set up and manage a community night market event.",
            max_participants=20, duration=5.0, points=80, rating=0.0,
            requirements="Available in evenings and able to lift moderate weights."
        ),
        "completed_project": _get_or_create_project(
            "Urban Greening Planting Project", greenearth,
            date=date(2025, 11, 20), location="City Park",
            category="Environmental", description="Plant native trees and shrubs to improve urban biodiversity and air quality.",
            max_participants=30, duration=5.0, points=90, rating=4.9,
            requirements="Comfortable with outdoor manual work for several hours."
        ),
        "approved_record_project": _get_or_create_project(
            "Community Book Donation", greenearth,
            date=date(2025, 11, 25), location="Civic Center",
            category="Education", description="Organize and catalog donated books before delivering them to local community centers.",
            max_participants=12, duration=3.5, points=55, rating=4.3,
            requirements="Attention to detail and ability to lift small boxes."
        ),
    }
    
    # Set statuses explicitly
    projects["registered_project"].status = 'approved'
    projects["approved_registration_project"].status = 'approved'
    projects["cancelled_registration_project"].status = 'approved'
    projects["approved_record_project"].status = 'approved'
    projects["pending_project"].status = 'pending'
    projects["rejected_project"].status = 'rejected'
    projects["completed_project"].status = 'completed'
    
    db.session.commit()
    
    # Seed registrations
    registrations = [
        (emma, projects["registered_project"], "registered"),
        (emma, projects["approved_registration_project"], "approved"),
        (emma, projects["cancelled_registration_project"], "cancelled"),
        (emma, projects["completed_project"], "completed"),
    ]
    
    for user, proj, status in registrations:
        existing = Registration.query.filter_by(
            user_id=user.id, project_id=proj.id, status=status).first()
        if not existing:
            reg = Registration(
                user_id=user.id, project_id=proj.id, status=status,
                created_at=datetime.utcnow()
            )
            db.session.add(reg)
    
    db.session.commit()
    
    # Create records for completed projects
    completed_regs = Registration.query.filter_by(status='completed').all()
    for reg in completed_regs:
        existing = VolunteerRecord.query.filter_by(user_id=reg.user_id, project_id=reg.project_id).first()
        if not existing:
            project = reg.project
            record = VolunteerRecord(
                user_id=reg.user_id,
                project_id=reg.project_id,
                hours=project.duration,
                points=project.points,
                status='pending',
                completed_at=datetime.utcnow()
            )
            db.session.add(record)
    
    # Seed historical records
    if not VolunteerRecord.query.filter_by(user_id=emma.id, project_id=projects["approved_record_project"].id).first():
        record = VolunteerRecord(
            user_id=emma.id,
            project_id=projects["approved_record_project"].id,
            hours=3.5,
            points=55,
            status='approved',
            completed_at=datetime.utcnow()
        )
        db.session.add(record)
    
    db.session.commit()
    
    # Seed Badges
    badge_definitions = [
        {"code": "rising-star", "name": "Rising Star", "description": "Complete first volunteer service", "accent_color": "var(--accent-yellow)", "background_color": "#fef3c7", "icon": "star"},
        {"code": "eco-pioneer", "name": "Eco Pioneer", "description": "Complete 50 hours of environmental service", "accent_color": "var(--primary-green)", "background_color": "#dcfce7", "icon": "leaf"},
        {"code": "compassion", "name": "Compassion Ambassador", "description": "Volunteer for 6 consecutive months", "accent_color": "var(--gray-500)", "background_color": "#f3f4f6", "icon": "heart"},
        {"code": "public-welfare", "name": "Public Welfare Expert", "description": "Complete 100 hours of service", "accent_color": "var(--gray-500)", "background_color": "#f3f4f6", "icon": "medal"},
        {"code": "team-leader", "name": "Team Leader", "description": "Organize 10 volunteer activities", "accent_color": "var(--gray-500)", "background_color": "#f3f4f6", "icon": "leader"}
    ]
    
    badges_map = {}
    for definition in badge_definitions:
        badge = Badge.query.filter_by(code=definition["code"]).first()
        if not badge:
            badge = Badge(**definition)
            db.session.add(badge)
        badges_map[definition['code']] = badge
    db.session.commit()
    
    # Assign badges
    if emma:
        earned_badges = ["rising-star", "eco-pioneer"]
        for code, badge_obj in badges_map.items():
            if not badge_obj.id: continue # Should be committed
            
            earned = code in earned_badges
            ub = UserBadge.query.filter_by(user_id=emma.id, badge_id=badge_obj.id).first()
            if not ub:
                ub = UserBadge(
                    user_id=emma.id,
                    badge_id=badge_obj.id,
                    earned=earned,
                    earned_at=datetime.utcnow() if earned else None,
                    progress=100.0 if earned else 0.0
                )
                db.session.add(ub)
    
    db.session.commit()
    app.logger.info("Sample data seeded successfully.")

# Expose app for CLI
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
