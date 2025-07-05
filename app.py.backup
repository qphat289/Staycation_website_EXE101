import os
from flask import Flask, render_template, session, send_from_directory, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_migrate import Migrate
from config.config import Config
from app.models.models import db, Admin, Owner, Renter, Statistics, Room, Booking, Review, Amenity, RoomImage
from app.utils.utils import get_rank_info, get_location_name
from app.utils.address_formatter import format_district, format_city, format_full_address
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# Load environment variables from .env file for google login
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

app.jinja_env.filters['rank_info'] = get_rank_info
app.jinja_env.filters['location_name'] = get_location_name

# Add address formatting filters
@app.template_filter('format_district')
def format_district_filter(district):
    return format_district(district)

@app.template_filter('format_city') 
def format_city_filter(city):
    return format_city(city)

# Add functions to template global context
@app.template_global()
def format_full_address(street=None, ward=None, district=None, city=None):
    from app.utils.address_formatter import format_full_address as formatter
    return formatter(street, ward, district, city)

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

@app.template_filter('property_type_vn')
def property_type_vn_filter(value):
    """Chuyển đổi property type sang tiếng Việt"""
    property_type_map = {
        'house': 'Nhà',
        'apartment': 'Căn hộ', 
        'hotel': 'Khách sạn'
    }
    return property_type_map.get(value, value)

@login_manager.user_loader
def load_user(user_id):
    # Get user role from session to load correct user type
    user_role = session.get('user_role')
    print(f"Loading user with ID: {user_id}, Role from session: {user_role}")
    
    # Try to load based on session role first
    if user_role == 'admin':
        admin = db.session.get(Admin, int(user_id))
        if admin:
            print(f"Loaded admin: {admin.username}")
            return admin
    elif user_role == 'owner':
        owner = db.session.get(Owner, int(user_id))
        if owner:
            print(f"Loaded owner: {owner.username}")
            return owner
    elif user_role == 'renter':
        renter = db.session.get(Renter, int(user_id))
        if renter:
            print(f"Loaded renter: {renter.username}")
            return renter
    
    # Fallback: try to load from each user model if session role not available
    admin = db.session.get(Admin, int(user_id))
    if admin:
        print(f"Fallback loaded admin: {admin.username}")
        return admin
    
    owner = db.session.get(Owner, int(user_id))
    if owner:
        print(f"Fallback loaded owner: {owner.username}")
        return owner
    
    renter = db.session.get(Renter, int(user_id))
    if renter:
        print(f"Fallback loaded renter: {renter.username}")
        return renter
    
    print(f"No user found with ID: {user_id}")
    return None

# Initialize migration
migrate = Migrate(app, db)

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
                top_rooms=json.dumps([])
            )
            db.session.add(stats)
            db.session.commit()
            print("Initial statistics created.")
    except Exception as e:
        print(f"Error creating statistics: {e}")

# Import and register blueprints
from app.routes.auth import auth_bp
from app.routes.owner import owner_bp
from app.routes.renter import renter_bp
from app.routes.admin import admin_bp
from app.routes.payment import payment_bp
from app.routes.api import api_bp

app.register_blueprint(auth_bp)
app.register_blueprint(owner_bp)
app.register_blueprint(renter_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(api_bp)

# Home route
@app.route('/')
def home():
    # If user is logged in and is owner, redirect to their dashboard instead of showing home page
    if current_user.is_authenticated and current_user.is_owner():
        return redirect(url_for('owner.dashboard'))
    # If user is logged in and is admin, redirect to their dashboard instead of showing home page
    if current_user.is_authenticated and isinstance(current_user, Admin):
        return redirect(url_for('admin.dashboard'))
    # Retrieve featured homestays to display on the homepage
    from sqlalchemy.orm import joinedload
    homestays = Room.query.options(
        joinedload(Room.images),
        joinedload(Room.reviews)
    ).filter_by(is_active=True).limit(6).all()
    return render_template('home.html', homestays=homestays)

# Route to handle image uploads (legacy)
@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(os.path.join(app.config.get('UPLOAD_FOLDER', 'static/uploads')), filename)

# Route to handle new data directory structure
@app.route('/static/data/<path:filepath>')
def data_file(filepath):
    return send_from_directory(os.path.join('static', 'data'), filepath)

if __name__ == '__main__':
    app.run(debug=True)