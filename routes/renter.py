from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import Homestay, Booking, db
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
    bookings = Booking.query.filter_by(renter_id=current_user.id).all()
    return render_template('renter/dashboard.html', bookings=bookings, now=datetime.utcnow)

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
    """View details of a specific homestay"""
    homestay = Homestay.query.get_or_404(id)
    return render_template('renter/view_homestay.html', homestay=homestay)

@renter_bp.route('/book/<int:id>', methods=['GET', 'POST'])
@renter_required
def book_homestay(id):
    """Book a homestay"""
    homestay = Homestay.query.get_or_404(id)
    
    if request.method == 'POST':
        # Get booking details
        start_date = request.form.get('start_date')
        start_time = request.form.get('start_time')

        if not start_date or not start_time:
            flash('You must select both date and time', 'warning')
            return redirect(url_for('renter.book_homestay', id=homestay.id))
        
        hours = int(request.form.get('hours', 1))
        
        # Parse datetime
        start_str = f"{start_date} {start_time}"  # e.g. "2025-03-12 13:30"
        start_datetime = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
        end_datetime = start_datetime + timedelta(hours=hours)
        
        # Calculate total price
        total_price = homestay.price_per_hour * hours
        
        # Check if homestay is available for the requested time period
        existing_bookings = Booking.query.filter_by(homestay_id=homestay.id).all()
        
        for booking in existing_bookings:
            # Check if there's overlap with an existing booking
            if (start_datetime < booking.end_time and end_datetime > booking.start_time):
                flash('This homestay is not available during the selected time period', 'danger')
                return redirect(url_for('renter.book_homestay', id=homestay.id))
        
        # Create new booking
        booking = Booking(
            homestay_id=homestay.id,
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