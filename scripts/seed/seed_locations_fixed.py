#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# Add the project root to Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from app.models.models import db, Province, District, Ward
from flask import Flask
from config.config import Config

# Tạo Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Khởi tạo database
db.init_app(app)

# Dữ liệu địa chỉ - Cập nhật 2024 với cấu trúc hành chính mới nhất
LOCATION_DATA = {
    'hcm': {
        'name': 'TP. Hồ Chí Minh',
        'districts': {
            # Các quận nội thành (theo thứ tự số)
            'quan1': {
                'name': 'Quận 1',
                'wards': ['Phường Tân Định', 'Phường Đa Kao', 'Phường Bến Nghé', 'Phường Bến Thành', 'Phường Nguyễn Thái Bình', 'Phường Phạm Ngũ Lão', 'Phường Cầu Ông Lãnh', 'Phường Cô Giang', 'Phường Nguyễn Cư Trinh', 'Phường Cầu Kho']
            },
            'quan3': {
                'name': 'Quận 3',
                'wards': ['Phường 1', 'Phường 2', 'Phường 3', 'Phường 4', 'Phường 5', 'Phường 6', 'Phường 7', 'Phường 8', 'Phường 9', 'Phường 10', 'Phường 11', 'Phường 12', 'Phường 13', 'Phường 14']
            },
            'quan4': {
                'name': 'Quận 4',
                'wards': ['Phường 1', 'Phường 2', 'Phường 3', 'Phường 4', 'Phường 6', 'Phường 8', 'Phường 9', 'Phường 10', 'Phường 13', 'Phường 14', 'Phường 15', 'Phường 16', 'Phường 18']
            },
            'quan5': {
                'name': 'Quận 5',
                'wards': ['Phường 1', 'Phường 2', 'Phường 3', 'Phường 4', 'Phường 5', 'Phường 6', 'Phường 7', 'Phường 8', 'Phường 9', 'Phường 10', 'Phường 11', 'Phường 12', 'Phường 13', 'Phường 14', 'Phường 15']
            },
            'quan6': {
                'name': 'Quận 6',
                'wards': ['Phường 1', 'Phường 2', 'Phường 3', 'Phường 4', 'Phường 5', 'Phường 6', 'Phường 7', 'Phường 8', 'Phường 9', 'Phường 10', 'Phường 11', 'Phường 12', 'Phường 13', 'Phường 14']
            },
            'quan7': {
                'name': 'Quận 7',
                'wards': ['Phường Tân Thuận Đông', 'Phường Tân Thuận Tây', 'Phường Tân Kiểng', 'Phường Tân Hưng', 'Phường Bình Thuận', 'Phường Tân Quy', 'Phường Phú Thuận', 'Phường Tân Phú', 'Phường Tân Phong', 'Phường Phú Mỹ']
            },
            'quan8': {
                'name': 'Quận 8',
                'wards': ['Phường 1', 'Phường 2', 'Phường 3', 'Phường 4', 'Phường 5', 'Phường 6', 'Phường 7', 'Phường 8', 'Phường 9', 'Phường 10', 'Phường 11', 'Phường 12', 'Phường 13', 'Phường 14', 'Phường 15', 'Phường 16']
            },
            'quan10': {
                'name': 'Quận 10',
                'wards': ['Phường 1', 'Phường 2', 'Phường 4', 'Phường 5', 'Phường 6', 'Phường 7', 'Phường 8', 'Phường 9', 'Phường 10', 'Phường 11', 'Phường 12', 'Phường 13', 'Phường 14', 'Phường 15']
            },
            'quan11': {
                'name': 'Quận 11',
                'wards': ['Phường 1', 'Phường 2', 'Phường 3', 'Phường 4', 'Phường 5', 'Phường 6', 'Phường 7', 'Phường 8', 'Phường 9', 'Phường 10', 'Phường 11', 'Phường 12', 'Phường 13', 'Phường 14', 'Phường 15', 'Phường 16']
            },
            'quan12': {
                'name': 'Quận 12',
                'wards': ['Phường Thạnh Xuân', 'Phường Thạnh Lộc', 'Phường Hiệp Thành', 'Phường Thới An', 'Phường Tân Chánh Hiệp', 'Phường An Phú Đông', 'Phường Tân Thới Hiệp', 'Phường Trung Mỹ Tây', 'Phường Tân Hưng Thuận', 'Phường Đông Hưng Thuận', 'Phường Tân Thới Nhất']
            },
            
            # Các quận có tên (theo thứ tự alphabet)
            'quanbinhtan': {
                'name': 'Quận Bình Tân',
                'wards': ["Phường An Lạc","Phường An Lạc A", "Phường Bình Hưng Hòa","Phường Bình Hưng Hòa A","Phường Bình Hưng Hòa B","Phường Bình Trị Đông","Phường Bình Trị Đông A","Phường Bình Trị Đông B","Phường Tân Tạo","Phường Tân Tạo A"
      ]
            },
            'quanbinhthanh': {
                'name': 'Quận Bình Thạnh',
                'wards': ['Phường 1', 'Phường 2', 'Phường 3', 'Phường 5', 'Phường 6', 'Phường 7', 'Phường 11', 'Phường 12', 'Phường 13', 'Phường 14', 'Phường 15', 'Phường 17', 'Phường 19', 'Phường 21', 'Phường 22', 'Phường 24', 'Phường 25', 'Phường 26', 'Phường 27', 'Phường 28']
            },
            'quangovap': {
                'name': 'Quận Gò Vấp',
                'wards': ['Phường 1', 'Phường 3', 'Phường 4', 'Phường 5', 'Phường 6', 'Phường 7', 'Phường 8', 'Phường 9', 'Phường 10', 'Phường 11', 'Phường 12', 'Phường 13', 'Phường 14', 'Phường 15', 'Phường 16', 'Phường 17']
            },
            'quanphunhuan': {
                'name': 'Quận Phú Nhuận',
                'wards': ['Phường 1', 'Phường 2', 'Phường 3', 'Phường 4', 'Phường 5', 'Phường 7', 'Phường 8', 'Phường 9', 'Phường 10', 'Phường 11', 'Phường 13', 'Phường 15', 'Phường 17']
            },
            'quantanbinh': {
                'name': 'Quận Tân Bình',
                'wards': ['Phường 1', 'Phường 2', 'Phường 3', 'Phường 4', 'Phường 5', 'Phường 6', 'Phường 7', 'Phường 8', 'Phường 9', 'Phường 10', 'Phường 11', 'Phường 12', 'Phường 13', 'Phường 14', 'Phường 15']
            },
            'quantanphu': {
                'name': 'Quận Tân Phú',
                'wards': ['Phường Tân Sơn Nhì', 'Phường Tây Thạnh', 'Phường Sơn Kỳ', 'Phường Tân Quý', 'Phường Tân Thành', 'Phường Phú Thọ Hòa', 'Phường Phú Thạnh', 'Phường Phú Trung', 'Phường Hòa Thạnh', 'Phường Hiệp Tân', 'Phường Tân Thới Hòa']
            },
            
            # 5 Huyện ngoại thành
            'huyenbinhchanh': {
                'name': 'Huyện Bình Chánh',
                'wards': [
                    'Thị trấn Tân Túc', 'Xã Phạm Văn Hai', 'Xã Vĩnh Lộc A', 'Xã Vĩnh Lộc B', 
                    'Xã Bình Lợi', 'Xã Lê Minh Xuân', 'Xã Tân Nhựt', 'Xã Tân Kiên', 
                    'Xã Bình Hưng', 'Xã Phong Phú', 'Xã An Phú Tây', 'Xã Hưng Long', 
                    'Xã Đa Phước', 'Xã Tân Quý Tây', 'Xã Bình Chánh', 'Xã Quy Đức'
                ]
            },
            'huyencangio': {
                'name': 'Huyện Cần Giờ',
                'wards': [
                    'Thị trấn Cần Thạnh', 'Xã Bình Khánh', 'Xã Tam Thôn Hiệp', 'Xã An Thới Đông', 
                    'Xã Thạnh An', 'Xã Long Hòa', 'Xã Lý Nhơn'
                ]
            },
            'huyencuchi': {
                'name': 'Huyện Củ Chi',
                'wards': [
                    'Thị trấn Củ Chi', 'Xã Phú Mỹ Hưng', 'Xã An Phú', 'Xã Trung Lập Thượng', 
                    'Xã An Nhơn Tây', 'Xã Nhuận Đức', 'Xã Phạm Văn Cội', 'Xã Phú Hòa Đông', 
                    'Xã Trung Lập Hạ', 'Xã Trung An', 'Xã Phước Thạnh', 'Xã Phước Hiệp', 
                    'Xã Tân An Hội', 'Xã Phước Vĩnh An', 'Xã Thái Mỹ', 'Xã Tân Thạnh Tây', 
                    'Xã Hòa Phú', 'Xã Trung Hòa', 'Xã Nhị Bình', 'Xã Bình Mỹ', 'Xã Tân Phú Trung'
                ]
            },
            'huyenhocmon': {
                'name': 'Huyện Hóc Môn',
                'wards': [
                    'Thị trấn Hóc Môn', 'Xã Tân Hiệp', 'Xã Nhị Bình', 'Xã Đông Thạnh', 
                    'Xã Tân Thới Nhì', 'Xã Thới Tam Thôn', 'Xã Xuân Thới Sơn', 'Xã Tân Xuân', 
                    'Xã Xuân Thới Đông', 'Xã Trung Chánh', 'Xã Xuân Thới Thượng', 'Xã Bà Điểm'
                ]
            },
            'huyennhabe': {
                'name': 'Huyện Nhà Bè',
                'wards': [
                    'Thị trấn Nhà Bè', 'Xã Phước Kiển', 'Xã Phước Lộc', 'Xã Nhơn Đức', 
                    'Xã Phú Xuân', 'Xã Long Thới', 'Xã Hiệp Phước'
                ]
            },
            
            # Thành phố Thủ Đức (đặt cuối cùng sau tất cả Huyện)
            'thuduc': {
                'name': 'Thành phố Thủ Đức',
                'wards': [
                    # Khu vực cũ thuộc Quận 2
                    'Phường Thảo Điền', 'Phường An Phú', 'Phường An Khánh', 'Phường Bình An', 
                    'Phường Bình Khanh', 'Phường Bình Trưng Đông', 'Phường Bình Trưng Tây', 
                    'Phường Cát Lái', 'Phường Thạnh Mỹ Lợi', 'Phường An Lợi Đông', 'Phường Thủ Thiêm',
                    
                    # Khu vực cũ thuộc Quận 9  
                    'Phường Long Bình', 'Phường Long Thạnh Mỹ', 'Phường Tân Phú', 'Phường Hiệp Phú', 
                    'Phường Tăng Nhơn Phú A', 'Phường Tăng Nhơn Phú B', 'Phường Phước Long A', 
                    'Phường Phước Long B', 'Phường Trường Thạnh', 'Phường Long Phước', 
                    'Phường Long Trường', 'Phường Phước Bình', 'Phường Phú Hữu',
                    
                    # Khu vực cũ thuộc Quận Thủ Đức
                    'Phường Linh Xuân', 'Phường Bình Chiểu', 'Phường Linh Trung', 'Phường Tam Bình', 
                    'Phường Tam Phú', 'Phường Hiệp Bình Phước', 'Phường Hiệp Bình Chánh', 
                    'Phường Linh Chiểu', 'Phường Linh Đông', 'Phường Bình Thọ', 'Phường Trường Thọ'
                ]
            }
        }
    },
    'hanoi': {
        'name': 'Hà Nội',
        'districts': {
            'quanbadinh': {
                'name': 'Quận Ba Đình',
                'wards': ['Phường Phúc Xá', 'Phường Trúc Bạch', 'Phường Vĩnh Phúc', 'Phường Cống Vị', 'Phường Liễu Giai', 'Phường Nguyễn Trung Trực', 'Phường Quán Thánh', 'Phường Ngọc Hà', 'Phường Điện Biên', 'Phường Đội Cấn', 'Phường Ngọc Khánh', 'Phường Kim Mã', 'Phường Giảng Võ', 'Phường Thành Công']
            },
            'quanhoankieu': {
                'name': 'Quận Hoàn Kiếm',
                'wards': ['Phường Phúc Tấn', 'Phường Đồng Xuân', 'Phường Hàng Mã', 'Phường Hàng Buồm', 'Phường Hàng Đào', 'Phường Hàng Bồ', 'Phường Cửa Đông', 'Phường Lý Thái Tổ', 'Phường Hàng Bạc', 'Phường Hàng Gai', 'Phường Chương Dương Độ', 'Phường Hàng Trống', 'Phường Cửa Nam', 'Phường Hàng Bông', 'Phường Tràng Tiền', 'Phường Trần Hưng Đạo', 'Phường Phan Chu Trinh']
            },
            'quantayho': {
                'name': 'Quận Tây Hồ',
                'wards': ['Phường Phú Thượng', 'Phường Nhật Tân', 'Phường Tứ Liên', 'Phường Quảng An', 'Phường Xuân La', 'Phường Yên Phụ', 'Phường Bưởi', 'Phường Thụy Khuê']
            },
            'quanlongbien': {
                'name': 'Quận Long Biên',
                'wards': ['Phường Thượng Thanh', 'Phường Ngọc Lâm', 'Phường Gia Thụy', 'Phường Ngọc Thụy', 'Phường Giang Biên', 'Phường Việt Hưng', 'Phường Long Biên', 'Phường Thạch Bàn', 'Phường Phúc Lợi', 'Phường Bo Đề', 'Phường Sài Đồng', 'Phường Phúc Đông', 'Phường Cự Khối']
            },
            'quancaugiay': {
                'name': 'Quận Cầu Giấy',
                'wards': ['Phường Nghĩa Đô', 'Phường Nghĩa Tân', 'Phường Mai Dịch', 'Phường Dịch Vọng', 'Phường Dịch Vọng Hậu', 'Phường Quan Hoa', 'Phường Yên Hòa', 'Phường Trung Hòa']
            },
            'quandongda': {
                'name': 'Quận Đống Đa',
                'wards': ['Phường Cát Linh', 'Phường Văn Miếu', 'Phường Quốc Tử Giám', 'Phường Láng Thượng', 'Phường Ô Chợ Dừa', 'Phường Văn Chương', 'Phường Hàng Bột', 'Phường Láng Hạ', 'Phường Khâm Thiên', 'Phường Thổ Quan', 'Phường Nam Đồng', 'Phường Trung Phụng', 'Phường Quang Trung', 'Phường Trung Liệt', 'Phường Phương Liên', 'Phường Thịnh Quang', 'Phường Trung Tự', 'Phường Kim Liên', 'Phường Phương Mai', 'Phường Ngã Tư Sở', 'Phường Khương Thượng']
            },
            'quanhaibatrung': {
                'name': 'Quận Hai Bà Trưng',
                'wards': ['Phường Nguyễn Du', 'Phường Bạch Đằng', 'Phường Phạm Đình Hổ', 'Phường Lê Đại Hành', 'Phường Đồng Nhân', 'Phường Phố Huế', 'Phường Đống Mác', 'Phường Thanh Lương', 'Phường Thanh Nhàn', 'Phường Cầu Dền', 'Phường Bách Khoa', 'Phường Đồng Tâm', 'Phường Vĩnh Tuy', 'Phường Bạch Mai', 'Phường Quỳnh Mai', 'Phường Quỳnh Lôi', 'Phường Minh Khai', 'Phường Trương Định']
            },
            'quanhoangmai': {
                'name': 'Quận Hoàng Mai',
                'wards': ['Phường Thanh Trì', 'Phường Vĩnh Hưng', 'Phường Định Công', 'Phường Mai Động', 'Phường Tương Mai', 'Phường Đại Kim', 'Phường Tân Mai', 'Phường Hoàng Văn Thụ', 'Phường Trần Phú', 'Phường Hoàng Liệt', 'Phường Lĩnh Nam', 'Phường Thịnh Liệt', 'Phường Giáp Bát', 'Phường Yên Sở']
            },
            'quanthanxuan': {
                'name': 'Quận Thanh Xuân',
                'wards': ['Phường Hạ Đình', 'Phường Thanh Xuân Bắc', 'Phường Thanh Xuân Nam', 'Phường Khương Trung', 'Phường Khương Mai', 'Phường Nhân Chính', 'Phường Thượng Đình', 'Phường Khương Đình', 'Phường Phương Liệt', 'Phường Thanh Xuân Trung', 'Phường Kim Giang']
            },
            'quannamtuliem': {
                'name': 'Quận Nam Từ Liêm',
                'wards': ['Phường Mễ Trì', 'Phường Phú Đô', 'Phường Phương Canh', 'Phường Mỹ Đình 1', 'Phường Mỹ Đình 2', 'Phường Tây Mỗ', 'Phường Đại Mỗ', 'Phường Trung Văn']
            },
            'quanbactuliem': {
                'name': 'Quận Bắc Từ Liêm',
                'wards': ['Phường Thượng Cát', 'Phường Liên Mạc', 'Phường Đông Ngạc', 'Phường Đức Thắng', 'Phường Thụy Phương', 'Phường Tây Tựu', 'Phường Xuân Phương', 'Phường Xuân Tảo', 'Phường Minh Khai', 'Phường Cổ Nhuế 1', 'Phường Cổ Nhuế 2', 'Phường Phú Diễn', 'Phường Phúc Diễn']
            },
            'quanhadong': {
                'name': 'Quận Hà Đông',
                'wards': ['Phường Nguyễn Trãi', 'Phường Mộ Lao', 'Phường Hà Cầu', 'Phường Văn Quán', 'Phường Vạn Phúc', 'Phường Yên Nghĩa', 'Phường La Khê', 'Phường Phú La', 'Phường Phú Lãm', 'Phường Phú Lương', 'Phường Kiến Hưng', 'Phường Phúc La', 'Phường Quang Trung', 'Phường Dương Nội', 'Phường Đồng Mai', 'Phường Biên Giang']
            },
            'thixasontay': {
                'name': 'Thị xã Sơn Tây',
                'wards': ['Phường Lê Lợi', 'Phường Phú Thịnh', 'Phường Ngô Quyền', 'Phường Quang Trung', 'Phường Sơn Lộc', 'Phường Trung Hưng', 'Phường Trung Sơn Trầm', 'Phường Viên Sơn', 'Phường Xuân Khanh', 'Xã Đường Lâm', 'Xã Kim Sơn', 'Xã Sơn Đông', 'Xã Xuân Sơn', 'Xã Thanh Mỹ', 'Xã Cổ Đông']
            },
            'huyenbavi': {
                'name': 'Huyện Ba Vì',
                'wards': ['Thị trấn Tây Đằng', 'Xã Ba Vì', 'Xã Tản Lĩnh', 'Xã Thuần Mỹ', 'Xã Tòng Bạt', 'Xã Cổ Đô', 'Xã Tản Hồng', 'Xã Vạn Thắng', 'Xã Đông Quang', 'Xã Tiên Phong', 'Xã Minh Quang', 'Xã Sơn Đà', 'Xã Vật Lại', 'Xã Chu Minh', 'Xã Ba Trại', 'Xã Cam Thượng', 'Xã Thuỳ An', 'Xã Phú Cường', 'Xã Cẩm Lĩnh', 'Xã Yên Bài', 'Xã Khánh Thượng', 'Xã Phú Đông', 'Xã Phú Phương', 'Xã Phú Châu', 'Xã Thái Hòa', 'Xã Đồng Thái', 'Xã Phú Sơn', 'Xã Minh Châu', 'Xã Vân Hòa']
            },
            'huyenchuongmy': {
                'name': 'Huyện Chương Mỹ',
                'wards': ['Thị trấn Chúc Sơn', 'Thị trấn Xuân Mai', 'Xã Phụng Châu', 'Xã Tiên Phương', 'Xã Đông Sơn', 'Xã Đông Phương Yên', 'Xã Phú Nghĩa', 'Xã Trường Yên', 'Xã Ngọc Hòa', 'Xã Thủy Xuân Tiên', 'Xã Thanh Bình', 'Xã Tân Tiến', 'Xã Văn Võ', 'Xã Đồng Lạc', 'Xã Hòa Chính', 'Xã Trung Hòa', 'Xã Nam Phương Tiến', 'Xã Hợp Đồng', 'Xã Lam Điền', 'Xã Tốt Động', 'Xã Cẩm Yên', 'Xã Sơn Tây', 'Xã Xuân Mai', 'Xã Hòa Phú', 'Xã Đại Yên', 'Xã Hoàng Diệu', 'Xã Thụy Hương', 'Xã Hữu Văn', 'Xã Quảng Bị', 'Xã Mỹ Lương', 'Xã Trần Phú', 'Xã Đồng Phú']
            },
            'huyendanphuong': {
                'name': 'Huyện Đan Phượng',
                'wards': ['Thị trấn Phùng', 'Xã Trung Châu', 'Xã Hạ Mỗ', 'Xã Liên Hà', 'Xã Liên Trung', 'Xã Liên Hồng', 'Xã Hồng Hà', 'Xã Đan Phượng', 'Xã Đồng Tháp', 'Xã Song Phượng', 'Xã Tân Hội', 'Xã Thượng Mỗ', 'Xã Tân Lập', 'Xã Đông Lỗ', 'Xã Thọ An', 'Xã Thọ Xuân', 'Xã Phương Đình']
            },
            'huyendonganh': {
                'name': 'Huyện Đông Anh',
                'wards': ['Thị trấn Đông Anh', 'Xã Xuân Nộn', 'Xã Thuỵ Lâm', 'Xã Bắc Hồng', 'Xã Nguyên Khê', 'Xã Nam Hồng', 'Xã Tiên Dương', 'Xã Vân Hà', 'Xã Uy Nỗ', 'Xã Vân Nội', 'Xã Liên Hà', 'Xã Việt Hùng', 'Xã Kim Nỗ', 'Xã Kim Chung', 'Xã Dục Tú', 'Xã Đại Mạch', 'Xã Vọng La', 'Xã Cổ Loa', 'Xã Hải Bối', 'Xã Xuân Canh', 'Xã Võng La', 'Xã Tàm Xá', 'Xã Mai Lâm', 'Xã Đông Hội', 'Xã Vĩnh Ngọc']
            },
            'huyengialâm': {
                'name': 'Huyện Gia Lâm',
                'wards': ['Thị trấn Trâu Quỳ', 'Thị trấn Yên Viên', 'Xã Yên Thường', 'Xã Yên Viên', 'Xã Ninh Hiệp', 'Xã Đặng Xá', 'Xã Phù Đổng', 'Xã Trung Mầu', 'Xã Lệ Chi', 'Xã Cổ Bi', 'Xã Đa Tốn', 'Xã Kiêu Kỵ', 'Xã Bát Tràng', 'Xã Kim Đức', 'Xã Cầu Diễn', 'Xã Dương Quang', 'Xã Phú Sơn', 'Xã Dương Xá', 'Xã Gia Lâm', 'Xã Phụ Lỗ', 'Xã Kim Lan', 'Xã Đông Dư']
            },
            'huyenhoiduc': {
                'name': 'Huyện Hoài Đức',
                'wards': ['Thị trấn Trạm Trôi', 'Xã Sơn Đồng', 'Xã Cát Quế', 'Xã An Khánh', 'Xã An Thượng', 'Xã Vân Canh', 'Xã La Phù', 'Xã Đức Giang', 'Xã Đức Thượng', 'Xã Tiền Yên', 'Xã Song Phương', 'Xã Vân Côn', 'Xã Lại Yên', 'Xã Kim Chung', 'Xã Yên Sở', 'Xã Minh Khai', 'Xã Dương Liễu', 'Xã Di Trạch', 'Xã Đắc Sở', 'Xã Đông La']
            },
            'huyenmelinh': {
                'name': 'Huyện Mê Linh',
                'wards': ['Thị trấn Chi Đông', 'Thị trấn Quang Minh', 'Xã Hoàng Kim', 'Xã Liên Mạc', 'Xã Vạn Yên', 'Xã Chu Phan', 'Xã Tiến Thịnh', 'Xã Kim Hoa', 'Xã Thạch Đà', 'Xã Tiến Thắng', 'Xã Tráng Việt', 'Xã Mê Linh', 'Xã Văn Khê', 'Xã Thanh Lâm', 'Xã Tam Đồng', 'Xã Chăn Nười', 'Xã Đại Thịnh']
            },
            'huyenmyduc': {
                'name': 'Huyện Mỹ Đức',
                'wards': ['Thị trấn Đại Nghĩa', 'Xã Đốc Tín', 'Xã Phù Lưu Tế', 'Xã An Phú', 'Xã Phúc Lâm', 'Xã Hợp Thanh', 'Xã Đại Hưng', 'Xã Lê Thanh', 'Xã Xuy Xá', 'Xã Phùng Xá', 'Xã An Mỹ', 'Xã Hồng Sơn', 'Xã Đồng Tâm', 'Xã Bột Xuyên', 'Xã Hương Sơn', 'Xã Hợp Tiến', 'Xã Bình Yên', 'Xã Phước Sang', 'Xã An Tiến', 'Xã Mỹ Xuyên', 'Xã Tuy Lai', 'Xã Thượng Lâm', 'Xã Vạn Tín', 'Xã Hùng Tiến']
            },
            'huyenphuxuyen': {
                'name': 'Huyện Phú Xuyên',
                'wards': ['Thị trấn Phủ Xuyên', 'Thị trấn Phú Minh', 'Xã Hồng Minh', 'Xã Phú Túc', 'Xã Văn Hoàng', 'Xã Đại Xuyên', 'Xã Tri Thủy', 'Xã Phúc Tiến', 'Xã Phượng Dực', 'Xã Nam Tiến', 'Xã Tân Dân', 'Xã Châu Can', 'Xã Tri Trung', 'Xã Hoàng Long', 'Xã Bạch Hạ', 'Xã Phú Yên', 'Xã Vân Từ', 'Xã Chuyên Mỹ', 'Xã Khai Thái', 'Xã Minh Tân', 'Xã Quang Lãng', 'Xã Hồng Thái', 'Xã Quang Hà', 'Xã Nam Phong']
            },
            'huyenphuctho': {
                'name': 'Huyện Phúc Thọ',
                'wards': ['Thị trấn Phúc Thọ', 'Xã Vân Hà', 'Xã Vân Phúc', 'Xã Tam Thuận', 'Xã Tam Hiệp', 'Xã Hiệp Thuận', 'Xã Phúc Hòa', 'Xã Liên Hiệp', 'Xã Trạch Mỹ Lộc', 'Xã Phụng Thượng', 'Xã Tam Đa', 'Xã Hạ Mỗ', 'Xã Sen Phương', 'Xã Võng Xuyên', 'Xã Thọ Lộc', 'Xã Long Thượng', 'Xã Thanh Đa', 'Xã Tích Lộc', 'Xã Hát Môn', 'Xã Ngọc Tảo', 'Xã Xuân Đình']
            },
            'huyenquocoai': {
                'name': 'Huyện Quốc Oai',
                'wards': ['Thị trấn Quốc Oai', 'Xã Đông Xuân', 'Xã Sài Sơn', 'Xã Phượng Sơn', 'Xã Thạch Thán', 'Xã Đồng Quang', 'Xã Nghĩa Hương', 'Xã Cộng Hòa', 'Xã Tuyết Nghĩa', 'Xã Liệp Nghĩa', 'Xã Cẩn Hữu', 'Xã Đông Yên', 'Xã Hòa Thạch', 'Xã Ngọc Liệp', 'Xã Ngọc Mỹ', 'Xã Phú Cát', 'Xã Hưng Đạo', 'Xã Phú Mãn']
            },
            'huyensocson': {
                'name': 'Huyện Sóc Sơn',
                'wards': ['Thị trấn Sóc Sơn', 'Xã Bắc Sơn', 'Xã Minh Đức', 'Xã Hồng Kỳ', 'Xã Nam Sơn', 'Xã Trung Giã', 'Xã Tân Minh', 'Xã Minh Trí', 'Xã Minh Phú', 'Xã Phù Linh', 'Xã Bắc Phú', 'Xã Tân Dân', 'Xã Tiên Dược', 'Xã Việt Long', 'Xã Xuân Giang', 'Xã Mai Đình', 'Xã Đức Hoà', 'Xã Tân Hưng', 'Xã Quang Tiến', 'Xã Hiền Ninh', 'Xã Phú Cường', 'Xã Phú Minh', 'Xã Phù Lỗ', 'Xã Đông Xuân', 'Xã Kim Lũ', 'Xã Xuân Thu', 'Xã Thanh Xuân']
            },
            'huyenthachthat': {
                'name': 'Huyện Thạch Thất',
                'wards': ['Thị trấn Liên Quan', 'Xã Đại Đồng', 'Xã Cẩm Yên', 'Xã Lại Thượng', 'Xã Phú Kim', 'Xã Hạ Bằng', 'Xã Thạch Hoà', 'Xã Cần Kiệm', 'Xã Đồng Trúc', 'Xã Yên Trung', 'Xã Yên Bình', 'Xã Tiến Xuân', 'Xã Thạch Xá', 'Xã Bình Yên', 'Xã Phùng Xá', 'Xã Tân Xã', 'Xã Hương Ngải', 'Xã Quang Trung', 'Xã Kim Quan', 'Xã Lam Sơn']
            },
            'huyenthanhoai': {
                'name': 'Huyện Thanh Oai',
                'wards': ['Thị trấn Kim Bài', 'Xã Thanh Cao', 'Xã Thanh Thủy', 'Xã Thanh Mai', 'Xã Thanh Văn', 'Xã Đỗ Động', 'Xã Kim An', 'Xã Kim Thư', 'Xã Phương Trung', 'Xã Tân Ước', 'Xã Dân Hòa', 'Xã Liên Châu', 'Xã Cao Viên', 'Xã Bích Hòa', 'Xã Cao Xuân Dương', 'Xã Hồng Dương', 'Xã Mỹ Hưng', 'Xã Tam Hưng', 'Xã Cự Khê', 'Xã Tân Lộc', 'Xã Bình Minh']
            },
            'huyenthanhri': {
                'name': 'Huyện Thanh Trì',
                'wards': ['Thị trấn Văn Điển', 'Xã Tứ Hiệp', 'Xã Yên Mỹ', 'Xã Thanh Liệt', 'Xã Tả Thanh Oai', 'Xã Hữu Hoà', 'Xã Tam Hiệp', 'Xã Tân Triều', 'Xã Ngũ Hiệp', 'Xã Duyên Hà', 'Xã Ngọc Hồi', 'Xã Vĩnh Quỳnh', 'Xã Đông Mỹ', 'Xã Liên Ninh', 'Xã Vạn Phúc', 'Xã Đại Áng']
            },
            'huyenthuongtin': {
                'name': 'Huyện Thường Tín',
                'wards': ['Thị trấn Thường Tín', 'Xã Ninh Sở', 'Xã Nhị Khê', 'Xã Duyên Thái', 'Xã Khánh Hà', 'Xã Hòa Bình', 'Xã Văn Bình', 'Xã Hiển Giang', 'Xã Hồng Vân', 'Xã Vạn Điểm', 'Xã Liên Phương', 'Xã Văn Phú', 'Xã Tự Nhiên', 'Xã Tiền Phong', 'Xã Chương Dương', 'Xã Tô Hiệu', 'Xã Vân Tảo', 'Xã Lê Lợi', 'Xã Thắng Lợi', 'Xã Dũng Tiến', 'Xã Minh Cường', 'Xã Vạn Nhất', 'Xã Tân Minh', 'Xã Quất Động', 'Xã Nghiêm Xuyên', 'Xã Hà Hồi', 'Xã Nguyễn Trãi', 'Xã Văn Tự']
            },
            'huyenunghoa': {
                'name': 'Huyện Ứng Hòa',
                'wards': ['Thị trấn Vân Đình', 'Xã Viên An', 'Xã Trung Tú', 'Xã Hoa Viên', 'Xã Quảng Phú Cầu', 'Xã Trường Thịnh', 'Xã Cao Sơn', 'Xã Liên Bạt', 'Xã Hòa Phú', 'Xã Đồng Tân', 'Xã Phù Lưu', 'Xã Viên Nội', 'Xã Hòa Nam', 'Xã Đại Cường', 'Xã Lưu Hoàng', 'Xã Kim Đường', 'Xã Hòa Xá', 'Xã Trầm Lộng', 'Xã Bình Lưu', 'Xã Đại Hùng', 'Xã Phương Tú', 'Xã Tảo Dương Văn', 'Xã Hòa Lâm', 'Xã Minh Đức', 'Xã Đông Lỗ', 'Xã Thái Hòa']
            }
        }
    }
}

