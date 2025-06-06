# routes/owner.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Room, Booking, RoomImage, Renter, Admin, Owner
import os
from datetime import datetime, timedelta
from PIL import Image
import io
import os
from sqlalchemy.exc import IntegrityError


owner_bp = Blueprint('owner', __name__, url_prefix='/owner')

def allowed_file(filename):
    """Check if the file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Custom decorator to ensure user is an owner
def owner_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        print(f"owner_required: current_user type: {type(current_user)}")
        print(f"owner_required: current_user.is_owner(): {current_user.is_owner()}")
        print(f"owner_required: current_user role: {getattr(current_user, 'role', 'No role attribute')}")
        print(f"owner_required: session user_role: {session.get('user_role', 'Not set')}")
        
        if not current_user.is_owner():
            flash('You must be an owner to access this page', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


@owner_bp.route('/dashboard')
@login_required
def dashboard():
    # Lấy tất cả phòng của owner hiện tại
    rooms = Room.query.filter_by(owner_id=current_user.id).all()
    
    return render_template('owner/dashboard.html', rooms=rooms)


@owner_bp.route('/manage-rooms')
@owner_required
def manage_rooms():
    rooms = Room.query.filter_by(owner_id=current_user.id).all()
    return render_template('owner/manage_rooms.html', rooms=rooms)


@owner_bp.route('/add-room', methods=['GET', 'POST'])
@login_required
def add_room():
    if request.method == 'POST':
        try:
            # Lấy dữ liệu từ form wizard
            room_title = request.form.get('room_title')
            room_description = request.form.get('room_description')
            province = request.form.get('province')
            district = request.form.get('district')
            ward = request.form.get('ward')
            street = request.form.get('street')
            
            # Số lượng từ counter
            bathroom_count = int(request.form.get('bathroom_count', 2))
            bed_count = int(request.form.get('bed_count', 1))
            guest_count = int(request.form.get('guest_count', 1))
            
            # Lấy rental type được chọn
            selected_rental_type = request.form.get('selected_rental_type')
            
            # Xử lý giá dựa theo rental type được chọn
            price_per_hour = None
            price_per_night = None
            
            if selected_rental_type == 'hourly':
                hourly_price = request.form.get('hourly_price')
                price_per_hour = float(hourly_price) if hourly_price else 0.0
            elif selected_rental_type == 'nightly':
                nightly_price = request.form.get('nightly_price')
                price_per_night = float(nightly_price) if nightly_price else 0.0
            
            # Tạo room mới
            new_room = Room(
                title=room_title,
                room_type="Standard",  # Mặc định
                address=f"{street}, {ward}" if street and ward else "Chưa cập nhật",
                city=province if province else "Chưa cập nhật",
                district=district if district else "Chưa cập nhật",
                room_number=room_title,  # Sử dụng title làm room number
                bed_count=bed_count,
                bathroom_count=bathroom_count,
                max_guests=guest_count,
                price_per_hour=price_per_hour,
                price_per_night=price_per_night,
                description=room_description,
                floor_number=1,  # Mặc định
                owner_id=current_user.id
            )
            
            db.session.add(new_room)
            db.session.commit()
            
            flash('Đã thêm phòng thành công!', 'success')
            return redirect(url_for('owner.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra khi thêm phòng: {str(e)}', 'danger')
            
    return render_template('owner/add_room.html')

@owner_bp.route('/edit-room/<int:room_id>', methods=['GET', 'POST'])
@login_required
def edit_room(room_id):
    room = Room.query.get_or_404(room_id)
    if room.owner_id != current_user.id:
        flash('Bạn không có quyền chỉnh sửa phòng này!', 'danger')
        return redirect(url_for('owner.dashboard'))
    
    if request.method == 'POST':
        # Xử lý chỉnh sửa phòng
        pass
    return render_template('owner/edit_room.html', room=room)

@owner_bp.route('/delete-room/<int:room_id>', methods=['POST'])
@login_required
def delete_room(room_id):
    room = Room.query.get_or_404(room_id)
    if room.owner_id != current_user.id:
        flash('Bạn không có quyền xóa phòng này!', 'danger')
        return redirect(url_for('owner.dashboard'))
    
    db.session.delete(room)
    db.session.commit()
    
    flash('Đã xóa phòng thành công!', 'success')
    return redirect(url_for('owner.dashboard'))


@owner_bp.route('/view-bookings')
@owner_bp.route('/view-bookings/<status>')
@owner_required
def view_bookings(status=None):
    # Get all rooms owned by current user
    rooms = Room.query.filter_by(owner_id=current_user.id).all()
    
    # Get all bookings for these rooms
    all_bookings = []
    for room in rooms:
        all_bookings.extend(room.bookings)
    
    # Filter bookings by status if specified
    if status:
        all_bookings = [b for b in all_bookings if b.status == status]
    
    # Sort bookings by created_at date, newest first
    all_bookings.sort(key=lambda x: x.created_at, reverse=True)
    
    return render_template('owner/view_bookings.html', 
                          bookings=all_bookings, 
                          current_status=status)


@owner_bp.route('/room/<int:room_id>/add-images', methods=['GET', 'POST'])
@owner_required
def add_room_images(room_id):
    room = Room.query.get_or_404(room_id)
    
    # Kiểm tra quyền sở hữu
    if room.owner_id != current_user.id:
        flash('Bạn không có quyền thêm ảnh cho phòng này.', 'danger')
        return redirect(url_for('owner.dashboard'))
    
    if request.method == 'POST':
        images = request.files.getlist('images')
        for img_file in images:
            if img_file and img_file.filename:
                # Process image to improve quality and standardize size
                try:
                    # Open the image
                    img = Image.open(img_file)
                    
                    # Convert to RGB if needed (for PNG with transparency)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Resize to a standard size while maintaining aspect ratio
                    max_size = (800, 600)
                    img.thumbnail(max_size, Image.LANCZOS)
                    
                    # Create a filename
                    filename = secure_filename(img_file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    
                    # Save path
                    upload_folder = os.path.join('static', 'uploads')
                    os.makedirs(upload_folder, exist_ok=True)
                    save_path = os.path.join(upload_folder, filename)
                    
                    # Save the processed image
                    img.save(save_path, quality=85, optimize=True)
                    
                    # Create database record
                    is_featured = not RoomImage.query.filter_by(room_id=room.id, is_featured=True).first()
                    
                    new_img = RoomImage(
                        image_path=f"uploads/{filename}",
                        room_id=room.id,
                        is_featured=is_featured
                    )
                    db.session.add(new_img)
                    
                except Exception as e:
                    # Log the error but continue processing other images
                    print(f"Error processing image: {e}")
                    continue
                    
        db.session.commit()
        flash("Ảnh đã được thêm thành công vào thư viện phòng!", "success")
        return redirect(url_for('owner.add_room_images', room_id=room.id))
    
    # Get existing images for this room
    existing_images = RoomImage.query.filter_by(room_id=room.id).all()
    
    return render_template('owner/add_room_images.html', room=room, existing_images=existing_images)

@owner_bp.route('/set-featured-image/<int:image_id>', methods=['GET'])
@login_required
def set_featured_image(image_id):
    # Lấy thông tin ảnh
    image = RoomImage.query.get_or_404(image_id)
    room = image.room

    # Kiểm tra quyền sở hữu
    if room.owner_id != current_user.id:
        flash("Bạn không có quyền thực hiện thao tác này.", "danger")
        return redirect(url_for('owner.dashboard'))

    # Bỏ featured của tất cả ảnh khác trong phòng
    RoomImage.query.filter_by(room_id=room.id).update({RoomImage.is_featured: False})
    
    # Đặt ảnh được chọn làm featured
    image.is_featured = True
    db.session.commit()

    flash("Đã đặt ảnh làm ảnh đại diện thành công!", "success")
    return redirect(url_for('owner.add_room_images', room_id=room.id))

@owner_bp.route('/room-image/<int:image_id>/delete')
@owner_required
def delete_room_image(image_id):
    image = RoomImage.query.get_or_404(image_id)
    room_id = image.room_id
    
    # Lấy thông tin phòng để kiểm tra quyền sở hữu
    room = Room.query.get_or_404(room_id)
    
    # Kiểm tra quyền sở hữu
    if room.owner_id != current_user.id:
        flash('Bạn không có quyền xóa ảnh của phòng này.', 'danger')
        return redirect(url_for('owner.dashboard'))
    
    # Delete the image file
    if image.image_path:
        file_path = os.path.join('static', image.image_path)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    # Check if this was the featured image
    was_featured = image.is_featured
    
    # Delete the database record
    db.session.delete(image)
    db.session.commit()
    
    # If we deleted the featured image, set a new one if available
    if was_featured:
        next_image = RoomImage.query.filter_by(room_id=room_id).first()
        if next_image:
            next_image.is_featured = True
            db.session.commit()
    
    flash('Đã xóa ảnh thành công!', 'success')
    return redirect(url_for('owner.add_room_images', room_id=room_id))


@owner_bp.route('/room-detail/<int:room_id>', methods=['GET', 'POST'])
@login_required
def room_detail(room_id):
    room = Room.query.get_or_404(room_id)
    if room.owner_id != current_user.id:
        flash('Bạn không có quyền xem phòng này!', 'danger')
        return redirect(url_for('owner.dashboard'))
    
    if request.method == 'POST':
        # Handle form submission to edit
        room.room_number = request.form.get('room_number', room.room_number)
        room.bed_count = request.form.get('bed_count', room.bed_count)
        room.bathroom_count = request.form.get('bathroom_count', room.bathroom_count)
        room.max_guests = request.form.get('max_guests', room.max_guests)
        room.price_per_hour = request.form.get('price_per_hour', room.price_per_hour)
        
        # Lấy giá trị mô tả ban đầu (đã được lọc tiện ích từ client)
        description = request.form.get('description', '').strip()
        
        # Xử lý các tiện ích được chọn
        has_wifi = 'has_wifi' in request.form
        has_tv = 'has_tv' in request.form
        has_ac = 'has_ac' in request.form
        has_coffee = 'has_coffee' in request.form
        has_view = 'has_view' in request.form
        has_bluetooth = 'has_bluetooth' in request.form
        
        # Tạo mảng tiện ích đã chọn
        amenities = []
        if has_wifi: amenities.append("Wifi tốc độ cao")
        if has_tv: amenities.append("Netflix")
        if has_ac: amenities.append("Điều hòa")
        if has_coffee: amenities.append("Máy pha cà phê")
        if has_view: amenities.append("View đẹp")
        if has_bluetooth: amenities.append("Loa bluetooth")
        
        # Tạo chuỗi tiện ích
        amenities_string = ', '.join(amenities)
        
        # Xử lý dữ liệu lưu vào database
        # Nếu có cả mô tả và tiện ích
        if description and amenities:
            room.description = description + (', ' + amenities_string if description else '')
        # Nếu chỉ có tiện ích
        elif amenities:
            room.description = amenities_string
        # Nếu chỉ có mô tả
        elif description:
            room.description = description
        # Nếu không có cả hai
        else:
            room.description = '1'  # Giá trị mặc định

        # Xử lý hình ảnh
        image_files = request.files.getlist('gallery')
        for image_file in image_files:
            if image_file and image_file.filename:
                # Save file to uploads folder
                filename = secure_filename(image_file.filename)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                image_file.save(file_path)

                # Create RoomImage record
                new_image = RoomImage(
                    room_id=room.id,
                    image_path=f"uploads/{filename}"
                )
                db.session.add(new_image)

        db.session.commit()
        flash("Phòng đã được cập nhật thành công!", "success")
        return redirect(url_for('owner.room_detail', room_id=room.id))

    # For GET requests, display the edit form
    return render_template('owner/room_detail.html', room=room)

@owner_bp.route('/booking/confirm/<int:id>')
@owner_required
def confirm_booking(id):
    booking = Booking.query.get_or_404(id)
    
    # Make sure the owner owns this booking's homestay
    if booking.homestay.owner_id != current_user.id:
        flash('You do not have permission to manage this booking.', 'danger')
        return redirect(url_for('owner.view_bookings'))
    
    # Get all other pending bookings for the same room with overlapping time
    overlapping_pending_bookings = Booking.query.filter(
        Booking.room_id == booking.room_id,
        Booking.id != booking.id,
        Booking.status == 'pending',
        Booking.start_time < booking.end_time,
        Booking.end_time > booking.start_time
    ).all()
    
    # Reject all other overlapping pending bookings
    for other_booking in overlapping_pending_bookings:
        other_booking.status = 'rejected'
        # You could also set a rejection reason here
        other_booking.rejection_reason = "Room was booked by another guest for the same time period."
    
    # Set status to confirmed
    booking.status = 'confirmed'
    
    # Add notification (you can expand this into a proper notification system)
    booking.notification_for_renter = 'Your booking has been confirmed! Please proceed with payment.'
    booking.notification_date = datetime.now()
    
    db.session.commit()
    
    flash('Booking #' + str(booking.id) + ' has been confirmed! Renter will be prompted for payment.', 'success')
    return redirect(url_for('owner.booking_details', booking_id=id))

@owner_bp.route('/reject-booking/<int:id>')
@owner_required
def reject_booking(id):
    booking = Booking.query.get_or_404(id)
    
    # Ensure this booking belongs to one of the current owner's homestays
    if booking.homestay.owner_id != current_user.id:
        flash('Bạn không có quyền từ chối đặt phòng này.', 'danger')
        return redirect(url_for('owner.dashboard'))

    # Update the booking status
    booking.status = 'rejected'
    
    # Add notification with suggestion to book another room/homestay
    booking.notification_for_renter = 'Yêu cầu đặt phòng của bạn đã bị từ chối. Vui lòng tìm kiếm và đặt phòng khác phù hợp với nhu cầu của bạn.'
    booking.notification_date = datetime.now()
    
    db.session.commit()
    
    flash('Đã từ chối đặt phòng.', 'warning')
    return redirect(url_for('owner.view_bookings'))

# @owner_bp.route('/mark-completed/<int:id>')
# @owner_required
# def mark_completed(id):
#     booking = Booking.query.get_or_404(id)
    
#     # Ensure this booking belongs to one of the current owner's homestays
#     if booking.homestay.owner_id != current_user.id:
#         flash('You do not have permission to update this booking.', 'danger')
#         return redirect(url_for('owner.view_bookings'))

#     # Update the booking status
#     booking.status = 'completed'
#     db.session.commit()

#     flash('Booking marked as completed.', 'success')
#     return redirect(url_for('owner.view_bookings'))

@owner_bp.route('/booking-details/<int:booking_id>')
@owner_required
def booking_details(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Ensure this booking belongs to one of the current owner's homestays
    if booking.homestay.owner_id != current_user.id:
        flash('Bạn không có quyền xem thông tin đặt phòng này.', 'danger')
        return redirect(url_for('owner.dashboard'))

    return render_template('owner/booking_details.html', booking=booking)

@owner_bp.route('/settings')
@login_required
def settings():
    return render_template('owner/settings.html')

@owner_bp.route('/profile', methods=['GET', 'POST'])
@owner_required
def profile():
    if request.method == 'POST':
        # Get form data
        current_user.full_name = request.form.get('full_name')
        current_user.email = request.form.get('email')
        current_user.phone = request.form.get('phone')
        current_user.address = request.form.get('address')
        current_user.business_name = request.form.get('business_name')
        current_user.tax_code = request.form.get('tax_code')
        current_user.bank_account = request.form.get('bank_account')
        current_user.bank_name = request.form.get('bank_name')
        
        # Handle avatar upload
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                current_user.avatar = filename
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('Error updating profile. Please try again.', 'danger')
            
    return render_template('owner/profile.html')

@owner_bp.route('/book-room/<int:room_id>', methods=['GET', 'POST'])
@owner_required
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

    return render_template('owner/book_room.html', room=room)

@owner_bp.route('/check-username', methods=['POST'])
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

@owner_bp.route('/check-email', methods=['POST'])
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

@owner_bp.route('/toggle-room-status/<int:room_id>', methods=['POST'])
@login_required
def toggle_room_status(room_id):
    room = Room.query.get_or_404(room_id)
    if room.owner_id != current_user.id:
        flash('Bạn không có quyền thay đổi trạng thái phòng này!', 'danger')
        return redirect(url_for('owner.dashboard'))
    
    room.is_available = not room.is_available
    db.session.commit()
    
    status = 'mở khóa' if room.is_available else 'khóa'
    flash(f'Đã {status} phòng thành công!', 'success')
    return redirect(url_for('owner.dashboard'))