from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user, logout_user
from models import Homestay, Booking, Review, db, Room, RoomImage, Admin, Owner, Renter
from datetime import datetime, timedelta
from PIL import Image
import io
import os
from werkzeug.utils import secure_filename
from utils.s3_utils import S3Handler

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
        if current_user.__class__.__name__ == 'Owner' and current_user.is_renter() and request.endpoint in ['renter.book_homestay', 'renter.cancel_booking']:
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


@renter_bp.route('/search')
def search():
    """Search for homestays with filters"""
    # Get search parameters
    city = request.args.get('city', '')
    district = request.args.get('district', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    bedrooms = request.args.get('bedrooms', type=int)
    
    # Build query
    query = Homestay.query.filter_by(is_active=True)
    
    if city:
        query = query.filter(Homestay.city.ilike(f'%{city}%'))
    if district:
        query = query.filter(Homestay.district.ilike(f'%{district}%'))
    if min_price is not None:
        query = query.filter(Homestay.price_per_hour >= min_price)
    if max_price is not None:
        query = query.filter(Homestay.price_per_hour <= max_price)
    if bedrooms is not None:
        query = query.filter(Homestay.bedrooms >= bedrooms)
    
    # Execute query
    homestays = query.all()
    
    # Get unique cities and districts for filter dropdowns
    cities = db.session.query(Homestay.city).distinct().all()
    districts = db.session.query(Homestay.district).distinct().all()
    
    return render_template('renter/search.html', 
                          homestays=homestays,
                          cities=[city[0] for city in cities],
                          districts=[district[0] for district in districts],
                          search_params=request.args)

@renter_bp.route('/view-homestay/<int:id>')
def view_homestay(id):
    homestay = Homestay.query.get_or_404(id)
    
    # Kiểm tra nếu homestay đã bị khóa
    if not homestay.is_active:
        flash("Homestay này hiện tại đã ngừng hoạt động và không khả dụng để đặt phòng.", "warning")
        return redirect(url_for('home'))
    
    rooms = Room.query.filter_by(homestay_id=id).all()
    
    # Load images for each room
    for room in rooms:
        room.images = RoomImage.query.filter_by(room_id=room.id).all()
    
    reviews = Review.query.filter_by(homestay_id=id).order_by(Review.created_at.desc()).all()
    
    return render_template('renter/view_homestay.html', 
                          homestay=homestay, 
                          rooms=rooms, 
                          reviews=reviews)


@renter_bp.route('/book/<int:homestay_id>', methods=['GET', 'POST'])
@renter_required
def book_homestay(homestay_id):
    homestay = Homestay.query.get_or_404(homestay_id)
    # Get room_id from query string (or form data)
    room_id = request.args.get('room_id') or request.form.get('room_id')
    if not room_id:
        flash("Please select a room.", "warning")
        return redirect(url_for('renter.view_homestay', id=homestay.id))
    room = Room.query.get_or_404(room_id)
    
    if request.method == 'POST':
        duration_str = request.form.get('duration')
        if not duration_str:
            flash("Duration is required", "warning")
            return redirect(url_for('renter.book_homestay', homestay_id=homestay.id, room_id=room_id))
        
        try:
            duration = int(duration_str)
        except ValueError:
            flash("Invalid duration value.", "danger")
            return redirect(url_for('renter.book_homestay', homestay_id=homestay.id, room_id=room_id))
        
        if duration < 1:
            flash("Minimum duration is 1 minute.", "warning")
            return redirect(url_for('renter.book_homestay', homestay_id=homestay.id, room_id=room_id))
        
        start_date = request.form.get('start_date')
        start_time = request.form.get('start_time')
        if not start_date or not start_time:
            flash("You must select both date and time.", "warning")
            return redirect(url_for('renter.book_homestay', homestay_id=homestay.id, room_id=room_id))
        
        start_str = f"{start_date} {start_time}"
        try:
            start_datetime = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
        except ValueError:
            flash("Invalid date or time format.", "danger")
            return redirect(url_for('renter.book_homestay', homestay_id=homestay.id, room_id=room_id))
        
        end_datetime = start_datetime + timedelta(minutes=duration)
        # Calculate total price using the room's price; convert minutes to hours.
        total_price = room.price_per_hour * (duration / 60)
        
        # Check for overlapping bookings for this room
        existing_bookings = Booking.query.filter_by(room_id=room.id).all()
        for booking in existing_bookings:
            if start_datetime < booking.end_time and end_datetime > booking.start_time:
                flash('This room is not available during the selected time period.', 'danger')
                return redirect(url_for('renter.book_homestay', homestay_id=homestay.id, room_id=room_id))
        
        new_booking = Booking(
            homestay_id=homestay.id,
            room_id=room.id,
            renter_id=current_user.id,
            start_time=start_datetime,
            end_time=end_datetime,
            total_price=total_price,
            status='pending'
        )
        db.session.add(new_booking)
        db.session.commit()
        current_user.experience_points += total_price * 10  # Update user XP based on total price
        
        db.session.add(new_booking)
        db.session.commit()

        flash('Booking request submitted successfully!', 'success')
        return redirect(url_for('renter.dashboard'))

    return render_template('renter/book_homestay.html', homestay=homestay, room=room)
  




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

def handle_file_upload(file, folder=""):
    """Handle file upload using either S3 or local storage"""
    if not file or not file.filename:
        return None
        
    if not allowed_file(file.filename):
        raise ValueError("File type not allowed")
        
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = f"{timestamp}_{filename}"
    
    if current_app.config.get('USE_S3'):
        s3 = S3Handler(
            aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
            region_name=current_app.config['AWS_REGION'],
            bucket_name=current_app.config['S3_BUCKET']
        )
        return s3.upload_file(file, folder)
    else:
        # Fallback to local storage
        upload_path = os.path.join('static', 'uploads', folder) if folder else os.path.join('static', 'uploads')
        os.makedirs(upload_path, exist_ok=True)
        filepath = os.path.join(upload_path, filename)
        file.save(filepath)
        return os.path.join('uploads', folder, filename) if folder else os.path.join('uploads', filename)

def delete_file(file_path):
    """Delete file from either S3 or local storage"""
    if current_app.config['USE_S3']:
        s3 = S3Handler(
            aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
            region_name=current_app.config['AWS_REGION'],
            bucket_name=current_app.config['S3_BUCKET']
        )
        return s3.delete_file(file_path)
    else:
        # Delete from local storage
        if file_path:
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(file_path))
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
    return False

