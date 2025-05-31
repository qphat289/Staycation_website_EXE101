# routes/owner.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Homestay, Room, Booking, RoomImage, Renter, Admin, Owner
import os
from datetime import datetime, timedelta
from PIL import Image
import io
import os


owner_bp = Blueprint('owner', __name__, url_prefix='/owner')

def allowed_file(filename):
    """Check if the file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Custom decorator to ensure user is an owner
def owner_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_owner():
            flash('You must be an owner to access this page', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


@owner_bp.route('/dashboard')
@owner_required
def dashboard():
    homestays = Homestay.query.filter_by(owner_id=current_user.id).all()
    
    # Get homestay IDs owned by current owner
    homestay_ids = [h.id for h in homestays]
    
    # Get pending bookings count for notifications
    pending_bookings = Booking.query.filter(
        Booking.homestay_id.in_(homestay_ids),
        Booking.status == 'pending'
    ).all()
    
    # Get recent bookings (last 5) for quick access
    recent_bookings = Booking.query.filter(
        Booking.homestay_id.in_(homestay_ids)
    ).order_by(Booking.created_at.desc()).limit(5).all()
    
    return render_template(
        'owner/dashboard.html', 
        homestays=homestays, 
        pending_bookings=pending_bookings,
        recent_bookings=recent_bookings
    )


@owner_bp.route('/manage-homestays')
@owner_required
def manage_homestays():
    homestays = Homestay.query.filter_by(owner_id=current_user.id).all()
    return render_template('owner/manage_homestays.html', homestays=homestays)


@owner_bp.route('/add-homestay', methods=['GET', 'POST'])
@login_required
def add_homestay():
    """Add a new homestay"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        address = request.form.get('address')
        city = request.form.get('city')
        district = request.form.get('district')
        
        # Handle image upload (optional)
        image_path = None
        if 'image' in request.files:
            image = request.files['image']
            if image.filename:
                filename = secure_filename(image.filename)
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                filename = f"{timestamp}_{filename}"
                
                # Make sure uploads folder exists inside static
                upload_folder = os.path.join('static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                
                # Save image to static/uploads folder
                save_path = os.path.join(upload_folder, filename)
                image.save(save_path)
                
                # Store path relative to static folder for url_for
                image_path = f"uploads/{filename}"
        
        homestay = Homestay(
            title=title,
            description=description,
            address=address,
            city=city,
            district=district,
            image_path=image_path,
            owner_id=current_user.id 
        )
        
        db.session.add(homestay)
        db.session.commit()
        flash("Homestay added successfully!", "success")

        # INSTEAD of returning to manage_homestays, return to your owner dashboard
        return redirect(url_for('owner.dashboard'))

    return render_template('owner/add_homestay.html')

@owner_bp.route('/edit-homestay/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_homestay(id):
    homestay = Homestay.query.get_or_404(id)

    if request.method == 'POST':
        # 1) Update basic fields
        homestay.title = request.form.get('title')
        homestay.description = request.form.get('description')
        homestay.city = request.form.get('city')
        homestay.district = request.form.get('district')
        homestay.address = request.form.get('address')

        # 2) Handle new image upload (if provided)
        image_file = request.files.get('image')
        if image_file and image_file.filename != '':
            # Tuỳ chọn: xoá ảnh cũ nếu muốn
            if homestay.image_path:
                old_path = os.path.join(
                    current_app.config['UPLOAD_FOLDER'],
                    os.path.basename(homestay.image_path)
                )
                if os.path.exists(old_path):
                    os.remove(old_path)

            # Lưu file mới
            filename = secure_filename(image_file.filename)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"{timestamp}_{filename}"

            # Tạo đường dẫn lưu file trong 'static/uploads'
            save_path = os.path.join(
                current_app.config['UPLOAD_FOLDER'], 
                filename
            )
            image_file.save(save_path)

            # **QUAN TRỌNG**: Gán vào `image_path`, không phải `image`
            homestay.image_path = f"uploads/{filename}"

        # 3) Commit changes to DB
        db.session.commit()
        flash('Homestay updated successfully!', 'success')
        return redirect(url_for('owner.owner_dashboard'))
    
    # For GET requests, display the edit form with existing data
    return render_template('owner/edit_homestay.html', homestay=homestay)

@owner_bp.route('/delete-homestay/<int:id>')
@owner_required
def delete_homestay(id):
    homestay = Homestay.query.get_or_404(id)
    
    # Ensure the current user owns this homestay
    if homestay.owner_id != current_user.id:
        flash('Bạn không có quyền xóa homestay này', 'danger')
        return redirect(url_for('owner.dashboard'))
    
    # Delete image file if it exists
    if homestay.image_path:
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'],
                                  os.path.basename(homestay.image_path))
        if os.path.exists(image_path):
            os.remove(image_path)
    
    db.session.delete(homestay)
    db.session.commit()
    
    flash('Đã xóa homestay thành công!', 'success')
    return redirect(url_for('owner.dashboard'))


@owner_bp.route('/view-bookings')
@owner_bp.route('/view-bookings/<status>')
@owner_required
def view_bookings(status=None):
    # Get all homestays owned by current user
    homestays = Homestay.query.filter_by(owner_id=current_user.id).all()
    
    # Get all bookings for these homestays
    all_bookings = []
    for homestay in homestays:
        all_bookings.extend(homestay.bookings)
    
    # Filter bookings by status if specified
    if status and status != 'all':
        filtered_bookings = [b for b in all_bookings if b.status == status]
    else:
        filtered_bookings = all_bookings
    
    # Sort bookings by created_at (newest first)
    filtered_bookings.sort(key=lambda x: x.created_at, reverse=True)
    
    return render_template('owner/view_bookings.html', 
                          bookings=all_bookings,  # Send all bookings for counting
                          filtered_bookings=filtered_bookings)  # Send filtered bookings for display



@owner_bp.route('/add-room/<int:homestay_id>', methods=['GET', 'POST'])
@login_required
def add_room(homestay_id):
    homestay = Homestay.query.get_or_404(homestay_id)
    
    # Kiểm tra quyền sở hữu
    if homestay.owner_id != current_user.id:
        flash('Bạn không có quyền thêm phòng vào homestay này.', 'danger')
        return redirect(url_for('owner.dashboard'))
    
    if request.method == 'POST':
        room_number = request.form['room_number']
        floor_number = request.form['floor_number']  # Get Floor Number
        bed_count = request.form['bed_count']
        bathroom_count = request.form['bathroom_count']
        max_guests = request.form['max_guests']
        # Convert price from display format (e.g. 120 -> 120.000 for storage)
        price_per_hour = float(request.form['price_per_hour'])
        description = request.form['description']

        new_room = Room(
            homestay_id=homestay_id,
            room_number=room_number,
            floor_number=floor_number,  # Save Floor Number
            bed_count=bed_count,
            bathroom_count=bathroom_count,
            max_guests=max_guests,
            price_per_hour=price_per_hour,
            description=description
        )

        db.session.add(new_room)
        db.session.commit()
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)

            featured_image = RoomImage(
                image_path=f"uploads/{filename}",
                is_featured=True,
                room_id=new_room.id
            )
            db.session.add(featured_image)

        # Multiple gallery images
        gallery_files = request.files.getlist('gallery')
        for g_file in gallery_files:
            if g_file and g_file.filename:
                g_filename = secure_filename(g_file.filename)
                g_path = os.path.join(current_app.config['UPLOAD_FOLDER'], g_filename)
                g_file.save(g_path)

                gallery_image = RoomImage(
                    image_path=f"uploads/{g_filename}",
                    is_featured=False,
                    room_id=new_room.id
                )
                db.session.add(gallery_image)

        db.session.commit()
        flash("Đã thêm phòng thành công!", "success")
        return redirect(url_for('owner.dashboard'))

    return render_template('owner/add_room.html', homestay=homestay)


