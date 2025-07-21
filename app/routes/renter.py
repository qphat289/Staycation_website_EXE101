from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user, logout_user
from app.models.models import Booking, Review, db, Home, HomeImage, Admin, Owner, Renter, Amenity, AmenityCategory, Rule
from datetime import datetime, timedelta
from PIL import Image
import io
import os
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload
from app.utils.utils import get_rank_info, get_location_name, save_user_image, delete_user_image, fix_image_orientation, allowed_file
from app.utils.email_validator import process_email
from app.utils.password_validator import PasswordValidator
from app.utils.email_service import email_service
import random
import string
from flask import session
import logging

logger = logging.getLogger(__name__)

renter_bp = Blueprint('renter', __name__, url_prefix='/renter')

def update_booking_status(bookings):
    """
    Utility function để cập nhật trạng thái booking dựa trên thời gian thực tế
    """
    now = datetime.utcnow()
    updated = False
    
    for booking in bookings:
        # Chỉ cập nhật booking đã thanh toán
        if booking.payment_status == 'paid':
            # Nếu đã qua thời gian kết thúc -> completed
            if now >= booking.end_time and booking.status != 'completed':
                booking.status = 'completed'
                updated = True
            # Nếu đã đến thời gian bắt đầu nhưng chưa qua thời gian kết thúc -> active
            elif now >= booking.start_time and now < booking.end_time and booking.status == 'confirmed':
                booking.status = 'active'
                updated = True
    
    return updated

