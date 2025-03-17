# routes/owner.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Homestay, Room, Booking, RoomImage
import os
from datetime import datetime
from PIL import Image
import io
import os


owner_bp = Blueprint('owner', __name__, url_prefix='/owner')

def allowed_file(filename):
    """Check if the file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Decorator to ensure user is an owner
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
    return render_template('owner/dashboard.html', homestays=homestays)


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
            # OPTIONAL: remove old image from disk if you want to replace it

            # e.g., save to uploads folder
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)

            # update homestay's image field in DB
            homestay.image = filename

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
        flash('You do not have permission to delete this homestay', 'danger')
        return redirect(url_for('owner.dashboard'))
    
    # Delete image file if it exists
    if homestay.image_path:
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'],
                                  os.path.basename(homestay.image_path))
        if os.path.exists(image_path):
            os.remove(image_path)
    
    db.session.delete(homestay)
    db.session.commit()
    
    flash('Homestay deleted successfully', 'success')
    return redirect(url_for('owner.dashboard'))


@owner_bp.route('/view-bookings')
@owner_required
def view_bookings():
    """View all bookings for the owner's homestays."""
    homestays = Homestay.query.filter_by(owner_id=current_user.id).all()
    
    # Gather all bookings for these homestays
    bookings = []
    for h in homestays:
        for b in h.bookings:
            bookings.append(b)
    
    return render_template('owner/view_bookings.html', bookings=bookings)



@owner_bp.route('/add-room/<int:homestay_id>', methods=['GET', 'POST'])
@login_required
def add_room(homestay_id):
    homestay = Homestay.query.get_or_404(homestay_id)
    if request.method == 'POST':
        room_number = request.form['room_number']
        floor_number = request.form['floor_number']  # Get Floor Number
        bed_count = request.form['bed_count']
        bathroom_count = request.form['bathroom_count']
        max_guests = request.form['max_guests']
        price_per_hour = request.form['price_per_hour']
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
        flash("Room added successfully with images!", "success")
        return redirect(url_for('owner.dashboard'))

    return render_template('owner/add_room.html', homestay=homestay)


@owner_bp.route('/room/<int:room_id>/add-images', methods=['GET', 'POST'])
@owner_required
def add_room_images(room_id):
    room = Room.query.get_or_404(room_id)
    
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
        flash("Images added successfully to the room gallery!", "success")
        return redirect(url_for('owner.add_room_images', room_id=room.id))
    
    # Get existing images for this room
    existing_images = RoomImage.query.filter_by(room_id=room.id).all()
    
    return render_template('owner/add_room_images.html', room=room, existing_images=existing_images)

@owner_bp.route('/room-image/<int:image_id>/set-featured')
@owner_required
def set_featured_image(image_id):
    image = RoomImage.query.get_or_404(image_id)
    room = Room.query.get_or_404(image.room_id)
    homestay = room.homestay
    
    # Check if the current user owns this homestay
    if homestay.owner_id != current_user.id:
        flash('You do not have permission to modify this room', 'danger')
        return redirect(url_for('owner.dashboard'))
    
    # Clear featured status from all images for this room
    for img in RoomImage.query.filter_by(room_id=room.id).all():
        img.is_featured = False
    
    # Set this image as featured
    image.is_featured = True
    db.session.commit()
    
    flash('Featured image updated successfully', 'success')
    return redirect(url_for('owner.add_room_images', room_id=room.id))

@owner_bp.route('/manage-rooms/<int:homestay_id>')
@login_required
def manage_rooms(homestay_id):
    homestay = Homestay.query.get_or_404(homestay_id)
    rooms = Room.query.filter_by(homestay_id=homestay_id).order_by(Room.floor_number, Room.room_number).all()

    # Group rooms by floor
    rooms_by_floor = {}
    for room in rooms:
        floor = room.floor_number
        if floor not in rooms_by_floor:
            rooms_by_floor[floor] = []
        rooms_by_floor[floor].append(room)

    # Pass the dictionary to the template
    return render_template('owner/manage_rooms.html', homestay=homestay, rooms_by_floor=rooms_by_floor)


@owner_bp.route('/room-image/<int:image_id>/set-featured')
@owner_required
def set_room_image_as_featured(image_id):
    image = RoomImage.query.get_or_404(image_id)
    room = Room.query.get_or_404(image.room_id)
    
    # Clear featured status from all images for this room
    for img in RoomImage.query.filter_by(room_id=room.id).all():
        img.is_featured = False
    
    # Set this image as featured
    image.is_featured = True
    db.session.commit()
    
    flash('Featured image updated successfully', 'success')
    return redirect(url_for('owner.add_room_images', room_id=room.id))

@owner_bp.route('/room-image/<int:image_id>/delete')
@owner_required
def delete_room_image(image_id):
    image = RoomImage.query.get_or_404(image_id)
    room_id = image.room_id
    
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
    
    flash('Image deleted successfully', 'success')
    return redirect(url_for('owner.add_room_images', room_id=room_id))


