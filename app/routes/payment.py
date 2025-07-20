# routes/payment.py - Final Complete File with All Fixes
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models.models import db, Booking, Payment, PaymentConfig
from app.services.payos_service import PayOSService
from datetime import datetime, timedelta
import json
import os
import uuid
import time
from dotenv import load_dotenv
from app.utils.notification_service import notification_service

payment_bp = Blueprint('payment', __name__, url_prefix='/payment')

# Load environment variables
load_dotenv()

# Get the base URL for the application
APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:5000")

@payment_bp.route('/checkout/<int:booking_id>')
@login_required
def checkout(booking_id):
    """Hiển thị trang checkout với thông tin booking"""
    # Kiểm tra email verification cho Renter
    if current_user.is_renter() and not current_user.email_verified:
        flash('Vui lòng xác thực email trước khi thực hiện thanh toán', 'warning')
        return redirect(url_for('renter.verify_email'))
    
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

    # Calculate minimum date (30 days before booking start time)
    min_date = booking.start_time - timedelta(days=30)

    return render_template('payment/checkout.html', booking=booking, min_date=min_date)

@payment_bp.route('/modify-booking/<int:booking_id>', methods=['POST'])
@login_required
def modify_booking(booking_id):
    """Modify booking details before payment"""
    # Kiểm tra email verification cho Renter
    if current_user.is_renter() and not current_user.email_verified:
        flash('Vui lòng xác thực email trước khi thực hiện thanh toán', 'warning')
        return redirect(url_for('renter.verify_email'))
    
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
    
    try:
        booking_type = request.form.get('booking_type', 'daily')
        home = booking.home
        
        if booking_type == 'hourly':
            start_date = request.form.get('start_date_hourly')
            start_time = request.form.get('start_time')
            duration_str = request.form.get('duration_hourly')
            
            if not start_date or not start_time or not duration_str:
                flash("Bạn phải chọn ngày, giờ bắt đầu và số giờ thuê.", "warning")
                return redirect(url_for('payment.checkout', booking_id=booking_id))
            
            try:
                duration = int(duration_str)
            except ValueError:
                flash("Số giờ thuê không hợp lệ.", "danger")
                return redirect(url_for('payment.checkout', booking_id=booking_id))
            
            if duration < 2:
                flash("Số giờ thuê tối thiểu là 2.", "warning")
                return redirect(url_for('payment.checkout', booking_id=booking_id))
            
            # Calculate start and end time
            try:
                start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
            except ValueError:
                flash("Định dạng ngày/giờ không hợp lệ.", "danger")
                return redirect(url_for('payment.checkout', booking_id=booking_id))
            
            end_datetime = start_datetime + timedelta(hours=duration)
            
            # Calculate total price
            total_price = 0
            start_hour = start_datetime.hour
            end_hour = end_datetime.hour
            
            # Check for overnight/daytime pricing
            is_overnight = (start_hour >= 21 or start_hour <= 8) and home.price_overnight
            is_daytime = (start_hour >= 9 and start_hour <= 20) and home.price_daytime
            
            if is_overnight and duration >= 8:
                total_price = home.price_overnight
            elif is_daytime and duration >= 8:
                total_price = home.price_daytime
            elif duration <= 2 and home.price_first_2_hours:
                total_price = home.price_first_2_hours
            elif duration > 2 and home.price_first_2_hours and home.price_per_additional_hour:
                total_price = home.price_first_2_hours + (duration - 2) * home.price_per_additional_hour
            elif home.price_per_hour:
                total_price = duration * home.price_per_hour
            else:
                flash("Nhà này chưa có giá phù hợp với thời gian bạn chọn.", "warning")
                return redirect(url_for('payment.checkout', booking_id=booking_id))
            
        else:  # daily booking
            start_date = request.form.get('start_date')
            duration_str = request.form.get('duration_daily')
            
            if not start_date or not duration_str:
                flash("You must select date and duration.", "warning")
                return redirect(url_for('payment.checkout', booking_id=booking_id))
            
            try:
                duration = int(duration_str)
            except ValueError:
                flash("Invalid duration.", "danger")
                return redirect(url_for('payment.checkout', booking_id=booking_id))
            
            if duration < 1:
                flash("Minimum duration is 1 night.", "warning")
                return redirect(url_for('payment.checkout', booking_id=booking_id))
            
            # Check if home has price_per_night or price_per_day
            price = home.price_per_day if home.price_per_day and home.price_per_day > 0 else home.price_per_night
            if not price or price <= 0:
                flash("Nhà này chưa có thông tin giá. Vui lòng liên hệ chủ nhà để cập nhật giá trước khi đặt.", "warning")
                return redirect(url_for('payment.checkout', booking_id=booking_id))
            
            # For home bookings, check-in is typically at 3 PM
            start_str = f"{start_date} 15:00"
            try:
                start_datetime = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
            except ValueError:
                flash("Invalid date format.", "danger")
                return redirect(url_for('payment.checkout', booking_id=booking_id))
            
            end_datetime = start_datetime + timedelta(days=duration)
            total_price = price * duration
            duration = duration * 24  # Convert to hours for total_hours field
        
        # Check for overlapping bookings (excluding current booking)
        existing_bookings = Booking.query.filter(
            Booking.home_id == home.id,
            Booking.status.in_(['pending', 'confirmed', 'active']),
            Booking.id != booking.id
        ).all()
        
        for existing_booking in existing_bookings:
            if start_datetime < existing_booking.end_time and end_datetime > existing_booking.start_time:
                flash('This home is not available during the selected time period.', 'danger')
                return redirect(url_for('payment.checkout', booking_id=booking_id))
        
        # Update booking
        booking.start_time = start_datetime
        booking.end_time = end_datetime
        booking.total_hours = duration if booking_type == 'hourly' else duration
        booking.total_price = total_price
        booking.booking_type = booking_type
        
        db.session.commit()
        
        flash('Thông tin đặt phòng đã được cập nhật thành công!', 'success')
        return redirect(url_for('payment.checkout', booking_id=booking_id))
        
    except Exception as e:
        current_app.logger.error(f"[PAYMENT] Error modifying booking: {str(e)}")
        flash(f"Lỗi cập nhật thông tin đặt phòng: {str(e)}", 'danger')
        return redirect(url_for('payment.checkout', booking_id=booking_id))

