"""
Notification Service - Xử lý thông báo và gửi email
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, render_template_string
from app.models.models import db, Payment, Booking, Renter, Owner
from config.email_config import EmailConfig
import logging
from datetime import datetime
import os

class NotificationService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def send_payment_success_email(self, payment: Payment):
        """
        Gửi email xác nhận thanh toán thành công cho renter
        """
        try:
            print(f"🔍 DEBUG: Bắt đầu gửi email cho payment {payment.id}")
            print(f"🔍 DEBUG: Customer email: {payment.customer_email}")
            print(f"🔍 DEBUG: Payment amount: {payment.amount}")
            self.logger.info(f"DEBUG: Gọi hàm gửi email cho payment {payment.id}, email: {payment.customer_email}")
            print(f"🔍 DEBUG: EmailConfig.is_configured(): {EmailConfig.is_configured()}")
            print(f"🔍 DEBUG: SMTP_USERNAME: {EmailConfig.SMTP_USERNAME}")
            print(f"🔍 DEBUG: SMTP_PASSWORD exists: {bool(EmailConfig.SMTP_PASSWORD)}")
            if not EmailConfig.is_configured():
                print("❌ DEBUG: Email chưa được cấu hình!")
                self.logger.warning("Email chưa được cấu hình, bỏ qua gửi email")
                return False
            if not payment.customer_email:
                print(f"❌ DEBUG: Không có email khách hàng cho payment {payment.id}")
                self.logger.warning(f"Không có email khách hàng cho payment {payment.id}")
                return False
            print(f"🔍 DEBUG: Lấy thông tin booking...")
            booking = payment.booking
            if not booking:
                print(f"❌ DEBUG: Không tìm thấy booking cho payment {payment.id}")
                return False
            print(f"🔍 DEBUG: Booking ID: {booking.id}")
            home = booking.home
            if not home:
                print(f"❌ DEBUG: Không tìm thấy home cho booking {booking.id}")
                return False
            print(f"🔍 DEBUG: Home title: {home.title}")
            owner = home.owner
            print(f"🔍 DEBUG: Tạo email content...")
            subject = f"Xác nhận thanh toán thành công - Mã giao dịch: {payment.payment_code}"
            
            # Template email mới
            email_template = '''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Xác nhận thanh toán thành công</title>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px #eee; }
                    .header { text-align: center; margin-bottom: 20px; }
                    .header .icon { font-size: 48px; color: #28a745; }
                    .header h1 { color: #28a745; margin: 10px 0 0 0; }
                    .section { margin-bottom: 20px; }
                    .section-title { font-weight: bold; margin-bottom: 8px; color: #222; }
                    .info-table { width: 100%; border-collapse: collapse; }
                    .info-table td { padding: 4px 0; }
                    .label { color: #666; font-weight: bold; width: 120px; }
                    .value { color: #222; }
                    .amount { color: #28a745; font-weight: bold; }
                    .note { background: #eaf6ff; padding: 12px; border-radius: 6px; font-size: 14px; }
                    .footer { margin-top: 30px; font-size: 13px; color: #888; text-align: center; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="icon">✔️</div>
                        <h1>Thanh toán thành công!</h1>
                        <p>Cảm ơn bạn đã sử dụng dịch vụ của chúng tôi. Giao dịch của bạn đã được xử lý thành công.</p>
                    </div>
                    <div class="section">
                        <div class="section-title">THÔNG TIN GIAO DỊCH</div>
                        <table class="info-table">
                            <tr><td class="label">Mã giao dịch:</td><td class="value">{{ transaction_id }}</td></tr>
                            <tr><td class="label">Thời gian:</td><td class="value">{{ date }} {{ time }}</td></tr>
                            <tr><td class="label">Số tiền:</td><td class="value amount">{{ amount }} VND</td></tr>
                            <tr><td class="label">Phương thức:</td><td class="value">{{ payment_method }}</td></tr>
                        </table>
                    </div>
                    <div class="section">
                        <div class="section-title">THÔNG TIN ĐẶT PHÒNG</div>
                        <table class="info-table">
                            <tr><td class="label">Nhà:</td><td class="value">{{ property_name }}</td></tr>
                            <tr><td class="label">Địa chỉ:</td><td class="value">{{ address }}</td></tr>
                            <tr><td class="label">Ngày đặt:</td><td class="value">{{ booking_date }}</td></tr>
                            <tr><td class="label">Thời gian:</td><td class="value">{{ check_in_time }} - {{ check_out_time }}</td></tr>
                        </table>
                    </div>
                    <div class="note">
                        <b>Lưu ý quan trọng:</b><br>
                        • Email xác nhận đã được gửi đến {{ email }}<br>
                        • Bạn có thể xem chi tiết booking trong tài khoản<br>
                        • Liên hệ chủ phòng nếu cần hỗ trợ thêm
                    </div>
                    <div class="footer">
                        <div><b>Liên hệ hỗ trợ:</b></div>
                        <div>Email: support@yourcompany.com</div>
                        <div>Hotline: 1900-xxxx-xxx</div>
                        <br>
                        Trân trọng,<br>
                        {{ company_name }}
                    </div>
                </div>
            </body>
            </html>
            '''
            # Chuẩn bị dữ liệu cho template
            paid_at = payment.paid_at or datetime.now()
            template_data = {
                'customer_name': payment.customer_name or 'Khách hàng',
                'transaction_id': payment.payment_code,
                'date': paid_at.strftime('%d/%m/%Y'),
                'time': paid_at.strftime('%H:%M'),
                'amount': f"{payment.amount:,.0f}",
                'payment_method': payment.payment_method or 'PayOS',
                'property_name': home.title,
                'address': f"{home.address}, {home.district}, {home.city}",
                'booking_date': booking.start_time.strftime('%d/%m/%Y'),
                'check_in_time': booking.start_time.strftime('%H:%M'),
                'check_out_time': booking.end_time.strftime('%H:%M'),
                'email': payment.customer_email,
                'company_name': EmailConfig.COMPANY_NAME or 'Staycation',
            }
            html_content = render_template_string(email_template, **template_data)
            print(f"🔍 DEBUG: Gọi _send_email...")
            success = self._send_email(
                to_email=payment.customer_email,
                subject=subject,
                html_content=html_content
            )
            print(f"🔍 DEBUG: Kết quả gửi email: {success}")
            if success:
                print(f"✅ DEBUG: Email đã gửi thành công!")
                self.logger.info(f"Email xác nhận thanh toán đã gửi thành công cho payment {payment.id}")
                return True
            else:
                print(f"❌ DEBUG: Gửi email thất bại!")
                self.logger.error(f"Không thể gửi email xác nhận thanh toán cho payment {payment.id}")
                return False
                
        except Exception as e:
            print(f"💥 DEBUG: Exception trong send_payment_success_email: {str(e)}")
            print(f"💥 DEBUG: Exception type: {type(e)}")
            import traceback
            traceback.print_exc()
            self.logger.error(f"Lỗi khi gửi email xác nhận thanh toán: {str(e)}")
            return False
    
    def send_payment_success_notification_to_owner(self, payment: Payment):
        """
        Gửi thông báo cho owner khi có thanh toán thành công
        """
        try:
            # Kiểm tra cấu hình email
            if not EmailConfig.is_configured():
                self.logger.warning("Email chưa được cấu hình, bỏ qua gửi email")
                return False
            
            booking = payment.booking
            home = booking.home
            owner = home.owner
            
            subject = EmailConfig.EMAIL_TEMPLATES['payment_success_owner']['subject'].format(room_title=home.title)
            
            email_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Thanh toán thành công</title>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background: #007bff; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
                    .content { background: #f8f9fa; padding: 20px; border-radius: 0 0 8px 8px; }
                    .notification-icon { font-size: 48px; margin-bottom: 10px; }
                    .booking-details { background: white; padding: 15px; border-radius: 5px; margin: 15px 0; }
                    .detail-row { display: flex; justify-content: space-between; margin: 8px 0; }
                    .label { font-weight: bold; color: #666; }
                    .value { color: #333; }
                    .amount { color: #28a745; font-weight: bold; font-size: 18px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="notification-icon">💰</div>
                        <h1>Thanh toán thành công!</h1>
                        <p>Bạn có một giao dịch thanh toán mới</p>
                    </div>
                    
                    <div class="content">
                        <h2>Xin chào {{ owner_name }},</h2>
                        <p>Nhà <strong>{{ room_title }}</strong> của bạn vừa có thanh toán thành công.</p>
                        
                        <div class="booking-details">
                            <h3>Thông tin khách hàng</h3>
                            <div class="detail-row">
                                <span class="label">Tên khách:</span>
                                <span class="value">{{ customer_name }}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Email:</span>
                                <span class="value">{{ customer_email }}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Số điện thoại:</span>
                                <span class="value">{{ customer_phone or 'Chưa cập nhật' }}</span>
                            </div>
                        </div>
                        
                        <div class="booking-details">
                            <h3>Thông tin đặt nhà</h3>
                            <div class="detail-row">
                                <span class="label">Ngày đặt:</span>
                                <span class="value">{{ booking_date }}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Thời gian:</span>
                                <span class="value">{{ booking_time }}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Loại đặt:</span>
                                <span class="value">{{ booking_type }}</span>
                            </div>
                        </div>
                        
                        <div class="booking-details">
                            <h3>Thông tin thanh toán</h3>
                            <div class="detail-row">
                                <span class="label">Mã giao dịch:</span>
                                <span class="value">{{ payment_code }}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Số tiền:</span>
                                <span class="value amount">{{ formatted_amount }}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Phương thức:</span>
                                <span class="value">{{ payment_method }}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Thời gian:</span>
                                <span class="value">{{ payment_time }}</span>
                            </div>
                        </div>
                        
                        <p><strong>Hành động cần thiết:</strong></p>
                        <ul>
                            <li>Chuẩn bị nhà sạch sẽ</li>
                            <li>Kiểm tra các tiện nghi</li>
                            <li>Liên hệ khách hàng để xác nhận thời gian check-in</li>
                            <li>Cập nhật trạng thái nhà trong hệ thống</li>
                        </ul>
                    </div>
                </div>
            </body>
            </html>
            """
            
            template_data = {
                'owner_name': owner.full_name or owner.username,
                'room_title': home.title,
                'customer_name': payment.customer_name or 'Khách hàng',
                'customer_email': payment.customer_email or 'Chưa cập nhật',
                'customer_phone': payment.customer_phone,
                'booking_date': booking.start_time.strftime('%d/%m/%Y'),
                'booking_time': f"{booking.start_time.strftime('%H:%M')} - {booking.end_time.strftime('%H:%M')}",
                'booking_type': 'Theo giờ' if booking.booking_type == 'hourly' else 'Theo đêm',
                'payment_code': payment.payment_code,
                'formatted_amount': f"{payment.amount:,.0f} VND",
                'payment_method': payment.payment_method or 'PayOS',
                'payment_time': payment.paid_at.strftime('%d/%m/%Y %H:%M') if payment.paid_at else 'Vừa xong'
            }
            
            html_content = render_template_string(email_template, **template_data)
            
            success = self._send_email(
                to_email=owner.email,
                subject=subject,
                html_content=html_content
            )
            
            if success:
                self.logger.info(f"Email thông báo đã gửi thành công cho owner {owner.id}")
                return True
            else:
                self.logger.error(f"Không thể gửi email thông báo cho owner {owner.id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Lỗi khi gửi email thông báo cho owner: {str(e)}")
            return False
    
    def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """
        Gửi email sử dụng SMTP
        """
        try:
            print(f"🔍 DEBUG: _send_email called")
            print(f"🔍 DEBUG: to_email: {to_email}")
            print(f"🔍 DEBUG: subject: {subject}")
            smtp_config = EmailConfig.get_smtp_config()
            print(f"🔍 DEBUG: SMTP config: {smtp_config}")
            if not EmailConfig.is_configured():
                print("❌ DEBUG: SMTP not configured in _send_email")
                self.logger.warning("Thiếu cấu hình SMTP, bỏ qua gửi email")
                return False
            print(f"🔍 DEBUG: Creating email message...")
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = smtp_config['from_email']
            msg['To'] = to_email
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            print(f"🔍 DEBUG: Connecting to SMTP server...")
            with smtplib.SMTP(smtp_config['server'], smtp_config['port']) as server:
                print(f"🔍 DEBUG: Starting TLS...")
                server.starttls()
                print(f"🔍 DEBUG: Logging in...")
                server.login(smtp_config['username'], smtp_config['password'])
                print(f"🔍 DEBUG: Sending message...")
                server.send_message(msg)
            print(f"✅ DEBUG: Email sent successfully!")
            return True
        except Exception as e:
            print(f"💥 DEBUG: Exception in _send_email: {str(e)}")
            print(f"💥 DEBUG: Exception type: {type(e)}")
            import traceback
            traceback.print_exc()
            self.logger.error(f"Lỗi khi gửi email: {str(e)}")
            return False
    
    def create_web_notification(self, payment: Payment, notification_type: str = 'payment_success'):
        """
        Tạo thông báo web cho real-time notification
        """
        try:
            # Tạo notification data
            notification_data = {
                'type': notification_type,
                'payment_id': payment.id,
                'booking_id': payment.booking_id,
                'renter_id': payment.renter_id,
                'owner_id': payment.owner_id,
                'amount': payment.amount,
                'payment_code': payment.payment_code,
                'timestamp': datetime.utcnow().isoformat(),
                'message': f'Thanh toán thành công: {payment.payment_code} - {payment.amount:,.0f} VND'
            }
            
            # Lưu vào database hoặc cache để real-time notification
            # Có thể sử dụng Redis hoặc database table riêng
            self.logger.info(f"Tạo web notification: {notification_data}")
            
            return notification_data
            
        except Exception as e:
            self.logger.error(f"Lỗi khi tạo web notification: {str(e)}")
            return None

# Global instance
notification_service = NotificationService() 