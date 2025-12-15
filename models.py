from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import UniqueConstraint

# SQLAlchemy instance to be initialized in app factory
db = SQLAlchemy()

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # participant, organization, admin
    display_name = db.Column(db.String(120))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    # Ban system fields
    ban_reason = db.Column(db.String(500))  # Reason for ban (shown to user)
    ban_until = db.Column(db.DateTime)  # NULL = permanent ban when is_active=False
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    projects = relationship('Project', backref='organization', lazy=True)
    registrations = relationship('Registration', backref='user', lazy=True)
    volunteer_records = relationship('VolunteerRecord', backref='user', lazy=True)
    
    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    max_participants = db.Column(db.Integer, nullable=False)
    min_participants = db.Column(db.Integer, default=1)  # Minimum participants to start
    duration = db.Column(db.Float, nullable=False)  # hours
    points = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='pending')  # pending, approved, in_progress, rejected, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    requirements = db.Column(db.Text)
    
    registrations = relationship('Registration', backref='project', lazy=True)
    volunteer_records = relationship('VolunteerRecord', backref='project', lazy=True)

class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    status = db.Column(db.String(20), default='registered')  # registered, completed, cancelled, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class VolunteerRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    hours = db.Column(db.Float, nullable=False)
    points = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved，rejected
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)  # For replies
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    project = relationship('Project', backref='comments', lazy=True)
    user = relationship('User', backref='comments', lazy=True)
    parent = relationship('Comment', remote_side=[id], backref='replies', lazy=True)
