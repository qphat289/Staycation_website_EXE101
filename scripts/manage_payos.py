#!/usr/bin/env python3
"""
Script để admin quản lý PayOS credentials cho từng owner
"""

import sys
import os
import importlib.util
import sys as _sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Also set it in the environment for subprocesses
os.environ['PYTHONPATH'] = project_root + (os.pathsep + os.environ.get('PYTHONPATH', ''))

app_py_path = os.path.join(project_root, 'app.py')
spec = importlib.util.spec_from_file_location('app_main', app_py_path)
app_module = importlib.util.module_from_spec(spec)
_sys.modules['app_main'] = app_module
spec.loader.exec_module(app_module)
flask_app = app_module.app

from app.models.models import db, PaymentConfig, Owner
from datetime import datetime

def list_all_owners():
    """Liệt kê tất cả owners và trạng thái PayOS config"""
    print("📋 Danh sách tất cả owners:")
    print("-" * 80)
    
    with flask_app.app_context():
        try:
            owners = Owner.query.all()
            configs = PaymentConfig.query.all()
            
            config_map = {config.owner_id: config for config in configs}
            
            for i, owner in enumerate(owners, 1):
                config = config_map.get(owner.id)
                status = "✅ Có config" if config else "❌ Chưa có"
                active_status = "🟢 Hoạt động" if config and config.is_active else "🔴 Không hoạt động" if config else ""
                
                print(f"{i:2d}. {owner.username} ({owner.full_name})")
                print(f"     Email: {owner.email}")
                print(f"     PayOS: {status} {active_status}")
                
                if config:
                    print(f"     Client ID: {config.payos_client_id[:8]}...")
                    print(f"     Cập nhật: {config.updated_at.strftime('%d/%m/%Y %H:%M')}")
                
                print("-" * 80)
            
            return owners, configs
            
        except Exception as e:
            print(f"❌ Lỗi khi lấy danh sách owners: {e}")
            return [], []

def setup_payos_for_owner(owner_id):
    """Thiết lập PayOS cho owner cụ thể"""
    print(f"\n🔧 Thiết lập PayOS cho owner ID {owner_id}...")
    
    with flask_app.app_context():
        try:
            owner = Owner.query.get(owner_id)
            if not owner:
                print("❌ Không tìm thấy owner!")
                return False
            
            print(f"Owner: {owner.username} ({owner.full_name})")
            
            # Nhập thông tin PayOS
            print("\nNhập thông tin PayOS:")
            client_id = input("Client ID: ").strip()
            api_key = input("API Key: ").strip()
            checksum_key = input("Checksum Key: ").strip()
            
            if not all([client_id, api_key, checksum_key]):
                print("❌ Vui lòng nhập đầy đủ thông tin!")
                return False
            
            # Kiểm tra config hiện tại
            existing_config = PaymentConfig.query.filter_by(owner_id=owner_id).first()
            
            if existing_config:
                # Cập nhật
                existing_config.payos_client_id = client_id
                existing_config.payos_api_key = api_key
                existing_config.payos_checksum_key = checksum_key
                existing_config.is_active = True
                existing_config.updated_at = datetime.utcnow()
                print("✅ Đã cập nhật PayOS config")
            else:
                # Tạo mới
                config = PaymentConfig(
                    owner_id=owner_id,
                    payos_client_id=client_id,
                    payos_api_key=api_key,
                    payos_checksum_key=checksum_key,
                    is_active=True
                )
                db.session.add(config)
                print("✅ Đã tạo PayOS config mới")
            
            db.session.commit()
            return True
            
        except Exception as e:
            print(f"❌ Lỗi khi thiết lập PayOS: {e}")
            db.session.rollback()
            return False

def update_payos_for_owner(owner_id):
    """Cập nhật PayOS cho owner cụ thể"""
    print(f"\n🔄 Cập nhật PayOS cho owner ID {owner_id}...")
    
    with flask_app.app_context():
        try:
            owner = Owner.query.get(owner_id)
            config = PaymentConfig.query.filter_by(owner_id=owner_id).first()
            
            if not owner:
                print("❌ Không tìm thấy owner!")
                return False
            
            if not config:
                print("❌ Owner chưa có PayOS config!")
                return False
            
            print(f"Owner: {owner.username} ({owner.full_name})")
            print(f"Client ID hiện tại: {config.payos_client_id[:8]}...")
            
            # Nhập thông tin mới
            print("\nNhập thông tin PayOS mới (Enter để giữ nguyên):")
            client_id = input(f"Client ID [{config.payos_client_id[:8]}...]: ").strip()
            api_key = input("API Key (Enter để giữ nguyên): ").strip()
            checksum_key = input("Checksum Key (Enter để giữ nguyên): ").strip()
            
            # Cập nhật nếu có thay đổi
            if client_id:
                config.payos_client_id = client_id
            if api_key:
                config.payos_api_key = api_key
            if checksum_key:
                config.payos_checksum_key = checksum_key
            
            config.updated_at = datetime.utcnow()
            db.session.commit()
            
            print("✅ Đã cập nhật PayOS config")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi khi cập nhật PayOS: {e}")
            db.session.rollback()
            return False

