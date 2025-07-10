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

renter_bp = Blueprint('renter', __name__, url_prefix='/renter')

# Custom decorator to ensure user is a renter
def renter_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_renter():
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

@renter_bp.route('/dashboard')
@renter_required
def dashboard():
    bookings = Booking.query.filter_by(renter_id=current_user.id).all()
    now = datetime.utcnow()
    updated = False

    for booking in bookings:
        # Only update confirmed bookings that have been paid
        if booking.status == 'confirmed' and booking.payment_status == 'paid' and booking.start_time <= now:
            booking.status = 'active'
            updated = True
        elif booking.status == 'active' and booking.end_time <= now:
            booking.status = 'completed'
            updated = True

    if updated:
        db.session.commit()
    
    return render_template('renter/dashboard.html', bookings=bookings)

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

@renter_bp.route('/view-home/<int:id>')
def view_home(id):
    # Load home với amenities và category relationships
    home = Home.query.options(
        joinedload(Home.amenities).joinedload(Amenity.amenity_category),
        joinedload(Home.images)
    ).get_or_404(id)
    
    # Kiểm tra nếu nhà đã bị khóa
    if not home.is_active:
        flash("Nhà này hiện tại đã ngừng hoạt động và không khả dụng để đặt.", "warning")
        return redirect(url_for('home'))
    
    # Load reviews for this home
    reviews = Review.query.filter_by(home_id=id).order_by(Review.created_at.desc()).all()
    
    return render_template('renter/view_home_detail.html', 
                          home=home,
                          reviews=reviews)

@renter_bp.route('/book/<int:home_id>', methods=['GET', 'POST'])
@renter_required
def book_home(home_id):
    home = Home.query.get_or_404(home_id)
    
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        duration_str = request.form.get('duration')
        guests_str = request.form.get('guests')
        
        if not start_date or not duration_str:
            flash("You must select date and duration.", "warning")
            return redirect(url_for('renter.book_home', home_id=home.id))
        
        try:
            duration = int(duration_str)
            guests = int(guests_str) if guests_str else 1
        except ValueError:
            flash("Invalid duration or guest count.", "danger")
            return redirect(url_for('renter.book_home', home_id=home.id))
        
        if duration < 1:
            flash("Minimum duration is 1 night.", "warning")
            return redirect(url_for('renter.book_home', home_id=home.id))
        
        if guests > home.max_guests:
            flash(f"Maximum guests allowed: {home.max_guests}", "warning")
            return redirect(url_for('renter.book_home', home_id=home.id))
        
        # Check if home has price_per_night
        if not home.price_per_night:
            flash("This home does not have daily pricing available.", "danger")
            return redirect(url_for('renter.book_home', home_id=home.id))
        
        # For home bookings, check-in is typically at 3 PM
        start_str = f"{start_date} 15:00"
        try:
            start_datetime = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
        except ValueError:
            flash("Invalid date format.", "danger")
            return redirect(url_for('renter.book_home', home_id=home.id))
        
        end_datetime = start_datetime + timedelta(days=duration)
        # Calculate total price using the home's price per night
        total_price = home.price_per_night * duration
        # Calculate total hours (24 hours per day for daily bookings)
        total_hours = duration * 24
        
        # Check for overlapping bookings for this home (chỉ check với booking chưa bị hủy)
        existing_bookings = Booking.query.filter(
            Booking.home_id == home.id,
            Booking.status.in_(['pending', 'confirmed', 'active'])
        ).all()
        for booking in existing_bookings:
            if start_datetime < booking.end_time and end_datetime > booking.start_time:
                flash('This home is not available during the selected time period.', 'danger')
                return redirect(url_for('renter.book_home', home_id=home.id))
        
        new_booking = Booking(
            home_id=home.id,
            renter_id=current_user.id,
            start_time=start_datetime,
            end_time=end_datetime,
            total_hours=total_hours,
            total_price=total_price,
            status='confirmed',
            payment_status='pending',
            booking_type='daily'  # Set booking type to daily for home bookings
        )
        
        db.session.add(new_booking)
        # current_user.experience_points += total_price * 10  # Update user XP based on total price
        db.session.commit()

        # Redirect directly to payment instead of dashboard
        flash('Booking created successfully! Please proceed with payment.', 'success')
        return redirect(url_for('payment.checkout', booking_id=new_booking.id))

    return render_template('renter/book_home.html', home=home)
  




@renter_bp.route('/cancel-booking/<int:id>')
@renter_required
def cancel_booking(id):
    """Cancel a booking"""
    booking = Booking.query.get_or_404(id)
    
    # Ensure the current user owns this booking
    if booking.renter_id != current_user.id:
        flash('You do not have permission to cancel this booking', 'danger')
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
    now = datetime.utcnow()
    updated = False

    for booking in bookings:
        # Only update confirmed bookings that have been paid
        if booking.status == 'confirmed' and booking.payment_status == 'paid' and booking.start_time <= now:
            booking.status = 'active'
            updated = True
        elif booking.status == 'active' and booking.end_time <= now:
            booking.status = 'completed'
            updated = True

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

@renter_bp.route('/home/<int:home_id>/detail')
def view_home_detail(home_id):
    home = Home.query.get_or_404(home_id)
    # This page shows all images for the home
    return render_template('renter/view_home_detail.html', home=home)

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
