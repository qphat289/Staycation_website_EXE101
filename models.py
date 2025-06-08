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
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    gender = db.Column(db.String(10), default='Nam')
    address = db.Column(db.String(200))
    birth_date = db.Column(db.Date)
    phone = db.Column(db.String(20))
    avatar = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Thêm các trường mới
    business_name = db.Column(db.String(200))  # Tên doanh nghiệp/thương hiệu (nếu có)
    tax_code = db.Column(db.String(50))  # Mã số thuế (nếu có)
    bank_account = db.Column(db.String(50))  # Số tài khoản ngân hàng
    bank_name = db.Column(db.String(100))  # Tên ngân hàng
    
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
    username = db.Column(db.String(80), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    full_name = db.Column(db.String(100))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    gender = db.Column(db.String(10), default='Nam')
    address = db.Column(db.String(200))
    birth_date = db.Column(db.Date)
    phone = db.Column(db.String(20))
    avatar = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    temp_role = db.Column(db.String(20), default='renter')
    
    # Social login fields
    is_google = db.Column(db.Boolean, default=False)
    is_facebook = db.Column(db.Boolean, default=False)
    google_id = db.Column(db.String(100), unique=True)
    facebook_id = db.Column(db.String(100), unique=True)
    google_username = db.Column(db.String(100))
    facebook_username = db.Column(db.String(100))
    
    # Relationships
    bookings = db.relationship('Booking', backref='renter', lazy=True)
    reviews = db.relationship('Review', backref='renter', lazy=True)
    
    def __init__(self, username, email, full_name=None, first_name=None, last_name=None,
                 gender='Nam', address=None, birth_date=None, phone=None, avatar=None,
                 is_active=True, temp_role='renter', is_google=False, is_facebook=False,
                 google_id=None, facebook_id=None, google_username=None, facebook_username=None):
        self.username = username
        self.email = email
        self.full_name = full_name or username
        self.first_name = first_name
        self.last_name = last_name
        self.gender = gender
        self.address = address
        self.birth_date = birth_date
        self.phone = phone
        self.avatar = avatar
        self.is_active = is_active
        self.temp_role = temp_role
        self.is_google = is_google
        self.is_facebook = is_facebook
        self.google_id = google_id
        self.facebook_id = facebook_id
        self.google_username = google_username
        self.facebook_username = facebook_username

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

#######################################
# 2. Các bảng liên quan đến Room      #
#######################################

# Bảng liên kết nhiều-nhiều giữa Room và Amenity
room_amenities = db.Table('room_amenities',
    db.Column('room_id', db.Integer, db.ForeignKey('room.id'), primary_key=True),
    db.Column('amenity_id', db.Integer, db.ForeignKey('amenity.id'), primary_key=True)
)

# Bảng liên kết nhiều-nhiều giữa Room và Rule
room_rules = db.Table('room_rules',
    db.Column('room_id', db.Integer, db.ForeignKey('room.id'), primary_key=True),
    db.Column('rule_id', db.Integer, db.ForeignKey('rule.id'), primary_key=True)
)

#######################################
# 3. Các bảng địa chỉ                 #
#######################################

class Province(db.Model):
    __tablename__ = 'province'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)  # VD: 'hcm', 'hanoi'
    name = db.Column(db.String(100), nullable=False)  # VD: 'TP. Hồ Chí Minh', 'Hà Nội'
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    districts = db.relationship('District', backref='province', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Province {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name
        }

class District(db.Model):
    __tablename__ = 'district'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False)  # VD: 'quan1', 'quanbadinh'
    name = db.Column(db.String(100), nullable=False)  # VD: 'Quận 1', 'Quận Ba Đình'
    is_active = db.Column(db.Boolean, default=True)
    
    # Foreign Key
    province_id = db.Column(db.Integer, db.ForeignKey('province.id'), nullable=False)
    
    # Relationships
    wards = db.relationship('Ward', backref='district', lazy=True, cascade="all, delete-orphan")
    
    # Unique constraint để tránh trùng lặp trong cùng tỉnh
    __table_args__ = (db.UniqueConstraint('code', 'province_id', name='_district_code_province_uc'),)
    
    def __repr__(self):
        return f'<District {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'province_id': self.province_id
        }

