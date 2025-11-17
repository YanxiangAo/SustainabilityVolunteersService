# Flask Backend for Sustainable Volunteer Service Platform

from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
from models import db, User, Project, Badge, UserBadge, Registration, VolunteerRecord
from routes import bp
from sqlalchemy import text, inspect
from datetime import date, datetime

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'main.login'
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
    app.register_blueprint(bp)

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
    # 删除现有的注册、工时记录和用户徽章数据（保留用户、项目和徽章定义）
    print("Clearing existing registration and volunteer record data...")
    Registration.query.delete()
    VolunteerRecord.query.delete()
    UserBadge.query.delete()
    db.session.commit()
    print("Existing data cleared.")
    
    # 获取或创建必要的用户和项目（简化：直接查询，如果不存在则创建）
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
            # 确保已存在的项目状态是 approved（用于这些特定的项目）
            if 'status' in kwargs and kwargs['status'] == 'approved':
                project.status = 'approved'
                db.session.add(project)
                db.session.commit()
        return project
    
    # 创建一个组织
    greenearth = _get_or_create_user("greenearth", "contact@greenearth.org", "organization", "OrgPass123!", "Green Earth Environmental")
    
    # 创建一个参与者（用于验证流程的各个阶段）
    emma = _get_or_create_user("emma", "emma@example.com", "participant", "Volunteer123!", "Emma Wilson")
    
    # 创建多个项目（用于验证 Project 状态流转：pending, approved, rejected, completed）
    projects = {
        # Project 状态：pending - 等待管理员审核
        "pending_project": _get_or_create_project(
            "Community Garden Initiative", greenearth,
            date=date(2025, 12, 1), location="Community Center",
            category="Environmental", description="Establish a community garden to promote sustainable living and local food production.",
            max_participants=15, duration=6.0, points=100, rating=0.0,
            requirements="Interest in gardening and sustainable practices."
        ),
        # Project 状态：approved - 已批准，可以接受注册（用于 registered 状态的注册）
        "registered_project": _get_or_create_project(
            "Beach Cleanup Action", greenearth,
            date=date(2025, 12, 5), location="Golden Coast",
            category="Environmental", description="Join a community effort to remove debris from the shoreline and protect marine ecosystems.",
            max_participants=25, duration=4.5, points=70, rating=4.6,
            requirements="Able to walk on sandy terrain and handle cleanup tools."
        ),
        # Project 状态：approved - 已批准（用于 approved 状态的注册）
        "approved_registration_project": _get_or_create_project(
            "River Conservation Program", greenearth,
            date=date(2025, 12, 8), location="Riverside Park",
            category="Environmental", description="Monitor water quality and clean up riverbanks to protect aquatic ecosystems.",
            max_participants=20, duration=5.0, points=75, rating=4.7,
            requirements="Comfortable working near water and able to use testing equipment."
        ),
        # Project 状态：approved - 已批准（用于 cancelled 状态的注册）
        "cancelled_registration_project": _get_or_create_project(
            "Wildlife Habitat Restoration", greenearth,
            date=date(2025, 12, 12), location="Nature Reserve",
            category="Environmental", description="Restore native habitats and create safe spaces for local wildlife.",
            max_participants=18, duration=4.0, points=65, rating=4.5,
            requirements="Physical fitness and respect for wildlife."
        ),
        # Project 状态：rejected - 被管理员拒绝
        "rejected_project": _get_or_create_project(
            "Night Market Setup", greenearth,
            date=date(2025, 12, 10), location="Downtown Square",
            category="Education", description="Help set up and manage a community night market event.",
            max_participants=20, duration=5.0, points=80, rating=0.0,
            requirements="Available in evenings and able to lift moderate weights."
        ),
        # Project 状态：completed - 已完成（用于 completed 状态的注册）
        "completed_project": _get_or_create_project(
            "Urban Greening Planting Project", greenearth,
            date=date(2025, 11, 20), location="City Park",
            category="Environmental", description="Plant native trees and shrubs to improve urban biodiversity and air quality.",
            max_participants=30, duration=5.0, points=90, rating=4.9,
            requirements="Comfortable with outdoor manual work for several hours."
        ),
        # 用于创建已审核通过的 VolunteerRecord（展示完整流程）
        "approved_record_project": _get_or_create_project(
            "Community Book Donation", greenearth,
            date=date(2025, 11, 25), location="Civic Center",
            category="Education", description="Organize and catalog donated books before delivering them to local community centers.",
            max_participants=12, duration=3.5, points=55, rating=4.3,
            requirements="Attention to detail and ability to lift small boxes."
        ),
    }
    
    # 设置项目的状态（除了 approved 是默认值）
    # 确保 registered_project 和 approved_registration_project 的状态是 approved
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

    # Seed registrations - 一个参与者注册多个项目，处于不同的状态，用于验证 Registration 状态流转
    # Registration 状态：registered, approved, cancelled, completed
    # 注意：只能注册到 approved 状态的项目，每个状态使用不同的项目
    registrations = [
        # 1. registered - 待组织审核的注册（参与者已注册，等待组织批准/拒绝）
        (emma, projects["registered_project"], "registered"),
        
        # 2. approved - 已批准（组织已批准，参与者可以参与，等待组织确认完成）
        (emma, projects["approved_registration_project"], "approved"),
        
        # 3. cancelled - 已取消（被组织拒绝或标记为未完成）
        (emma, projects["cancelled_registration_project"], "cancelled"),
        
        # 4. completed - 已完成（组织确认参与者完成，会自动创建 pending 的 VolunteerRecord）
        (emma, projects["completed_project"], "completed"),
    ]
    
    # 创建所有状态的注册
    for user, proj, status in registrations:
        # 检查是否已存在相同的注册
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

    # 对于 completed 状态的注册，手动创建对应的 pending VolunteerRecord
    # （因为自动创建只在状态变更时触发，seeding 时直接创建 completed 状态不会触发）
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
                status='pending',  # 待管理员审核
                completed_at=datetime.utcnow()
            )
            db.session.add(record)
            pending_records_created += 1
    db.session.commit()
    
    # Seed 一些已审核通过的 VolunteerRecord（用于展示完整的流程）
    # 这些代表之前已完成并审核通过的项目
    approved_records = [
        # 已审核通过 - 会显示在参与者的统计和 Hour Records 中
        (emma, projects["approved_record_project"], 3.5, 55, "approved"),
    ]
    
    approved_count = 0
    for user, proj, hours, points, status in approved_records:
        # 检查是否已存在
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
    
    # 统计创建的注册数量
    total_registrations = Registration.query.filter_by(user_id=emma.id).count()
    print(f"Created {total_registrations} registrations for participant emma:")
    print(f"  - registered: {Registration.query.filter_by(user_id=emma.id, status='registered').count()}")
    print(f"  - approved: {Registration.query.filter_by(user_id=emma.id, status='approved').count()}")
    print(f"  - completed: {Registration.query.filter_by(user_id=emma.id, status='completed').count()}")
    print(f"  - cancelled: {Registration.query.filter_by(user_id=emma.id, status='cancelled').count()}")
    print(f"\nCreated {pending_records_created} pending volunteer records (from completed registrations).")
    print(f"Created {approved_count} approved volunteer records.")
    
    # 打印项目状态统计
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
