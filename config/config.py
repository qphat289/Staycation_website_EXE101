import os

class Config:
    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-for-development-only'
    
    # PostgreSQL database configuration
    # Luôn sử dụng PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://postgres:123@localhost:5432/homestay')
    
    # Cấu hình cũ (SQLite fallback)
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "instance", "homestay.db")}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Google OAuth config
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')  # Remove the hardcoded value
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')  # Remove the hardcoded value
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
    #GOOGLE_REDIRECT_URI = "/auth/callback"

    # Facebook OAuth settings
    FACEBOOK_CLIENT_ID = os.environ.get('FACEBOOK_CLIENT_ID')
    FACEBOOK_CLIENT_SECRET = os.environ.get('FACEBOOK_CLIENT_SECRET')
    FACEBOOK_CALLBACK_URL = os.environ.get('FACEBOOK_CALLBACK_URL', 'http://localhost:5000/auth/facebook/callback')

    # Upload folder for homestay images
    UPLOAD_FOLDER = os.path.join('static', 'uploads')
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    DEBUG_REVIEW = False
