# routes/owner.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Homestay, Room, Booking, RoomImage
import os
from datetime import datetime
from PIL import Image

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
@owner_required
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
        
        flash('Homestay added successfully!', 'success')
        return redirect(url_for('owner.manage_homestays'))
        
    return render_template('owner/add_homestay.html')


@owner_bp.route('/edit-homestay/<int:id>', methods=['GET', 'POST'])
@owner_required
def edit_homestay(id):
    homestay = Homestay.query.get_or_404(id)
    
    # Ensure the current user owns this homestay
    if homestay.owner_id != current_user.id:
        flash('You do not have permission to edit this homestay', 'danger')
        return redirect(url_for('owner.dashboard'))
    
    if request.method == 'POST':
        homestay.title = request.form.get('title')
        homestay.description = request.form.get('description')
        # If you removed price from Homestay, remove references here
        # homestay.price_per_hour = float(request.form.get('price_per_hour'))
        homestay.address = request.form.get('address')
        homestay.city = request.form.get('city')
        homestay.district = request.form.get('district')
        homestay.max_guests = int(request.form.get('max_guests'))
        homestay.bedrooms = int(request.form.get('bedrooms'))
        homestay.bathrooms = int(request.form.get('bathrooms'))
        homestay.updated_at = datetime.utcnow()
        
        # Handle image upload
        if 'image' in request.files:
            image = request.files['image']
            if image.filename:
                filename = secure_filename(image.filename)
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                filename = f"{timestamp}_{filename}"
                
                # Make sure uploads folder exists inside static
                upload_folder = os.path.join('static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                
                # Delete old image if it exists
                if homestay.image_path:
                    old_path = os.path.join('static', homestay.image_path)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                # Save image to static/uploads folder
                save_path = os.path.join(upload_folder, filename)
                image.save(save_path)
                
                # Store path relative to static folder for url_for
                homestay.image_path = f"uploads/{filename}"
        
        db.session.commit()
        
        flash('Homestay updated successfully!', 'success')
        return redirect(url_for('owner.manage_homestays'))
        
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
    return redirect(url_for('owner.manage_homestays'))


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
@owner_required
def add_room(homestay_id):
    homestay = Homestay.query.get_or_404(homestay_id)
    
    if request.method == 'POST':
        # Basic room fields
        room_number = request.form.get('room_number')
        bed_count = int(request.form.get('bed_count', 1))
        bathroom_count = int(request.form.get('bathroom_count', 1))
        
        # Fallback to 1 if missing
        max_guests_str = request.form.get('max_guests', '1')
        max_guests = int(max_guests_str)
        
        price_per_hour = float(request.form.get('price_per_hour', 0.0))
        description = request.form.get('description', '')

        # Create the new Room
        new_room = Room(
            room_number=room_number,
            bed_count=bed_count,
            bathroom_count=bathroom_count,
            max_guests=max_guests,
            price_per_hour=price_per_hour,
            description=description,
            homestay_id=homestay.id
        )
        db.session.add(new_room)
        db.session.commit()

        # Single "featured" image if desired
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
@owner_required
def manage_rooms(homestay_id):
    homestay = Homestay.query.get_or_404(homestay_id)
    
    # Check if the current user owns this homestay
    if homestay.owner_id != current_user.id:
        flash('You do not have permission to manage rooms for this homestay', 'danger')
        return redirect(url_for('owner.dashboard'))
    
    rooms = Room.query.filter_by(homestay_id=homestay_id).all()
    
    # For each room, get the featured image
    for room in rooms:
        room.featured_image = RoomImage.query.filter_by(room_id=room.id, is_featured=True).first()
    
    return render_template('owner/manage_rooms.html', homestay=homestay, rooms=rooms)

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


