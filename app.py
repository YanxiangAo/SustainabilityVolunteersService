# Flask Backend for Sustainable Volunteer Service Platform

from flask import Flask
from config import Config
from models import db, User
from routes import bp
from sqlalchemy import text


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)

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
            db.session.add(admin)
            db.session.commit()


# Expose the app instance for Flask CLI
app = create_app()


if __name__ == '__main__':
    app.run(debug=True)
