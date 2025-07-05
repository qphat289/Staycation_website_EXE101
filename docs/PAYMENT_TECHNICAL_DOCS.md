# Tài Liệu Kỹ Thuật - Hệ Thống Thanh Toán PayOS

## 📚 Mục Lục

1. [Kiến Trúc Hệ Thống](#kiến-trúc-hệ-thống)
2. [Database Schema](#database-schema)
3. [API Documentation](#api-documentation)
4. [Webhook Implementation](#webhook-implementation)
5. [Frontend Integration](#frontend-integration)
6. [Security Implementation](#security-implementation)
7. [Error Handling](#error-handling)
8. [Testing Strategy](#testing-strategy)
9. [Deployment Guide](#deployment-guide)

## 🏗️ Kiến Trúc Hệ Thống

### 1. Component Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   External      │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │Payment Status│ │◄──►│ │Payment Routes│ │    │ │   PayOS     │ │
│ │Page          │ │    │ │             │ │    │ │   API       │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │QR Code      │ │◄──►│ │PayOS Service│ │◄──►│ │   Webhook   │ │
│ │Display      │ │    │ │             │ │    │ │   Callback  │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │Notification │ │◄──►│ │Notification │ │    │ │   Email     │ │
│ │System       │ │    │ │Service      │ │◄──►│ │   Service   │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 2. Data Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant P as PayOS
    participant DB as Database
    participant E as Email

    U->>F: Đặt phòng
    F->>B: POST /payment/process_payment
    B->>P: Create Payment Link
    P->>B: Return QR + Link
    B->>DB: Save Payment Record
    B->>F: Redirect to /payment/status
    
    loop Polling every 5s
        F->>B: GET /payment/refresh-status
        B->>DB: Check Status
        B->>F: Return Status
    end
    
    U->>P: Complete Payment
    P->>B: POST /webhook/payos
    B->>DB: Update Status
    B->>E: Send Email
    B->>F: Next Poll Returns Success
    F->>U: Show Success Page
```

## 🗄️ Database Schema

### 1. Payment Table

```sql
CREATE TABLE payment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_code VARCHAR(100) UNIQUE NOT NULL,
    order_code VARCHAR(100) UNIQUE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'VND',
    
    -- PayOS Integration
    payos_transaction_id VARCHAR(100),
    payos_signature TEXT,
    checkout_url VARCHAR(500),
    
    -- Status & Timing
    status VARCHAR(20) DEFAULT 'pending',
    payment_method VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP,
    
    -- Customer Info
    description TEXT,
    customer_name VARCHAR(100),
    customer_email VARCHAR(120),
    customer_phone VARCHAR(20),
    
    -- Foreign Keys
    booking_id INTEGER NOT NULL,
    owner_id INTEGER NOT NULL,
    renter_id INTEGER NOT NULL,
    
    FOREIGN KEY (booking_id) REFERENCES booking(id),
    FOREIGN KEY (owner_id) REFERENCES owner(id),
    FOREIGN KEY (renter_id) REFERENCES renter(id)
);
```

### 2. PaymentConfig Table

```sql
CREATE TABLE payment_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER UNIQUE NOT NULL,
    
    -- Encrypted PayOS Credentials
    payos_client_id VARCHAR(100) NOT NULL,
    payos_api_key VARCHAR(200) NOT NULL,
    payos_checksum_key VARCHAR(200) NOT NULL,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (owner_id) REFERENCES owner(id)
);
```

### 3. Indexes

```sql
-- Performance indexes
CREATE INDEX idx_payment_status ON payment(status);
CREATE INDEX idx_payment_order_code ON payment(order_code);
CREATE INDEX idx_payment_booking_id ON payment(booking_id);
CREATE INDEX idx_payment_created_at ON payment(created_at);
CREATE INDEX idx_payment_owner_id ON payment(owner_id);
CREATE INDEX idx_payment_renter_id ON payment(renter_id);

-- Composite indexes
CREATE INDEX idx_payment_status_created ON payment(status, created_at);
CREATE INDEX idx_payment_owner_status ON payment(owner_id, status);
```

## 🔌 API Documentation

### 1. Payment Routes

#### POST /payment/process_payment

**Request:**
```json
{
    "booking_id": 123,
    "amount": 500000,
    "description": "Booking #123"
}
```

**Response:**
```json
{
    "success": true,
    "payment_id": 456,
    "redirect_url": "/payment/status/456"
}
```

#### GET /payment/status/{payment_id}

**Response:**
```json
{
    "payment": {
        "id": 456,
        "payment_code": "PAY-ABC123",
        "amount": 500000,
        "status": "pending",
        "checkout_url": "https://payos.vn/checkout/...",
        "qr_code": "data:image/png;base64,..."
    },
    "booking": {
        "id": 123,
        "room_title": "Phòng Deluxe",
        "start_time": "2024-01-15T14:00:00Z",
        "end_time": "2024-01-15T17:00:00Z"
    }
}
```

#### GET /payment/refresh-status/{payment_id}

**Response:**
```json
{
    "status": "success",
    "message": "Payment completed successfully",
    "payment_status": "success",
    "redirect": "/payment/success/456"
}
```

### 2. Webhook Endpoints

#### POST /webhook/payos

**Request Headers:**
```
Content-Type: application/json
x-signature: HMAC_SHA256_SIGNATURE
```

**Request Body:**
```json
{
    "orderCode": "123456789",
    "status": "PAID",
    "transId": "TXN123456",
    "paymentMethod": "bank_transfer",
    "amount": 500000,
    "currency": "VND"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Webhook processed successfully",
    "order_code": "123456789",
    "status": "PAID"
}
```

## 🔗 Webhook Implementation

### 1. Signature Verification

```python
def verify_webhook_signature(data, received_signature):
    """
    Xác thực chữ ký webhook từ PayOS
    """
    # Tạo chữ ký từ data
    data_string = json.dumps(data, separators=(',', ':'))
    expected_signature = hmac.new(
        self.checksum_key.encode('utf-8'),
        data_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, received_signature)
```

### 2. Webhook Processing

```python
@webhook_bp.route('/webhook/payos', methods=['POST'])
def payos_webhook():
    try:
        # 1. Validate request
        data = request.get_json()
        signature = request.headers.get('x-signature')
        
        if not verify_signature(data, signature):
            return jsonify({"error": "Invalid signature"}), 400
        
        # 2. Find payment
        payment = Payment.query.filter_by(
            order_code=data['orderCode']
        ).first()
        
        if not payment:
            return jsonify({"error": "Payment not found"}), 404
        
        # 3. Update status
        if data['status'] == 'PAID':
            payment.mark_as_successful(
                payos_transaction_id=data.get('transId'),
                payment_method=data.get('paymentMethod')
            )
            payment.booking.payment_status = 'paid'
            payment.booking.status = 'confirmed'
            
            # 4. Send notifications
            notification_service.send_payment_success_email(payment)
            notification_service.create_web_notification(payment)
        
        db.session.commit()
        
        return jsonify({"success": True})
        
    except Exception as e:
        current_app.logger.error(f"Webhook error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
```

## 🎨 Frontend Integration

### 1. Payment Status Page

```javascript
// Auto-refresh payment status
function startAutoRefresh() {
    refreshInterval = setInterval(function() {
        checkPaymentStatus();
    }, 5000); // 5 seconds
}

function checkPaymentStatus() {
    fetch(PAYMENT_DATA.checkStatusUrl)
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showSuccessMessage();
            setTimeout(() => {
                window.location.href = data.redirect;
            }, 1500);
        } else if (data.status === 'failed') {
            showFailedMessage();
            setTimeout(() => {
                window.location.href = data.redirect;
            }, 2000);
        }
    })
    .catch(error => {
        console.error('Status check error:', error);
    });
}
```

### 2. QR Code Display

```javascript
// Load QR code from API
function loadQRCode() {
    fetch(PAYMENT_DATA.getQrUrl)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayQRCode(data.qr_code);
            displayBankInfo(data.account_info);
        } else {
            showError('Không thể tải mã QR');
        }
    })
    .catch(error => {
        showError('Lỗi khi tải mã QR: ' + error.message);
    });
}
```

### 3. Notification System

```javascript
// Real-time notifications
function initNotificationSystem() {
    setInterval(function() {
        checkNewNotifications();
    }, 10000); // 10 seconds
}

function checkNewNotifications() {
    fetch('/api/notifications/check')
    .then(response => response.json())
    .then(data => {
        if (data.has_new) {
            showNotification(data.notifications);
        }
    });
}
```

## 🔒 Security Implementation

### 1. Data Encryption

```python
from cryptography.fernet import Fernet
import base64

class EncryptionService:
    def __init__(self):
        self.key = os.environ.get('ENCRYPTION_KEY')
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data):
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data):
        return self.cipher.decrypt(encrypted_data.encode()).decode()

