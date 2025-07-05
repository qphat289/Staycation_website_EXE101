from flask import Flask
from flask_login import LoginManager
from app.models.models import db, Admin, Owner, Renter
import os

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    # Try to load from each user model
    admin = Admin.query.get(int(user_id))
    if admin:
        return admin
        
    owner = Owner.query.get(int(user_id))
    if owner:
        return owner
        
    renter = Renter.query.get(int(user_id))
    if renter:
        return renter
        
    return None

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'
    
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Configure SQLite database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configure upload folder
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Register blueprints
    from app.routes.admin import admin_bp
    app.register_blueprint(admin_bp)
    
    return app 

# This file can be empty to make Python treat the directory as a package 