# Flask Backend for Sustainable Volunteer Service Platform

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import text
from datetime import date, datetime, timedelta
from models import (
    db,
    User,
    Project,
    Registration,
    VolunteerRecord,
    Comment,
    ProjectStatus,
    RegistrationStatus,
    VolunteerRecordStatus,
)

# Load environment variables early so Config picks them up (supports .env files)
# Use project-root .env even if the working directory differs (e.g., gunicorn/IDE)
_DOTENV_PATH = find_dotenv()
load_dotenv(_DOTENV_PATH)
from config import Config

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

        # Create admin user if it doesn't exist
        # Security: Read credentials from environment variables to avoid hardcoded secrets
        admin_username = app.config.get('ADMIN_USERNAME', 'admin')
        admin = User.query.filter_by(username=admin_username).first()
        
        if not admin:
            admin_email = app.config.get('ADMIN_EMAIL', 'admin@example.com')
            admin_password = app.config.get('ADMIN_PASSWORD', 'admin123') or 'admin123'
            if admin_password == 'admin123':
                app.logger.warning("Using default admin password; override via ADMIN_PASSWORD.")
            
            admin = User(username=admin_username, email=admin_email, user_type='admin')
            admin.set_password(admin_password)
            
            # Set is_active for new admin user
            if hasattr(admin, 'is_active'):
                admin.is_active = True
                
            db.session.add(admin)
            db.session.commit()
            app.logger.info(f"Admin user '{admin_username}' created.")

        # Seed sample data
        # Optionally seed sample data
        if app.config.get('SEED_SAMPLE_DATA', True):
            seed_sample_data(app)
            update_project_dates(app)
        else:
            app.logger.info("SEED_SAMPLE_DATA disabled; skipping demo data seeding.")

def update_project_dates(app: Flask) -> None:
    """Update existing project dates to future dates so they're visible on homepage."""
    today = datetime.utcnow().date()
    projects = Project.query.all()
    
    for i, project in enumerate(projects):
        # Update approved projects to future dates
        if project.status in (
            ProjectStatus.APPROVED.value,
            ProjectStatus.IN_PROGRESS.value,
        ):
            # Set dates to 15-30 days in the future
            days_offset = 15 + (i % 16)  # Distribute dates between 15-30 days
            project.date = today + timedelta(days=days_offset)
            db.session.add(project)
            app.logger.info(f"Updated project '{project.title}' date to {project.date}")
    
    db.session.commit()
    app.logger.info(f"Updated {len(projects)} project dates")


