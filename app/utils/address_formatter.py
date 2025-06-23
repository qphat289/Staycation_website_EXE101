"""
Address Formatter - Module chuẩn hóa địa chỉ Việt Nam
Xử lý tất cả các trường hợp viết tắt và chuẩn hóa địa chỉ
"""

import re

class AddressFormatter:
    def __init__(self):
        # Mapping các quận/huyện viết tắt
        self.district_mapping = {
            # TP.HCM
            'quan1': 'Quận 1',
            'quan 1': 'Quận 1',
            'q1': 'Quận 1',
            'q.1': 'Quận 1',
            'district1': 'Quận 1',
            'district 1': 'Quận 1',
            
            'quan2': 'Quận 2',
            'quan 2': 'Quận 2',
            'q2': 'Quận 2',
            'q.2': 'Quận 2',
            'district2': 'Quận 2',
            'district 2': 'Quận 2',
            
            'quan3': 'Quận 3',
            'quan 3': 'Quận 3',
            'q3': 'Quận 3',
            'q.3': 'Quận 3',
            'district3': 'Quận 3',
            'district 3': 'Quận 3',
            
            'quan4': 'Quận 4',
            'quan 4': 'Quận 4',
            'q4': 'Quận 4',
            'q.4': 'Quận 4',
            'district4': 'Quận 4',
            'district 4': 'Quận 4',
            
            'quan5': 'Quận 5',
            'quan 5': 'Quận 5',
            'q5': 'Quận 5',
            'q.5': 'Quận 5',
            'district5': 'Quận 5',
            'district 5': 'Quận 5',
            
            'quan6': 'Quận 6',
            'quan 6': 'Quận 6',
            'q6': 'Quận 6',
            'q.6': 'Quận 6',
            'district6': 'Quận 6',
            'district 6': 'Quận 6',
            
            'quan7': 'Quận 7',
            'quan 7': 'Quận 7',
            'q7': 'Quận 7',
            'q.7': 'Quận 7',
            'district7': 'Quận 7',
            'district 7': 'Quận 7',
            
            'quan8': 'Quận 8',
            'quan 8': 'Quận 8',
            'q8': 'Quận 8',
            'q.8': 'Quận 8',
            'district8': 'Quận 8',
            'district 8': 'Quận 8',
            
            'quan9': 'Quận 9',
            'quan 9': 'Quận 9',
            'q9': 'Quận 9',
            'q.9': 'Quận 9',
            'district9': 'Quận 9',
            'district 9': 'Quận 9',
            
            'quan10': 'Quận 10',
            'quan 10': 'Quận 10',
            'q10': 'Quận 10',
            'q.10': 'Quận 10',
            'district10': 'Quận 10',
            'district 10': 'Quận 10',
            
            'quan11': 'Quận 11',
            'quan 11': 'Quận 11',
            'q11': 'Quận 11',
            'q.11': 'Quận 11',
            'district11': 'Quận 11',
            'district 11': 'Quận 11',
            
            'quan12': 'Quận 12',
            'quan 12': 'Quận 12',
            'q12': 'Quận 12',
            'q.12': 'Quận 12',
            'district12': 'Quận 12',
            'district 12': 'Quận 12',
            
            # Quận có tên đặc biệt
            'govap': 'Quận Gò Vấp',
            'go vap': 'Quận Gò Vấp',
            'quangovap': 'Quận Gò Vấp',
            'quan govap': 'Quận Gò Vấp',
            'quan go vap': 'Quận Gò Vấp',
            'q.govap': 'Quận Gò Vấp',
            'q.go vap': 'Quận Gò Vấp',
            'district govap': 'Quận Gò Vấp',
            'district go vap': 'Quận Gò Vấp',
            
            'tanbinh': 'Quận Tân Bình',
            'tan binh': 'Quận Tân Bình',
            'quantanbinh': 'Quận Tân Bình',
            'quan tanbinh': 'Quận Tân Bình',
            'quan tan binh': 'Quận Tân Bình',
            'q.tanbinh': 'Quận Tân Bình',
            'q.tan binh': 'Quận Tân Bình',
            'district tanbinh': 'Quận Tân Bình',
            'district tan binh': 'Quận Tân Bình',
            
            'tanphu': 'Quận Tân Phú',
            'tan phu': 'Quận Tân Phú',
            'quantanphu': 'Quận Tân Phú',
            'quan tanphu': 'Quận Tân Phú',
            'quan tan phu': 'Quận Tân Phú',
            'q.tanphu': 'Quận Tân Phú',
            'q.tan phu': 'Quận Tân Phú',
            'district tanphu': 'Quận Tân Phú',
            'district tan phu': 'Quận Tân Phú',
            
            'binhtan': 'Quận Bình Tân',
            'binh tan': 'Quận Bình Tân',
            'quan binhtan': 'Quận Bình Tân',
            'quan binh tan': 'Quận Bình Tân',
            'q.binhtan': 'Quận Bình Tân',
            'q.binh tan': 'Quận Bình Tân',
            'district binhtan': 'Quận Bình Tân',
            'district binh tan': 'Quận Bình Tân',
            
            'binhthanh': 'Quận Bình Thạnh',
            'binh thanh': 'Quận Bình Thạnh',
            'quan binhthanh': 'Quận Bình Thạnh',
            'quan binh thanh': 'Quận Bình Thạnh',
            'q.binhthanh': 'Quận Bình Thạnh',
            'q.binh thanh': 'Quận Bình Thạnh',
            'district binhthanh': 'Quận Bình Thạnh',
            'district binh thanh': 'Quận Bình Thạnh',
            
            'phunhuan': 'Quận Phú Nhuận',
            'phu nhuan': 'Quận Phú Nhuận',
            'quanphunhuan': 'Quận Phú Nhuận',
            'quan phunhuan': 'Quận Phú Nhuận',
            'quan phu nhuan': 'Quận Phú Nhuận',
            'q.phunhuan': 'Quận Phú Nhuận',
            'q.phu nhuan': 'Quận Phú Nhuận',
            'district phunhuan': 'Quận Phú Nhuận',
            'district phu nhuan': 'Quận Phú Nhuận',
            
            # Thành phố thủ đức
            'thuduc': 'Thành phố Thủ Đức',
            'thu duc': 'Thành phố Thủ Đức',
            'tp thuduc': 'Thành phố Thủ Đức',
            'tp thu duc': 'Thành phố Thủ Đức',
            'thanh pho thu duc': 'Thành phố Thủ Đức',
            'city thu duc': 'Thành phố Thủ Đức',
        }
        
        # Mapping các thành phố/tỉnh
        self.city_mapping = {
            'hcm': 'Thành phố Hồ Chí Minh',
            'ho chi minh': 'Thành phố Hồ Chí Minh',
            'tp.hcm': 'Thành phố Hồ Chí Minh',
            'tp hcm': 'Thành phố Hồ Chí Minh',
            'tphcm': 'Thành phố Hồ Chí Minh',
            'saigon': 'Thành phố Hồ Chí Minh',
            'sai gon': 'Thành phố Hồ Chí Minh',
            'ho chi minh city': 'Thành phố Hồ Chí Minh',
            'hcmc': 'Thành phố Hồ Chí Minh',
            
            'hn': 'Thành phố Hà Nội',
            'hanoi': 'Thành phố Hà Nội',
            'ha noi': 'Thành phố Hà Nội',
            'tp hanoi': 'Thành phố Hà Nội',
            'tp ha noi': 'Thành phố Hà Nội',
            'tp.hanoi': 'Thành phố Hà Nội',
            'tp.ha noi': 'Thành phố Hà Nội',
            
            'dn': 'Thành phố Đà Nẵng',
            'da nang': 'Thành phố Đà Nẵng',
            'danang': 'Thành phố Đà Nẵng',
            'tp da nang': 'Thành phố Đà Nẵng',
            'tp.da nang': 'Thành phố Đà Nẵng',
        }
    
    def format_district(self, district_str):
        """
        Chuẩn hóa tên quận/huyện
        """
        if not district_str:
            return district_str
            
        # Chuyển về lowercase để so sánh
        district_lower = district_str.lower().strip()
        
        # Xóa các ký tự đặc biệt
        district_clean = re.sub(r'[^\w\s]', '', district_lower)
        district_clean = re.sub(r'\s+', ' ', district_clean).strip()
        
        # Kiểm tra trong mapping
        if district_clean in self.district_mapping:
            return self.district_mapping[district_clean]
        
        # Nếu không tìm thấy, thử format cơ bản
        if district_clean.startswith('quan '):
            number = district_clean.replace('quan ', '').strip()
            if number.isdigit():
                return f'Quận {number}'
        
        # Trả về title case nếu không tìm thấy
        return district_str.title()
    
    def format_city(self, city_str):
        """
        Chuẩn hóa tên thành phố/tỉnh
        """
        if not city_str:
            return city_str
            
        city_lower = city_str.lower().strip()
        
        # Xóa các ký tự đặc biệt
        city_clean = re.sub(r'[^\w\s]', '', city_lower)
        city_clean = re.sub(r'\s+', ' ', city_clean).strip()
        
        if city_clean in self.city_mapping:
            return self.city_mapping[city_clean]
        
        return city_str.title()
    
    def format_full_address(self, street=None, ward=None, district=None, city=None):
        """
        Chuẩn hóa địa chỉ đầy đủ
        """
        parts = []
        
        if street:
            parts.append(street.strip())
        
        if ward:
            # Chuẩn hóa phường/xã
            ward_formatted = ward.strip()
            if not ward_formatted.lower().startswith(('phường', 'xã', 'thị trấn')):
                if ward_formatted.lower().startswith('p.'):
                    ward_formatted = ward_formatted.replace('p.', 'Phường ', 1)
                elif ward_formatted.lower().startswith('p '):
                    ward_formatted = ward_formatted.replace('p ', 'Phường ', 1)
                elif ward_formatted.isdigit():
                    ward_formatted = f'Phường {ward_formatted}'
            parts.append(ward_formatted)
        
        if district:
            parts.append(self.format_district(district))
        
        if city:
            parts.append(self.format_city(city))
        
        return ', '.join(parts)

# Tạo instance global
address_formatter = AddressFormatter()

# Các hàm helper để sử dụng trong template
def format_district(district):
    """Helper function để sử dụng trong template"""
    return address_formatter.format_district(district)

def format_city(city):
    """Helper function để sử dụng trong template"""
    return address_formatter.format_city(city)

def format_full_address(street=None, ward=None, district=None, city=None):
    """Helper function để sử dụng trong template"""
    return address_formatter.format_full_address(street, ward, district, city) 