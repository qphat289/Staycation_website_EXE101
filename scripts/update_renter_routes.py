#!/usr/bin/env python3
"""
Script để cập nhật file renter.py từ room thành home
"""

import re
import os

def update_renter_routes():
    """Update renter.py file from room to home"""
    
    file_path = 'app/routes/renter.py'
    
    if not os.path.exists(file_path):
        print(f"File {file_path} not found!")
        return
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup original file
    backup_path = file_path + '.backup'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ Backup created: {backup_path}")
    
    # Define replacements
    replacements = [
        # Model and class names
        ('Room', 'Home'),
        ('RoomImage', 'HomeImage'),
        
        # Variable names
        ('room_id', 'home_id'),
        ('rooms', 'homes'),
        ('room_type', 'home_type'),
        ('room.', 'home.'),
        
        # Route names
        ('/view-room', '/view-home'),
        ('/book/<int:home_id>', '/book/<int:home_id>'),
        ('/home/<int:home_id>/detail', '/home/<int:home_id>/detail'),
        
        # Function names
        ('view_room', 'view_home'),
        ('book_room', 'book_home'),
        ('view_room_detail', 'view_home_detail'),
        
        # URL patterns
        ('renter.book_room', 'renter.book_home'),
        ('renter.view_room', 'renter.view_home'),
        ('renter.view_room_detail', 'renter.view_home_detail'),
        
        # Comments and strings
        ('Search for rooms', 'Search for homes'),
        ('matching rooms', 'matching homes'),
        ('Found.*rooms', 'Found homes'),
        ('Room Details:', 'Home Details:'),
        ('Load room', 'Load home'),
        ('phòng', 'nhà'),
        ('Phòng', 'Nhà'),
        ('PHÒNG', 'NHÀ'),
        ('room', 'home'),
        
        # Database field references
        ('Home.city', 'Home.city'),
        ('Home.district', 'Home.district'),
        ('Home.title', 'Home.title'),
        ('Home.max_guests', 'Home.max_guests'),
        ('Home.price_per_hour', 'Home.price_per_hour'),
        ('Home.price_per_night', 'Home.price_per_night'),
        ('Home.is_active', 'Home.is_active'),
        ('Home.home_type', 'Home.home_type'),
        
        # Query patterns
        ('Home.query.filter', 'Home.query.filter'),
        ('query.filter(Home.', 'query.filter(Home.'),
        
        # Template names
        ('view_room_detail.html', 'view_home_detail.html'),
        
        # Specific patterns
        ('debug_homes', 'debug_homes'),
        ('Home type filter', 'Home type filter'),
        ('home_types', 'home_types'),
    ]
    
    # Apply replacements
    for old, new in replacements:
        content = content.replace(old, new)
    
    # Write updated content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ Updated {file_path}")
    print("✓ All replacements applied successfully!")

if __name__ == "__main__":
    update_renter_routes() 