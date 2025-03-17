from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import Homestay, Booking, Review, db, Room, RoomImage
from datetime import datetime, timedelta
from PIL import Image
import io
import os

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

@renter_bp.route('/view-homestay/<int:id>')
def view_homestay(id):
    homestay = Homestay.query.get_or_404(id)
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
        
        flash('Booking request submitted successfully!', 'success')
        return redirect(url_for('renter.dashboard'))
    
    # For GET requests, render the booking form. You can also pass the room to display details.
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