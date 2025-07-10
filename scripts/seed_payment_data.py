#!/usr/bin/env python3
"""
Script để tạo dữ liệu mẫu cho payment và payment_config
"""

import sys
import os
import uuid
from datetime import datetime, timedelta

# Thêm thư mục gốc vào Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import trực tiếp từ file app.py
import importlib.util
spec = importlib.util.spec_from_file_location("app_module", "app.py")
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

app = app_module.app
db = app_module.db
from app.models.models import Payment, PaymentConfig, Owner, Renter, Booking, Home

def generate_payment_code():
    """Tạo mã giao dịch ngẫu nhiên"""
    return f"PAY{uuid.uuid4().hex[:8].upper()}"

def generate_order_code():
    """Tạo mã đơn hàng ngẫu nhiên"""
    return f"ORD{uuid.uuid4().hex[:8].upper()}"

def create_sample_payment_configs():
    """Tạo cấu hình PayOS mẫu cho các owner"""
    
    with app.app_context():
        try:
            # Lấy tất cả owner
            owners = Owner.query.all()
            
            if not owners:
                print(" Không có owner nào trong database!")
                return False
            
            created_count = 0
            
            for owner in owners:
                # Kiểm tra xem owner đã có payment_config chưa
                existing_config = PaymentConfig.query.filter_by(owner_id=owner.id).first()
                
                if existing_config:
                    print(f"  Owner {owner.username} đã có payment_config")
                    continue
                
                # Tạo payment_config mẫu
                payment_config = PaymentConfig(
                    owner_id=owner.id,
                    payos_client_id=f"client_{owner.id}_{uuid.uuid4().hex[:8]}",
                    payos_api_key=f"api_key_{owner.id}_{uuid.uuid4().hex[:16]}",
                    payos_checksum_key=f"checksum_{owner.id}_{uuid.uuid4().hex[:16]}",
                    is_active=True
                )
                
                db.session.add(payment_config)
                created_count += 1
                print(f" Đã tạo payment_config cho owner {owner.username}")
            
            db.session.commit()
            print(f" Đã tạo {created_count} payment_config mẫu!")
            return True
            
        except Exception as e:
            print(f" Lỗi khi tạo payment_config: {e}")
            db.session.rollback()
            return False

def create_sample_payments():
    """Tạo giao dịch thanh toán mẫu"""
    
    with app.app_context():
        try:
            # Lấy các booking có sẵn
            bookings = Booking.query.all()
            
            if not bookings:
                print(" Không có booking nào trong database!")
                return False
            
            created_count = 0
            
            for booking in bookings:
                # Kiểm tra xem booking đã có payment chưa
                existing_payment = Payment.query.filter_by(booking_id=booking.id).first()
                
                if existing_payment:
                    print(f"  Booking {booking.id} đã có payment")
                    continue
                
                # Tạo payment mẫu
                payment = Payment(
                    payment_code=generate_payment_code(),
                    order_code=generate_order_code(),
                    amount=booking.total_price,
                    currency='VND',
                    status='success',  # Mặc định thành công
                    payment_method='bank_transfer',
                    created_at=booking.created_at,
                    paid_at=booking.created_at + timedelta(minutes=5),  # Thanh toán sau 5 phút
                    description=f"Thanh toán cho booking nhà {booking.home.title}",
                    customer_name=booking.renter.full_name,
                    customer_email=booking.renter.email,
                    customer_phone=booking.renter.phone,
                    booking_id=booking.id,
                    owner_id=booking.home.owner_id,
                    renter_id=booking.renter_id
                )
                
                db.session.add(payment)
                created_count += 1
                print(f" Đã tạo payment cho booking {booking.id}")
            
            db.session.commit()
            print(f" Đã tạo {created_count} payment mẫu!")
            return True
            
        except Exception as e:
            print(f" Lỗi khi tạo payment: {e}")
            db.session.rollback()
            return False

def create_pending_payments():
    """Tạo một số giao dịch đang chờ thanh toán"""
    
    with app.app_context():
        try:
            # Lấy các booking gần đây chưa có payment
            recent_bookings = Booking.query.filter(
                ~Booking.id.in_(
                    db.session.query(Payment.booking_id)
                )
            ).limit(3).all()
            
            if not recent_bookings:
                print(" Không có booking nào chưa có payment!")
                return False
            
            created_count = 0
            
            for booking in recent_bookings:
                payment = Payment(
                    payment_code=generate_payment_code(),
                    order_code=generate_order_code(),
                    amount=booking.total_price,
                    currency='VND',
                    status='pending',  # Đang chờ thanh toán
                    payment_method=None,
                    created_at=datetime.utcnow(),
                    description=f"Thanh toán cho booking nhà {booking.home.title}",
                    customer_name=booking.renter.full_name,
                    customer_email=booking.renter.email,
                    customer_phone=booking.renter.phone,
                    booking_id=booking.id,
                    owner_id=booking.home.owner_id,
                    renter_id=booking.renter_id
                )
                
                db.session.add(payment)
                created_count += 1
                print(f" Đã tạo pending payment cho booking {booking.id}")
            
            db.session.commit()
            print(f" Đã tạo {created_count} pending payment!")
            return True
            
        except Exception as e:
            print(f" Lỗi khi tạo pending payment: {e}")
            db.session.rollback()
            return False

def show_payment_statistics():
    """Hiển thị thống kê payment"""
    
    with app.app_context():
        try:
            total_payments = Payment.query.count()
            successful_payments = Payment.query.filter_by(status='success').count()
            pending_payments = Payment.query.filter_by(status='pending').count()
            failed_payments = Payment.query.filter_by(status='failed').count()
            
            total_amount = db.session.query(db.func.sum(Payment.amount)).filter_by(status='success').scalar() or 0
            
            print("\n Thống kê Payment:")
            print(f"  - Tổng số giao dịch: {total_payments}")
            print(f"  - Giao dịch thành công: {successful_payments}")
            print(f"  - Giao dịch đang chờ: {pending_payments}")
            print(f"  - Giao dịch thất bại: {failed_payments}")
            print(f"  - Tổng tiền đã thanh toán: {total_amount:,.0f} VND")
            
            # Thống kê theo owner
            owner_stats = db.session.query(
                Payment.owner_id,
                db.func.count(Payment.id).label('total_payments'),
                db.func.sum(Payment.amount).label('total_amount')
            ).filter_by(status='success').group_by(Payment.owner_id).all()
            
            print("\n Thống kê theo Owner:")
            for owner_id, total_payments, total_amount in owner_stats:
                owner = Owner.query.get(owner_id)
                owner_name = owner.full_name if owner else f"Owner {owner_id}"
                print(f"  - {owner_name}: {total_payments} giao dịch, {total_amount:,.0f} VND")
                
        except Exception as e:
            print(f" Lỗi khi hiển thị thống kê: {e}")

if __name__ == "__main__":
    print(" Bắt đầu tạo dữ liệu mẫu cho payment...")
    
    # Tạo payment_config mẫu
    print("\n1️⃣ Tạo payment_config mẫu...")
    create_sample_payment_configs()
    
    # Tạo payment mẫu
    print("\n2️⃣ Tạo payment mẫu...")
    create_sample_payments()
    
    # Tạo pending payment
    print("\n3️⃣ Tạo pending payment...")
    create_pending_payments()
    
    # Hiển thị thống kê
    print("\n4️⃣ Hiển thị thống kê...")
    show_payment_statistics()
    
    print("\n Hoàn thành tạo dữ liệu mẫu!") 