from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import json
from app.utils.payment_utils import encrypt_api_key, decrypt_api_key

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
    
    # Email verification fields
    email_verified = db.Column(db.Boolean, default=False)
    first_login = db.Column(db.Boolean, default=True)
    
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
        
    @property
    def title(self):
        """Return a title for the homestay (owner)"""
        return self.full_name or self.username or "My Homestay"
    
    @property
    def display_name(self):
        """Trả về tên hiển thị của owner"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.full_name:
            return self.full_name
        elif self.username:
            return self.username
        else:
            return self.email.split('@')[0]  # Fallback to email prefix
    
    @property
    def city(self):
        """Return the city from one of the owner's homes"""
        if self.homes:
            return self.homes[0].city
        return "Chưa cập nhật"
        
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
    
    # Email verification fields
    email_verified = db.Column(db.Boolean, default=False)
    first_login = db.Column(db.Boolean, default=True)
    
    # Relationships
    bookings = db.relationship('Booking', backref='renter', lazy=True)
    reviews = db.relationship('Review', backref='renter', lazy=True)
    
    def __init__(self, username, email, full_name=None, first_name=None, last_name=None,
                 gender='Nam', address=None, birth_date=None, phone=None, avatar=None,
                 is_active=True, temp_role='renter', is_google=False, is_facebook=False,
                 google_id=None, facebook_id=None, google_username=None, facebook_username=None,
                 email_verified=False, first_login=True):
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
        self.email_verified = email_verified
        self.first_login = first_login

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
    
    @property
    def display_name(self):
        """Trả về tên hiển thị của renter"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.full_name:
            return self.full_name
        elif self.username:
            return self.username
        else:
            return self.email.split('@')[0]  # Fallback to email prefix
        
    def __repr__(self):
        return f'<Renter {self.username}>'

#######################################
# 2. Các bảng liên quan đến Home      #
#######################################

# Bảng liên kết nhiều-nhiều giữa Home và Amenity
home_amenities = db.Table('home_amenities',
    db.Column('home_id', db.Integer, db.ForeignKey('home.id'), primary_key=True),
    db.Column('amenity_id', db.Integer, db.ForeignKey('amenity.id'), primary_key=True)
)

# Bảng liên kết nhiều-nhiều giữa Home và Rule
home_rules = db.Table('home_rules',
    db.Column('home_id', db.Integer, db.ForeignKey('home.id'), primary_key=True),
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

class Home(db.Model):
    __tablename__ = 'home'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    home_type = db.Column(db.String(50), nullable=False)  # Loại nhà: Standard, Deluxe, Suite, etc.
    accommodation_type = db.Column(db.String(50), nullable=False, default='entire_home')  # 'entire_home' hoặc 'private_room'
    
    # Thông tin địa chỉ
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    district = db.Column(db.String(50), nullable=False)
    floor_number = db.Column(db.Integer, nullable=False, default=1)
    
    # Thông tin nhà
    home_number = db.Column(db.String(100), nullable=True)  # Có thể không cần số nhà
    bed_count = db.Column(db.Integer, nullable=False)
    bathroom_count = db.Column(db.Integer, nullable=False)
    max_guests = db.Column(db.Integer, nullable=False)
    
    # Giá và mô tả
    price_per_hour = db.Column(db.Float, nullable=True)  # Allow NULL for homes that only have nightly pricing
    price_per_night = db.Column(db.Float, nullable=True)  # Thêm giá theo đêm
    
    # Enhanced pricing structure for flexible hourly pricing
    price_first_2_hours = db.Column(db.Float, nullable=True)  # Giá 2 giờ đầu
    price_per_additional_hour = db.Column(db.Float, nullable=True)  # Giá 1 giờ sau
    price_overnight = db.Column(db.Float, nullable=True)  # Giá qua đêm (21h-8h)
    price_daytime = db.Column(db.Float, nullable=True)  # Giá qua ngày (9h-20h)
    price_per_day = db.Column(db.Float, nullable=True)  # Giá theo ngày
    
    description = db.Column(db.Text, nullable=True)
    
    # Hoa hồng cho từng căn
    commission_percent = db.Column(db.Float, nullable=True, default=10.0)  # Phần trăm hoa hồng, mặc định 10%
    
    # Trạng thái và thời gian
    is_active = db.Column(db.Boolean, default=True)
    is_booked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def is_available(self):
        # A home is available if it's both active and not currently booked
        return self.is_active and not self.is_booked
    
    # Liên kết với Owner
    owner_id = db.Column(db.Integer, db.ForeignKey('owner.id'), nullable=False)
    owner = db.relationship('Owner', backref=db.backref('homes', lazy=True))
    
    # Relationships
    images = db.relationship('HomeImage', backref='home', lazy=True, cascade="all, delete-orphan")
    bookings = db.relationship('Booking', backref='home', lazy=True, cascade="all, delete-orphan")
    reviews = db.relationship('Review', backref='home', lazy=True)
    amenities = db.relationship('Amenity', secondary=home_amenities, backref=db.backref('homes', lazy='dynamic'))
    rules = db.relationship('Rule', secondary=home_rules, backref=db.backref('homes', lazy='dynamic'))

    @property
    def homestay(self):
        """Return the homestay (owner) for this home"""
        return self.owner
    
    @property
    def homestay_id(self):
        """Return the homestay (owner) ID for this home"""
        return self.owner_id

    @property
    def display_price(self):
        """Return formatted price per hour - prioritize enhanced pricing"""
        if self.price_first_2_hours and self.price_first_2_hours > 0:
            return self.price_first_2_hours
        return self.price_per_hour or 0

    @property
    def display_price_per_night(self):
        """Return formatted price per night - prioritize enhanced pricing"""
        if self.price_per_day and self.price_per_day > 0:
            return self.price_per_day
        return self.price_per_night or 0

    @property
    def revenue(self):
        # Tổng doanh thu của phòng là tổng total_price của các booking đã hoàn thành
        if not self.bookings:
            return 0
        return sum([b.total_price for b in self.bookings if getattr(b, 'status', None) == 'completed'])

    @property
    def rental_status(self):
        """
        Determine current rental status based on bookings
        Returns: tuple (status_text, status_class)
        - không trong giờ thuê -> "Trống" - xanh lá (status-available)
        - trước giờ thuê 15p -> "Check-in" - màu vàng (status-checkin)  
        - đang được thuê -> "Đang ở" - màu cam (status-occupied)
        - dọn dẹp (1 tiếng sau khi thuê xong) -> "Dọn dẹp" - xanh dương (status-cleaning)
        """
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        
        # Get active bookings (confirmed, active, or paid)
        active_bookings = [b for b in self.bookings if b.status in ['confirmed', 'active'] and b.payment_status == 'paid']
        
        # First, check for highest priority statuses
        for booking in active_bookings:
            if not booking.start_time or not booking.end_time:
                continue
                
            # Check if currently rented (between start and end time) - HIGHEST PRIORITY
            if booking.start_time <= now <= booking.end_time:
                return ("Đang ở", "status-occupied")
        
        # Second, check for upcoming check-ins - SECOND PRIORITY
        for booking in active_bookings:
            if not booking.start_time or not booking.end_time:
                continue
                
            # Check if check-in is within 15 minutes
            if booking.start_time > now and (booking.start_time - now).total_seconds() <= 15 * 60:
                return ("Check-in", "status-checkin")
        
        # Third, check for cleaning period - THIRD PRIORITY
        # Only show cleaning if there's no upcoming check-in within the next hour
        for booking in active_bookings:
            if not booking.start_time or not booking.end_time:
                continue
                
            # Check if in cleaning period (1 hour after checkout)
            if booking.end_time < now and (now - booking.end_time).total_seconds() <= 60 * 60:
                # Before showing cleaning status, check if there's any upcoming booking within the next hour
                has_upcoming_checkin = False
                for future_booking in active_bookings:
                    if (future_booking.start_time and future_booking.start_time > now and 
                        (future_booking.start_time - now).total_seconds() <= 60 * 60):  # Within next hour
                        has_upcoming_checkin = True
                        break
                
                # Only show cleaning if no upcoming check-in
                if not has_upcoming_checkin:
                    return ("Dọn dẹp", "status-cleaning")
        
        # Default: available
        return ("Trống", "status-available")

    def __repr__(self):
        return f'<Home {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'home_type': self.home_type,
            'accommodation_type': self.accommodation_type,
            'address': self.address,
            'city': self.city,
            'district': self.district,
            'floor_number': self.floor_number,
            'home_number': self.home_number,
            'bed_count': self.bed_count,
            'bathroom_count': self.bathroom_count,
            'max_guests': self.max_guests,
            'price_per_hour': self.price_per_hour,
            'price_per_night': self.price_per_night,
            'price_first_2_hours': self.price_first_2_hours,
            'price_per_additional_hour': self.price_per_additional_hour,
            'price_overnight': self.price_overnight,
            'price_daytime': self.price_daytime,
            'price_per_day': self.price_per_day,
            'description': self.description,
            'is_active': self.is_active,
            'is_booked': self.is_booked,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'owner_id': self.owner_id
        }

class HomeImage(db.Model):
    __tablename__ = 'home_image'
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(200))
    is_featured = db.Column(db.Boolean, default=False)
    home_id = db.Column(db.Integer, db.ForeignKey('home.id'), nullable=False)
    
    def __repr__(self):
        return f'<HomeImage {self.id} for Home {self.home_id}>'

# Bảng phân loại tiện nghi
class AmenityCategory(db.Model):
    __tablename__ = 'amenity_category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # VD: "Tiện nghi nhà", "Tiện nghi phổ biến"
    code = db.Column(db.String(50), nullable=False, unique=True)  # VD: "home", "common", "unique"
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
    
    home_id = db.Column(db.Integer, db.ForeignKey('home.id'), nullable=False)
    renter_id = db.Column(db.Integer, db.ForeignKey('renter.id'), nullable=False)
    
    payment_status = db.Column(db.String(20), default='pending')
    payment_date = db.Column(db.DateTime, nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)
    payment_reference = db.Column(db.String(100), nullable=True)
    
    booking_type = db.Column(db.String(20), default='hourly')  # 'hourly' hoặc 'daily'
    
    @property
    def homestay(self):
        """Return the homestay (owner) for this booking"""
        return self.home.homestay if self.home else None
    
    @property
    def homestay_id(self):
        """Return the homestay (owner) ID for this booking"""
        return self.home.owner_id if self.home else None
    
    def get_display_status(self):
        """
        Trả về trạng thái hiển thị cho renter với màu sắc tương ứng
        """
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        
        # 1. Trạng thái hủy - màu đỏ
        if self.status == 'cancelled':
            return {
                'text': 'Hủy đặt phòng',
                'color': 'danger',  # đỏ
                'icon': 'x-circle-fill'
            }
        
        # 2. Chờ thanh toán - màu xám
        if self.payment_status != 'paid':
            return {
                'text': 'Chờ thanh toán',
                'color': 'secondary',  # xám
                'icon': 'clock-fill'
            }
        
        # 3. Hoàn thành - màu xanh lá (đã kết thúc thời gian thuê)
        if now >= self.end_time:
            return {
                'text': 'Hoàn thành',
                'color': 'success',  # xanh lá
                'icon': 'check-circle-fill'
            }
        
        # 4. Đang tận hưởng - màu xanh dương (đang trong thời gian thuê)
        if self.start_time <= now < self.end_time:
            return {
                'text': 'Đang tận hưởng',
                'color': 'info',  # xanh dương
                'icon': 'heart-fill'
            }
        
        # 5. Check-in - màu vàng (trước giờ thuê 15 phút)
        if self.status == 'confirmed' and self.payment_status == 'paid':
            checkin_time = self.start_time - timedelta(minutes=15)
            if checkin_time <= now < self.start_time:
                return {
                    'text': 'Check-in',
                    'color': 'warning',  # màu vàng
                    'icon': 'door-open-fill'
                }
        
        # 6. Chờ nhận phòng - màu cam (đã thanh toán, chưa đến thời gian thuê)
        if self.status == 'confirmed' and self.payment_status == 'paid' and now < self.start_time:
            return {
                'text': 'Chờ nhận phòng',
                'color': 'orange',  # màu cam
                'icon': 'house-check-fill'
            }
        
        # Mặc định
        return {
            'text': self.status.capitalize(),
            'color': 'secondary',
            'icon': 'info-circle-fill'
        }
    
    def __repr__(self):
        return f'<Booking {self.id}>'

class Review(db.Model):
    __tablename__ = 'review'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    home_id = db.Column(db.Integer, db.ForeignKey('home.id'))
    renter_id = db.Column(db.Integer, db.ForeignKey('renter.id'))
    
    def __repr__(self):
        return f'<Review {self.id} for Home {self.home_id}>'

class Statistics(db.Model):
    __tablename__ = 'statistics'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    
    # Thống kê tổng quan
    total_users = db.Column(db.Integer, default=0)
    total_owners = db.Column(db.Integer, default=0)
    total_renters = db.Column(db.Integer, default=0)
    total_homes = db.Column(db.Integer, default=0)
    
    # Thống kê đặt nhà
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
    
    # Thống kê nhà nổi bật
    top_homes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Statistics for {self.date}>'

class HomeDeletionLog(db.Model):
    __tablename__ = 'home_deletion_log'
    id = db.Column(db.Integer, primary_key=True)
    home_id = db.Column(db.Integer, nullable=False)  # ID nhà đã bị xóa
    home_title = db.Column(db.String(100), nullable=False)  # Tên nhà
    owner_id = db.Column(db.Integer, db.ForeignKey('owner.id'), nullable=False)
    owner_name = db.Column(db.String(100), nullable=False)  # Tên owner
    delete_reason = db.Column(db.Text, nullable=False)  # Lý do xóa
    deleted_at = db.Column(db.DateTime, default=datetime.utcnow)  # Thời gian xóa
    
    # Additional info
    home_address = db.Column(db.String(200), nullable=True)
    home_price = db.Column(db.Float, nullable=True)
    
    # Relationship
    owner = db.relationship('Owner', backref=db.backref('deleted_homes_log', lazy=True))
    
    def __repr__(self):
        return f'<HomeDeletionLog {self.home_title} deleted by {self.owner_name}>'

class PaymentConfig(db.Model):
    __tablename__ = 'payment_config'
    id = db.Column(db.Integer, primary_key=True)
    
    # Thông tin owner
    owner_id = db.Column(db.Integer, db.ForeignKey('owner.id'), nullable=False, unique=True)
    
    # PayOS Configuration
    _payos_client_id = db.Column('payos_client_id', db.String(100), nullable=False)
    _payos_api_key = db.Column('payos_api_key', db.String(200), nullable=False)
    _payos_checksum_key = db.Column('payos_checksum_key', db.String(200), nullable=False)
    
    # Trạng thái và thời gian
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    owner = db.relationship('Owner', backref=db.backref('payment_config', uselist=False, lazy=True))
    
    @property
    def payos_client_id(self):
        return self._payos_client_id
    @payos_client_id.setter
    def payos_client_id(self, value):
        self._payos_client_id = value

    @property
    def payos_api_key(self):
        return decrypt_api_key(self._payos_api_key)
    @payos_api_key.setter
    def payos_api_key(self, value):
        self._payos_api_key = encrypt_api_key(value)

    @property
    def payos_checksum_key(self):
        return decrypt_api_key(self._payos_checksum_key)
    @payos_checksum_key.setter
    def payos_checksum_key(self, value):
        self._payos_checksum_key = encrypt_api_key(value)

    def __repr__(self):
        return f'<PaymentConfig for Owner {self.owner_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'owner_id': self.owner_id,
            'payos_client_id': self.payos_client_id,
            'payos_api_key': self.payos_api_key,
            'payos_checksum_key': self.payos_checksum_key,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Payment(db.Model):
    __tablename__ = 'payment'
    id = db.Column(db.Integer, primary_key=True)
    
    # Thông tin giao dịch
    payment_code = db.Column(db.String(100), unique=True, nullable=False)  # Mã giao dịch PayOS
    order_code = db.Column(db.String(100), unique=True, nullable=False)    # Mã đơn hàng nội bộ
    amount = db.Column(db.Float, nullable=False)  # Số tiền thanh toán
    currency = db.Column(db.String(10), default='VND')  # Loại tiền tệ
    
    # Thông tin giao dịch PayOS
    payos_transaction_id = db.Column(db.String(100), nullable=True)  # Transaction ID từ PayOS
    payos_signature = db.Column(db.String(500), nullable=True)  # Chữ ký xác thực từ PayOS
    checkout_url = db.Column(db.String(500), nullable=True)  # Link thanh toán PayOS
    
    # Trạng thái giao dịch
    status = db.Column(db.String(20), default='pending')  # pending, success, failed, cancelled
    payment_method = db.Column(db.String(50), nullable=True)  # bank_transfer, e_wallet, etc.
    
    # Thông tin thời gian
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at = db.Column(db.DateTime, nullable=True)  # Thời gian thanh toán thành công
    
    # Thông tin bổ sung
    description = db.Column(db.Text, nullable=True)  # Mô tả giao dịch
    customer_name = db.Column(db.String(100), nullable=True)  # Tên khách hàng
    customer_email = db.Column(db.String(120), nullable=True)  # Email khách hàng
    customer_phone = db.Column(db.String(20), nullable=True)  # SĐT khách hàng
    
    # Foreign Keys
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('owner.id'), nullable=False)
    renter_id = db.Column(db.Integer, db.ForeignKey('renter.id'), nullable=False)
    
    # Relationships
    booking = db.relationship('Booking', backref=db.backref('payments', lazy=True))
    owner = db.relationship('Owner', backref=db.backref('payments', lazy=True))
    renter = db.relationship('Renter', backref=db.backref('payments', lazy=True))
    
    def __repr__(self):
        return f'<Payment {self.payment_code} - {self.status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'payment_code': self.payment_code,
            'order_code': self.order_code,
            'amount': self.amount,
            'currency': self.currency,
            'payos_transaction_id': self.payos_transaction_id,
            'status': self.status,
            'payment_method': self.payment_method,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'description': self.description,
            'customer_name': self.customer_name,
            'customer_email': self.customer_email,
            'customer_phone': self.customer_phone,
            'booking_id': self.booking_id,
            'owner_id': self.owner_id,
            'renter_id': self.renter_id
        }
    
    @property
    def is_successful(self):
        """Kiểm tra xem giao dịch có thành công không"""
        return self.status == 'success'
    
    @property
    def is_pending(self):
        """Kiểm tra xem giao dịch có đang chờ xử lý không"""
        return self.status == 'pending'
    
    @property
    def is_failed(self):
        """Kiểm tra xem giao dịch có thất bại không"""
        return self.status == 'failed'
    
    @property
    def formatted_amount(self):
        """Trả về số tiền đã được format"""
        return f"{self.amount:,.0f} {self.currency}"
    
    def mark_as_successful(self, payos_transaction_id=None, payment_method=None):
        """Đánh dấu giao dịch thành công"""
        self.status = 'success'
        self.paid_at = datetime.utcnow()
        if payos_transaction_id:
            self.payos_transaction_id = payos_transaction_id
        if payment_method:
            self.payment_method = payment_method
        self.updated_at = datetime.utcnow()
    
    def mark_as_failed(self, reason=None):
        """Đánh dấu giao dịch thất bại"""
        self.status = 'failed'
        if reason:
            self.description = f"{self.description or ''} - Lý do thất bại: {reason}"
        self.updated_at = datetime.utcnow()
    
    def mark_as_cancelled(self, reason=None):
        """Đánh dấu giao dịch bị hủy"""
        self.status = 'cancelled'
        if reason:
            self.description = f"{self.description or ''} - Lý do hủy: {reason}"
        self.updated_at = datetime.utcnow()
