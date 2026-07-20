import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Secret key for sessions
    SECRET_KEY = os.environ.get('SECRET_KEY', 'wakalapro-secret-key-change-in-production')
    
    # ============================================
    # LICENSE SECRET KEY - IMPORTANT!
    # Change this to a random string
    # ============================================
    LICENSE_SECRET_KEY = os.environ.get('LICENSE_SECRET_KEY', 'WAKALAPRO_SUPER_SECRET_KEY_2024_7x9K2mP5nR8tY3vZ')
    
    # Database
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'wakala.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session security
    SESSION_PERMANENT = False
    SESSION_COOKIE_NAME = "wakalapro_session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_SAMESITE = "Lax"
    
    # Remember me
    REMEMBER_COOKIE_NAME = "wakalapro_remember"
    REMEMBER_COOKIE_DURATION = 0
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    REMEMBER_COOKIE_SAMESITE = "Lax"