class Config:
    SECRET_KEY = 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///volunteer.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Increase SQLite busy timeout to reduce 'database is locked' errors
    SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"timeout": 30}}
