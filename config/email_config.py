"""
Email Configuration - Cấu hình email settings
"""
import os
from dotenv import load_dotenv

load_dotenv()

class EmailConfig:
    # SMTP Configuration
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
    FROM_EMAIL = os.environ.get('FROM_EMAIL', SMTP_USERNAME)
    
    # Email Templates
    EMAIL_TEMPLATES = {
        'payment_success': {
            'subject': 'Xác nhận thanh toán thành công - {room_title}',
            'template': 'payment_success_email.html'
        },
        'payment_success_owner': {
            'subject': 'Thanh toán thành công - Nhà {room_title}',
            'template': 'payment_success_owner_email.html'
        }
    }
    
    # Notification Settings
    ENABLE_EMAIL_NOTIFICATIONS = os.environ.get('ENABLE_EMAIL_NOTIFICATIONS', 'true').lower() == 'true'
    ENABLE_WEB_NOTIFICATIONS = os.environ.get('ENABLE_WEB_NOTIFICATIONS', 'true').lower() == 'true'
    
    # Email Content
    COMPANY_NAME = 'Staycation'
    SUPPORT_EMAIL = 'support@staycation.com'
    WEBSITE_URL = 'https://staycation.com'
    
    @classmethod
    def is_configured(cls):
        """Kiểm tra xem email đã được cấu hình chưa"""
        return bool(cls.SMTP_USERNAME and cls.SMTP_PASSWORD)
    
    @classmethod
    def get_smtp_config(cls):
        """Lấy cấu hình SMTP"""
        return {
            'server': cls.SMTP_SERVER,
            'port': cls.SMTP_PORT,
            'username': cls.SMTP_USERNAME,
            'password': cls.SMTP_PASSWORD,
            'from_email': cls.FROM_EMAIL
        } 