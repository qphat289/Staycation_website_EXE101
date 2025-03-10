# routes/owner.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Homestay
import os
from datetime import datetime

owner_bp = Blueprint('owner', __name__, url_prefix='/owner')

# Custom decorator to ensure user is an owner
def owner_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_owner():  # is_owner() is in your User model
            flash('You must be an owner to access this page', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


@owner_bp.route('/dashboard')
@owner_required
def dashboard():
    """
    Display an owner dashboard with some quick info or a partial list of homestays.
    You could add stats here if you like.
    """
    homestays = Homestay.query.filter_by(owner_id=current_user.id).all()
    return render_template('owner/dashboard.html', homestays=homestays)


@owner_bp.route('/manage-homestays')
@owner_required
def manage_homestays():
    """
    Display a list of all homestays the current owner has posted.
    Useful if you want a separate "Manage" page from the dashboard.
    """
    homestays = Homestay.query.filter_by(owner_id=current_user.id).all()
    return render_template('owner/manage_homestays.html', homestays=homestays)


@owner_bp.route('/add-homestay', methods=['GET', 'POST'])
@owner_required
def add_homestay():
    """Add a new homestay"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        price_per_hour = float(request.form.get('price_per_hour'))
        address = request.form.get('address')
        city = request.form.get('city')
        district = request.form.get('district')
        max_guests = int(request.form.get('max_guests'))
        bedrooms = int(request.form.get('bedrooms'))
        bathrooms = int(request.form.get('bathrooms'))
        
        # Handle image upload (optional)
        image_path = None
        if 'image' in request.files:
            image = request.files['image']
            if image.filename:
                filename = secure_filename(image.filename)
                # Create unique filename
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                filename = f"{timestamp}_{filename}"
                
                # Ensure upload folder exists
                os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                
                image_path = os.path.join('uploads', filename)
                image.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        
        # Create new homestay
        homestay = Homestay(
            title=title,
            description=description,
            price_per_hour=price_per_hour,
            address=address,
            city=city,
            district=district,
            max_guests=max_guests,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
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
    """Edit an existing homestay"""
    homestay = Homestay.query.get_or_404(id)
    
    # Ensure the current user owns this homestay
    if homestay.owner_id != current_user.id:
        flash('You do not have permission to edit this homestay', 'danger')
        return redirect(url_for('owner.dashboard'))
    
    if request.method == 'POST':
        homestay.title = request.form.get('title')
        homestay.description = request.form.get('description')
        homestay.price_per_hour = float(request.form.get('price_per_hour'))
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
    """Delete a homestay"""
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
    """View all bookings for the owner's homestays"""
    homestays = Homestay.query.filter_by(owner_id=current_user.id).all()
    
    # Gather bookings for each homestay
    bookings = []
    for h in homestays:
        for booking in h.bookings:
            bookings.append(booking)
    
    # If you have a Booking model with fields like booking.id, booking.status, etc.,
    # you can pass them to a template to display
    return render_template('owner/view_bookings.html', bookings=bookings)
