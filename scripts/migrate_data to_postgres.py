"""
Script đơn giản để di chuyển chỉ dữ liệu từ SQLite sang PostgreSQL
- Không cần khởi tạo lại cấu trúc bảng
- Chuyển đổi kiểu dữ liệu tự động (từ integer sang boolean)
- Xử lý các thứ tự ràng buộc khóa ngoại
"""

import os
import sys
import time
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load các biến môi trường từ file .env
load_dotenv()

# Thêm thư mục gốc vào PATH để có thể import
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Đường dẫn tới file SQLite
sqlite_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "instance", "homestay.db")

# Lấy thông tin kết nối PostgreSQL từ biến môi trường
pg_conn_string = os.environ.get('DATABASE_URL', 'postgresql://postgres:timnolun2004@localhost:5432/homestay')
pg_user = pg_conn_string.split('://')[1].split(':')[0]
pg_password = pg_conn_string.split('://')[1].split(':')[1].split('@')[0]
pg_host = pg_conn_string.split('@')[1].split(':')[0]
pg_port = pg_conn_string.split(':')[3].split('/')[0]
pg_db = pg_conn_string.split('/')[-1]

def get_sqlite_tables():
    """Lấy danh sách các bảng từ SQLite"""
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    
    # Lấy danh sách các bảng (không bao gồm các bảng của SQLite)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return tables

def get_pg_table_info(table_name):
    """Lấy thông tin về cấu trúc bảng từ PostgreSQL"""
    conn = psycopg2.connect(
        user=pg_user,
        password=pg_password,
        host=pg_host,
        port=pg_port,
        database=pg_db
    )
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Lấy thông tin cột và kiểu dữ liệu
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))
    columns = cursor.fetchall()
    
    # Lấy thông tin khóa chính
    cursor.execute("""
        SELECT c.column_name
        FROM information_schema.table_constraints tc 
        JOIN information_schema.constraint_column_usage AS ccu USING (constraint_schema, constraint_name) 
        JOIN information_schema.columns AS c ON c.table_schema = tc.constraint_schema
          AND tc.table_name = c.table_name AND ccu.column_name = c.column_name
        WHERE constraint_type = 'PRIMARY KEY' and tc.table_name = %s
    """, (table_name,))
    primary_keys = [row['column_name'] for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    return {
        'columns': columns,
        'primary_keys': primary_keys
    }

def get_sqlite_data(table_name):
    """Lấy toàn bộ dữ liệu từ một bảng trong SQLite"""
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    
    conn.close()
    return [dict(row) for row in rows]

def convert_value_for_pg(value, data_type):
    """Chuyển đổi giá trị phù hợp với kiểu dữ liệu PostgreSQL"""
    if value is None:
        return None
        
    # Chuyển đổi boolean
    if data_type == 'boolean':
        if isinstance(value, int):
            return 'TRUE' if value == 1 else 'FALSE'
        if isinstance(value, str) and value.isdigit():
            return 'TRUE' if int(value) == 1 else 'FALSE'
    
    return value

def disable_foreign_key_constraints():
    """Tạm thời vô hiệu hóa ràng buộc khóa ngoại trong PostgreSQL"""
    conn = psycopg2.connect(
        user=pg_user,
        password=pg_password,
        host=pg_host,
        port=pg_port,
        database=pg_db
    )
    cursor = conn.cursor()
    
    cursor.execute("SET session_replication_role = 'replica';")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("Đã tạm thời vô hiệu hóa ràng buộc khóa ngoại")

def enable_foreign_key_constraints():
    """Kích hoạt lại ràng buộc khóa ngoại trong PostgreSQL"""
    conn = psycopg2.connect(
        user=pg_user,
        password=pg_password,
        host=pg_host,
        port=pg_port,
        database=pg_db
    )
    cursor = conn.cursor()
    
    cursor.execute("SET session_replication_role = 'origin';")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("Đã kích hoạt lại ràng buộc khóa ngoại")

def clear_table_data(table_name):
    """Xóa toàn bộ dữ liệu trong một bảng PostgreSQL"""
    conn = psycopg2.connect(
        user=pg_user,
        password=pg_password,
        host=pg_host,
        port=pg_port,
        database=pg_db
    )
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"TRUNCATE TABLE {table_name} CASCADE;")
        conn.commit()
        print(f"Đã xóa dữ liệu bảng {table_name}")
    except Exception as e:
        print(f"Lỗi khi xóa dữ liệu bảng {table_name}: {e}")
    
    cursor.close()
    conn.close()

