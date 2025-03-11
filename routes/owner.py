# routes/owner.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Homestay, Room, Booking, RoomImage
import os
from datetime import datetime

owner_bp = Blueprint('owner', __name__, url_prefix='/owner')

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
                os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                
                image_path = os.path.join('uploads', filename)
                image.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        
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
                
                os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                
                # Delete old image if it exists
                if homestay.image_path:
                    old_path = os.path.join(current_app.config['UPLOAD_FOLDER'],
                                            os.path.basename(homestay.image_path))
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                homestay.image_path = os.path.join('uploads', filename)
                image.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        
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
    homestays = Homestay.query.filter_by(owner_id=current_user.id).all()
    bookings = []
    for h in homestays:
        bookings.extend(h.bookings)
    
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
                filename = secure_filename(img_file.filename)
                save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                img_file.save(save_path)

                new_img = RoomImage(
                    image_path=f"uploads/{filename}",
                    room_id=room.id
                )
                db.session.add(new_img)
        db.session.commit()
        flash("Images added successfully!", "success")
        return redirect(url_for('owner.dashboard'))
    
    return render_template('owner/add_room_images.html', room=room)
