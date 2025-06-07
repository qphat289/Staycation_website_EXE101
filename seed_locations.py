#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import app
from models import db, Province, District, Ward

# Dữ liệu địa chỉ - Cập nhật 2024 với cấu trúc hành chính mới nhất
LOCATION_DATA = {
    'hcm': {
        'name': 'TP. Hồ Chí Minh',
        'districts': {
            # 16 Quận nội thành
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
            'quan12': {
                'name': 'Quận 12',
                'wards': ['Phường Thạnh Xuân', 'Phường Thạnh Lộc', 'Phường Hiệp Thành', 'Phường Thới An', 'Phường Tân Chánh Hiệp', 'Phường An Phú Đông', 'Phường Tân Thới Hiệp', 'Phường Trung Mỹ Tây', 'Phường Tân Hưng Thuận', 'Phường Đông Hưng Thuận', 'Phường Tân Thới Nhất']
            },
            'quantanbinh': {
                'name': 'Quận Tân Bình',
                'wards': ['Phường 1', 'Phường 2', 'Phường 3', 'Phường 4', 'Phường 5', 'Phường 6', 'Phường 7', 'Phường 8', 'Phường 9', 'Phường 10', 'Phường 11', 'Phường 12', 'Phường 13', 'Phường 14', 'Phường 15']
            },
            'quantanphu': {
                'name': 'Quận Tân Phú',
                'wards': ['Phường Tân Sơn Nhì', 'Phường Tây Thạnh', 'Phường Sơn Kỳ', 'Phường Tân Quý', 'Phường Tân Thành', 'Phường Phú Thọ Hòa', 'Phường Phú Thạnh', 'Phường Phú Trung', 'Phường Hòa Thạnh', 'Phường Hiệp Tân', 'Phường Tân Thới Hòa']
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
            
            # Thành phố Thủ Đức (thành phố trực thuộc thành phố)
            'thanhphothuduc': {
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
            }
        }
    }
}

def normalize_string(s):
    """Chuyển đổi chuỗi thành dạng code (lowercase, no spaces, no special chars)"""
    import re
    import unicodedata
    
    # Loại bỏ dấu tiếng Việt
    s = unicodedata.normalize('NFD', s)
    s = ''.join(char for char in s if unicodedata.category(char) != 'Mn')
    
    # Chuyển thành lowercase và thay thế khoảng trắng, ký tự đặc biệt
    s = re.sub(r'[^\w\s]', '', s.lower())
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