def migrate_table_data(table_name):
    """Di chuyển dữ liệu của một bảng từ SQLite sang PostgreSQL"""
    try:
        # Lấy dữ liệu từ SQLite
        rows = get_sqlite_data(table_name)
        
        if not rows:
            print(f"  - Không có dữ liệu trong bảng {table_name}")
            return True
        
        print(f"Found {len(rows)} records in {table_name}")
        
        # Lấy thông tin cấu trúc bảng từ PostgreSQL
        table_info = get_pg_table_info(table_name)
        column_info = {col['column_name']: col for col in table_info['columns']}
        
        # Kết nối tới PostgreSQL
        pg_conn = psycopg2.connect(
            user=pg_user,
            password=pg_password,
            host=pg_host,
            port=pg_port,
            database=pg_db
        )
        pg_cursor = pg_conn.cursor()
        
        # Xóa bảng hiện tại trước khi insert
        clear_table_data(table_name)
        
        success_count = 0
        error_count = 0
        
        # Chèn từng dòng dữ liệu
        for i, row in enumerate(rows):
            try:
                # Lọc các cột có trong PostgreSQL
                filtered_row = {}
                for col_name, value in row.items():
                    if col_name in column_info:
                        data_type = column_info[col_name]['data_type']
                        filtered_row[col_name] = convert_value_for_pg(value, data_type)
                
                # Xây dựng câu lệnh SQL
                columns = list(filtered_row.keys())
                columns_str = ", ".join(columns)
                
                # Tạo placeholders và values
                placeholders = []
                values = []
                
                for col in columns:
                    val = filtered_row[col]
                    if isinstance(val, str) and (val == 'TRUE' or val == 'FALSE'):
                        placeholders.append(val)
                    else:
                        placeholders.append("%s")
                        values.append(val)
                
                placeholders_str = ", ".join(placeholders)
                
                # Tạo câu lệnh SQL
                insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders_str})"
                
                # Thực thi câu lệnh
                pg_cursor.execute(insert_sql, values)
                success_count += 1
                
            except Exception as e:
                print(f"Error inserting record {i+1} in {table_name}: {e}")
                error_count += 1
                continue
        
        # Commit và đóng kết nối
        pg_conn.commit()
        pg_cursor.close()
        pg_conn.close()
        
        print(f"Đã migrate {success_count}/{len(rows)} bản ghi cho bảng {table_name} (Lỗi: {error_count})")
        return True
        
    except Exception as e:
        print(f"Error migrating data for table {table_name}: {e}")
        return False

def migrate_many_to_many_relations():
    """Migrate các bảng quan hệ nhiều-nhiều"""
    # Danh sách các bảng liên kết nhiều-nhiều thông thường
    m2m_tables = [
        'home_amenities',
        'home_rules'
    ]
    
    for table_name in m2m_tables:
        print(f"\nProcessing many-to-many table: {table_name}")
        migrate_table_data(table_name)

def main():
    """Hàm chính để di chuyển dữ liệu"""
    print("Starting SQLite to PostgreSQL data migration...")
    
    start_time = time.time()
    
    # Lấy danh sách các bảng từ SQLite
    tables = get_sqlite_tables()
    
    # Thứ tự các bảng để đảm bảo đúng ràng buộc khóa ngoại
    priority_tables = [
        'province', 'district', 'ward', 'amenity', 'rule',
        'admin', 'owner', 'renter',
        'home', 'home_image',
        'booking', 'review',
        'statistics', 'notification',
        'payment_config', 'payment',
        'home_deletion_log'
    ]
    
    # Lọc các bảng đã định nghĩa trong priority_tables
    tables_to_process = [t for t in priority_tables if t in tables]
    
    # Thêm các bảng còn lại (nếu có)
    remaining_tables = [t for t in tables if t not in priority_tables and not t.startswith('alembic')]
    tables_to_process.extend(remaining_tables)
    
    try:
        # Vô hiệu hóa tạm thời ràng buộc khóa ngoại
        disable_foreign_key_constraints()
        
        # Di chuyển dữ liệu từng bảng
        for table in tables_to_process:
            print(f"\nProcessing table: {table}")
            migrate_table_data(table)
        
        # Di chuyển các bảng quan hệ nhiều-nhiều
        migrate_many_to_many_relations()
        
    finally:
        # Đảm bảo khóa ngoại được bật lại
        enable_foreign_key_constraints()
    
    end_time = time.time()
    print(f"\nMigration completed in {end_time - start_time:.2f} seconds")
    
    print("\n=== NEXT STEPS ===")
    print("1. Kiểm tra dữ liệu đã migrate bằng cách chạy ứng dụng: python app.py")
    print("2. Kiểm tra tính đúng đắn của dữ liệu trong các bảng có quan hệ khóa ngoại")

if __name__ == "__main__":
    main()
