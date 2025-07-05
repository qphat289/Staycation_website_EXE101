"""
Webhook Handler - Xử lý các webhook từ bên ngoài (PayOS, etc.)
"""

from flask import Blueprint, request, jsonify, current_app
from app.models.models import Payment, PaymentConfig, Booking
from app.services.payos_service import PayOSService
from app.utils.payment_utils import update_booking_payment_status
from app.utils.notification_service import notification_service
from app.models.models import db
import logging

webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/webhook/payos', methods=['POST'])
def payos_webhook():
    """
    Webhook endpoint nhận callback từ PayOS
    Không cần authentication vì đây là callback từ bên ngoài
    """
    try:
        # Log webhook request
        current_app.logger.info("Received PayOS webhook")
        
        # Lấy dữ liệu từ webhook
        data = request.get_json()
        if not data:
            current_app.logger.error("Webhook: Không có dữ liệu JSON")
            return jsonify({"error": "Không có dữ liệu"}), 400
        
        # Log dữ liệu webhook (che giấu thông tin nhạy cảm)
        log_data = data.copy()
        if 'signature' in log_data:
            log_data['signature'] = '***'
        current_app.logger.info(f"Webhook data: {log_data}")
        
        # Lấy chữ ký từ header
        received_signature = request.headers.get('x-signature', '')
        if not received_signature:
            current_app.logger.error("Webhook: Không có chữ ký trong header")
            return jsonify({"error": "Không có chữ ký"}), 400
        
        # Lấy order_code từ dữ liệu
        order_code = data.get('orderCode')
        if not order_code:
            current_app.logger.error("Webhook: Không có orderCode")
            return jsonify({"error": "Không có orderCode"}), 400
        
        # Tìm payment record
        payment = Payment.query.filter_by(order_code=order_code).first()
        if not payment:
            current_app.logger.error(f"Webhook: Không tìm thấy payment với order_code {order_code}")
            return jsonify({"error": "Payment không tồn tại"}), 404
        
        # Lấy cấu hình PayOS
        owner_config = PaymentConfig.query.filter_by(
            owner_id=payment.owner_id, 
            is_active=True
        ).first()
        
        if not owner_config:
            current_app.logger.error(f"Webhook: Không tìm thấy config cho owner {payment.owner_id}")
            return jsonify({"error": "Cấu hình PayOS không tồn tại"}), 400
        
        # Tạo PayOS service và xác thực chữ ký
        payos = PayOSService(
            owner_config.payos_client_id,
            owner_config.payos_api_key,
            owner_config.payos_checksum_key
        )
        
        if not payos.verify_webhook_signature(data, received_signature):
            current_app.logger.error(f"Webhook: Chữ ký không hợp lệ cho order_code {order_code}")
            return jsonify({"error": "Chữ ký không hợp lệ"}), 400
        
        # Xử lý trạng thái payment
        payos_status = data.get('status', '').lower()
        trans_id = data.get('transId')
        payment_method = data.get('paymentMethod', 'unknown')
        
        current_app.logger.info(f"Processing payment {order_code} with status: {payos_status}")
        
        if payos.is_payment_successful(payos_status):
            # Thanh toán thành công
            payment.mark_as_successful(
                payos_transaction_id=trans_id,
                payment_method=payment_method
            )
            update_booking_payment_status(payment.booking_id, 'success')
            current_app.logger.info(f"Payment {order_code} marked as successful")
            
            # Gửi thông báo và email
            try:
                # Gửi email xác nhận cho renter
                notification_service.send_payment_success_email(payment)
                
                # Gửi thông báo cho owner
                notification_service.send_payment_success_notification_to_owner(payment)
                
                # Tạo web notification
                notification_service.create_web_notification(payment)
                
                current_app.logger.info(f"Notifications sent successfully for payment {order_code}")
            except Exception as e:
                current_app.logger.error(f"Error sending notifications for payment {order_code}: {str(e)}")
            
        elif payos.is_payment_failed(payos_status):
            # Thanh toán thất bại
            payment.mark_as_failed(f"PayOS status: {payos_status}")
            update_booking_payment_status(payment.booking_id, 'failed')
            current_app.logger.info(f"Payment {order_code} marked as failed")
        
        else:
            # Trạng thái khác (pending, etc.)
            payment.status = payos_status
            payment.updated_at = db.func.now()
            current_app.logger.info(f"Payment {order_code} status updated to: {payos_status}")
        
        db.session.commit()
        
        current_app.logger.info(f"Webhook processed successfully for order_code {order_code}")
        
        return jsonify({
            "success": True,
            "message": "Webhook processed successfully",
            "order_code": order_code,
            "status": payos_status
        })
        
    except Exception as e:
        current_app.logger.error(f"Lỗi khi xử lý webhook: {str(e)}")
        return jsonify({"error": "Lỗi server"}), 500

@webhook_bp.route('/webhook/test', methods=['POST'])
def test_webhook():
    """
    Webhook test endpoint để kiểm tra webhook có hoạt động không
    """
    try:
        data = request.get_json()
        current_app.logger.info(f"Test webhook received: {data}")
        
        return jsonify({
            "success": True,
            "message": "Test webhook received successfully",
            "data": data
        })
        
    except Exception as e:
        current_app.logger.error(f"Lỗi khi xử lý test webhook: {str(e)}")
        return jsonify({"error": "Lỗi server"}), 500

@webhook_bp.route('/webhook/health', methods=['GET'])
def webhook_health():
    """
    Health check endpoint cho webhook
    """
    return jsonify({
        "status": "healthy",
        "message": "Webhook service is running",
        "timestamp": db.func.now()
    }) 