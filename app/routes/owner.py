# routes/owner.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.models import db, Home, Booking, HomeImage, Renter, Admin, Owner, Province, District, Ward, Rule, Amenity, HomeDeletionLog, Review
import os
import shutil
from datetime import datetime, timedelta
from PIL import Image
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from app.utils.utils import get_rank_info, get_location_name, get_user_upload_path, save_user_image, delete_user_image, generate_unique_filename, fix_image_orientation, allowed_file
from app.utils.email_validator import process_email
import json
from urllib.parse import quote


owner_bp = Blueprint('owner', __name__, url_prefix='/owner')

# Create a constant for property type mapping at module level
PROPERTY_TYPE_MAP = {
    'townhouse': 'Nhà phố',
    'apartment': 'Chung cư', 
    'villa': 'Villa',
    'penthouse': 'Penthouse',
    'farmstay': 'Farmstay',
    'resort': 'Resort'
}

PROPERTY_TYPE_REVERSE_MAP = {v: k for k, v in PROPERTY_TYPE_MAP.items()}

def get_location_names(home_data):
    """Lấy tên đầy đủ của địa chỉ từ database thay vì hard code"""
    try:
        result = {
            'province_name': 'Chưa chọn',
            'district_name': 'Chưa chọn', 
            'ward_name': 'Chưa chọn'
        }
        
        if home_data.get('province'):
            province = Province.query.filter_by(code=home_data['province']).first()
            if province:
                result['province_name'] = province.name
                
                if home_data.get('district'):
                    district = District.query.filter_by(code=home_data['district'], province_id=province.id).first()
                    if district:
                        result['district_name'] = district.name
                        
                        if home_data.get('ward'):
                            # Ward có thể là tên đầy đủ hoặc code
                            ward = Ward.query.filter(
                                Ward.district_id == district.id,
                                (Ward.name == home_data['ward']) | (Ward.code == home_data['ward'])
                            ).first()
                            if ward:
                                result['ward_name'] = ward.name
        
        print(f"✅ Location lookup: {result}")
        return result
        
    except Exception as e:
        print(f"❌ Error in get_location_names: {e}")
        return {
            'province_name': 'Chưa chọn',
            'district_name': 'Chưa chọn',
            'ward_name': 'Chưa chọn'
        }

def get_location_codes_from_names(city_name, district_name, ward_name=None):
    """Lấy mã địa chỉ từ tên để hiển thị trong form edit"""
    try:
        result = {
            'province_code': None,
            'district_code': None,
            'ward_name': ward_name  # Ward sẽ giữ nguyên tên
        }
        
        if city_name:
            # Tìm province theo tên
            province = Province.query.filter_by(name=city_name).first()
            if province:
                result['province_code'] = province.code
                
                if district_name:
                    # Tìm district theo tên và province_id
                    district = District.query.filter_by(name=district_name, province_id=province.id).first()
                    if district:
                        result['district_code'] = district.code
        
        print(f"✅ Location codes lookup: {result}")
        return result
        
    except Exception as e:
        print(f"❌ Error in get_location_codes_from_names: {e}")
        return {
            'province_code': None,
            'district_code': None,
            'ward_name': ward_name
        }

def get_rules_and_amenities(home_data):
    """Lấy thông tin rules và amenities từ database"""
    try:
        result = {
            'rules': [],
            'amenities': []
        }
        
        # Lấy rules nếu có
        if home_data.get('rules'):
            # Check if rules are already dict objects or string IDs
            if isinstance(home_data['rules'], list) and home_data['rules']:
                if isinstance(home_data['rules'][0], dict):
                    # Already processed as dict objects
                    result['rules'] = home_data['rules']
                else:
                    # String IDs, need to lookup from database
                    rule_ids = [int(id) for id in home_data['rules'] if str(id).isdigit()]
                    if rule_ids:
                        rules = Rule.query.filter(Rule.id.in_(rule_ids)).all()
                        result['rules'] = [rule.to_dict() for rule in rules]
        
        # Lấy amenities nếu có
        if home_data.get('amenities'):
            # Check if amenities are already dict objects or string IDs
            if isinstance(home_data['amenities'], list) and home_data['amenities']:
                if isinstance(home_data['amenities'][0], dict):
                    # Already processed as dict objects
                    result['amenities'] = home_data['amenities']
                else:
                    # String IDs, need to lookup from database
                    amenity_ids = [int(id) for id in home_data['amenities'] if str(id).isdigit()]
                    if amenity_ids:
                        amenities = Amenity.query.filter(Amenity.id.in_(amenity_ids)).all()
                        result['amenities'] = [amenity.to_dict() for amenity in amenities]
        
        print(f"✅ Rules & Amenities lookup: {len(result['rules'])} rules, {len(result['amenities'])} amenities")
        return result
        
    except Exception as e:
        print(f"❌ Error in get_rules_and_amenities: {e}")
        return {'rules': [], 'amenities': []}



def validate_uploaded_file(file, max_size_mb=5):
    """Validate uploaded file for security and size"""
    if not file or not file.filename:
        return False, "No file selected"
    
    if not allowed_file(file.filename):
        return False, "File type not allowed"
    
    # Check file size (read first to get size, then reset)
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if size > max_size_mb * 1024 * 1024:
        return False, f"File size exceeds {max_size_mb}MB limit"
    
    return True, "Valid file"

def get_property_type_en(vn_value):
    """Chuyển đổi property type từ tiếng Việt sang English"""
    return PROPERTY_TYPE_REVERSE_MAP.get(vn_value, 'house')  # Default là house

# Custom decorator to ensure user is an owner
def owner_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        print(f"owner_required: current_user type: {type(current_user)}")
        print(f"owner_required: current_user.is_owner(): {current_user.is_owner()}")
        print(f"owner_required: current_user role: {getattr(current_user, 'role', 'No role attribute')}")
        print(f"owner_required: session user_role: {session.get('user_role', 'Not set')}")
        
        if not current_user.is_owner():
            flash('You must be an owner to access this page', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


@owner_bp.route('/dashboard')
@login_required
def dashboard():
    # Kiểm tra email verification cho Owner
    if current_user.is_owner() and not current_user.email_verified and current_user.first_login:
        return redirect(url_for('owner.verify_email'))
    
    # Lấy tất cả nhà của owner hiện tại với relationship images, sắp xếp theo ngày tạo mới nhất
    homes = Home.query.options(joinedload(Home.images)).filter_by(owner_id=current_user.id).order_by(Home.created_at.desc()).all()
    
    return render_template('owner/dashboard.html', homes=homes)

@owner_bp.route('/verify-email')
@login_required
def verify_email():
    """Trang verify email cho Owner"""
    if not current_user.is_owner():
        flash('Chỉ Owner mới có thể truy cập trang này', 'danger')
        return redirect(url_for('auth.login'))
    
    if current_user.email_verified:
        flash('Email đã được xác thực', 'info')
        return redirect(url_for('owner.dashboard'))
    
    return render_template('owner/verify_email.html')





@owner_bp.route('/add-home', methods=['GET', 'POST'])
@owner_bp.route('/add-home/<int:home_id>', methods=['GET', 'POST'])
@login_required
def add_home(home_id=None):
    # Determine if this is a fresh request or coming back from preview
    is_fresh_request = request.method == 'GET' and not request.args.get('from_preview')
    
    # Clear session data if this is a fresh GET request (not coming from back-to-edit)
    if is_fresh_request:
        session.pop('home_preview_data', None)
        # Also clear any other home-related session data
        for key in list(session.keys()):
            if key.startswith('home_'):
                session.pop(key, None)
    
    if request.method == 'POST':
        try:
            # Lưu dữ liệu vào session để preview
            home_data = {
                'home_title': request.form.get('home_title'),
                'home_description': request.form.get('home_description'),
                'accommodation_type': request.form.get('accommodation_type', 'entire_home'),
                'property_type': request.form.get('property_type'),
                'province': request.form.get('province'),
                'district': request.form.get('district'),
                'ward': request.form.get('ward'),
                'street': request.form.get('street'),
                'bathroom_count': int(request.form.get('bathroom_count', 2)),
                'bed_count': int(request.form.get('bed_count', 1)),
                'guest_count': int(request.form.get('guest_count', 1)),
                'selected_rental_type': request.form.get('selected_rental_type'),
                
                # Enhanced pricing structure
                'price_first_2_hours': request.form.get('price_first_2_hours') or request.form.get('price_first_2_hours_both'),
                'price_per_additional_hour': request.form.get('price_per_additional_hour') or request.form.get('price_per_additional_hour_both'),
                'price_overnight': request.form.get('price_overnight') or request.form.get('price_overnight_both'),
                'price_daytime': request.form.get('price_daytime') or request.form.get('price_daytime_both'),
                'price_per_day': request.form.get('price_per_day') or request.form.get('price_per_day_both'),
                
                # Legacy pricing for backward compatibility
                'hourly_price': request.form.get('hourly_price'),
                'daily_price': request.form.get('daily_price'),
                
                'rules': request.form.getlist('rules[]'),
                'amenities': request.form.getlist('amenities[]')
            }
            
            # Xử lý file ảnh tạm thời
            image_paths = []
            main_image_path = None
            
            # Tạo thư mục temp nếu chưa có
            temp_folder = os.path.join('static', 'temp')
            os.makedirs(temp_folder, exist_ok=True)
            
            # Xử lý ảnh bìa
            if 'main_image' in request.files:
                main_image = request.files['main_image']
                if main_image and main_image.filename:
                    filename = secure_filename(main_image.filename)
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    filename = f"temp_main_{timestamp}_{filename}"
                    save_path = os.path.join(temp_folder, filename)
                    main_image.save(save_path)
                    main_image_path = f"/static/temp/{filename}"
            
            # Xử lý các ảnh khác - chỉ xử lý key 'images[]' một lần và loại bỏ trùng lặp
            if 'images[]' in request.files:
                files = request.files.getlist('images[]')
                
                # Track processed filenames to avoid duplicates
                processed_filenames = set()
                
                for file in files:
                    if file and file.filename:
                        original_filename = file.filename
                        
                        # Check for duplicate filename
                        if original_filename in processed_filenames:
                            continue
                        
                        processed_filenames.add(original_filename)
                        
                        filename = secure_filename(file.filename)
                        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]  # microseconds to milliseconds
                        filename = f"temp_{timestamp}_{filename}"
                        save_path = os.path.join(temp_folder, filename)
                        file.save(save_path)
                        image_paths.append(f"/static/temp/{filename}")
            
            # Thêm đường dẫn ảnh vào home_data
            home_data['main_image'] = main_image_path
            home_data['images'] = image_paths
            
            session['home_preview_data'] = home_data
            # Save the current step (assume user completed all steps before preview)
            session['last_completed_step'] = 3
            return redirect(url_for('owner.home_preview'))
            
        except Exception as e:
            flash(f'Có lỗi xảy ra: {str(e)}', 'danger')
    
    # Lấy dữ liệu từ session nếu có (khi quay lại từ preview), otherwise use empty dict
    if is_fresh_request:
        home_data = {}
        last_step = 1  # Start from step 1 for fresh requests
    else:
        home_data = session.get('home_preview_data', {})
        # Get the last step user was on before going to preview
        last_step = session.get('last_completed_step', 1)
    
    # Nếu có rules/amenities trong session, chuẩn bị data cho JavaScript
    if home_data.get('rules') or home_data.get('amenities'):
        pass
    
    return render_template('owner/add_home.html', home_data=home_data, last_step=last_step)

