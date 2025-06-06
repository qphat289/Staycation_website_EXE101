# Hướng dẫn thiết lập Google Maps API Key

## Bước 1: Truy cập Google Cloud Console
1. Đi tới: https://console.cloud.google.com/
2. Đăng nhập bằng tài khoản Google của bạn

## Bước 2: Tạo hoặc chọn Project
1. Tạo project mới hoặc chọn project hiện có
2. Ghi nhớ tên project để theo dõi

## Bước 3: Enable APIs cần thiết
1. Đi tới **APIs & Services** > **Library**
2. Tìm và enable các API sau:
   - **Maps JavaScript API** (bắt buộc)
   - **Geocoding API** (bắt buộc) 
   - **Places API** (tùy chọn)

## Bước 4: Tạo API Key
1. Đi tới **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **API Key**
3. Copy API key được tạo

## Bước 5: Cấu hình API Key (Quan trọng!)
1. Click vào API key vừa tạo để edit
2. **Application restrictions**: 
   - Chọn **HTTP referrers (web sites)**
   - Thêm domain của bạn: 
     - `http://localhost:*/*` (cho development)
     - `http://127.0.0.1:*/*` (cho development)
     - `https://yourdomain.com/*` (cho production)

3. **API restrictions**:
   - Chọn **Restrict key**  
   - Chọn:
     - Maps JavaScript API
     - Geocoding API
     - Places API (nếu đã enable)

## Bước 6: Cập nhật code
1. Mở file `static/js/config.js`
2. Thay thế `'YOUR_NEW_API_KEY_HERE'` bằng API key mới:

```javascript
const CONFIG = {
    GOOGLE_MAPS_API_KEY: 'PASTE_YOUR_API_KEY_HERE',
    // ... rest of config
};
```

## Bước 7: Test
1. Khởi động lại ứng dụng
2. Reload trang room preview
3. Kiểm tra xem map có hiển thị không

## Lưu ý quan trọng:
- ⚠️ **Không commit API key lên git public**
- 💳 **Theo dõi quota usage để tránh bị charge**
- 🔒 **Luôn restrict API key theo domain**
- 📊 **Enable billing nếu cần (Google cung cấp $200 credit miễn phí/tháng)**

## Troubleshooting:
- Nếu map vẫn không hiển thị, kiểm tra Console (F12) để xem lỗi
- Đảm bảo billing account đã được setup
- Kiểm tra quota limits trong Cloud Console 