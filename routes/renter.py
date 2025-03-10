from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import Homestay, Booking, Review, db
from datetime import datetime, timedelta

renter_bp = Blueprint('renter', __name__, url_prefix='/renter')

# Custom decorator to ensure user is a renter
def renter_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_renter():
            flash('You must be a renter to access this page', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@renter_bp.route('/dashboard')
@renter_required
def dashboard():
    """Display renter dashboard with their bookings, newest first."""
    # Order by created_at descending (or booking.id desc if you prefer)
    bookings = Booking.query \
        .filter_by(renter_id=current_user.id) \
        .order_by(Booking.created_at.desc()) \
        .all()
    
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
    query = Homestay.query
    
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

@renter_bp.route('/homestay/<int:id>')
def view_homestay(id):
    homestay = Homestay.query.get_or_404(id)
    # Get all rooms for the homestay (you might filter based on availability later)
    rooms = homestay.rooms  # Assuming the relationship is set up in Homestay model
    reviews = homestay.reviews.order_by(Review.created_at.desc()).all()
    return render_template('renter/view_homestay.html', homestay=homestay, rooms=rooms, reviews=reviews)



@renter_bp.route('/book/<int:id>', methods=['GET', 'POST'])
@renter_required
def book_homestay(id):
    homestay = Homestay.query.get_or_404(id)
    
    if request.method == 'POST':
        # Get selected room_id from the form
        room_id = request.form.get('room_id')
        start_date = request.form.get('start_date')
        start_time = request.form.get('start_time')
        if not start_date or not start_time:
            flash('You must select both date and time', 'warning')
            return redirect(url_for('renter.book_homestay', id=homestay.id))
        
        hours = int(request.form.get('hours', 1))
        start_str = f"{start_date} {start_time}"
        start_datetime = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
        end_datetime = start_datetime + timedelta(hours=hours)
        total_price = homestay.price_per_hour * hours

        # Check for overlapping bookings (for this homestay, or even for this room if desired)
        existing_bookings = Booking.query.filter_by(homestay_id=homestay.id).all()
        for booking in existing_bookings:
            if (start_datetime < booking.end_time and end_datetime > booking.start_time):
                flash('This homestay is not available during the selected time period', 'danger')
                return redirect(url_for('renter.book_homestay', id=homestay.id))
        
        booking = Booking(
            homestay_id=homestay.id,
            room_id=room_id,  # now we use the room_id from the form
            renter_id=current_user.id,
            start_time=start_datetime,
            end_time=end_datetime,
            total_price=total_price,
            status='pending'
        )
        db.session.add(booking)
        db.session.commit()
        
        flash('Booking request submitted successfully!', 'success')
        return redirect(url_for('renter.dashboard'))
    
    return render_template('renter/book_homestay.html', homestay=homestay)
    


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
        current_user.full_name = request.form.get('full_name')
        current_user.phone = request.form.get('phone')
        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('renter.profile'))

    return render_template("renter/profile.html")

@renter_bp.route('/homestay/<int:homestay_id>/review', methods=['GET', 'POST'])
@login_required
def add_review(homestay_id):
    homestay = Homestay.query.get_or_404(homestay_id)

    # Check if the user has already left a review for this homestay
    existing_review = Review.query.filter_by(homestay_id=homestay.id, user_id=current_user.id).first()
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
            user_id=current_user.id
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

