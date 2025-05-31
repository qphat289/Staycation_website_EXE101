import os

class Config:
    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-for-development-only'
    
    # SQLite database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///homestay.db'
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