# Custom decorator for password change API endpoints
def password_change_api_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'message': 'Bạn phải đăng nhập để thực hiện thao tác này'}), 401
        
        if not current_user.is_renter():
            return jsonify({'success': False, 'message': 'Chỉ Renter mới có thể đổi mật khẩu'}), 403
            
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Custom decorator to ensure user is a renter
def renter_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_renter():
            # Check if this is an API request
            if request.headers.get('Content-Type') == 'application/json' or request.path.startswith('/renter/change-password/'):
                return jsonify({'success': False, 'message': 'Bạn phải đăng nhập để thực hiện thao tác này'}), 401
            else:
                flash('You must be a renter to access this page', 'danger')
                return redirect(url_for('home'))
        
        # Kiểm tra nếu là owner đang dùng chế độ xem renter
        # Chỉ ngăn chặn các chức năng booking/đặt nhà
        if current_user.__class__.__name__ == 'Owner' and current_user.is_renter() and request.endpoint in ['renter.book_home', 'renter.cancel_booking']:
            flash('Bạn đang ở chế độ xem, không thể thực hiện đặt nhà', 'warning')
            return redirect(url_for('home'))
            
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Custom decorator to check email verification for booking
def require_email_verification_for_booking(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_renter():
            flash('You must be a renter to access this page', 'danger')
            return redirect(url_for('home'))
        
        # Kiểm tra email verification
        if not current_user.email_verified:
            flash('Vui lòng xác thực email trước khi thực hiện đặt phòng', 'warning')
            return redirect(url_for('renter.verify_email'))
            
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@renter_bp.route('/dashboard')
@renter_required
def dashboard():
    bookings = Booking.query.filter_by(renter_id=current_user.id).all()
    
    # Cập nhật trạng thái booking
    updated = update_booking_status(bookings)
    if updated:
        db.session.commit()
    
    return render_template('renter/dashboard.html', bookings=bookings)

@renter_bp.route('/verify-email')
@login_required
def verify_email():
    """Trang verify email cho Renter"""
    if not current_user.is_renter():
        flash('Chỉ Renter mới có thể truy cập trang này', 'danger')
        return redirect(url_for('auth.login'))
    
    if current_user.email_verified:
        flash('Email đã được xác thực', 'info')
        return redirect(url_for('renter.dashboard'))
    
    return render_template('renter/verify_email.html')

# City and district mapping
CITY_MAPPING = {
    'TP. Hồ Chí Minh': 'TP. Hồ Chí Minh',  # Use the actual names stored in the database
    'Hà Nội': 'Hà Nội',
    'Đà Nẵng': 'Đà Nẵng',
    'Hội An': 'Hội An',
    'Đà Lạt': 'Đà Lạt',
    'Nha Trang': 'Nha Trang',
    'Huế': 'Huế',
    'Vũng Tàu': 'Vũng Tàu'
}

DISTRICT_MAPPING = {
    'Quận 1': 'quan1',
    'Quận 2': 'quan2',
    'Quận 3': 'quan3',
    'Quận 4': 'quan4',
    'Quận 5': 'quan5',
    'Quận 6': 'quan6',
    'Quận 7': 'quan7',
    'Quận 8': 'quan8',
    'Quận 9': 'quan9',
    'Quận 10': 'quan10',
    'Quận 11': 'quan11',
    'Quận 12': 'quan12',
    'Quận Bình Thạnh': 'quan_binh_thanh',
    'Quận Tân Bình': 'quan_tan_binh',
    'Quận Gò Vấp': 'quan_go_vap',
    'Quận Phú Nhuận': 'quan_phu_nhuan',
    'Quận Tân Phú': 'quan_tan_phu',
    'Quận Bình Tân': 'quan_binh_tan',
    'Quận Thủ Đức': 'quan_thu_duc'
}

def _get_location_db_value(location):
    """Helper function to get database value for location"""
    if location in CITY_MAPPING:
        return CITY_MAPPING[location]
    elif location in DISTRICT_MAPPING:
        return DISTRICT_MAPPING[location]
    return location

def _build_location_filters(location):
    """Helper function to build location filters"""
    location_db = _get_location_db_value(location)
    
    filters = []
    # Search in city, district, title, and address (case insensitive)
    for field in [Home.city, Home.district, Home.title, Home.address]:
        filters.append(field.ilike(f'%{location}%'))
        if location_db != location:
            filters.append(field.ilike(f'%{location_db}%'))
    
    return filters

def _build_price_filters(booking_type, min_price=None, max_price=None):
    """Helper function to build price filters"""
    if booking_type == 'hourly':
        availability_fields = [Home.price_per_hour, Home.price_first_2_hours, Home.price_per_additional_hour]
    else:
        availability_fields = [Home.price_per_night, Home.price_per_day, Home.price_overnight, Home.price_daytime]
    
    # First, ensure availability
    availability_filter = db.or_(*[
        db.and_(field.isnot(None), field > 0) for field in availability_fields
    ])
    
    # Then apply price range if specified
    price_filters = []
    if min_price is not None or max_price is not None:
        for field in availability_fields:
            conditions = [db.and_(field.isnot(None), field > 0)]
            if min_price is not None:
                conditions.append(field >= min_price)
            if max_price is not None:
                conditions.append(field <= max_price)
            
            if len(conditions) > 1:
                price_filters.append(db.and_(*conditions))
    
    return availability_filter, price_filters

def _convert_ids_to_integers(ids_list):
    """Helper function to convert string IDs to integers"""
    valid_ids = []
    for id_str in ids_list:
        try:
            valid_ids.append(int(id_str))
        except (ValueError, TypeError):
            continue
    return valid_ids

def _get_filter_options():
    """Helper function to get filter options for dropdowns"""
    cities = [city[0] for city in db.session.query(Home.city).distinct().all() if city[0]]
    cities.sort()
    
    # Map district database values to display names
    district_display_names = {v: k for k, v in DISTRICT_MAPPING.items()}
    districts = []
    for district in db.session.query(Home.district).distinct().all():
        if district[0]:
            display_name = district_display_names.get(district[0], district[0])
            if display_name not in districts:
                districts.append(display_name)
    districts.sort()
    
    home_types = [rt[0] for rt in db.session.query(Home.home_type).distinct().all() if rt[0]]
    
    return cities, districts, home_types

@renter_bp.route('/search')
def search():
    """Search for rooms with filters"""
    # Get search parameters
    location = request.args.get('location', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    room_type = request.args.get('room_type', '')
    booking_type = request.args.get('booking_type', 'daily')
    city = request.args.get('city', '')
    district = request.args.get('district', '')
    
    # Get guest parameters
    adults = request.args.get('adults', type=int, default=1)
    children = request.args.get('children', type=int, default=0)
    total_guests = adults + children if adults is not None and children is not None else None
    
    # Get amenity and rule filters
    amenity_ids = request.args.getlist('amenities')
    rule_ids = request.args.getlist('rules')
    
    # Build base query
    query = Home.query.filter_by(is_active=True)
    
    # Apply location filters
    if location:
        location_filters = _build_location_filters(location)
        query = query.filter(db.or_(*location_filters))
    
    # Apply price filters
    availability_filter, price_filters = _build_price_filters(booking_type, min_price, max_price)
    query = query.filter(availability_filter)
    if price_filters:
        query = query.filter(db.or_(*price_filters))
    
    # Apply other filters
    if room_type:
        query = query.filter(Home.home_type == room_type)
    
    if total_guests is not None:
        query = query.filter(Home.max_guests >= total_guests)
    
    if city:
        city_db = CITY_MAPPING.get(city, city)
        query = query.filter(Home.city == city_db)
    
    if district:
        district_db = DISTRICT_MAPPING.get(district, district)
        query = query.filter(Home.district == district_db)
    
    # Apply amenity filters
    valid_amenity_ids = _convert_ids_to_integers(amenity_ids)
    for amenity_id in valid_amenity_ids:
        query = query.filter(Home.amenities.any(Amenity.id == amenity_id))
    
    # Apply rule filters
    valid_rule_ids = _convert_ids_to_integers(rule_ids)
    for rule_id in valid_rule_ids:
        query = query.filter(Home.rules.any(Rule.id == rule_id))
    
    # Execute query
    homes = query.all()

    # Lọc loại home có booking trùng thời gian nếu là hourly
    if booking_type == 'hourly':
        search_date = request.args.get('checkin_date') or request.args.get('start_date_hourly')
        search_time = request.args.get('checkin_time') or request.args.get('start_time')
        hours_duration = request.args.get('hours_duration') or request.args.get('duration_hourly')
        if search_date and search_time and hours_duration:
            from datetime import datetime, timedelta
            try:
                start_dt = datetime.strptime(f"{search_date} {search_time}", "%Y-%m-%d %H:%M")
                end_dt = start_dt + timedelta(hours=int(hours_duration))
                filtered_homes = []
                for home in homes:
                    bookings = Booking.query.filter(
                        Booking.home_id == home.id,
                        Booking.status.in_(['pending', 'confirmed', 'active']),
                        Booking.start_time < end_dt,
                        Booking.end_time > start_dt
                    ).all()
                    if not bookings:
                        filtered_homes.append(home)
                homes = filtered_homes
            except Exception as e:
                pass
    
    # Get filter options
    cities, districts, home_types = _get_filter_options()
    
    # Get amenities and categories for filter
    amenity_categories = AmenityCategory.query.filter_by(is_active=True).order_by(AmenityCategory.display_order).all()
    amenities = Amenity.query.filter_by(is_active=True).options(
        joinedload(Amenity.amenity_category)
    ).order_by(Amenity.display_order).all()
    
    # Get rules for filter
    rules = Rule.query.filter_by(is_active=True).order_by(Rule.name).all()
    
    return render_template('renter/search.html', 
                          homes=homes,
                          cities=cities,
                          districts=districts,
                          home_types=home_types,
                          amenity_categories=amenity_categories,
                          amenities=amenities,
                          rules=rules,
                          selected_amenity_ids=valid_amenity_ids,
                          selected_rule_ids=valid_rule_ids,
                          search_params=request.args)

# --- Thay thế hàm book_home ---
@renter_bp.route('/book/<int:home_id>', methods=['GET', 'POST'])
@require_email_verification_for_booking
def book_home(home_id):
    """Create a booking with default values and redirect to payment"""
    from datetime import datetime, timedelta
    home = Home.query.get_or_404(home_id)
    
    # Check if home is active
    if not home.is_active:
        flash("This home is currently not available for booking.", "danger")
        return redirect(url_for('renter.view_home_detail', home_id=home.id))

    # --- Lấy tham số đặt phòng từ request (ưu tiên nếu có) ---
    booking_type = request.args.get('type') or 'daily'
    date = request.args.get('date')
    time = request.args.get('time')
    duration = request.args.get('duration')
    guests = request.args.get('guests')

    # Nếu là hourly và có đủ tham số thì dùng, nếu không thì fallback như cũ
    if booking_type == 'hourly' and date and time and duration:
        try:
            total_hours = int(duration)
            start_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            end_datetime = start_datetime + timedelta(hours=total_hours)
            # Tính giá
            if total_hours <= 2 and home.price_first_2_hours:
                total_price = home.price_first_2_hours
            elif total_hours > 2 and home.price_first_2_hours and home.price_per_additional_hour:
                total_price = home.price_first_2_hours + (total_hours - 2) * home.price_per_additional_hour
            elif home.price_per_hour:
                total_price = total_hours * home.price_per_hour
            else:
                flash("Nhà này chưa có thông tin giá theo giờ.", "warning")
                return redirect(url_for('renter.view_home_detail', home_id=home.id))
        except Exception as e:
            flash("Thông tin đặt phòng không hợp lệ.", "danger")
            return redirect(url_for('renter.view_home_detail', home_id=home.id))
    else:
        # --- Logic cũ fallback ---
        booking_type = 'daily'  # Default to daily booking
        total_price = 0
        total_hours = 24  # Default 1 day
        price = home.price_per_day if home.price_per_day and home.price_per_day > 0 else home.price_per_night
        if price and price > 0:
            booking_type = 'daily'
            total_price = price
            total_hours = 24
        elif home.price_per_hour and home.price_per_hour > 0:
            booking_type = 'hourly'
            total_price = home.price_per_hour * 2  # Default 2 hours
            total_hours = 2
        elif home.price_first_2_hours and home.price_first_2_hours > 0:
            booking_type = 'hourly'
            total_price = home.price_first_2_hours
            total_hours = 2
        else:
            flash("Nhà này chưa có thông tin giá. Vui lòng liên hệ chủ nhà để cập nhật giá trước khi đặt.", "warning")
            return redirect(url_for('renter.view_home_detail', home_id=home.id))
        now = datetime.utcnow()
        if booking_type == 'daily':
            start_datetime = now.replace(hour=15, minute=0, second=0, microsecond=0) + timedelta(days=1)
            end_datetime = start_datetime + timedelta(days=1)
        else:
            start_datetime = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            end_datetime = start_datetime + timedelta(hours=total_hours)

    # --- Kiểm tra trùng booking ---
    existing_bookings = Booking.query.filter(
        Booking.home_id == home.id,
        Booking.status.in_(['pending', 'confirmed', 'active'])
    ).all()
    for booking in existing_bookings:
        if start_datetime < booking.end_time and end_datetime > booking.start_time:
            flash('This home is not available during the selected time period. Please try a different time.', 'danger')
            return redirect(url_for('renter.view_home_detail', home_id=home.id))

    # --- Tạo booking ---
    new_booking = Booking(
        home_id=home.id,
        renter_id=current_user.id,
        start_time=start_datetime,
        end_time=end_datetime,
        total_hours=total_hours,
        total_price=total_price,
        status='pending',
        payment_status='pending',
        booking_type=booking_type
    )
    db.session.add(new_booking)
    db.session.commit()
    flash('Booking created successfully! Please proceed with payment.', 'success')
    return redirect(url_for('payment.checkout', booking_id=new_booking.id))


@renter_bp.route('/cancel-booking/<int:id>')
@renter_required
def cancel_booking(id):
    """Cancel a booking"""
    booking = Booking.query.get_or_404(id)
    
    # Ensure the current user owns this booking
    if booking.renter_id != current_user.id:
        flash('You do not have permission to cancel this booking', 'danger')
        return redirect(url_for('renter.dashboard'))
    
    # Kiểm tra trạng thái có thể hủy không
    status_info = booking.get_display_status()
    if status_info['text'] not in ['Chờ thanh toán', 'Chờ nhận phòng']:
        flash('Không thể hủy booking ở trạng thái hiện tại', 'danger')
        return redirect(url_for('renter.dashboard'))
    
    # Check if booking can be cancelled (not already started)
    if booking.start_time <= datetime.utcnow():
        flash('Cannot cancel a booking that has already started', 'danger')
        return redirect(url_for('renter.dashboard'))
    
    booking.status = 'cancelled'
    db.session.commit()
    
    flash('Booking cancelled successfully', 'success')
    return redirect(url_for('renter.dashboard'))



@renter_bp.route('/profile', methods=['GET', 'POST'])
@login_required  
def profile():
    if request.method == 'POST':
        try:
            # Cập nhật thông tin cơ bản
            current_user.username = request.form.get('username')
            current_user.first_name = request.form.get('first_name')
            current_user.last_name = request.form.get('last_name')
            current_user.gender = request.form.get('gender')
            # Xử lý email với validation và cleaning
            email_input = request.form.get('email')
            if email_input:
                cleaned_email, is_valid = process_email(email_input)
                if is_valid:
                    current_user.email = cleaned_email
                else:
                    flash('Email không hợp lệ!', 'warning')
            current_user.phone = request.form.get('phone')
            current_user.address = request.form.get('address')
            
            # Xử lý ngày sinh
            birth_day = request.form.get('birth_day')
            birth_month = request.form.get('birth_month')
            birth_year = request.form.get('birth_year')
            
            if birth_day and birth_month and birth_year:
                try:
                    current_user.birth_date = datetime(int(birth_year), int(birth_month), int(birth_day)).date()
                except ValueError:
                    pass  # Ignore invalid date
            
            # Xử lý upload avatar với cấu trúc mới
            avatar_file = request.files.get('avatar')
            if avatar_file and avatar_file.filename and allowed_file(avatar_file.filename):
                # Xóa avatar cũ nếu có
                if current_user.avatar:
                    delete_user_image(current_user.avatar)
                
                # Lưu avatar mới với cấu trúc data/renter/{renter_id}/
                avatar_path = save_user_image(avatar_file, 'renter', current_user.id, prefix='avatar')
                
                if avatar_path:
                    # Xử lý xoay ảnh và resize
                    try:
                        full_path = os.path.join('static', avatar_path)
                        
                        # Sửa hướng xoay ảnh theo EXIF
                        fix_image_orientation(full_path)
                        
                        # Resize image sau khi sửa hướng
                        with Image.open(full_path) as img:
                            # Tạo ảnh vuông bằng cách crop từ giữa
                            width, height = img.size
                            if width != height:
                                # Crop to square from center
                                min_size = min(width, height)
                                left = (width - min_size) // 2
                                top = (height - min_size) // 2
                                right = left + min_size
                                bottom = top + min_size
                                img = img.crop((left, top, right, bottom))
                            
                            # Resize to 200x200
                            img = img.resize((200, 200), Image.Resampling.LANCZOS)
                            img.save(full_path, optimize=True, quality=85)
                    except Exception as e:
                        print(f"Error processing avatar: {e}")
                    
                    current_user.avatar = avatar_path
            
            db.session.commit()
            flash('Cập nhật thông tin thành công!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'danger')
        
        return redirect(url_for('renter.profile'))
    
    return render_template('renter/profile.html')

@renter_bp.route('/check-username', methods=['POST'])
@login_required
def check_username():
    data = request.get_json()
    username = data.get('username')
    
    # Kiểm tra nếu username này là của user hiện tại thì available
    if username == current_user.username:
        return jsonify({'available': True})
    
    existing_owner = Owner.query.filter_by(username=username).first()
    existing_admin = Admin.query.filter_by(username=username).first()
    existing_renter = Renter.query.filter_by(username=username).first()
    
    return jsonify({
        'available': not bool(existing_owner or existing_admin or existing_renter)
    })

@renter_bp.route('/check-email', methods=['POST'])
@login_required
def check_email():
    data = request.get_json()
    email = data.get('email')
    
    # Kiểm tra nếu email này là của user hiện tại thì available
    if email == current_user.email:
        return jsonify({'available': True})
    
    existing_owner = Owner.query.filter_by(email=email).first()
    existing_admin = Admin.query.filter_by(email=email).first()
    existing_renter = Renter.query.filter_by(email=email).first()
    
    return jsonify({
        'available': not bool(existing_owner or existing_admin or existing_renter)
    })

@renter_bp.route('/home/<int:home_id>/review', methods=['GET', 'POST'])
@login_required
def add_review(home_id):
    home = Home.query.get_or_404(home_id)
    
    # Check if the user has already left a review for this home
    existing_review = Review.query.filter_by(home_id=home.id, renter_id=current_user.id).first()
    if existing_review:
        flash('You have already left a review for this home.', 'danger')
        return redirect(url_for('renter.view_home_detail', home_id=home.id))

    if request.method == 'POST':
        rating = int(request.form.get('rating', 5))
        content = request.form.get('content', '')
        
        review = Review(
            rating=rating,
            content=content,
            home_id=home.id,
            renter_id=current_user.id  # CHỖ NÀY ĐÃ ĐỔI user_id -> renter_id
        )
        db.session.add(review)
        db.session.commit()
        flash('Review submitted!', 'success')
        return redirect(url_for('renter.view_home_detail', home_id=home.id))

    return render_template('renter/add_review.html', home=home)

@renter_bp.route('/booking-history')
@renter_required
def booking_history():
    """View booking history for the current renter"""
    bookings = Booking.query.filter_by(renter_id=current_user.id).order_by(Booking.created_at.desc()).all()
    
    # Cập nhật trạng thái booking
    updated = update_booking_status(bookings)
    if updated:
        db.session.commit()
    
    return render_template('renter/booking_history.html', bookings=bookings)

@renter_bp.route('/booking/<int:booking_id>')
@login_required
def booking_details(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    # Optionally ensure the current_user owns this booking
    if booking.renter_id != current_user.id:
        flash("You don't have permission to view this booking.", "danger")
        return redirect(url_for('renter.dashboard'))

    # Cập nhật trạng thái booking
    updated = update_booking_status([booking])
    if updated:
        db.session.commit()

    return render_template('renter/booking_details.html', booking=booking)

@renter_bp.route('/review-booking/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def review_booking(booking_id):
    """
    Displays an existing review or allows the user to post one 
    if they haven't already, for a completed booking.
    """
    booking = Booking.query.get_or_404(booking_id)
    
    # Ensure the current user owns this booking
    if booking.renter_id != current_user.id:
        flash("You don't have permission to review this booking.", "danger")
        return redirect(url_for('renter.dashboard'))
    
    # Ensure the booking is completed
    if booking.status != 'completed':
        flash("You can only review a completed booking.", "danger")
        return redirect(url_for('renter.dashboard'))

    # Check if there's already a review
    existing_review = Review.query.filter_by(
        home_id=booking.home_id,
        renter_id=current_user.id  # ĐÃ ĐỔI user_id -> renter_id
    ).first()

    if request.method == 'POST':
        rating = int(request.form.get('rating', 5))
        content = request.form.get('content', '')

        if existing_review:
            existing_review.rating = rating
            existing_review.content = content
            flash("Your review has been updated!", "success")
        else:
            new_review = Review(
                rating=rating,
                content=content,
                home_id=booking.home_id,
                renter_id=current_user.id  # ĐÃ ĐỔI user_id -> renter_id
            )
            db.session.add(new_review)
            flash("Review submitted!", "success")

        db.session.commit()
        return redirect(url_for('renter.dashboard'))
    
    return render_template('renter/review_booking.html', booking=booking, existing_review=existing_review)

@renter_bp.route('/reviews/<int:home_id>', methods=['GET', 'POST'])
def view_reviews(home_id):
    """
    Displays reviews for home, optionally letting the user post a review if they have a completed booking.
    """
    home = Home.query.get_or_404(home_id)
    
    # Get existing reviews
    reviews = Review.query.filter_by(home_id=home.id).order_by(Review.created_at.desc()).all()
    
    # Determine if user can post (i.e., they have a completed booking)
    can_post = False
    if current_user.is_authenticated and current_user.is_renter():
        completed_booking = Booking.query.filter_by(
            home_id=home.id,
            renter_id=current_user.id,
            status='completed'
        ).first()
        if completed_booking:
            can_post = True

    # If user is trying to post a new or updated review
    if request.method == 'POST':
        if not can_post:
            flash("You can only post a review if you have a completed booking.", "danger")
            return redirect(url_for('renter.view_reviews', home_id=home.id))
        
        rating = int(request.form.get('rating', 5))
        content = request.form.get('content', '')
        
        existing_review = Review.query.filter_by(
            home_id=home.id,
            renter_id=current_user.id  # ĐÃ ĐỔI user_id -> renter_id
        ).first()
        if existing_review:
            existing_review.rating = rating
            existing_review.content = content
            flash("Your review has been updated!", "success")
        else:
            new_review = Review(
                rating=rating,
                content=content,
                home_id=home.id,
                renter_id=current_user.id  # ĐÃ ĐỔI user_id -> renter_id
            )
            db.session.add(new_review)
            flash("Review submitted!", "success")
        db.session.commit()
        return redirect(url_for('renter.view_reviews', home_id=home.id))
    
    write_mode = request.args.get('write')
    
    if write_mode and not can_post:
        flash("You can only post a review if you have a completed booking.", "warning")
    
    return render_template(
        'renter/view_reviews.html',
        home=home,
        reviews=reviews,
        can_post=can_post,
        write_mode=write_mode
    )

# --- Sửa view_home_detail: load home với joinedload, truyền reviews, search_params ---
@renter_bp.route('/view-home/<int:home_id>')
def view_home_detail(home_id):
    # Load home với amenities và category relationships
    home = Home.query.options(
        joinedload(Home.amenities).joinedload(Amenity.amenity_category),
        joinedload(Home.images)
    ).get_or_404(home_id)
    
    # Kiểm tra nếu nhà đã bị khóa
    if not home.is_active:
        flash("Nhà này hiện tại đã ngừng hoạt động và không khả dụng để đặt.", "warning")
        return redirect(url_for('home'))
    
    # Load reviews for this home
    reviews = Review.query.filter_by(home_id=home_id).order_by(Review.created_at.desc()).all()
    
    return render_template('renter/view_home_detail.html', 
                          home=home,
                          reviews=reviews,
                          search_params=request.args)

@renter_bp.route('/settings')
@login_required
def settings():
    return render_template('renter/settings.html')

@renter_bp.route('/update-settings', methods=['POST'])
@login_required
def update_settings():
    email_notifications = request.form.get('email_notifications') == 'on'
    booking_reminders = request.form.get('booking_reminders') == 'on'
    
    current_user.email_notifications = email_notifications
    current_user.booking_reminders = booking_reminders
    db.session.commit()
    
    flash('Cài đặt thông báo đã được cập nhật', 'success')
    return redirect(url_for('renter.settings'))

@renter_bp.route('/update-privacy', methods=['POST'])
@login_required
def update_privacy():
    show_profile = request.form.get('show_profile') == 'on'
    show_booking_history = request.form.get('show_booking_history') == 'on'
    
    current_user.show_profile = show_profile
    current_user.show_booking_history = show_booking_history
    db.session.commit()
    
    flash('Cài đặt quyền riêng tư đã được cập nhật', 'success')
    return redirect(url_for('renter.settings'))

@renter_bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    password = request.form.get('password')
    
    if not current_user.check_password(password):
        flash('Mật khẩu không chính xác', 'danger')
        return redirect(url_for('renter.settings'))
    
    # Xóa tất cả bookings và reviews của user
    Booking.query.filter_by(renter_id=current_user.id).delete()
    Review.query.filter_by(renter_id=current_user.id).delete()
    
    # Xóa user
    db.session.delete(current_user)
    db.session.commit()
    
    logout_user()
    flash('Tài khoản của bạn đã được xóa', 'success')
    return redirect(url_for('home'))

@renter_bp.route('/debug_homes')
def debug_homes():
    """Temporary route to debug home data"""
    homes = Home.query.all()
    result = []
    for home in homes:
        result.append({
            'title': home.title,
            'city': home.city,
            'district': home.district,
            'max_guests': home.max_guests,
            'price_per_hour': home.price_per_hour,
            'price_per_night': home.price_per_night,
            'is_active': home.is_active,
            'home_type': home.home_type
        })
    
    # Also return unique city values for debugging
    unique_cities = db.session.query(Home.city).distinct().all()
    city_list = [city[0] for city in unique_cities]
    
    return jsonify({
        'homes': result,
        'unique_cities': city_list,
        'city_mapping': CITY_MAPPING
    })

@renter_bp.route('/debug_rules')
def debug_rules():
    """Temporary route to debug rule data"""
    # Get all rules
    rules = Rule.query.all()
    rule_data = []
    for rule in rules:
        rule_data.append({
            'id': rule.id,
            'name': rule.name,
            'icon': rule.icon,
            'type': rule.type,
            'category': rule.category,
            'is_active': rule.is_active
        })
    
    # Get a sample home with rules
    sample_home = Home.query.filter(Home.rules.any()).first()
    home_rules = []
    if sample_home:
        for rule in sample_home.rules:
            home_rules.append({
                'id': rule.id,
                'name': rule.name,
                'icon': rule.icon,
                'type': rule.type,
                'category': rule.category
            })
    
    return jsonify({
        'all_rules': rule_data,
        'sample_home_id': sample_home.id if sample_home else None,
        'sample_home_rules': home_rules
    })

@renter_bp.route('/debug_search')
def debug_search():
    """Single comprehensive debug route for search functionality"""
    try:
        # Get basic statistics
        all_homes = Home.query.all()
        active_homes = Home.query.filter_by(is_active=True).all()
        
        # Test different search scenarios
        test_results = {}
        
        if active_homes:
            sample_home = active_homes[0]
            
            # Test basic search
            test_results['basic_search'] = {
                'total_homes': len(all_homes),
                'active_homes': len(active_homes)
            }
            
            # Test location search
            if sample_home.title:
                title_part = sample_home.title[:3]
                title_results = Home.query.filter_by(is_active=True).filter(
                    Home.title.ilike(f'%{title_part}%')
                ).all()
                test_results['title_search'] = {
                    'search_term': title_part,
                    'results': len(title_results)
                }
            
            # Test price availability
            hourly_homes = Home.query.filter_by(is_active=True).filter(
                db.or_(
                    db.and_(Home.price_per_hour.isnot(None), Home.price_per_hour > 0),
                    db.and_(Home.price_first_2_hours.isnot(None), Home.price_first_2_hours > 0)
                )
            ).all()
            
            daily_homes = Home.query.filter_by(is_active=True).filter(
                db.or_(
                    db.and_(Home.price_per_night.isnot(None), Home.price_per_night > 0),
                    db.and_(Home.price_per_day.isnot(None), Home.price_per_day > 0)
                )
            ).all()
            
            test_results['pricing'] = {
                'hourly_homes': len(hourly_homes),
                'daily_homes': len(daily_homes)
            }
            
            # Sample home info
            test_results['sample_home'] = {
                'id': sample_home.id,
                'title': sample_home.title,
                'city': sample_home.city,
                'district': sample_home.district,
                'pricing': {
                    'hourly': sample_home.price_per_hour,
                    'nightly': sample_home.price_per_night,
                    'first_2_hours': sample_home.price_first_2_hours,
                    'per_day': sample_home.price_per_day
                }
            }
        
        return jsonify(test_results)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'type': type(e).__name__
        }), 500

@renter_bp.route('/api/bookings/<int:home_id>/<date>', methods=['GET'])
def get_bookings_by_home_and_date(home_id, date):
    """API: Lấy danh sách booking của 1 home trong 1 ngày (dạng JSON)"""
    try:
        from datetime import datetime, timedelta
        # Parse ngày dạng yyyy-mm-dd
        day = datetime.strptime(date, '%Y-%m-%d')
        start_of_day = day.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        bookings = Booking.query.filter(
            Booking.home_id == home_id,
            Booking.status.in_(['pending', 'confirmed', 'active']),
            Booking.start_time < end_of_day,
            Booking.end_time > start_of_day
        ).all()
        data = [
            {
                'id': b.id,
                'start_time': b.start_time.strftime('%Y-%m-%d %H:%M'),
                'end_time': b.end_time.strftime('%Y-%m-%d %H:%M')
            }
            for b in bookings
        ]
        return jsonify({'success': True, 'bookings': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@renter_bp.route('/debug_booking_status')
def debug_booking_status():
    """Debug route để kiểm tra trạng thái booking"""
    bookings = Booking.query.filter_by(renter_id=current_user.id).all() if current_user.is_authenticated else []
    
    # Cập nhật trạng thái trước khi debug
    updated = update_booking_status(bookings)
    if updated:
        db.session.commit()
    
    result = []
    now = datetime.utcnow()
    
    for booking in bookings:
        status_info = booking.get_display_status()
        
        # Lấy thông tin payment
        payments = booking.payments if hasattr(booking, 'payments') else []
        payment_info = []
        for payment in payments:
            payment_info.append({
                'id': payment.id,
                'amount': payment.amount,
                'status': payment.status,
                'payment_method': payment.payment_method,
                'created_at': payment.created_at.strftime('%Y-%m-%d %H:%M') if payment.created_at else None,
                'paid_at': payment.paid_at.strftime('%Y-%m-%d %H:%M') if payment.paid_at else None
            })
        
        result.append({
            'id': booking.id,
            'database_status': booking.status,
            'payment_status': booking.payment_status,
            'start_time': booking.start_time.strftime('%Y-%m-%d %H:%M'),
            'end_time': booking.end_time.strftime('%Y-%m-%d %H:%M'),
            'display_status': status_info,
            'renter_display_name': booking.renter.display_name if booking.renter else None,
            'payments': payment_info,
            'time_checks': {
                'now_vs_start': 'passed' if now >= booking.start_time else 'not_yet',
                'now_vs_end': 'passed' if now >= booking.end_time else 'not_yet',
                'minutes_to_start': int((booking.start_time - now).total_seconds() / 60) if now < booking.start_time else 'already_started',
                'minutes_to_end': int((booking.end_time - now).total_seconds() / 60) if now < booking.end_time else 'already_ended'
            }
        })
    
    return jsonify({
        'bookings': result,
        'current_time': now.strftime('%Y-%m-%d %H:%M'),
        'current_user_display_name': current_user.display_name if current_user.is_authenticated else None,
        'updated_in_this_request': updated
    })

@renter_bp.route('/payment-history')
@renter_required
def payment_history():
    """Lịch sử thanh toán của renter"""
    # Import Payment model
    from app.models.models import Payment
    
    # Lấy tất cả payment của renter hiện tại
    payments = Payment.query.filter_by(renter_id=current_user.id).order_by(Payment.created_at.desc()).all()
    
    return render_template('renter/payment_history.html', payments=payments)

@renter_bp.route('/payment/<int:payment_id>')
@renter_required
def payment_details(payment_id):
    """Chi tiết giao dịch thanh toán"""
    from app.models.models import Payment
    
    payment = Payment.query.get_or_404(payment_id)
    
    # Kiểm tra quyền truy cập
    if payment.renter_id != current_user.id:
        flash("Bạn không có quyền xem giao dịch này", "danger")
        return redirect(url_for('renter.payment_history'))
    
    return render_template('renter/payment_details.html', payment=payment)

@renter_bp.route('/debug_payment_status/<int:booking_id>')
def debug_payment_status(booking_id):
    """Debug route để kiểm tra trạng thái thanh toán của booking cụ thể"""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Not authenticated'}), 401
    
    from app.models.models import Payment
    
    booking = Booking.query.get_or_404(booking_id)
    
    # Kiểm tra quyền truy cập
    if booking.renter_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Cập nhật trạng thái booking
    updated = update_booking_status([booking])
    if updated:
        db.session.commit()
    
    # Lấy thông tin payment
    payments = Payment.query.filter_by(booking_id=booking_id).all()
    
    payment_data = []
    for payment in payments:
        payment_data.append({
            'id': payment.id,
            'payment_code': payment.payment_code,
            'amount': payment.amount,
            'status': payment.status,
            'payment_method': payment.payment_method,
            'created_at': payment.created_at.strftime('%Y-%m-%d %H:%M:%S') if payment.created_at else None,
            'paid_at': payment.paid_at.strftime('%Y-%m-%d %H:%M:%S') if payment.paid_at else None,
            'payos_transaction_id': payment.payos_transaction_id,
            'is_successful': payment.is_successful,
            'is_pending': payment.is_pending,
            'is_failed': payment.is_failed
        })
    
    # Lấy trạng thái hiển thị
    status_info = booking.get_display_status()
    
    return jsonify({
        'booking': {
            'id': booking.id,
            'database_status': booking.status,
            'payment_status': booking.payment_status,
            'start_time': booking.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': booking.end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_price': booking.total_price,
            'display_status': status_info,
            'updated_in_this_request': updated
        },
        'payments': payment_data,
        'payment_count': len(payments),
        'successful_payments': len([p for p in payments if p.status == 'success']),
        'current_time': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    })

# Password Change Routes
@renter_bp.route('/change-password/send-otp', methods=['POST'])
@password_change_api_required
def send_password_change_otp():
    """Gửi mã OTP để đổi mật khẩu cho Renter"""
    try:
        renter = current_user
        
        # Kiểm tra email đã verify chưa
        if not renter.email_verified:
            return jsonify({'success': False, 'message': 'Vui lòng xác thực email trước khi đổi mật khẩu'}), 400
        
        # Kiểm tra số lần gửi trong ngày
        today = datetime.now().date().isoformat()
        send_count = session.get('password_change_send_count', {}).get(today, 0)
        blocked_until = session.get('password_change_send_blocked_until')
        now = datetime.now()
        
        if send_count >= 3:  # Giới hạn 3 lần/ngày
            if blocked_until:
                blocked_until_dt = datetime.fromisoformat(blocked_until)
                if now < blocked_until_dt:
                    seconds_left = int((blocked_until_dt - now).total_seconds())
                    minutes = seconds_left // 60
                    seconds = seconds_left % 60
                    return jsonify({'success': False, 'message': f'Bạn đã gửi quá 3 lần. Vui lòng thử lại sau {minutes} phút {seconds} giây.'}), 400
                else:
                    send_count = 0
                    session['password_change_send_count'][today] = 0
                    session.pop('password_change_send_blocked_until', None)
            else:
                session['password_change_send_blocked_until'] = (now + timedelta(minutes=5)).isoformat()
                return jsonify({'success': False, 'message': 'Bạn đã gửi quá 3 lần. Vui lòng thử lại sau 5 phút.'}), 400
        
        # Validate current password
        data = request.get_json()
        current_password = data.get('current_password', '').strip()
        
        if not current_password:
            return jsonify({'success': False, 'message': 'Vui lòng nhập mật khẩu hiện tại'}), 400
        
        if not renter.check_password(current_password):
            return jsonify({'success': False, 'message': 'Mật khẩu hiện tại không đúng'}), 400
        
        # Validate new password
        new_password = data.get('new_password', '').strip()
        confirm_password = data.get('confirm_password', '').strip()
        
        if not all([new_password, confirm_password]):
            return jsonify({'success': False, 'message': 'Vui lòng điền đầy đủ thông tin mật khẩu mới'}), 400
        
        if new_password != confirm_password:
            return jsonify({'success': False, 'message': 'Mật khẩu xác nhận không khớp'}), 400
        
        if new_password == current_password:
            return jsonify({'success': False, 'message': 'Mật khẩu mới không được trùng với mật khẩu cũ'}), 400
        
        # Validate password strength
        password_evaluation = PasswordValidator.evaluate_password(new_password)
        if not password_evaluation['is_acceptable']:
            return jsonify({'success': False, 'message': 'Mật khẩu quá yếu. Vui lòng chọn mật khẩu mạnh hơn.'}), 400
        
        # Tạo mã OTP
        otp = ''.join(random.choices(string.digits, k=6))
        
        # Gửi email với token bảo mật
        success, message, secure_token = email_service.send_password_change_otp_email(
            renter.email, 
            otp, 
            renter.full_name or renter.username,
            renter.id
        )
        
        if success:
            # Lưu OTP và token vào session với thời gian hết hạn 2 phút
            session['password_change_otp'] = otp
            session['password_change_token'] = secure_token
            session['password_change_expires'] = (datetime.now() + timedelta(minutes=2)).isoformat()
            session['password_change_attempts'] = 0
            
            # Cập nhật số lần gửi
            if 'password_change_send_count' not in session:
                session['password_change_send_count'] = {}
            session['password_change_send_count'][today] = send_count + 1
            
            logger.info(f"Password change OTP sent successfully to renter {renter.email}")
            return jsonify({
                'success': True, 
                'message': f'Mã OTP đã được gửi đến email của bạn (có hiệu lực 2 phút)',
                'email': renter.email,
                'expires_in': 2,
                'token': secure_token
            })
        else:
            logger.error(f"Failed to send password change OTP to renter {renter.email}: {message}")
            return jsonify({'success': False, 'message': f'Không thể gửi email: {message}'}), 500
            
    except Exception as e:
        logger.error(f"Error in send_password_change_otp: {e}")
        return jsonify({'success': False, 'message': f'Lỗi hệ thống: {str(e)}'}), 500

@renter_bp.route('/change-password/verify-otp', methods=['POST'])
@password_change_api_required
def verify_password_change_otp():
    """Xác thực mã OTP và đổi mật khẩu cho Renter"""
    try:
        renter = current_user
        data = request.get_json()
        otp_input = data.get('otp', '').strip()
        new_password = data.get('new_password', '').strip()
        confirm_password = data.get('confirm_password', '').strip()
        
        if not all([otp_input, new_password, confirm_password]):
            return jsonify({'success': False, 'message': 'Vui lòng điền đầy đủ thông tin'}), 400
        
        # Kiểm tra mật khẩu mới khớp nhau
        if new_password != confirm_password:
            return jsonify({'success': False, 'message': 'Mật khẩu xác nhận không khớp'}), 400
        
        # Validate password strength
        password_evaluation = PasswordValidator.evaluate_password(new_password)
        if not password_evaluation['is_acceptable']:
            return jsonify({'success': False, 'message': 'Mật khẩu quá yếu. Vui lòng chọn mật khẩu mạnh hơn.'}), 400
        
        # Kiểm tra OTP
        stored_otp = session.get('password_change_otp')
        stored_token = session.get('password_change_token')
        expires_str = session.get('password_change_expires')
        
        if not stored_otp or not stored_token or not expires_str:
            return jsonify({'success': False, 'message': 'Mã OTP không hợp lệ hoặc đã hết hạn'}), 400
        
        expires = datetime.fromisoformat(expires_str)
        if datetime.now() > expires:
            session.pop('password_change_otp', None)
            session.pop('password_change_token', None)
            session.pop('password_change_expires', None)
            session.pop('password_change_attempts', None)
            return jsonify({'success': False, 'message': 'Mã OTP đã hết hạn'}), 400
        
        attempts = session.get('password_change_attempts', 0)
        if attempts >= 3:  # Giới hạn 3 lần thử
            return jsonify({'success': False, 'message': 'Bạn đã thử quá 3 lần. Vui lòng yêu cầu mã mới'}), 400
        
        # Tăng số lần thử
        session['password_change_attempts'] = attempts + 1
        
        # Xác thực token bảo mật
        verified_otp, timestamp = email_service.verify_secure_token(stored_token, renter.id)
        if not verified_otp or verified_otp != stored_otp:
            return jsonify({'success': False, 'message': 'Token xác thực không hợp lệ'}), 400
        
        # Kiểm tra OTP
        if otp_input != stored_otp:
            return jsonify({'success': False, 'message': 'Mã OTP không đúng'}), 400
        
        # OTP đúng - đổi mật khẩu
        renter.set_password(new_password)
        db.session.commit()
        
        # Xóa OTP khỏi session
        session.pop('password_change_otp', None)
        session.pop('password_change_token', None)
        session.pop('password_change_expires', None)
        session.pop('password_change_attempts', None)
        
        # Gửi email thông báo đổi mật khẩu thành công
        email_service.send_password_change_success_email(
            renter.email,
            renter.full_name or renter.username
        )
        
        logger.info(f"Password changed successfully for renter {renter.email}")
        return jsonify({
            'success': True, 
            'message': 'Đổi mật khẩu thành công!'
        })
        
    except Exception as e:
        logger.error(f"Error in verify_password_change_otp: {e}")
        return jsonify({'success': False, 'message': f'Lỗi hệ thống: {str(e)}'}), 500

@renter_bp.route('/change-password/check-status', methods=['GET'])
@password_change_api_required
def check_password_change_status():
    """Kiểm tra trạng thái đổi mật khẩu cho Renter"""
    try:
        renter = current_user
        expires_str = session.get('password_change_expires')
        remaining_time = 0
        
        if expires_str:
            expires = datetime.fromisoformat(expires_str)
            if datetime.now() < expires:
                remaining_time = int((expires - datetime.now()).total_seconds() / 60)
        
        today = datetime.now().date().isoformat()
        send_count = session.get('password_change_send_count', {}).get(today, 0)
        blocked_until = session.get('password_change_send_blocked_until')
        blocked_until_str = None
        
        if blocked_until:
            try:
                dt = datetime.fromisoformat(blocked_until)
                blocked_until_str = dt.strftime('%H:%M:%S')
            except:
                blocked_until_str = blocked_until
        
        return jsonify({
            'success': True,
            'email_verified': renter.email_verified,
            'email': renter.email,
            'remaining_time': remaining_time,
            'max_attempts': 3,
            'send_count': send_count,
            'blocked_until': blocked_until_str
        })
        
    except Exception as e:
        logger.error(f"Error in check_password_change_status: {e}")
        return jsonify({'success': False, 'message': f'Lỗi hệ thống: {str(e)}'}), 500

@renter_bp.route('/change-password/cancel', methods=['POST'])
@password_change_api_required
def cancel_password_change():
    """Hủy quá trình đổi mật khẩu cho Renter"""
    try:
        # Xóa tất cả dữ liệu OTP khỏi session
        session.pop('password_change_otp', None)
        session.pop('password_change_token', None)
        session.pop('password_change_expires', None)
        session.pop('password_change_attempts', None)
        
        logger.info(f"Password change process cancelled for renter {current_user.email}")
        return jsonify({
            'success': True,
            'message': 'Đã hủy quá trình đổi mật khẩu'
        })
        
    except Exception as e:
        logger.error(f"Error in cancel_password_change: {e}")
        return jsonify({'success': False, 'message': f'Lỗi hệ thống: {str(e)}'}), 500

@renter_bp.route('/room/<int:room_id>/detail')
def view_room_detail(room_id):
    """View room detail page"""
    room = Home.query.get_or_404(room_id)
    
    # Check if room is active
    if not room.is_active:
        flash("Phòng này hiện tại đã ngừng hoạt động và không khả dụng để đặt.", "warning")
        return redirect(url_for('home'))
    
    # Load reviews for this room
    reviews = Review.query.filter_by(home_id=room_id).order_by(Review.created_at.desc()).all()
    
    # For rooms, we want to default to hourly booking
    search_params = request.args.copy()
    if 'booking_type' not in search_params:
        search_params['booking_type'] = 'hourly'
    
    return render_template('renter/view_home_detail.html', 
                          home=room,
                          reviews=reviews,
                          search_params=search_params)

@renter_bp.route('/book-homestay/<int:homestay_id>/<int:room_id>')
@require_email_verification_for_booking
def book_homestay(homestay_id, room_id):
    """Book a specific room in a homestay"""
    room = Home.query.get_or_404(room_id)
    
    # Check if room is active
    if not room.is_active:
        flash("Phòng này hiện tại đã ngừng hoạt động và không khả dụng để đặt.", "warning")
        return redirect(url_for('renter.view_room_detail', room_id=room.id))
    
    # Get query parameters for pre-filling form
    booking_type = request.args.get('type', 'hourly')  # Default to hourly for rooms
    checkin_date = request.args.get('checkin')
    checkout_date = request.args.get('checkout')
    hourly_date = request.args.get('date')
    start_time = request.args.get('time')
    duration = request.args.get('duration')
    guests = request.args.get('guests', '1 khách')
    
    print(f"DEBUG: Received query params for homestay booking - type: {booking_type}, checkin: {checkin_date}, checkout: {checkout_date}, date: {hourly_date}, time: {start_time}, duration: {duration}, guests: {guests}")
    
    # Build redirect URL to book_home with all parameters
    redirect_url = url_for('renter.book_home', home_id=room.id)
    params = []
    
    if booking_type:
        params.append(f'type={booking_type}')
    if checkin_date:
        params.append(f'checkin={checkin_date}')
    if checkout_date:
        params.append(f'checkout={checkout_date}')
    if hourly_date:
        params.append(f'date={hourly_date}')
    if start_time:
        params.append(f'time={start_time}')
    if duration:
        params.append(f'duration={duration}')
    if guests:
        params.append(f'guests={guests}')
    
    if params:
        redirect_url += '?' + '&'.join(params)
    
    print(f"DEBUG: Redirecting to: {redirect_url}")
    return redirect(redirect_url)
