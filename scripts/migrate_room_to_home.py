#!/usr/bin/env python3
"""
Script migration để đổi tên từ "room" thành "home" trong database
"""

import sqlite3
import os
import sys

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def migrate_room_to_home():
    """Migrate database from room-based naming to home-based naming"""
    
    db_path = 'instance/homestay.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    # Backup database
    backup_path = 'instance/homestay_backup.db'
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"✓ Database backed up to {backup_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Đổi tên bảng room thành home
        print("1. Renaming table 'room' to 'home'...")
        cursor.execute("ALTER TABLE room RENAME TO home")
        
        # 2. Đổi tên bảng room_image thành home_image
        print("2. Renaming table 'room_image' to 'home_image'...")
        cursor.execute("ALTER TABLE room_image RENAME TO home_image")
        
        # 3. Đổi tên bảng room_amenities thành home_amenities
        print("3. Renaming table 'room_amenities' to 'home_amenities'...")
        cursor.execute("ALTER TABLE room_amenities RENAME TO home_amenities")
        
        # 4. Đổi tên bảng room_rules thành home_rules
        print("4. Renaming table 'room_rules' to 'home_rules'...")
        cursor.execute("ALTER TABLE room_rules RENAME TO home_rules")
        
        # 5. Đổi tên bảng room_deletion_log thành home_deletion_log
        print("5. Renaming table 'room_deletion_log' to 'home_deletion_log'...")
        cursor.execute("ALTER TABLE room_deletion_log RENAME TO home_deletion_log")
        
        # 6. Cập nhật tên cột trong các bảng
        print("6. Updating column names...")
        
        # Trong bảng home_image: room_id -> home_id
        cursor.execute("ALTER TABLE home_image RENAME COLUMN room_id TO home_id")
        
        # Trong bảng home_amenities: room_id -> home_id
        cursor.execute("ALTER TABLE home_amenities RENAME COLUMN room_id TO home_id")
        
        # Trong bảng home_rules: room_id -> home_id
        cursor.execute("ALTER TABLE home_rules RENAME COLUMN room_id TO home_id")
        
        # Trong bảng booking: room_id -> home_id
        cursor.execute("ALTER TABLE booking RENAME COLUMN room_id TO home_id")
        
        # Trong bảng review: room_id -> home_id
        cursor.execute("ALTER TABLE review RENAME COLUMN room_id TO home_id")
        
        # Trong bảng home_deletion_log: room_id -> home_id, room_title -> home_title, etc.
        cursor.execute("ALTER TABLE home_deletion_log RENAME COLUMN room_id TO home_id")
        cursor.execute("ALTER TABLE home_deletion_log RENAME COLUMN room_title TO home_title")
        cursor.execute("ALTER TABLE home_deletion_log RENAME COLUMN room_address TO home_address")
        cursor.execute("ALTER TABLE home_deletion_log RENAME COLUMN room_price TO home_price")
        
        # 7. Cập nhật các trường trong bảng home
        print("7. Updating field names in home table...")
        cursor.execute("ALTER TABLE home RENAME COLUMN room_type TO home_type")
        cursor.execute("ALTER TABLE home RENAME COLUMN room_number TO home_number")
        
        # 8. Cập nhật các trường trong bảng statistics
        print("8. Updating statistics table...")
        cursor.execute("ALTER TABLE statistics RENAME COLUMN total_rooms TO total_homes")
        cursor.execute("ALTER TABLE statistics RENAME COLUMN top_rooms TO top_homes")
        
        # 9. Cập nhật category code trong amenity_category
        print("9. Updating amenity category codes...")
        cursor.execute("UPDATE amenity_category SET code = 'home' WHERE code = 'room'")
        cursor.execute("UPDATE amenity_category SET name = 'Tiện nghi nhà' WHERE name = 'Tiện nghi phòng'")
        cursor.execute("UPDATE amenity_category SET description = 'Các tiện nghi cơ bản trong nhà' WHERE description = 'Các tiện nghi cơ bản trong phòng'")
        
        conn.commit()
        print("✓ Database migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        # Restore backup
        shutil.copy2(backup_path, db_path)
        print("✓ Database restored from backup")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_room_to_home() 