@renter_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        try:
            # Get form data
            new_full_name = request.form.get('full_name')
            new_phone = request.form.get('phone')
            new_email = request.form.get('email')
            new_personal_id = request.form.get('personal_id')
            
            # Validate required fields
            if not new_email or not new_personal_id:
                flash("Email và CCCD/CMND là bắt buộc!", "danger")
                return redirect(url_for('renter.profile'))
            
            # Check if email is being changed and if it already exists
            if new_email != current_user.email:
                existing_admin = Admin.query.filter_by(email=new_email).first()
                existing_owner = Owner.query.filter_by(email=new_email).first()
                existing_renter = Renter.query.filter_by(email=new_email).filter(Renter.id != current_user.id).first()
                
                if existing_admin or existing_owner or existing_renter:
                    flash(f"Email '{new_email}' đã tồn tại! Vui lòng chọn email khác.", "danger")
                    return redirect(url_for('renter.profile'))
            
            # Check if phone is being changed and if it already exists
            if new_phone and new_phone != current_user.phone:
                existing_owner = Owner.query.filter_by(phone=new_phone).first()
                existing_renter = Renter.query.filter_by(phone=new_phone).filter(Renter.id != current_user.id).first()
                
                if existing_owner or existing_renter:
                    flash(f"Số điện thoại '{new_phone}' đã tồn tại! Vui lòng chọn số khác.", "danger")
                    return redirect(url_for('renter.profile'))
            
            # Check if personal_id is being changed and if it already exists
            if new_personal_id != current_user.personal_id:
                existing_owner = Owner.query.filter_by(personal_id=new_personal_id).first()
                existing_renter = Renter.query.filter_by(personal_id=new_personal_id).filter(Renter.id != current_user.id).first()
                
                if existing_owner or existing_renter:
                    flash(f"CCCD/CMND '{new_personal_id}' đã tồn tại! Vui lòng chọn số khác.", "danger")
                    return redirect(url_for('renter.profile'))
            
            # Update user info
            current_user.full_name = new_full_name
            current_user.phone = new_phone
            current_user.email = new_email
            current_user.personal_id = new_personal_id

            # Handle avatar upload
            if 'avatar' in request.files:
                avatar = request.files['avatar']
                if avatar and avatar.filename != '':
                    if not allowed_file(avatar.filename):
                        flash("File type not allowed. Please use: png, jpg, jpeg, or gif", "danger")
                        return redirect(url_for('renter.profile'))
                    
                    try:
                        # Delete old avatar if exists
                        if current_user.avatar:
                            delete_file(current_user.avatar)
                        
                        # Upload new avatar
                        file_path = handle_file_upload(avatar, 'avatars')
                        if file_path:
                            current_user.avatar = file_path
                            flash("Avatar updated successfully!", "success")
                        else:
                            flash("Error uploading avatar", "danger")
                            return redirect(url_for('renter.profile'))
                            
                    except Exception as e:
                        print(f"Error during file operations: {str(e)}")
                        flash(f"Error saving avatar: {str(e)}", "danger")
                        return redirect(url_for('renter.profile'))

            # Handle CCCD upload
            if 'cccd_front' in request.files:
                cccd_front = request.files['cccd_front']
                if cccd_front and cccd_front.filename != '':
                    if not allowed_file(cccd_front.filename):
                        flash("File type not allowed. Please use: png, jpg, jpeg, or gif", "danger")
                        return redirect(url_for('renter.profile'))
                    
                    try:
                        # Delete old CCCD front if exists
                        if current_user.cccd_front_image:
                            delete_file(current_user.cccd_front_image)
                        
                        # Upload new CCCD front
                        file_path = handle_file_upload(cccd_front, 'cccd')
                        if file_path:
                            current_user.cccd_front_image = file_path
                            flash("CCCD front updated successfully!", "success")
                        else:
                            flash("Error uploading CCCD front", "danger")
                            return redirect(url_for('renter.profile'))
                            
                    except Exception as e:
                        print(f"Error during CCCD front file operations: {str(e)}")
                        flash(f"Error saving CCCD front: {str(e)}", "danger")
                        return redirect(url_for('renter.profile'))

            if 'cccd_back' in request.files:
                cccd_back = request.files['cccd_back']
                if cccd_back and cccd_back.filename != '':
                    if not allowed_file(cccd_back.filename):
                        flash("File type not allowed. Please use: png, jpg, jpeg, or gif", "danger")
                        return redirect(url_for('renter.profile'))
                    
                    try:
                        # Delete old CCCD back if exists
                        if current_user.cccd_back_image:
                            delete_file(current_user.cccd_back_image)
                        
                        # Upload new CCCD back
                        file_path = handle_file_upload(cccd_back, 'cccd')
                        if file_path:
                            current_user.cccd_back_image = file_path
                            flash("CCCD back updated successfully!", "success")
                        else:
                            flash("Error uploading CCCD back", "danger")
                            return redirect(url_for('renter.profile'))
                            
                    except Exception as e:
                        print(f"Error during CCCD back file operations: {str(e)}")
                        flash(f"Error saving CCCD back: {str(e)}", "danger")
                        return redirect(url_for('renter.profile'))

            # Commit changes to the database
            db.session.commit()
            flash("Profile updated successfully!", "success")
            
        except Exception as e:
            print(f"Error updating profile: {str(e)}")
            db.session.rollback()
            flash(f"Error updating profile: {str(e)}", "danger")
            
        return redirect(url_for('renter.profile'))

    return render_template("user/profile.html")

