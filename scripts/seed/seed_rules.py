    
import sys
import os

# Add the project root to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from flask import Flask
from config.config import Config
from app.models.models import db, Rule

# Tạo ứng dụng Flask
app = Flask(__name__)
app.config.from_object(Config)

# Khởi tạo database
db.init_app(app)

# Dữ liệu nội quy chuẩn - THỰC SỰ LÀ NỘI QUY CHỨ KHÔNG PHẢI TIỆN NGHI
RULES_DATA = [
    # Smoking rules
    {
        'name': 'Không hút thuốc',
        'icon': 'bi-x-circle',
        'type': 'not_allowed',
        'category': 'smoking',
        'description': 'Không được phép hút thuốc trong phòng'
    },
    {
        'name': 'Được phép hút thuốc',
        'icon': 'bi-check-circle',
        'type': 'allowed',
        'category': 'smoking',
        'description': 'Khách được phép hút thuốc trong phòng'
    },
    {
        'name': 'Hút thuốc ngoài ban công',
        'icon': 'bi-check-circle',
        'type': 'allowed',
        'category': 'smoking',
        'description': 'Chỉ được hút thuốc ở ban công'
    },
    
    # Pet rules
    {
        'name': 'Không mang thú cưng',
        'icon': 'bi-x-circle',
        'type': 'not_allowed',
        'category': 'pets',
        'description': 'Không cho phép mang thú cưng vào phòng'
    },
    {
        'name': 'Được mang thú cưng',
        'icon': 'bi-check-circle',
        'type': 'allowed',
        'category': 'pets',
        'description': 'Khách được phép mang thú cưng'
    },
    {
        'name': 'Phí thêm cho thú cưng',
        'icon': 'bi-currency-dollar',
        'type': 'allowed',
        'category': 'pets',
        'description': 'Cho phép thú cưng với phí phụ thu'
    },
    
    # Children rules
    {
        'name': 'Không phù hợp trẻ em',
        'icon': 'bi-x-circle',
        'type': 'not_allowed',
        'category': 'children',
        'description': 'Phòng không thích hợp cho trẻ em dưới 12 tuổi'
    },
    {
        'name': 'Thân thiện trẻ em',
        'icon': 'bi-check-circle',
        'type': 'allowed',
        'category': 'children',
        'description': 'Phòng phù hợp và an toàn cho trẻ em'
    },
    {
        'name': 'Trẻ em cần giám sát',
        'icon': 'bi-eye',
        'type': 'allowed',
        'category': 'children',
        'description': 'Trẻ em phải có người lớn giám sát'
    },
    
    # Party/Events rules
    {
        'name': 'Không tổ chức tiệc',
        'icon': 'bi-x-circle',
        'type': 'not_allowed',
        'category': 'party',
        'description': 'Không được tổ chức tiệc tùng, ăn mừng'
    },
    {
        'name': 'Tiệc nhỏ dưới 10 người',
        'icon': 'bi-people',
        'type': 'allowed',
        'category': 'party',
        'description': 'Cho phép tổ chức tiệc nhỏ dưới 10 người'
    },
    {
        'name': 'Không nhạc lớn',
        'icon': 'bi-volume-down',
        'type': 'not_allowed',
        'category': 'party',
        'description': 'Không mở nhạc quá to ảnh hưởng hàng xóm'
    },
    
    # Time rules
    {
        'name': 'Yên lặng sau 22h',
        'icon': 'bi-moon',
        'type': 'not_allowed',
        'category': 'time',
        'description': 'Giữ yên lặng sau 22h để tôn trọng hàng xóm'
    },
    {
        'name': 'Check-in sau 15h',
        'icon': 'bi-clock',
        'type': 'allowed',
        'category': 'time',
        'description': 'Thời gian check-in từ 15h trở đi'
    },
    {
        'name': 'Check-out trước 11h',
        'icon': 'bi-clock-history',
        'type': 'not_allowed',
        'category': 'time',
        'description': 'Khách cần check-out trước 11h sáng'
    },
    {
        'name': 'Không khách qua đêm',
        'icon': 'bi-person-x',
        'type': 'not_allowed',
        'category': 'time',
        'description': 'Không cho phép khách khác qua đêm'
    },
    
    # Behavior rules
    {
        'name': 'Giữ gìn vệ sinh',
        'icon': 'bi-house-heart',
        'type': 'allowed',
        'category': 'behavior',
        'description': 'Khách cần giữ gìn vệ sinh chung'
    },
    {
        'name': 'Không làm hỏng đồ đạc',
        'icon': 'bi-shield-exclamation',
        'type': 'not_allowed',
        'category': 'behavior',
        'description': 'Không làm hỏng tài sản trong phòng'
    },
    {
        'name': 'Báo trước khi rời đi',
        'icon': 'bi-telephone',
        'type': 'allowed',
        'category': 'behavior',
        'description': 'Thông báo chủ nhà trước khi check-out'
    },
    {
        'name': 'Không mang bạn về',
        'icon': 'bi-person-plus',
        'type': 'not_allowed',
        'category': 'behavior',
        'description': 'Không mang người lạ về phòng'
    },
    {
        'name': 'Đúng số người đăng ký',
        'icon': 'bi-people-fill',
        'type': 'allowed',
        'category': 'behavior',
        'description': 'Chỉ đúng số người đã đăng ký'
    }
]

def seed_rules():
    """Import dữ liệu nội quy vào database"""
    with app.app_context():
        try:
            print("Bắt đầu import dữ liệu nội quy...")
            
            # Xóa dữ liệu cũ nếu có
            Rule.query.delete()
            db.session.commit()
            print("Đã xóa dữ liệu nội quy cũ")
            
            # Import từng nội quy
            for rule_data in RULES_DATA:
                print(f"Đang import: {rule_data['name']}")
                
                rule = Rule(
                    name=rule_data['name'],
                    icon=rule_data['icon'],
                    type=rule_data['type'],
                    category=rule_data['category'],
                    description=rule_data['description']
                )
                db.session.add(rule)
            
            # Commit tất cả
            db.session.commit()
            print("Import dữ liệu nội quy thành công!")
            
            # Thống kê
            total_rules = Rule.query.count()
            allowed_rules = Rule.query.filter_by(type='allowed').count()
            not_allowed_rules = Rule.query.filter_by(type='not_allowed').count()
            
            print(f"Đã import:")
            print(f"  - {total_rules} nội quy tổng cộng")
            print(f"  - {allowed_rules} nội quy cho phép")
            print(f"  - {not_allowed_rules} nội quy không cho phép")
            
        except Exception as e:
            db.session.rollback()
            print(f"Lỗi khi import dữ liệu nội quy: {e}")
            raise

if __name__ == '__main__':
    seed_rules() 