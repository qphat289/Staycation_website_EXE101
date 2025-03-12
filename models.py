from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

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
    phone = db.Column(db.String(12))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    personal_id = db.Column(db.String(12))  # newly added

    # Relationships
    homestays = db.relationship('Homestay', backref='owner', lazy='dynamic')
    bookings = db.relationship('Booking', backref='renter', lazy='dynamic')
    reviews = db.relationship('Review', backref='author', lazy='dynamic')
    
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
    __tablename__ = 'homestay'
    
    """Homestay model for properties listed by owners"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    district = db.Column(db.String(50), nullable=False)
    image_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Key
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # One homestay has many rooms, with a single backref on the Room side named 'homestay'
    rooms = db.relationship('Room', backref='homestay', lazy=True)
    
    # Bookings for this homestay
    bookings = db.relationship('Booking', backref='homestay', lazy='dynamic')

    # Reviews for this homestay
    reviews = db.relationship('Review', backref='homestay', lazy='dynamic')
    
    def __repr__(self):
        return f'<Homestay {self.title}>'


class Booking(db.Model):
    __tablename__ = 'booking'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    homestay_id = db.Column(db.Integer, db.ForeignKey('homestay.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=True)  # room is optional
    renter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Room relationship (no conflict because 'backref="bookings"' is a different name)
    room = db.relationship('Room', backref='bookings', lazy=True)


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    homestay_id = db.Column(db.Integer, db.ForeignKey('homestay.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class Room(db.Model):
    __tablename__ = 'room'
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(20), nullable=False)
    bed_count = db.Column(db.Integer, nullable=False)
    bathroom_count = db.Column(db.Integer, nullable=False)
    max_guests = db.Column(db.Integer, nullable=False)
    price_per_hour = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)

    # Link back to Homestay
    homestay_id = db.Column(db.Integer, db.ForeignKey('homestay.id'), nullable=False)
    # Do NOT define a second relationship with backref='homestay' here. One side is enough.

    # If you want a simple relationship w/o backref:
    # homestay = db.relationship('Homestay', lazy=True)

class RoomImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(200))
    is_featured = db.Column(db.Boolean, default=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)

    room = db.relationship('Room', backref='images', lazy=True)