@owner_bp.route('/room/<int:room_id>/add-images', methods=['GET', 'POST'])
@owner_required
def add_room_images(room_id):
    room = Room.query.get_or_404(room_id)
    
    # Kiểm tra quyền sở hữu
    if room.homestay.owner_id != current_user.id:
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
    if room.homestay.owner_id != current_user.id:
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
    if room.homestay.owner_id != current_user.id:
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


@owner_bp.route('/edit-room/<int:room_id>', methods=['GET', 'POST'])
@login_required
def edit_room(room_id):
    # 1) Fetch the room by ID
    room = Room.query.get_or_404(room_id)
    
    # Kiểm tra quyền sở hữu phòng
    if room.homestay.owner_id != current_user.id:
        flash("Bạn không có quyền chỉnh sửa phòng này.", "danger")
        return redirect(url_for('owner.dashboard'))
    
    if request.method == 'POST':
        # Handle form submission to edit
        room.room_number = request.form.get('room_number', room.room_number)
        room.bed_count = request.form.get('bed_count', room.bed_count)
        room.bathroom_count = request.form.get('bathroom_count', room.bathroom_count)
        room.max_guests = request.form.get('max_guests', room.max_guests)
        # Convert price from display format (e.g. 100 -> 0.1 for storage)
        room.price_per_hour = float(request.form.get('price_per_hour', room.price_per_hour))
        
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
        return redirect(url_for('owner.owner_room_detail', room_id=room.id))

    # Render a form with existing room data
    return render_template('owner/room_detail_owner.html', room=room)