@payment_bp.route('/process_payment', methods=['POST'])
@login_required
def process_payment():
    print('[DEBUG] Đã vào route /process_payment')
    current_app.logger.info(f'[PAYMENT] User {current_user.id} ({current_user.email}) bắt đầu tạo payment cho booking {request.form.get("booking_id")}.')
    
    # Kiểm tra email verification cho Renter
    if current_user.is_renter() and not current_user.email_verified:
        flash('Vui lòng xác thực email trước khi thực hiện thanh toán', 'warning')
        return redirect(url_for('renter.verify_email'))
    
    booking_id = request.form.get('booking_id')
    booking = Booking.query.get_or_404(booking_id)
    
    # Kiểm tra quyền
    if booking.renter_id != current_user.id:
        flash(f'Bạn không có quyền thực hiện thanh toán này.', 'danger')
        return redirect(url_for('renter.dashboard'))
    
    # Kiểm tra trạng thái booking
    if booking.payment_status == 'paid':
        flash('Đơn đặt phòng này đã được thanh toán.', 'info')
        return redirect(url_for('renter.booking_details', booking_id=booking_id))
    
    if booking.status == 'cancelled':
        flash('Đơn đặt nhà này đã bị hủy.', 'warning')
        return redirect(url_for('renter.dashboard'))
    
    try:
        # Kiểm tra payment pending
        existing_payment = Payment.query.filter_by(booking_id=booking.id, status='pending').first()
        if existing_payment and existing_payment.checkout_url:
            flash('Đã có giao dịch thanh toán đang chờ.', 'info')
            return redirect(url_for('payment.payment_status', payment_id=existing_payment.id))
        
        # Xóa payment cũ không có link
        if existing_payment and not existing_payment.checkout_url:
            db.session.delete(existing_payment)
            db.session.commit()
        
        # Lấy payment config
        payment_config = PaymentConfig.query.filter_by(owner_id=booking.home.owner_id).first()
        if not payment_config:
            flash('Chưa cấu hình thanh toán cho chủ nhà.', 'danger')
            return redirect(url_for('payment.checkout', booking_id=booking_id))
        
        # Tạo payment record với orderCode số nguyên
        order_code_int = int(f"{booking.id}{int(time.time() % 100000)}")
        
        # Tạo description ngắn gọn
        short_description = f"Booking #{booking.id}"
        
        payment = Payment(
            payment_code=f"PAY-{uuid.uuid4().hex[:8].upper()}",
            order_code=str(order_code_int),
            amount=booking.total_price,
            currency='VND',
            status='pending',
            description=short_description,
            customer_name=current_user.full_name,
            customer_email=current_user.email,
            customer_phone=current_user.phone,
            booking_id=booking.id,
            owner_id=booking.home.owner_id,
            renter_id=current_user.id
        )
        db.session.add(payment)
        db.session.commit()
        
        print(f'[DEBUG] Đã tạo payment: {payment.payment_code}, order_code: {payment.order_code}')
        current_app.logger.info(f'[PAYMENT] Đã tạo payment {payment.payment_code} cho booking {booking.id}, user {current_user.id}.')
        
        # Khởi tạo PayOS service
        payos_service = PayOSService(
            client_id=payment_config.payos_client_id,
            api_key=payment_config.payos_api_key,
            checksum_key=payment_config.payos_checksum_key
        )
        
        # Tạo payment link với orderCode số nguyên
        payment_link_result = payos_service.create_payment_link(
            order_code=order_code_int,
            amount=int(payment.amount),
            description=payment.description,
            return_url=url_for('payment.payment_success', payment_id=payment.id, _external=True),
            cancel_url=url_for('payment.payment_cancelled', payment_id=payment.id, _external=True),
            items=[{
                'name': f"Nha {booking.home.title}"[:25],
                'quantity': 1,
                'price': int(payment.amount)
            }]
        )
        
        print(f'[DEBUG] PayOS result: {payment_link_result}')
        
        if not payment_link_result.get('success'):
            error_msg = payment_link_result.get('message', 'Không thể tạo link thanh toán')
            current_app.logger.error(f'[PAYMENT] Không thể tạo link thanh toán cho payment {payment.payment_code}: {error_msg}')
            raise Exception(error_msg)
        
        # Lấy thông tin từ PayOS result
        checkout_url = payment_link_result.get('checkout_url') or payment_link_result.get('checkoutUrl')
        qr_code_data = payment_link_result.get('qrCode')
        account_number = payment_link_result.get('accountNumber')
        account_name = payment_link_result.get('accountName')
        bin_code = payment_link_result.get('bin')
        
        if not checkout_url:
            raise Exception('PayOS không trả về checkout URL')
        
        # Cập nhật payment với thông tin PayOS
        payment.checkout_url = checkout_url
        payment.payos_transaction_id = payment_link_result.get('paymentLinkId')
        
        # Lưu thông tin QR và ngân hàng vào JSON
        payos_data = {
            'qr_code': qr_code_data,
            'account_number': account_number,
            'account_name': account_name,
            'bin': bin_code,
            'bank_name': payos_service.get_bank_name_from_bin(bin_code) if bin_code else None,
            'order_code': payment_link_result.get('orderCode'),
            'amount': payment_link_result.get('amount'),
            'status': payment_link_result.get('status'),
            'currency': payment_link_result.get('currency', 'VND')
        }
        
        # Lưu vào field payos_signature
        if hasattr(payment, 'payos_signature'):
            payment.payos_signature = json.dumps(payos_data, ensure_ascii=False)
        
        db.session.commit()
        
        print(f'[DEBUG] Đã lưu checkout_url: {checkout_url}')
        print(f'[DEBUG] Đã lưu QR data: {qr_code_data is not None}')
        current_app.logger.info(f'[PAYMENT] Tạo link thanh toán thành công cho {payment.payment_code}: {checkout_url}')
        
        return redirect(url_for('payment.payment_status', payment_id=payment.id))
            
    except Exception as e:
        current_app.logger.error(f"[PAYMENT] Error processing payment: {str(e)}")
        flash(f"Lỗi xử lý thanh toán: {str(e)}", 'danger')
        return redirect(url_for('payment.checkout', booking_id=booking_id))

