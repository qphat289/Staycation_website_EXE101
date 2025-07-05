# Hệ thống Thông báo (Notification System)

## Tổng quan

Hệ thống thông báo được thiết kế để xử lý các thông báo real-time và email khi có thanh toán thành công. Hệ thống bao gồm:

1. **Web Notifications**: Thông báo real-time trên web
2. **Email Notifications**: Gửi email xác nhận cho renter và owner
3. **API Endpoints**: Các API để quản lý thông báo

## Cấu trúc hệ thống

### 1. Notification Service (`app/utils/notification_service.py`)

Service chính để xử lý thông báo:

```python
from app.utils.notification_service import notification_service

# Gửi email cho renter
notification_service.send_payment_success_email(payment)

# Gửi email cho owner
notification_service.send_payment_success_notification_to_owner(payment)

# Tạo web notification
notification_service.create_web_notification(payment)
```

### 2. Email Configuration (`config/email_config.py`)

Cấu hình email SMTP:

```python
# Các biến môi trường cần thiết:
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
```

### 3. Notification API (`app/routes/notification_api.py`)

Các API endpoint để quản lý thông báo:

- `GET /api/notifications/payment-success/<payment_id>`: Lấy thông báo payment
- `GET /api/notifications/user/<user_id>`: Lấy thông báo của user
- `GET /api/notifications/owner/<owner_id>`: Lấy thông báo của owner
- `POST /api/notifications/check-new`: Kiểm tra thông báo mới
- `POST /api/notifications/mark-read/<notification_id>`: Đánh dấu đã đọc

### 4. Frontend JavaScript (`static/js/notification.js`)

Xử lý thông báo real-time trên frontend:

```javascript
// Khởi tạo notification system
window.notificationSystem = new NotificationSystem();

// Hiển thị thông báo tùy chỉnh
notificationSystem.showCustomNotification('Message', 'success', 5000);
```

## Cài đặt và Cấu hình

### 1. Cấu hình Email

Tạo file `.env` với các thông tin sau:

```env
# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com

# Notification Settings
ENABLE_EMAIL_NOTIFICATIONS=true
ENABLE_WEB_NOTIFICATIONS=true
```

**Lưu ý**: Đối với Gmail, bạn cần sử dụng "App Password" thay vì mật khẩu thông thường.

### 2. Đăng ký Blueprint

Notification API đã được đăng ký trong `app.py`:

```python
from app.routes.notification_api import notification_api
app.register_blueprint(notification_api)
```

### 3. Thêm JavaScript

Notification JavaScript đã được thêm vào `templates/base.html`:

```html
<script src="{{ url_for('static', filename='js/notification.js') }}"></script>
```

## Sử dụng

### 1. Tích hợp vào Webhook Handler

Webhook handler đã được cập nhật để tự động gửi thông báo khi thanh toán thành công:

```python
if payos.is_payment_successful(payos_status):
    # Thanh toán thành công
    payment.mark_as_successful(
        payos_transaction_id=trans_id,
        payment_method=payment_method
    )
    update_booking_payment_status(payment.booking_id, 'success')
    
    # Gửi thông báo và email
    try:
        notification_service.send_payment_success_email(payment)
        notification_service.send_payment_success_notification_to_owner(payment)
        notification_service.create_web_notification(payment)
    except Exception as e:
        current_app.logger.error(f"Error sending notifications: {str(e)}")
```

### 2. Test hệ thống

Chạy script test để kiểm tra hệ thống:

```bash
python scripts/test_notification.py
```

### 3. Kiểm tra thông báo trên Frontend

Thông báo sẽ tự động hiển thị khi:
- User đã đăng nhập
- Có thanh toán thành công mới
- Trang web đang active

## Tính năng

### 1. Web Notifications

- **Real-time**: Kiểm tra thông báo mới mỗi 10 giây
- **Auto-hide**: Tự động ẩn sau 5 giây
- **Clickable**: Click để xem chi tiết payment
- **Responsive**: Hoạt động tốt trên mobile

### 2. Email Notifications

- **HTML Templates**: Email đẹp với template HTML
- **Responsive Design**: Hiển thị tốt trên mobile
- **Thông tin chi tiết**: Bao gồm thông tin booking, payment, contact
- **Error Handling**: Xử lý lỗi gracefully

### 3. API Endpoints

- **Authentication**: Yêu cầu đăng nhập
- **Authorization**: Kiểm tra quyền truy cập
- **Real-time**: Trả về dữ liệu real-time
- **Pagination**: Hỗ trợ phân trang

## Troubleshooting

### 1. Email không gửi được

- Kiểm tra cấu hình SMTP trong `.env`
- Đảm bảo sử dụng App Password cho Gmail
- Kiểm tra firewall/antivirus

### 2. Web notification không hiển thị

- Kiểm tra console browser có lỗi JavaScript không
- Đảm bảo user đã đăng nhập
- Kiểm tra network connection

### 3. API trả về lỗi

- Kiểm tra authentication
- Kiểm tra quyền truy cập
- Xem log server để debug

## Mở rộng

### 1. Thêm loại thông báo mới

```python
# Trong notification_service.py
def send_booking_confirmation_email(self, booking):
    # Logic gửi email xác nhận booking
    pass

def send_reminder_email(self, booking):
    # Logic gửi email nhắc nhở
    pass
```

### 2. Thêm notification channels

```python
# SMS notification
def send_sms_notification(self, phone, message):
    # Logic gửi SMS
    pass

# Push notification
def send_push_notification(self, user_id, message):
    # Logic gửi push notification
    pass
```

### 3. Tùy chỉnh template email

Tạo file template mới trong `templates/emails/` và cập nhật `EmailConfig.EMAIL_TEMPLATES`.

## Monitoring

### 1. Logs

Hệ thống ghi log chi tiết:
- Email sent/failed
- Web notification created
- API calls
- Errors

### 2. Metrics

Có thể thêm metrics để theo dõi:
- Số lượng email gửi thành công/thất bại
- Thời gian response của API
- Số lượng web notification hiển thị

## Security

### 1. Authentication

- Tất cả API endpoints yêu cầu đăng nhập
- Kiểm tra quyền truy cập dữ liệu

### 2. Rate Limiting

- Có thể thêm rate limiting cho API
- Giới hạn số lượng email gửi

### 3. Data Protection

- Không lưu mật khẩu email trong database
- Mã hóa thông tin nhạy cảm 