# Usage in PaymentConfig
@property
def payos_api_key(self):
    return encryption_service.decrypt(self._payos_api_key)

@payos_api_key.setter
def payos_api_key(self, value):
    self._payos_api_key = encryption_service.encrypt(value)
```

### 2. User Authorization

```python
@payment_bp.route('/status/<int:payment_id>')
@login_required
def payment_status(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    
    # Check ownership
    if payment.renter_id != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('renter.dashboard'))
    
    return render_template('payment/payment_status.html', payment=payment)
```

### 3. Rate Limiting

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@payment_bp.route('/refresh-status/<int:payment_id>')
@limiter.limit("10 per minute")
@login_required
def refresh_payment_status(payment_id):
    # Implementation
    pass
```

## ⚠️ Error Handling

### 1. Payment Errors

```python
class PaymentError(Exception):
    """Base exception for payment errors"""
    pass

class PayOSConnectionError(PaymentError):
    """PayOS API connection error"""
    pass

class PaymentValidationError(PaymentError):
    """Payment validation error"""
    pass

def handle_payment_error(error):
    """Global error handler for payment errors"""
    if isinstance(error, PayOSConnectionError):
        return jsonify({
            'error': 'PayOS service unavailable',
            'code': 'PAYOS_CONNECTION_ERROR'
        }), 503
    elif isinstance(error, PaymentValidationError):
        return jsonify({
            'error': str(error),
            'code': 'VALIDATION_ERROR'
        }), 400
    else:
        return jsonify({
            'error': 'Internal payment error',
            'code': 'INTERNAL_ERROR'
        }), 500
```

