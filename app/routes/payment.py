# routes/payment.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models.models import db, Booking
from datetime import datetime, timedelta
import json
import os
import uuid
from dotenv import load_dotenv

payment_bp = Blueprint('payment', __name__, url_prefix='/payment')

# Load environment variables
load_dotenv()

# Get the base URL for the application
APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:5000")

@payment_bp.route('/checkout/<int:booking_id>')
@login_required
def checkout(booking_id):
    # Get the booking
    booking = Booking.query.get_or_404(booking_id)
    
    # Make sure the current user is the one who made the booking
    if booking.renter_id != current_user.id:
        flash('Bạn không có quyền truy cập thanh toán này.', 'danger')
        return redirect(url_for('renter.dashboard'))
    
    # Check if the booking is already paid
    if booking.payment_status == 'paid':
        flash('Đơn đặt phòng này đã được thanh toán.', 'info')
        return redirect(url_for('renter.booking_details', booking_id=booking_id))
    
    # Generate a unique order ID
    order_id = f"ORDER-{booking.id}-{uuid.uuid4().hex[:8]}"
    
    # Save the order ID in the booking for reference
    booking.payment_reference = order_id
    db.session.commit()
    
    try:
        # Simulate successful payment
        booking.payment_status = 'paid'
        booking.payment_date = datetime.now()
        booking.payment_method = 'demo'
        # Set status to confirmed after payment (no need for owner approval)
        booking.status = 'confirmed'
        booking.renter.experience_points += int(booking.total_price)
        db.session.commit()
        
        flash('Thanh toán thành công! Đặt phòng đã được xác nhận.', 'success')
        return redirect(url_for('renter.booking_details', booking_id=booking_id))
    
    except Exception as e:
        current_app.logger.error(f"Error processing payment: {str(e)}")
        flash(f"Lỗi xử lý thanh toán: {str(e)}", 'danger')
        return redirect(url_for('renter.booking_details', booking_id=booking_id))

@payment_bp.route('/check-status/<int:booking_id>')
@login_required
def check_status(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.renter_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    # Always return paid status for demo
    return jsonify({'status': 'paid'})

@payment_bp.route('/webhook', methods=['POST'])
def webhook():
    # Simulate successful webhook
    return jsonify({'code': '00', 'message': 'Success'}), 200

@payment_bp.route('/success')
def success():
    return render_template('payment/success.html')

@payment_bp.route('/cancel')
def cancel():
    return render_template('payment/cancel.html')