@owner_bp.route('/dashboard')
@login_required
def owner_dashboard():
    homestays = Homestay.query.filter_by(owner_id=current_user.id).all()
    return render_template('owner/dashboard.html', homestays=homestays)


@owner_bp.route('/room-detail/<int:room_id>', methods=['GET', 'POST'])
@login_required
def owner_room_detail(room_id):
    room = Room.query.get_or_404(room_id)
    
    # Kiểm tra quyền sở hữu - Owner chỉ xem được phòng của mình
    if room.homestay.owner_id != current_user.id:
        flash("Bạn không có quyền xem hoặc chỉnh sửa phòng này.", "danger")
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
        return redirect(url_for('owner.owner_room_detail', room_id=room.id))

    # For GET requests, display the edit form
    return render_template('owner/room_detail_owner.html', room=room)

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

@owner_bp.route('/switch-to-owner')
@login_required
def switch_to_owner():
    if current_user.role != 'renter':
        flash('Bạn không phải là người thuê để thực hiện chuyển đổi này', 'danger')
        return redirect(url_for('home'))
    
    current_user.temp_role = 'owner'
    db.session.commit()
    flash('Đã chuyển sang vai trò chủ nhà', 'success')
    return redirect(url_for('home'))

@owner_bp.route('/profile', methods=['GET', 'POST'])
@owner_required
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
                return redirect(url_for('owner.profile'))
            
            # Check if email is being changed and if it already exists
            if new_email != current_user.email:
                existing_admin = Admin.query.filter_by(email=new_email).first()
                existing_owner = Owner.query.filter_by(email=new_email).filter(Owner.id != current_user.id).first()
                existing_renter = Renter.query.filter_by(email=new_email).first()
                
                if existing_admin or existing_owner or existing_renter:
                    flash(f"Email '{new_email}' đã tồn tại! Vui lòng chọn email khác.", "danger")
                    return redirect(url_for('owner.profile'))
            
            # Check if phone is being changed and if it already exists
            if new_phone and new_phone != current_user.phone:
                existing_owner = Owner.query.filter_by(phone=new_phone).filter(Owner.id != current_user.id).first()
                existing_renter = Renter.query.filter_by(phone=new_phone).first()
                
                if existing_owner or existing_renter:
                    flash(f"Số điện thoại '{new_phone}' đã tồn tại! Vui lòng chọn số khác.", "danger")
                    return redirect(url_for('owner.profile'))
            
            # Check if personal_id is being changed and if it already exists
            if new_personal_id != current_user.personal_id:
                existing_owner = Owner.query.filter_by(personal_id=new_personal_id).filter(Owner.id != current_user.id).first()
                existing_renter = Renter.query.filter_by(personal_id=new_personal_id).first()
                
                if existing_owner or existing_renter:
                    flash(f"CCCD/CMND '{new_personal_id}' đã tồn tại! Vui lòng chọn số khác.", "danger")
                    return redirect(url_for('owner.profile'))
            
            # Update user info
            current_user.full_name = new_full_name
            current_user.phone = new_phone
            current_user.email = new_email
            current_user.personal_id = new_personal_id

            # Handle avatar upload
            if 'avatar' in request.files:
                avatar = request.files['avatar']
                print(f"Received file: {avatar.filename}")
                
                if avatar and avatar.filename != '':
                    if not allowed_file(avatar.filename):
                        flash("File type not allowed. Please use: png, jpg, jpeg, or gif", "danger")
                        return redirect(url_for('owner.profile'))
                    
                    try:
                        # Ensure upload folder exists
                        upload_folder = current_app.config['UPLOAD_FOLDER']
                        print(f"Upload folder path: {upload_folder}")
                        
                        if not os.path.exists(upload_folder):
                            print(f"Creating upload folder: {upload_folder}")
                            os.makedirs(upload_folder, exist_ok=True)
                        
                        # Generate secure filename and save file
                        filename = secure_filename(avatar.filename)
                        filepath = os.path.join(upload_folder, filename)
                        print(f"Saving file to: {filepath}")
                        
                        # Save file
                        avatar.save(filepath)
                        
                        if not os.path.exists(filepath):
                            raise Exception(f"File was not saved successfully to {filepath}")
                        
                        print(f"File saved successfully. Size: {os.path.getsize(filepath)} bytes")
                        
                        # Delete old avatar if exists
                        if current_user.avatar:
                            old_avatar_path = os.path.join(upload_folder, current_user.avatar)
                            if os.path.exists(old_avatar_path):
                                os.remove(old_avatar_path)
                                print(f"Deleted old avatar: {old_avatar_path}")
                        
                        # Update the avatar field in the user's profile
                        current_user.avatar = filename
                        print(f"Updated user avatar in database: {filename}")
                        
                    except Exception as e:
                        print(f"Error during file operations: {str(e)}")
                        flash(f"Error saving avatar: {str(e)}", "danger")
                        return redirect(url_for('owner.profile'))

            # Handle CCCD upload
            if 'cccd_front' in request.files:
                cccd_front = request.files['cccd_front']
                print(f"Received CCCD front file: {cccd_front.filename}")
                
                if cccd_front and cccd_front.filename != '':
                    if not allowed_file(cccd_front.filename):
                        flash("File type not allowed. Please use: png, jpg, jpeg, or gif", "danger")
                        return redirect(url_for('owner.profile'))
                    
                    try:
                        # Ensure upload folder exists
                        upload_folder = current_app.config['UPLOAD_FOLDER']
                        
                        if not os.path.exists(upload_folder):
                            os.makedirs(upload_folder, exist_ok=True)
                        
                        # Generate secure filename and save file
                        filename = secure_filename(cccd_front.filename)
                        filepath = os.path.join(upload_folder, filename)
                        
                        # Save file
                        cccd_front.save(filepath)
                        
                        if not os.path.exists(filepath):
                            raise Exception(f"File was not saved successfully to {filepath}")
                        
                        # Delete old CCCD front if exists
                        if current_user.cccd_front_image:
                            old_cccd_path = os.path.join(upload_folder, current_user.cccd_front_image)
                            if os.path.exists(old_cccd_path):
                                os.remove(old_cccd_path)
                        
                        # Update the CCCD front field in the user's profile
                        current_user.cccd_front_image = filename
                        
                    except Exception as e:
                        print(f"Error during CCCD front file operations: {str(e)}")
                        flash(f"Error saving CCCD front: {str(e)}", "danger")
                        return redirect(url_for('owner.profile'))

            if 'cccd_back' in request.files:
                cccd_back = request.files['cccd_back']
                print(f"Received CCCD back file: {cccd_back.filename}")
                
                if cccd_back and cccd_back.filename != '':
                    if not allowed_file(cccd_back.filename):
                        flash("File type not allowed. Please use: png, jpg, jpeg, or gif", "danger")
                        return redirect(url_for('owner.profile'))
                    
                    try:
                        # Ensure upload folder exists
                        upload_folder = current_app.config['UPLOAD_FOLDER']
                        
                        if not os.path.exists(upload_folder):
                            os.makedirs(upload_folder, exist_ok=True)
                        
                        # Generate secure filename and save file
                        filename = secure_filename(cccd_back.filename)
                        filepath = os.path.join(upload_folder, filename)
                        
                        # Save file
                        cccd_back.save(filepath)
                        
                        if not os.path.exists(filepath):
                            raise Exception(f"File was not saved successfully to {filepath}")
                        
                        # Delete old CCCD back if exists
                        if current_user.cccd_back_image:
                            old_cccd_path = os.path.join(upload_folder, current_user.cccd_back_image)
                            if os.path.exists(old_cccd_path):
                                os.remove(old_cccd_path)
                        
                        # Update the CCCD back field in the user's profile
                        current_user.cccd_back_image = filename
                        
                    except Exception as e:
                        print(f"Error during CCCD back file operations: {str(e)}")
                        flash(f"Error saving CCCD back: {str(e)}", "danger")
                        return redirect(url_for('owner.profile'))

            # Commit changes to the database
            db.session.commit()
            flash("Profile updated successfully!", "success")
            
        except Exception as e:
            print(f"Error updating profile: {str(e)}")
            db.session.rollback()
            flash(f"Error updating profile: {str(e)}", "danger")
            
        return redirect(url_for('owner.profile'))

    return render_template("user/profile.html")