### 2. Webhook Error Handling

```python
def process_webhook_safely(data):
    """Safely process webhook with retry logic"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            return process_webhook(data)
        except Exception as e:
            retry_count += 1
            current_app.logger.error(
                f"Webhook processing error (attempt {retry_count}): {str(e)}"
            )
            
            if retry_count >= max_retries:
                # Log to external monitoring service
                log_critical_error('webhook_processing_failed', {
                    'data': data,
                    'error': str(e),
                    'retry_count': retry_count
                })
                raise
            else:
                time.sleep(2 ** retry_count)  # Exponential backoff
```

### 3. Frontend Error Handling

```javascript
// Global error handler
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    
    // Show user-friendly error message
    showNotification('error', 'Có lỗi xảy ra. Vui lòng thử lại.');
    
    // Log to monitoring service
    logError('unhandled_promise_rejection', {
        reason: event.reason,
        url: window.location.href,
        timestamp: new Date().toISOString()
    });
});

// API error interceptor
function handleApiError(response) {
    if (!response.ok) {
        const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
        error.status = response.status;
        error.response = response;
        throw error;
    }
    return response;
}
```

## 🧪 Testing Strategy

### 1. Unit Tests

```python
import unittest
from unittest.mock import patch, MagicMock

class TestPaymentService(unittest.TestCase):
    
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    @patch('app.services.payos_service.PayOSService')
    def test_create_payment_success(self, mock_payos):
        # Arrange
        mock_payos.return_value.create_payment_link.return_value = {
            'success': True,
            'checkout_url': 'https://payos.vn/checkout/123',
            'qrCode': 'data:image/png;base64,...'
        }
        
        # Act
        response = self.client.post('/payment/process_payment', json={
            'booking_id': 1,
            'amount': 100000
        })
        
        # Assert
        self.assertEqual(response.status_code, 302)
        self.assertIn('/payment/status/', response.location)
    
    def test_payment_authorization(self):
        # Test that users can only access their own payments
        pass
    
    def test_webhook_signature_verification(self):
        # Test webhook security
        pass
```

