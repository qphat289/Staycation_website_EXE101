from models import db, Owner
from werkzeug.security import generate_password_hash
from datetime import datetime

def seed_owners():
    # Xóa dữ liệu cũ
    Owner.query.delete()
    
    # Danh sách 10 owner mẫu
    owners_data = [
        {
            'username': 'nguyenvana',
            'email': 'nguyenvana@gmail.com',
            'password': 'password123',
            'full_name': 'Nguyễn Văn A',
            'phone': '0901234567',
            'personal_id': '001234567890',
            'is_active': True
        },
        {
            'username': 'tranthib',
            'email': 'tranthib@gmail.com',
            'password': 'password123',
            'full_name': 'Trần Thị B',
            'phone': '0912345678',
            'personal_id': '001234567891',
            'is_active': True
        },
        {
            'username': 'phamvanc',
            'email': 'phamvanc@gmail.com',
            'password': 'password123',
            'full_name': 'Phạm Văn C',
            'phone': '0923456789',
            'personal_id': '001234567892',
            'is_active': False
        },
        {
            'username': 'lethid',
            'email': 'lethid@gmail.com',
            'password': 'password123',
            'full_name': 'Lê Thị D',
            'phone': '0934567890',
            'personal_id': '001234567893',
            'is_active': True
        },
        {
            'username': 'hoangvane',
            'email': 'hoangvane@gmail.com',
            'password': 'password123',
            'full_name': 'Hoàng Văn E',
            'phone': '0945678901',
            'personal_id': '001234567894',
            'is_active': True
        },
        {
            'username': 'ngothif',
            'email': 'ngothif@gmail.com',
            'password': 'password123',
            'full_name': 'Ngô Thị F',
            'phone': '0956789012',
            'personal_id': '001234567895',
            'is_active': False
        },
        {
            'username': 'vuvanG',
            'email': 'vuvang@gmail.com',
            'password': 'password123',
            'full_name': 'Vũ Văn G',
            'phone': '0967890123',
            'personal_id': '001234567896',
            'is_active': True
        },
        {
            'username': 'dothih',
            'email': 'dothih@gmail.com',
            'password': 'password123',
            'full_name': 'Đỗ Thị H',
            'phone': '0978901234',
            'personal_id': '001234567897',
            'is_active': True
        },
        {
            'username': 'buivani',
            'email': 'buivani@gmail.com',
            'password': 'password123',
            'full_name': 'Bùi Văn I',
            'phone': '0989012345',
            'personal_id': '001234567898',
            'is_active': False
        },
        {
            'username': 'maithik',
            'email': 'maithik@gmail.com',
            'password': 'password123',
            'full_name': 'Mai Thị K',
            'phone': '0990123456',
            'personal_id': '001234567899',
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
            personal_id=owner_data['personal_id'],
            is_active=owner_data['is_active']
        )
        owner.password_hash = generate_password_hash(owner_data['password'])
        db.session.add(owner)
    
    # Lưu vào database
    db.session.commit()
    print("Đã thêm 10 owner mẫu vào database!") 