def delete_payos_for_owner(owner_id):
    """Xóa PayOS config cho owner cụ thể"""
    print(f"\n🗑️ Xóa PayOS config cho owner ID {owner_id}...")
    
    with flask_app.app_context():
        try:
            owner = Owner.query.get(owner_id)
            config = PaymentConfig.query.filter_by(owner_id=owner_id).first()
            
            if not owner:
                print("❌ Không tìm thấy owner!")
                return False
            
            if not config:
                print("❌ Owner chưa có PayOS config!")
                return False
            
            print(f"Owner: {owner.username} ({owner.full_name})")
            print(f"Client ID: {config.payos_client_id[:8]}...")
            
            confirm = input("\n⚠️ Bạn có chắc chắn muốn xóa? (y/N): ")
            if confirm.lower() != 'y':
                print("❌ Đã hủy thao tác.")
                return False
            
            db.session.delete(config)
            db.session.commit()
            
            print("✅ Đã xóa PayOS config")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi khi xóa PayOS: {e}")
            db.session.rollback()
            return False

def toggle_payos_status(owner_id):
    """Bật/tắt PayOS config cho owner"""
    print(f"\n🔄 Thay đổi trạng thái PayOS cho owner ID {owner_id}...")
    
    with flask_app.app_context():
        try:
            owner = Owner.query.get(owner_id)
            config = PaymentConfig.query.filter_by(owner_id=owner_id).first()
            
            if not owner:
                print("❌ Không tìm thấy owner!")
                return False
            
            if not config:
                print("❌ Owner chưa có PayOS config!")
                return False
            
            print(f"Owner: {owner.username} ({owner.full_name})")
            print(f"Trạng thái hiện tại: {'🟢 Hoạt động' if config.is_active else '🔴 Không hoạt động'}")
            
            config.is_active = not config.is_active
            config.updated_at = datetime.utcnow()
            db.session.commit()
            
            new_status = "🟢 Hoạt động" if config.is_active else "🔴 Không hoạt động"
            print(f"✅ Đã thay đổi trạng thái thành: {new_status}")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi khi thay đổi trạng thái: {e}")
            db.session.rollback()
            return False

def main():
    """Main function"""
    print("🚀 PayOS Management Tool")
    print("=" * 50)
    
    while True:
        print("\n📋 Menu:")
        print("1. Xem danh sách owners")
        print("2. Thiết lập PayOS cho owner")
        print("3. Cập nhật PayOS cho owner")
        print("4. Xóa PayOS config")
        print("5. Bật/tắt PayOS config")
        print("0. Thoát")
        
        choice = input("\nChọn tùy chọn (0-5): ").strip()
        
        if choice == '0':
            print("👋 Tạm biệt!")
            break
        
        elif choice == '1':
            list_all_owners()
        
        elif choice == '2':
            owner_id = input("Nhập Owner ID: ").strip()
            if owner_id.isdigit():
                setup_payos_for_owner(int(owner_id))
            else:
                print("❌ ID không hợp lệ!")
        
        elif choice == '3':
            owner_id = input("Nhập Owner ID: ").strip()
            if owner_id.isdigit():
                update_payos_for_owner(int(owner_id))
            else:
                print("❌ ID không hợp lệ!")
        
        elif choice == '4':
            owner_id = input("Nhập Owner ID: ").strip()
            if owner_id.isdigit():
                delete_payos_for_owner(int(owner_id))
            else:
                print("❌ ID không hợp lệ!")
        
        elif choice == '5':
            owner_id = input("Nhập Owner ID: ").strip()
            if owner_id.isdigit():
                toggle_payos_status(int(owner_id))
            else:
                print("❌ ID không hợp lệ!")
        
        else:
            print("❌ Tùy chọn không hợp lệ!")

if __name__ == "__main__":
    main() 