@owner_bp.route('/home-preview')
@login_required
def home_preview():
    # Lấy dữ liệu từ session
    home_data = session.get('home_preview_data')
    if not home_data:
        flash('Không tìm thấy dữ liệu nhà để xem trước.', 'warning')
        return redirect(url_for('owner.add_home'))
    
    # Lookup tên đầy đủ từ database
    location_names = get_location_names(home_data)
    
    # Lấy rules và amenities từ database
    rules_amenities = get_rules_and_amenities(home_data)
    

    
    # Chỉ hiển thị khi thực sự có data được chọn
    
    # Merge rules và amenities vào home_data
    home_data.update(rules_amenities)
    
    # Tạo map_address và encoded_map_address cho template
    street = home_data.get('street', '')
    ward_name = location_names.get('ward_name', '')
    district_name = location_names.get('district_name', '')
    province_name = location_names.get('province_name', '')
    
    map_address = f"{street}, {ward_name}, {district_name}, {province_name}, Vietnam" if street else f"{ward_name}, {district_name}, {province_name}, Vietnam"
    encoded_map_address = quote(map_address)
    
    # Tạo danh sách ảnh để hiển thị
    all_images = []
    if home_data.get('main_image'):
        all_images.append({
            'image_path': home_data['main_image'],
            'is_main': True
        })
    
    if home_data.get('images'):
        for img_path in home_data['images']:
            all_images.append({
                'image_path': img_path,
                'is_main': False
            })
    
    return render_template('owner/home_preview.html', 
                         home_data=home_data, 
                         location_names=location_names,
                         map_address=map_address,
                         encoded_map_address=encoded_map_address,
                         all_images=all_images)

@owner_bp.route('/save-current-step', methods=['POST'])
@login_required
def save_current_step():
    """Save the current step to session for back-to-edit functionality"""
    try:
        data = request.get_json()
        current_step = data.get('current_step', 1)
        
        # Validate step number
        if current_step in [1, 2, 3]:
            session['last_completed_step'] = current_step
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'error', 'message': 'Invalid step number'}), 400
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@owner_bp.route('/back-to-edit')
@login_required
def back_to_edit():
    # Dữ liệu đã được lưu trong session từ lúc tạo preview
    # Chỉ cần redirect về add_home với parameter để không xóa session
    return redirect(url_for('owner.add_home', from_preview=1))

@owner_bp.route('/clear-home-data')
@login_required
def clear_home_data():
    # Xóa dữ liệu tạm thời khỏi session khi owner thoát khỏi giao diện tạo nhà
    session.pop('home_preview_data', None)
    flash('Đã hủy quá trình tạo nhà.', 'info')
    return redirect(url_for('owner.dashboard'))

@owner_bp.route('/clear-home-session', methods=['POST'])
@login_required
def clear_home_session():
    # API endpoint để xóa session data qua AJAX
    session.pop('home_preview_data', None)
    # Also clear any other home-related session data
    for key in list(session.keys()):
        if key.startswith('home_'):
            session.pop(key, None)
    return jsonify({'status': 'success'})