@owner_bp.route('/edit-room/<int:room_id>', methods=['GET', 'POST'])
@login_required
def edit_room(room_id):
    # 1) Fetch the room by ID
    room = Room.query.get_or_404(room_id)
    
    if request.method == 'POST':
        # 2) Update fields from form
        room.room_number = request.form['room_number']
        room.floor_number = request.form['floor_number']
        room.bed_count = request.form['bed_count']
        room.bathroom_count = request.form['bathroom_count']
        room.max_guests = request.form['max_guests']
        room.price_per_hour = request.form['price_per_hour']
        room.description = request.form['description']
        image_files = request.files.getlist('gallery')
        for image_file in image_files:
            if image_file and image_file.filename != '':
                # Save to uploads folder
                filename = secure_filename(image_file.filename)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                image_file.save(file_path)

                # Add to DB (assuming a RoomImage model)
                new_image = RoomImage(
                    room_id=room.id,
                    image_path=f"uploads/{filename}"
                )
                db.session.add(new_image)
        db.session.commit()
        flash('Room updated successfully!', 'success')
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
    
    # Optionally confirm that current_user is the owner of this homestay
    # e.g., if your Homestay has an owner_id
    # if room.homestay.owner_id != current_user.id:
    #     flash("You do not have permission to edit this room.", "danger")
    #     return redirect(url_for('owner.owner_dashboard'))

    if request.method == 'POST':
        # Handle form submission to edit
        room.room_number = request.form.get('room_number', room.room_number)
        room.bed_count = request.form.get('bed_count', room.bed_count)
        room.bathroom_count = request.form.get('bathroom_count', room.bathroom_count)
        room.max_guests = request.form.get('max_guests', room.max_guests)
        room.price_per_hour = request.form.get('price_per_hour', room.price_per_hour)
        room.description = request.form.get('description', room.description)
        
        # (Optional) handle images if you allow owners to upload more images
        # image_files = request.files.getlist('gallery')
        # ... logic to save them ...
        image_files = request.files.getlist('gallery')  # matches <input name="gallery" multiple>
        for image_file in image_files:
            if image_file and image_file.filename:
                # Save file to uploads folder
                filename = secure_filename(image_file.filename)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                image_file.save(file_path)

                # Create RoomImage record
                new_image = RoomImage(
                    room_id=room.id,
                    image_path=f"uploads/{filename}"  # or however you store the path
                )
                db.session.add(new_image)

        db.session.commit()
        flash("Room updated successfully!", "success")
        return redirect(url_for('owner.owner_room_detail', room_id=room.id))

    # For GET requests, display the edit form
    return render_template('owner/room_detail_owner.html', room=room)

@owner_bp.route('/confirm-booking/<int:id>')
@owner_required
def confirm_booking(id):
    booking = Booking.query.get_or_404(id)
    
    # Ensure this booking belongs to one of the current owner's homestays
    if booking.homestay.owner_id != current_user.id:
        flash('You do not have permission to confirm this booking.', 'danger')
        return redirect(url_for('owner.view_bookings'))

    # Update the booking status
    booking.status = 'confirmed'
    db.session.commit()

    flash('Booking confirmed successfully!', 'success')
    return redirect(url_for('owner.view_bookings'))

@owner_bp.route('/reject-booking/<int:id>')
@owner_required
def reject_booking(id):
    booking = Booking.query.get_or_404(id)
    
    # Ensure this booking belongs to one of the current owner's homestays
    if booking.homestay.owner_id != current_user.id:
        flash('You do not have permission to reject this booking.', 'danger')
        return redirect(url_for('owner.view_bookings'))

    # Update the booking status
    booking.status = 'rejected'
    db.session.commit()

    flash('Booking rejected.', 'warning')
    return redirect(url_for('owner.view_bookings'))

@owner_bp.route('/mark-completed/<int:id>')
@owner_required
def mark_completed(id):
    booking = Booking.query.get_or_404(id)
    
    # Ensure this booking belongs to one of the current owner's homestays
    if booking.homestay.owner_id != current_user.id:
        flash('You do not have permission to update this booking.', 'danger')
        return redirect(url_for('owner.view_bookings'))

    # Update the booking status
    booking.status = 'completed'
    db.session.commit()

    flash('Booking marked as completed.', 'success')
    return redirect(url_for('owner.view_bookings'))

@owner_bp.route('/booking-details/<int:booking_id>')
@owner_required
def booking_details(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Ensure this booking belongs to one of the current owner's homestays
    if booking.homestay.owner_id != current_user.id:
        flash('You do not have permission to view this booking.', 'danger')
        return redirect(url_for('owner.view_bookings'))

    return render_template('owner/booking_details.html', booking=booking)