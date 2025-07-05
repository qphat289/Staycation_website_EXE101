#!/usr/bin/env python3
"""
Script để kiểm tra các owner đã có trong database
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

from app.models.models import db, Owner, PaymentConfig

def check_existing_owners():
    """Kiểm tra các owner đã có trong database"""
    print("🔍 Kiểm tra các owner đã có trong database...")
    
    owners = Owner.query.all()
    
    if not owners:
        print(" Không có owner nào trong database!")
        return None
    
    print(f" Tìm thấy {len(owners)} owner(s):")
    print("-" * 50)
    
    for i, owner in enumerate(owners, 1):
        print(f"{i}. ID: {owner.id}")
        print(f"   Username: {owner.username}")
        print(f"   Email: {owner.email}")
        print(f"   Full Name: {owner.full_name}")
        print(f"   Phone: {owner.phone}")
        print(f"   Address: {owner.address}")
        print(f"   Created: {owner.created_at}")
        
        # Kiểm tra payment config
        payment_config = PaymentConfig.query.filter_by(owner_id=owner.id).first()
        if payment_config:
            print(f"    Đã có PayOS config (ID: {payment_config.id})")
            print(f"      Client ID: {payment_config.payos_client_id[:8]}...")
            print(f"      Active: {payment_config.is_active}")
        else:
            print(f"    Chưa có PayOS config")
        
        print("-" * 50)
    
    return owners

def main():
    """Main function"""
    print(" Bắt đầu kiểm tra owners...")
    
    with flask_app.app_context():
        try:
            owners = check_existing_owners()
            
            if owners:
                print(f"\n Tổng kết:")
                print(f"  - Tổng số owner: {len(owners)}")
                
                # Đếm số owner có payment config
                configs = PaymentConfig.query.all()
                print(f"  - Owner có PayOS config: {len(configs)}")
                print(f"  - Owner chưa có PayOS config: {len(owners) - len(configs)}")
                
                if len(owners) > 1:
                    print(f"\n💡 Gợi ý: Bạn có thể chọn owner nào để setup PayOS credentials:")
                    for owner in owners:
                        config = PaymentConfig.query.filter_by(owner_id=owner.id).first()
                        status = " Đã có config" if config else " Chưa có config"
                        print(f"  - {owner.username} ({owner.full_name}): {status}")
            
        except Exception as e:
            print(f" Lỗi khi kiểm tra: {e}")

if __name__ == "__main__":
    main() 