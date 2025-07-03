#!/usr/bin/env python3
"""
Script để cập nhật file owner.py từ room thành home
"""

import re
import os

def update_owner_routes():
    """Update owner.py file from room to home"""
    
    file_path = 'app/routes/owner.py'
    
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
        ('RoomDeletionLog', 'HomeDeletionLog'),
        
        # Variable names
        ('room_data', 'home_data'),
        ('room_id', 'home_id'),
        ('rooms', 'homes'),
        ('new_room', 'new_home'),
        ('room_image', 'home_image'),
        ('room_images', 'home_images'),
        
        # Form field names
        ('room_title', 'home_title'),
        ('room_description', 'home_description'),
        ('room_number', 'home_number'),
        ('room_type', 'home_type'),
        
        # Session keys
        ('room_preview_data', 'home_preview_data'),
        
        # Route names
        ('/add-room', '/add-home'),
        ('/edit-room', '/edit-home'),
        ('/delete-room', '/delete-home'),
        ('/room-preview', '/home-preview'),
        ('/room-image', '/home-image'),
        ('/room-detail', '/home-detail'),
        ('/room/', '/home/'),
        ('/clear-room-data', '/clear-home-data'),
        ('/clear-room-session', '/clear-home-session'),
        ('/confirm-room', '/confirm-home'),
        ('/toggle-room-status', '/toggle-home-status'),
        
        # Function names
        ('add_room', 'add_home'),
        ('edit_room', 'edit_home'),
        ('delete_room', 'delete_home'),
        ('room_preview', 'home_preview'),
        ('room_detail', 'home_detail'),
        ('confirm_room', 'confirm_home'),
        ('book_room', 'book_home'),
        ('add_room_images', 'add_home_images'),
        ('delete_room_image', 'delete_home_image'),
        ('toggle_room_status', 'toggle_home_status'),
        ('clear_room_data', 'clear_home_data'),
        ('clear_room_session', 'clear_home_session'),
        
        # Template names
        ('add_room.html', 'add_home.html'),
        ('edit_room.html', 'edit_home.html'),
        ('room_preview.html', 'home_preview.html'),
        
        # URL patterns
        ('owner.add_room', 'owner.add_home'),
        ('owner.edit_room', 'owner.edit_home'),
        ('owner.delete_room', 'owner.delete_home'),
        ('owner.room_preview', 'owner.home_preview'),
        ('owner.room_detail', 'owner.home_detail'),
        ('owner.confirm_room', 'owner.confirm_home'),
        ('owner.book_room', 'owner.book_home'),
        ('owner.add_room_images', 'owner.add_home_images'),
        ('owner.delete_room_image', 'owner.delete_home_image'),
        ('owner.toggle_room_status', 'owner.toggle_home_status'),
        ('owner.clear_room_data', 'owner.clear_home_data'),
        ('owner.clear_room_session', 'owner.clear_home_session'),
        
        # Comments and strings
        ('# Lấy tất cả phòng', '# Lấy tất cả nhà'),
        ('Get all rooms', 'Get all homes'),
        ('phòng', 'nhà'),
        ('Phòng', 'Nhà'),
        ('PHÒNG', 'NHÀ'),
        ('room', 'home'),
        
        # Database field references
        ('room.id', 'home.id'),
        ('room.title', 'home.title'),
        ('room.owner_id', 'home.owner_id'),
        ('room.images', 'home.images'),
        ('room.created_at', 'home.created_at'),
        ('room.is_active', 'home.is_active'),
        ('room.price_per_hour', 'home.price_per_hour'),
        ('room.price_per_night', 'home.price_per_night'),
        
        # Specific patterns
        ('startswith(\'room_\')', 'startswith(\'home_\')'),
        ('key.startswith(\'room_\')', 'key.startswith(\'home_\')'),
        ('room_', 'home_'),
        
        # Fix joinedload references
        ('joinedload(Home.images)', 'joinedload(Home.images)'),
        ('Home.query.options(joinedload(Home.images))', 'Home.query.options(joinedload(Home.images))'),
        
        # Fix specific database queries
        ('Home.created_at.desc()', 'Home.created_at.desc()'),
        ('filter_by(owner_id=current_user.id)', 'filter_by(owner_id=current_user.id)'),
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
    update_owner_routes() 