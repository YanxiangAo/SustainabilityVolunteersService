import os

class Config:
    """Base Configuration."""
    
    # Security: Read SECRET_KEY from environment. FAIL if not set in production.
    # We provide a default for dev ONLY.
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database: Use DATABASE_URL environment variable, defaulting to local SQLite.
    # Note: SQLite URI format is sqlite:///path/to/db
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///volunteer.db')
    
    # Disable modification tracking to save memory
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database Engine Options
    # Increase timeout for SQLite to reduce 'database is locked' errors during concurrency
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            "timeout": 30
        }
    }
    
    # Logging Configuration
    # Log files will be written to this path
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/app.log')
    
    # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