def normalize_string(s):
    """Chuyển đổi chuỗi thành dạng code (lowercase, no spaces, no special chars)"""
    import re
    import unicodedata
    
    # Bản đồ chuyển đổi dấu tiếng Việt để tránh trùng lặp
    vietnamese_map = {
        'á': 'a1', 'à': 'a2', 'ả': 'a3', 'ã': 'a4', 'ạ': 'a5',
        'ă': 'a6', 'ắ': 'a7', 'ằ': 'a8', 'ẳ': 'a9', 'ẵ': 'a10', 'ặ': 'a11',
        'â': 'a12', 'ấ': 'a13', 'ầ': 'a14', 'ẩ': 'a15', 'ẫ': 'a16', 'ậ': 'a17',
        'é': 'e1', 'è': 'e2', 'ẻ': 'e3', 'ẽ': 'e4', 'ẹ': 'e5',
        'ê': 'e6', 'ế': 'e7', 'ề': 'e8', 'ể': 'e9', 'ễ': 'e10', 'ệ': 'e11',
        'í': 'i1', 'ì': 'i2', 'ỉ': 'i3', 'ĩ': 'i4', 'ị': 'i5',
        'ó': 'o1', 'ò': 'o2', 'ỏ': 'o3', 'õ': 'o4', 'ọ': 'o5',
        'ô': 'o6', 'ố': 'o7', 'ồ': 'o8', 'ổ': 'o9', 'ỗ': 'o10', 'ộ': 'o11',
        'ơ': 'o12', 'ớ': 'o13', 'ờ': 'o14', 'ở': 'o15', 'ỡ': 'o16', 'ợ': 'o17',
        'ú': 'u1', 'ù': 'u2', 'ủ': 'u3', 'ũ': 'u4', 'ụ': 'u5',
        'ư': 'u6', 'ứ': 'u7', 'ừ': 'u8', 'ử': 'u9', 'ữ': 'u10', 'ự': 'u11',
        'ý': 'y1', 'ỳ': 'y2', 'ỷ': 'y3', 'ỹ': 'y4', 'ỵ': 'y5',
        'đ': 'd1'
    }
    
    # Chuyển thành lowercase
    s = s.lower()
    
    # Thay thế các ký tự có dấu bằng mã unique
    for viet_char, code in vietnamese_map.items():
        s = s.replace(viet_char, code)
    
    # Loại bỏ các ký tự đặc biệt còn lại và thay khoảng trắng bằng underscore
    s = re.sub(r'[^\w\s]', '', s)
    s = re.sub(r'\s+', '_', s)
    
    return s