@owner_bp.route('/book-room/<int:homestay_id>', methods=['GET', 'POST'])
@owner_required
def book_room(homestay_id):
    """Allow owner to book a room for themselves at their homestay"""
    homestay = Homestay.query.get_or_404(homestay_id)
    
    # Ensure this homestay belongs to the current owner
    if homestay.owner_id != current_user.id:
        flash("Bạn chỉ có thể đặt phòng trong homestay của chính mình.", "danger")
        return redirect(url_for('owner.dashboard'))
    
    # Get room_id from query string (or form data)
    room_id = request.args.get('room_id') or request.form.get('room_id')
    
    if request.method == 'POST':
        if not room_id:
            flash("Vui lòng chọn phòng.", "warning")
            return redirect(url_for('owner.book_room', homestay_id=homestay.id))
            
        room = Room.query.get_or_404(room_id)
        
        # Verify the room belongs to this homestay and owner
        if room.homestay_id != homestay.id:
            flash("Lựa chọn phòng không hợp lệ.", "danger")
            return redirect(url_for('owner.book_room', homestay_id=homestay.id))
            
        # Double check owner ownership
        if room.homestay.owner_id != current_user.id:
            flash("Bạn chỉ có thể đặt phòng trong homestay của chính mình.", "danger")
            return redirect(url_for('owner.dashboard'))
        
        duration_str = request.form.get('duration')
        if not duration_str:
            flash("Duration is required", "warning")
            return redirect(url_for('owner.book_room', homestay_id=homestay.id, room_id=room_id))
        
        try:
            duration = int(duration_str)
        except ValueError:
            flash("Invalid duration value.", "danger")
            return redirect(url_for('owner.book_room', homestay_id=homestay.id, room_id=room_id))
        
        if duration < 1:
            flash("Minimum duration is 1 minute.", "warning")
            return redirect(url_for('owner.book_room', homestay_id=homestay.id, room_id=room_id))
        
        start_date = request.form.get('start_date')
        start_time = request.form.get('start_time')
        if not start_date or not start_time:
            flash("You must select both date and time.", "warning")
            return redirect(url_for('owner.book_room', homestay_id=homestay.id, room_id=room_id))
        
        start_str = f"{start_date} {start_time}"
        try:
            start_datetime = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
        except ValueError:
            flash("Invalid date or time format.", "danger")
            return redirect(url_for('owner.book_room', homestay_id=homestay.id, room_id=room_id))
        
        end_datetime = start_datetime + timedelta(minutes=duration)
        # Calculate total price using the room's price; convert minutes to hours.
        total_price = room.price_per_hour * (duration / 60)
        
        # Check for overlapping bookings for this room
        existing_bookings = Booking.query.filter_by(room_id=room.id).all()
        for booking in existing_bookings:
            if start_datetime < booking.end_time and end_datetime > booking.start_time:
                flash('This room is not available during the selected time period.', 'danger')
                return redirect(url_for('owner.book_room', homestay_id=homestay.id, room_id=room_id))
        
        # Tìm renter account của owner hiện tại (nếu có)
        renter = Renter.query.filter_by(email=current_user.email).first()
        
        # Nếu không có, tạo mới một renter cho owner này
        if not renter:
            renter = Renter(
                username=f"{current_user.username}_renter",
                email=current_user.email,
                full_name=current_user.full_name,
                phone=current_user.phone,
                personal_id=current_user.personal_id
            )
            # Generate a default password based on the username
            default_password = f"{current_user.username}123"
            renter.set_password(default_password)
            db.session.add(renter)
            db.session.commit()
        
        # Tạo booking mới
        new_booking = Booking(
            homestay_id=homestay.id,
            room_id=room.id,
            renter_id=renter.id,
            start_time=start_datetime,
            end_time=end_datetime,
            total_price=total_price,
            status='confirmed'  # Auto-confirm since owner is booking for themselves
        )
        
        db.session.add(new_booking)
        db.session.commit()

        flash('Booking created successfully!', 'success')
        return redirect(url_for('owner.view_bookings'))
        
    # GET request - hiển thị form để đặt phòng
    return render_template('owner/book_room.html', homestay=homestay)

