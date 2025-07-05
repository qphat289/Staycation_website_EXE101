#!/usr/bin/env python3
"""
Script để chạy migration thủ công cho payment tables
"""

import sys
import os

# Thêm thư mục gốc vào Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import trực tiếp từ file app.py
import importlib.util
spec = importlib.util.spec_from_file_location("app_module", "app.py")
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

app = app_module.app
db = app_module.db
from app.models.models import Payment, PaymentConfig
from sqlalchemy import text

def create_payment_tables():
    """Tạo bảng payment và payment_config"""
    
    with app.app_context():
        try:
            # Tạo bảng payment_config
            with db.engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS payment_config (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        owner_id INTEGER NOT NULL UNIQUE,
                        payos_client_id VARCHAR(100) NOT NULL,
                        payos_api_key VARCHAR(200) NOT NULL,
                        payos_checksum_key VARCHAR(200) NOT NULL,
                        is_active BOOLEAN DEFAULT 1,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (owner_id) REFERENCES owner (id)
                    )
                """))
                conn.commit()
            print(" Bảng payment_config đã được tạo thành công!")
            
            # Tạo bảng payment
            with db.engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS payment (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        payment_code VARCHAR(100) NOT NULL UNIQUE,
                        order_code VARCHAR(100) NOT NULL UNIQUE,
                        amount FLOAT NOT NULL,
                        currency VARCHAR(10) DEFAULT 'VND',
                        payos_transaction_id VARCHAR(100),
                        payos_signature VARCHAR(500),
                        status VARCHAR(20) DEFAULT 'pending',
                        payment_method VARCHAR(50),
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        paid_at DATETIME,
                        description TEXT,
                        customer_name VARCHAR(100),
                        customer_email VARCHAR(120),
                        customer_phone VARCHAR(20),
                        booking_id INTEGER NOT NULL,
                        owner_id INTEGER NOT NULL,
                        renter_id INTEGER NOT NULL,
                        FOREIGN KEY (booking_id) REFERENCES booking (id),
                        FOREIGN KEY (owner_id) REFERENCES owner (id),
                        FOREIGN KEY (renter_id) REFERENCES renter (id)
                    )
                """))
                conn.commit()
            print(" Bảng payment đã được tạo thành công!")
            
            # Kiểm tra xem bảng đã được tạo chưa
            with db.engine.connect() as conn:
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('payment', 'payment_config')"))
                tables = [row[0] for row in result]
            
            if 'payment' in tables and 'payment_config' in tables:
                print(" Cả hai bảng đã được tạo thành công!")
                return True
            else:
                print(" Có lỗi xảy ra khi tạo bảng!")
                return False
                
        except Exception as e:
            print(f" Lỗi: {e}")
            return False

def verify_tables():
    """Kiểm tra cấu trúc bảng đã tạo"""
    
    with app.app_context():
        try:
            # Kiểm tra cấu trúc bảng payment_config
            with db.engine.connect() as conn:
                result = conn.execute(text("PRAGMA table_info(payment_config)"))
                print("\n Cấu trúc bảng payment_config:")
                for row in result:
                    print(f"  - {row[1]} ({row[2]})")
            # Kiểm tra cấu trúc bảng payment
            with db.engine.connect() as conn:
                result = conn.execute(text("PRAGMA table_info(payment)"))
                print("\n Cấu trúc bảng payment:")
                for row in result:
                    print(f"  - {row[1]} ({row[2]})")
                
        except Exception as e:
            print(f" Lỗi khi kiểm tra cấu trúc bảng: {e}")

if __name__ == "__main__":
    print(" Bắt đầu tạo bảng payment và payment_config...")
    
    if create_payment_tables():
        print("\n Kiểm tra cấu trúc bảng...")
        verify_tables()
        print("\n Hoàn thành! Bảng payment và payment_config đã sẵn sàng sử dụng.")
    else:
        print("\n Không thể tạo bảng. Vui lòng kiểm tra lại!") 