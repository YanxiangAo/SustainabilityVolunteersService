# Flask Backend for Sustainable Volunteer Service Platform

from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
from models import db, User, Project, Badge, UserBadge, Registration, VolunteerRecord, SystemSettings, Comment
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
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    register_blueprints(app)

    # Ensure logs show up even when debug is off
    try:
        import logging
        app.logger.setLevel(logging.INFO)
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

    # Initialize database and seed admin
    init_db(app)

    return app


def init_db(app: Flask) -> None:
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
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@example.com', user_type='admin')
            admin.set_password('admin123')  # Change this password!
            # Set is_active for new admin user
            if hasattr(admin, 'is_active'):
                admin.is_active = True
            db.session.add(admin)
            db.session.commit()

        seed_sample_data()

def seed_sample_data() -> None:
    """Populate the database with initial sample data for demo usage."""
    # Remove existing registrations, volunteer records, and user badges while keeping users, projects, and badge definitions.
    print("Clearing existing registration and volunteer record data...")
    Registration.query.delete()
    VolunteerRecord.query.delete()
    UserBadge.query.delete()
    Comment.query.delete()
    db.session.commit()
    print("Existing data cleared.")
    
    # Helper utilities to fetch or create prerequisite users/projects (simple query-or-create approach).
    def _get_or_create_user(username: str, email: str, user_type: str, password: str, display_name: str = None) -> User:
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(
                username=username,
                email=email,
                user_type=user_type,
                display_name=display_name or username
            )
            user.set_password(password)
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
            # Ensure any pre-existing seed project is set to approved when required.
            if 'status' in kwargs and kwargs['status'] == 'approved':
                project.status = 'approved'
                db.session.add(project)
                db.session.commit()
        return project
    
    # Create a seed organization account.
    greenearth = _get_or_create_user("greenearth", "contact@greenearth.org", "organization", "OrgPass123!", "Green Earth Environmental")
    
    # Create a participant used across all workflow scenarios.
    emma = _get_or_create_user("emma", "emma@example.com", "participant", "Volunteer123!", "Emma Wilson")
    
    # Create multiple projects that exercise every project lifecycle state (pending, approved, rejected, completed).
    projects = {
        # Project state: pending — awaiting admin review.
        "pending_project": _get_or_create_project(
            "Community Garden Initiative", greenearth,
            date=date(2025, 12, 1), location="Community Center",
            category="Environmental", description="Establish a community garden to promote sustainable living and local food production.",
            max_participants=15, duration=6.0, points=100, rating=0.0,
            requirements="Interest in gardening and sustainable practices."
        ),
        # Project state: approved — open for registrations (used for the "registered" sample).
        "registered_project": _get_or_create_project(
            "Beach Cleanup Action", greenearth,
            date=date(2025, 12, 5), location="Golden Coast",
            category="Environmental", description="Join a community effort to remove debris from the shoreline and protect marine ecosystems.",
            max_participants=25, duration=4.5, points=70, rating=4.6,
            requirements="Able to walk on sandy terrain and handle cleanup tools."
        ),
        # Project state: approved — used for the "approved" registration sample.
        "approved_registration_project": _get_or_create_project(
            "River Conservation Program", greenearth,
            date=date(2025, 12, 8), location="Riverside Park",
            category="Environmental", description="Monitor water quality and clean up riverbanks to protect aquatic ecosystems.",
            max_participants=20, duration=5.0, points=75, rating=4.7,
            requirements="Comfortable working near water and able to use testing equipment."
        ),
        # Project state: approved — used for the "cancelled" registration sample.
        "cancelled_registration_project": _get_or_create_project(
            "Wildlife Habitat Restoration", greenearth,
            date=date(2025, 12, 12), location="Nature Reserve",
            category="Environmental", description="Restore native habitats and create safe spaces for local wildlife.",
            max_participants=18, duration=4.0, points=65, rating=4.5,
            requirements="Physical fitness and respect for wildlife."
        ),
        # Project state: rejected — demonstrates a project removed by admin.
        "rejected_project": _get_or_create_project(
            "Night Market Setup", greenearth,
            date=date(2025, 12, 10), location="Downtown Square",
            category="Education", description="Help set up and manage a community night market event.",
            max_participants=20, duration=5.0, points=80, rating=0.0,
            requirements="Available in evenings and able to lift moderate weights."
        ),
        # Project state: completed — used for the "completed" registration sample.
        "completed_project": _get_or_create_project(
            "Urban Greening Planting Project", greenearth,
            date=date(2025, 11, 20), location="City Park",
            category="Environmental", description="Plant native trees and shrubs to improve urban biodiversity and air quality.",
            max_participants=30, duration=5.0, points=90, rating=4.9,
            requirements="Comfortable with outdoor manual work for several hours."
        ),
        # Dedicated project for pre-approved volunteer record seeding.
        "approved_record_project": _get_or_create_project(
            "Community Book Donation", greenearth,
            date=date(2025, 11, 25), location="Civic Center",
            category="Education", description="Organize and catalog donated books before delivering them to local community centers.",
            max_participants=12, duration=3.5, points=55, rating=4.3,
            requirements="Attention to detail and ability to lift small boxes."
        ),
    }
    
    # Explicitly set project statuses (approved is the default unless overridden here).
    # Ensure the projects tied to registration samples remain approved.
    registered_project = projects["registered_project"]
    registered_project.status = 'approved'
    db.session.add(registered_project)
    
    approved_registration_project = projects["approved_registration_project"]
    approved_registration_project.status = 'approved'
    db.session.add(approved_registration_project)
    
    cancelled_registration_project = projects["cancelled_registration_project"]
    cancelled_registration_project.status = 'approved'
    db.session.add(cancelled_registration_project)
    
    approved_record_project = projects["approved_record_project"]
    approved_record_project.status = 'approved'
    db.session.add(approved_record_project)
    
    pending_project = projects["pending_project"]
    pending_project.status = 'pending'
    db.session.add(pending_project)
    
    rejected_project = projects["rejected_project"]
    rejected_project.status = 'rejected'
    db.session.add(rejected_project)
    
    completed_project = projects["completed_project"]
    completed_project.status = 'completed'
    db.session.add(completed_project)
    
    db.session.commit()

    # Seed registrations: one participant registers for multiple projects to cover every Registration state.
    # Registration states covered: registered, approved, cancelled, completed.
    # Note: Only approved projects accept registrations, so each sample references an approved project.
    registrations = [
        # 1. registered — pending organization approval (participant is waiting for decision).
        (emma, projects["registered_project"], "registered"),
        
        # 2. approved — organization accepted the participant and awaits completion confirmation.
        (emma, projects["approved_registration_project"], "approved"),
        
        # 3. cancelled — rejected by organization or manually marked as cancelled.
        (emma, projects["cancelled_registration_project"], "cancelled"),
        
        # 4. completed — organization confirmed completion, which normally triggers a pending VolunteerRecord.
        (emma, projects["completed_project"], "completed"),
    ]
    
    # Create registrations for each target state if they do not already exist.
    for user, proj, status in registrations:
        # Skip creation when the same registration already exists.
        existing = Registration.query.filter_by(
            user_id=user.id,
            project_id=proj.id,
            status=status
        ).first()
        if not existing:
            registration = Registration(
                user_id=user.id, 
                project_id=proj.id, 
                status=status,
                created_at=datetime.utcnow()
            )
            db.session.add(registration)
    
    db.session.commit()

    # Manually create pending volunteer records for completed registrations, because automatic creation only happens during state transitions.
    completed_registrations = Registration.query.filter_by(status='completed').all()
    pending_records_created = 0
    for reg in completed_registrations:
        existing = VolunteerRecord.query.filter_by(
            user_id=reg.user_id,
            project_id=reg.project_id
        ).first()
        if not existing:
            project = reg.project
            record = VolunteerRecord(
                user_id=reg.user_id,
                project_id=reg.project_id,
                hours=project.duration,
                points=project.points,
                status='pending',  # Waiting for admin approval
                completed_at=datetime.utcnow()
            )
            db.session.add(record)
            pending_records_created += 1
    db.session.commit()
    
    # Seed a few already-approved volunteer records to demonstrate the end-to-end flow.
    # These represent historical projects that finished and passed admin review.
    approved_records = [
        # Approved record — shows up inside participant statistics and Hour Records.
        (emma, projects["approved_record_project"], 3.5, 55, "approved"),
    ]
    
    approved_count = 0
    for user, proj, hours, points, status in approved_records:
        # Skip when a record already exists for the user/project pair.
        existing = VolunteerRecord.query.filter_by(
            user_id=user.id,
            project_id=proj.id
        ).first()
        if not existing:
            record = VolunteerRecord(
                user_id=user.id,
                project_id=proj.id,
                hours=hours,
                points=points,
                status=status,
                completed_at=datetime.utcnow()
            )
            db.session.add(record)
            approved_count += 1
    db.session.commit()
    
    # Output a quick summary of how many registrations were generated.
    total_registrations = Registration.query.filter_by(user_id=emma.id).count()
    print(f"Created {total_registrations} registrations for participant emma:")
    print(f"  - registered: {Registration.query.filter_by(user_id=emma.id, status='registered').count()}")
    print(f"  - approved: {Registration.query.filter_by(user_id=emma.id, status='approved').count()}")
    print(f"  - completed: {Registration.query.filter_by(user_id=emma.id, status='completed').count()}")
    print(f"  - cancelled: {Registration.query.filter_by(user_id=emma.id, status='cancelled').count()}")
    print(f"\nCreated {pending_records_created} pending volunteer records (from completed registrations).")
    print(f"Created {approved_count} approved volunteer records.")
    
    # Print the distribution of project statuses for visibility.
    print(f"\nProject status summary:")
    print(f"  - pending: {Project.query.filter_by(organization_id=greenearth.id, status='pending').count()}")
    print(f"  - approved: {Project.query.filter_by(organization_id=greenearth.id, status='approved').count()}")
    print(f"  - rejected: {Project.query.filter_by(organization_id=greenearth.id, status='rejected').count()}")
    print(f"  - completed: {Project.query.filter_by(organization_id=greenearth.id, status='completed').count()}")

    # Seed badges
    badge_definitions = [
        {
            "code": "rising-star",
            "name": "Rising Star",
            "description": "Complete first volunteer service",
            "accent_color": "var(--accent-yellow)",
            "background_color": "#fef3c7",
            "icon": "star"
        },
        {
            "code": "eco-pioneer",
            "name": "Eco Pioneer",
            "description": "Complete 50 hours of environmental service",
            "accent_color": "var(--primary-green)",
            "background_color": "#dcfce7",
            "icon": "leaf"
        },
        {
            "code": "compassion",
            "name": "Compassion Ambassador",
            "description": "Volunteer for 6 consecutive months",
            "accent_color": "var(--gray-500)",
            "background_color": "#f3f4f6",
            "icon": "heart"
        },
        {
            "code": "public-welfare",
            "name": "Public Welfare Expert",
            "description": "Complete 100 hours of service",
            "accent_color": "var(--gray-500)",
            "background_color": "#f3f4f6",
            "icon": "medal"
        },
        {
            "code": "team-leader",
            "name": "Team Leader",
            "description": "Organize 10 volunteer activities",
            "accent_color": "var(--gray-500)",
            "background_color": "#f3f4f6",
            "icon": "leader"
        }
    ]

    badges_by_code = {}
    for definition in badge_definitions:
        badge = Badge.query.filter_by(code=definition["code"]).first()
        if not badge:
            badge = Badge(
                code=definition["code"],
                name=definition["name"],
                description=definition["description"],
                accent_color=definition["accent_color"],
                background_color=definition["background_color"],
                icon=definition["icon"]
            )
            db.session.add(badge)
            db.session.commit()
        else:
            badge.name = definition["name"]
            badge.description = definition["description"]
            badge.accent_color = definition["accent_color"]
            badge.background_color = definition["background_color"]
            badge.icon = definition["icon"]
            db.session.add(badge)
            db.session.commit()
        badges_by_code[badge.code] = badge

    # Assign badges to sample participant
    if not emma:
        return  # Skip badge assignments if user doesn't exist
    
    user_badge_assignments = [
        ("rising-star", True),
        ("eco-pioneer", True),
        ("compassion", False),
        ("public-welfare", False),
        ("team-leader", False),
    ]

    # Query all existing user_badges for this user in one go to avoid queries in loop
    existing_user_badges = {
        (ub.user_id, ub.badge_id): ub 
        for ub in UserBadge.query.filter_by(user_id=emma.id).all()
    }

    # Now process all assignments without any queries
    for badge_code, earned in user_badge_assignments:
        badge = badges_by_code.get(badge_code)
        if not badge:
            continue
        
        key = (emma.id, badge.id)
        user_badge = existing_user_badges.get(key)
        
        if not user_badge:
            user_badge = UserBadge(
                user_id=emma.id,
                badge_id=badge.id,
                earned=earned,
                earned_at=datetime.utcnow() if earned else None,
                progress=100.0 if earned else 0.0
            )
            db.session.add(user_badge)
        else:
            user_badge.earned = earned
            user_badge.earned_at = datetime.utcnow() if earned else None
            user_badge.progress = 100.0 if earned else user_badge.progress
            db.session.add(user_badge)
    
    db.session.commit()


# Expose the app instance for Flask CLI
app = create_app()


if __name__ == '__main__':
    app.run(debug=True)