@owner_bp.route('/manage-rooms/<int:homestay_id>')
@login_required
def manage_rooms(homestay_id):
    homestay = Homestay.query.get_or_404(homestay_id)
    
    # Kiểm tra quyền sở hữu
    if homestay.owner_id != current_user.id:
        flash('Bạn không có quyền quản lý phòng của homestay này.', 'danger')
        return redirect(url_for('owner.dashboard'))
    
    # Lấy tham số floor từ query string (nếu có)
    floor_filter = request.args.get('floor', type=int)
    
    # Lấy tất cả các phòng để xác định danh sách các tầng
    all_rooms = Room.query.filter_by(homestay_id=homestay_id).all()
    all_floors = sorted(set(room.floor_number for room in all_rooms))
    
    # Lọc phòng theo tầng nếu có tham số floor
    if floor_filter:
        rooms = Room.query.filter_by(homestay_id=homestay_id, floor_number=floor_filter).order_by(Room.room_number).all()
    else:
        # Lấy tất cả phòng nếu không có tham số floor
        rooms = all_rooms
        rooms.sort(key=lambda x: (x.floor_number, x.room_number))

    # Group rooms by floor
    rooms_by_floor = {}
    for room in rooms:
        floor = room.floor_number
        if floor not in rooms_by_floor:
            rooms_by_floor[floor] = []
        rooms_by_floor[floor].append(room)

    # Pass the dictionary to the template
    return render_template('owner/manage_rooms.html', homestay=homestay, rooms_by_floor=rooms_by_floor, all_floors=all_floors)

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