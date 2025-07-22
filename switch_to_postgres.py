#!/usr/bin/env python
"""
Script để chuyển đổi sang sử dụng PostgreSQL
Sử dụng: python switch_to_postgres.py [username] [password] [host] [database]
Ví dụ: python switch_to_postgres.py postgres mypassword localhost homestay
"""
import os
import sys
import re
import shutil
from datetime import datetime

# Lấy thông tin kết nối PostgreSQL từ tham số dòng lệnh
if len(sys.argv) >= 5:
    pg_username = sys.argv[1]
    pg_password = sys.argv[2]
    pg_host = sys.argv[3]
    pg_database = sys.argv[4]
else:
    # Giá trị mặc định nếu không có tham số
    pg_username = "postgres"
    pg_password = "password"  # Cần thay đổi tùy theo môi trường
    pg_host = "localhost"
    pg_database = "homestay"
    print(f"Sử dụng thông tin kết nối PostgreSQL mặc định:")
    print(f"Username: {pg_username}")
    print(f"Password: {pg_password}")
    print(f"Host: {pg_host}")
    print(f"Database: {pg_database}")
    print("Nếu muốn thay đổi, hãy chạy với tham số: python switch_to_postgres.py [username] [password] [host] [database]")

# Tạo chuỗi kết nối PostgreSQL
pg_connection_string = f"postgresql://{pg_username}:{pg_password}@{pg_host}:5432/{pg_database}"

# Đường dẫn đến thư mục gốc
root_dir = os.path.dirname(os.path.abspath(__file__))

# Đường dẫn đến file config.py và .env
config_file = os.path.join(root_dir, 'config', 'config.py')
env_file = os.path.join(root_dir, '.env')

# Tạo backup trước khi thay đổi
backup_suffix = datetime.now().strftime('%Y%m%d_%H%M%S')

# Backup file config.py
config_backup = f"{config_file}.{backup_suffix}.bak"
shutil.copy2(config_file, config_backup)
print(f"Đã tạo backup cho config.py tại: {config_backup}")

# Backup file .env nếu tồn tại
if os.path.exists(env_file):
    env_backup = f"{env_file}.{backup_suffix}.bak"
    shutil.copy2(env_file, env_backup)
    print(f"Đã tạo backup cho .env tại: {env_backup}")

# Cập nhật file config.py
try:
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern để tìm dòng cấu hình database
    pg_pattern = r"#\s*(SQLALCHEMY_DATABASE_URI\s*=\s*os\.environ\.get\('DATABASE_URL'.*?postgresql.*?\))"
    sqlite_pattern = r"(SQLALCHEMY_DATABASE_URI\s*=\s*os\.environ\.get\('DATABASE_URL'\).*?sqlite.*?)"
    
    # Kiểm tra xem cần thay đổi cấu hình không
    if re.search(pg_pattern, content) and re.search(sqlite_pattern, content):
        # Uncomment dòng PostgreSQL
        content = re.sub(pg_pattern, r"\1", content)
        # Comment dòng SQLite
        content = re.sub(sqlite_pattern, r"# \1", content)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Đã cập nhật file config.py để sử dụng PostgreSQL")
    else:
        # Nếu không tìm thấy pattern phù hợp, cố gắng thay thế chuỗi kết nối
        pg_config_line = f"SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '{pg_connection_string}')"
        if "SQLALCHEMY_DATABASE_URI" in content:
            content = re.sub(r"SQLALCHEMY_DATABASE_URI\s*=.*", pg_config_line, content)
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("Đã cập nhật chuỗi kết nối PostgreSQL trong config.py")
        else:
            print("Không tìm thấy cấu hình SQLALCHEMY_DATABASE_URI trong config.py. Cần kiểm tra và chỉnh sửa thủ công.")

except Exception as e:
    print(f"Lỗi khi cập nhật file config.py: {str(e)}")

# Cập nhật hoặc thêm DATABASE_URL vào file .env
try:
    if os.path.exists(env_file):
        # Đọc file .env hiện tại
        with open(env_file, 'r', encoding='utf-8') as f:
            env_content = f.read()
        
        # Kiểm tra xem DATABASE_URL đã tồn tại chưa
        if 'DATABASE_URL=' in env_content:
            # Thay thế DATABASE_URL hiện có
            env_content = re.sub(r"#?\s*DATABASE_URL=.*", f"DATABASE_URL={pg_connection_string}", env_content)
        else:
            # Thêm DATABASE_URL mới
            env_content += f"\n# PostgreSQL database configuration\nDATABASE_URL={pg_connection_string}\n"
        
        # Ghi lại file .env
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
    else:
        # Tạo file .env mới nếu không tồn tại
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(f"# PostgreSQL database configuration\nDATABASE_URL={pg_connection_string}\n")
    
    print(f"Đã cập nhật DATABASE_URL={pg_connection_string} trong file .env")
except Exception as e:
    print(f"Lỗi khi cập nhật file .env: {str(e)}")

print("\nĐã hoàn tất chuyển đổi sang sử dụng PostgreSQL")
print("Hãy chạy 'python check_database_connection.py' để xác nhận kết nối đến PostgreSQL")
print("\nLưu ý: Cần đảm bảo PostgreSQL đang chạy và database đã được tạo.")
print("Nếu bạn chưa tạo database trong PostgreSQL, hãy thực hiện các lệnh sau trong psql hoặc pgAdmin:")
print(f"    CREATE DATABASE {pg_database};")
print(f"    CREATE USER {pg_username} WITH ENCRYPTED PASSWORD '{pg_password}';") 
print(f"    GRANT ALL PRIVILEGES ON DATABASE {pg_database} TO {pg_username};")

print("\nSau đó chạy migration để tạo cấu trúc bảng:")
print("    flask db upgrade")

print("\nDữ liệu không được tự động chuyển từ SQLite sang PostgreSQL.")
print("Nếu bạn cần di chuyển dữ liệu, hãy thực hiện riêng quy trình migration dữ liệu.")