@payment_bp.route('/status/<int:payment_id>')
@login_required
def payment_status(payment_id):
    """Hiển thị trang trạng thái thanh toán với QR Code"""
    payment = Payment.query.get_or_404(payment_id)
    booking = payment.booking
    
    # Kiểm tra quyền
    if payment.renter_id != current_user.id:
        flash('Bạn không có quyền truy cập thông tin này.', 'danger')
        return redirect(url_for('renter.dashboard'))
    
    # Parse PayOS data từ JSON
    payos_data = {}
    if hasattr(payment, 'payos_signature') and payment.payos_signature:
        try:
            payos_data = json.loads(payment.payos_signature)
        except:
            payos_data = {}
    
    # Chuẩn bị dữ liệu cho template
    template_data = {
        'payment': payment,
        'booking': booking,
        'payos_data': payos_data,
        'qr_code': payos_data.get('qr_code'),
        'account_number': payos_data.get('account_number'),
        'account_name': payos_data.get('account_name'),
        'bank_name': payos_data.get('bank_name'),
        'formatted_amount': f"{payment.amount:,.0f} VND"
    }
    
    return render_template('payment/payment_status.html', **template_data)

@payment_bp.route('/success/<int:payment_id>')
@login_required
def payment_success(payment_id):
    """Trang thanh toán thành công"""
    payment = Payment.query.get_or_404(payment_id)
    booking = payment.booking
    
    # DEBUG: Log payment success
    print(f"DEBUG SUCCESS: Payment success page accessed for payment {payment_id}")
    print(f"DEBUG SUCCESS: Payment status: {payment.status}")
    print(f"DEBUG SUCCESS: Customer email: {payment.customer_email}")
    
    # Kiểm tra quyền
    if payment.renter_id != current_user.id:
        flash('Bạn không có quyền truy cập thông tin này.', 'danger')
        return redirect(url_for('renter.dashboard'))
    
    # Cập nhật trạng thái nếu chưa được cập nhật
    if payment.status == 'pending':
        print(f"DEBUG SUCCESS: Updating payment status to success...")
        payment.mark_as_successful()
        booking.payment_status = 'paid'
        booking.payment_date = datetime.utcnow()
        booking.payment_method = payment.payment_method or 'PayOS'
        booking.status = 'confirmed'
        db.session.commit()
        current_app.logger.info(f'[PAYMENT] Payment {payment.payment_code} thành công cho booking {booking.id}, user {current_user.id}.')
    
    # Gửi email nếu payment thành công và có email
    if payment.status in ['success', 'completed', 'paid'] and payment.customer_email:
        print(f"DEBUG SUCCESS: Attempting to send email...")
        
        try:
            # Gửi email xác nhận cho renter
            print(f"DEBUG SUCCESS: Calling send_payment_success_email...")
            email_result = notification_service.send_payment_success_email(payment)
            print(f"DEBUG SUCCESS: Email result: {email_result}")
            
            # Gửi thông báo cho owner
            print(f"DEBUG SUCCESS: Calling send_payment_success_notification_to_owner...")
            owner_result = notification_service.send_payment_success_notification_to_owner(payment)
            print(f"DEBUG SUCCESS: Owner notification result: {owner_result}")
            
            if email_result:
                print(f"DEBUG SUCCESS: Email sent successfully!")
                current_app.logger.info(f'[PAYMENT] Email confirmation sent for payment {payment.payment_code}')
            else:
                print(f"DEBUG SUCCESS: Email failed!")
                current_app.logger.error(f'[PAYMENT] Failed to send email for payment {payment.payment_code}')
                
        except Exception as e:
            print(f"DEBUG SUCCESS: Email exception: {str(e)}")
            import traceback
            traceback.print_exc()
            current_app.logger.error(f'[PAYMENT] Exception sending email for payment {payment.payment_code}: {str(e)}')
    else:
        print(f"DEBUG SUCCESS: Skipping email - Status: {payment.status}, Email: {payment.customer_email}")
    
    return render_template('payment/success.html', payment=payment, booking=booking)

