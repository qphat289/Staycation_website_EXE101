#!/usr/bin/env python3
"""
Script để setup PayOS credentials cho owner
"""

import sys
import os
import importlib.util
import sys as _sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app_py_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.py')
spec = importlib.util.spec_from_file_location('app_main', app_py_path)
app_module = importlib.util.module_from_spec(spec)
_sys.modules['app_main'] = app_module
spec.loader.exec_module(app_module)
flask_app = app_module.app

from app.models.models import db
from app.models.models import Owner, PaymentConfig
from datetime import datetime

def create_owner_if_not_exists():
    """Tạo owner nếu chưa tồn tại"""
    print("🔧 Tạo owner mẫu...")
    
    # Kiểm tra xem đã có owner chưa
    existing_owner = Owner.query.first()
    if existing_owner:
        print(f" Đã có owner: {existing_owner.username} (ID: {existing_owner.id})")
        return existing_owner
    
    # Tạo owner mới
    owner = Owner(
        username="owner1",
        email="owner@example.com",
        full_name="Owner Mẫu",
        phone="0123456789",
        address="123 Đường ABC, Quận 1, TP.HCM",
        created_at=datetime.utcnow()
    )
    
    db.session.add(owner)
    db.session.commit()
    
    print(f" Đã tạo owner mới: {owner.username} (ID: {owner.id})")
    return owner

def setup_payos_credentials(owner_id):
    """Setup PayOS credentials cho owner"""
    print(f"\n Setup PayOS credentials cho owner {owner_id}...")
    
    # PayOS credentials
    PAYOS_CREDENTIALS = {
        'payos_client_id': '0c4f23f9-5321-439b-a909-c74641f98de9',
        'payos_api_key': 'bde40f77-1af5-4b74-bfe7-540165dd465f',
        'payos_checksum_key': '041db3b7e1158179d9ba8774fae25346b284073674dc57fd4f4d6a0f9ec3a14e'
    }
    
    # Kiểm tra xem đã có config chưa
    existing_config = PaymentConfig.query.filter_by(owner_id=owner_id).first()
    
    if existing_config:
        print(" Cập nhật PayOS config hiện có...")
        existing_config.payos_client_id = PAYOS_CREDENTIALS['payos_client_id']
        existing_config.payos_api_key = PAYOS_CREDENTIALS['payos_api_key']
        existing_config.payos_checksum_key = PAYOS_CREDENTIALS['payos_checksum_key']
        existing_config.is_active = True
        existing_config.updated_at = datetime.utcnow()
        
        db.session.commit()
        print(" Đã cập nhật PayOS config")
        return existing_config
    else:
        print(" Tạo PayOS config mới...")
        config = PaymentConfig(
            owner_id=owner_id,
            payos_client_id=PAYOS_CREDENTIALS['payos_client_id'],
            payos_api_key=PAYOS_CREDENTIALS['payos_api_key'],
            payos_checksum_key=PAYOS_CREDENTIALS['payos_checksum_key'],
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(config)
        db.session.commit()
        
        print(" Đã tạo PayOS config mới")
        return config

def verify_setup():
    """Verify setup đã thành công"""
    print("\n Verify setup...")
    
    configs = PaymentConfig.query.all()
    print(f" Tìm thấy {len(configs)} payment configs:")
    
    for config in configs:
        owner = Owner.query.get(config.owner_id)
        if owner:
            owner_display = owner.full_name or owner.username or f"ID {owner.id}"
        else:
            owner_display = 'Unknown'
        print(f"  - Owner: {owner_display}")
        print(f"    Client ID: {config.payos_client_id[:8]}...")
        print(f"    API Key: {config.payos_api_key[:8]}...")
        print(f"    Checksum Key: {config.payos_checksum_key[:8]}...")
        print(f"    Active: {config.is_active}")
        print()

def main():
    """Main function"""
    print("[DEBUG] Đã vào hàm main!")
    print(" Bắt đầu setup PayOS credentials...")
    
    with flask_app.app_context():
        try:
            # Tạo owner
            owner = create_owner_if_not_exists()
            
            # Setup PayOS credentials
            config = setup_payos_credentials(owner.id)
            
            # Verify setup
            verify_setup()
            
            print("\n Setup PayOS credentials hoàn thành!")
            print("\n Thông tin PayOS đã được cấu hình:")
            print(f"  - Owner ID: {owner.id}")
            print(f"  - Config ID: {config.id}")
            print(f"  - Client ID: {config.payos_client_id}")
            print(f"  - API Key: {config.payos_api_key}")
            print(f"  - Checksum Key: {config.payos_checksum_key}")
            
        except Exception as e:
            print(f"[DEBUG] Lỗi khi setup: {e}")
            db.session.rollback()

if __name__ == "__main__":
    main() 