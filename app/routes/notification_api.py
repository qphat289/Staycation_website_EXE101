"""
Notification API - Xử lý thông báo real-time
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models.models import Payment, Booking, db
from app.utils.notification_service import notification_service
import logging
from datetime import datetime, timedelta

notification_api = Blueprint('notification_api', __name__)

@notification_api.route('/api/notifications/payment-success/<int:payment_id>', methods=['GET'])
@login_required
def get_payment_notification(payment_id):
    """
    Lấy thông báo thanh toán thành công
    """
    try:
        payment = Payment.query.get_or_404(payment_id)
        
        # Kiểm tra quyền truy cập
        if payment.renter_id != current_user.id and payment.owner_id != current_user.id:
            return jsonify({"error": "Không có quyền truy cập"}), 403
        
        # Tạo notification data
        notification_data = {
            'type': 'payment_success',
            'payment_id': payment.id,
            'booking_id': payment.booking_id,
            'amount': payment.amount,
            'payment_code': payment.payment_code,
            'status': payment.status,
            'timestamp': payment.paid_at.isoformat() if payment.paid_at else datetime.utcnow().isoformat(),
            'message': f'Thanh toán thành công: {payment.payment_code} - {payment.amount:,.0f} VND'
        }
        
        return jsonify({
            'success': True,
            'notification': notification_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Lỗi khi lấy thông báo payment: {str(e)}")
        return jsonify({"error": "Lỗi server"}), 500

@notification_api.route('/api/notifications/user/<int:user_id>', methods=['GET'])
@login_required
def get_user_notifications(user_id):
    """
    Lấy tất cả thông báo của user
    """
    try:
        # Kiểm tra quyền truy cập
        if current_user.id != user_id:
            return jsonify({"error": "Không có quyền truy cập"}), 403
        
        # Lấy các payment gần đây của user
        recent_payments = Payment.query.filter_by(
            renter_id=user_id if current_user.is_renter() else user_id
        ).filter(
            Payment.status == 'success',
            Payment.paid_at >= datetime.utcnow() - timedelta(days=7)
        ).order_by(Payment.paid_at.desc()).limit(10).all()
        
        notifications = []
        for payment in recent_payments:
            notification_data = {
                'type': 'payment_success',
                'payment_id': payment.id,
                'booking_id': payment.booking_id,
                'amount': payment.amount,
                'payment_code': payment.payment_code,
                'status': payment.status,
                'timestamp': payment.paid_at.isoformat() if payment.paid_at else None,
                'message': f'Thanh toán thành công: {payment.payment_code} - {payment.amount:,.0f} VND',
                'booking_info': {
                    'room_title': payment.booking.home.title if payment.booking else None,
                    'start_time': payment.booking.start_time.isoformat() if payment.booking else None,
                    'end_time': payment.booking.end_time.isoformat() if payment.booking else None
                }
            }
            notifications.append(notification_data)
        
        return jsonify({
            'success': True,
            'notifications': notifications,
            'count': len(notifications)
        })
        
    except Exception as e:
        current_app.logger.error(f"Lỗi khi lấy thông báo user: {str(e)}")
        return jsonify({"error": "Lỗi server"}), 500

@notification_api.route('/api/notifications/owner/<int:owner_id>', methods=['GET'])
@login_required
def get_owner_notifications(owner_id):
    """
    Lấy thông báo cho owner
    """
    try:
        # Kiểm tra quyền truy cập
        if not current_user.is_owner() or current_user.id != owner_id:
            return jsonify({"error": "Không có quyền truy cập"}), 403
        
        # Lấy các payment gần đây của owner
        recent_payments = Payment.query.filter_by(
            owner_id=owner_id
        ).filter(
            Payment.status == 'success',
            Payment.paid_at >= datetime.utcnow() - timedelta(days=7)
        ).order_by(Payment.paid_at.desc()).limit(10).all()
        
        notifications = []
        for payment in recent_payments:
            notification_data = {
                'type': 'payment_success',
                'payment_id': payment.id,
                'booking_id': payment.booking_id,
                'amount': payment.amount,
                'payment_code': payment.payment_code,
                'status': payment.status,
                'timestamp': payment.paid_at.isoformat() if payment.paid_at else None,
                'message': f'Thanh toán thành công: {payment.payment_code} - {payment.amount:,.0f} VND',
                'customer_info': {
                    'name': payment.customer_name,
                    'email': payment.customer_email,
                    'phone': payment.customer_phone
                },
                'booking_info': {
                    'room_title': payment.booking.home.title if payment.booking else None,
                    'start_time': payment.booking.start_time.isoformat() if payment.booking else None,
                    'end_time': payment.booking.end_time.isoformat() if payment.booking else None
                }
            }
            notifications.append(notification_data)
        
        return jsonify({
            'success': True,
            'notifications': notifications,
            'count': len(notifications)
        })
        
    except Exception as e:
        current_app.logger.error(f"Lỗi khi lấy thông báo owner: {str(e)}")
        return jsonify({"error": "Lỗi server"}), 500

@notification_api.route('/api/notifications/check-new', methods=['POST'])
@login_required
def check_new_notifications():
    """
    Kiểm tra thông báo mới
    """
    try:
        data = request.get_json()
        last_check_time = data.get('last_check_time')
        
        if last_check_time:
            last_check = datetime.fromisoformat(last_check_time.replace('Z', '+00:00'))
        else:
            last_check = datetime.utcnow() - timedelta(hours=1)
        
        # Tìm payments mới
        new_payments = Payment.query.filter(
            Payment.paid_at >= last_check,
            Payment.status == 'success'
        )
        
        # Lọc theo user type
        if current_user.is_renter():
            new_payments = new_payments.filter(Payment.renter_id == current_user.id)
        elif current_user.is_owner():
            new_payments = new_payments.filter(Payment.owner_id == current_user.id)
        
        new_payments = new_payments.order_by(Payment.paid_at.desc()).all()
        
        notifications = []
        for payment in new_payments:
            notification_data = {
                'type': 'payment_success',
                'payment_id': payment.id,
                'booking_id': payment.booking_id,
                'amount': payment.amount,
                'payment_code': payment.payment_code,
                'timestamp': payment.paid_at.isoformat() if payment.paid_at else None,
                'message': f'Thanh toán thành công: {payment.payment_code} - {payment.amount:,.0f} VND'
            }
            notifications.append(notification_data)
        
        return jsonify({
            'success': True,
            'has_new': len(notifications) > 0,
            'notifications': notifications,
            'count': len(notifications)
        })
        
    except Exception as e:
        current_app.logger.error(f"Lỗi khi kiểm tra thông báo mới: {str(e)}")
        return jsonify({"error": "Lỗi server"}), 500

@notification_api.route('/api/notifications/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """
    Đánh dấu thông báo đã đọc
    """
    try:
        # Trong thực tế, bạn có thể có bảng Notification riêng
        # Ở đây chúng ta chỉ trả về success
        return jsonify({
            'success': True,
            'message': 'Thông báo đã được đánh dấu đã đọc'
        })
        
    except Exception as e:
        current_app.logger.error(f"Lỗi khi đánh dấu thông báo đã đọc: {str(e)}")
        return jsonify({"error": "Lỗi server"}), 500 