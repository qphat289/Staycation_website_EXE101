import os
from flask import Flask, render_template, session, send_from_directory, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from config import Config
from models import db, Admin, Owner, Renter, Homestay, Statistics
from utils import get_rank_info
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta

# Load environment variables from .env file for google login
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize database and login manager
    db.init_app(app)
    migrate = Migrate(app, db)
    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.login'
    app.jinja_env.filters['rank_info'] = get_rank_info

    # Add custom filter
    @app.template_filter('from_json')
    def from_json_filter(value):
        try:
            if value is None or value == '':
                return []
            if isinstance(value, str):
                return json.loads(value)
            return value  # If already parsed
        except (json.JSONDecodeError, TypeError, AttributeError) as e:
            print(f"Error parsing JSON in template filter: {e}, value: {value}")
            return []

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

        # Create initial statistics if not exist
        today = datetime.now().date()
        try:
            stats = Statistics.query.filter_by(date=today).first()
            if not stats:
                stats = Statistics(
                    date=today,
                    total_users=0,
                    total_owners=0,
                    total_renters=0,
                    total_bookings=0,
                    hourly_bookings=0,
                    overnight_bookings=0,
                    total_hours=0,
                    booking_rate=0,
                    common_type="Theo giờ",
                    average_rating=0,
                    hourly_stats=json.dumps({
                        'labels': ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'],
                        'data': [0, 0, 0, 0, 0, 0, 0]
                    }),
                    overnight_stats=json.dumps({
                        'labels': ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'],
                        'data': [0, 0, 0, 0, 0, 0, 0]
                    }),
                    top_homestays=json.dumps([])
                )
                db.session.add(stats)
                db.session.commit()
                print("Initial statistics created.")
        except Exception as e:
            print(f"Error creating statistics: {e}")

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
        # If user is logged in and is owner, show their homestays
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