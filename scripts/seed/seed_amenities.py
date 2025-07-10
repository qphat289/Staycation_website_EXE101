#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# Add the project root to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config.config import Config
from app.models.models import db, Admin, Owner, Renter, Home, Booking, Review, Amenity, HomeImage, Statistics, AmenityCategory

# Tạo ứng dụng Flask
app = Flask(__name__)
app.config.from_object(Config)

# Khởi tạo database
db.init_app(app)

# Dữ liệu phân loại tiện nghi
amenity_categories = [
    {
        'name': 'Tiện nghi nhà',
        'code': 'home',
        'icon': 'bi-house-door',
        'description': 'Các tiện nghi cơ bản trong nhà',
        'display_order': 1
    },
    {
        'name': 'Tiện nghi phổ biến',
        'code': 'common',
        'icon': 'bi-star',
        'description': 'Các tiện nghi thông dụng được yêu thích',
        'display_order': 2
    },
    {
        'name': 'Tiện nghi độc đáo',
        'code': 'unique',
        'icon': 'bi-gem',
        'description': 'Các tiện nghi đặc biệt và cao cấp',
        'display_order': 3
    }
]

# Dữ liệu tiện nghi theo từng loại
amenities_data = {
    'home': [
        {'name': 'Điều hòa không khí', 'icon': 'bi-thermometer-sun', 'display_order': 1},
        {'name': 'Tivi màn hình phẳng', 'icon': 'bi-tv', 'display_order': 2},
        {'name': 'Tủ lạnh mini', 'icon': 'bi-box', 'display_order': 3},
        {'name': 'Giường đôi', 'icon': 'bi-house-heart', 'display_order': 4},
        {'name': 'Bàn làm việc', 'icon': 'bi-table', 'display_order': 5},
        {'name': 'Tủ quần áo', 'icon': 'bi-archive', 'display_order': 6},
        {'name': 'Gương trang điểm', 'icon': 'bi-symmetry-horizontal', 'display_order': 7},
        {'name': 'Quạt trần', 'icon': 'bi-fan', 'display_order': 8},
        {'name': 'Máy sấy tóc', 'icon': 'bi-wind', 'display_order': 9},
        {'name': 'Két an toàn', 'icon': 'bi-safe2', 'display_order': 10}
    ],
    'common': [
        {'name': 'WiFi miễn phí', 'icon': 'bi-wifi', 'display_order': 1},
        {'name': 'Dọn nhà hàng ngày', 'icon': 'bi-brush', 'display_order': 2},
        {'name': 'Đồ vệ sinh cá nhân', 'icon': 'bi-droplet', 'display_order': 3},
        {'name': 'Khăn tắm và ga giường', 'icon': 'bi-house-check', 'display_order': 4},
        {'name': 'Nước uống miễn phí', 'icon': 'bi-cup-straw', 'display_order': 5},
        {'name': 'Bãi đỗ xe', 'icon': 'bi-car-front', 'display_order': 6},
        {'name': 'Lễ tân 24/7', 'icon': 'bi-clock', 'display_order': 7},
        {'name': 'Dịch vụ giặt ủi', 'icon': 'bi-bag-check', 'display_order': 8},
        {'name': 'Thang máy', 'icon': 'bi-arrow-up-square', 'display_order': 9},
        {'name': 'An ninh 24/7', 'icon': 'bi-shield-check', 'display_order': 10}
    ],
    'unique': [
        {'name': 'Jacuzzi riêng', 'icon': 'bi-droplet-half', 'display_order': 1},
        {'name': 'Ban công view đẹp', 'icon': 'bi-tree', 'display_order': 2},
        {'name': 'Bếp nhỏ riêng', 'icon': 'bi-fire', 'display_order': 3},
        {'name': 'Nhà gym mini', 'icon': 'bi-heart-pulse', 'display_order': 4},
        {'name': 'Hồ bơi riêng', 'icon': 'bi-water', 'display_order': 5},
        {'name': 'Karaoke riêng', 'icon': 'bi-mic', 'display_order': 6},
        {'name': 'Cinema mini', 'icon': 'bi-camera-reels', 'display_order': 7},
        {'name': 'Máy massage', 'icon': 'bi-hand-thumbs-up', 'display_order': 8},
        {'name': 'Bar mini', 'icon': 'bi-cup-hot', 'display_order': 9},
        {'name': 'Tầng thượng riêng', 'icon': 'bi-building-up', 'display_order': 10}
    ]
}

def import_amenity_data():
    """Import dữ liệu tiện nghi vào database"""
    try:
        print("Bắt đầu import dữ liệu tiện nghi...")
        
        # Xóa dữ liệu cũ
        Amenity.query.delete()
        AmenityCategory.query.delete()
        db.session.commit()
        print("Đã xóa dữ liệu tiện nghi cũ")
        
        # Import amenity categories
        category_objects = {}
        for cat_data in amenity_categories:
            category = AmenityCategory(**cat_data)
            db.session.add(category)
            db.session.flush()  # Để lấy ID
            category_objects[cat_data['code']] = category
            print(f"Đã thêm loại tiện nghi: {cat_data['name']}")
        
        # Import amenities
        total_amenities = 0
        for category_code, amenities in amenities_data.items():
            category = category_objects[category_code]
            for amenity_data in amenities:
                amenity = Amenity(
                    name=amenity_data['name'],
                    icon=amenity_data['icon'],
                    display_order=amenity_data['display_order'],
                    category_id=category.id
                )
                db.session.add(amenity)
                total_amenities += 1
        
        db.session.commit()
        print("Import dữ liệu tiện nghi thành công!")
        
        # Thống kê
        print("\n=== THỐNG KÊ ===")
        print(f"  - {len(amenity_categories)} loại tiện nghi")
        print(f"  - {total_amenities} tiện nghi tổng cộng")
        for category_code, amenities in amenities_data.items():
            category_name = next(cat['name'] for cat in amenity_categories if cat['code'] == category_code)
            print(f"    + {category_name}: {len(amenities)} tiện nghi")
        
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi khi import dữ liệu tiện nghi: {e}")
        raise e

if __name__ == '__main__':
    with app.app_context():
        import_amenity_data() 