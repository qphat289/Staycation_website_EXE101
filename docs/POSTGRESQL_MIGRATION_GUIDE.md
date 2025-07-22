# Hướng dẫn di chuyển dữ liệu từ SQLite sang PostgreSQL

## Vấn đề hiện tại
Khi di chuyển dữ liệu từ SQLite sang PostgreSQL, có một số khác biệt về kiểu dữ liệu cần được xử lý:

1. **Vấn đề kiểu dữ liệu Boolean**: 
   - SQLite lưu trữ boolean dưới dạng integer (0/1)
   - PostgreSQL yêu cầu kiểu boolean thực (TRUE/FALSE)

2. **Vấn đề độ dài chuỗi**:
   - Một số trường như `password_hash` có độ dài vượt quá giới hạn (128) trong schema

## Các bước khắc phục

### 1. Cập nhật các mô hình
Đã cập nhật các mô hình với trường `password_hash` từ 128 lên 255 ký tự:
- `Admin.password_hash`: String(255)
- `Owner.password_hash`: String(255)
- `Renter.password_hash`: String(255)

### 2. Di chuyển dữ liệu với script cải tiến
Sử dụng script `migrate_improved.py` để di chuyển dữ liệu, script này sẽ:
- Tự động chuyển đổi số nguyên (0/1) thành boolean (TRUE/FALSE)
- Xử lý các lỗi ngoại lệ và tiếp tục di chuyển
- Đảm bảo thứ tự chèn dữ liệu chính xác để tránh lỗi khóa ngoại

### 3. Cách sử dụng

#### Thiết lập môi trường
1. Đảm bảo biến môi trường `DATABASE_URL` đã được cấu hình chính xác:
```
DATABASE_URL=postgresql://username:password@localhost:5432/homestay
```

#### Thực hiện di chuyển
1. **Reset database** (Nếu cần):
```
python scripts/fix_postgres_migration.py
```

2. **Khởi động ứng dụng** để tạo schema mới:
```
python app.py
```

3. **Di chuyển dữ liệu** với script cải tiến:
```
python scripts/migrate_improved.py
```

4. **Kiểm tra kết quả**:
```
python app.py
```

## Xử lý lỗi phổ biến

### Lỗi kiểu dữ liệu boolean
Nếu vẫn gặp lỗi về kiểu dữ liệu boolean, có thể sửa trực tiếp trong cơ sở dữ liệu:

```sql
UPDATE table_name 
SET boolean_column = 'TRUE' 
WHERE boolean_column = 1;

UPDATE table_name 
SET boolean_column = 'FALSE' 
WHERE boolean_column = 0;
```

### Lỗi khóa ngoại
Trong quá trình di chuyển, một số bảng như `booking` và `review` có thể gặp lỗi khóa ngoại. Nguyên nhân là dữ liệu tham chiếu chưa được insert đúng.

Giải pháp:
1. Tạm thời vô hiệu hóa ràng buộc khóa ngoại:
```sql
SET session_replication_role = 'replica';
-- Thực hiện các thao tác insert
SET session_replication_role = 'origin';
```

2. Hoặc đảm bảo thứ tự insert đúng, từ bảng chính đến bảng phụ thuộc.
