import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
import random
import string
from datetime import datetime, timedelta
import json
import hashlib
import hmac
import base64
import logging
from config.email_config import EmailConfig

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.otp_expiry_minutes = 2  # Thay đổi thành 2 phút
        self.max_resend_per_day = 3  # Giảm xuống 3 lần/ngày
        self.max_attempts_per_otp = 3  # Giảm xuống 3 lần thử/OTP
        
    def _get_config(self):
        """Lấy cấu hình email từ EmailConfig"""
        try:
            if not EmailConfig.is_configured():
                logger.error("Email configuration not found")
                return None
            
            config = EmailConfig.get_smtp_config()
            logger.info(f"Email config loaded: {config['username']}")
            return config
        except Exception as e:
            logger.error(f"Error loading email config: {e}")
            return None
    
    def generate_otp(self, length=6):
        """Tạo mã OTP ngẫu nhiên"""
        return ''.join(random.choices(string.digits, k=length))
    
    def generate_secure_token(self, otp, user_id, timestamp):
        """Tạo token bảo mật cho OTP"""
        # Tạo secret key từ app config hoặc fallback
        try:
            secret_key = current_app.config.get('SECRET_KEY', 'fallback-secret-key')
        except RuntimeError:
            secret_key = 'fallback-secret-key'
        
        # Tạo payload
        payload = f"{otp}:{user_id}:{timestamp}"
        
        # Tạo HMAC signature
        signature = hmac.new(
            secret_key.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Encode payload và signature
        token_data = f"{payload}:{signature}"
        return base64.urlsafe_b64encode(token_data.encode('utf-8')).decode('utf-8')
    
    def verify_secure_token(self, token, user_id):
        """Xác thực token bảo mật"""
        try:
            # Decode token
            token_data = base64.urlsafe_b64decode(token.encode('utf-8')).decode('utf-8')
            payload, signature = token_data.rsplit(':', 1)
            
            # Tách payload
            otp, token_user_id, timestamp = payload.split(':', 2)
            
            # Kiểm tra user_id
            if int(token_user_id) != user_id:
                return None, None
            
            # Tạo secret key
            try:
                secret_key = current_app.config.get('SECRET_KEY', 'fallback-secret-key')
            except RuntimeError:
                secret_key = 'fallback-secret-key'
            
            # Verify signature
            expected_signature = hmac.new(
                secret_key.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return None, None
            
            return otp, timestamp
            
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None, None
    
    def send_verification_email(self, to_email, otp, owner_name, user_id):
        """Gửi email chứa mã OTP để verify email"""
        try:
            config = self._get_config()
            if not config:
                return False, "Email configuration not found", None
            
            # Tạo timestamp và token bảo mật
            timestamp = datetime.now().isoformat()
            secure_token = self.generate_secure_token(otp, user_id, timestamp)
            
            logger.info(f"Sending verification email to {to_email}")
            
            # Tạo message
            message = MIMEMultipart("alternative")
            message["Subject"] = "Xác thực Email - Staycation"
            message["From"] = config['from_email']
            message["To"] = to_email
            
            # HTML content với thời gian hết hạn mới
            html_content = f"""
            <html>
            <body>
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center;">
                        <h2 style="color: #007bff; margin-bottom: 20px;">🔒 Xác thực Email</h2>
                        <p style="font-size: 16px; color: #333; margin-bottom: 20px;">
                            Xin chào <strong>{owner_name}</strong>,
                        </p>
                        <p style="font-size: 16px; color: #333; margin-bottom: 20px;">
                            Để hoàn tất việc xác thực tài khoản, vui lòng sử dụng mã OTP dưới đây:
                        </p>
                        <div style="background-color: #007bff; color: white; padding: 15px; border-radius: 8px; font-size: 24px; font-weight: bold; letter-spacing: 5px; margin: 20px 0;">
                            {otp}
                        </div>
                        <p style="font-size: 14px; color: #666; margin-bottom: 20px;">
                            Mã này có hiệu lực trong <strong>{self.otp_expiry_minutes} phút</strong>.
                        </p>
                        <p style="font-size: 14px; color: #666; margin-bottom: 20px;">
                            Bạn có thể thử tối đa <strong>{self.max_attempts_per_otp} lần</strong> với mã này.
                        </p>
                        <p style="font-size: 14px; color: #666; margin-bottom: 20px;">
                            Nếu bạn không thực hiện yêu cầu này, vui lòng bỏ qua email này.
                        </p>
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                        <p style="font-size: 12px; color: #999;">
                            Email này được gửi từ hệ thống Staycation. Vui lòng không trả lời email này.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text content
            text_content = f"""
            Xác thực Email - Staycation
            
            Xin chào {owner_name},
            
            Để hoàn tất việc xác thực tài khoản, vui lòng sử dụng mã OTP: {otp}
            
            Mã này có hiệu lực trong {self.otp_expiry_minutes} phút.
            Bạn có thể thử tối đa {self.max_attempts_per_otp} lần với mã này.
            
            Nếu bạn không thực hiện yêu cầu này, vui lòng bỏ qua email này.
            
            ---
            Email này được gửi từ hệ thống Staycation.
            """
            
            # Attach parts
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")
            message.attach(part1)
            message.attach(part2)
            
            # Gửi email với debug logging
            logger.info(f"Connecting to SMTP server: {self.smtp_server}:{self.smtp_port}")
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.set_debuglevel(1)  # Enable debug logging
                logger.info("Starting TLS connection...")
                server.starttls(context=context)
                logger.info("Logging in to SMTP server...")
                server.login(config['username'], config['password'])
                logger.info("Sending email...")
                server.sendmail(config['from_email'], to_email, message.as_string())
                logger.info("Email sent successfully!")
            
            return True, "Email sent successfully", secure_token
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP Authentication failed: {e}"
            logger.error(error_msg)
            return False, error_msg, None
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error occurred: {e}"
            logger.error(error_msg)
            return False, error_msg, None
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.error(error_msg)
            return False, error_msg, None
    
    def send_resend_otp_email(self, to_email, otp, owner_name, user_id):
        """Gửi lại mã OTP"""
        try:
            config = self._get_config()
            if not config:
                return False, "Email configuration not found", None
            
            # Tạo timestamp và token bảo mật
            timestamp = datetime.now().isoformat()
            secure_token = self.generate_secure_token(otp, user_id, timestamp)
            
            logger.info(f"Resending OTP email to {to_email}")
            
            message = MIMEMultipart("alternative")
            message["Subject"] = "Mã OTP mới - Staycation"
            message["From"] = config['from_email']
            message["To"] = to_email
            
            html_content = f"""
            <html>
            <body>
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center;">
                        <h2 style="color: #007bff; margin-bottom: 20px;">🔄 Mã OTP mới</h2>
                        <p style="font-size: 16px; color: #333; margin-bottom: 20px;">
                            Xin chào <strong>{owner_name}</strong>,
                        </p>
                        <p style="font-size: 16px; color: #333; margin-bottom: 20px;">
                            Dưới đây là mã OTP mới để xác thực email:
                        </p>
                        <div style="background-color: #28a745; color: white; padding: 15px; border-radius: 8px; font-size: 24px; font-weight: bold; letter-spacing: 5px; margin: 20px 0;">
                            {otp}
                        </div>
                        <p style="font-size: 14px; color: #666; margin-bottom: 20px;">
                            Mã này có hiệu lực trong <strong>{self.otp_expiry_minutes} phút</strong>.
                        </p>
                        <p style="font-size: 14px; color: #666; margin-bottom: 20px;">
                            Bạn có thể thử tối đa <strong>{self.max_attempts_per_otp} lần</strong> với mã này.
                        </p>
                        <p style="font-size: 14px; color: #666; margin-bottom: 20px;">
                            Nếu bạn không thực hiện yêu cầu này, vui lòng bỏ qua email này.
                        </p>
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                        <p style="font-size: 12px; color: #999;">
                            Email này được gửi từ hệ thống Staycation. Vui lòng không trả lời email này.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            Mã OTP mới - Staycation
            
            Xin chào {owner_name},
            
            Dưới đây là mã OTP mới để xác thực email: {otp}
            
            Mã này có hiệu lực trong {self.otp_expiry_minutes} phút.
            Bạn có thể thử tối đa {self.max_attempts_per_otp} lần với mã này.
            
            Nếu bạn không thực hiện yêu cầu này, vui lòng bỏ qua email này.
            
            ---
            Email này được gửi từ hệ thống Staycation.
            """
            
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")
            message.attach(part1)
            message.attach(part2)
            
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.set_debuglevel(1)  # Enable debug logging
                server.starttls(context=context)
                server.login(config['username'], config['password'])
                server.sendmail(config['from_email'], to_email, message.as_string())
            
            return True, "Resend email sent successfully", secure_token
            
        except Exception as e:
            error_msg = f"Failed to send resend email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None

    def send_password_change_otp_email(self, to_email, otp, user_name, user_id):
        """Gửi email chứa mã OTP để đổi mật khẩu"""
        try:
            config = self._get_config()
            if not config:
                return False, "Email configuration not found", None
            
            # Tạo timestamp và token bảo mật
            timestamp = datetime.now().isoformat()
            secure_token = self.generate_secure_token(otp, user_id, timestamp)
            
            logger.info(f"Sending password change OTP email to {to_email}")
            
            # Tạo message
            message = MIMEMultipart("alternative")
            message["Subject"] = "Đổi mật khẩu - Staycation"
            message["From"] = config['from_email']
            message["To"] = to_email
            
            # HTML content
            html_content = f"""
            <html>
            <body>
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center;">
                        <h2 style="color: #dc3545; margin-bottom: 20px;">🔐 Đổi Mật Khẩu</h2>
                        <p style="font-size: 16px; color: #333; margin-bottom: 20px;">
                            Xin chào <strong>{user_name}</strong>,
                        </p>
                        <p style="font-size: 16px; color: #333; margin-bottom: 20px;">
                            Bạn đã yêu cầu đổi mật khẩu tài khoản Staycation. Vui lòng sử dụng mã OTP dưới đây:
                        </p>
                        <div style="background-color: #dc3545; color: white; padding: 15px; border-radius: 8px; font-size: 24px; font-weight: bold; letter-spacing: 5px; margin: 20px 0;">
                            {otp}
                        </div>
                        <p style="font-size: 14px; color: #666; margin-bottom: 20px;">
                            Mã này có hiệu lực trong <strong>2 phút</strong>.
                        </p>
                        <p style="font-size: 14px; color: #666; margin-bottom: 20px;">
                            Bạn có thể thử tối đa <strong>3 lần</strong> với mã này.
                        </p>
                        <p style="font-size: 14px; color: #666; margin-bottom: 20px;">
                            Nếu bạn không thực hiện yêu cầu này, vui lòng bỏ qua email này và mật khẩu của bạn sẽ không thay đổi.
                        </p>
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                        <p style="font-size: 12px; color: #999;">
                            Email này được gửi từ hệ thống Staycation. Vui lòng không trả lời email này.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text content
            text_content = f"""
            Đổi Mật Khẩu - Staycation
            
            Xin chào {user_name},
            
            Bạn đã yêu cầu đổi mật khẩu tài khoản Staycation. Vui lòng sử dụng mã OTP: {otp}
            
            Mã này có hiệu lực trong 2 phút.
            Bạn có thể thử tối đa 3 lần với mã này.
            
            Nếu bạn không thực hiện yêu cầu này, vui lòng bỏ qua email này.
            
            ---
            Email này được gửi từ hệ thống Staycation.
            """
            
            # Attach parts
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")
            message.attach(part1)
            message.attach(part2)
            
            # Gửi email
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(config['username'], config['password'])
                server.sendmail(config['from_email'], to_email, message.as_string())
            
            return True, "Email sent successfully", secure_token
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP Authentication failed: {e}"
            logger.error(error_msg)
            return False, error_msg, None
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error occurred: {e}"
            logger.error(error_msg)
            return False, error_msg, None
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.error(error_msg)
            return False, error_msg, None

    def send_password_change_success_email(self, to_email, user_name):
        """Gửi email thông báo đổi mật khẩu thành công"""
        try:
            config = self._get_config()
            if not config:
                return False, "Email configuration not found"
            
            logger.info(f"Sending password change success email to {to_email}")
            
            # Tạo message
            message = MIMEMultipart("alternative")
            message["Subject"] = "Đổi mật khẩu thành công - Staycation"
            message["From"] = config['from_email']
            message["To"] = to_email
            
            # HTML content
            html_content = f"""
            <html>
            <body>
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center;">
                        <h2 style="color: #28a745; margin-bottom: 20px;">✅ Đổi Mật Khẩu Thành Công</h2>
                        <p style="font-size: 16px; color: #333; margin-bottom: 20px;">
                            Xin chào <strong>{user_name}</strong>,
                        </p>
                        <p style="font-size: 16px; color: #333; margin-bottom: 20px;">
                            Mật khẩu tài khoản Staycation của bạn đã được thay đổi thành công.
                        </p>
                        <div style="background-color: #28a745; color: white; padding: 15px; border-radius: 8px; margin: 20px 0;">
                            <i class="fas fa-check-circle" style="font-size: 24px; margin-right: 10px;"></i>
                            Mật khẩu đã được cập nhật
                        </div>
                        <p style="font-size: 14px; color: #666; margin-bottom: 20px;">
                            Nếu bạn không thực hiện thay đổi này, vui lòng liên hệ ngay với chúng tôi.
                        </p>
                        <p style="font-size: 14px; color: #666; margin-bottom: 20px;">
                            Để bảo mật tài khoản, vui lòng không chia sẻ mật khẩu với bất kỳ ai.
                        </p>
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                        <p style="font-size: 12px; color: #999;">
                            Email này được gửi từ hệ thống Staycation. Vui lòng không trả lời email này.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text content
            text_content = f"""
            Đổi Mật Khẩu Thành Công - Staycation
            
            Xin chào {user_name},
            
            Mật khẩu tài khoản Staycation của bạn đã được thay đổi thành công.
            
            Nếu bạn không thực hiện thay đổi này, vui lòng liên hệ ngay với chúng tôi.
            
            Để bảo mật tài khoản, vui lòng không chia sẻ mật khẩu với bất kỳ ai.
            
            ---
            Email này được gửi từ hệ thống Staycation.
            """
            
            # Attach parts
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")
            message.attach(part1)
            message.attach(part2)
            
            # Gửi email
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(config['username'], config['password'])
                server.sendmail(config['from_email'], to_email, message.as_string())
            
            return True, "Email sent successfully"
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP Authentication failed: {e}"
            logger.error(error_msg)
            return False, error_msg
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error occurred: {e}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.error(error_msg)
            return False, error_msg

# Global instance
email_service = EmailService() 