def seed_sample_data(app: Flask) -> None:
    """Populate the database with initial sample data for demonstration purposes."""
    
    app.logger.info("Seeding sample data...")
    
    # Remove existing data to ensure clean state for demo
    # Note: In production, one should be very careful with this!
    Registration.query.delete()
    VolunteerRecord.query.delete()
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
            # Update project fields if provided
            if 'status' in kwargs:
                project.status = kwargs['status']
            if 'date' in kwargs:
                project.date = kwargs['date']
            if 'location' in kwargs:
                project.location = kwargs['location']
            if 'category' in kwargs:
                project.category = kwargs['category']
            if 'description' in kwargs:
                project.description = kwargs['description']
            if 'max_participants' in kwargs:
                project.max_participants = kwargs['max_participants']
            if 'duration' in kwargs:
                project.duration = kwargs['duration']
            if 'points' in kwargs:
                project.points = kwargs['points']
            if 'rating' in kwargs:
                project.rating = kwargs['rating']
            if 'requirements' in kwargs:
                project.requirements = kwargs['requirements']
                db.session.add(project)
                db.session.commit()
        return project
    
    # Keep three accounts: admin (created earlier), one org, one participant
    greenearth = _get_or_create_user("greenearth", "contact@greenearth.org", "organization", "Green Earth Environmental")
    emma = _get_or_create_user("emma", "emma@example.com", "participant", "Emma Wilson")
    admin_user = User.query.filter_by(user_type='admin').first()
    
    # Create sample projects covering various states
    # Use future dates for active projects and past dates for completed ones
    today = datetime.utcnow().date()
    projects = {
        "pending_project": _get_or_create_project(
            "Community Garden Initiative", greenearth,
            date=today + timedelta(days=30), location="Community Center",
            category="Environmental", description="Establish a community garden to promote sustainable living and local food production.",
            max_participants=15, duration=6.0, points=100, rating=0.0,
            requirements="Interest in gardening and sustainable practices."
        ),
        "open_project": _get_or_create_project(
            "Beach Cleanup Action", greenearth,
            date=today + timedelta(days=15), location="Golden Coast",
            category="Environmental", description="Join a community effort to remove debris from the shoreline and protect marine ecosystems.",
            max_participants=25, duration=4.5, points=70, rating=4.6,
            requirements="Able to walk on sandy terrain and handle cleanup tools."
        ),
        "in_progress_project": _get_or_create_project(
            "River Conservation Program", greenearth,
            date=today + timedelta(days=10), location="Riverside Park",
            category="Environmental", description="Monitor water quality and clean up riverbanks to protect aquatic ecosystems.",
            max_participants=20, duration=5.0, points=75, rating=4.7,
            requirements="Comfortable working near water and able to use testing equipment."
        ),
        "rejected_project": _get_or_create_project(
            "Night Market Setup", greenearth,
            date=today + timedelta(days=22), location="Downtown Square",
            category="Education", description="Help set up and manage a community night market event.",
            max_participants=20, duration=5.0, points=80, rating=0.0,
            requirements="Available in evenings and able to lift moderate weights."
        ),
        "completed_project": _get_or_create_project(
            "Urban Greening Planting Project", greenearth,
            date=today - timedelta(days=30), location="City Park",
            category="Environmental", description="Plant native trees and shrubs to improve urban biodiversity and air quality.",
            max_participants=30, duration=5.0, points=90, rating=4.9,
            requirements="Comfortable with outdoor manual work for several hours."
        ),
        "record_pending_project": _get_or_create_project(
            "Community Book Donation", greenearth,
            date=today - timedelta(days=10), location="Civic Center",
            category="Education", description="Organize and catalog donated books before delivering them to local community centers.",
            max_participants=12, duration=3.5, points=55, rating=4.3,
            requirements="Attention to detail and ability to lift small boxes."
        ),
        "record_rejected_project": _get_or_create_project(
            "Urban Street Tree Care", greenearth,
            date=today - timedelta(days=8), location="Main Avenue",
            category="Environmental", description="Water and mulch street trees to improve urban canopy health.",
            max_participants=12, duration=2.0, points=40, rating=4.0,
            requirements="Comfortable with light outdoor work."
        ),
    }
    
    # Set statuses explicitly
    projects["open_project"].status = ProjectStatus.APPROVED.value
    projects["in_progress_project"].status = ProjectStatus.IN_PROGRESS.value
    projects["pending_project"].status = ProjectStatus.PENDING.value
    projects["rejected_project"].status = ProjectStatus.REJECTED.value
    projects["completed_project"].status = ProjectStatus.COMPLETED.value
    projects["record_pending_project"].status = ProjectStatus.APPROVED.value
    projects["record_rejected_project"].status = ProjectStatus.APPROVED.value
    
    db.session.commit()
    
    # Seed registrations to cover statuses: registered, approved, cancelled, completed, rejected
    registrations = [
        (emma, projects["open_project"], "registered"),
        (emma, projects["in_progress_project"], "approved"),
        (emma, projects["completed_project"], "completed"),
        (emma, projects["record_pending_project"], "completed"),
        (emma, projects["record_rejected_project"], "rejected"),
        (emma, projects["pending_project"], "cancelled"),
    ]
    
    for user, proj, status in registrations:
        existing = Registration.query.filter_by(
            user_id=user.id, project_id=proj.id, status=status).first()
        if not existing:
            reg = Registration(
                user_id=user.id,
                project_id=proj.id,
                status=status,
                created_at=datetime.utcnow(),
            )
            db.session.add(reg)
    
    db.session.commit()
    
    # Create records for completed registrations (pending and approved variants)
    for reg in Registration.query.filter_by(status=RegistrationStatus.COMPLETED.value).all():
        existing = VolunteerRecord.query.filter_by(user_id=reg.user_id, project_id=reg.project_id).first()
        if not existing:
            project = reg.project
            record = VolunteerRecord(
                user_id=reg.user_id,
                project_id=reg.project_id,
                hours=project.duration,
                points=project.points,
                status=VolunteerRecordStatus.PENDING.value,  # pending review by default
                completed_at=datetime.utcnow()
            )
            db.session.add(record)
    
    # Additional record variants for review states
    if not VolunteerRecord.query.filter_by(user_id=emma.id, project_id=projects["record_pending_project"].id).first():
        db.session.add(VolunteerRecord(
            user_id=emma.id,
            project_id=projects["record_pending_project"].id,
            hours=projects["record_pending_project"].duration,
            points=projects["record_pending_project"].points,
            status=VolunteerRecordStatus.PENDING.value,
            completed_at=datetime.utcnow()
        ))
    if not VolunteerRecord.query.filter_by(user_id=emma.id, project_id=projects["record_rejected_project"].id).first():
        db.session.add(VolunteerRecord(
            user_id=emma.id,
            project_id=projects["record_rejected_project"].id,
            hours=projects["record_rejected_project"].duration,
            points=projects["record_rejected_project"].points,
            status=VolunteerRecordStatus.REJECTED.value,
            completed_at=datetime.utcnow()
        ))
    
    # Seed comments (participants + organization) and a reply
    emma_comment = Comment(
        user_id=emma.id,
        project_id=projects["open_project"].id,
        content="Looking forward to joining the beach cleanup!"
    )
    org_comment = Comment(
        user_id=greenearth.id,
        project_id=projects["in_progress_project"].id,
        content="Thanks for the support! We still need 5 more volunteers."
    )
    db.session.add_all([emma_comment, org_comment])
    db.session.flush()  # obtain IDs for replies
    
    reply_comment = Comment(
        user_id=greenearth.id,
        project_id=projects["open_project"].id,
        parent_id=emma_comment.id,
        content="Welcome! Please check the packing list we just uploaded."
    )
    db.session.add(reply_comment)
    
    db.session.commit()
    app.logger.info("Sample data seeded successfully.")

# Expose app for CLI
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