class Ward(db.Model):
    __tablename__ = 'ward'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), nullable=False)  # VD: 'phuong_tan_dinh', 'phuong_phuc_xa'
    name = db.Column(db.String(100), nullable=False)  # VD: 'Phường Tân Định', 'Phường Phúc Xá'
    is_active = db.Column(db.Boolean, default=True)
    
    # Foreign Key
    district_id = db.Column(db.Integer, db.ForeignKey('district.id'), nullable=False)
    
    # Unique constraint để tránh trùng lặp trong cùng quận
    __table_args__ = (db.UniqueConstraint('code', 'district_id', name='_ward_code_district_uc'),)
    
    def __repr__(self):
        return f'<Ward {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'district_id': self.district_id
        }

class Room(db.Model):
    __tablename__ = 'room'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    room_type = db.Column(db.String(50), nullable=False)  # Loại phòng: Standard, Deluxe, Suite, etc.
    
    # Thông tin địa chỉ
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    district = db.Column(db.String(50), nullable=False)
    floor_number = db.Column(db.Integer, nullable=False, default=1)
    
    # Thông tin phòng
    room_number = db.Column(db.String(100), nullable=True)  # Có thể không cần số phòng
    bed_count = db.Column(db.Integer, nullable=False)
    bathroom_count = db.Column(db.Integer, nullable=False)
    max_guests = db.Column(db.Integer, nullable=False)
    
    # Giá và mô tả
    price_per_hour = db.Column(db.Float, nullable=False)
    price_per_night = db.Column(db.Float, nullable=True)  # Thêm giá theo đêm
    description = db.Column(db.Text, nullable=True)
    
    # Trạng thái và thời gian
    is_active = db.Column(db.Boolean, default=True)
    is_booked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Liên kết với Owner
    owner_id = db.Column(db.Integer, db.ForeignKey('owner.id'), nullable=False)
    owner = db.relationship('Owner', backref=db.backref('rooms', lazy=True))
    
    # Relationships
    images = db.relationship('RoomImage', backref='room', lazy=True, cascade="all, delete-orphan")
    bookings = db.relationship('Booking', backref='room', lazy=True, cascade="all, delete-orphan")
    reviews = db.relationship('Review', backref='room', lazy=True)
    amenities = db.relationship('Amenity', secondary=room_amenities, backref=db.backref('rooms', lazy='dynamic'))
    rules = db.relationship('Rule', secondary=room_rules, backref=db.backref('rooms', lazy='dynamic'))

    @property
    def display_price(self):
        """Return the price formatted for display (multiplied by 1000 and converted to integer)"""
        return int(self.price_per_hour * 1000)

    @property
    def display_price_per_night(self):
        """Return the night price formatted for display (multiplied by 1000 and converted to integer)"""
        return int(self.price_per_night * 1000) if self.price_per_night else None

    def __repr__(self):
        return f'<Room {self.title}>'

class RoomImage(db.Model):
    __tablename__ = 'room_image'
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(200))
    is_featured = db.Column(db.Boolean, default=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    
    def __repr__(self):
        return f'<RoomImage {self.id} for Room {self.room_id}>'

# Bảng phân loại tiện nghi
class AmenityCategory(db.Model):
    __tablename__ = 'amenity_category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # VD: "Tiện nghi phòng", "Tiện nghi phổ biến"
    code = db.Column(db.String(50), nullable=False, unique=True)  # VD: "room", "common", "unique"
    icon = db.Column(db.String(100), nullable=True)  # Bootstrap icon
    description = db.Column(db.Text, nullable=True)
    display_order = db.Column(db.Integer, default=0)  # Thứ tự hiển thị
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    amenities = db.relationship('Amenity', backref='amenity_category', lazy=True)
    
    def __repr__(self):
        return f'<AmenityCategory {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'icon': self.icon,
            'description': self.description,
            'display_order': self.display_order,
            'is_active': self.is_active
        }