@payment_bp.route('/failed/<int:payment_id>')
@login_required
def payment_failed(payment_id):
    """Trang thanh toán thất bại"""
    payment = Payment.query.get_or_404(payment_id)
    booking = payment.booking
    
    # Kiểm tra quyền
    if payment.renter_id != current_user.id:
        flash('Bạn không có quyền truy cập thông tin này.', 'danger')
        return redirect(url_for('renter.dashboard'))
    
    current_app.logger.warning(f'[PAYMENT] Payment {payment.payment_code} thất bại cho booking {booking.id}, user {current_user.id}.')
    return render_template('payment/failed.html', payment=payment, booking=booking)

@payment_bp.route('/cancelled/<int:payment_id>')
@login_required
def payment_cancelled(payment_id):
    """Trang thanh toán bị hủy"""
    payment = Payment.query.get_or_404(payment_id)
    booking = payment.booking
    
    # Kiểm tra quyền
    if payment.renter_id != current_user.id:
        flash('Bạn không có quyền truy cập thông tin này.', 'danger')
        return redirect(url_for('renter.dashboard'))
    
    # Đánh dấu payment bị hủy
    if payment.status == 'pending':
        payment.mark_as_cancelled('Người dùng hủy thanh toán')
        db.session.commit()
        current_app.logger.info(f'[PAYMENT] Payment {payment.payment_code} bị hủy bởi user {current_user.id}, booking {booking.id}.')
    
    flash('Thanh toán đã bị hủy.', 'warning')
    return redirect(url_for('renter.booking_details', booking_id=booking.id))

