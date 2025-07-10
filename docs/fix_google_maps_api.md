# Hướng dẫn sửa lỗi Google Maps API

## Vấn đề hiện tại:
- API key không được ủy quyền sử dụng Maps JavaScript API
- Geocoding API bị từ chối quyền truy cập
- Bản đồ không hiển thị được

## Cách khắc phục:

### Bước 1: Kích hoạt APIs cần thiết
1. Vào [Google Cloud Console](https://console.cloud.google.com/)
2. Chọn project của bạn
3. Vào **APIs & Services** > **Library**
4. Tìm và kích hoạt các API sau:
   - **Maps JavaScript API**
   - **Geocoding API**
   - **Places API** (nếu cần)

### Bước 2: Kiểm tra API Key
1. Vào **APIs & Services** > **Credentials**
2. Chọn API key của bạn
3. Trong **API restrictions**, đảm bảo đã chọn:
   - Maps JavaScript API
   - Geocoding API

### Bước 3: Thiết lập Billing
1. Vào **Billing** trong Google Cloud Console
2. Đảm bảo có payment method hợp lệ
3. APIs này cần billing account để hoạt động

### Bước 4: Kiểm tra Application Restrictions
1. Trong API key settings
2. **Application restrictions** chọn:
   - **HTTP referrers (web sites)**
   - Thêm: `http://localhost:5000/*` và `http://127.0.0.1:5000/*`

### Bước 5: Đợi propagation
- Sau khi thay đổi, đợi 5-10 phút để các thay đổi có hiệu lực

## Test API Key:
Sau khi hoàn thành, test tại: `http://localhost:5000/test-map`

## Nếu vẫn lỗi:
1. Kiểm tra browser console (F12)
2. Tắt ad blocker
3. Thử với trình duyệt khác
4. Kiểm tra network connectivity 