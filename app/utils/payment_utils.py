"""
Utility functions cho việc xử lý payment
"""

import uuid
import hashlib
import hmac
import json
from datetime import datetime
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet, InvalidToken
import os

def generate_payment_code() -> str:
    """Tạo mã giao dịch ngẫu nhiên"""
    return f"PAY{uuid.uuid4().hex[:8].upper()}"

def generate_order_code() -> str:
    """Tạo mã đơn hàng ngẫu nhiên"""
    return f"ORD{uuid.uuid4().hex[:8].upper()}"

def create_payment_from_booking(booking, payment_method = None):
    from app.models.models import Payment
    payment = Payment(
        payment_code=generate_payment_code(),
        order_code=generate_order_code(),
        amount=booking.total_price,
        currency='VND',
        status='pending',
        payment_method=payment_method,
        description=f"Thanh toán cho booking nhà {booking.home.title}",
        customer_name=booking.renter.full_name,
        customer_email=booking.renter.email,
        customer_phone=booking.renter.phone,
        booking_id=booking.id,
        owner_id=booking.home.owner_id,
        renter_id=booking.renter_id
    )
    return payment

def get_payment_config_for_owner(owner_id):
    from app.models.models import PaymentConfig
    return PaymentConfig.query.filter_by(owner_id=owner_id, is_active=True).first()

