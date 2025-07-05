"""
Payment API Routes - Xử lý các API endpoints liên quan đến thanh toán
"""

from flask import Blueprint, request, jsonify, current_app, url_for
from flask_login import login_required, current_user
from app.models.models import Payment, PaymentConfig, Booking, Owner, Renter
from app.services.payos_service import PayOSService
from app.utils.payment_utils import create_payment_from_booking, update_booking_payment_status
from app.models.models import db
import uuid
from datetime import datetime

payment_api = Blueprint('payment_api', __name__)

@payment_api.route('/api/payment/create', methods=['POST'])
@login_required
def create_payment():
    """
    API tạo link thanh toán cho booking
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Dữ liệu không hợp lệ"}), 400
        
        booking_id = data.get('booking_id')
        return_url = data.get('return_url')
        cancel_url = data.get('cancel_url')
        
        if not booking_id:
            return jsonify({"error": "Thiếu booking_id"}), 400
        
        # Kiểm tra booking
        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({"error": "Booking không tồn tại"}), 404
        
        # Kiểm tra quyền truy cập
        if current_user.is_renter() and booking.renter_id != current_user.id:
            return jsonify({"error": "Không có quyền truy cập booking này"}), 403
        
        # Lấy cấu hình PayOS của owner
        owner_config = PaymentConfig.query.filter_by(
            owner_id=booking.home.owner_id, 
            is_active=True
        ).first()
        
        if not owner_config:
            return jsonify({
                "error": "Chủ nhà chưa cấu hình PayOS. Vui lòng liên hệ admin."
            }), 400
        
        # Tạo PayOS service
        payos = PayOSService(
            owner_config.payos_client_id,
            owner_config.payos_api_key,
            owner_config.payos_checksum_key
        )
        
        # Tạo payment record trong database
        payment = create_payment_from_booking(booking)
        db.session.add(payment)
        db.session.commit()
        
        # Tạo items cho PayOS
        items = payos.create_payment_items(booking)
        
        # Tạo link thanh toán
        payment_response = payos.create_payment_link(
            order_code=payment.order_code,
            amount=payos.format_amount(booking.total_price),
            description=f"Thanh toán booking #{booking.id} - {booking.home.title}",
            return_url=return_url or url_for('payment.success', payment_id=payment.id, _external=True),
            cancel_url=cancel_url or url_for('payment.cancel', payment_id=payment.id, _external=True),
            items=items
        )
        
        if payment_response.get('error'):
            # Xóa payment record nếu tạo link thất bại
            db.session.delete(payment)
            db.session.commit()
            return jsonify({
                "error": "Không thể tạo link thanh toán",
                "details": payment_response.get('message', 'Lỗi không xác định')
            }), 500
        
        # Cập nhật payment record với thông tin từ PayOS
        payment.payos_transaction_id = payment_response.get('data', {}).get('paymentLinkId')
        payment.payos_signature = payment_response.get('data', {}).get('signature')
        db.session.commit()
        
        return jsonify({
            "success": True,
            "payment_id": payment.id,
            "payment_code": payment.payment_code,
            "order_code": payment.order_code,
            "amount": payment.amount,
            "payment_url": payment_response.get('checkout_url') or payment_response.get('checkoutUrl'),
            "qr_code": payment_response.get('qr_code') or payment_response.get('qrCode'),
            "expires_at": payment_response.get('expires_at') or payment_response.get('expiresAt')
        })
        
    except Exception as e:
        current_app.logger.error(f"Lỗi khi tạo payment: {str(e)}")
        return jsonify({"error": "Lỗi server"}), 500

@payment_api.route('/api/payment/<int:payment_id>/status', methods=['GET'])
@login_required
def get_payment_status(payment_id):
    """
    API lấy trạng thái payment
    """
    try:
        payment = Payment.query.get(payment_id)
        if not payment:
            return jsonify({"error": "Payment không tồn tại"}), 404
        
        # Kiểm tra quyền truy cập
        if current_user.is_renter() and payment.renter_id != current_user.id:
            return jsonify({"error": "Không có quyền truy cập"}), 403
        
        if current_user.is_owner() and payment.owner_id != current_user.id:
            return jsonify({"error": "Không có quyền truy cập"}), 403
        
        return jsonify({
            "payment_id": payment.id,
            "payment_code": payment.payment_code,
            "order_code": payment.order_code,
            "amount": payment.amount,
            "status": payment.status,
            "status_text": payment.get_payment_status_text(payment.status),
            "payment_method": payment.payment_method,
            "created_at": payment.created_at.isoformat() if payment.created_at else None,
            "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
            "description": payment.description
        })
        
    except Exception as e:
        current_app.logger.error(f"Lỗi khi lấy payment status: {str(e)}")
        return jsonify({"error": "Lỗi server"}), 500

@payment_api.route('/api/payment/webhook', methods=['POST'])
def payos_webhook():
    """
    Webhook endpoint nhận callback từ PayOS
    """
    try:
        # Lấy dữ liệu từ webhook
        data = request.get_json()
        if not data:
            current_app.logger.error("Webhook: Không có dữ liệu")
            return jsonify({"error": "Không có dữ liệu"}), 400
        
        # Lấy chữ ký từ header
        received_signature = request.headers.get('x-signature', '')
        if not received_signature:
            current_app.logger.error("Webhook: Không có chữ ký")
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
        
        if payos.is_payment_successful(payos_status):
            # Thanh toán thành công
            payment.mark_as_successful(
                payos_transaction_id=trans_id,
                payment_method=data.get('paymentMethod', 'unknown')
            )
            update_booking_payment_status(payment.booking_id, 'success')
            
        elif payos.is_payment_failed(payos_status):
            # Thanh toán thất bại
            payment.mark_as_failed(f"PayOS status: {payos_status}")
            update_booking_payment_status(payment.booking_id, 'failed')
        
        db.session.commit()
        
        current_app.logger.info(f"Webhook processed successfully for order_code {order_code}, status: {payos_status}")
        
        return jsonify({
            "success": True,
            "message": "Webhook processed successfully",
            "order_code": order_code,
            "status": payos_status
        })
        
    except Exception as e:
        current_app.logger.error(f"Lỗi khi xử lý webhook: {str(e)}")
        return jsonify({"error": "Lỗi server"}), 500

@payment_api.route('/api/payment/<int:payment_id>/cancel', methods=['POST'])
@login_required
def cancel_payment(payment_id):
    """
    API hủy payment
    """
    try:
        payment = Payment.query.get(payment_id)
        if not payment:
            return jsonify({"error": "Payment không tồn tại"}), 404
        
        # Kiểm tra quyền truy cập
        if current_user.is_renter() and payment.renter_id != current_user.id:
            return jsonify({"error": "Không có quyền truy cập"}), 403
        
        if current_user.is_owner() and payment.owner_id != current_user.id:
            return jsonify({"error": "Không có quyền truy cập"}), 403
        
        # Chỉ cho phép hủy payment đang pending
        if payment.status != 'pending':
            return jsonify({"error": "Chỉ có thể hủy payment đang chờ thanh toán"}), 400
        
        # Lấy cấu hình PayOS
        owner_config = PaymentConfig.query.filter_by(
            owner_id=payment.owner_id, 
            is_active=True
        ).first()
        
        if not owner_config:
            return jsonify({"error": "Cấu hình PayOS không tồn tại"}), 400
        
        # Hủy payment trên PayOS nếu có transaction_id
        if payment.payos_transaction_id:
            payos = PayOSService(
                owner_config.payos_client_id,
                owner_config.payos_api_key,
                owner_config.payos_checksum_key
            )
            
            cancel_response = payos.cancel_payment(
                payment.payos_transaction_id,
                "Hủy bởi người dùng"
            )
            
            if cancel_response.get('error'):
                current_app.logger.warning(f"Không thể hủy payment trên PayOS: {cancel_response.get('message')}")
        
        # Cập nhật trạng thái payment
        payment.mark_as_cancelled("Hủy bởi người dùng")
        update_booking_payment_status(payment.booking_id, 'cancelled')
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Payment đã được hủy thành công",
            "payment_id": payment.id,
            "status": payment.status
        })
        
    except Exception as e:
        current_app.logger.error(f"Lỗi khi hủy payment: {str(e)}")
        return jsonify({"error": "Lỗi server"}), 500

@payment_api.route('/api/payment/list', methods=['GET'])
@login_required
def list_payments():
    """
    API lấy danh sách payment của user
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        
        # Xây dựng query
        if current_user.is_renter():
            query = Payment.query.filter_by(renter_id=current_user.id)
        elif current_user.is_owner():
            query = Payment.query.filter_by(owner_id=current_user.id)
        else:
            return jsonify({"error": "Không có quyền truy cập"}), 403
        
        # Lọc theo status nếu có
        if status:
            query = query.filter_by(status=status)
        
        # Sắp xếp theo thời gian tạo mới nhất
        query = query.order_by(Payment.created_at.desc())
        
        # Phân trang
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        payments = []
        for payment in pagination.items:
            payments.append({
                "id": payment.id,
                "payment_code": payment.payment_code,
                "order_code": payment.order_code,
                "amount": payment.amount,
                "status": payment.status,
                "status_text": payment.get_payment_status_text(payment.status),
                "payment_method": payment.payment_method,
                "created_at": payment.created_at.isoformat() if payment.created_at else None,
                "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
                "description": payment.description,
                "booking_id": payment.booking_id
            })
        
        return jsonify({
            "payments": payments,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Lỗi khi lấy danh sách payment: {str(e)}")
        return jsonify({"error": "Lỗi server"}), 500 