from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db, Admin, Owner, Renter, Room, Booking, Review, Amenity, RoomImage, Statistics

# Tạo ứng dụng Flask
app = Flask(__name__)
app.config.from_object(Config)

# Khởi tạo database
db.init_app(app)

def seed_amenities():
    with app.app_context():
        # Tạo các bảng nếu chưa tồn tại
        db.create_all()
        
        # Xóa tất cả tiện nghi hiện có
        Amenity.query.delete()
        
        # Tiện nghi phổ biến (common)
        common_amenities = [
            {
                'name': 'Wi-Fi miễn phí',
                'icon': 'bi-wifi',
                'category': 'common',
                'description': 'Kết nối internet tốc độ cao miễn phí'
            },
            {
                'name': 'Điều hòa',
                'icon': 'bi-thermometer-snow',
                'category': 'common',
                'description': 'Điều hòa nhiệt độ hai chiều'
            },
            {
                'name': 'TV màn hình phẳng',
                'icon': 'bi-tv',
                'category': 'common',
                'description': 'TV LED thông minh với các kênh giải trí đa dạng'
            },
            {
                'name': 'Nước nóng',
                'icon': 'bi-droplet-half',
                'category': 'common',
                'description': 'Hệ thống nước nóng trung tâm'
            },
            {
                'name': 'Bãi đỗ xe',
                'icon': 'bi-p-square',
                'category': 'common',
                'description': 'Bãi đỗ xe an toàn, có camera giám sát'
            },
            {
                'name': 'Thang máy',
                'icon': 'bi-elevator',
                'category': 'common',
                'description': 'Thang máy hiện đại, hoạt động 24/7'
            },
            {
                'name': 'An ninh 24/7',
                'icon': 'bi-shield-check',
                'category': 'common',
                'description': 'Bảo vệ và camera an ninh 24/7'
            },
            {
                'name': 'Dọn phòng',
                'icon': 'bi-brush',
                'category': 'common',
                'description': 'Dịch vụ dọn phòng hàng ngày'
            },
            {
                'name': 'Lễ tân 24/7',
                'icon': 'bi-person-workspace',
                'category': 'common',
                'description': 'Lễ tân phục vụ 24/7'
            },
            {
                'name': 'Thang bộ',
                'icon': 'bi-ladder',
                'category': 'common',
                'description': 'Thang bộ rộng rãi, thoát hiểm an toàn'
            }
        ]
        
        # Tiện nghi phòng (room)
        room_amenities = [
            {
                'name': 'Minibar',
                'icon': 'bi-cup-straw',
                'category': 'room',
                'description': 'Tủ lạnh mini với đồ uống và snack'
            },
            {
                'name': 'Két an toàn',
                'icon': 'bi-safe',
                'category': 'room',
                'description': 'Két sắt điện tử đựng đồ quý giá'
            },
            {
                'name': 'Bàn làm việc',
                'icon': 'bi-desk',
                'category': 'room',
                'description': 'Bàn làm việc rộng rãi với ghế êm ái'
            },
            {
                'name': 'Tủ quần áo',
                'icon': 'bi-door-closed',
                'category': 'room',
                'description': 'Tủ đựng quần áo rộng rãi với gương'
            },
            {
                'name': 'Máy sấy tóc',
                'icon': 'bi-wind',
                'category': 'room',
                'description': 'Máy sấy tóc công suất cao'
            },
            {
                'name': 'Bồn tắm',
                'icon': 'bi-water',
                'category': 'room',
                'description': 'Bồn tắm đứng với vòi sen cao cấp'
            },
            {
                'name': 'Đồ vệ sinh cá nhân',
                'icon': 'bi-basket',
                'category': 'room',
                'description': 'Bộ đồ vệ sinh cá nhân cao cấp'
            },
            {
                'name': 'Ấm đun nước',
                'icon': 'bi-cup-hot',
                'category': 'room',
                'description': 'Ấm đun nước điện với bộ pha trà, cà phê'
            },
            {
                'name': 'Rèm cửa tự động',
                'icon': 'bi-curtain',
                'category': 'room',
                'description': 'Rèm cửa điện thông minh'
            },
            {
                'name': 'Điện thoại bàn',
                'icon': 'bi-telephone',
                'category': 'room',
                'description': 'Điện thoại kết nối trực tiếp lễ tân'
            }
        ]
        
        # Tiện nghi độc đáo (unique)
        unique_amenities = [
            {
                'name': 'Ban công riêng',
                'icon': 'bi-door-open',
                'category': 'unique',
                'description': 'Ban công riêng với view thành phố'
            },
            {
                'name': 'Bồn tắm massage',
                'icon': 'bi-water',
                'category': 'unique',
                'description': 'Bồn tắm massage thư giãn'
            },
            {
                'name': 'Phòng gym mini',
                'icon': 'bi-bicycle',
                'category': 'unique',
                'description': 'Góc tập gym với thiết bị cơ bản'
            },
            {
                'name': 'Góc làm việc riêng',
                'icon': 'bi-briefcase',
                'category': 'unique',
                'description': 'Không gian làm việc riêng biệt'
            },
            {
                'name': 'Bếp mini',
                'icon': 'bi-fire',
                'category': 'unique',
                'description': 'Bếp nhỏ với dụng cụ nấu ăn cơ bản'
            },
            {
                'name': 'Smart TV cao cấp',
                'icon': 'bi-tv',
                'category': 'unique',
                'description': 'Smart TV 4K với Netflix, YouTube Premium'
            },
            {
                'name': 'Góc đọc sách',
                'icon': 'bi-book',
                'category': 'unique',
                'description': 'Góc đọc sách yên tĩnh với đèn đọc sách'
            },
            {
                'name': 'Máy pha cà phê',
                'icon': 'bi-cup',
                'category': 'unique',
                'description': 'Máy pha cà phê tự động với hạt cà phê'
            },
            {
                'name': 'Tủ rượu mini',
                'icon': 'bi-cup-fill',
                'category': 'unique',
                'description': 'Tủ rượu mini với các loại rượu cao cấp'
            },
            {
                'name': 'Hệ thống âm thanh',
                'icon': 'bi-speaker',
                'category': 'unique',
                'description': 'Hệ thống âm thanh vòm cao cấp'
            }
        ]
        
        # Thêm tất cả tiện nghi vào database
        all_amenities = common_amenities + room_amenities + unique_amenities
        for amenity_data in all_amenities:
            amenity = Amenity(**amenity_data)
            db.session.add(amenity)
        
        try:
            db.session.commit()
            print('Đã thêm thành công 30 tiện nghi vào database!')
            print('\nTiện nghi phổ biến:')
            for a in common_amenities:
                print(f"- {a['name']}")
            print('\nTiện nghi phòng:')
            for a in room_amenities:
                print(f"- {a['name']}")
            print('\nTiện nghi độc đáo:')
            for a in unique_amenities:
                print(f"- {a['name']}")
        except Exception as e:
            db.session.rollback()
            print(f'Lỗi khi thêm tiện nghi: {str(e)}')

if __name__ == '__main__':
    seed_amenities() 