@payment_bp.route('/timeout/<int:payment_id>')
@login_required
def payment_timeout(payment_id):
    """Trang thanh toán hết hạn"""
    payment = Payment.query.get_or_404(payment_id)
    booking = payment.booking
    
    # Kiểm tra quyền
    if payment.renter_id != current_user.id:
        flash('Bạn không có quyền truy cập thông tin này.', 'danger')
        return redirect(url_for('renter.dashboard'))
    
    # Đánh dấu payment hết hạn
    if payment.status == 'pending':
        payment.mark_as_failed('Thanh toán hết hạn')
        db.session.commit()
        current_app.logger.warning(f'[PAYMENT] Payment {payment.payment_code} hết hạn cho booking {booking.id}, user {current_user.id}.')
    
    flash('Thời gian thanh toán đã hết hạn.', 'warning')
    return redirect(url_for('payment.payment_failed', payment_id=payment.id))

@payment_bp.route('/retry/<int:payment_id>')
@login_required
def retry_payment(payment_id):
    """Thử lại thanh toán"""
    payment = Payment.query.get_or_404(payment_id)
    booking = payment.booking
    
    # Kiểm tra quyền
    if payment.renter_id != current_user.id:
        flash('Bạn không có quyền thực hiện thao tác này.', 'danger')
        return redirect(url_for('renter.dashboard'))
    
    current_app.logger.info(f'[PAYMENT] User {current_user.id} retry payment cho booking {booking.id}, payment {payment.payment_code}.')
    # Chuyển hướng về trang checkout
    return redirect(url_for('payment.checkout', booking_id=booking.id))

@payment_bp.route('/cancel/<int:payment_id>')
@login_required
def cancel_payment(payment_id):
    """Hủy thanh toán"""
    payment = Payment.query.get_or_404(payment_id)
    booking = payment.booking
    
    # Kiểm tra quyền
    if payment.renter_id != current_user.id:
        flash('Bạn không có quyền thực hiện thao tác này.', 'danger')
        return redirect(url_for('renter.dashboard'))
    
    # Đánh dấu payment bị hủy
    if payment.status == 'pending':
        payment.mark_as_cancelled('Người dùng hủy thanh toán')
        db.session.commit()
    
    flash('Thanh toán đã được hủy.', 'info')
    return redirect(url_for('renter.booking_details', booking_id=booking.id))

@payment_bp.route('/check-status/<int:payment_id>')
@login_required
def check_payment_status(payment_id):
    """API kiểm tra trạng thái thanh toán"""
    payment = Payment.query.get_or_404(payment_id)
    
    # Kiểm tra quyền
    if payment.renter_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    # Parse PayOS data từ JSON
    payos_data = {}
    if hasattr(payment, 'payos_signature') and payment.payos_signature:
        try:
            payos_data = json.loads(payment.payos_signature)
        except:
            payos_data = {}
    
    return jsonify({
        'status': payment.status,
        'payment_code': payment.payment_code,
        'amount': payment.amount,
        'formatted_amount': f"{payment.amount:,.0f} VND",
        'created_at': payment.created_at.isoformat() if payment.created_at else None,
        'checkout_url': payment.checkout_url,
        'qr_code': payos_data.get('qr_code'),
        'account_info': {
            'account_number': payos_data.get('account_number'),
            'account_name': payos_data.get('account_name'),
            'bank_name': payos_data.get('bank_name')
        }
    })

