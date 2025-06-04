from models import db, Owner
from werkzeug.security import generate_password_hash
from datetime import datetime

def seed_owners():
    # Xóa dữ liệu cũ
    Owner.query.delete()
    
    # Danh sách 10 owner mẫu
    owners_data = [
        {
            'username': 'owner1',
            'email': 'owner1@example.com',
            'password': 'password123',
            'full_name': 'Owner One',
            'phone': '0123456789',
            'is_active': True
        },
        {
            'username': 'owner2', 
            'email': 'owner2@example.com',
            'password': 'password123',
            'full_name': 'Owner Two',
            'phone': '0123456790',
            'is_active': True
        }
    ]
    
    # Thêm từng owner vào database
    for owner_data in owners_data:
        owner = Owner(
            username=owner_data['username'],
            email=owner_data['email'],
            full_name=owner_data['full_name'],
            phone=owner_data['phone'],
            is_active=owner_data['is_active']
        )
        owner.set_password(owner_data['password'])
        db.session.add(owner)
    
    try:
        db.session.commit()
        print("✓ Seeded owners successfully")
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error seeding owners: {str(e)}") 