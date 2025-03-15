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
    role = db.Column(db.String(50), nullable=False, default="renter") # 'renter' or 'owner'
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(12))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    personal_id = db.Column(db.String(12))  # newly added
    experience_points = db.Column(db.Integer, default=0)  # NEW column
  
    # Relationships
    homestays = db.relationship('Homestay', backref='user', lazy='dynamic')
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
    
    def is_admin(self):
        return self.role == 'admin'

class Owner(db.Model):
    __tablename__ = 'owner'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(12))
    personal_id = db.Column(db.String(12), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Sử dụng back_populates thay vì backref
    homestays = db.relationship('Homestay', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Owner {self.username}>'
    

class Renter(db.Model):
    """
    Lưu thông tin người thuê (Renter),
    Tự đăng ký và đăng nhập.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(12))
    personal_id = db.Column(db.String(12), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Bookings => relationship ở Booking (renter_id -> this.id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Renter {self.username}>'
    
class Homestay(db.Model):
    __tablename__ = 'homestay'
    
    """Homestay model for properties listed by owners"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    floor_count = db.Column(db.Integer, nullable=False, default=1)
    district = db.Column(db.String(50), nullable=False)
    image_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Foreign Key
    owner_id = db.Column(db.Integer, db.ForeignKey('owner.id'), nullable=False)

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
    id = db.Column(db.Integer, primary_key=True)
    homestay_id = db.Column(db.Integer, db.ForeignKey('homestay.id'), nullable=False)
    room_number = db.Column(db.String(100), nullable=False)  # Existing
    floor_number = db.Column(db.Integer, nullable=False, default=1)  # NEW COLUMN
    bed_count = db.Column(db.Integer, nullable=False)
    bathroom_count = db.Column(db.Integer, nullable=False)
    max_guests = db.Column(db.Integer, nullable=False)
    price_per_hour = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_booked = db.Column(db.Boolean, default=False)
    images = db.relationship('RoomImage', backref='room', lazy=True)
    # Do NOT define a second relationship with backref='homestay' here. One side is enough.

    # If you want a simple relationship w/o backref:
    # homestay = db.relationship('Homestay', lazy=True)

class RoomImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(255), nullable=False)
    is_featured = db.Column(db.Boolean, default=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)

