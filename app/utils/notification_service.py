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
            # Kiểm tra cấu hình email
            if not EmailConfig.is_configured():
                self.logger.warning("Email chưa được cấu hình, bỏ qua gửi email")
                return False
            
            if not payment.customer_email:
                self.logger.warning(f"Không có email khách hàng cho payment {payment.id}")
                return False
            
            # Lấy thông tin booking và home
            booking = payment.booking
            home = booking.home
            owner = home.owner
            
            # Tạo nội dung email
            subject = EmailConfig.EMAIL_TEMPLATES['payment_success']['subject'].format(room_title=home.title)
            
            # Template email
            email_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Xác nhận thanh toán thành công</title>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background: #28a745; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
                    .content { background: #f8f9fa; padding: 20px; border-radius: 0 0 8px 8px; }
                    .success-icon { font-size: 48px; margin-bottom: 10px; }
                    .payment-details { background: white; padding: 15px; border-radius: 5px; margin: 15px 0; }
                    .detail-row { display: flex; justify-content: space-between; margin: 8px 0; }
                    .label { font-weight: bold; color: #666; }
                    .value { color: #333; }
                    .amount { color: #28a745; font-weight: bold; font-size: 18px; }
                    .footer { margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="success-icon">✅</div>
                        <h1>Thanh toán thành công!</h1>
                        <p>Cảm ơn bạn đã sử dụng dịch vụ của chúng tôi</p>
                    </div>
                    
                    <div class="content">
                        <h2>Xin chào {{ customer_name }},</h2>
                        <p>Giao dịch thanh toán của bạn đã được xử lý thành công. Dưới đây là thông tin chi tiết:</p>
                        
                        <div class="payment-details">
                            <h3>Thông tin đặt nhà</h3>
                            <div class="detail-row">
                                <span class="label">Nhà:</span>
                                <span class="value">{{ room_title }}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Địa chỉ:</span>
                                <span class="value">{{ room_address }}</span>
                            </div>
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
                        
                        <div class="payment-details">
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
                                <span class="label">Thời gian thanh toán:</span>
                                <span class="value">{{ payment_time }}</span>
                            </div>
                        </div>
                        
                        <div class="payment-details">
                            <h3>Thông tin liên hệ</h3>
                            <div class="detail-row">
                                <span class="label">Chủ nhà:</span>
                                <span class="value">{{ owner_name }}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Số điện thoại:</span>
                                <span class="value">{{ owner_phone or 'Chưa cập nhật' }}</span>
                            </div>
                        </div>
                        
                        <p><strong>Lưu ý:</strong></p>
                        <ul>
                            <li>Vui lòng đến đúng thời gian đã đặt</li>
                            <li>Mang theo giấy tờ tùy thân khi check-in</li>
                            <li>Liên hệ chủ nhà nếu có thay đổi</li>
                            <li>Bạn có thể xem chi tiết đặt nhà trong tài khoản</li>
                        </ul>
                        
                        <div class="footer">
                            <p>Email này được gửi tự động từ hệ thống Staycation.</p>
                            <p>Nếu có thắc mắc, vui lòng liên hệ: support@staycation.com</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Chuẩn bị dữ liệu cho template
            template_data = {
                'customer_name': payment.customer_name or 'Khách hàng',
                'room_title': home.title,
                'room_address': f"{home.address}, {home.district}, {home.city}",
                'booking_date': booking.start_time.strftime('%d/%m/%Y'),
                'booking_time': f"{booking.start_time.strftime('%H:%M')} - {booking.end_time.strftime('%H:%M')}",
                'booking_type': 'Theo giờ' if booking.booking_type == 'hourly' else 'Theo đêm',
                'payment_code': payment.payment_code,
                'formatted_amount': f"{payment.amount:,.0f} VND",
                'payment_method': payment.payment_method or 'PayOS',
                'payment_time': payment.paid_at.strftime('%d/%m/%Y %H:%M') if payment.paid_at else 'Vừa xong',
                'owner_name': owner.full_name or owner.username,
                'owner_phone': owner.phone
            }
            
            # Render email content
            html_content = render_template_string(email_template, **template_data)
            
            # Gửi email
            success = self._send_email(
                to_email=payment.customer_email,
                subject=subject,
                html_content=html_content
            )
            
            if success:
                self.logger.info(f"Email xác nhận thanh toán đã gửi thành công cho payment {payment.id}")
                return True
            else:
                self.logger.error(f"Không thể gửi email xác nhận thanh toán cho payment {payment.id}")
                return False
                
        except Exception as e:
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
            # Lấy cấu hình email từ EmailConfig
            smtp_config = EmailConfig.get_smtp_config()
            
            if not EmailConfig.is_configured():
                self.logger.warning("Thiếu cấu hình SMTP, bỏ qua gửi email")
                return False
            
            # Tạo message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = smtp_config['from_email']
            msg['To'] = to_email
            
            # Thêm HTML content
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Kết nối SMTP và gửi
            with smtplib.SMTP(smtp_config['server'], smtp_config['port']) as server:
                server.starttls()
                server.login(smtp_config['username'], smtp_config['password'])
                server.send_message(msg)
            
            return True
            
        except Exception as e:
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