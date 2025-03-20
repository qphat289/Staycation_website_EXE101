from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

#######################################
# 1. Các bảng người dùng riêng biệt   #
#######################################

class Admin(UserMixin, db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    full_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def role(self):
        return 'admin'
    
    def is_owner(self):
        return False
    
    def is_renter(self):
        return False
        
    def __repr__(self):
        return f'<Admin {self.username}>'

class Owner(UserMixin, db.Model):
    __tablename__ = 'owner'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(12))
    personal_id = db.Column(db.String(12), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Một owner có nhiều homestays
    homestays = db.relationship('Homestay', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_owner(self):
        return True
    
    def is_renter(self):
        return False
        
    def __repr__(self):
        return f'<Owner {self.username}>'

class Renter(UserMixin, db.Model):
    __tablename__ = 'renter'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(12))
    personal_id = db.Column(db.String(12), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    experience_points = db.Column(db.Integer, default=0)
    # Một renter có nhiều booking và reviews
    bookings = db.relationship('Booking', backref='renter', lazy=True)
    reviews = db.relationship('Review', backref='renter', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def is_renter(self):
        return True
    
    def is_owner(self):
        return False

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def __repr__(self):
        return f'<Renter {self.username}>'

###########################################
# 2. Các bảng liên quan đến Homestay       #
###########################################

class Homestay(db.Model):
    __tablename__ = 'homestay'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    district = db.Column(db.String(50), nullable=False)
    floor_count = db.Column(db.Integer, nullable=False, default=1)
    image_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Liên kết với Owner
    owner_id = db.Column(db.Integer, db.ForeignKey('owner.id'), nullable=False)
    
    # Quan hệ
    rooms = db.relationship('Room', backref='homestay', lazy=True)
    bookings = db.relationship('Booking', backref='homestay', lazy=True)
    reviews = db.relationship('Review', backref='homestay', lazy=True)
    
    def __repr__(self):
        return f'<Homestay {self.title}>'

class Room(db.Model):
    __tablename__ = 'room'
    id = db.Column(db.Integer, primary_key=True)
    homestay_id = db.Column(db.Integer, db.ForeignKey('homestay.id'), nullable=False)
    room_number = db.Column(db.String(100), nullable=False)
    floor_number = db.Column(db.Integer, nullable=False, default=1)
    bed_count = db.Column(db.Integer, nullable=False)
    bathroom_count = db.Column(db.Integer, nullable=False)
    max_guests = db.Column(db.Integer, nullable=False)
    price_per_hour = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_booked = db.Column(db.Boolean, default=False)
    
    # Quan hệ với RoomImage
    images = db.relationship('RoomImage', backref='room', lazy=True)
    
    def __repr__(self):
        return f'<Room {self.room_number} in {self.homestay.title}>'

class RoomImage(db.Model):
    __tablename__ = 'room_image'
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(200))
    is_featured = db.Column(db.Boolean, default=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    
    def __repr__(self):
        return f'<RoomImage {self.id} for Room {self.room_id}>'

class Booking(db.Model):
    __tablename__ = 'booking'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    homestay_id = db.Column(db.Integer, db.ForeignKey('homestay.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=True)  # Có thể không chỉ định phòng
    renter_id = db.Column(db.Integer, db.ForeignKey('renter.id'), nullable=False)
    
    room = db.relationship('Room', backref='bookings', lazy=True)
    
    def __repr__(self):
        return f'<Booking {self.id} for Homestay {self.homestay.title}>'

class Review(db.Model):
    __tablename__ = 'review'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    homestay_id = db.Column(db.Integer, db.ForeignKey('homestay.id'))
    renter_id = db.Column(db.Integer, db.ForeignKey('renter.id'))
    
    def __repr__(self):
        return f'<Review {self.id} for Homestay {self.homestay.title}>'