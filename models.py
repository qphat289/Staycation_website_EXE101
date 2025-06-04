from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import json

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
    avatar = db.Column(db.String(200))
    is_super_admin = db.Column(db.Boolean, default=False)
    can_manage_admins = db.Column(db.Boolean, default=False)
    can_approve_changes = db.Column(db.Boolean, default=False)
    can_view_all_stats = db.Column(db.Boolean, default=True)
    can_manage_users = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)

    def __init__(self, username, email, full_name=None, is_super_admin=False):
        self.username = username
        self.email = email
        self.full_name = full_name or username
        self.is_super_admin = is_super_admin
        
        # Tự động set quyền dựa vào loại admin
        if is_super_admin:
            self.can_manage_admins = True
            self.can_approve_changes = True
            self.can_view_all_stats = True
            self.can_manage_users = True

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
        
    @property
    def display_name(self):
        return self.full_name or self.username

    def update_last_login(self):
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    # Kiểm tra các quyền
    def can_create_admin(self):
        return self.is_super_admin and self.can_manage_admins
    
    def can_delete_admin(self):
        return self.is_super_admin and self.can_manage_admins
    
    def can_modify_admin(self):
        return self.is_super_admin and self.can_manage_admins
    
    def can_approve_system_changes(self):
        return self.is_super_admin and self.can_approve_changes
        
    def __repr__(self):
        return f'<Admin {self.username}>'

class Owner(UserMixin, db.Model):
    __tablename__ = 'owner'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    avatar = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    homestays = db.relationship('Homestay', backref='owner', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    @property
    def role(self):
        return 'owner'
        
    def is_owner(self):
        return True
        
    def is_renter(self):
        return False
        
    def __repr__(self):
        return f'<Owner {self.username}>'

class Renter(UserMixin, db.Model):
    __tablename__ = 'renter'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    avatar = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    temp_role = db.Column(db.String(20), default='renter')
    
    # Social login fields
    is_google = db.Column(db.Boolean, default=False)
    is_facebook = db.Column(db.Boolean, default=False)
    facebook_id = db.Column(db.String(100), unique=True)
    
    # Relationships
    bookings = db.relationship('Booking', backref='renter', lazy=True)
    reviews = db.relationship('Review', backref='renter', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    @property
    def role(self):
        return 'renter'
        
    def is_owner(self):
        return False
        
    def is_renter(self):
        return True
        
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
    is_active = db.Column(db.Boolean, default=True)
    
    # Liên kết với Owner
    owner_id = db.Column(db.Integer, db.ForeignKey('owner.id'), nullable=False)
    
    # Quan hệ với cascade delete:
    rooms = db.relationship('Room', backref='homestay', lazy=True, cascade="all, delete-orphan")
    bookings = db.relationship('Booking', backref='homestay', lazy=True, cascade="all, delete-orphan")
    reviews = db.relationship('Review', backref='homestay', lazy=True, cascade="all, delete-orphan")
    
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
    
    # Quan hệ với cascade delete cho RoomImage:
    images = db.relationship('RoomImage', backref='room', lazy=True, cascade="all, delete-orphan")
    
    @property
    def display_price(self):
        """Return the price formatted for display (multiplied by 1000 and converted to integer)"""
        return int(self.price_per_hour * 1000)

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

# Bảng liên kết nhiều-nhiều giữa Room và Amenity
room_amenities = db.Table('room_amenities',
    db.Column('room_id', db.Integer, db.ForeignKey('room.id'), primary_key=True),
    db.Column('amenity_id', db.Integer, db.ForeignKey('amenity.id'), primary_key=True)
)

class Amenity(db.Model):
    __tablename__ = 'amenity'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(100), nullable=False)  # Tên biểu tượng Bootstrap
    category = db.Column(db.String(50), default='general')  # Phân loại: general, bathroom, entertainment, etc.
    
    # Quan hệ nhiều-nhiều với Room
    rooms = db.relationship('Room', secondary=room_amenities, backref=db.backref('amenities', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Amenity {self.name}>'

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
    
    payment_status = db.Column(db.String(20), default='pending')
    payment_date = db.Column(db.DateTime, nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)
    payment_reference = db.Column(db.String(100), nullable=True)
    
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

class Statistics(db.Model):
    __tablename__ = 'statistics'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)  # Ngày thống kê
    
    # Thống kê tổng quan
    total_users = db.Column(db.Integer, default=0)  # Tổng số người dùng (owner + renter)
    total_owners = db.Column(db.Integer, default=0)  # Số lượng owner
    total_renters = db.Column(db.Integer, default=0)  # Số lượng renter
    
    # Thống kê đặt phòng
    total_bookings = db.Column(db.Integer, default=0)  # Tổng số lượt đặt
    hourly_bookings = db.Column(db.Integer, default=0)  # Số lượt đặt theo giờ
    overnight_bookings = db.Column(db.Integer, default=0)  # Số lượt đặt qua đêm
    total_hours = db.Column(db.Integer, default=0)  # Tổng số giờ đã thuê
    
    # Tỷ lệ và đánh giá
    booking_rate = db.Column(db.Float, default=0)  # Tỷ lệ đặt phòng thành công
    common_type = db.Column(db.String(50))  # Hình thức thuê phổ biến
    average_rating = db.Column(db.Float, default=0)  # Đánh giá trung bình
    
    # Thống kê theo thời gian (7 ngày)
    hourly_stats = db.Column(db.Text)  # Dữ liệu biểu đồ thuê theo giờ
    overnight_stats = db.Column(db.Text)  # Dữ liệu biểu đồ thuê qua đêm
    
    # Thống kê homestay nổi bật
    top_homestays = db.Column(db.Text)  # Danh sách homestay nổi bật