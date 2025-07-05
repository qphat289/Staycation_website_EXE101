# Hướng Dẫn Transfer - Hệ Thống Thanh Toán PayOS

## 🎯 Mục Tiêu

Tài liệu này hướng dẫn team members mới tiếp nhận và phát triển hệ thống thanh toán PayOS cho Staycation Website.

## 📋 Danh Sách Công Việc Đã Hoàn Thành

### ✅ Đã Hoàn Thành

1. **Tích hợp PayOS API**
   - ✅ Tạo PayOS service (`app/services/payos_service.py`)
   - ✅ Cấu hình credentials và encryption
   - ✅ Tạo payment links và QR codes

2. **Payment Routes & API**
   - ✅ Checkout page (`/payment/checkout/<booking_id>`)
   - ✅ Payment processing (`/payment/process_payment`)
   - ✅ Payment status page (`/payment/status/<payment_id>`)
   - ✅ Status refresh API (`/payment/refresh-status/<payment_id>`)

3. **Webhook System**
   - ✅ Webhook handler (`/webhook/payos`)
   - ✅ Signature verification
   - ✅ Payment status updates
   - ✅ Database synchronization

4. **Frontend Integration**
   - ✅ Payment status page với QR code
   - ✅ Auto-refresh polling (5 giây)
   - ✅ Real-time status updates
   - ✅ Success/failed redirects

5. **Notification System**
   - ✅ Email notifications (cấu hình sẵn)
   - ✅ Web notifications
   - ✅ Payment success alerts

6. **Security & Error Handling**
   - ✅ User authorization
   - ✅ Webhook signature verification
   - ✅ Data encryption
   - ✅ Error handling & logging

### 🔄 Cần Hoàn Thiện

1. **Email Configuration**
   - ⏳ Cấu hình SMTP settings
   - ⏳ Test email sending
   - ⏳ Email templates

2. **Production Deployment**
   - ⏳ SSL certificate
   - ⏳ Domain configuration
   - ⏳ Webhook URL setup

## 🚀 Hướng Dẫn Khởi Động

### 1. Setup Development Environment

```bash
# Clone repository
git clone <repository-url>
cd Staycation_website_EXE101

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env với PayOS credentials

# Initialize database
flask db upgrade

# Run development server
python app.py
```

### 2. Cấu Hình PayOS

1. **Đăng ký tài khoản PayOS**
   - Truy cập: https://business.payos.vn/
   - Tạo tài khoản merchant
   - Lấy Client ID, API Key, Checksum Key

2. **Cấu hình credentials**
   ```bash
   python scripts/setup_payos_credentials.py
   ```

3. **Test connection**
   ```bash
   python scripts/test_payos_connection.py
   ```

### 3. Test Payment Flow

1. **Tạo dữ liệu test**
   ```bash
   python scripts/create_test_data.py
   ```

2. **Test payment flow**
   - Truy cập: http://localhost:5000/payment/checkout/1
   - Tạo payment
   - Test QR code
   - Test webhook (cần ngrok cho local)

## 📁 Cấu Trúc Code Quan Trọng

### 1. Payment Models
```python
# app/models/models.py
class Payment(db.Model):
    # Payment records
    pass

class PaymentConfig(db.Model):
    # PayOS configuration per owner
    pass
```

### 2. Payment Routes
```python
# app/routes/payment.py
@payment_bp.route('/checkout/<int:booking_id>')
@payment_bp.route('/process_payment', methods=['POST'])
@payment_bp.route('/status/<int:payment_id>')
@payment_bp.route('/refresh-status/<int:payment_id>')
```

### 3. Webhook Handler
```python
# app/routes/webhook_handler.py
@webhook_bp.route('/webhook/payos', methods=['POST'])
def payos_webhook():
    # Xử lý webhook từ PayOS
    pass
```

### 4. PayOS Service
```python
# app/services/payos_service.py
class PayOSService:
    def create_payment_link(self, ...)
    def verify_webhook_signature(self, ...)
    def get_payment_info(self, ...)
```

