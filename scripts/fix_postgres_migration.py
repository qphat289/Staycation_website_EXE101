"""
Script để khắc phục các vấn đề sau khi di chuyển từ SQLite sang PostgreSQL
- Sửa lỗi chuyển đổi kiểu Boolean
- Khởi tạo lại database schema với kích thước trường password_hash lớn hơn
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
load_dotenv()

# Thêm thư mục gốc vào PATH để có thể import
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Lấy thông tin kết nối PostgreSQL từ biến môi trường
pg_conn_string = os.environ.get('DATABASE_URL', 'postgresql://postgres:timnolun2004@localhost:5432/homestay')
pg_user = pg_conn_string.split('://')[1].split(':')[0]
pg_password = pg_conn_string.split('://')[1].split(':')[1].split('@')[0]
pg_host = pg_conn_string.split('@')[1].split(':')[0]
pg_port = pg_conn_string.split(':')[3].split('/')[0]
pg_db = pg_conn_string.split('/')[-1]

def reset_database():
    """Xóa và tạo lại database"""
    # Kết nối tới PostgreSQL server (không phải database cụ thể)
    conn = psycopg2.connect(
        user=pg_user,
        password=pg_password,
        host=pg_host,
        port=pg_port
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # Thử xóa database nếu tồn tại
    try:
        cursor.execute(f"DROP DATABASE IF EXISTS {pg_db}")
        print(f"Đã xóa database {pg_db}")
    except Exception as e:
        print(f"Lỗi khi xóa database: {e}")
    
    # Tạo database mới
    try:
        cursor.execute(f"CREATE DATABASE {pg_db}")
        print(f"Đã tạo database mới {pg_db}")
    except Exception as e:
        print(f"Lỗi khi tạo database mới: {e}")
    
    cursor.close()
    conn.close()

def main():
    """Hàm chính để khắc phục các vấn đề"""
    print("Bắt đầu quy trình khắc phục sau khi migrate...")
    
    # 1. Reset database
    reset_database()
    
    print("\nĐã reset database. Bây giờ bạn cần thực hiện các bước sau:")
    print("1. Khởi động lại ứng dụng với 'python app.py' - điều này sẽ tạo schema mới với trường password_hash có kích thước lớn hơn")
    print("2. Chạy lại script migrate_simple.py sau khi sửa đổi để xử lý chuyển đổi boolean")
    print("\nHướng dẫn sửa script migrate_simple.py:")
    print("- Thêm đoạn code chuyển đổi kiểu dữ liệu trong hàm migrate_table_data")
    print("- Đối với các trường boolean, chuyển đổi 1 -> TRUE, 0 -> FALSE")

if __name__ == "__main__":
    main()