@payment_bp.route('/refresh-status/<int:payment_id>')
@login_required
def refresh_payment_status(payment_id):
    """Refresh trạng thái thanh toán từ PayOS hoặc database"""
    payment = Payment.query.get_or_404(payment_id)
    
    # Kiểm tra quyền
    if payment.renter_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    # Trước tiên kiểm tra trạng thái trong database (có thể đã được webhook cập nhật)
    if payment.status == 'success':
        return jsonify({
            'status': 'success',
            'message': 'Payment completed successfully',
            'payment_status': payment.status,
            'redirect': url_for('payment.payment_success', payment_id=payment.id)
        })
    elif payment.status == 'failed':
        return jsonify({
            'status': 'failed',
            'message': 'Payment failed',
            'payment_status': payment.status,
            'redirect': url_for('payment.payment_failed', payment_id=payment.id)
        })
    elif payment.status == 'cancelled':
        return jsonify({
            'status': 'cancelled',
            'message': 'Payment cancelled',
            'payment_status': payment.status,
            'redirect': url_for('payment.payment_cancelled', payment_id=payment.id)
        })
    
    # Nếu vẫn pending, kiểm tra từ PayOS API
    try:
        # Lấy payment config để kiểm tra trạng thái từ PayOS
        payment_config = PaymentConfig.query.filter_by(owner_id=payment.owner_id).first()
        if not payment_config:
            return jsonify({'status': 'error', 'message': 'Payment config not found'})
        
        # Khởi tạo PayOS service
        payos_service = PayOSService(
            client_id=payment_config.payos_client_id,
            api_key=payment_config.payos_api_key,
            checksum_key=payment_config.payos_checksum_key
        )
        
        # Lấy thông tin từ PayOS
        order_code = int(payment.order_code)
        payment_info = payos_service.get_payment_info(order_code)
        
        if payment_info.get('success'):
            # PayOS SDK trả về object, dùng getattr
            data = payment_info.get('data')
            payos_status = getattr(data, 'status', '') if data else ''
            
            # Cập nhật trạng thái payment nếu có thay đổi
            if payos_service.is_payment_successful(payos_status) and payment.status == 'pending':
                payment.mark_as_successful()
                payment.booking.payment_status = 'paid'
                payment.booking.payment_date = datetime.utcnow()
                payment.booking.status = 'confirmed'
                db.session.commit()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Payment completed successfully',
                    'payment_status': payment.status,
                    'redirect': url_for('payment.payment_success', payment_id=payment.id)
                })
            elif payos_service.is_payment_failed(payos_status) and payment.status == 'pending':
                payment.mark_as_failed('Payment failed on PayOS')
                db.session.commit()
                
                return jsonify({
                    'status': 'failed',
                    'message': 'Payment failed',
                    'payment_status': payment.status,
                    'redirect': url_for('payment.payment_failed', payment_id=payment.id)
                })
            else:
                return jsonify({
                    'status': 'pending',
                    'message': 'Payment still pending',
                    'payment_status': payment.status
                })
        else:
            return jsonify({
                'status': 'pending',
                'message': 'Could not check payment status from PayOS, assuming pending',
                'payment_status': payment.status
            })
            
    except Exception as e:
        current_app.logger.error(f"[PAYMENT] Error refreshing payment status: {str(e)}")
        return jsonify({
            'status': 'pending',
            'message': f'Error checking status, assuming pending: {str(e)}',
            'payment_status': payment.status
        })

