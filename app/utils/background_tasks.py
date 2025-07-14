"""
Background Tasks Module
Xử lý các task chạy nền như auto cancel payment
"""

import threading
import time
from datetime import datetime, timedelta
from flask import current_app
from app.models.models import db, Payment, PaymentConfig
from app.services.payos_service import PayOSService
from app.utils.payment_utils import update_booking_payment_status

class PaymentTimeoutScheduler:
    """
    Scheduler để tự động hủy payment hết hạn
    """
    
    def __init__(self, app=None):
        self.app = app
        self.running = False
        self.thread = None
        self.interval_minutes = 1  # Kiểm tra mỗi 1 phút
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Khởi tạo scheduler với Flask app"""
        self.app = app
        
        # Đăng ký với app context
        with app.app_context():
            self.start()
    
    def start(self):
        """Bắt đầu scheduler"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.thread.start()
            current_app.logger.info("🚀 Payment timeout scheduler đã khởi động")
    
    def stop(self):
        """Dừng scheduler"""
        self.running = False
        if self.thread:
            self.thread.join()
        current_app.logger.info("⏹️ Payment timeout scheduler đã dừng")
    
    def _run_scheduler(self):
        """Chạy scheduler trong thread riêng"""
        while self.running:
            try:
                with self.app.app_context():
                    self._check_and_cancel_expired_payments()
                
                # Đợi interval
                time.sleep(self.interval_minutes * 60)
                
            except Exception as e:
                current_app.logger.error(f"❌ Lỗi trong payment timeout scheduler: {str(e)}")
                time.sleep(60)  # Đợi 1 phút nếu có lỗi
    
    def _check_and_cancel_expired_payments(self):
        """Kiểm tra và hủy payment hết hạn"""
        try:
            # Tìm tất cả payment pending quá 5 phút
            cutoff_time = datetime.utcnow() - timedelta(minutes=5)
            expired_payments = Payment.query.filter(
                Payment.status == 'pending',
                Payment.created_at < cutoff_time
            ).all()
            
            if expired_payments:
                current_app.logger.info(f"🔍 Tìm thấy {len(expired_payments)} payment hết hạn")
                
                cancelled_count = 0
                error_count = 0
                
                for payment in expired_payments:
                    try:
                        current_app.logger.info(f"🔄 Đang hủy payment {payment.payment_code}")
                        
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
                                    current_app.logger.warning(f"⚠️ Không thể hủy payment trên PayOS: {cancel_response.get('message')}")
                            except Exception as e:
                                current_app.logger.warning(f"⚠️ Lỗi khi hủy payment trên PayOS: {str(e)}")
                        
                        # Cập nhật trạng thái payment
                        payment.mark_as_cancelled("Tự động hủy sau 5 phút")
                        update_booking_payment_status(payment.booking_id, 'cancelled')
                        
                        cancelled_count += 1
                        current_app.logger.info(f"✅ Đã hủy payment {payment.payment_code}")
                        
                    except Exception as e:
                        error_count += 1
                        current_app.logger.error(f"❌ Lỗi khi hủy payment {payment.payment_code}: {str(e)}")
                
                # Commit tất cả thay đổi
                db.session.commit()
                
                current_app.logger.info(f"📊 Hoàn thành: {cancelled_count} payment đã hủy, {error_count} lỗi")
            
        except Exception as e:
            current_app.logger.error(f"❌ Lỗi chung trong check expired payments: {str(e)}")

# Global scheduler instance
payment_scheduler = PaymentTimeoutScheduler()

def init_background_tasks(app):
    """Khởi tạo tất cả background tasks"""
    payment_scheduler.init_app(app)
    app.logger.info("🎯 Background tasks đã được khởi tạo")

def stop_background_tasks(app):
    """Dừng tất cả background tasks"""
    payment_scheduler.stop()
    app.logger.info("🛑 Background tasks đã được dừng") 