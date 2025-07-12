import re
import string

class PasswordValidator:
    """Đánh giá độ mạnh mật khẩu theo 3 mức độ: YẾU, TRUNG BÌNH, MẠNH"""
    
    # Danh sách mật khẩu phổ biến (top 100)
    COMMON_PASSWORDS = {
        '123456', 'password', '123456789', '12345678', '12345', 'qwerty', 'abc123',
        '1234567', '111111', '1234', 'admin', 'letmein', 'welcome', 'monkey',
        '1234567890', 'dragon', 'master', 'hello', 'freedom', 'whatever', 'qazwsx',
        'trustno1', 'jordan', 'harley', 'ranger', 'iwantu', 'jennifer', 'hunter',
        'buster', 'soccer', 'tiger', 'charlie', 'andrew', 'michelle', 'love',
        'sunshine', 'jessica', 'asshole', 'fuckme', '2000', 'chocolate', 'rangers',
        'phoenix', 'mickey', 'secret', 'summer', 'internet', 'service', 'canada',
        'cooper', 'jonathan', 'liverpool', 'david', 'diamond', 'chelsea', 'biteme',
        'silver', 'gordon', 'casper', 'stupid', 'saturn', 'gemini', 'apples',
        'august', 'canes', 'blowme', 'rover', 'parker', '55555', 'puppies',
        'heaven', 'newyork', 'little', '98765', 'business', 'maggie', 'quinn',
        'cowboys', 'cooper', 'mickey', 'biteme', 'lovely', 'andrea', 'trevor',
        'rocky', 'bubbles', 'shotgun', 'dolphin', 'griffin', 'cool', 'beer',
        'rock', 'tiger', 'reddog', 'summer', 'april', 'sierra', 'fallout',
        'naomi', 'bulldog', 'king', 'maddog', 'queen', 'jordan', 'swimming',
        'dolphins', 'gordon', 'casper', 'stupid', 'saturn', 'gemini', 'apples',
        'august', 'canes', 'blowme', 'rover', 'parker', '55555', 'puppies',
        'heaven', 'newyork', 'little', '98765', 'business', 'maggie', 'quinn'
    }
    
    # Từ điển tiếng Việt phổ biến
    VIETNAMESE_WORDS = {
        'matkhau', 'password', 'admin', 'user', 'login', 'dangnhap', 'taikhoan',
        'account', 'email', 'gmail', 'hotmail', 'yahoo', 'facebook', 'google',
        'youtube', 'instagram', 'twitter', 'linkedin', 'github', 'stackoverflow',
        'microsoft', 'apple', 'samsung', 'sony', 'nokia', 'motorola', 'htc',
        'lg', 'asus', 'acer', 'dell', 'hp', 'lenovo', 'toshiba', 'fujitsu',
        'canon', 'nikon', 'sony', 'panasonic', 'sharp', 'philips', 'samsung',
        'lg', 'toshiba', 'hitachi', 'mitsubishi', 'daikin', 'carrier', 'gree',
        'midea', 'haier', 'tcl', 'hisense', 'skyworth', 'changhong', 'konka',
        'coocaa', 'oppo', 'vivo', 'xiaomi', 'huawei', 'honor', 'oneplus',
        'realme', 'iqoo', 'meizu', 'zte', 'coolpad', 'gionee', 'lenovo',
        'motorola', 'nokia', 'blackberry', 'htc', 'lg', 'sony', 'samsung',
        'apple', 'iphone', 'ipad', 'macbook', 'imac', 'macpro', 'airpods',
        'applewatch', 'appletv', 'homepod', 'airtag', 'magicmouse', 'magicpad',
        'magickeyboard', 'magictrackpad', 'magicmouse', 'magicpad', 'magickeyboard'
    }
    
    @staticmethod
    def evaluate_password(password):
        """
        Đánh giá mật khẩu và trả về kết quả chi tiết
        
        Args:
            password (str): Mật khẩu cần đánh giá
            
        Returns:
            dict: Kết quả đánh giá với các thông tin chi tiết
        """
        if not password:
            return {
                'strength': 'YẾU',
                'score': 0,
                'details': ['Mật khẩu không được để trống'],
                'suggestions': ['Nhập mật khẩu'],
                'is_acceptable': False
            }
        
        password = str(password)
        length = len(password)
        score = 0
        details = []
        suggestions = []
        
        # Kiểm tra độ dài
        if length <= 5:
            details.append('Độ dài quá ngắn (≤ 5 ký tự)')
            suggestions.append('Tăng độ dài mật khẩu lên ít nhất 6 ký tự')
        elif length >= 8:
            score += 2
            details.append('Độ dài tốt (≥ 8 ký tự)')
        else:
            score += 1
            details.append('Độ dài trung bình (6-7 ký tự)')
            suggestions.append('Tăng độ dài mật khẩu lên ít nhất 8 ký tự')
        
        # Kiểm tra các loại ký tự
        has_lower = bool(re.search(r'[a-z]', password))
        has_upper = bool(re.search(r'[A-Z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password))
        
        char_types = sum([has_lower, has_upper, has_digit, has_special])
        
        if char_types == 1:
            details.append('Chỉ sử dụng 1 loại ký tự')
            suggestions.append('Kết hợp nhiều loại ký tự (chữ hoa, chữ thường, số, ký tự đặc biệt)')
        elif char_types == 2:
            score += 1
            details.append('Sử dụng 2 loại ký tự')
            suggestions.append('Thêm ký tự đặc biệt để tăng độ mạnh')
        elif char_types >= 3:
            score += 2
            details.append(f'Sử dụng {char_types} loại ký tự')
        
        # Kiểm tra mật khẩu phổ biến
        if password.lower() in PasswordValidator.COMMON_PASSWORDS:
            details.append('Mật khẩu quá phổ biến')
            suggestions.append('Tránh sử dụng mật khẩu phổ biến')
            score -= 2
        
        # Kiểm tra từ điển tiếng Việt
        if password.lower() in PasswordValidator.VIETNAMESE_WORDS:
            details.append('Sử dụng từ điển tiếng Việt')
            suggestions.append('Tránh sử dụng từ có nghĩa')
            score -= 1
        
        # Kiểm tra pattern dễ đoán
        if re.search(r'(.)\1{2,}', password):  # Ký tự lặp lại 3 lần trở lên
            details.append('Có ký tự lặp lại')
            suggestions.append('Tránh lặp lại ký tự liên tiếp')
            score -= 1
        
        if re.search(r'(123|abc|qwe|asd|zxc)', password.lower()):
            details.append('Có pattern dễ đoán')
            suggestions.append('Tránh sử dụng pattern phổ biến')
            score -= 1
        
        # Kiểm tra thông tin cá nhân dễ đoán
        personal_patterns = [
            r'\b\d{4}\b',  # Năm sinh
            r'\b\d{2}\b',  # Ngày/tháng
            r'\b\d{10,11}\b',  # Số điện thoại
        ]
        
        for pattern in personal_patterns:
            if re.search(pattern, password):
                details.append('Có thể chứa thông tin cá nhân')
                suggestions.append('Tránh sử dụng thông tin cá nhân')
                score -= 1
                break
        
        # Xác định độ mạnh
        if score <= 0:
            strength = 'YẾU'
            is_acceptable = False
        elif score <= 2:
            strength = 'TRUNG BÌNH'
            is_acceptable = True
        else:
            strength = 'MẠNH'
            is_acceptable = True
        
        # Thêm gợi ý chung
        if strength == 'YẾU':
            suggestions.extend([
                'Sử dụng ít nhất 6 ký tự',
                'Kết hợp chữ hoa, chữ thường và số',
                'Tránh thông tin cá nhân'
            ])
        elif strength == 'TRUNG BÌNH':
            suggestions.extend([
                'Tăng độ dài lên 8 ký tự trở lên',
                'Thêm ký tự đặc biệt',
                'Tránh pattern dễ đoán'
            ])
        else:  # MẠNH
            suggestions.append('Mật khẩu của bạn đã đủ mạnh!')
        
        return {
            'strength': strength,
            'score': score,
            'details': details,
            'suggestions': suggestions,
            'is_acceptable': is_acceptable,
            'length': length,
            'char_types': char_types,
            'has_lower': has_lower,
            'has_upper': has_upper,
            'has_digit': has_digit,
            'has_special': has_special
        }
    
    @staticmethod
    def get_password_display(password):
        """
        Trả về mật khẩu được ẩn một phần để hiển thị
        
        Args:
            password (str): Mật khẩu gốc
            
        Returns:
            str: Mật khẩu được ẩn một phần
        """
        if not password:
            return ''
        
        length = len(password)
        if length <= 2:
            return '*' * length
        elif length <= 4:
            return password[0] + '*' * (length - 1)
        else:
            return password[0] + '*' * (length - 2) + password[-1]
    
    @staticmethod
    def format_evaluation_result(password):
        """
        Format kết quả đánh giá theo yêu cầu
        
        Args:
            password (str): Mật khẩu cần đánh giá
            
        Returns:
            str: Kết quả được format
        """
        result = PasswordValidator.evaluate_password(password)
        display_password = PasswordValidator.get_password_display(password)
        
        formatted_result = f"""🔐 ĐÁNH GIÁ MẬT KHẨU

Mật khẩu: {display_password}
Độ mạnh: {result['strength']}

📋 Chi tiết:
"""
        
        for detail in result['details']:
            formatted_result += f"• {detail}\n"
        
        if result['suggestions']:
            formatted_result += "\n💡 Gợi ý cải thiện:\n"
            for suggestion in result['suggestions']:
                formatted_result += f"• {suggestion}\n"
        
        return formatted_result 