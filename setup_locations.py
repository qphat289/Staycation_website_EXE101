#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script để setup dữ liệu địa chỉ cho hệ thống
Chạy script này để:
1. Tạo migration cho các bảng địa chỉ mới
2. Chạy migration
3. Seed dữ liệu TP.HCM và Hà Nội
"""

import os
import sys
import subprocess
from app import app
from models import db
from seed_locations import seed_locations

def run_command(command, description):
    """Chạy command và hiển thị kết quả"""
    print(f"\n🔄 {description}...")
    print(f"Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {description} thành công!")
            if result.stdout:
                print("Output:", result.stdout)
        else:
            print(f"❌ {description} thất bại!")
            if result.stderr:
                print("Error:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Lỗi khi chạy command: {e}")
        return False
    
    return True

def setup_locations():
    """Setup hoàn chỉnh hệ thống địa chỉ"""
    print("🚀 Bắt đầu setup hệ thống địa chỉ...")
    
    # 1. Tạo migration
    print("\n" + "="*50)
    if not run_command(
        "flask db migrate -m 'Add Province, District, Ward tables'",
        "Tạo migration cho bảng địa chỉ"
    ):
        print("⚠️ Có thể migration đã tồn tại, tiếp tục...")
    
    # 2. Chạy migration
    print("\n" + "="*50)
    if not run_command(
        "flask db upgrade",
        "Chạy migration"
    ):
        print("❌ Không thể chạy migration. Dừng lại.")
        return False
    
    # 3. Seed dữ liệu
    print("\n" + "="*50)
    print("🌱 Seed dữ liệu địa chỉ...")
    try:
        seed_locations()
        print("✅ Seed dữ liệu thành công!")
    except Exception as e:
        print(f"❌ Lỗi khi seed dữ liệu: {e}")
        return False
    
    # 4. Kiểm tra kết quả
    print("\n" + "="*50)
    print("🔍 Kiểm tra dữ liệu đã được import...")
    
    with app.app_context():
        from models import Province, District, Ward
        
        provinces = Province.query.all()
        districts = District.query.all() 
        wards = Ward.query.all()
        
        print(f"📊 Thống kê:")
        print(f"   - {len(provinces)} tỉnh/thành phố")
        print(f"   - {len(districts)} quận/huyện")
        print(f"   - {len(wards)} phường/xã")
        
        print(f"\n📍 Danh sách tỉnh/thành phố:")
        for province in provinces:
            district_count = len([d for d in districts if d.province_id == province.id])
            print(f"   - {province.name} ({district_count} quận/huyện)")
    
    print("\n" + "="*50)
    print("🎉 Setup hoàn tất!")
    print("\n📌 Để test API, bạn có thể truy cập:")
    print("   - GET /api/provinces")
    print("   - GET /api/provinces/hcm/districts") 
    print("   - GET /api/districts/quan1/wards")
    print("   - GET /api/locations/all")
    
    return True

def check_requirements():
    """Kiểm tra các yêu cầu trước khi chạy"""
    print("🔍 Kiểm tra requirements...")
    
    # Kiểm tra Flask-Migrate
    try:
        import flask_migrate
        print("✅ Flask-Migrate có sẵn")
    except ImportError:
        print("❌ Flask-Migrate chưa cài đặt. Chạy: pip install Flask-Migrate")
        return False
    
    # Kiểm tra database connection
    try:
        with app.app_context():
            db.create_all()
        print("✅ Database connection OK")
    except Exception as e:
        print(f"❌ Lỗi kết nối database: {e}")
        return False
    
    return True

def main():
    """Main function"""
    print("🏠 Setup Hệ thống Địa chỉ - TP.HCM & Hà Nội")
    print("="*50)
    
    # Kiểm tra requirements
    if not check_requirements():
        print("\n❌ Kiểm tra requirements thất bại!")
        sys.exit(1)
    
    # Setup 
    if setup_locations():
        print("\n🎉 Setup thành công! Hệ thống địa chỉ đã sẵn sàng.")
        sys.exit(0)
    else:
        print("\n❌ Setup thất bại!")
        sys.exit(1)

if __name__ == '__main__':
    main() 