from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Define user roles
ROLE_RENTER = 'renter'
ROLE_OWNER = 'owner'
ROLE_ADMIN = 'admin'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    personal_id = db.Column(db.String(12), unique=True)
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(12))
    role = db.Column(db.String(20), nullable=False, default='admin')  # 'owner' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_renter(self):
        return self.role == 'renter'

    def is_admin(self):
        return self.role == 'admin'
    
    def is_owner(self):
        return self.role == 'owner'

    def __repr__(self):
        return f'<User {self.username}>'


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
    homestays = db.relationship('Homestay', back_populates='owner', lazy=True)

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
    """
    Homestay thuộc Owner
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    district = db.Column(db.String(50), nullable=False)
    image_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Key -> OWNER
    owner_id = db.Column(db.Integer, db.ForeignKey('owner.id'), nullable=False)

    # Sử dụng back_populates thay vì backref
    owner = db.relationship('Owner', back_populates='homestays', lazy=True)
    
    # Rooms
    rooms = db.relationship('Room', backref='homestay', lazy=True)
    
    # Bookings
    bookings = db.relationship('Booking', backref='homestay', lazy='dynamic')

    # Reviews
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
