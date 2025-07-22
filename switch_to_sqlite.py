#!/usr/bin/env python
"""
Script để chuyển đổi sang sử dụng SQLite
Sử dụng: python switch_to_sqlite.py
"""
import os
import sys
import re
import shutil
from datetime import datetime

# Đường dẫn đến thư mục gốc
root_dir = os.path.dirname(os.path.abspath(__file__))

# Đường dẫn đến file config.py
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
    pg_pattern = r"(SQLALCHEMY_DATABASE_URI\s*=\s*os\.environ\.get\('DATABASE_URL'.*?postgresql.*?\))"
    sqlite_pattern = r"#\s*(SQLALCHEMY_DATABASE_URI\s*=\s*os\.environ\.get\('DATABASE_URL'\).*?sqlite.*?)"
    
    # Kiểm tra xem cấu hình hiện tại là gì
    if re.search(pg_pattern, content) and re.search(sqlite_pattern, content):
        # Comment dòng PostgreSQL
        content = re.sub(pg_pattern, r"# \1", content)
        # Uncomment dòng SQLite
        content = re.sub(sqlite_pattern, r"\1", content)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Đã cập nhật file config.py để sử dụng SQLite")
    else:
        print("Không tìm thấy mẫu cấu hình phù hợp trong config.py. Cần kiểm tra và chỉnh sửa thủ công.")

except Exception as e:
    print(f"Lỗi khi cập nhật file config.py: {str(e)}")

# Cập nhật file .env (comment DATABASE_URL)
if os.path.exists(env_file):
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            env_lines = f.readlines()
        
        with open(env_file, 'w', encoding='utf-8') as f:
            for line in env_lines:
                if line.strip().startswith('DATABASE_URL='):
                    f.write(f"# {line}")  # Comment dòng DATABASE_URL
                else:
                    f.write(line)
        
        print("Đã comment biến DATABASE_URL trong file .env")
    except Exception as e:
        print(f"Lỗi khi cập nhật file .env: {str(e)}")

print("\nĐã hoàn tất chuyển đổi sang sử dụng SQLite")
print("Hãy chạy 'python check_database_connection.py' để xác nhận kết nối đến SQLite")
print("\nLưu ý: Dữ liệu không được tự động chuyển từ PostgreSQL sang SQLite.")
print("Nếu bạn cần di chuyển dữ liệu, hãy thực hiện riêng quy trình migration dữ liệu.")
