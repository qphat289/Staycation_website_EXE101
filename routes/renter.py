from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user, logout_user
from models import Booking, Review, db, Room, RoomImage, Admin, Owner, Renter
from datetime import datetime, timedelta
from PIL import Image
import io
import os
from werkzeug.utils import secure_filename

renter_bp = Blueprint('renter', __name__, url_prefix='/renter')

# Custom decorator to ensure user is a renter
def renter_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_renter():
            flash('You must be a renter to access this page', 'danger')
            return redirect(url_for('home'))
        
        # Kiểm tra nếu là owner đang dùng chế độ xem renter
        # Chỉ ngăn chặn các chức năng booking/đặt phòng
        if current_user.__class__.__name__ == 'Owner' and current_user.is_renter() and request.endpoint in ['renter.book_room', 'renter.cancel_booking']:
            flash('Bạn đang ở chế độ xem, không thể thực hiện đặt phòng', 'warning')
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
        if booking.status == 'pending' and booking.start_time <= now:
            booking.status = 'active'
            updated = True
        elif booking.status == 'confirmed' and booking.start_time <= now:
            booking.status = 'active'
            updated = True
        elif booking.status in ['active', 'confirmed'] and booking.end_time <= now:
            booking.status = 'completed'
            updated = True

    if updated:
        db.session.commit()
    
    return render_template('renter/dashboard.html', bookings=bookings)