## 🔧 Các Script Hữu Ích

### 1. Setup & Configuration
```bash
# Setup PayOS credentials
python scripts/setup_payos_credentials.py

# Test PayOS connection
python scripts/test_payos_connection.py

# Create test data
python scripts/create_test_data.py
```

### 2. Maintenance
```bash
# Cleanup temp files
python scripts/cleanup.py

# Check database
python scripts/check_existing_owners.py
```

### 3. Database Management
```bash
# Create migration
flask db migrate -m "Description"

# Apply migration
flask db upgrade

# Reset database
python scripts/db/recreate_db.py
```

## 🐛 Troubleshooting

### 1. Payment Không Tạo Được
```bash
# Kiểm tra PayOS credentials
python scripts/check_payos_credentials.py

# Kiểm tra logs
tail -f logs/payment.log
```

### 2. Webhook Không Hoạt Động
```bash
# Test webhook endpoint
curl -X POST http://localhost:5000/webhook/health

# Kiểm tra webhook logs
tail -f logs/webhook.log
```

### 3. QR Code Không Hiển Thị
```bash
# Test PayOS API
python scripts/test_payos_connection.py

# Kiểm tra network
curl -I https://api-merchant.payos.vn
```

## 📊 Monitoring & Logs

### 1. Log Files
- `logs/payment.log` - Payment processing logs
- `logs/webhook.log` - Webhook processing logs
- `logs/error.log` - Error logs

### 2. Database Queries
```sql
-- Xem payments
SELECT * FROM payment ORDER BY created_at DESC;

-- Xem payments pending
SELECT * FROM payment WHERE status = 'pending';

-- Xem payments thành công hôm nay
SELECT * FROM payment 
WHERE status = 'success' 
AND DATE(paid_at) = CURDATE();
```

### 3. Health Checks
```bash
# Payment system health
curl http://localhost:5000/webhook/health

# Database health
python -c "from app import app; from app.models.models import db; print('DB OK' if db.engine.execute('SELECT 1') else 'DB Error')"
```

## 🔄 Workflow Development

### 1. Feature Development
1. Tạo branch mới: `git checkout -b feature/payment-enhancement`
2. Implement feature
3. Test locally
4. Create pull request
5. Code review
6. Merge to main

### 2. Bug Fix
1. Tạo issue với description chi tiết
2. Reproduce bug
3. Fix và test
4. Update documentation
5. Deploy

### 3. Deployment
1. Test trên staging
2. Update production environment variables
3. Run database migrations
4. Deploy code
5. Monitor logs

## 📞 Liên Hệ & Support

### 1. Team Members
- **Tech Lead**: [tech-lead@company.com]
- **Backend Developer**: [backend@company.com]
- **Frontend Developer**: [frontend@company.com]

### 2. External Support
- **PayOS Support**: https://docs.payos.vn/
- **PayOS API Docs**: https://docs.payos.vn/api
- **PayOS Webhook Guide**: https://docs.payos.vn/webhook

### 3. Internal Resources
- **Project Repository**: [repository-url]
- **Documentation**: `docs/` folder
- **API Documentation**: `docs/PAYMENT_TECHNICAL_DOCS.md`

## 🎯 Next Steps

### 1. Immediate Tasks
- [ ] Cấu hình email SMTP
- [ ] Test email notifications
- [ ] Setup production domain
- [ ] Configure SSL certificate

### 2. Future Enhancements
- [ ] Payment analytics dashboard
- [ ] Multi-currency support
- [ ] Payment method selection
- [ ] Refund functionality
- [ ] Payment scheduling

### 3. Performance Optimization
- [ ] Implement caching
- [ ] Database indexing
- [ ] Async webhook processing
- [ ] CDN for static files

---

**Lưu ý**: 
- Luôn backup database trước khi deploy
- Test kỹ trên staging trước khi deploy production
- Monitor logs sau khi deploy
- Update documentation khi có thay đổi

**Chúc may mắn với dự án! 🚀** 