class Amenity(db.Model):
    __tablename__ = 'amenity'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(100), nullable=False)  # Tên biểu tượng Bootstrap
    description = db.Column(db.Text, nullable=True)  # Mô tả thêm về tiện nghi
    display_order = db.Column(db.Integer, default=0)  # Thứ tự hiển thị
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Key tới AmenityCategory
    category_id = db.Column(db.Integer, db.ForeignKey('amenity_category.id'), nullable=False)
    
    def __repr__(self):
        return f'<Amenity {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'icon': self.icon,
            'description': self.description,
            'category_id': self.category_id,
            'category_name': self.amenity_category.name if self.amenity_category else None,
            'display_order': self.display_order,
            'is_active': self.is_active
        }

class Rule(db.Model):
    __tablename__ = 'rule'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # VD: "Không hút thuốc"
    icon = db.Column(db.String(100), nullable=False)  # Bootstrap icon class
    type = db.Column(db.String(20), nullable=False)  # 'allowed' hoặc 'not_allowed'
    category = db.Column(db.String(50), nullable=False)  # 'smoking', 'pets', 'children', 'party', 'time', 'other'
    description = db.Column(db.Text, nullable=True)  # Mô tả chi tiết
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Rule {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'icon': self.icon,
            'type': self.type,
            'category': self.category,
            'description': self.description
        }

class Booking(db.Model):
    __tablename__ = 'booking'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    total_hours = db.Column(db.Integer)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    renter_id = db.Column(db.Integer, db.ForeignKey('renter.id'), nullable=False)
    
    payment_status = db.Column(db.String(20), default='pending')
    payment_date = db.Column(db.DateTime, nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)
    payment_reference = db.Column(db.String(100), nullable=True)
    
    booking_type = db.Column(db.String(20), default='hourly')  # 'hourly' hoặc 'nightly'
    
    def __repr__(self):
        return f'<Booking {self.id}>'

class Review(db.Model):
    __tablename__ = 'review'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    renter_id = db.Column(db.Integer, db.ForeignKey('renter.id'))
    
    def __repr__(self):
        return f'<Review {self.id} for Room {self.room_id}>'

class Statistics(db.Model):
    __tablename__ = 'statistics'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    
    # Thống kê tổng quan
    total_users = db.Column(db.Integer, default=0)
    total_owners = db.Column(db.Integer, default=0)
    total_renters = db.Column(db.Integer, default=0)
    total_rooms = db.Column(db.Integer, default=0)
    
    # Thống kê đặt phòng
    total_bookings = db.Column(db.Integer, default=0)
    hourly_bookings = db.Column(db.Integer, default=0)
    overnight_bookings = db.Column(db.Integer, default=0)
    total_hours = db.Column(db.Integer, default=0)
    
    # Tỷ lệ và đánh giá
    booking_rate = db.Column(db.Float, default=0)
    common_type = db.Column(db.String(50))
    average_rating = db.Column(db.Float, default=0)
    
    # Thống kê theo thời gian
    hourly_stats = db.Column(db.Text)
    overnight_stats = db.Column(db.Text)
    
    # Thống kê phòng nổi bật
    top_rooms = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Statistics for {self.date}>'

class RoomDeletionLog(db.Model):
    __tablename__ = 'room_deletion_log'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, nullable=False)  # ID phòng đã bị xóa
    room_title = db.Column(db.String(100), nullable=False)  # Tên phòng
    owner_id = db.Column(db.Integer, db.ForeignKey('owner.id'), nullable=False)
    owner_name = db.Column(db.String(100), nullable=False)  # Tên owner
    delete_reason = db.Column(db.Text, nullable=False)  # Lý do xóa
    deleted_at = db.Column(db.DateTime, default=datetime.utcnow)  # Thời gian xóa
    
    # Additional info
    room_address = db.Column(db.String(200), nullable=True)
    room_price = db.Column(db.Float, nullable=True)
    
    # Relationship
    owner = db.relationship('Owner', backref=db.backref('deleted_rooms_log', lazy=True))
    
    def __repr__(self):
        return f'<RoomDeletionLog {self.room_title} deleted by {self.owner_name}>'