### 2. Integration Tests

```python
class TestPaymentFlow(unittest.TestCase):
    
    def test_complete_payment_flow(self):
        """Test complete payment flow from booking to success"""
        
        # 1. Create booking
        booking = self.create_test_booking()
        
        # 2. Process payment
        payment_response = self.client.post('/payment/process_payment', json={
            'booking_id': booking.id
        })
        
        # 3. Simulate webhook
        payment = Payment.query.filter_by(booking_id=booking.id).first()
        webhook_data = {
            'orderCode': payment.order_code,
            'status': 'PAID',
            'transId': 'TEST123'
        }
        
        webhook_response = self.client.post('/webhook/payos', json=webhook_data)
        
        # 4. Verify final state
        self.assertEqual(webhook_response.status_code, 200)
        
        payment.refresh()
        self.assertEqual(payment.status, 'success')
        self.assertEqual(booking.payment_status, 'paid')
```

### 3. Load Testing

```python
import locust

class PaymentLoadTest(locust.HttpUser):
    
    @locust.task(3)
    def test_payment_status_page(self):
        """Test payment status page load"""
        self.client.get("/payment/status/1")
    
    @locust.task(1)
    def test_webhook_processing(self):
        """Test webhook processing under load"""
        webhook_data = {
            'orderCode': '123456',
            'status': 'PAID',
            'transId': 'TXN123'
        }
        self.client.post("/webhook/payos", json=webhook_data)
```

## 🚀 Deployment Guide

### 1. Production Environment

```bash
# Environment variables
export FLASK_ENV=production
export FLASK_DEBUG=0
export DATABASE_URL=mysql://user:pass@host/db
export PAYOS_CLIENT_ID=your_production_client_id
export PAYOS_API_KEY=your_production_api_key
export PAYOS_CHECKSUM_KEY=your_production_checksum_key
export ENCRYPTION_KEY=your_32_byte_encryption_key

# Install dependencies
pip install -r requirements.txt

# Run migrations
flask db upgrade

# Start application
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 2. Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### 3. Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /webhook/ {
        # Webhook endpoints need special handling
        proxy_pass http://127.0.0.1:5000;
        proxy_read_timeout 30s;
        proxy_connect_timeout 30s;
    }
}
```

### 4. SSL Configuration

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 Monitoring & Analytics

### 1. Key Metrics

```python
# Payment success rate
def calculate_success_rate():
    total_payments = Payment.query.count()
    successful_payments = Payment.query.filter_by(status='success').count()
    return (successful_payments / total_payments) * 100 if total_payments > 0 else 0

# Average processing time
def calculate_avg_processing_time():
    successful_payments = Payment.query.filter_by(status='success').all()
    if not successful_payments:
        return 0
    
    total_time = sum([
        (p.paid_at - p.created_at).total_seconds() 
        for p in successful_payments 
        if p.paid_at and p.created_at
    ])
    return total_time / len(successful_payments)
```

### 2. Health Checks

```python
@app.route('/health/payment')
def payment_health_check():
    """Health check for payment system"""
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        
        # Check PayOS connection
        payos_service = PayOSService()
        payos_service.test_connection()
        
        # Check webhook endpoint
        webhook_url = url_for('webhook.webhook_health', _external=True)
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'payos_api': 'connected',
            'webhook_endpoint': webhook_url,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500
```

---

**Tài liệu này được cập nhật lần cuối**: 2024-01-15
**Phiên bản**: 1.0.0
**Tác giả**: Development Team 