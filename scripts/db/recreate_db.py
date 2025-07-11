#!/usr/bin/env python3
"""
Script to recreate the database
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from flask import Flask
from config.config import Config
from app.models.models import db

def recreate_database():
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        # Drop all tables
        db.drop_all()
        print("✓ Đã xóa tất cả các bảng")
        
        # Create all tables
        db.create_all()
        print("✓ Đã tạo lại tất cả các bảng")
        
        print("\nĐã tạo lại database thành công!")

if __name__ == "__main__":
    recreate_database() 