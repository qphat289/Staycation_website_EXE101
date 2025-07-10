# Hướng Dẫn Cấu Hình Email cho Verify OTP

## 🔧 Cấu Hình Gmail

### Bước 1: Bật 2-Factor Authentication
1. Đăng nhập vào Google Account
2. Vào **Security** → **2-Step Verification**
3. Bật **2-Step Verification**

### Bước 2: Tạo App Password
1. Vào **Security** → **App passwords**
2. Chọn **Mail** và **Other (Custom name)**
3. Đặt tên: `Staycation Email Service`
4. Copy App Password (16 ký tự)

### Bước 3: Cấu Hình Environment
Tạo file `.env` trong thư mục gốc:

```env
# Email Configuration
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-16-char-app-password
```

**Lưu ý quan trọng:**
- Không dùng mật khẩu Gmail thường
- Chỉ dùng App Password
- Không commit file `.env` vào git

## 🧪 Test Cấu Hình

### Chạy Script Test
```bash
python scripts/test_email_config.py
```

### Kết Quả Mong Đợi
```
=== CHECK ENVIRONMENT CONFIG ===
✅ File .env tồn tại
✅ EMAIL_USERNAME được cấu hình
✅ EMAIL_PASSWORD được cấu hình

Environment variables:
   - EMAIL_USERNAME: your-email@gmail.com
   - EMAIL_PASSWORD: ****************

=== TEST EMAIL CONFIGURATION ===
1. Kiểm tra cấu hình email:
   - Sender Email: your-email@gmail.com
   - Sender Password: ****************

2. Test tạo OTP:
   - OTP generated: 123456
   - Length: 6
   - Is numeric: True

3. Test tạo token bảo mật:
   - Secure token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
   - Verified OTP: 123456
   - Token valid: True

4. Test gửi email:
   ✅ Email sent successfully!
```

## 🚨 Troubleshooting

### Lỗi 1: SMTP Authentication failed
```
❌ SMTP Authentication failed: (535, b'5.7.8 Username and Password not accepted')
```

**Nguyên nhân:** Sử dụng mật khẩu Gmail thường thay vì App Password

**Giải pháp:**
1. Tạo App Password mới
2. Cập nhật EMAIL_PASSWORD trong .env
3. Restart ứng dụng

### Lỗi 2: Less secure app access
```
❌ SMTP Authentication failed: (534, b'5.7.9 Application-specific password required')
```

**Nguyên nhân:** Gmail yêu cầu App Password

**Giải pháp:**
1. Bật 2-Factor Authentication
2. Tạo App Password
3. Sử dụng App Password

### Lỗi 3: Connection timeout
```
❌ Failed to send email: [Errno 11001] getaddrinfo failed
```

**Nguyên nhân:** Lỗi kết nối mạng hoặc firewall

**Giải pháp:**
1. Kiểm tra kết nối internet
2. Tắt firewall tạm thời
3. Thử lại

### Lỗi 4: Rate limit exceeded
```
❌ SMTP error: 550 5.7.1 Too many login attempts
```

**Nguyên nhân:** Gửi quá nhiều email trong thời gian ngắn

**Giải pháp:**
1. Đợi 1-2 giờ
2. Giảm tần suất gửi email
3. Sử dụng email khác

## 📧 Cấu Hình Email Khác

### Outlook/Hotmail
```python
# Trong email_service.py
self.smtp_server = "smtp-mail.outlook.com"
self.smtp_port = 587
```

### Yahoo Mail
```python
# Trong email_service.py
self.smtp_server = "smtp.mail.yahoo.com"
self.smtp_port = 587
```

### Custom SMTP Server
```python
# Trong email_service.py
self.smtp_server = "your-smtp-server.com"
self.smtp_port = 587  # hoặc 465 cho SSL
```

## 🔒 Bảo Mật

### Best Practices
1. **App Password**: Luôn dùng App Password, không dùng mật khẩu chính
2. **Environment Variables**: Không hardcode credentials trong code
3. **Rate Limiting**: Giới hạn số lần gửi email
4. **Token Encryption**: Mã hóa OTP token
5. **Session Security**: Lưu OTP trong session với thời gian hết hạn

### Production Deployment
1. **Email Service**: Sử dụng SendGrid, Mailgun, AWS SES
2. **Queue System**: Sử dụng Redis/Celery cho email queue
3. **Monitoring**: Theo dõi tỷ lệ gửi email thành công
4. **Backup**: Có phương án backup khi email service fail

## 📋 Checklist

### Trước Khi Deploy
- [ ] Tạo App Password cho Gmail
- [ ] Cấu hình EMAIL_USERNAME và EMAIL_PASSWORD
- [ ] Test gửi email thành công
- [ ] Kiểm tra rate limiting
- [ ] Test các edge cases

### Sau Khi Deploy
- [ ] Monitor email delivery rate
- [ ] Kiểm tra logs cho lỗi SMTP
- [ ] Test verify email flow end-to-end
- [ ] Backup email configuration

## 🆘 Support

Nếu gặp vấn đề:
1. Chạy `python scripts/test_email_config.py`
2. Kiểm tra logs trong console
3. Verify cấu hình .env
4. Test với email thật
5. Kiểm tra firewall/network

---

**Lưu ý:** Đảm bảo cấu hình email đúng trước khi test tính năng verify email! 🔧 