# City and district mapping
CITY_MAPPING = {
    'TP. Hồ Chí Minh': 'hcm',
    'Hà Nội': 'hanoi'
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

@renter_bp.route('/search')
def search():
    """Search for rooms with filters"""
    # Get search parameters
    location = request.args.get('location', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    room_type = request.args.get('room_type', '')
    booking_type = request.args.get('booking_type', 'hourly')  # Default to hourly if not specified
    
    # Get time parameters
    checkin_date = request.args.get('checkin_date')
    checkin_time = request.args.get('checkin_time')
    checkout_time = request.args.get('checkout_time')
    
    # Get guest parameters
    adults = request.args.get('adults', type=int, default=1)
    children = request.args.get('children', type=int, default=0)
    rooms_count = request.args.get('rooms', type=int, default=1)
    total_guests = adults + children if adults is not None and children is not None else None
    
    # Log search parameters
    print("🔍 Search Parameters:")
    print(f"Location: {location}")
    print(f"Booking Type: {booking_type}")
    print(f"Check-in Date: {checkin_date}")
    print(f"Check-in Time: {checkin_time}")
    print(f"Check-out Time: {checkout_time}")
    print(f"Adults: {adults}")
    print(f"Children: {children}")
    print(f"Rooms: {rooms_count}")
    print(f"Total Guests: {total_guests}")
    
    # Build query
    query = Room.query.filter_by(is_active=True)
    
    # Filter by location (city, district or room title)
    if location:
        # Map location to database values if it matches a city or district
        location_db = location
        if location in CITY_MAPPING:
            location_db = CITY_MAPPING[location]
        elif location in DISTRICT_MAPPING:
            location_db = DISTRICT_MAPPING[location]
            
        # Try to match location against city, district, or title
        query = query.filter(
            db.or_(
                Room.city.ilike(f'%{location_db}%'),
                Room.district.ilike(f'%{location_db}%'),
                Room.title.ilike(f'%{location}%')  # Keep original for title search
            )
        )
        print(f"🔍 Location filter: {location} -> {location_db}")
        
    # Apply price filters based on booking type
    if booking_type == 'hourly':
        if min_price is not None:
            query = query.filter(Room.price_per_hour >= min_price)
            print(f"🔍 Min hourly price filter: {min_price}")
        if max_price is not None:
            query = query.filter(Room.price_per_hour <= max_price)
            print(f"🔍 Max hourly price filter: {max_price}")
        # Ensure room has hourly price and it's not zero
        query = query.filter(Room.price_per_hour.isnot(None))
        query = query.filter(Room.price_per_hour > 0)
    else:  # daily/nightly
        if min_price is not None:
            query = query.filter(Room.price_per_night >= min_price)
            print(f"🔍 Min nightly price filter: {min_price}")
        if max_price is not None:
            query = query.filter(Room.price_per_night <= max_price)
            print(f"🔍 Max nightly price filter: {max_price}")
        # Ensure room has nightly price and it's not zero
        query = query.filter(Room.price_per_night.isnot(None))
        query = query.filter(Room.price_per_night > 0)
    
    if room_type:
        query = query.filter(Room.room_type == room_type)
        print(f"🔍 Room type filter: {room_type}")
    
    # Filter by max guests if specified
    if total_guests is not None:
        query = query.filter(Room.max_guests >= total_guests)
        print(f"🔍 Max guests filter: {total_guests}")
    
    # Execute query and get all matching rooms
    rooms = query.all()
    print(f"🔍 Found {len(rooms)} matching rooms")
    
    # Print details of each room for debugging
    for room in rooms:
        print(f"\nRoom Details:")
        print(f"Title: {room.title}")
        print(f"City: {room.city}")
        print(f"District: {room.district}")
        print(f"Max Guests: {room.max_guests}")
        print(f"Price per Hour: {room.price_per_hour}")
        print(f"Price per Night: {room.price_per_night}")
        print(f"Is Active: {room.is_active}")
    
    # Get unique cities and districts for filter dropdowns
    cities = db.session.query(Room.city).distinct().all()
    districts = db.session.query(Room.district).distinct().all()
    room_types = db.session.query(Room.room_type).distinct().all()
    
    # Map database values to display names
    city_display_names = {v: k for k, v in CITY_MAPPING.items()}
    district_display_names = {v: k for k, v in DISTRICT_MAPPING.items()}
    
    cities = [city_display_names.get(city[0], city[0].upper()) for city in cities]
    districts = [district_display_names.get(district[0], district[0].upper()) for district in districts]
    
    return render_template('renter/search.html', 
                          rooms=rooms,
                          cities=cities,
                          districts=districts,
                          room_types=[rt[0] for rt in room_types if rt[0]],
                          search_params=request.args)

@renter_bp.route('/view-room/<int:id>')
def view_room(id):
    room = Room.query.get_or_404(id)
    
    # Kiểm tra nếu phòng đã bị khóa
    if not room.is_active:
        flash("Phòng này hiện tại đã ngừng hoạt động và không khả dụng để đặt.", "warning")
        return redirect(url_for('home'))
    
    # Load room images
    room_images = RoomImage.query.filter_by(room_id=room.id).all()
    
    # Load reviews for this room
    reviews = Review.query.filter_by(room_id=id).order_by(Review.created_at.desc()).all()
    
    return render_template('renter/view_room_detail.html', 
                          room=room,
                          room_images=room_images,
                          reviews=reviews)


@renter_bp.route('/book/<int:room_id>', methods=['GET', 'POST'])
@renter_required
def book_room(room_id):
    room = Room.query.get_or_404(room_id)
    
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        start_time = request.form.get('start_time')
        duration_str = request.form.get('duration')
        
        if not start_date or not start_time or not duration_str:
            flash("You must select date, time and duration.", "warning")
            return redirect(url_for('renter.book_room', room_id=room.id))
        
        try:
            duration = int(duration_str)
        except ValueError:
            flash("Invalid duration value.", "danger")
            return redirect(url_for('renter.book_room', room_id=room.id))
        
        if duration < 1:
            flash("Minimum duration is 1 night.", "warning")
            return redirect(url_for('renter.book_room', room_id=room.id))
        
        start_str = f"{start_date} {start_time}"
        try:
            start_datetime = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
        except ValueError:
            flash("Invalid date or time format.", "danger")
            return redirect(url_for('renter.book_room', room_id=room.id))
        
        end_datetime = start_datetime + timedelta(days=duration)
        # Calculate total price using the room's price per night
        total_price = room.price_per_night * duration
        
        # Check for overlapping bookings for this room
        existing_bookings = Booking.query.filter_by(room_id=room.id).all()
        for booking in existing_bookings:
            if start_datetime < booking.end_time and end_datetime > booking.start_time:
                flash('This room is not available during the selected time period.', 'danger')
                return redirect(url_for('renter.book_room', room_id=room.id))
        
        new_booking = Booking(
            room_id=room.id,
            renter_id=current_user.id,
            start_time=start_datetime,
            end_time=end_datetime,
            total_price=total_price,
            status='pending'
        )
        
        db.session.add(new_booking)
        current_user.experience_points += total_price * 10  # Update user XP based on total price
        db.session.commit()

        flash('Booking request submitted successfully!', 'success')
        return redirect(url_for('renter.dashboard'))

    return render_template('renter/book_room.html', room=room)
  




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

def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

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
            current_user.email = request.form.get('email')
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
            
            # Xử lý upload avatar
            avatar_file = request.files.get('avatar')
            if avatar_file and avatar_file.filename and allowed_file(avatar_file.filename):
                # Tạo tên file unique
                filename = secure_filename(avatar_file.filename)
                timestamp = str(int(datetime.now().timestamp()))
                filename = f"avatar_{current_user.id}_{timestamp}_{filename}"
                
                # Đảm bảo upload folder tồn tại
                upload_folder = current_app.config.get('UPLOAD_FOLDER')
                if not upload_folder:
                    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
                    current_app.config['UPLOAD_FOLDER'] = upload_folder
                
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                
                # Lưu file
                upload_path = os.path.join(upload_folder, filename)
                avatar_file.save(upload_path)
                
                # Resize image
                try:
                    with Image.open(upload_path) as img:
                        img = img.resize((200, 200), Image.Resampling.LANCZOS)
                        img.save(upload_path, optimize=True, quality=85)
                except Exception as e:
                    print(f"Error resizing image: {e}")
                
                # Xóa avatar cũ nếu có
                if current_user.avatar:
                    old_avatar_path = os.path.join(upload_folder, current_user.avatar)
                    if os.path.exists(old_avatar_path):
                        try:
                            os.remove(old_avatar_path)
                        except Exception as e:
                            print(f"Error removing old avatar: {e}")
                
                current_user.avatar = filename
            
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

@renter_bp.route('/homestay/<int:homestay_id>/review', methods=['GET', 'POST'])
@login_required
def add_review(homestay_id):
    homestay = Homestay.query.get_or_404(homestay_id)

    # Check if the user has already left a review for this homestay
    existing_review = Review.query.filter_by(homestay_id=homestay.id, renter_id=current_user.id).first()
    if existing_review:
        flash('You have already left a review for this homestay.', 'danger')
        return redirect(url_for('renter.view_room', id=homestay.id))

    if request.method == 'POST':
        rating = int(request.form.get('rating', 5))
        content = request.form.get('content', '')
        
        review = Review(
            rating=rating,
            content=content,
            homestay_id=homestay.id,
            renter_id=current_user.id  # CHỖ NÀY ĐÃ ĐỔI user_id -> renter_id
        )
        db.session.add(review)
        db.session.commit()
        flash('Review submitted!', 'success')
        return redirect(url_for('renter.view_room', id=homestay.id))

    return render_template('renter/add_review.html', homestay=homestay)

@renter_bp.route('/booking-history')
@renter_required
def booking_history():
    """View booking history for the current renter"""
    bookings = Booking.query.filter_by(renter_id=current_user.id).order_by(Booking.created_at.desc()).all()
    now = datetime.utcnow()
    updated = False

    for booking in bookings:
        if booking.status == 'pending' and booking.start_time <= now:
            booking.status = 'active'
            updated = True
        elif booking.status == 'confirmed' and booking.start_time <= now:
            booking.status = 'active'
            updated = True
        elif booking.status in ['active', 'confirmed'] and booking.end_time <= now:
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
        homestay_id=booking.homestay_id,
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
                homestay_id=booking.homestay_id,
                renter_id=current_user.id  # ĐÃ ĐỔI user_id -> renter_id
            )
            db.session.add(new_review)
            flash("Review submitted!", "success")

        db.session.commit()
        return redirect(url_for('renter.dashboard'))
    
    return render_template('renter/review_booking.html', booking=booking, existing_review=existing_review)

@renter_bp.route('/reviews/<int:homestay_id>', methods=['GET', 'POST'])
def view_reviews(homestay_id):
    """
    Displays reviews for homestay, optionally letting the user post a review if they have a completed booking.
    """
    homestay = Homestay.query.get_or_404(homestay_id)
    
    # Get existing reviews
    reviews = Review.query.filter_by(homestay_id=homestay.id).order_by(Review.created_at.desc()).all()
    
    # Determine if user can post (i.e., they have a completed booking)
    can_post = False
    if current_user.is_authenticated and current_user.is_renter():
        completed_booking = Booking.query.filter_by(
            homestay_id=homestay.id,
            renter_id=current_user.id,
            status='completed'
        ).first()
        if completed_booking:
            can_post = True

    # If user is trying to post a new or updated review
    if request.method == 'POST':
        if not can_post:
            flash("You can only post a review if you have a completed booking.", "danger")
            return redirect(url_for('renter.view_reviews', homestay_id=homestay.id))
        
        rating = int(request.form.get('rating', 5))
        content = request.form.get('content', '')
        
        existing_review = Review.query.filter_by(
            homestay_id=homestay.id,
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
                homestay_id=homestay.id,
                renter_id=current_user.id  # ĐÃ ĐỔI user_id -> renter_id
            )
            db.session.add(new_review)
            flash("Review submitted!", "success")
        db.session.commit()
        return redirect(url_for('renter.view_reviews', homestay_id=homestay.id))
    
    write_mode = request.args.get('write')
    
    if write_mode and not can_post:
        flash("You can only post a review if you have a completed booking.", "warning")
    
    return render_template(
        'renter/view_reviews.html',
        homestay=homestay,
        reviews=reviews,
        can_post=can_post,
        write_mode=write_mode
    )

@renter_bp.route('/room/<int:room_id>/detail')
def view_room_detail(room_id):
    room = Room.query.get_or_404(room_id)
    # This page shows all images for the room
    return render_template('renter/view_room_detail.html', room=room)

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

@renter_bp.route('/debug_rooms')
def debug_rooms():
    """Temporary route to debug room data"""
    rooms = Room.query.all()
    result = []
    for room in rooms:
        result.append({
            'title': room.title,
            'city': room.city,
            'district': room.district,
            'max_guests': room.max_guests,
            'price_per_hour': room.price_per_hour,
            'price_per_night': room.price_per_night,
            'is_active': room.is_active,
            'room_type': room.room_type
        })
    return jsonify(result)