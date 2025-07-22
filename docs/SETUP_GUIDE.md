# HƯỚNG DẪN THIẾT LẬP VÀ CHẠY ỨNG DỤNG STAYCATION

Tài liệu này cung cấp hướng dẫn chi tiết để thiết lập và chạy ứng dụng Staycation trên máy mới. Bạn có thể lựa chọn giữa sử dụng SQLite (đơn giản hơn) hoặc PostgreSQL (mạnh mẽ hơn cho môi trường production).

## MỤC LỤC

1. [Yêu cầu hệ thống](#1-yêu-cầu-hệ-thống)
2. [Cài đặt môi trường Python](#2-cài-đặt-môi-trường-python)
3. [Tải về và chuẩn bị dự án](#3-tải-về-và-chuẩn-bị-dự-án)
4. [Cấu hình cơ sở dữ liệu](#4-cấu-hình-cơ-sở-dữ-liệu)
   - [4.1. Sử dụng SQLite (Đơn giản)](#41-sử-dụng-sqlite-đơn-giản)
   - [4.2. Sử dụng PostgreSQL](#42-sử-dụng-postgresql)
5. [Chạy ứng dụng](#5-chạy-ứng-dụng)
6. [Chuyển đổi giữa SQLite và PostgreSQL](#6-chuyển-đổi-giữa-sqlite-và-postgresql)
7. [Xử lý sự cố thường gặp](#7-xử-lý-sự-cố-thường-gặp)

## 1. YÊU CẦU HỆ THỐNG

- Python 3.8 trở lên
- pip (Trình quản lý gói Python)
- Git (để clone dự án)
- PostgreSQL (nếu sử dụng PostgreSQL)

## 2. CÀI ĐẶT MÔI TRƯỜNG PYTHON

### Windows

1. Tải xuống và cài đặt Python từ [python.org](https://www.python.org/downloads/)
2. Đảm bảo chọn "Add Python to PATH" trong quá trình cài đặt
3. Mở Command Prompt hoặc PowerShell để kiểm tra cài đặt:
   ```
   python --version
   pip --version
   ```

### macOS/Linux

1. Cài đặt Python sử dụng trình quản lý gói hệ thống hoặc pyenv:
   ```
   # macOS (sử dụng Homebrew)
   brew install python

   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3 python3-pip
   ```

2. Kiểm tra cài đặt:
   ```
   python3 --version
   pip3 --version
   ```

## 3. TẢI VỀ VÀ CHUẨN BỊ DỰ ÁN

1. Clone dự án từ repository (hoặc tải xuống dưới dạng ZIP và giải nén):
   ```
   git clone <repository_url>
   cd Staycation_website_EXE101-main
   ```

2. Tạo và kích hoạt môi trường ảo Python:

   **Windows:**
   ```
   python -m venv venv
   venv\Scripts\activate
   ```

   **macOS/Linux:**
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Cài đặt các thư viện phụ thuộc:

   **Cho SQLite:**
   ```
   pip install -r requirements.txt
   ```

   **Cho PostgreSQL:**
   ```
   pip install -r requirements_postgres.txt
   ```

## 4. CẤU HÌNH CƠ SỞ DỮ LIỆU

### 4.1. SỬ DỤNG SQLITE (ĐƠN GIẢN)

SQLite không yêu cầu cài đặt server riêng, dữ liệu được lưu trong file `instance/homestay.db`.

1. Chỉnh sửa file `config/config.py` để sử dụng SQLite:

   ```python
   # Mở file config/config.py và chỉnh sửa dòng SQLALCHEMY_DATABASE_URI
   # Comment dòng cấu hình PostgreSQL
   # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/homestay')
   
   # Bỏ comment dòng cấu hình SQLite
   SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "instance", "homestay.db")}'
   ```

2. Kiểm tra file `.env` và đảm bảo rằng biến `DATABASE_URL` được comment lại (nếu có):

   ```
   # DATABASE_URL=postgresql://postgres:password@localhost:5432/homestay
   ```

3. Khởi tạo cơ sở dữ liệu và chạy migration:

   ```
   flask db upgrade
   ```

### 4.2. SỬ DỤNG POSTGRESQL

PostgreSQL mạnh mẽ hơn cho môi trường production và làm việc đồng thời.

1. Cài đặt PostgreSQL:

   **Windows:**
   - Tải và cài đặt từ [postgresql.org](https://www.postgresql.org/download/windows/)
   - Ghi nhớ password đã đặt cho user postgres

   **macOS:**
   ```
   brew install postgresql
   brew services start postgresql
   ```

   **Ubuntu/Debian:**
   ```
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   ```

2. Tạo cơ sở dữ liệu và người dùng PostgreSQL:

   ```
   # Đăng nhập vào PostgreSQL
   sudo -u postgres psql  # Linux/macOS
   # hoặc sử dụng pgAdmin trên Windows

   # Tạo cơ sở dữ liệu và cấp quyền
   CREATE DATABASE homestay;
   CREATE USER myuser WITH ENCRYPTED PASSWORD 'mypassword';
   GRANT ALL PRIVILEGES ON DATABASE homestay TO myuser;
   \q
   ```

3. Chỉnh sửa file `config/config.py` để sử dụng PostgreSQL:

   ```python
   # Mở file config/config.py và chỉnh sửa dòng SQLALCHEMY_DATABASE_URI
   # Bỏ comment dòng cấu hình PostgreSQL và cập nhật thông tin kết nối
   SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://postgres:mypassword@localhost:5432/homestay')
   
   # Comment dòng cấu hình SQLite
   # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "instance", "homestay.db")}'
   ```

4. Thêm biến môi trường vào file `.env`:

   ```
   DATABASE_URL=postgresql://postgres:mypassword@localhost:5432/homestay
   ```

5. Khởi tạo cơ sở dữ liệu và chạy migration:

   ```
   flask db upgrade
   ```

## 5. CHẠY ỨNG DỤNG

1. Sau khi cấu hình cơ sở dữ liệu, chạy ứng dụng:

   ```
   python app.py
   ```

2. Truy cập ứng dụng trong trình duyệt tại địa chỉ:
   ```
   http://localhost:5000
   ```

3. Đăng nhập với tài khoản admin mặc định (nếu là lần đầu chạy):
   - Username: `admin`
   - Password: `123`

## 6. CHUYỂN ĐỔI GIỮA SQLITE VÀ POSTGRESQL

### Từ SQLite sang PostgreSQL

1. Đảm bảo đã cài đặt PostgreSQL và tạo cơ sở dữ liệu như hướng dẫn ở mục 4.2
2. Sử dụng script hỗ trợ chuyển đổi:
   ```
   python switch_to_postgres.py [username] [password] [host] [database]
   ```
   Ví dụ: `python switch_to_postgres.py postgres mypassword localhost homestay`
3. Chạy migration để tạo cấu trúc bảng trong PostgreSQL:
   ```
   flask db upgrade
   ```
4. Để di chuyển dữ liệu từ SQLite sang PostgreSQL, bạn có thể sử dụng script:
   ```
   python scripts/migrate_sqlite_to_postgres.py
   ```
5. Nếu gặp lỗi trong quá trình chuyển đổi (ví dụ: lỗi boolean type hoặc kích thước trường), sử dụng script sửa lỗi:
   ```
   python scripts/fix_postgres_migration.py
   ```

### Từ PostgreSQL sang SQLite

1. Sử dụng script hỗ trợ chuyển đổi:
   ```
   python switch_to_sqlite.py
   ```
   Script này sẽ tự động chỉnh sửa file `config/config.py` và comment biến `DATABASE_URL` trong file `.env`

2. Chạy migration để tạo cấu trúc bảng trong SQLite:
   ```
   flask db upgrade
   ```

3. Để di chuyển dữ liệu từ PostgreSQL sang SQLite, bạn có thể sử dụng script:
   ```
   python scripts/migrate_postgres_to_sqlite.py
   ```

4. Kiểm tra kết nối để xác nhận đã chuyển thành công:
   ```
   python check_database_connection.py
   ```

## 7. XỬ LÝ SỰ CỐ THƯỜNG GẶP

### Lỗi kết nối PostgreSQL

- **Lỗi "role postgres does not exist"**: Tạo user postgres hoặc sử dụng user khác trong chuỗi kết nối
- **Lỗi "password authentication failed"**: Kiểm tra lại password trong chuỗi kết nối
- **Lỗi "database homestay does not exist"**: Tạo cơ sở dữ liệu homestay trước khi kết nối

### Lỗi khi chạy migration

- **Lỗi "Target database is not up to date"**: Chạy `flask db stamp head` trước khi chạy `flask db upgrade`
- **Lỗi Boolean type**: Đảm bảo chuyển đổi đúng giữa kiểu Boolean trong PostgreSQL (TRUE/FALSE) và SQLite (0/1)
- **Lỗi chuyển đổi từ SQLite sang PostgreSQL**: Sử dụng script `scripts/fix_postgres_migration.py` để khắc phục các vấn đề sau khi di chuyển từ SQLite sang PostgreSQL:
  ```
  python scripts/fix_postgres_migration.py
  ```
  Script này giúp reset database PostgreSQL và hướng dẫn bạn sửa lỗi chuyển đổi kiểu Boolean và kích thước trường password_hash.

### Lỗi khi chạy ứng dụng

- **ModuleNotFoundError**: Kiểm tra lại việc cài đặt các thư viện phụ thuộc
- **Error: Failed to find Flask application**: Đảm bảo bạn đang ở trong thư mục gốc của dự án

### Kiểm tra database đang sử dụng

Bạn có thể kiểm tra ứng dụng đang kết nối với database nào bằng cách chạy script:

```
python check_database_connection.py
```

### Lỗi varchar(128) trong PostgreSQL

Nếu gặp lỗi liên quan đến độ dài varchar(128) khi di chuyển từ SQLite sang PostgreSQL, hãy chỉnh sửa định nghĩa model trong `app/models/models.py` để tăng độ dài trường:

```python
# Thay đổi
password_hash = db.Column(db.String(128))
# Thành
password_hash = db.Column(db.String(255))
```

---

## LƯU Ý QUAN TRỌNG

- **Backup dữ liệu**: Luôn sao lưu dữ liệu trước khi chuyển đổi giữa các loại cơ sở dữ liệu
- **Môi trường phát triển vs sản xuất**: SQLite phù hợp cho phát triển, PostgreSQL phù hợp cho sản xuất
- **An toàn mật khẩu**: Thay đổi mật khẩu admin mặc định ngay sau khi đăng nhập lần đầu
- **Khác biệt về kiểu dữ liệu**: Lưu ý sự khác biệt về kiểu dữ liệu giữa SQLite và PostgreSQL (đặc biệt là kiểu Boolean)

---

© 2025 - Tài liệu hướng dẫn thiết lập Staycation