@renter_bp.route('/homestay/<int:homestay_id>/review', methods=['GET', 'POST'])
@login_required
def add_review(homestay_id):
    homestay = Homestay.query.get_or_404(homestay_id)

    # Check if the user has already left a review for this homestay
    existing_review = Review.query.filter_by(homestay_id=homestay.id, renter_id=current_user.id).first()
    if existing_review:
        flash('You have already left a review for this homestay.', 'danger')
        return redirect(url_for('renter.view_homestay', id=homestay.id))

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
        return redirect(url_for('renter.view_homestay', id=homestay.id))

    return render_template('renter/add_review.html', homestay=homestay)

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

@renter_bp.route('/switch-to-renter')
@login_required
def switch_to_renter():
    if current_user.role != 'owner':
        flash('Bạn không phải là chủ nhà để thực hiện chuyển đổi này', 'danger')
        return redirect(url_for('home'))
    
    current_user.temp_role = 'renter'
    db.session.commit()
    flash('Bạn đang ở chế độ xem', 'success')
    return redirect(url_for('home'))

@renter_bp.route('/booking-history')
@login_required
def booking_history():
    bookings = Booking.query.filter_by(renter_id=current_user.id).order_by(Booking.created_at.desc()).all()
    return render_template('renter/booking_history.html', bookings=bookings)

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