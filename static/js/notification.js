/**
 * Notification System - Xử lý thông báo real-time
 */
class NotificationSystem {
    constructor() {
        this.checkInterval = 10000; // 10 giây
        this.lastCheckTime = new Date().toISOString();
        this.isRunning = false;
        this.notificationContainer = null;
        this.init();
    }

    init() {
        // Tạo notification container nếu chưa có
        this.createNotificationContainer();
        
        // Bắt đầu kiểm tra thông báo
        this.startNotificationCheck();
        
        // Lắng nghe sự kiện visibility change
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopNotificationCheck();
            } else {
                this.startNotificationCheck();
            }
        });
    }

    createNotificationContainer() {
        // Kiểm tra xem container đã tồn tại chưa
        if (document.getElementById('notification-container')) {
            this.notificationContainer = document.getElementById('notification-container');
            return;
        }

        // Tạo notification container
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 400px;
            pointer-events: none;
        `;
        
        document.body.appendChild(container);
        this.notificationContainer = container;
    }

    startNotificationCheck() {
        if (this.isRunning) return;
        
        this.isRunning = true;
        this.checkNewNotifications();
        
        // Thiết lập interval
        this.intervalId = setInterval(() => {
            this.checkNewNotifications();
        }, this.checkInterval);
    }

    stopNotificationCheck() {
        this.isRunning = false;
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    async checkNewNotifications() {
        try {
            const response = await fetch('/api/notifications/check-new', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    last_check_time: this.lastCheckTime
                })
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            
            if (data.success && data.has_new) {
                // Hiển thị thông báo mới
                data.notifications.forEach(notification => {
                    this.showNotification(notification);
                });
                
                // Cập nhật thời gian kiểm tra cuối
                this.lastCheckTime = new Date().toISOString();
            }
        } catch (error) {
            console.error('Error checking notifications:', error);
        }
    }

    showNotification(notificationData) {
        const notification = this.createNotificationElement(notificationData);
        
        // Thêm vào container
        this.notificationContainer.appendChild(notification);
        
        // Hiển thị animation
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
            notification.style.opacity = '1';
        }, 100);
        
        // Tự động ẩn sau 5 giây
        setTimeout(() => {
            this.hideNotification(notification);
        }, 5000);
    }

    createNotificationElement(notificationData) {
        const notification = document.createElement('div');
        notification.className = 'notification-item';
        notification.style.cssText = `
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            transform: translateX(100%);
            opacity: 0;
            transition: all 0.3s ease;
            pointer-events: auto;
            cursor: pointer;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        `;

        // Tạo nội dung thông báo
        const icon = document.createElement('div');
        icon.innerHTML = '💰';
        icon.style.cssText = `
            font-size: 24px;
            margin-bottom: 8px;
        `;

        const title = document.createElement('div');
        title.textContent = 'Thanh toán thành công!';
        title.style.cssText = `
            font-weight: bold;
            font-size: 16px;
            margin-bottom: 5px;
        `;

        const message = document.createElement('div');
        message.textContent = notificationData.message;
        message.style.cssText = `
            font-size: 14px;
            opacity: 0.9;
            margin-bottom: 8px;
        `;

        const time = document.createElement('div');
        time.textContent = this.formatTime(notificationData.timestamp);
        time.style.cssText = `
            font-size: 12px;
            opacity: 0.7;
        `;

        // Thêm close button
        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '×';
        closeBtn.style.cssText = `
            position: absolute;
            top: 5px;
            right: 10px;
            background: none;
            border: none;
            color: white;
            font-size: 18px;
            cursor: pointer;
            opacity: 0.7;
            transition: opacity 0.2s;
        `;
        closeBtn.onmouseover = () => closeBtn.style.opacity = '1';
        closeBtn.onmouseout = () => closeBtn.style.opacity = '0.7';
        closeBtn.onclick = (e) => {
            e.stopPropagation();
            this.hideNotification(notification);
        };

        // Thêm các element vào notification
        notification.appendChild(closeBtn);
        notification.appendChild(icon);
        notification.appendChild(title);
        notification.appendChild(message);
        notification.appendChild(time);

        // Thêm click event để xem chi tiết
        notification.onclick = () => {
            this.handleNotificationClick(notificationData);
        };

        return notification;
    }

    hideNotification(notification) {
        notification.style.transform = 'translateX(100%)';
        notification.style.opacity = '0';
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }

    handleNotificationClick(notificationData) {
        // Xử lý khi click vào thông báo
        if (notificationData.type === 'payment_success') {
            // Chuyển hướng đến trang chi tiết payment
            window.location.href = `/payment/status/${notificationData.payment_id}`;
        }
    }

    formatTime(timestamp) {
        if (!timestamp) return 'Vừa xong';
        
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) { // < 1 phút
            return 'Vừa xong';
        } else if (diff < 3600000) { // < 1 giờ
            const minutes = Math.floor(diff / 60000);
            return `${minutes} phút trước`;
        } else if (diff < 86400000) { // < 1 ngày
            const hours = Math.floor(diff / 3600000);
            return `${hours} giờ trước`;
        } else {
            return date.toLocaleDateString('vi-VN');
        }
    }

    // Phương thức để hiển thị thông báo tùy chỉnh
    showCustomNotification(message, type = 'success', duration = 5000) {
        const notificationData = {
            type: 'custom',
            message: message,
            timestamp: new Date().toISOString()
        };

        const notification = this.createNotificationElement(notificationData);
        
        // Thay đổi màu sắc theo type
        if (type === 'error') {
            notification.style.background = 'linear-gradient(135deg, #dc3545, #c82333)';
        } else if (type === 'warning') {
            notification.style.background = 'linear-gradient(135deg, #ffc107, #e0a800)';
        } else if (type === 'info') {
            notification.style.background = 'linear-gradient(135deg, #17a2b8, #138496)';
        }

        this.notificationContainer.appendChild(notification);
        
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
            notification.style.opacity = '1';
        }, 100);
        
        setTimeout(() => {
            this.hideNotification(notification);
        }, duration);
    }
}

// Khởi tạo notification system khi trang load
document.addEventListener('DOMContentLoaded', function() {
    // Chỉ khởi tạo nếu user đã đăng nhập
    if (document.body.classList.contains('logged-in') || 
        document.querySelector('[data-user-id]') ||
        window.currentUser) {
        window.notificationSystem = new NotificationSystem();
    }
});

// Export cho sử dụng global
window.NotificationSystem = NotificationSystem; 