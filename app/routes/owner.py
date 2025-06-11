# routes/owner.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models.models import db, Room, Booking, RoomImage, Renter, Admin, Owner, Province, District, Ward, Rule, Amenity, RoomDeletionLog
import os
import shutil
from datetime import datetime, timedelta
from PIL import Image
import io
import os
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload


owner_bp = Blueprint('owner', __name__, url_prefix='/owner')

def get_location_names(room_data):
    """Lấy tên đầy đủ của địa chỉ từ database thay vì hard code"""
    try:
        result = {
            'province_name': 'Chưa chọn',
            'district_name': 'Chưa chọn', 
            'ward_name': 'Chưa chọn'
        }
        
        if room_data.get('province'):
            province = Province.query.filter_by(code=room_data['province']).first()
            if province:
                result['province_name'] = province.name
                
                if room_data.get('district'):
                    district = District.query.filter_by(code=room_data['district'], province_id=province.id).first()
                    if district:
                        result['district_name'] = district.name
                        
                        if room_data.get('ward'):
                            # Ward có thể là tên đầy đủ hoặc code
                            ward = Ward.query.filter(
                                Ward.district_id == district.id,
                                (Ward.name == room_data['ward']) | (Ward.code == room_data['ward'])
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

def get_rules_and_amenities(room_data):
    """Lấy thông tin rules và amenities từ database"""
    try:
        result = {
            'rules': [],
            'amenities': []
        }
        
        # Lấy rules nếu có
        if room_data.get('rules'):
            rule_ids = [int(id) for id in room_data['rules'] if id.isdigit()]
            if rule_ids:
                rules = Rule.query.filter(Rule.id.in_(rule_ids)).all()
                result['rules'] = [rule.to_dict() for rule in rules]
        
        # Lấy amenities nếu có
        if room_data.get('amenities'):
            amenity_ids = [int(id) for id in room_data['amenities'] if id.isdigit()]
            if amenity_ids:
                amenities = Amenity.query.filter(Amenity.id.in_(amenity_ids)).all()
                result['amenities'] = [amenity.to_dict() for amenity in amenities]
        
        print(f"✅ Rules & Amenities lookup: {len(result['rules'])} rules, {len(result['amenities'])} amenities")
        return result
        
    except Exception as e:
        print(f"❌ Error in get_rules_and_amenities: {e}")
        return {'rules': [], 'amenities': []}

def allowed_file(filename):
    """Check if the file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_property_type_en(vn_value):
    """Chuyển đổi property type từ tiếng Việt sang English"""
    vn_to_en_map = {
        'Nhà': 'house',
        'Căn hộ': 'apartment', 
        'Khách sạn': 'hotel'
    }
    return vn_to_en_map.get(vn_value, 'house')  # Default là house

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
    # Lấy tất cả phòng của owner hiện tại với relationship images
    rooms = Room.query.options(joinedload(Room.images)).filter_by(owner_id=current_user.id).all()
    
    return render_template('owner/dashboard.html', rooms=rooms)


@owner_bp.route('/manage-rooms')
@owner_required
def manage_rooms():
    rooms = Room.query.filter_by(owner_id=current_user.id).all()
    return render_template('owner/manage_rooms.html', rooms=rooms)


@owner_bp.route('/add-room', methods=['GET', 'POST'])
@login_required
def add_room():
    if request.method == 'POST':
        try:
            # Lưu dữ liệu vào session để preview
            room_data = {
                'room_title': request.form.get('room_title'),
                'room_description': request.form.get('room_description'),
                'property_type': request.form.get('property_type'),
                'province': request.form.get('province'),
                'district': request.form.get('district'),
                'ward': request.form.get('ward'),
                'street': request.form.get('street'),
                'bathroom_count': int(request.form.get('bathroom_count', 2)),
                'bed_count': int(request.form.get('bed_count', 1)),
                'guest_count': int(request.form.get('guest_count', 1)),
                'selected_rental_type': request.form.get('selected_rental_type'),
                'hourly_price': request.form.get('hourly_price'),
                'nightly_price': request.form.get('nightly_price'),
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
            
            # Xử lý các ảnh khác
            for key in request.files:
                if key.startswith('images'):
                    files = request.files.getlist(key)
                    for file in files:
                        if file and file.filename:
                            filename = secure_filename(file.filename)
                            timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]  # microseconds to milliseconds
                            filename = f"temp_{timestamp}_{filename}"
                            save_path = os.path.join(temp_folder, filename)
                            file.save(save_path)
                            image_paths.append(f"/static/temp/{filename}")
            
            # Thêm đường dẫn ảnh vào room_data
            room_data['main_image'] = main_image_path
            room_data['images'] = image_paths
            
            session['room_preview_data'] = room_data
            print(f"DEBUG: Saving room_data to session with keys: {list(room_data.keys())}")
            print(f"DEBUG: Main image: {main_image_path}")
            print(f"DEBUG: Images: {image_paths}")
            return redirect(url_for('owner.room_preview'))
            
        except Exception as e:
            flash(f'Có lỗi xảy ra: {str(e)}', 'danger')
    
    # Lấy dữ liệu từ session nếu có (khi quay lại từ preview)
    room_data = session.get('room_preview_data', {})
    print(f"DEBUG: Loading add_room with room_data keys: {list(room_data.keys()) if room_data else 'None'}")
    
    # Nếu có rules/amenities trong session, chuẩn bị data cho JavaScript
    if room_data.get('rules') or room_data.get('amenities'):
        print(f"DEBUG: Found saved rules: {room_data.get('rules', [])}")
        print(f"DEBUG: Found saved amenities: {room_data.get('amenities', [])}")
    
    return render_template('owner/add_room.html', room_data=room_data)

@owner_bp.route('/room-preview')
@login_required
def room_preview():
    # Lấy dữ liệu từ session
    room_data = session.get('room_preview_data')
    if not room_data:
        flash('Không tìm thấy dữ liệu phòng để xem trước.', 'warning')
        return redirect(url_for('owner.add_room'))
    
    # Lookup tên đầy đủ từ database
    location_names = get_location_names(room_data)
    
    # Lấy rules và amenities từ database
    rules_amenities = get_rules_and_amenities(room_data)
    
    # Debug log - kiểm tra data trong session
    print(f"DEBUG room_data keys: {list(room_data.keys())}")
    print(f"DEBUG room_data rules: {room_data.get('rules', 'No rules')}")
    print(f"DEBUG room_data amenities: {room_data.get('amenities', 'No amenities')}")
    print(f"DEBUG lookup results: {rules_amenities}")
    
    # Chỉ hiển thị khi thực sự có data được chọn
    
    # Merge rules và amenities vào room_data
    room_data.update(rules_amenities)
    
    return render_template('owner/room_preview.html', room_data=room_data, location_names=location_names)

@owner_bp.route('/back-to-edit')
@login_required
def back_to_edit():
    # Dữ liệu đã được lưu trong session từ lúc tạo preview
    # Chỉ cần redirect về add_room, dữ liệu sẽ được load tự động
    return redirect(url_for('owner.add_room'))

@owner_bp.route('/clear-room-data')
@login_required
def clear_room_data():
    # Xóa dữ liệu tạm thời khỏi session khi owner thoát khỏi giao diện tạo phòng
    session.pop('room_preview_data', None)
    flash('Đã hủy quá trình tạo phòng.', 'info')
    return redirect(url_for('owner.dashboard'))

@owner_bp.route('/clear-room-session', methods=['POST'])
@login_required
def clear_room_session():
    # API endpoint để xóa session data qua AJAX
    session.pop('room_preview_data', None)
    print("DEBUG: Cleared room_preview_data from session")
    return jsonify({'status': 'success'})

@owner_bp.route('/confirm-room', methods=['POST'])
@login_required
def confirm_room():
    # Lấy dữ liệu từ session
    room_data = session.get('room_preview_data')
    if not room_data:
        flash('Không tìm thấy dữ liệu phòng để tạo.', 'warning')
        return redirect(url_for('owner.add_room'))
    
    try:
        # Xử lý giá dựa theo rental type được chọn
        price_per_hour = None
        price_per_night = None
        
        if room_data['selected_rental_type'] == 'hourly':
            price_per_hour = float(room_data['hourly_price']) / 1000 if room_data['hourly_price'] else 0.0
        elif room_data['selected_rental_type'] == 'nightly':
            price_per_night = float(room_data['nightly_price']) / 1000 if room_data['nightly_price'] else 0.0
        
        # Map property_type từ English sang Vietnamese
        property_type_map = {
            'house': 'Nhà',
            'apartment': 'Căn hộ', 
            'hotel': 'Khách sạn'
        }
        property_type_vn = property_type_map.get(room_data.get('property_type'), 'Mô hình chuẩn')
        
        # Tạo room mới
        new_room = Room(
            title=room_data['room_title'],
            room_type=property_type_vn,  # Lưu giá trị tiếng Việt
            address=f"{room_data['street']}, {room_data['ward']}" if room_data['street'] and room_data['ward'] else "Chưa cập nhật",
            city=room_data['province'] if room_data['province'] else "Chưa cập nhật",
            district=room_data['district'] if room_data['district'] else "Chưa cập nhật",
            room_number=room_data['room_title'],  # Sử dụng title làm room number
            bed_count=room_data['bed_count'],
            bathroom_count=room_data['bathroom_count'],
            max_guests=room_data['guest_count'],
            price_per_hour=price_per_hour,
            price_per_night=price_per_night,
            description=room_data['room_description'],
            floor_number=1,  # Mặc định
            owner_id=current_user.id
        )
        
        db.session.add(new_room)
        db.session.commit()
        
        # Xử lý amenities và rules
        try:
            # Lưu amenities (amenities trong session là array của ID strings)
            if room_data.get('amenities'):
                amenity_ids = [int(amenity_id) for amenity_id in room_data['amenities']]
                amenities = Amenity.query.filter(Amenity.id.in_(amenity_ids)).all()
                new_room.amenities.extend(amenities)
                print(f"DEBUG: Added {len(amenities)} amenities to room: {[a.name for a in amenities]}")
            
            # Lưu rules (rules trong session là array của ID strings)
            if room_data.get('rules'):
                rule_ids = [int(rule_id) for rule_id in room_data['rules']]
                rules = Rule.query.filter(Rule.id.in_(rule_ids)).all()
                new_room.rules.extend(rules)
                print(f"DEBUG: Added {len(rules)} rules to room: {[r.name for r in rules]}")
            
            db.session.commit()
            print("DEBUG: Successfully saved amenities and rules")
            
        except Exception as e:
            print(f"Lỗi khi lưu amenities/rules: {str(e)}")
            # Không làm fail việc tạo phòng nếu có lỗi
            pass
        
        # Xử lý ảnh từ temp sang uploads
        try:
            # Tạo folder riêng cho phòng này
            room_folder = os.path.join('static', 'uploads', f'room_{new_room.id}')
            os.makedirs(room_folder, exist_ok=True)
            print(f"DEBUG: Created room folder: {room_folder}")
            print(f"DEBUG: Room data images: {room_data.get('images', [])}")
            print(f"DEBUG: Room data main_image: {room_data.get('main_image')}")
            
            # Xử lý ảnh chính (main_image)
            if room_data.get('main_image'):
                main_image_path = room_data['main_image']
                if main_image_path.startswith('/static/temp/'):
                    # Đường dẫn đầy đủ đến file temp (bao gồm 'static/')
                    temp_file = main_image_path[1:]  # Bỏ '/' đầu để có đường dẫn tương đối
                    print(f"DEBUG: Processing main image - original path: {main_image_path}")
                    print(f"DEBUG: Processing main image - temp_file: {temp_file}")
                    print(f"DEBUG: Main image file exists: {os.path.exists(temp_file)}")
                    
                    if os.path.exists(temp_file):
                        # Tạo tên file mới (đơn giản hơn vì đã có folder riêng)
                        original_name = os.path.basename(temp_file).replace('temp_main_', '', 1)
                        # Loại bỏ timestamp cũ từ tên file nếu có
                        if '_' in original_name:
                            parts = original_name.split('_', 1)
                            if len(parts) > 1:
                                original_name = parts[1]
                        new_filename = f"main_{original_name}"
                        
                        # Copy từ temp sang room folder
                        new_path = os.path.join(room_folder, new_filename)
                        print(f"DEBUG: Copying main image from {temp_file} to {new_path}")
                        shutil.copy2(temp_file, new_path)
                        print(f"DEBUG: Main image copied successfully")
                        
                        # Tạo record trong database
                        main_img = RoomImage(
                            image_path=f"uploads/room_{new_room.id}/{new_filename}",
                            room_id=new_room.id,
                            is_featured=True
                        )
                        db.session.add(main_img)
                        print(f"DEBUG: Created main image record in DB: {main_img.image_path}")
                        
                        # Xóa file temp
                        os.remove(temp_file)
                        print(f"DEBUG: Removed temp file: {temp_file}")
            
            # Xử lý các ảnh khác
            if room_data.get('images'):
                for i, image_path in enumerate(room_data['images']):
                    if image_path.startswith('/static/temp/'):
                        # Đường dẫn đầy đủ đến file temp (bao gồm 'static/')
                        temp_file = image_path[1:]  # Bỏ '/' đầu để có đường dẫn tương đối
                        print(f"DEBUG: Processing image {i+1} - original path: {image_path}")
                        print(f"DEBUG: Processing image {i+1} - temp_file: {temp_file}")
                        print(f"DEBUG: Image {i+1} file exists: {os.path.exists(temp_file)}")
                        
                        if os.path.exists(temp_file):
                            # Tạo tên file mới (đơn giản hơn)
                            original_name = os.path.basename(temp_file).replace('temp_', '', 1)
                            # Loại bỏ timestamp cũ từ tên file nếu có
                            if '_' in original_name:
                                parts = original_name.split('_', 1)
                                if len(parts) > 1:
                                    original_name = parts[1]
                            new_filename = f"image_{i+1}_{original_name}"
                            
                            # Copy từ temp sang room folder
                            new_path = os.path.join(room_folder, new_filename)
                            print(f"DEBUG: Copying image {i+1} from {temp_file} to {new_path}")
                            shutil.copy2(temp_file, new_path)
                            
                            # Tạo record trong database
                            img = RoomImage(
                                image_path=f"uploads/room_{new_room.id}/{new_filename}",
                                room_id=new_room.id,
                                is_featured=False
                            )
                            db.session.add(img)
                            print(f"DEBUG: Created image {i+1} record in DB: {img.image_path}")
                            
                            # Xóa file temp
                            os.remove(temp_file)
                            print(f"DEBUG: Removed temp file: {temp_file}")
            
            db.session.commit()
            
        except Exception as e:
            print(f"Lỗi khi xử lý ảnh: {str(e)}")
            # Không làm fail việc tạo phòng nếu ảnh có lỗi
            pass
        
        # Xóa dữ liệu preview khỏi session
        session.pop('room_preview_data', None)
        
        flash('Đã tạo phòng thành công!', 'success')
        return redirect(url_for('owner.dashboard', created='success'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Có lỗi xảy ra khi tạo phòng: {str(e)}', 'danger')
        return redirect(url_for('owner.room_preview'))

@owner_bp.route('/edit-room/<int:room_id>', methods=['GET', 'POST'])
@login_required
def edit_room(room_id):
    room = Room.query.options(joinedload(Room.images)).get_or_404(room_id)
    if room.owner_id != current_user.id:
        flash('Bạn không có quyền chỉnh sửa phòng này!', 'danger')
        return redirect(url_for('owner.dashboard'))
    
    if request.method == 'POST':
        try:
            # Cập nhật thông tin cơ bản
            room.title = request.form.get('room_title')
            room.description = request.form.get('room_description')
            
            # Chuyển đổi property_type sang tiếng Việt trước khi lưu
            property_type_map = {
                'house': 'Nhà',
                'apartment': 'Căn hộ', 
                'hotel': 'Khách sạn'
            }
            property_type_vn = property_type_map.get(request.form.get('property_type'), request.form.get('property_type'))
            room.room_type = property_type_vn
            room.city = request.form.get('province')  # Sử dụng city thay vì province
            room.district = request.form.get('district')
            
            # Gộp ward và street thành address đầy đủ
            street = request.form.get('street', '').strip()
            ward = request.form.get('ward', '').strip()
            
            if street and ward:
                room.address = f"{street}, {ward}"
            elif street:
                room.address = street
            elif ward:
                room.address = ward
            else:
                room.address = "Chưa cập nhật"
            
            # Cập nhật sức chứa
            room.bathroom_count = int(request.form.get('bathroom_count', 1))
            room.bed_count = int(request.form.get('bed_count', 1))
            room.max_guests = int(request.form.get('guest_count', 1))  # Sử dụng max_guests thay vì guest_count
            
            # Cập nhật hình thức cho thuê và giá
            rental_type = request.form.get('rental_type')
            # Bỏ rental_type vì Room model không có rental_type
            
            # Cập nhật giá theo hình thức cho thuê
            if rental_type == 'hourly':
                hourly_price = request.form.get('hourly_price')
                if hourly_price:
                    # Loại bỏ định dạng, chuyển thành số và chia cho 1000 để cân bằng với display_price logic
                    price_value = int(hourly_price.replace(',', '').replace('.', ''))
                    room.price_per_hour = price_value / 1000
                room.price_per_night = None
            elif rental_type == 'nightly':
                nightly_price = request.form.get('nightly_price')
                if nightly_price:
                    # Loại bỏ định dạng, chuyển thành số và chia cho 1000 để cân bằng với display_price logic
                    price_value = int(nightly_price.replace(',', '').replace('.', ''))
                    room.price_per_night = price_value / 1000
                # Giữ price_per_hour để tương thích với logic hiện tại
                if not room.price_per_hour:
                    room.price_per_hour = 0
            
            # Cập nhật rules
            room.rules.clear()
            rule_ids = request.form.getlist('rules[]')
            if rule_ids:
                rules = Rule.query.filter(Rule.id.in_(rule_ids)).all()
                room.rules.extend(rules)
            
            # Cập nhật amenities
            room.amenities.clear()
            amenity_ids = request.form.getlist('amenities[]')
            if amenity_ids:
                amenities = Amenity.query.filter(Amenity.id.in_(amenity_ids)).all()
                room.amenities.extend(amenities)
            
            # Xử lý ảnh mới nếu có
            # Tạo thư mục upload cho room nếu chưa có
            room_folder = os.path.join('static', 'uploads', f'room_{room_id}')
            os.makedirs(room_folder, exist_ok=True)
            
            # Xử lý ảnh bìa mới
            if 'main_image' in request.files:
                main_image = request.files['main_image']
                if main_image and main_image.filename and allowed_file(main_image.filename):
                    # Xóa ảnh bìa cũ
                    old_main_image = RoomImage.query.filter_by(room_id=room_id, is_featured=True).first()
                    if old_main_image:
                        old_path = os.path.join('static', old_main_image.image_path)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                        db.session.delete(old_main_image)
                    
                    # Lưu ảnh bìa mới
                    filename = secure_filename(main_image.filename)
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    filename = f"main_{timestamp}_{filename}"
                    save_path = os.path.join(room_folder, filename)
                    main_image.save(save_path)
                    
                    new_main_image = RoomImage(
                        image_path=f"uploads/room_{room_id}/{filename}",
                        room_id=room_id,
                        is_featured=True
                    )
                    db.session.add(new_main_image)
            
            # Xử lý ảnh phụ mới
            for key in request.files:
                if key.startswith('images'):
                    files = request.files.getlist(key)
                    for file in files:
                        if file and file.filename and allowed_file(file.filename):
                            filename = secure_filename(file.filename)
                            timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]
                            filename = f"{timestamp}_{filename}"
                            save_path = os.path.join(room_folder, filename)
                            file.save(save_path)
                            
                            new_image = RoomImage(
                                image_path=f"uploads/room_{room_id}/{filename}",
                                room_id=room_id,
                                is_featured=False
                            )
                            db.session.add(new_image)
            
            db.session.commit()
            flash('Đã cập nhật thông tin phòng thành công!', 'success')
            return redirect(url_for('owner.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra khi cập nhật: {str(e)}', 'danger')
    
    # Chuẩn bị dữ liệu cho template
    # Tách địa chỉ để hiển thị đúng phường và số nhà
    street_address = ''
    ward_name = ''
    
    if room.address:
        # Tách địa chỉ nếu có phường
        address_parts = room.address.split(', ')
        if len(address_parts) >= 2:
            # Nếu có nhiều phần, phần cuối có thể là phường
            for i, part in enumerate(address_parts):
                if 'phường' in part.lower() or 'xã' in part.lower():
                    ward_name = part.strip()
                    # Phần còn lại là địa chỉ số nhà
                    street_address = ', '.join(address_parts[:i] + address_parts[i+1:]).strip()
                    break
            else:
                # Nếu không tìm thấy phường, coi toàn bộ là địa chỉ số nhà
                street_address = room.address
        else:
            street_address = room.address
    
    room_data = {
        'id': room.id,
        'title': room.title,
        'description': room.description,
        'property_type': get_property_type_en(room.room_type),  # Chuyển đổi ngược từ tiếng Việt sang English cho form
        'province': room.city,  # Sử dụng city thay vì province
        'district': room.district,
        'ward': ward_name,  # Phường được tách từ address
        'street': street_address,  # Số nhà được tách từ address
        'bathroom_count': room.bathroom_count,
        'bed_count': room.bed_count,
        'guest_count': room.max_guests,  # Sử dụng max_guests thay vì guest_count
        'rental_type': 'nightly' if room.price_per_night and room.price_per_night > 0 else 'hourly',
        'hourly_price': int(room.price_per_hour * 1000) if room.price_per_hour else 0,
        'nightly_price': int(room.price_per_night * 1000) if room.price_per_night else None,
        'rules': [{'id': rule.id, 'name': rule.name} for rule in room.rules],
        'amenities': [{'id': amenity.id, 'name': amenity.name, 'icon': amenity.icon} for amenity in room.amenities],
        'images': [{'id': img.id, 'path': img.image_path, 'is_featured': img.is_featured} for img in room.images]
    }
    
    return render_template('owner/edit_room.html', room=room_data)

@owner_bp.route('/delete-room/<int:room_id>', methods=['POST'])
@login_required
def delete_room(room_id):
    room = Room.query.get_or_404(room_id)
    if room.owner_id != current_user.id:
        flash('Bạn không có quyền xóa phòng này!', 'danger')
        return redirect(url_for('owner.dashboard'))
    
    # Lấy lý do xóa từ form
    delete_reason = request.form.get('delete_reason', '').strip()
    
    # Validate lý do xóa
    if not delete_reason or len(delete_reason) < 10:
        flash('Lý do xóa phòng phải có ít nhất 10 ký tự!', 'danger')
        return redirect(url_for('owner.dashboard'))
    
    try:
        # Lưu log xóa phòng (tùy chọn - có thể tạo bảng RoomDeletionLog)
        room_title = room.title
        owner_name = current_user.full_name or current_user.username
        
        # Xóa folder ảnh của phòng
        room_folder = os.path.join('static', 'uploads', f'room_{room_id}')
        if os.path.exists(room_folder):
            try:
                shutil.rmtree(room_folder)
                print(f"Đã xóa folder ảnh: {room_folder}")
            except Exception as e:
                print(f"Không thể xóa folder ảnh: {e}")
                # Fallback: xóa từng file
                for image in room.images:
                    if image.image_path:
                        file_path = os.path.join('static', image.image_path)
                        if os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                            except Exception as e:
                                print(f"Không thể xóa file ảnh: {e}")
        
        # Lưu log vào database
        deletion_log = RoomDeletionLog(
            room_id=room_id,
            room_title=room_title,
            owner_id=current_user.id,
            owner_name=owner_name,
            delete_reason=delete_reason,
            room_address=f"{room.address}, {room.district}, {room.city}",
            room_price=room.price_per_hour or room.price_per_night
        )
        db.session.add(deletion_log)
        
        # Ghi log ra console
        log_message = f"[{datetime.now()}] Owner '{owner_name}' (ID: {current_user.id}) đã xóa phòng '{room_title}' (ID: {room_id}). Lý do: {delete_reason}"
        print(log_message)
        
        # Xóa phòng (cascade sẽ tự động xóa các record liên quan)
        db.session.delete(room)
        db.session.commit()
        
        flash(f'Đã xóa phòng "{room_title}" thành công!', 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi khi xóa phòng: {str(e)}")
        flash('Có lỗi xảy ra khi xóa phòng. Vui lòng thử lại!', 'danger')
    
    return redirect(url_for('owner.dashboard'))


@owner_bp.route('/view-bookings')
@owner_bp.route('/view-bookings/<status>')
@owner_required
def view_bookings(status=None):
    # Get all rooms owned by current user
    rooms = Room.query.filter_by(owner_id=current_user.id).all()
    
    # Get all bookings for these rooms
    all_bookings = []
    for room in rooms:
        all_bookings.extend(room.bookings)
    
    # Filter bookings by status if specified
    if status:
        all_bookings = [b for b in all_bookings if b.status == status]
    
    # Sort bookings by created_at date, newest first
    all_bookings.sort(key=lambda x: x.created_at, reverse=True)
    
    return render_template('owner/view_bookings.html', 
                          bookings=all_bookings, 
                          current_status=status)


@owner_bp.route('/room/<int:room_id>/add-images', methods=['GET', 'POST'])
@owner_required
def add_room_images(room_id):
    room = Room.query.get_or_404(room_id)
    
    # Kiểm tra quyền sở hữu
    if room.owner_id != current_user.id:
        flash('Bạn không có quyền thêm ảnh cho phòng này.', 'danger')
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
                    
                    # Create a filename
                    filename = secure_filename(img_file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    
                    # Save path
                    upload_folder = os.path.join('static', 'uploads')
                    os.makedirs(upload_folder, exist_ok=True)
                    save_path = os.path.join(upload_folder, filename)
                    
                    # Save the processed image
                    img.save(save_path, quality=85, optimize=True)
                    
                    # Create database record
                    is_featured = not RoomImage.query.filter_by(room_id=room.id, is_featured=True).first()
                    
                    new_img = RoomImage(
                        image_path=f"uploads/{filename}",
                        room_id=room.id,
                        is_featured=is_featured
                    )
                    db.session.add(new_img)
                    
                except Exception as e:
                    # Log the error but continue processing other images
                    print(f"Error processing image: {e}")
                    continue
                    
        db.session.commit()
        flash("Ảnh đã được thêm thành công vào thư viện phòng!", "success")
        return redirect(url_for('owner.add_room_images', room_id=room.id))
    
    # Get existing images for this room
    existing_images = RoomImage.query.filter_by(room_id=room.id).all()
    
    return render_template('owner/add_room_images.html', room=room, existing_images=existing_images)

@owner_bp.route('/set-featured-image/<int:image_id>', methods=['GET'])
@login_required
def set_featured_image(image_id):
    # Lấy thông tin ảnh
    image = RoomImage.query.get_or_404(image_id)
    room = image.room

    # Kiểm tra quyền sở hữu
    if room.owner_id != current_user.id:
        flash("Bạn không có quyền thực hiện thao tác này.", "danger")
        return redirect(url_for('owner.dashboard'))

    # Bỏ featured của tất cả ảnh khác trong phòng
    RoomImage.query.filter_by(room_id=room.id).update({RoomImage.is_featured: False})
    
    # Đặt ảnh được chọn làm featured
    image.is_featured = True
    db.session.commit()

    flash("Đã đặt ảnh làm ảnh đại diện thành công!", "success")
    return redirect(url_for('owner.add_room_images', room_id=room.id))

@owner_bp.route('/room-image/<int:image_id>/delete', methods=['GET', 'POST'])
@owner_required
def delete_room_image(image_id):
    image = RoomImage.query.get_or_404(image_id)
    room_id = image.room_id
    
    # Lấy thông tin phòng để kiểm tra quyền sở hữu
    room = Room.query.get_or_404(room_id)
    
    # Kiểm tra quyền sở hữu
    if room.owner_id != current_user.id:
        flash('Bạn không có quyền xóa ảnh của phòng này.', 'danger')
        return redirect(url_for('owner.dashboard'))
    
    # Delete the image file
    if image.image_path:
        file_path = os.path.join('static', image.image_path)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    # Check if this was the featured image
    was_featured = image.is_featured
    
    # Delete the database record
    db.session.delete(image)
    db.session.commit()
    
    # If we deleted the featured image, set a new one if available
    if was_featured:
        next_image = RoomImage.query.filter_by(room_id=room_id).first()
        if next_image:
            next_image.is_featured = True
            db.session.commit()
    
    flash('Đã xóa ảnh thành công!', 'success')
    
    # Check if the request came from edit_room page
    referer = request.headers.get('Referer', '')
    if '/edit-room/' in referer:
        return redirect(url_for('owner.edit_room', room_id=room_id))
    else:
        return redirect(url_for('owner.add_room_images', room_id=room_id))


@owner_bp.route('/room-detail/<int:room_id>')
@login_required
def room_detail(room_id):
    """Redirect to edit room - no separate detail page needed"""
    room = Room.query.get_or_404(room_id)
    if room.owner_id != current_user.id:
        flash('Bạn không có quyền xem phòng này!', 'danger')
        return redirect(url_for('owner.dashboard'))
    
    # Redirect to edit page to view/edit details
    return redirect(url_for('owner.edit_room', room_id=room_id))

@owner_bp.route('/booking/confirm/<int:id>')
@owner_required
def confirm_booking(id):
    booking = Booking.query.get_or_404(id)
    
    # Make sure the owner owns this booking's homestay
    if booking.homestay.owner_id != current_user.id:
        flash('You do not have permission to manage this booking.', 'danger')
        return redirect(url_for('owner.view_bookings'))
    
    # Get all other pending bookings for the same room with overlapping time
    overlapping_pending_bookings = Booking.query.filter(
        Booking.room_id == booking.room_id,
        Booking.id != booking.id,
        Booking.status == 'pending',
        Booking.start_time < booking.end_time,
        Booking.end_time > booking.start_time
    ).all()
    
    # Reject all other overlapping pending bookings
    for other_booking in overlapping_pending_bookings:
        other_booking.status = 'rejected'
        # You could also set a rejection reason here
        other_booking.rejection_reason = "Room was booked by another guest for the same time period."
    
    # Set status to confirmed
    booking.status = 'confirmed'
    
    # Add notification (you can expand this into a proper notification system)
    booking.notification_for_renter = 'Your booking has been confirmed! Please proceed with payment.'
    booking.notification_date = datetime.now()
    
    db.session.commit()
    
    flash('Booking #' + str(booking.id) + ' has been confirmed! Renter will be prompted for payment.', 'success')
    return redirect(url_for('owner.booking_details', booking_id=id))

@owner_bp.route('/reject-booking/<int:id>')
@owner_required
def reject_booking(id):
    booking = Booking.query.get_or_404(id)
    
    # Ensure this booking belongs to one of the current owner's homestays
    if booking.homestay.owner_id != current_user.id:
        flash('Bạn không có quyền từ chối đặt phòng này.', 'danger')
        return redirect(url_for('owner.dashboard'))

    # Update the booking status
    booking.status = 'rejected'
    
    # Add notification with suggestion to book another room/homestay
    booking.notification_for_renter = 'Yêu cầu đặt phòng của bạn đã bị từ chối. Vui lòng tìm kiếm và đặt phòng khác phù hợp với nhu cầu của bạn.'
    booking.notification_date = datetime.now()
    
    db.session.commit()
    
    flash('Đã từ chối đặt phòng.', 'warning')
    return redirect(url_for('owner.view_bookings'))

# @owner_bp.route('/mark-completed/<int:id>')
# @owner_required
# def mark_completed(id):
#     booking = Booking.query.get_or_404(id)
    
#     # Ensure this booking belongs to one of the current owner's homestays
#     if booking.homestay.owner_id != current_user.id:
#         flash('You do not have permission to update this booking.', 'danger')
#         return redirect(url_for('owner.view_bookings'))

#     # Update the booking status
#     booking.status = 'completed'
#     db.session.commit()

#     flash('Booking marked as completed.', 'success')
#     return redirect(url_for('owner.view_bookings'))

@owner_bp.route('/booking-details/<int:booking_id>')
@owner_required
def booking_details(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Ensure this booking belongs to one of the current owner's homestays
    if booking.homestay.owner_id != current_user.id:
        flash('Bạn không có quyền xem thông tin đặt phòng này.', 'danger')
        return redirect(url_for('owner.dashboard'))

    return render_template('owner/booking_details.html', booking=booking)

@owner_bp.route('/settings')
@login_required
def settings():
    return render_template('owner/settings.html')

@owner_bp.route('/profile', methods=['GET', 'POST'])
@owner_required
def profile():
    if request.method == 'POST':
        try:
            # Cập nhật thông tin cơ bản
            current_user.username = request.form.get('username')
            current_user.first_name = request.form.get('first_name')
            current_user.last_name = request.form.get('last_name')
            current_user.gender = request.form.get('gender')
            current_user.email = request.form.get('email')
            current_user.phone = request.form.get('phone')
            current_user.address = request.form.get('address')
            
            # Xử lý ngày sinh
            birth_day = request.form.get('birth_day')
            birth_month = request.form.get('birth_month')
            birth_year = request.form.get('birth_year')
            
            if birth_day and birth_month and birth_year:
                try:
                    current_user.birth_date = datetime(int(birth_year), int(birth_month), int(birth_day)).date()
                except ValueError:
                    pass  # Ignore invalid date
            
            # Xử lý upload avatar
            avatar_file = request.files.get('avatar')
            if avatar_file and avatar_file.filename and allowed_file(avatar_file.filename):
                # Tạo tên file unique
                filename = secure_filename(avatar_file.filename)
                timestamp = str(int(datetime.now().timestamp()))
                filename = f"avatar_{current_user.id}_{timestamp}_{filename}"
                
                # Đảm bảo upload folder tồn tại
                upload_folder = current_app.config.get('UPLOAD_FOLDER')
                if not upload_folder:
                    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
                    current_app.config['UPLOAD_FOLDER'] = upload_folder
                
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                
                # Lưu file
                upload_path = os.path.join(upload_folder, filename)
                avatar_file.save(upload_path)
                
                # Resize image  
                try:
                    from PIL import Image
                    with Image.open(upload_path) as img:
                        img = img.resize((200, 200), Image.Resampling.LANCZOS)
                        img.save(upload_path, optimize=True, quality=85)
                except Exception as e:
                    print(f"Error resizing image: {e}")
                
                # Xóa avatar cũ nếu có
                if current_user.avatar:
                    old_avatar_path = os.path.join(upload_folder, current_user.avatar)
                    if os.path.exists(old_avatar_path):
                        try:
                            os.remove(old_avatar_path)
                        except Exception as e:
                            print(f"Error removing old avatar: {e}")
                
                current_user.avatar = filename
            
            db.session.commit()
            flash('Cập nhật thông tin thành công!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'danger')
        
        return redirect(url_for('owner.profile'))
            
    return render_template('owner/profile.html')

@owner_bp.route('/book-room/<int:room_id>', methods=['GET', 'POST'])
@owner_required
def book_room(room_id):
    room = Room.query.get_or_404(room_id)
    
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        start_time = request.form.get('start_time')
        duration_str = request.form.get('duration')
        
        if not start_date or not start_time or not duration_str:
            flash("You must select date, time and duration.", "warning")
            return redirect(url_for('renter.book_room', room_id=room.id))
        
        try:
            duration = int(duration_str)
        except ValueError:
            flash("Invalid duration value.", "danger")
            return redirect(url_for('renter.book_room', room_id=room.id))
        
        if duration < 1:
            flash("Minimum duration is 1 night.", "warning")
            return redirect(url_for('renter.book_room', room_id=room.id))
        
        start_str = f"{start_date} {start_time}"
        try:
            start_datetime = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
        except ValueError:
            flash("Invalid date or time format.", "danger")
            return redirect(url_for('renter.book_room', room_id=room.id))
        
        end_datetime = start_datetime + timedelta(days=duration)
        # Calculate total price using the room's price per night
        total_price = room.price_per_night * duration
        
        # Check for overlapping bookings for this room
        existing_bookings = Booking.query.filter_by(room_id=room.id).all()
        for booking in existing_bookings:
            if start_datetime < booking.end_time and end_datetime > booking.start_time:
                flash('This room is not available during the selected time period.', 'danger')
                return redirect(url_for('renter.book_room', room_id=room.id))
        
        new_booking = Booking(
            room_id=room.id,
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
        return redirect(url_for('renter.dashboard'))

    return render_template('owner/book_room.html', room=room)

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

@owner_bp.route('/toggle-room-status/<int:room_id>', methods=['POST'])
@login_required
def toggle_room_status(room_id):
    room = Room.query.get_or_404(room_id)
    if room.owner_id != current_user.id:
        flash('Bạn không có quyền thay đổi trạng thái phòng này!', 'danger')
        return redirect(url_for('owner.dashboard'))
    
    room.is_available = not room.is_available
    db.session.commit()
    
    status = 'mở khóa' if room.is_available else 'khóa'
    flash(f'Đã {status} phòng thành công!', 'success')
    return redirect(url_for('owner.dashboard'))