def seed_locations():
    """Import dữ liệu địa chỉ vào database"""
    with app.app_context():
        try:
            print("Bắt đầu import dữ liệu địa chỉ...")
            
            # Xóa dữ liệu cũ nếu có
            Ward.query.delete()
            District.query.delete() 
            Province.query.delete()
            db.session.commit()
            print("Đã xóa dữ liệu cũ")
            
            # Import từng tỉnh/thành phố
            for province_code, province_data in LOCATION_DATA.items():
                print(f"Đang import {province_data['name']}...")
                
                # Tạo province
                province = Province(
                    code=province_code,
                    name=province_data['name']
                )
                db.session.add(province)
                db.session.flush()  # Để lấy ID
                
                # Import các quận/huyện
                for district_code, district_data in province_data['districts'].items():
                    print(f"  - {district_data['name']}")
                    
                    district = District(
                        code=district_code,
                        name=district_data['name'],
                        province_id=province.id
                    )
                    db.session.add(district)
                    db.session.flush()  # Để lấy ID
                    
                    # Import các phường/xã
                    for ward_name in district_data['wards']:
                        ward_code = normalize_string(ward_name)
                        
                        ward = Ward(
                            code=ward_code,
                            name=ward_name,
                            district_id=district.id
                        )
                        db.session.add(ward)
            
            # Commit tất cả
            db.session.commit()
            print("Import dữ liệu địa chỉ thành công!")
            
            # Thống kê
            total_provinces = Province.query.count()
            total_districts = District.query.count()
            total_wards = Ward.query.count()
            
            print(f"Đã import:")
            print(f"  - {total_provinces} tỉnh/thành phố")
            print(f"  - {total_districts} quận/huyện")
            print(f"  - {total_wards} phường/xã")
            
        except Exception as e:
            db.session.rollback()
            print(f"Lỗi khi import dữ liệu: {e}")
            raise

if __name__ == '__main__':
    seed_locations() 