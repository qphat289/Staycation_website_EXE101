import os
from flask import Flask, render_template, session, send_from_directory, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from config import Config
from models import db, Admin, Owner, Renter, Homestay
from utils import get_rank_info
from dotenv import load_dotenv

# Load environment variables from .env file for google login
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize database, migrations, login manager
    db.init_app(app)
    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.login'
    app.jinja_env.filters['rank_info'] = get_rank_info

    # The force_https function has been removed to prevent redirect loops

    @login_manager.user_loader
    def load_user(user_id):
        role = session.get('user_role')
        if role == 'admin':
            return Admin.query.get(int(user_id))
        elif role == 'owner':
            return Owner.query.get(int(user_id))
        elif role == 'renter':
            return Renter.query.get(int(user_id))
        return None

    # Create tables and add admin if not exist
    with app.app_context():
        db.create_all()
        print("Database tables created successfully.")

        # Check if any admin exists and create one if not
        existing_admin = Admin.query.first()
        if existing_admin:
            print(f"Admin user already exists: {existing_admin.username}")
        else:
            admin_user = Admin(username='admin', email='admin@example.com')
            admin_user.set_password('123')
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin user created with username='admin', password='123'")
            print("Please login and update the admin information immediately!")

    # Import and register blueprints
    from routes.auth import auth_bp
    from routes.owner import owner_bp
    from routes.renter import renter_bp
    from routes.admin import admin_bp
    from routes.payment import payment_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(owner_bp)
    app.register_blueprint(renter_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(payment_bp)

    # Home route
    @app.route('/')
    def home():
        # Nếu người dùng đã đăng nhập và là owner thì hiển thị homestay của họ
        if current_user.is_authenticated and current_user.is_owner():
            homestays = Homestay.query.filter_by(owner_id=current_user.id).all()
            return render_template('home.html', homestays=homestays)
        # Retrieve featured homestays to display on the homepage
        homestays = Homestay.query.filter_by(is_active=True).limit(6).all()
        return render_template('home.html', homestays=homestays)

    # Route to handle image uploads
    @app.route('/static/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER']), filename)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)