@owner_bp.route('/confirm-home', methods=['POST'])
@login_required
def confirm_home():
    # Lấy dữ liệu từ session
    home_data = session.get('home_preview_data')
    
    if not home_data:
        flash('Không tìm thấy dữ liệu nhà để tạo.', 'warning')
        return redirect(url_for('owner.add_home'))
    
    try:
        # Xử lý giá dựa theo rental type được chọn
        # Initialize all pricing fields to 0.0 (or None for nullable fields)
        price_per_hour = 0.0
        price_per_night = 0.0
        price_first_2_hours = None
        price_per_additional_hour = None
        price_overnight = None
        price_daytime = None
        price_per_day = None
        
        selected_rental_type = home_data.get('selected_rental_type')
        
        # Helper function to safely convert price string to float
        def safe_price_convert(price_str):
            if not price_str:
                return None
            try:
                # Remove all thousand separators (dot or comma), keep only digits
                clean_price = str(price_str).replace('.', '').replace(',', '')
                return float(clean_price) if clean_price else None
            except (ValueError, TypeError):
                return None
        
        if selected_rental_type == 'hourly':
            # Enhanced hourly pricing
            price_first_2_hours = safe_price_convert(home_data.get('price_first_2_hours'))
            price_per_additional_hour = safe_price_convert(home_data.get('price_per_additional_hour'))
            price_overnight = safe_price_convert(home_data.get('price_overnight'))
            price_daytime = safe_price_convert(home_data.get('price_daytime'))
            
            # Legacy support: if hourly_price exists, use it for price_per_hour
            if home_data.get('hourly_price'):
                price_per_hour = safe_price_convert(home_data.get('hourly_price')) or 0.0
                
        elif selected_rental_type == 'daily':
            # Daily pricing
            price_per_day = safe_price_convert(home_data.get('price_per_day'))
            
            # Legacy support: if daily_price exists, use it for price_per_night
            if home_data.get('daily_price'):
                price_per_night = safe_price_convert(home_data.get('daily_price')) or 0.0
                
        elif selected_rental_type == 'both':
            # Both hourly and daily pricing
            price_first_2_hours = safe_price_convert(home_data.get('price_first_2_hours'))
            price_per_additional_hour = safe_price_convert(home_data.get('price_per_additional_hour'))
            price_overnight = safe_price_convert(home_data.get('price_overnight'))
            price_daytime = safe_price_convert(home_data.get('price_daytime'))
            price_per_day = safe_price_convert(home_data.get('price_per_day'))
            
            # Set basic prices for legacy compatibility
            if price_first_2_hours:
                price_per_hour = price_first_2_hours
            if price_per_day:
                price_per_night = price_per_day
        
        # Map property_type từ English sang Vietnamese using constant
        property_type_vn = PROPERTY_TYPE_MAP.get(home_data.get('property_type'), 'Mô hình chuẩn')
        
        # Get location names from database
        location_names = get_location_names(home_data)
        
        # Tạo home mới
        new_home = Home(
            title=home_data['home_title'],
            home_type=property_type_vn,  # Lưu giá trị tiếng Việt
            accommodation_type=home_data.get('accommodation_type', 'entire_home'),
            address=f"{home_data['street']}, {location_names['ward_name']}" if home_data['street'] and location_names['ward_name'] != 'Chưa chọn' else "Chưa cập nhật",
            city=location_names['province_name'] if location_names['province_name'] != 'Chưa chọn' else "Chưa cập nhật",
            district=location_names['district_name'] if location_names['district_name'] != 'Chưa chọn' else "Chưa cập nhật",
            home_number=home_data['home_title'],  # Sử dụng title làm home number
            bed_count=home_data['bed_count'],
            bathroom_count=home_data['bathroom_count'],
            max_guests=home_data['guest_count'],
            
            # Legacy pricing fields
            price_per_hour=price_per_hour,
            price_per_night=price_per_night,
            
            # Enhanced pricing fields
            price_first_2_hours=price_first_2_hours,
            price_per_additional_hour=price_per_additional_hour,
            price_overnight=price_overnight,
            price_daytime=price_daytime,
            price_per_day=price_per_day,
            
            description=home_data['home_description'],
            floor_number=1,  # Mặc định
            owner_id=current_user.id
        )
        # --- ĐỒNG BỘ GIÁ ---
        if (selected_rental_type in ['daily', 'both']) and new_home.price_per_day and new_home.price_per_day > 0:
            new_home.price_per_night = new_home.price_per_day
        
        db.session.add(new_home)
        db.session.commit()
        
        # Xử lý amenities và rules
        try:
            # Lưu amenities (amenities trong session là array của ID strings)
            if home_data.get('amenities'):
                amenity_ids = [int(amenity_id) for amenity_id in home_data['amenities']]
                amenities = Amenity.query.filter(Amenity.id.in_(amenity_ids)).all()
                new_home.amenities.extend(amenities)
            
            # Lưu rules (rules trong session là array của ID strings)
            if home_data.get('rules'):
                rule_ids = [int(rule_id) for rule_id in home_data['rules']]
                rules = Rule.query.filter(Rule.id.in_(rule_ids)).all()
                new_home.rules.extend(rules)
            
            db.session.commit()
            
        except Exception as e:
            # Không làm fail việc tạo nhà nếu có lỗi
            pass
        
        # Xử lý ảnh với cấu trúc mới: data/owner/{owner_id}/{home_id}/
        try:
            # Xử lý ảnh chính (main_image)
            if home_data.get('main_image'):
                main_image_path = home_data['main_image']
                if main_image_path.startswith('/static/temp/'):
                    temp_file = main_image_path[1:]  # Bỏ '/' đầu để có đường dẫn tương đối
                    
                    if os.path.exists(temp_file):
                        # Tạo đường dẫn mới với cấu trúc data/owner/{owner_id}/{home_id}/
                        relative_path, absolute_path = get_user_upload_path('owner', current_user.id, new_home.id)
                        
                        # Tạo tên file mới
                        original_name = os.path.basename(temp_file).replace('temp_main_', '', 1)
                        if '_' in original_name:
                            parts = original_name.split('_', 1)
                            if len(parts) > 1:
                                original_name = parts[1]
                        new_filename = generate_unique_filename(original_name, 'main')
                        
                        # Copy từ temp sang thư mục mới
                        new_path = os.path.join(absolute_path, new_filename)
                        shutil.copy2(temp_file, new_path)
                        
                        # Tạo record trong database với đường dẫn mới
                        main_img = HomeImage(
                            image_path=f"{relative_path}/{new_filename}",
                            home_id=new_home.id,
                            is_featured=True
                        )
                        db.session.add(main_img)
                        
                        # Xóa file temp
                        os.remove(temp_file)
            
            # Xử lý các ảnh khác
            if home_data.get('images'):
                for i, image_path in enumerate(home_data['images']):
                    if image_path.startswith('/static/temp/'):
                        temp_file = image_path[1:]  # Bỏ '/' đầu
                        
                        if os.path.exists(temp_file):
                            # Tạo đường dẫn mới
                            relative_path, absolute_path = get_user_upload_path('owner', current_user.id, new_home.id)
                            
                            # Tạo tên file mới
                            original_name = os.path.basename(temp_file).replace('temp_', '', 1)
                            if '_' in original_name:
                                parts = original_name.split('_', 1)
                                if len(parts) > 1:
                                    original_name = parts[1]
                            new_filename = generate_unique_filename(original_name, f'home_{i+1}')
                            
                            # Copy từ temp sang thư mục mới
                            new_path = os.path.join(absolute_path, new_filename)
                            shutil.copy2(temp_file, new_path)
                            
                            # Tạo record trong database
                            img = HomeImage(
                                image_path=f"{relative_path}/{new_filename}",
                                home_id=new_home.id,
                                is_featured=False
                            )
                            db.session.add(img)
                            
                            # Xóa file temp
                            os.remove(temp_file)
            
            db.session.commit()
            
        except Exception as e:
            # Không làm fail việc tạo nhà nếu ảnh có lỗi
            pass
        
        # Xóa dữ liệu preview khỏi session
        session.pop('home_preview_data', None)
        
        flash('Đã tạo nhà thành công!', 'success')
        return redirect(url_for('owner.dashboard', created='success'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Có lỗi xảy ra khi tạo nhà: {str(e)}', 'danger')
        return redirect(url_for('owner.home_preview'))

@owner_bp.route('/edit-home/<int:home_id>', methods=['GET', 'POST'])
@login_required
def edit_home(home_id):
    home = Home.query.options(joinedload(Home.images)).get_or_404(home_id)
    if home.owner_id != current_user.id:
        flash('Bạn không có quyền chỉnh sửa nhà này!', 'danger')
        return redirect(url_for('owner.dashboard'))
    
    if request.method == 'POST':
        try:
            # Cập nhật thông tin cơ bản với validation
            title = request.form.get('home_title', '').strip()
            if not title:
                flash('Tên nhà không được để trống!', 'danger')
                return redirect(url_for('owner.edit_home', home_id=home_id))
            
            home.title = title
            home.description = request.form.get('home_description', '').strip()
            
            # Chuyển đổi property_type sang tiếng Việt trước khi lưu
            property_type_vn = PROPERTY_TYPE_MAP.get(
                request.form.get('property_type'), 
                request.form.get('property_type', home.home_type)
            )
            home.home_type = property_type_vn
            
            # Cập nhật accommodation_type
            home.accommodation_type = request.form.get('accommodation_type', 'entire_home')
            
            # Update location with proper name lookup
            province_code = request.form.get('province')
            district_code = request.form.get('district')
            
            if province_code:
                # Get province name from database
                from app.models.models import Province, District
                province = Province.query.filter_by(code=province_code).first()
                if province:
                    home.city = province.name
                    
                    if district_code:
                        district = District.query.filter_by(code=district_code, province_id=province.id).first()
                        if district:
                            home.district = district.name

            # Cập nhật địa chỉ - improved logic with ward name lookup
            ward_input = request.form.get('ward', '').strip()
            street = request.form.get('street', '').strip()
            
            # Try to get ward name from database if ward_input is a code
            ward_name = ward_input
            if ward_input and district_code and province_code:
                from app.models.models import Ward
                # Find ward by name or code
                ward = Ward.query.join(District).join(Province).filter(
                    Province.code == province_code,
                    District.code == district_code,
                    (Ward.name == ward_input) | (Ward.code == ward_input)
                ).first()
                if ward:
                    ward_name = ward.name
            
            if street and ward_name:
                home.address = f"{street}, {ward_name}"
            elif street:
                home.address = street
            elif ward_name:
                home.address = ward_name
            # If both empty, keep existing address
            
            # Cập nhật thông tin nhà với validation
            try:
                home.bed_count = max(1, int(request.form.get('bed_count', 1)))
                home.bathroom_count = max(1, int(request.form.get('bathroom_count', 1)))
                home.max_guests = max(1, int(request.form.get('guest_count', 1)))
            except (ValueError, TypeError):
                flash('Thông tin số lượng không hợp lệ!', 'danger')
                return redirect(url_for('owner.edit_home', home_id=home_id))
            
            # Cập nhật giá dựa theo rental type với enhanced pricing structure
            rental_type = request.form.get('selected_rental_type') or request.form.get('rental_type')
            
            # If no rental type is specified, determine it from existing pricing
            if not rental_type:
                if home.price_per_day and home.price_per_day > 0:
                    if ((home.price_first_2_hours and home.price_first_2_hours > 0) or 
                        (home.price_per_additional_hour and home.price_per_additional_hour > 0) or
                        (home.price_overnight and home.price_overnight > 0) or 
                        (home.price_daytime and home.price_daytime > 0)):
                        rental_type = 'both'
                    else:
                        rental_type = 'daily'
                elif ((home.price_first_2_hours and home.price_first_2_hours > 0) or 
                      (home.price_per_additional_hour and home.price_per_additional_hour > 0) or
                      (home.price_overnight and home.price_overnight > 0) or 
                      (home.price_daytime and home.price_daytime > 0)):
                    rental_type = 'hourly'
                else:
                    rental_type = 'hourly'  # default fallback
            
            # Preserve existing pricing to avoid data loss if user doesn't modify prices
            existing_pricing = {
                'price_per_hour': home.price_per_hour,
                'price_per_night': home.price_per_night,
                'price_first_2_hours': home.price_first_2_hours,
                'price_per_additional_hour': home.price_per_additional_hour,
                'price_overnight': home.price_overnight,
                'price_daytime': home.price_daytime,
                'price_per_day': home.price_per_day
            }
            
            # Helper function to safely convert price
            def safe_price_convert(price_str):
                if not price_str:
                    return None
                try:
                    clean_price = str(price_str).replace('.', '').replace(',', '')
                    return float(clean_price) / 1000 if clean_price else None
                except (ValueError, TypeError):
                    return None
            
            try:
                if rental_type == 'hourly':
                    # Enhanced hourly pricing - only update if values provided, otherwise keep existing
                    new_price_first_2_hours = safe_price_convert(request.form.get('price_first_2_hours') or request.form.get('price_first_2_hours_both'))
                    new_price_per_additional_hour = safe_price_convert(request.form.get('price_per_additional_hour') or request.form.get('price_per_additional_hour_both'))
                    new_price_overnight = safe_price_convert(request.form.get('price_overnight') or request.form.get('price_overnight_both'))
                    new_price_daytime = safe_price_convert(request.form.get('price_daytime') or request.form.get('price_daytime_both'))
                    
                    home.price_first_2_hours = new_price_first_2_hours if new_price_first_2_hours is not None else existing_pricing['price_first_2_hours']
                    home.price_per_additional_hour = new_price_per_additional_hour if new_price_per_additional_hour is not None else existing_pricing['price_per_additional_hour']
                    home.price_overnight = new_price_overnight if new_price_overnight is not None else existing_pricing['price_overnight']
                    home.price_daytime = new_price_daytime if new_price_daytime is not None else existing_pricing['price_daytime']
                    
                    # Reset daily pricing for hourly only
                    home.price_per_day = None
                    
                    # Legacy support
                    hourly_price = request.form.get('hourly_price')
                    if hourly_price:
                        price_value = safe_price_convert(hourly_price)
                        if price_value and price_value > 0:
                            home.price_per_hour = price_value
                        elif price_value is not None and price_value <= 0:
                            flash('Giá nhà phải lớn hơn 0!', 'danger')
                            return redirect(url_for('owner.edit_home', home_id=home_id))
                    else:
                        # Keep existing hourly price or set from enhanced pricing
                        if home.price_first_2_hours and home.price_first_2_hours > 0:
                            home.price_per_hour = home.price_first_2_hours
                        else:
                            home.price_per_hour = existing_pricing['price_per_hour']
                    
                    # Reset daily legacy pricing
                    home.price_per_night = 0.0
                        
                elif rental_type == 'daily':
                    # Daily pricing - only update if values provided, otherwise keep existing
                    new_price_per_day = safe_price_convert(request.form.get('price_per_day') or request.form.get('price_per_day_both'))
                    home.price_per_day = new_price_per_day if new_price_per_day is not None else existing_pricing['price_per_day']
                    
                    # Reset hourly pricing for daily only
                    home.price_first_2_hours = None
                    home.price_per_additional_hour = None
                    home.price_overnight = None
                    home.price_daytime = None
                    
                    # Legacy support
                    daily_price = request.form.get('daily_price')
                    if daily_price:
                        price_value = safe_price_convert(daily_price)
                        if price_value and price_value > 0:
                            home.price_per_night = price_value
                        elif price_value is not None and price_value <= 0:
                            flash('Giá nhà phải lớn hơn 0!', 'danger')
                            return redirect(url_for('owner.edit_home', home_id=home_id))
                    else:
                        # Keep existing daily price or set from enhanced pricing
                        if home.price_per_day and home.price_per_day > 0:
                            home.price_per_night = home.price_per_day
                        else:
                            home.price_per_night = existing_pricing['price_per_night']
                    
                    # Reset hourly legacy pricing
                    home.price_per_hour = 0.0
                        
                elif rental_type == 'both':
                    # Both hourly and daily pricing - only update if values provided, otherwise keep existing
                    new_price_first_2_hours = safe_price_convert(request.form.get('price_first_2_hours') or request.form.get('price_first_2_hours_both'))
                    new_price_per_additional_hour = safe_price_convert(request.form.get('price_per_additional_hour') or request.form.get('price_per_additional_hour_both'))
                    new_price_overnight = safe_price_convert(request.form.get('price_overnight') or request.form.get('price_overnight_both'))
                    new_price_daytime = safe_price_convert(request.form.get('price_daytime') or request.form.get('price_daytime_both'))
                    new_price_per_day = safe_price_convert(request.form.get('price_per_day') or request.form.get('price_per_day_both'))
                    
                    home.price_first_2_hours = new_price_first_2_hours if new_price_first_2_hours is not None else existing_pricing['price_first_2_hours']
                    home.price_per_additional_hour = new_price_per_additional_hour if new_price_per_additional_hour is not None else existing_pricing['price_per_additional_hour']
                    home.price_overnight = new_price_overnight if new_price_overnight is not None else existing_pricing['price_overnight']
                    home.price_daytime = new_price_daytime if new_price_daytime is not None else existing_pricing['price_daytime']
                    home.price_per_day = new_price_per_day if new_price_per_day is not None else existing_pricing['price_per_day']
                    
                    # Set legacy pricing for compatibility - keep existing if new values not provided
                    if home.price_first_2_hours and home.price_first_2_hours > 0:
                        home.price_per_hour = home.price_first_2_hours
                    else:
                        home.price_per_hour = existing_pricing['price_per_hour']
                        
                    if home.price_per_day and home.price_per_day > 0:
                        home.price_per_night = home.price_per_day
                    else:
                        home.price_per_night = existing_pricing['price_per_night']
                        
                else:
                    # No rental type specified or unknown type - keep all existing pricing
                    home.price_per_hour = existing_pricing['price_per_hour']
                    home.price_per_night = existing_pricing['price_per_night']
                    home.price_first_2_hours = existing_pricing['price_first_2_hours']
                    home.price_per_additional_hour = existing_pricing['price_per_additional_hour']
                    home.price_overnight = existing_pricing['price_overnight']
                    home.price_daytime = existing_pricing['price_daytime']
                    home.price_per_day = existing_pricing['price_per_day']
                        
            except (ValueError, TypeError) as e:
                flash('Giá nhà không hợp lệ!', 'danger')
                return redirect(url_for('owner.edit_home', home_id=home_id))
            
            # Validate that we have at least some valid pricing after the update
            # Only enforce this if rental_type was provided (user modified pricing)
            has_valid_pricing = (
                (home.price_per_hour and home.price_per_hour > 0) or
                (home.price_per_night and home.price_per_night > 0) or
                (home.price_first_2_hours and home.price_first_2_hours > 0) or
                (home.price_per_day and home.price_per_day > 0)
            )
            
            # Only enforce pricing validation if user explicitly provided rental type (modified pricing section)
            if rental_type and not has_valid_pricing:
                flash('Vui lòng nhập giá hợp lệ để cập nhật homestay!', 'danger')
                return redirect(url_for('owner.edit_home', home_id=home_id))
            
            # Cập nhật amenities
            home.amenities.clear()
            amenity_ids = request.form.getlist('amenities[]')
            if amenity_ids:
                amenity_ids = [int(aid) for aid in amenity_ids if aid.isdigit()]
                if amenity_ids:
                    amenities = Amenity.query.filter(Amenity.id.in_(amenity_ids)).all()
                    home.amenities.extend(amenities)
            
            # Cập nhật rules
            home.rules.clear()
            rule_ids = request.form.getlist('rules[]')
            if rule_ids:
                rule_ids = [int(rid) for rid in rule_ids if rid.isdigit()]
                if rule_ids:
                    rules = Rule.query.filter(Rule.id.in_(rule_ids)).all()
                    home.rules.extend(rules)
            
            # Xử lý upload ảnh mới with validation
            owner_id = current_user.id
            home_folder = f"static/data/owner/{owner_id}/{home_id}"
            os.makedirs(home_folder, exist_ok=True)
            
            # Xử lý ảnh chính (main_image)
            if 'main_image' in request.files:
                main_image = request.files['main_image']
                is_valid, error_msg = validate_uploaded_file(main_image)
                
                if is_valid:
                    filename = secure_filename(main_image.filename)
                    unique_filename = generate_unique_filename(filename, 'main')
                    file_path = os.path.join(home_folder, unique_filename)
                    main_image.save(file_path)
                    
                    # Tạo record trong database
                    relative_path = f"data/owner/{owner_id}/{home_id}/{unique_filename}"
                    
                    # Xóa ảnh bìa cũ nếu có
                    old_featured = HomeImage.query.filter_by(home_id=home_id, is_featured=True).first()
                    if old_featured:
                        old_file_path = os.path.join('static', old_featured.image_path)
                        if os.path.exists(old_file_path):
                            os.remove(old_file_path)
                        db.session.delete(old_featured)
                    
                    # Tạo record mới
                    new_main_image = HomeImage(
                        image_path=relative_path,
                        home_id=home_id,
                        is_featured=True
                    )
                    db.session.add(new_main_image)
                elif main_image.filename:  # Only show error if user actually selected a file
                    flash(f'Ảnh chính: {error_msg}', 'danger')
            
            # Xử lý ảnh phụ (images[]) with validation
            if 'images[]' in request.files:
                additional_images = request.files.getlist('images[]')
                for i, image in enumerate(additional_images):
                    is_valid, error_msg = validate_uploaded_file(image)
                    
                    if is_valid:
                        filename = secure_filename(image.filename)
                        unique_filename = generate_unique_filename(filename, f'home_{i+1}')
                        file_path = os.path.join(home_folder, unique_filename)
                        image.save(file_path)
                        
                        # Tạo record trong database
                        relative_path = f"data/owner/{owner_id}/{home_id}/{unique_filename}"
                        new_image = HomeImage(
                            image_path=relative_path,
                            home_id=home_id,
                            is_featured=False
                        )
                        db.session.add(new_image)
                    elif image.filename:  # Only show error if user actually selected a file
                        flash(f'Ảnh {i+1}: {error_msg}', 'warning')
            
            # Cập nhật thời gian sửa đổi
            home.updated_at = datetime.now()
            
            db.session.commit()
            flash('Đã cập nhật thông tin nhà thành công!', 'success')
            return redirect(url_for('owner.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra khi cập nhật nhà: {str(e)}', 'danger')
            
    # GET request - prepare home data for template with improved address parsing
    street_address = ''
    ward_name = ''
    
    if home.address:
        # Improved address parsing logic
        address_parts = [part.strip() for part in home.address.split(',')]
        
        # Strategy 1: Look for ward keywords
        ward_found = False
        for i, part in enumerate(address_parts):
            if any(keyword in part.lower() for keyword in ['phường', 'xã', 'thị trấn']):
                ward_name = part
                # Remaining parts form street address
                remaining_parts = address_parts[:i] + address_parts[i+1:]
                street_address = ', '.join(remaining_parts).strip()
                ward_found = True
                break
        
        # Strategy 2: If no ward keywords found, assume last part is ward (if more than 1 part)
        if not ward_found and len(address_parts) > 1:
            ward_name = address_parts[-1]
            street_address = ', '.join(address_parts[:-1]).strip()
        elif not ward_found:
            # Single part - treat as street address
            street_address = home.address
    
    # Determine rental type based on what pricing fields are set
    rental_type = 'hourly'  # default
    if home.price_per_day and home.price_per_day > 0:
        if ((home.price_first_2_hours and home.price_first_2_hours > 0) or 
            (home.price_per_additional_hour and home.price_per_additional_hour > 0) or
            (home.price_overnight and home.price_overnight > 0) or 
            (home.price_daytime and home.price_daytime > 0)):
            rental_type = 'both'
        else:
            rental_type = 'daily'
    elif ((home.price_first_2_hours and home.price_first_2_hours > 0) or 
          (home.price_per_additional_hour and home.price_per_additional_hour > 0) or
          (home.price_overnight and home.price_overnight > 0) or 
          (home.price_daytime and home.price_daytime > 0)):
        rental_type = 'hourly'

    # Get location codes from stored names
    location_codes = get_location_codes_from_names(home.city, home.district, ward_name)
    
    home_data = {
        'id': home.id,
        'title': home.title,
        'description': home.description,
        'accommodation_type': home.accommodation_type,
        'property_type': get_property_type_en(home.home_type),
        'province': location_codes['province_code'],
        'district': location_codes['district_code'],
        'ward': location_codes['ward_name'],
        'street': street_address,
        'bathroom_count': home.bathroom_count,
        'bed_count': home.bed_count,
        'guest_count': home.max_guests,
        'rental_type': rental_type,
        
        # Legacy pricing fields
        'hourly_price': int(home.price_per_hour * 1000) if home.price_per_hour else 0,
        'daily_price': int(home.price_per_day * 1000) if home.price_per_day else None,
        
        # Enhanced pricing fields
        'price_first_2_hours': home.price_first_2_hours,
        'price_per_additional_hour': home.price_per_additional_hour,
        'price_overnight': home.price_overnight,
        'price_daytime': home.price_daytime,
        'price_per_day': home.price_per_day,
        
        'rules': [{'id': rule.id, 'name': rule.name} for rule in home.rules],
        'amenities': [{'id': amenity.id, 'name': amenity.name, 'icon': amenity.icon} for amenity in home.amenities],
        'images': [{'id': img.id, 'path': img.image_path, 'is_featured': img.is_featured} for img in home.images]
    }
    
    return render_template('owner/edit_home.html', home=home_data)

@owner_bp.route('/delete-home/<int:home_id>', methods=['POST'])
@login_required
def delete_home(home_id):
    home = Home.query.get_or_404(home_id)
    if home.owner_id != current_user.id:
        flash('Bạn không có quyền xóa nhà này!', 'danger')
        return redirect(url_for('owner.dashboard'))
    
    # Lấy lý do xóa từ form
    delete_reason = request.form.get('delete_reason', '').strip()
    
    # Validate lý do xóa
    if not delete_reason or len(delete_reason) < 10:
        flash('Lý do xóa nhà phải có ít nhất 10 ký tự!', 'danger')
        return redirect(url_for('owner.dashboard'))
    
    try:
        # Lưu log xóa nhà (tùy chọn - có thể tạo bảng HomeDeletionLog)
        home_title = home.title
        owner_name = current_user.full_name or current_user.username
        
        # Xóa folder ảnh của nhà
        home_folder = os.path.join('static', 'uploads', f'home_{home_id}')
        if os.path.exists(home_folder):
            try:
                shutil.rmtree(home_folder)
                print(f"Đã xóa folder ảnh: {home_folder}")
            except Exception as e:
                print(f"Không thể xóa folder ảnh: {e}")
                # Fallback: xóa từng file
                for image in home.images:
                    if image.image_path:
                        file_path = os.path.join('static', image.image_path)
                        if os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                            except Exception as e:
                                print(f"Không thể xóa file ảnh: {e}")
        
        # Lưu log vào database
        deletion_log = HomeDeletionLog(
            home_id=home_id,
            home_title=home_title,
            owner_id=current_user.id,
            owner_name=owner_name,
            delete_reason=delete_reason,
            home_address=f"{home.address}, {home.district}, {home.city}",
            home_price=home.price_per_hour or home.price_per_day
        )
        db.session.add(deletion_log)
        
        # Ghi log ra console
        log_message = f"[{datetime.now()}] Owner '{owner_name}' (ID: {current_user.id}) đã xóa nhà '{home_title}' (ID: {home_id}). Lý do: {delete_reason}"
        print(log_message)
        
        # Xóa nhà (cascade sẽ tự động xóa các record liên quan)
        db.session.delete(home)
        db.session.commit()
        
        flash(f'Đã xóa nhà "{home_title}" thành công!', 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi khi xóa nhà: {str(e)}")
        flash('Có lỗi xảy ra khi xóa nhà. Vui lòng thử lại!', 'danger')
    
    return redirect(url_for('owner.dashboard'))


@owner_bp.route('/calendar')
@owner_required
def calendar():
    # Get all homes owned by current user
    homes = Home.query.filter_by(owner_id=current_user.id).all()
    
    # Get all bookings for these homes
    all_bookings = []
    for home in homes:
        all_bookings.extend(home.bookings)
    
    # Sort bookings by start_time (handle None values)
    all_bookings.sort(key=lambda x: x.start_time or datetime.min)
    
    # Convert bookings to JSON-serializable format
    bookings_data = []
    for booking in all_bookings:
        booking_dict = {
            'id': booking.id,
            'start_time': booking.start_time.isoformat() if booking.start_time else None,
            'end_time': booking.end_time.isoformat() if booking.end_time else None,
            'created_at': booking.created_at.isoformat() if booking.created_at else None,
            'booking_type': booking.booking_type,
            'total_hours': booking.total_hours,
            'total_price': float(booking.total_price) if booking.total_price else 0,
            'status': booking.status,
            'home': {
                'id': booking.home.id if booking.home else None,
                'title': booking.home.title if booking.home else None
            } if booking.home else None,
            'renter': {
                'id': booking.renter.id if booking.renter else None,
                'username': booking.renter.username if booking.renter else None,
                'full_name': booking.renter.full_name if booking.renter else None,
                'email': booking.renter.email if booking.renter else None,
                'phone': booking.renter.phone if booking.renter else None
            } if booking.renter else None
        }
        bookings_data.append(booking_dict)
    
    # Convert homes to JSON-serializable format
    homes_data = []
    for home in homes:
        home_dict = {
            'id': home.id,
            'title': home.title,
            'home_type': home.home_type,
            'city': home.city,
            'district': home.district,
            'price_per_hour': float(home.price_per_hour) if home.price_per_hour else 0,
            'max_guests': home.max_guests
        }
        homes_data.append(home_dict)
    
    return render_template('owner/calendar.html', 
                          bookings=bookings_data,
                          homes=homes_data)

@owner_bp.route('/calendar/api/bookings/<date>')
@owner_required
def get_bookings_by_date(date):
    """API endpoint to get bookings for a specific date"""
    try:
        from datetime import datetime
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Get all homes owned by current user
        homes = Home.query.filter_by(owner_id=current_user.id).all()
        home_ids = [home.id for home in homes]
        
        # Get bookings for the specific date
        bookings = Booking.query.filter(
            Booking.home_id.in_(home_ids),
            func.date(Booking.start_time) == target_date
        ).all()
        
        bookings_data = []
        for booking in bookings:
            booking_dict = {
                'id': booking.id,
                'start_time': booking.start_time.isoformat() if booking.start_time else None,
                'end_time': booking.end_time.isoformat() if booking.end_time else None,
                'booking_type': booking.booking_type,
                'total_hours': booking.total_hours,
                'total_price': float(booking.total_price) if booking.total_price else 0,
                'status': booking.status,
                'home': {
                    'id': booking.home.id if booking.home else None,
                    'title': booking.home.title if booking.home else None
                } if booking.home else None,
                'renter': {
                    'id': booking.renter.id if booking.renter else None,
                    'username': booking.renter.username if booking.renter else None,
                    'full_name': booking.renter.full_name if booking.renter else None,
                    'email': booking.renter.email if booking.renter else None,
                    'phone': booking.renter.phone if booking.renter else None
                } if booking.renter else None
            }
            bookings_data.append(booking_dict)
        
        return jsonify({
            'success': True,
            'bookings': bookings_data,
            'date': date
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@owner_bp.route('/calendar/api/booking/<int:booking_id>')
@owner_required
def get_booking_detail(booking_id):
    """API endpoint to get detailed booking information"""
    try:
        booking = Booking.query.get_or_404(booking_id)
        
        # Check if booking belongs to current user's home
        if booking.home.owner_id != current_user.id:
            return jsonify({
                'success': False,
                'error': 'Unauthorized access'
            }), 403
        
        booking_detail = {
            'id': booking.id,
            'start_time': booking.start_time.isoformat() if booking.start_time else None,
            'end_time': booking.end_time.isoformat() if booking.end_time else None,
            'created_at': booking.created_at.isoformat() if booking.created_at else None,
            'booking_type': booking.booking_type,
            'total_hours': booking.total_hours,
            'total_price': float(booking.total_price) if booking.total_price else 0,
            'status': booking.status,
            'special_requests': getattr(booking, 'special_requests', None),
            'home': {
                'id': booking.home.id,
                'title': booking.home.title,
                'home_type': booking.home.home_type,
                'city': booking.home.city,
                'district': booking.home.district,
                'price_per_hour': float(booking.home.price_per_hour) if booking.home.price_per_hour else 0
            } if booking.home else None,
            'renter': {
                'id': booking.renter.id,
                'username': booking.renter.username,
                'full_name': booking.renter.full_name,
                'email': booking.renter.email,
                'phone': booking.renter.phone
            } if booking.renter else None
        }
        
        return jsonify({
            'success': True,
            'booking': booking_detail
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@owner_bp.route('/calendar/api/dates-with-bookings/<int:year>/<int:month>')
@owner_required
def get_dates_with_bookings(year, month):
    """API endpoint to get dates that have bookings for calendar dots"""
    try:
        from datetime import datetime, date
        from calendar import monthrange
        
        # Get first and last day of the month
        first_day = date(year, month, 1)
        last_day = date(year, month, monthrange(year, month)[1])
        
        # Get all homes owned by current user
        homes = Home.query.filter_by(owner_id=current_user.id).all()
        home_ids = [home.id for home in homes]
        
        # Get bookings for the month
        bookings = Booking.query.filter(
            Booking.home_id.in_(home_ids),
            func.date(Booking.start_time) >= first_day,
            func.date(Booking.start_time) <= last_day
        ).all()
        
        # Extract unique dates
        dates_with_bookings = set()
        for booking in bookings:
            if booking.start_time:
                dates_with_bookings.add(booking.start_time.date().day)
        
        return jsonify({
            'success': True,
            'dates': list(dates_with_bookings),
            'year': year,
            'month': month
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@owner_bp.route('/view-bookings')
@owner_bp.route('/view-bookings/<status>')
@owner_required
def view_bookings(status=None):
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 50  # 50 items per page
    
    # Get all homes owned by current user
    homes = Home.query.filter_by(owner_id=current_user.id).all()
    
    # Get all bookings for these homes
    all_bookings = []
    for home in homes:
        all_bookings.extend(home.bookings)
    
    # Filter bookings by status if specified
    if status:
        all_bookings = [b for b in all_bookings if b.status == status]
    
    # Sort bookings by created_at date, newest first
    all_bookings.sort(key=lambda x: x.created_at, reverse=True)
    
    # Calculate pagination
    total_bookings = len(all_bookings)
    total_pages = (total_bookings + per_page - 1) // per_page  # Ceiling division
    
    # Get bookings for current page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_bookings = all_bookings[start_idx:end_idx]
    
    # Create pagination info
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total_bookings,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_num': page - 1 if page > 1 else None,
        'next_num': page + 1 if page < total_pages else None
    }
    
    return render_template('owner/view_bookings.html', 
                          bookings=all_bookings,  # All bookings for counts
                          filtered_bookings=paginated_bookings,  # Paginated bookings for display
                          current_status=status,
                          pagination=pagination)


@owner_bp.route('/home/<int:home_id>/add-images', methods=['GET', 'POST'])
@owner_required
def add_home_images(home_id):
    home = Home.query.get_or_404(home_id)
    
    # Kiểm tra quyền sở hữu
    if home.owner_id != current_user.id:
        flash('Bạn không có quyền thêm ảnh cho nhà này.', 'danger')
        return redirect(url_for('owner.dashboard'))
    
    if request.method == 'POST':
        images = request.files.getlist('images')
        for img_file in images:
            if img_file and img_file.filename:
                # Process image to improve quality and standardize size
                try:
                    # Open the image
                    img = Image.open(img_file)
                    
                    # Convert to RGB if needed (for PNG with transparency)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Resize to a standard size while maintaining aspect ratio
                    max_size = (800, 600)
                    img.thumbnail(max_size, Image.LANCZOS)
                    
                    # Use new image storage structure
                    relative_path, absolute_path = get_user_upload_path('owner', current_user.id, home.id)
                    
                    # Generate unique filename
                    filename = generate_unique_filename(img_file.filename, 'home')
                    save_path = os.path.join(absolute_path, filename)
                    
                    # Save the processed image
                    img.save(save_path, quality=85, optimize=True)
                    
                    # Create database record
                    is_featured = not HomeImage.query.filter_by(home_id=home.id, is_featured=True).first()
                    
                    new_img = HomeImage(
                        image_path=f"{relative_path}/{filename}",
                        home_id=home.id,
                        is_featured=is_featured
                    )
                    db.session.add(new_img)
                    
                except Exception as e:
                    # Log the error but continue processing other images
                    print(f"Error processing image: {e}")
                    continue
                    
        db.session.commit()
        flash("Ảnh đã được thêm thành công vào thư viện nhà!", "success")
        return redirect(url_for('owner.add_home_images', home_id=home.id))
    
    # Get existing images for this home
    existing_images = HomeImage.query.filter_by(home_id=home.id).all()
    
    return render_template('owner/add_home_images.html', home=home, existing_images=existing_images)

@owner_bp.route('/set-featured-image/<int:image_id>', methods=['GET'])
@login_required
def set_featured_image(image_id):
    # Lấy thông tin ảnh
    image = HomeImage.query.get_or_404(image_id)
    home = image.home

    # Kiểm tra quyền sở hữu
    if home.owner_id != current_user.id:
        flash("Bạn không có quyền thực hiện thao tác này.", "danger")
        return redirect(url_for('owner.dashboard'))

    # Bỏ featured của tất cả ảnh khác trong nhà
    HomeImage.query.filter_by(home_id=home.id).update({HomeImage.is_featured: False})
    
    # Đặt ảnh được chọn làm featured
    image.is_featured = True
    db.session.commit()

    flash("Đã đặt ảnh làm ảnh đại diện thành công!", "success")
    return redirect(url_for('owner.add_home_images', home_id=home.id))

@owner_bp.route('/home-image/<int:image_id>/delete', methods=['GET', 'POST'])
@owner_required
def delete_home_image(image_id):
    image = HomeImage.query.get_or_404(image_id)
    home_id = image.home_id
    
    # Lấy thông tin nhà để kiểm tra quyền sở hữu
    home = Home.query.get_or_404(home_id)
    
    # Kiểm tra quyền sở hữu
    if home.owner_id != current_user.id:
        flash('Bạn không có quyền xóa ảnh của nhà này.', 'danger')
        return redirect(url_for('owner.dashboard'))
    
    # Delete the image file using new utility function
    if image.image_path:
        delete_user_image(image.image_path)
    
    # Check if this was the featured image
    was_featured = image.is_featured
    
    # Delete the database record
    db.session.delete(image)
    db.session.commit()
    
    # If we deleted the featured image, set a new one if available
    if was_featured:
        next_image = HomeImage.query.filter_by(home_id=home_id).first()
        if next_image:
            next_image.is_featured = True
            db.session.commit()
    
    flash('Đã xóa ảnh thành công!', 'success')
    
    # Check if the request came from edit_home page
    referer = request.headers.get('Referer', '')
    if '/edit-home/' in referer:
        return redirect(url_for('owner.edit_home', home_id=home_id))
    else:
        return redirect(url_for('owner.add_home_images', home_id=home_id))


@owner_bp.route('/home-detail/<int:home_id>')
@login_required
def home_detail(home_id):
    """Redirect to edit home - no separate detail page needed"""
    home = Home.query.get_or_404(home_id)
    if home.owner_id != current_user.id:
        flash('Bạn không có quyền xem nhà này!', 'danger')
        return redirect(url_for('owner.dashboard'))
    
    # Redirect to edit page to view/edit details
    return redirect(url_for('owner.edit_home', home_id=home_id))

@owner_bp.route('/booking-details/<int:booking_id>')
@owner_required
def booking_details(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Ensure this booking belongs to one of the current owner's homes
    if booking.home.owner_id != current_user.id:
        flash('Bạn không có quyền xem thông tin đặt nhà này.', 'danger')
        return redirect(url_for('owner.dashboard'))

    return render_template('owner/booking_details.html', booking=booking)

@owner_bp.route('/settings')
@login_required
@owner_required
def settings():
    # Kiểm tra email verification cho Owner
    if current_user.is_owner() and not current_user.email_verified and current_user.first_login:
        return redirect(url_for('owner.verify_email'))
    return render_template('owner/settings.html')

@owner_bp.route('/change_password', methods=['POST'])
@login_required
@owner_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # Validate input
    if not current_password or not new_password or not confirm_password:
        flash('Vui lòng điền đầy đủ thông tin', 'danger')
        return redirect(url_for('owner.settings'))
    
    # Check if current password is correct
    if not current_user.check_password(current_password):
        flash('Mật khẩu hiện tại không đúng', 'danger')
        return redirect(url_for('owner.settings'))
    
    # Check if new passwords match
    if new_password != confirm_password:
        flash('Mật khẩu mới không khớp', 'danger')
        return redirect(url_for('owner.settings'))
    
    # Update password
    current_user.set_password(new_password)
    db.session.commit()
    
    flash('Mật khẩu đã được cập nhật thành công', 'success')
    return redirect(url_for('owner.settings'))

@owner_bp.route('/update_profile', methods=['POST'])
@login_required
@owner_required
def update_profile():
    try:
        # Update account settings
        if 'username' in request.form:
            current_user.username = request.form.get('username')
            # Xử lý email với validation và cleaning
            email_input = request.form.get('email')
            if email_input:
                cleaned_email, is_valid = process_email(email_input)
                if is_valid:
                    current_user.email = cleaned_email
                else:
                    flash('Email không hợp lệ!', 'warning')
        
        # Update business information
        if 'business_name' in request.form:
            current_user.business_name = request.form.get('business_name')
            current_user.tax_code = request.form.get('tax_code')
            current_user.bank_name = request.form.get('bank_name')
            current_user.bank_account = request.form.get('bank_account')
        
        db.session.commit()
        flash('Thông tin đã được cập nhật thành công', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi cập nhật thông tin: {str(e)}', 'danger')
    
    return redirect(url_for('owner.settings'))

@owner_bp.route('/profile', methods=['GET', 'POST'])
@owner_required
def profile():
    # Kiểm tra email verification cho Owner
    if current_user.is_owner() and not current_user.email_verified and current_user.first_login:
        return redirect(url_for('owner.verify_email'))
    if request.method == 'POST':
        print(f"🔍 DEBUG: Owner profile POST request received")
        print(f"🔍 DEBUG: Form data keys: {list(request.form.keys())}")
        print(f"🔍 DEBUG: Files in request: {list(request.files.keys())}")
        try:
            # Cập nhật thông tin cơ bản (không cập nhật username vì form không có field này)
            current_user.first_name = request.form.get('first_name')
            current_user.last_name = request.form.get('last_name')
            current_user.gender = request.form.get('gender')
            current_user.nationality = request.form.get('nationality')
            # Xử lý email với validation và cleaning
            email_input = request.form.get('email')
            if email_input:
                cleaned_email, is_valid = process_email(email_input)
                if is_valid:
                    current_user.email = cleaned_email
                else:
                    flash('Email không hợp lệ!', 'warning')
            current_user.phone = request.form.get('phone')
            current_user.address = request.form.get('address')
            
            # Xử lý ngày sinh (định dạng DD/MM/YYYY từ flatpickr)
            birth_date_str = request.form.get('birth_date')
            if birth_date_str:
                try:
                    # Parse DD/MM/YYYY format
                    current_user.birth_date = datetime.strptime(birth_date_str, '%d/%m/%Y').date()
                except ValueError:
                    pass  # Ignore invalid date
            
            # Xử lý upload avatar với cấu trúc mới
            avatar_file = request.files.get('avatar')
            print(f"🔍 DEBUG: Avatar file received: {avatar_file}")
            print(f"🔍 DEBUG: Avatar filename: {avatar_file.filename if avatar_file else 'None'}")
            
            if avatar_file and avatar_file.filename and allowed_file(avatar_file.filename):
                print(f"🔍 DEBUG: Avatar file passed validation")
                print(f"🔍 DEBUG: Current user ID: {current_user.id}")
                print(f"🔍 DEBUG: Current avatar: {current_user.avatar}")
                
                # Xóa avatar cũ nếu có
                if current_user.avatar:
                    print(f"🔍 DEBUG: Deleting old avatar: {current_user.avatar}")
                    delete_user_image(current_user.avatar)
                
                # Lưu avatar mới với cấu trúc data/owner/{owner_id}/
                print(f"🔍 DEBUG: Saving new avatar...")
                avatar_path = save_user_image(avatar_file, 'owner', current_user.id, prefix='avatar')
                print(f"🔍 DEBUG: Avatar saved to: {avatar_path}")
                
                if avatar_path:
                    # Xử lý xoay ảnh và resize
                    try:
                        full_path = os.path.join('static', avatar_path)
                        print(f"🔍 DEBUG: Processing image at: {full_path}")
                        
                        # Sửa hướng xoay ảnh theo EXIF
                        fix_image_orientation(full_path)
                        
                        # Resize image sau khi sửa hướng
                        with Image.open(full_path) as img:
                            # Tạo ảnh vuông bằng cách crop từ giữa
                            width, height = img.size
                            if width != height:
                                # Crop to square from center
                                min_size = min(width, height)
                                left = (width - min_size) // 2
                                top = (height - min_size) // 2
                                right = left + min_size
                                bottom = top + min_size
                                img = img.crop((left, top, right, bottom))
                            
                            # Resize to 200x200
                            img = img.resize((200, 200), Image.Resampling.LANCZOS)
                            img.save(full_path, optimize=True, quality=85)
                            print(f"🔍 DEBUG: Image processing completed")
                    except Exception as e:
                        print(f"❌ Error processing avatar: {e}")
                    
                    current_user.avatar = avatar_path
                    print(f"🔍 DEBUG: Updated current_user.avatar to: {avatar_path}")
                else:
                    print(f"❌ DEBUG: Avatar path is None - save failed")
            else:
                if avatar_file:
                    print(f"❌ DEBUG: Avatar file validation failed")
                    print(f"   - Has filename: {bool(avatar_file.filename)}")
                    print(f"   - Allowed file: {allowed_file(avatar_file.filename) if avatar_file.filename else 'N/A'}")
                else:
                    print(f"🔍 DEBUG: No avatar file in request")
            
            db.session.commit()
            flash('Cập nhật thông tin thành công!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'danger')
        
        return redirect(url_for('owner.profile'))
            
    return render_template('owner/profile.html')

@owner_bp.route('/book-home/<int:home_id>', methods=['GET', 'POST'])
@owner_bp.route('/book-home', methods=['GET', 'POST'])
@owner_required
def book_home(home_id=None):
    # If home_id is provided in URL params, use it (though we don't really need it since home = owner)
    home_id_param = request.args.get('home_id', type=int)
    
    if home_id:
        # Original functionality - book a specific home
        home = Home.query.get_or_404(home_id)
    else:
        # If no home_id, redirect to manage homes to select a home
        return redirect(url_for('owner.dashboard'))
    
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        start_time = request.form.get('start_time')
        duration_str = request.form.get('duration')
        
        if not start_date or not start_time or not duration_str:
            flash("You must select date, time and duration.", "warning")
            return redirect(url_for('owner.book_home', home_id=home.id))
        
        try:
            duration = int(duration_str)
        except ValueError:
            flash("Invalid duration value.", "danger")
            return redirect(url_for('owner.book_home', home_id=home.id))
        
        if duration < 1:
            flash("Minimum duration is 1 night.", "warning")
            return redirect(url_for('owner.book_home', home_id=home.id))
        
        start_str = f"{start_date} {start_time}"
        try:
            start_datetime = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
        except ValueError:
            flash("Invalid date or time format.", "danger")
            return redirect(url_for('owner.book_home', home_id=home.id))
        
        end_datetime = start_datetime + timedelta(days=duration)
        # Calculate total price using the home's price per night
        total_price = home.price_per_day * duration
        
        # Check for overlapping bookings for this home
        existing_bookings = Booking.query.filter_by(home_id=home.id).all()
        for booking in existing_bookings:
            if start_datetime < booking.end_time and end_datetime > booking.start_time:
                flash('This home is not available during the selected time period.', 'danger')
                return redirect(url_for('owner.book_home', home_id=home.id))
        
        new_booking = Booking(
            home_id=home.id,
            renter_id=current_user.id,
            start_time=start_datetime,
            end_time=end_datetime,
            total_price=total_price,
            status='pending'
        )
        
        db.session.add(new_booking)
        current_user.experience_points += total_price * 10  # Update user XP based on total price
        db.session.commit()

        flash('Booking request submitted successfully!', 'success')
        return redirect(url_for('owner.dashboard'))

    # Create owner object for display
    owner_display = current_user
    # Add title property if not exists
    if not hasattr(owner_display, 'title'):
        owner_display.title = owner_display.full_name or owner_display.username or "My Home Business"

    return render_template('owner/book_home.html', home=home, owner=owner_display)

@owner_bp.route('/check-username', methods=['POST'])
@login_required
def check_username():
    data = request.get_json()
    username = data.get('username')
    
    # Kiểm tra nếu username này là của user hiện tại thì available
    if username == current_user.username:
        return jsonify({'available': True})
    
    existing_owner = Owner.query.filter_by(username=username).first()
    existing_admin = Admin.query.filter_by(username=username).first()
    existing_renter = Renter.query.filter_by(username=username).first()
    
    return jsonify({
        'available': not bool(existing_owner or existing_admin or existing_renter)
    })

@owner_bp.route('/check-email', methods=['POST'])
@login_required
def check_email():
    data = request.get_json()
    email = data.get('email')
    
    # Kiểm tra nếu email này là của user hiện tại thì available
    if email == current_user.email:
        return jsonify({'available': True})
    
    existing_owner = Owner.query.filter_by(email=email).first()
    existing_admin = Admin.query.filter_by(email=email).first()
    existing_renter = Renter.query.filter_by(email=email).first()
    
    return jsonify({
        'available': not bool(existing_owner or existing_admin or existing_renter)
    })

@owner_bp.route('/toggle-home-status/<int:home_id>', methods=['GET', 'POST'])
@login_required
def toggle_home_status(home_id):
    home = Home.query.get_or_404(home_id)
    if home.owner_id != current_user.id:
        flash('Bạn không có quyền thay đổi trạng thái nhà này!', 'danger')
        return redirect(url_for('owner.dashboard'))
    
    # Toggle the home's active status
    home.is_active = not home.is_active
    db.session.commit()
    
    status = 'mở khóa' if home.is_active else 'khóa'
    flash(f'Đã {status} nhà thành công!', 'success')
    return redirect(url_for('owner.dashboard'))

@owner_bp.route('/statistics')
@owner_required
def statistics():
    # Kiểm tra email verification cho Owner
    if current_user.is_owner() and not current_user.email_verified and current_user.first_login:
        return redirect(url_for('owner.verify_email'))
    """Owner statistics page showing revenue, bookings, and performance data"""
    try:
        # Get all homes owned by current user
        owner_homes = Home.query.filter_by(owner_id=current_user.id).all()
        home_ids = [home.id for home in owner_homes]
        
        if not home_ids:
            # If owner has no homes, show empty stats
            return render_template('owner/statistics.html', 
                                   stats={
                                       'total_profit': 0,
                                       'total_hours': 0,
                                       'total_bookings': 0,
                                       'booking_rate': 0,
                                       'common_type': 'N/A',
                                       'average_rating': 0,
                                       'hourly_revenue': 0,
                                       'nightly_revenue': 0,
                                       'top_homes': []
                                   })
        
        # Get all completed and confirmed bookings for owner's homes
        completed_bookings = Booking.query.filter(
            Booking.home_id.in_(home_ids),
            Booking.status.in_(['completed', 'confirmed'])
        ).all()
        
        # Calculate basic statistics
        total_bookings = len(completed_bookings)
        total_profit = sum(booking.total_price for booking in completed_bookings)
        total_hours = sum((b.end_time - b.start_time).total_seconds() / 3600 for b in completed_bookings)
        
        # Count booking types
        hourly_count = sum(1 for b in completed_bookings if b.booking_type == 'hourly')
        nightly_count = total_bookings - hourly_count
        
        # Calculate revenue by type
        hourly_revenue = sum(b.total_price for b in completed_bookings if b.booking_type == 'hourly')
        nightly_revenue = sum(b.total_price for b in completed_bookings if b.booking_type == 'daily')
        
        # Determine common booking type
        if hourly_count > nightly_count:
            common_type = "Theo giờ"
        elif nightly_count > hourly_count:
            common_type = "Theo ngày"
        else:
            common_type = "N/A"
        
        # Calculate booking rate (percentage of time homes are booked)
        # This is a simplified calculation - you might want to make it more sophisticated
        booking_rate = min((total_hours / (len(owner_homes) * 24 * 30)) * 100, 100) if owner_homes else 0
        
        # Calculate average rating
        all_reviews = Review.query.filter(Review.home_id.in_(home_ids)).all()
        average_rating = sum(r.rating for r in all_reviews) / len(all_reviews) if all_reviews else 0
        
        # Get top performing homes
        top_homes_query = db.session.query(
            Home.id,
            Home.title,
            func.count(Booking.id).label('booking_count'),
            func.sum(Booking.total_price).label('total_revenue'),
            func.avg(Review.rating).label('avg_rating')
        ).select_from(Home)\
         .outerjoin(Booking, (Home.id == Booking.home_id) & (Booking.status.in_(['completed', 'confirmed'])))\
         .outerjoin(Review, Home.id == Review.home_id)\
         .filter(Home.owner_id == current_user.id)\
         .group_by(Home.id, Home.title)\
         .order_by(func.sum(Booking.total_price).desc())\
         .limit(5).all()
        
        top_homes = []
        for home_data in top_homes_query:
            home = Home.query.get(home_data.id)
            home_bookings = [b for b in completed_bookings if b.home_id == home_data.id]
            
            # Determine most common booking type for this home
            home_hourly = sum(1 for b in home_bookings if b.booking_type == 'hourly')
            home_nightly = len(home_bookings) - home_hourly
            home_common_type = "Theo giờ" if home_hourly >= home_nightly else "Theo ngày"
            
            # Calculate booking rate for this home
            home_total_hours = sum((b.end_time - b.start_time).total_seconds() / 3600 for b in home_bookings)
            home_booking_rate = min((home_total_hours / (24 * 30)) * 100, 100) if home_total_hours > 0 else 0
            
            top_homes.append({
                'name': home_data.title,
                'type': home_common_type,
                'revenue': int(home_data.total_revenue or 0),
                'bookings': home_data.booking_count or 0,
                'booking_rate': f"{home_booking_rate:.0f}%",
                'rating': f"{home_data.avg_rating:.1f}" if home_data.avg_rating else "0.0"
            })
        
        # Generate chart data for the last 7 days
        chart_data = []
        for i in range(6, -1, -1):
            date = datetime.now().date() - timedelta(days=i)
            day_bookings = [b for b in completed_bookings if b.created_at.date() == date]
            day_revenue = sum(b.total_price for b in day_bookings)
            chart_data.append({
                'date': date.strftime('%d/%m'),
                'revenue': int(day_revenue)
            })
        
        stats = {
            'total_profit': int(total_profit),
            'total_hours': int(total_hours),
            'total_bookings': total_bookings,
            'booking_rate': f"{booking_rate:.0f}%",
            'common_type': common_type,
            'average_rating': f"{average_rating:.1f}/5.0",
            'hourly_revenue': int(hourly_revenue),
            'nightly_revenue': int(nightly_revenue),
            'top_homes': top_homes,
            'chart_data': chart_data
        }
        
        return render_template('owner/statistics.html', stats=stats)
        
    except Exception as e:
        print(f"Error in owner statistics: {e}")
        # Return empty stats on error
        return render_template('owner/statistics.html', 
                               stats={
                                   'total_profit': 0,
                                   'total_hours': 0,
                                   'total_bookings': 0,
                                   'booking_rate': 0,
                                   'common_type': 'N/A',
                                   'average_rating': 0,
                                   'hourly_revenue': 0,
                                   'nightly_revenue': 0,
                                   'top_homes': []
                               })

@owner_bp.route('/api/chart-data/<period>')
@owner_bp.route('/api/chart-data/<period>/<chart_type>')
@owner_required
def get_chart_data(period, chart_type='both'):
    """API endpoint to get chart data for different periods"""
    try:
        # Get all homes owned by current user
        owner_homes = Home.query.filter_by(owner_id=current_user.id).all()
        home_ids = [home.id for home in owner_homes]
        
        if not home_ids:
            return jsonify({'hourly': [], 'daily': []})
        
        # Get completed and confirmed bookings (confirmed bookings should also appear in charts)
        completed_bookings = Booking.query.filter(
            Booking.home_id.in_(home_ids),
            Booking.status.in_(['completed', 'confirmed'])
        ).all()
        
        if period == 'total':
            # Generate data for ALL completed bookings divided into exactly 20 columns
            chart_data_hourly = []
            chart_data_nightly = []
            
            # Get date range of all bookings
            if completed_bookings:
                earliest_booking = min(b.created_at for b in completed_bookings)
                latest_booking = max(b.created_at for b in completed_bookings)
                
                # Calculate total time span in days
                total_days = (latest_booking.date() - earliest_booking.date()).days + 1
                
                # Divide into 20 equal periods
                days_per_period = max(1, total_days // 20)
                
                for i in range(20):
                    # Calculate start and end date for this period
                    period_start = earliest_booking.date() + timedelta(days=i * days_per_period)
                    
                    # For the last period, make sure it goes to the end
                    if i == 19:
                        period_end = latest_booking.date()
                    else:
                        period_end = earliest_booking.date() + timedelta(days=(i + 1) * days_per_period - 1)
                        # Don't exceed the latest booking date
                        if period_end > latest_booking.date():
                            period_end = latest_booking.date()
                    
                    # Get bookings for this period
                    period_bookings = [b for b in completed_bookings 
                                     if period_start <= b.created_at.date() <= period_end]
                    
                    # Separate hourly and nightly bookings
                    hourly_bookings = [b for b in period_bookings if b.booking_type == 'hourly']
                    nightly_bookings = [b for b in period_bookings if b.booking_type == 'daily']
                    
                    hourly_revenue = sum(b.total_price for b in hourly_bookings)
                    nightly_revenue = sum(b.total_price for b in nightly_bookings)
                    
                    # Create period label
                    if days_per_period <= 7:
                        # For short periods, show date range
                        period_label = f"{period_start.strftime('%d/%m')}-{period_end.strftime('%d/%m')}"
                    elif days_per_period <= 31:
                        # For medium periods, show week numbers or dates
                        period_label = f"{period_start.strftime('%d/%m')}"
                    else:
                        # For long periods, show month/year
                        period_label = f"{period_start.strftime('%m/%Y')}"
                    
                    chart_data_hourly.append({
                        'date': period_label,
                        'revenue': int(hourly_revenue)
                    })
                    
                    chart_data_nightly.append({
                        'date': period_label,
                        'revenue': int(nightly_revenue)
                    })
            else:
                # No bookings, return empty data
                chart_data_hourly = []
                chart_data_nightly = []
        
        elif period == 'week':
            # Generate data for exactly 7 days counting from today (6 days ago to today)
            # Days arranged from left to right: oldest to newest
            chart_data_hourly = []
            chart_data_nightly = []
            
            # Generate exactly 7 days from 6 days ago to today
            for i in range(6, -1, -1):  # 6, 5, 4, 3, 2, 1, 0 (left to right: oldest to newest)
                date = datetime.now().date() - timedelta(days=i)
                day_bookings = [b for b in completed_bookings if b.created_at.date() == date]
                
                # Separate hourly and nightly bookings
                hourly_bookings = [b for b in day_bookings if b.booking_type == 'hourly']
                nightly_bookings = [b for b in day_bookings if b.booking_type == 'daily']
                
                hourly_revenue = sum(b.total_price for b in hourly_bookings)
                nightly_revenue = sum(b.total_price for b in nightly_bookings)
                
                chart_data_hourly.append({
                    'date': date.strftime('%d/%m'),
                    'revenue': int(hourly_revenue)
                })
                
                chart_data_nightly.append({
                    'date': date.strftime('%d/%m'),
                    'revenue': int(nightly_revenue)
                })
        
        elif period == 'month':
            # Generate data for the last 30 days
            chart_data_hourly = []
            chart_data_nightly = []
            
            for i in range(29, -1, -1):  # 30 days
                date = datetime.now().date() - timedelta(days=i)
                day_bookings = [b for b in completed_bookings if b.created_at.date() == date]
                
                # Separate hourly and nightly bookings
                hourly_bookings = [b for b in day_bookings if b.booking_type == 'hourly']
                nightly_bookings = [b for b in day_bookings if b.booking_type == 'daily']
                
                hourly_revenue = sum(b.total_price for b in hourly_bookings)
                nightly_revenue = sum(b.total_price for b in nightly_bookings)
                
                chart_data_hourly.append({
                    'date': date.strftime('%d/%m'),
                    'revenue': int(hourly_revenue)
                })
                
                chart_data_nightly.append({
                    'date': date.strftime('%d/%m'),
                    'revenue': int(nightly_revenue)
                })
        
        elif period == 'year':
            # Generate data for the last 12 months
            chart_data_hourly = []
            chart_data_nightly = []
            
            for i in range(11, -1, -1):  # 12 months
                # Calculate start and end of each month
                current_date = datetime.now().date()
                target_month = current_date.replace(day=1) - timedelta(days=i*30)
                
                # Get first day of target month
                first_day = target_month.replace(day=1)
                
                # Get last day of target month
                if first_day.month == 12:
                    last_day = first_day.replace(year=first_day.year + 1, month=1) - timedelta(days=1)
                else:
                    last_day = first_day.replace(month=first_day.month + 1) - timedelta(days=1)
                
                month_bookings = [b for b in completed_bookings 
                                if first_day <= b.created_at.date() <= last_day]
                
                # Separate hourly and nightly bookings
                hourly_bookings = [b for b in month_bookings if b.booking_type == 'hourly']
                nightly_bookings = [b for b in month_bookings if b.booking_type == 'daily']
                
                hourly_revenue = sum(b.total_price for b in hourly_bookings)
                nightly_revenue = sum(b.total_price for b in nightly_bookings)
                
                month_label = first_day.strftime('%m/%Y')
                
                chart_data_hourly.append({
                    'date': month_label,
                    'revenue': int(hourly_revenue)
                })
                
                chart_data_nightly.append({
                    'date': month_label,
                    'revenue': int(nightly_revenue)
                })
        
        return jsonify({
            'hourly': chart_data_hourly,
            'daily': chart_data_nightly
        })
        
    except Exception as e:
        print(f"Error getting chart data: {e}")
        return jsonify({'hourly': [], 'daily': []}), 500

@owner_bp.route('/api/stats-data/<period>')
@owner_bp.route('/api/stats-data/<period>/<chart_type>')
@owner_required
def get_stats_data(period, chart_type='both'):
    """API endpoint to get statistics data for different periods"""
    try:
        # Get all homes owned by current user
        owner_homes = Home.query.filter_by(owner_id=current_user.id).all()
        home_ids = [home.id for home in owner_homes]
        
        if not home_ids:
            return jsonify({
                'total_profit': '0đ',
                'total_hours': '0 giờ',
                'total_bookings': '0 lần',
                'booking_rate': '0%',
                'common_type': 'N/A',
                'average_rating': '0/5',
                'top_homes': []
            })
        
        # Calculate date range based on period
        end_date = datetime.now()
        
        if period == 'total':
            start_date = None  # All time
        elif period == 'week':
            start_date = end_date - timedelta(days=7)
        elif period == 'month':
            start_date = end_date - timedelta(days=30)
        elif period == 'year':
            start_date = end_date - timedelta(days=365)
        else:
            return jsonify({'error': 'Invalid period'}), 400
        
        # Get completed and confirmed bookings (confirmed bookings should also appear in stats)
        query = Booking.query.filter(
            Booking.home_id.in_(home_ids),
            Booking.status.in_(['completed', 'confirmed'])
        )
        
        if start_date:
            query = query.filter(Booking.created_at >= start_date)
        
        # Filter by chart type
        if chart_type == 'hourly':
            query = query.filter(Booking.booking_type == 'hourly')
        elif chart_type == 'daily':
            query = query.filter(Booking.booking_type == 'daily')
        # If chart_type == 'both', don't add any filter
        
        completed_bookings = query.all()
        
        # Calculate basic statistics
        total_bookings = len(completed_bookings)
        total_profit = sum(booking.total_price for booking in completed_bookings)
        total_hours = sum((b.end_time - b.start_time).total_seconds() / 3600 for b in completed_bookings)
        
        # Count booking types
        hourly_count = sum(1 for b in completed_bookings if b.booking_type == 'hourly')
        nightly_count = total_bookings - hourly_count
        
        # Determine common booking type
        if hourly_count > nightly_count:
            common_type = "Theo giờ"
        elif nightly_count > hourly_count:
            common_type = "Theo ngày"
        else:
            common_type = "N/A"
        
        # Calculate booking rate (percentage of time homes are booked)
        days_in_period = 30 if period == 'month' else (7 if period == 'week' else (365 if period == 'year' else 30))
        booking_rate = min((total_hours / (len(owner_homes) * 24 * days_in_period)) * 100, 100) if owner_homes else 0
        
        # Calculate average rating
        review_query = Review.query.filter(Review.home_id.in_(home_ids))
        if start_date:
            review_query = review_query.filter(Review.created_at >= start_date)
        
        all_reviews = review_query.all()
        average_rating = sum(r.rating for r in all_reviews) / len(all_reviews) if all_reviews else 0
        
        # Get top performing homes
        top_homes_query = db.session.query(
            Home.id,
            Home.title,
            func.count(Booking.id).label('booking_count'),
            func.sum(Booking.total_price).label('total_revenue'),
            func.avg(Review.rating).label('avg_rating')
        ).select_from(Home)\
         .outerjoin(Booking, (Home.id == Booking.home_id) & (Booking.status.in_(['completed', 'confirmed'])))\
         .outerjoin(Review, Home.id == Review.home_id)\
         .filter(Home.owner_id == current_user.id)
        
        if start_date:
            top_homes_query = top_homes_query.filter(Booking.created_at >= start_date)
        
        top_homes_data = top_homes_query.group_by(Home.id, Home.title)\
                                       .order_by(func.sum(Booking.total_price).desc())\
                                       .limit(5).all()
        
        top_homes = []
        for home_data in top_homes_data:
            home_bookings = [b for b in completed_bookings if b.home_id == home_data.id]
            
            # Determine most common booking type for this home
            home_hourly = sum(1 for b in home_bookings if b.booking_type == 'hourly')
            home_nightly = len(home_bookings) - home_hourly
            home_common_type = "Theo giờ" if home_hourly >= home_nightly else "Theo ngày"
            
            # Calculate booking rate for this home
            home_total_hours = sum((b.end_time - b.start_time).total_seconds() / 3600 for b in home_bookings)
            home_booking_rate = min((home_total_hours / (24 * days_in_period)) * 100, 100) if home_total_hours > 0 else 0
            
            top_homes.append({
                'name': home_data.title,
                'type': home_common_type,
                'revenue': int(home_data.total_revenue or 0),
                'bookings': home_data.booking_count or 0,
                'booking_rate': f"{home_booking_rate:.0f}%",
                'rating': f"{home_data.avg_rating:.1f}" if home_data.avg_rating else "0.0"
            })
        
        return jsonify({
            'total_profit': f"{int(total_profit):,}đ",
            'total_hours': f"{int(total_hours):,} giờ",
            'total_bookings': f"{total_bookings} lần",
            'booking_rate': f"{booking_rate:.0f}%",
            'common_type': common_type,
            'average_rating': f"{average_rating:.1f}/5",
            'top_homes': top_homes
        })
        
    except Exception as e:
        print(f"Error getting stats data: {e}")
        return jsonify({'error': 'Internal server error'}), 500



@owner_bp.route('/api/stats-data/custom')
@owner_bp.route('/api/stats-data/custom/<chart_type>')
@owner_required
def get_custom_stats_data(chart_type='both'):
    """API endpoint to get statistics data for custom date range"""
    try:
        start_date_str = request.args.get('start')
        end_date_str = request.args.get('end')
        
        if not start_date_str or not end_date_str:
            return jsonify({'error': 'Missing start or end date'}), 400
        
        # Parse dates
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)  # Include end date
        
        # Get all homes owned by current user
        owner_homes = Home.query.filter_by(owner_id=current_user.id).all()
        home_ids = [home.id for home in owner_homes]
        
        if not home_ids:
            return jsonify({
                'total_profit': '0đ',
                'total_hours': '0 giờ',
                'total_bookings': '0 lần',
                'booking_rate': '0%',
                'common_type': 'N/A',
                'average_rating': '0/5',
                'top_homes': []
            })
        
        # Get completed and confirmed bookings in date range
        query = Booking.query.filter(
            Booking.home_id.in_(home_ids),
            Booking.status.in_(['completed', 'confirmed']),
            Booking.created_at >= start_date,
            Booking.created_at < end_date
        )
        
        # Filter by chart type
        if chart_type == 'hourly':
            query = query.filter(Booking.booking_type == 'hourly')
        elif chart_type == 'daily':
            query = query.filter(Booking.booking_type == 'daily')
        # If chart_type == 'both', don't add any filter
        
        completed_bookings = query.all()
        
        # Calculate basic statistics
        total_bookings = len(completed_bookings)
        total_profit = sum(booking.total_price for booking in completed_bookings)
        total_hours = sum((b.end_time - b.start_time).total_seconds() / 3600 for b in completed_bookings)
        
        # Count booking types
        hourly_count = sum(1 for b in completed_bookings if b.booking_type == 'hourly')
        nightly_count = total_bookings - hourly_count
        
        # Determine common booking type
        if hourly_count > nightly_count:
            common_type = "Theo giờ"
        elif nightly_count > hourly_count:
            common_type = "Theo ngày"
        else:
            common_type = "N/A"
        
        # Calculate booking rate (percentage of time homes are booked)
        days_in_range = (end_date - start_date).days
        booking_rate = min((total_hours / (len(owner_homes) * 24 * days_in_range)) * 100, 100) if owner_homes and days_in_range > 0 else 0
        
        # Calculate average rating
        all_reviews = Review.query.filter(
            Review.home_id.in_(home_ids),
            Review.created_at >= start_date,
            Review.created_at < end_date
        ).all()
        average_rating = sum(r.rating for r in all_reviews) / len(all_reviews) if all_reviews else 0
        
        # Get top performing homes
        top_homes_query = db.session.query(
            Home.id,
            Home.title,
            func.count(Booking.id).label('booking_count'),
            func.sum(Booking.total_price).label('total_revenue'),
            func.avg(Review.rating).label('avg_rating')
        ).select_from(Home)\
         .outerjoin(Booking, (Home.id == Booking.home_id) & (Booking.status.in_(['completed', 'confirmed'])) & 
                    (Booking.created_at >= start_date) & (Booking.created_at < end_date))\
         .outerjoin(Review, (Home.id == Review.home_id) & 
                    (Review.created_at >= start_date) & (Review.created_at < end_date))\
         .filter(Home.owner_id == current_user.id)\
         .group_by(Home.id, Home.title)\
         .order_by(func.sum(Booking.total_price).desc())\
         .limit(5).all()
        
        top_homes = []
        for home_data in top_homes_query:
            home_bookings = [b for b in completed_bookings if b.home_id == home_data.id]
            
            # Determine most common booking type for this home
            home_hourly = sum(1 for b in home_bookings if b.booking_type == 'hourly')
            home_nightly = len(home_bookings) - home_hourly
            home_common_type = "Theo giờ" if home_hourly >= home_nightly else "Theo ngày"
            
            # Calculate booking rate for this home
            home_total_hours = sum((b.end_time - b.start_time).total_seconds() / 3600 for b in home_bookings)
            home_booking_rate = min((home_total_hours / (24 * days_in_range)) * 100, 100) if home_total_hours > 0 and days_in_range > 0 else 0
            
            top_homes.append({
                'name': home_data.title,
                'type': home_common_type,
                'revenue': int(home_data.total_revenue or 0),
                'bookings': home_data.booking_count or 0,
                'booking_rate': f"{home_booking_rate:.0f}%",
                'rating': f"{home_data.avg_rating:.1f}" if home_data.avg_rating else "0.0"
            })
        
        return jsonify({
            'total_profit': f"{int(total_profit):,}đ",
            'total_hours': f"{int(total_hours):,} giờ",
            'total_bookings': f"{total_bookings} lần",
            'booking_rate': f"{booking_rate:.0f}%",
            'common_type': common_type,
            'average_rating': f"{average_rating:.1f}/5",
            'top_homes': top_homes
        })
        
    except Exception as e:
        print(f"Error getting custom stats data: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@owner_bp.route('/api/chart-data/custom')
@owner_required
def get_custom_chart_data_query():
    """API endpoint to get chart data for custom date range via query parameters"""
    try:
        start_date_str = request.args.get('start')
        end_date_str = request.args.get('end')
        
        if not start_date_str or not end_date_str:
            return jsonify({'error': 'Missing start or end date'}), 400
        
        # Parse dates
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)  # Include end date
        
        # Get all homes owned by current user
        owner_homes = Home.query.filter_by(owner_id=current_user.id).all()
        home_ids = [home.id for home in owner_homes]
        
        if not home_ids:
            return jsonify({'hourly': [], 'daily': []})
        
        # Get completed and confirmed bookings in date range
        completed_bookings = Booking.query.filter(
            Booking.home_id.in_(home_ids),
            Booking.status.in_(['completed', 'confirmed']),
            Booking.created_at >= start_date,
            Booking.created_at < end_date
        ).all()
        
        # Calculate date range
        date_diff = (end_date - start_date).days
        chart_data_hourly = []
        chart_data_nightly = []
        
        if date_diff <= 7:
            # Show daily data for short ranges
            current_date = start_date.date()
            end_date_only = end_date.date()
            
            while current_date < end_date_only:
                day_bookings = [b for b in completed_bookings if b.created_at.date() == current_date]
                
                # Separate hourly and nightly bookings
                hourly_bookings = [b for b in day_bookings if b.booking_type == 'hourly']
                nightly_bookings = [b for b in day_bookings if b.booking_type == 'daily']
                
                hourly_revenue = sum(b.total_price for b in hourly_bookings)
                nightly_revenue = sum(b.total_price for b in nightly_bookings)
                
                chart_data_hourly.append({
                    'date': current_date.strftime('%d/%m'),
                    'revenue': int(hourly_revenue)
                })
                
                chart_data_nightly.append({
                    'date': current_date.strftime('%d/%m'),
                    'revenue': int(nightly_revenue)
                })
                
                current_date += timedelta(days=1)
        
        else:
            # Show weekly data for longer ranges
            current_date = start_date.date()
            end_date_only = end_date.date()
            
            while current_date < end_date_only:
                week_end = min(current_date + timedelta(days=6), end_date_only - timedelta(days=1))
                
                week_bookings = [b for b in completed_bookings 
                               if current_date <= b.created_at.date() <= week_end]
                
                # Separate hourly and nightly bookings
                hourly_bookings = [b for b in week_bookings if b.booking_type == 'hourly']
                nightly_bookings = [b for b in week_bookings if b.booking_type == 'daily']
                
                hourly_revenue = sum(b.total_price for b in hourly_bookings)
                nightly_revenue = sum(b.total_price for b in nightly_bookings)
                
                week_label = f"{current_date.strftime('%d/%m')}-{week_end.strftime('%d/%m')}"
                
                chart_data_hourly.append({
                    'date': week_label,
                    'revenue': int(hourly_revenue)
                })
                
                chart_data_nightly.append({
                    'date': week_label,
                    'revenue': int(nightly_revenue)
                })
                
                current_date += timedelta(days=7)
        
        return jsonify({
            'hourly': chart_data_hourly,
            'daily': chart_data_nightly
        })
        
    except Exception as e:
        print(f"Error getting custom chart data: {e}")
        return jsonify({'hourly': [], 'daily': []}), 500

@owner_bp.route('/api/bookings')
@owner_required
def get_bookings_api():
    """API endpoint to get bookings data for the new tab interface"""
    try:
        # Get filter parameters
        status_filter = request.args.get('status', '')
        search_term = request.args.get('search', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Get all homes owned by current user
        owner_homes = Home.query.filter_by(owner_id=current_user.id).all()
        home_ids = [home.id for home in owner_homes]
        
        if not home_ids:
            return jsonify({
                'bookings': [],
                'pagination': {
                    'page': 1,
                    'per_page': per_page,
                    'total': 0,
                    'total_pages': 0,
                    'has_prev': False,
                    'has_next': False
                }
            })
        
        # Build query
        query = Booking.query.join(Home).join(Renter).filter(
            Booking.home_id.in_(home_ids)
        )
        
        # Apply status filter
        if status_filter:
            status_list = status_filter.split(',')
            if 'active' in status_list:
                # For "active" status, we need confirmed bookings that are currently ongoing
                status_list = [s for s in status_list if s != 'active']
                now = datetime.now()
                if status_list:
                    # Include other statuses plus active bookings
                    query = query.filter(
                        db.or_(
                            Booking.status.in_(status_list),
                            db.and_(
                                Booking.status == 'confirmed',
                                Booking.start_time <= now,
                                Booking.end_time >= now
                            )
                        )
                    )
                else:
                    # Only active bookings
                    query = query.filter(
                        db.and_(
                            Booking.status == 'confirmed',
                            Booking.start_time <= now,
                            Booking.end_time >= now
                        )
                    )
            else:
                query = query.filter(Booking.status.in_(status_list))
        
        # Apply search filter
        if search_term:
            query = query.filter(
                db.or_(
                    Home.title.ilike(f'%{search_term}%'),
                    Renter.full_name.ilike(f'%{search_term}%'),
                    Renter.username.ilike(f'%{search_term}%')
                )
            )
        
        # Order by creation date (newest first)
        query = query.order_by(Booking.created_at.desc())
        
        # Paginate
        paginated_bookings = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Format booking data
        bookings_data = []
        for booking in paginated_bookings.items:
            # Calculate duration
            if booking.booking_type == 'hourly':
                duration_hours = (booking.end_time - booking.start_time).total_seconds() / 3600
                duration = f"{int(duration_hours)} giờ"
            else:
                duration_days = (booking.end_time.date() - booking.start_time.date()).days + 1
                duration = f"{duration_days} ngày"
            
            # Determine actual status for display
            display_status = booking.status
            if booking.status == 'confirmed':
                # Check if booking is currently active
                now = datetime.now()
                if booking.start_time <= now <= booking.end_time:
                    display_status = 'active'
            
            bookings_data.append({
                'id': booking.id,
                'created_at': booking.created_at.isoformat(),
                'home_title': booking.home.title,
                'renter_name': booking.renter.full_name or booking.renter.username,
                'duration': duration,
                'total_price': booking.total_price,
                'status': display_status,
                'start_time': booking.start_time.isoformat(),
                'end_time': booking.end_time.isoformat(),
                'booking_type': booking.booking_type
            })
        
        return jsonify({
            'bookings': bookings_data,
            'pagination': {
                'page': paginated_bookings.page,
                'per_page': paginated_bookings.per_page,
                'total': paginated_bookings.total,
                'total_pages': paginated_bookings.pages,
                'has_prev': paginated_bookings.has_prev,
                'has_next': paginated_bookings.has_next,
                'prev_num': paginated_bookings.prev_num,
                'next_num': paginated_bookings.next_num
            }
        })
        
    except Exception as e:
        print(f"Error in get_bookings_api: {e}")
        return jsonify({'error': 'Internal server error'}), 500