@payment_bp.route('/qr-data/<int:payment_id>')
@login_required
def get_qr_data(payment_id):
    """API trả về QR data để tạo QR code động"""
    payment = Payment.query.get_or_404(payment_id)
    
    # Kiểm tra quyền
    if payment.renter_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    # Parse PayOS data
    payos_data = {}
    if hasattr(payment, 'payos_signature') and payment.payos_signature:
        try:
            payos_data = json.loads(payment.payos_signature)
        except:
            payos_data = {}
    
    qr_code = payos_data.get('qr_code')
    if not qr_code:
        return jsonify({'status': 'error', 'message': 'QR code not available'})
    
    return jsonify({
        'status': 'success',
        'qr_data': qr_code,
        'payment_info': {
            'account_number': payos_data.get('account_number'),
            'account_name': payos_data.get('account_name'),
            'bank_name': payos_data.get('bank_name'),
            'amount': payment.amount,
            'formatted_amount': f"{payment.amount:,.0f} VND",
            'description': payment.description,
            'order_code': payment.order_code
        }
    })

@payment_bp.route('/get-qr/<int:payment_id>')
@login_required
def get_qr_direct(payment_id):
    """Lấy QR code trực tiếp từ PayOS API hoặc database"""
    payment = Payment.query.get_or_404(payment_id)
    
    # Kiểm tra quyền
    if payment.renter_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        print(f"[DEBUG] Getting QR for payment {payment_id}")
        
        # Trước tiên thử lấy từ database cache
        payos_data = {}
        if hasattr(payment, 'payos_signature') and payment.payos_signature:
            try:
                payos_data = json.loads(payment.payos_signature)
                print(f"[DEBUG] Found cached PayOS data: {payos_data.keys()}")
            except Exception as e:
                print(f"[DEBUG] Error parsing cached data: {e}")
        
        # Nếu có QR trong cache, dùng luôn
        if payos_data.get('qr_code'):
            print(f"[DEBUG] Using cached QR code")
            return jsonify({
                'success': True,
                'qr_code': payos_data.get('qr_code'),
                'account_number': payos_data.get('account_number'),
                'account_name': payos_data.get('account_name'),
                'bank_name': payos_data.get('bank_name', 'Ngân hàng TMCP Quân đội (MB Bank)'),
                'amount': payos_data.get('amount', payment.amount),
                'description': payos_data.get('description', payment.description),
                'status': payos_data.get('status', 'PENDING')
            })
        
        # Nếu không có cache, lấy từ PayOS API
        print(f"[DEBUG] No cached QR, fetching from PayOS API")
        
        # Lấy payment config
        payment_config = PaymentConfig.query.filter_by(owner_id=payment.owner_id).first()
        if not payment_config:
            return jsonify({'error': 'Payment config not found'})
        
        # Khởi tạo PayOS service
        payos_service = PayOSService(
            client_id=payment_config.payos_client_id,
            api_key=payment_config.payos_api_key,
            checksum_key=payment_config.payos_checksum_key
        )
        
        # Lấy thông tin từ PayOS
        order_code = int(payment.order_code)
        payment_info = payos_service.get_payment_info(order_code)
        
        print(f"[DEBUG] PayOS API result: {payment_info}")
        
        if payment_info.get('success'):
            data = payment_info.get('data')
            print(f"[DEBUG] PayOS data type: {type(data)}")
            
            # PayOS SDK trả về object - dùng getattr
            if data:
                qr_code = getattr(data, 'qrCode', None)
                account_number = getattr(data, 'accountNumber', None)
                account_name = getattr(data, 'accountName', None)
                amount = getattr(data, 'amount', None)
                description = getattr(data, 'description', None)
                status = getattr(data, 'status', None)
                
                bank_name = 'Ngân hàng TMCP Quân đội (MB Bank)'
                
                print(f"[DEBUG] Extracted QR: {qr_code is not None}, Account: {account_number}")
                
                return jsonify({
                    'success': True,
                    'qr_code': qr_code,
                    'account_number': account_number,
                    'account_name': account_name,
                    'bank_name': bank_name,
                    'amount': amount,
                    'description': description,
                    'status': status
                })
            else:
                return jsonify({'error': 'No payment data from PayOS'})
        else:
            error_msg = payment_info.get('message', 'Could not get payment info from PayOS')
            print(f"[DEBUG] PayOS error: {error_msg}")
            return jsonify({'error': error_msg})
            
    except Exception as e:
        current_app.logger.error(f"[QR] Error getting QR: {str(e)}")
        import traceback
        print(f"[DEBUG] Full exception: {traceback.format_exc()}")
        return jsonify({'error': str(e)})
