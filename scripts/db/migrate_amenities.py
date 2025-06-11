#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from models import db
from app import app
import sqlite3

def migrate_amenities():
    """Migration để cập nhật schema amenities"""
    try:
        print("Bắt đầu migration amenities...")
        
        # Lấy đường dẫn database
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Tạo bảng amenity_category mới
        print("Tạo bảng amenity_category...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS amenity_category (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL UNIQUE,
                code VARCHAR(50) NOT NULL UNIQUE,
                icon VARCHAR(100),
                description TEXT,
                display_order INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 2. Tạo bảng amenity mới với cấu trúc mới
        print("Tạo bảng amenity_new...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS amenity_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                icon VARCHAR(100) NOT NULL,
                description TEXT,
                display_order INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                category_id INTEGER NOT NULL,
                FOREIGN KEY (category_id) REFERENCES amenity_category (id)
            )
        ''')
        
        # 3. Backup dữ liệu cũ nếu có
        print("Backup dữ liệu amenity cũ...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='amenity'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            cursor.execute("SELECT COUNT(*) FROM amenity")
            old_count = cursor.fetchone()[0]
            print(f"Tìm thấy {old_count} amenity cũ")
            
            # Lưu dữ liệu cũ vào bảng backup
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS amenity_backup AS 
                SELECT * FROM amenity
            ''')
            
            # Xóa bảng cũ
            cursor.execute("DROP TABLE amenity")
            print("Đã xóa bảng amenity cũ")
        
        # 4. Đổi tên bảng mới
        cursor.execute("ALTER TABLE amenity_new RENAME TO amenity")
        print("Đã đổi tên bảng amenity_new thành amenity")
        
        # 5. Cập nhật bảng room_amenities nếu cần
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='room_amenities'")
        if cursor.fetchone():
            print("Bảng room_amenities đã tồn tại")
        else:
            print("Tạo bảng room_amenities...")
            cursor.execute('''
                CREATE TABLE room_amenities (
                    room_id INTEGER,
                    amenity_id INTEGER,
                    PRIMARY KEY (room_id, amenity_id),
                    FOREIGN KEY (room_id) REFERENCES room (id),
                    FOREIGN KEY (amenity_id) REFERENCES amenity (id)
                )
            ''')
        
        conn.commit()
        conn.close()
        
        print("Migration hoàn thành thành công!")
        
    except Exception as e:
        print(f"Lỗi khi migration: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        raise e

if __name__ == '__main__':
    with app.app_context():
        migrate_amenities() 