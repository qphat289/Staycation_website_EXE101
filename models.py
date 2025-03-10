from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Create an *uninitialized* SQLAlchemy instance
db = SQLAlchemy()
# Define user roles
ROLE_RENTER = 'renter'
ROLE_OWNER = 'owner'

class User(UserMixin, db.Model):
    """User model for both renters and owners"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(10), nullable=False)  # 'renter' or 'owner'
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    homestays = db.relationship('Homestay', backref='owner', lazy='dynamic')
    bookings = db.relationship('Booking', backref='renter', lazy='dynamic')
    
    def set_password(self, password):
        """Hash the password for security"""
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """Check if the password is correct"""
        return check_password_hash(self.password_hash, password)
    
    def is_owner(self):
        """Check if user is an owner"""
        return self.role == ROLE_OWNER
    
    def is_renter(self):
        """Check if user is a renter"""
        return self.role == ROLE_RENTER
    
    def __repr__(self):
        return f'<User {self.username}>'

class Homestay(db.Model):
    """Homestay model for properties listed by owners"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price_per_hour = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    district = db.Column(db.String(50), nullable=False)
    max_guests = db.Column(db.Integer, default=1)
    bedrooms = db.Column(db.Integer, default=1)
    bathrooms = db.Column(db.Integer, default=1)
    image_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    bookings = db.relationship('Booking', backref='homestay', lazy='dynamic')
    
    def __repr__(self):
        return f'<Homestay {self.title}>'

class Booking(db.Model):
    """Booking model for homestay reservations"""
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    homestay_id = db.Column(db.Integer, db.ForeignKey('homestay.id'), nullable=False)
    renter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<Booking {self.id}>'