def validate_payos_signature(data: Dict[str, Any], checksum_key: str) -> bool:
    """
    Xác thực chữ ký từ PayOS
    
    Args:
        data: Dữ liệu từ PayOS
        checksum_key: Checksum key từ cấu hình
    
    Returns:
        True nếu chữ ký hợp lệ, False nếu không
    """
    try:
        # Tạo chữ ký từ dữ liệu
        signature_data = f"{data.get('code', '')}{data.get('amount', '')}{data.get('cancelUrl', '')}{data.get('description', '')}{data.get('orderCode', '')}{data.get('returnUrl', '')}{data.get('status', '')}{data.get('transId', '')}"
        
        # Tạo HMAC SHA256
        expected_signature = hmac.new(
            checksum_key.encode('utf-8'),
            signature_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # So sánh với chữ ký nhận được
        received_signature = data.get('signature', '')
        return expected_signature == received_signature
        
    except Exception as e:
        print(f"Lỗi khi xác thực chữ ký: {e}")
        return False

def format_payment_amount(amount: float) -> str:
    """
    Format số tiền thanh toán
    
    Args:
        amount: Số tiền
    
    Returns:
        String đã format
    """
    return f"{amount:,.0f} VND"

def get_payment_status_text(status: str) -> str:
    """
    Chuyển đổi status code thành text
    
    Args:
        status: Status code
    
    Returns:
        Status text
    """
    status_map = {
        'pending': 'Chờ thanh toán',
        'success': 'Thành công',
        'failed': 'Thất bại',
        'cancelled': 'Đã hủy'
    }
    return status_map.get(status, status)

def get_payment_method_text(method: str) -> str:
    """
    Chuyển đổi payment method code thành text
    
    Args:
        method: Method code
    
    Returns:
        Method text
    """
    method_map = {
        'bank_transfer': 'Chuyển khoản ngân hàng',
        'e_wallet': 'Ví điện tử',
        'credit_card': 'Thẻ tín dụng',
        'cash': 'Tiền mặt'
    }
    return method_map.get(method, method)

def calculate_payment_statistics(owner_id = None):
    from app.models.models import Payment, db
    query = Payment.query
    if owner_id:
        query = query.filter_by(owner_id=owner_id)
    total_payments = query.count()
    successful_payments = query.filter_by(status='success').count()
    pending_payments = query.filter_by(status='pending').count()
    failed_payments = query.filter_by(status='failed').count()
    total_amount = db.session.query(db.func.sum(Payment.amount)).filter_by(status='success').scalar() or 0
    if owner_id:
        total_amount = db.session.query(db.func.sum(Payment.amount)).filter_by(
            status='success', owner_id=owner_id
        ).scalar() or 0
    return {
        'total_payments': total_payments,
        'successful_payments': successful_payments,
        'pending_payments': pending_payments,
        'failed_payments': failed_payments,
        'total_amount': total_amount,
        'success_rate': (successful_payments / total_payments * 100) if total_payments > 0 else 0
    }

def get_recent_payments(limit = 10, owner_id = None):
    from app.models.models import Payment
    query = Payment.query.order_by(Payment.created_at.desc())
    if owner_id:
        query = query.filter_by(owner_id=owner_id)
    return query.limit(limit).all()

def update_booking_payment_status(booking_id, payment_status):
    """
    Cập nhật trạng thái thanh toán cho booking
    Args:
        booking_id: ID của booking
        payment_status: Trạng thái thanh toán
    Returns:
        True nếu cập nhật thành công
    """
    try:
        from app.models.models import Booking
        booking = Booking.query.get(booking_id)
        if booking:
            booking.payment_status = payment_status
            if payment_status == 'success':
                booking.payment_date = datetime.utcnow()
            from app.models.models import db
            db.session.commit()
            return True
        return False
    except Exception as e:
        print(f"Lỗi khi cập nhật booking payment status: {e}")
        return False

def create_payos_payment_data(payment, payment_config, return_url: str, cancel_url: str):
    """
    Tạo dữ liệu để gửi đến PayOS
    
    Args:
        payment: Payment object
        payment_config: PaymentConfig object
        return_url: URL callback khi thanh toán thành công
        cancel_url: URL callback khi hủy thanh toán
    
    Returns:
        Dictionary chứa dữ liệu cho PayOS
    """
    
    # Tạo dữ liệu cơ bản
    payment_data = {
        'orderCode': payment.order_code,
        'amount': int(payment.amount),  # PayOS yêu cầu số nguyên
        'description': payment.description or f"Thanh toán cho {payment.order_code}",
        'cancelUrl': cancel_url,
        'returnUrl': return_url,
        'signature': '',  # Sẽ được tính toán sau
        'items': [
            {
                'name': f"Booking {payment.booking_id}",
                'quantity': 1,
                'price': int(payment.amount)
            }
        ]
    }
    
    # Tạo chữ ký
    signature_data = f"{payment_data['orderCode']}{payment_data['amount']}{payment_data['cancelUrl']}{payment_data['description']}{payment_data['returnUrl']}"
    signature = hmac.new(
        payment_config.payos_checksum_key.encode('utf-8'),
        signature_data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    payment_data['signature'] = signature
    
    return payment_data

def encrypt_api_key(api_key: str) -> str:
    FERNET_SECRET_KEY = os.environ.get('FERNET_SECRET_KEY', None)
    if not FERNET_SECRET_KEY:
        print('[ENCRYPT] FERNET_SECRET_KEY chưa được cấu hình!')
        raise Exception('Fernet secret key chưa được cấu hình!')
    try:
        fernet = Fernet(FERNET_SECRET_KEY.encode())
    except Exception as e:
        print(f'[ENCRYPT] Lỗi khi khởi tạo Fernet: {e}')
        raise
    return fernet.encrypt(api_key.encode()).decode()

def decrypt_api_key(encrypted_api_key: str) -> str:
    FERNET_SECRET_KEY = os.environ.get('FERNET_SECRET_KEY', None)
    if not FERNET_SECRET_KEY:
        print('[DECRYPT] FERNET_SECRET_KEY chưa được cấu hình!')
        raise Exception('Fernet secret key chưa được cấu hình!')
    try:
        fernet = Fernet(FERNET_SECRET_KEY.encode())
    except Exception as e:
        print(f'[DECRYPT] Lỗi khi khởi tạo Fernet: {e}')
        raise
    try:
        return fernet.decrypt(encrypted_api_key.encode()).decode()
    except InvalidToken:
        print('[DECRYPT] Giải mã API key thất bại!')
        raise Exception('Giải mã API key thất bại!') 