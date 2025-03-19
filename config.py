import os

class Config:
    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-for-development-only'
    
    # SQLite database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///homestay.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload folder for homestay images
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    DEBUG_REVIEW = False
