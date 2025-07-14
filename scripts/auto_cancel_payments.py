#!/usr/bin/env python3
"""
Script tự động hủy payment hết hạn sau 5 phút
Chạy định kỳ để kiểm tra và hủy payment pending quá 5 phút
"""

import sys
import os
import time
from datetime import datetime, timedelta

# Thêm đường dẫn project vào sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models.models import db, Payment, PaymentConfig
from app.services.payos_service import PayOSService
from app.utils.payment_utils import update_booking_payment_status
from config.config import Config

def auto_cancel_expired_payments():
    """
    Tự động hủy payment pending quá 5 phút
    """
    app = create_app()
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        try:
            # Tìm tất cả payment pending quá 5 phút
            cutoff_time = datetime.utcnow() - timedelta(minutes=5)
            expired_payments = Payment.query.filter(
                Payment.status == 'pending',
                Payment.created_at < cutoff_time
            ).all()
            
            print(f"[{datetime.utcnow()}] Tìm thấy {len(expired_payments)} payment hết hạn")
            
            cancelled_count = 0
            error_count = 0
            
            for payment in expired_payments:
                try:
                    print(f"Đang hủy payment {payment.payment_code} (tạo lúc {payment.created_at})")
                    
                    # Lấy cấu hình PayOS
                    owner_config = PaymentConfig.query.filter_by(
                        owner_id=payment.owner_id, 
                        is_active=True
                    ).first()
                    
                    # Hủy payment trên PayOS nếu có transaction_id
                    if payment.payos_transaction_id and owner_config:
                        try:
                            payos = PayOSService(
                                owner_config.payos_client_id,
                                owner_config.payos_api_key,
                                owner_config.payos_checksum_key
                            )
                            
                            cancel_response = payos.cancel_payment(
                                payment.payos_transaction_id,
                                "Tự động hủy sau 5 phút"
                            )
                            
                            if cancel_response.get('error'):
                                print(f"⚠️ Không thể hủy payment trên PayOS: {cancel_response.get('message')}")
                        except Exception as e:
                            print(f"⚠️ Lỗi khi hủy payment trên PayOS: {str(e)}")
                    
                    # Cập nhật trạng thái payment
                    payment.mark_as_cancelled("Tự động hủy sau 5 phút")
                    update_booking_payment_status(payment.booking_id, 'cancelled')
                    
                    cancelled_count += 1
                    print(f"✅ Đã hủy payment {payment.payment_code}")
                    
                except Exception as e:
                    error_count += 1
                    print(f"❌ Lỗi khi hủy payment {payment.payment_code}: {str(e)}")
            
            # Commit tất cả thay đổi
            db.session.commit()
            
            print(f"[{datetime.utcnow()}] Hoàn thành: {cancelled_count} payment đã hủy, {error_count} lỗi")
            
            return {
                'total_expired': len(expired_payments),
                'cancelled': cancelled_count,
                'errors': error_count
            }
            
        except Exception as e:
            print(f"❌ Lỗi chung: {str(e)}")
            return {
                'total_expired': 0,
                'cancelled': 0,
                'errors': 1
            }

def run_continuous_monitoring(interval_minutes=1):
    """
    Chạy monitoring liên tục với interval định kỳ
    """
    print(f"🚀 Bắt đầu monitoring payment timeout (interval: {interval_minutes} phút)")
    
    while True:
        try:
            result = auto_cancel_expired_payments()
            print(f"📊 Kết quả: {result}")
            
            # Đợi interval
            time.sleep(interval_minutes * 60)
            
        except KeyboardInterrupt:
            print("\n⏹️ Dừng monitoring...")
            break
        except Exception as e:
            print(f"❌ Lỗi trong monitoring: {str(e)}")
            time.sleep(60)  # Đợi 1 phút nếu có lỗi

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Auto cancel expired payments')
    parser.add_argument('--once', action='store_true', help='Chạy một lần rồi dừng')
    parser.add_argument('--interval', type=int, default=1, help='Interval monitoring (phút)')
    
    args = parser.parse_args()
    
    if args.once:
        print("🔄 Chạy một lần...")
        result = auto_cancel_expired_payments()
        print(f"📊 Kết quả cuối: {result}")
    else:
        run_continuous_monitoring(args.interval) 