from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from models import db, Admin, Owner, Renter, Room, Booking, Statistics, Review
from sqlalchemy.exc import IntegrityError
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from functools import wraps
import uuid
import json
import random
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def allowed_file(filename):
    """Check if the file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not isinstance(current_user, Admin):
        flash("You are not authorized!", "danger")
        return redirect(url_for('auth.login'))
    
    # Get page number from query string, default to 1
    page = request.args.get('page', 1, type=int)
    per_page = 6
    
    # Get filter parameters
    status_filter = request.args.get('status', 'all')
    search_query = request.args.get('search', '')
    
    # Base query for owners
    query = Owner.query
    
    # Apply filters
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
        
    # Apply search if provided
    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(
            (Owner.username.ilike(search_term)) |
            (Owner.email.ilike(search_term)) |
            (Owner.phone.ilike(search_term))
        )
    
    # Get paginated results
    owners = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Get counts for filter pills
    total_count = Owner.query.count()
    active_count = Owner.query.filter_by(is_active=True).count()
    inactive_count = Owner.query.filter_by(is_active=False).count()

    # Get or create today's statistics with error handling
    today = datetime.now().date()
    stats = None
    
    try:
        stats = Statistics.query.filter_by(date=today).first()
        
        # Nếu đã có stats cho hôm nay, cập nhật lại số liệu
        if stats:
            # 1. User statistics
            total_owners = Owner.query.count() or random.randint(5, 15)  # Fake nếu chưa có
            total_renters = Renter.query.count() or random.randint(20, 50)  # Fake nếu chưa có
            total_users = total_owners + total_renters
            
            # 2. Booking statistics
            # Lấy tất cả booking đã hoàn thành
            completed_bookings = Booking.query.filter_by(status='completed').all()
            
            if completed_bookings:
                # Tính tổng số giờ thuê và số lần thuê từ dữ liệu thật
                total_hours = 0
                total_bookings = len(completed_bookings)
                hourly_count = 0
                overnight_count = 0
                
                for booking in completed_bookings:
                    duration = (booking.end_time - booking.start_time).total_seconds() / 3600
                    total_hours += duration
                    
                    if duration <= 24:
                        hourly_count += 1
                    else:
                        overnight_count += 1
                        
                common_type = "Theo giờ" if hourly_count >= overnight_count else "Qua đêm"
            else:
                # Fake data nếu chưa có booking
                total_hours = random.randint(100, 500)
                total_bookings = random.randint(20, 100)
                hourly_count = random.randint(10, 50)
                overnight_count = random.randint(10, 50)
                common_type = random.choice(["Theo giờ", "Qua đêm"])
            
            # 3. Rating statistics
            avg_rating = db.session.query(func.avg(Review.rating)).scalar()
            if avg_rating is None:
                # Fake rating nếu chưa có đánh giá
                avg_rating = round(random.uniform(4.0, 5.0), 1)
            
            # Cập nhật số liệu
            stats.total_owners = total_owners
            stats.total_renters = total_renters
            stats.total_users = total_users
            stats.total_hours = int(total_hours)
            stats.total_bookings = total_bookings
            stats.hourly_bookings = hourly_count
            stats.overnight_bookings = overnight_count
            stats.common_type = common_type
            stats.average_rating = avg_rating
            
            # Fake data cho biểu đồ nếu chưa có
            if not stats.hourly_stats:
                stats.hourly_stats = json.dumps({
                    'labels': ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'],
                    'data': [random.randint(5, 20) for _ in range(7)]
                })
            
            if not stats.overnight_stats:
                stats.overnight_stats = json.dumps({
                    'labels': ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'],
                    'data': [random.randint(3, 15) for _ in range(7)]
                })
            
            if not stats.top_homestays:
                # Fake data cho homestay nổi bật
                stats.top_homestays = json.dumps([
                    {
                        'name': 'Thới Lai Apartment',
                        'type': 'Theo giờ',
                        'revenue': random.randint(3000000, 5000000),
                        'bookings': random.randint(20, 30),
                        'rate': random.randint(70, 90),
                        'rating': round(random.uniform(4.0, 5.0), 1)
                    },
                    {
                        'name': 'Nordic Signature The View',
                        'type': 'Qua đêm',
                        'revenue': random.randint(2500000, 4000000),
                        'bookings': random.randint(15, 25),
                        'rate': random.randint(60, 85),
                        'rating': round(random.uniform(4.0, 5.0), 1)
                    },
                    {
                        'name': 'LoveNStay',
                        'type': 'Theo giờ',
                        'revenue': random.randint(1500000, 2500000),
                        'bookings': random.randint(10, 20),
                        'rate': random.randint(50, 75),
                        'rating': round(random.uniform(4.0, 5.0), 1)
                    },
                    {
                        'name': 'GoNow',
                        'type': 'Qua đêm',
                        'revenue': random.randint(1000000, 2000000),
                        'bookings': random.randint(8, 15),
                        'rate': random.randint(40, 70),
                        'rating': round(random.uniform(4.0, 5.0), 1)
                    },
                    {
                        'name': 'Bonita Thái Bình',
                        'type': 'Theo giờ',
                        'revenue': random.randint(1000000, 2000000),
                        'bookings': random.randint(10, 18),
                        'rate': random.randint(45, 65),
                        'rating': round(random.uniform(4.0, 5.0), 1)
                    }
                ])
            
            # Commit changes
            db.session.commit()
            print(f"Updated statistics with real/fake data successfully")
            
    except Exception as e:
        print(f"Error querying/updating statistics: {e}")
        db.session.rollback()
    
    if not stats:
        try:
            # Tạo thống kê mới với fake data
            total_owners = Owner.query.count() or random.randint(5, 15)
            total_renters = Renter.query.count() or random.randint(20, 50)
            total_users = total_owners + total_renters
            total_hours = random.randint(100, 500)
            total_bookings = random.randint(20, 100)
            hourly_bookings = random.randint(10, 50)
            overnight_bookings = random.randint(10, 50)
            common_type = random.choice(["Theo giờ", "Qua đêm"])
            avg_rating = round(random.uniform(4.0, 5.0), 1)
            
            stats = Statistics(
                date=today,
                total_users=total_users,
                total_owners=total_owners,
                total_renters=total_renters,
                total_bookings=total_bookings,
                hourly_bookings=hourly_bookings,
                overnight_bookings=overnight_bookings,
                total_hours=total_hours,
                booking_rate=round(random.uniform(60, 90), 1),
                common_type=common_type,
                average_rating=avg_rating,
                hourly_stats=json.dumps({
                    'labels': ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'],
                    'data': [random.randint(5, 20) for _ in range(7)]
                }),
                overnight_stats=json.dumps({
                    'labels': ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'],
                    'data': [random.randint(3, 15) for _ in range(7)]
                }),
                top_homestays=json.dumps([
                    {
                        'name': 'Thới Lai Apartment',
                        'type': 'Theo giờ',
                        'revenue': random.randint(3000000, 5000000),
                        'bookings': random.randint(20, 30),
                        'rate': random.randint(70, 90),
                        'rating': round(random.uniform(4.0, 5.0), 1)
                    },
                    {
                        'name': 'Nordic Signature The View',
                        'type': 'Qua đêm',
                        'revenue': random.randint(2500000, 4000000),
                        'bookings': random.randint(15, 25),
                        'rate': random.randint(60, 85),
                        'rating': round(random.uniform(4.0, 5.0), 1)
                    },
                    {
                        'name': 'LoveNStay',
                        'type': 'Theo giờ',
                        'revenue': random.randint(1500000, 2500000),
                        'bookings': random.randint(10, 20),
                        'rate': random.randint(50, 75),
                        'rating': round(random.uniform(4.0, 5.0), 1)
                    },
                    {
                        'name': 'GoNow',
                        'type': 'Qua đêm',
                        'revenue': random.randint(1000000, 2000000),
                        'bookings': random.randint(8, 15),
                        'rate': random.randint(40, 70),
                        'rating': round(random.uniform(4.0, 5.0), 1)
                    },
                    {
                        'name': 'Bonita Thái Bình',
                        'type': 'Theo giờ',
                        'revenue': random.randint(1000000, 2000000),
                        'bookings': random.randint(10, 18),
                        'rate': random.randint(45, 65),
                        'rating': round(random.uniform(4.0, 5.0), 1)
                    }
                ])
            )
            db.session.add(stats)
            db.session.commit()
            print(f"Created new statistics with fake data successfully")
        except Exception as e:
            print(f"Error creating statistics: {e}")
            db.session.rollback()
            return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/dashboard.html',
                         owners=owners,
                         total_count=total_count,
                         active_count=active_count,
                         inactive_count=inactive_count,
                         current_filter=status_filter,
                         search_query=search_query,
                         stats=stats)

@admin_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if not isinstance(current_user, Admin):
        flash("You are not authorized!", "danger")
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        try:
            # Get form data
            new_username = request.form.get('username')
            new_full_name = request.form.get('full_name')
            new_email = request.form.get('email')
            
            # Validate required fields
            if not new_username or not new_email:
                flash("Username và Email là bắt buộc!", "danger")
                return redirect(url_for('admin.profile'))
            
            # Check if username is being changed and if it already exists
            if new_username != current_user.username:
                existing_admin = Admin.query.filter_by(username=new_username).filter(Admin.id != current_user.id).first()
                existing_owner = Owner.query.filter_by(username=new_username).first()
                existing_renter = Renter.query.filter_by(username=new_username).first()
                
                if existing_admin or existing_owner or existing_renter:
                    flash(f"Username '{new_username}' đã tồn tại! Vui lòng chọn username khác.", "danger")
                    return redirect(url_for('admin.profile'))
            
            # Check if email is being changed and if it already exists
            if new_email != current_user.email:
                existing_admin = Admin.query.filter_by(email=new_email).filter(Admin.id != current_user.id).first()
                existing_owner = Owner.query.filter_by(email=new_email).first()
                existing_renter = Renter.query.filter_by(email=new_email).first()
                
                if existing_admin or existing_owner or existing_renter:
                    flash(f"Email '{new_email}' đã tồn tại! Vui lòng chọn email khác.", "danger")
                    return redirect(url_for('admin.profile'))
            
            # Update admin info
            current_user.username = new_username
            current_user.full_name = new_full_name
            current_user.email = new_email

            # Handle avatar upload
            if 'avatar' in request.files:
                avatar = request.files['avatar']
                print(f"Received file: {avatar.filename}")
                print(f"File content type: {avatar.content_type}")
                print(f"File size: {len(avatar.read())} bytes")
                avatar.seek(0)  # Reset file pointer after reading
                
                if avatar and avatar.filename != '':
                    if not allowed_file(avatar.filename):
                        print(f"File type not allowed: {avatar.filename}")
                        flash("File type not allowed. Please use: png, jpg, jpeg, gif, or webp", "danger")
                        return redirect(url_for('admin.profile'))
                    
                    try:
                        # Ensure upload folder exists
                        upload_folder = current_app.config['UPLOAD_FOLDER']
                        print(f"Upload folder path: {upload_folder}")
                        abs_upload_folder = os.path.abspath(upload_folder)
                        print(f"Absolute upload folder path: {abs_upload_folder}")
                        
                        if not os.path.exists(abs_upload_folder):
                            print(f"Creating upload folder: {abs_upload_folder}")
                            os.makedirs(abs_upload_folder, exist_ok=True)
                        
                        # Generate secure filename and save file
                        filename = secure_filename(avatar.filename)
                        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                        filename = f"{timestamp}_{filename}"
                        filepath = os.path.join(abs_upload_folder, filename)
                        print(f"Saving file to: {filepath}")
                        
                        # Save file
                        avatar.save(filepath)
                        
                        if not os.path.exists(filepath):
                            raise Exception(f"File was not saved successfully to {filepath}")
                        
                        print(f"File saved successfully. Size: {os.path.getsize(filepath)} bytes")
                        
                        # Delete old avatar if exists
                        if current_user.avatar:
                            old_avatar_path = os.path.join(abs_upload_folder, current_user.avatar)
                            if os.path.exists(old_avatar_path):
                                os.remove(old_avatar_path)
                                print(f"Deleted old avatar: {old_avatar_path}")
                        
                        # Update the avatar field in the user's profile
                        current_user.avatar = filename
                        print(f"Updated user avatar in database: {filename}")
                        
                        # Commit changes to database
                        db.session.commit()
                        flash("Avatar updated successfully!", "success")
                        
                    except Exception as e:
                        print(f"Error during file operations: {str(e)}")
                        print(f"Current working directory: {os.getcwd()}")
                        flash(f"Error saving avatar: {str(e)}", "danger")
                        return redirect(url_for('admin.profile'))

            # Commit changes to the database
            db.session.commit()
            flash("Cập nhật thông tin thành công!", "success")
            
        except IntegrityError as e:
            print(f"IntegrityError: {str(e)}")
            db.session.rollback()
            flash("Lỗi: Username hoặc Email đã tồn tại. Vui lòng thử lại với thông tin khác.", "danger")
        except Exception as e:
            print(f"Error updating profile: {str(e)}")
            db.session.rollback()
            flash(f"Lỗi cập nhật thông tin: {str(e)}", "danger")
            
        return redirect(url_for('admin.profile'))

    # Calculate statistics for dashboard
    total_users = (Admin.query.count() or 0) + (Owner.query.count() or 0) + (Renter.query.count() or 0)
    total_homestays = Room.query.count() or 0
    
    return render_template("user/profile.html", 
                          total_users=total_users,
                          total_homestays=total_homestays)

@admin_bp.route('/create_owner', methods=['GET', 'POST'])
@login_required
def create_owner():
    if not isinstance(current_user, Admin):
        flash("Unauthorized access", "danger")
        return redirect(url_for('home'))
        
    form_data = {}
    
    if request.method == 'POST':
        # Get form data
        full_name = request.form.get('full_name')
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        # Store form data for repopulating the form
        form_data = {
            'full_name': full_name,
            'username': username,
            'email': email,
            'phone': phone
        }
        
        # Validate required fields
        if not all([full_name, username, email, phone, password]):
            flash("All fields are required", "danger")
            return render_template('admin/create_owner.html', form_data=form_data)
        
        # Check if username exists
        if Owner.query.filter_by(username=username).first():
            flash("Username already exists", "danger")
            return render_template('admin/create_owner.html', form_data=form_data)
        
        if (Admin.query.filter_by(email=email).first() or 
            Owner.query.filter_by(email=email).first() or 
            Renter.query.filter_by(email=email).first()):
            flash("Email already exists", "danger")
            return render_template('admin/create_owner.html', form_data=form_data)
        
        if (Owner.query.filter_by(phone=phone).first() or 
            Renter.query.filter_by(phone=phone).first()):
            flash("Phone number already exists", "danger")
            return render_template('admin/create_owner.html', form_data=form_data)
        
        try:
            new_owner = Owner(
                full_name=full_name,
                username=username,
                email=email,
                phone=phone
            )
            new_owner.set_password(password)
            db.session.add(new_owner)
            db.session.commit()
            
            flash("Owner created successfully!", "success")
            return redirect(url_for('admin.dashboard'))
        except IntegrityError:
            db.session.rollback()
            flash("Error: A unique field already exists. Please use different information.", "danger")
            return render_template('admin/create_owner.html', form_data=form_data)
            
    return render_template('admin/create_owner.html', form_data=form_data)

@admin_bp.route('/homestay/<int:homestay_id>')
@login_required
def homestay_details(homestay_id):
    if not isinstance(current_user, Admin):
        flash("Bạn không có quyền truy cập!", "danger")
        return redirect(url_for('auth.login'))
    
    homestay = Room.query.get_or_404(homestay_id)
    return render_template('admin/homestay_details.html', homestay=homestay)

@admin_bp.route('/homestay/<int:homestay_id>/toggle-status', methods=['POST'])
@login_required
def toggle_homestay_status(homestay_id):
    if not isinstance(current_user, Admin):
        flash("Bạn không có quyền thực hiện thao tác này!", "danger")
        return redirect(url_for('auth.login'))
    
    homestay = Room.query.get_or_404(homestay_id)
    
    # Đảo ngược trạng thái hoạt động
    homestay.is_active = not homestay.is_active
    
    try:
        db.session.commit()
        status_message = "Đã mở khóa" if homestay.is_active else "Đã tạm khóa"
        flash(f"{status_message} homestay '{homestay.title}' thành công!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Có lỗi xảy ra: {str(e)}", "danger")
    
    return redirect(url_for('admin.homestay_details', homestay_id=homestay.id))

# Decorator để kiểm tra super admin
def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_super_admin:
            flash('Bạn không có quyền truy cập trang này.', 'danger')
            return redirect(url_for('admin.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/manage-admins')
@login_required
@super_admin_required
def manage_admins():
    admins = Admin.query.all()
    return render_template('admin/manage_admins.html', admins=admins)

@admin_bp.route('/create-admin', methods=['GET', 'POST'])
@login_required
@super_admin_required
def create_admin():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        is_super_admin = request.form.get('is_super_admin') == 'on'
        
        # Kiểm tra username và email đã tồn tại chưa
        if Admin.query.filter_by(username=username).first():
            flash('Username đã tồn tại.', 'danger')
            return redirect(url_for('admin.create_admin'))
            
        if Admin.query.filter_by(email=email).first():
            flash('Email đã tồn tại.', 'danger')
            return redirect(url_for('admin.create_admin'))
        
        # Tạo admin mới
        new_admin = Admin(username=username, email=email, full_name=full_name, is_super_admin=is_super_admin)
        new_admin.set_password(password)
        
        db.session.add(new_admin)
        db.session.commit()
        
        flash('Tạo admin mới thành công!', 'success')
        return redirect(url_for('admin.manage_admins'))
        
    return render_template('admin/create_admin.html')

@admin_bp.route('/edit-admin/<int:admin_id>', methods=['GET', 'POST'])
@login_required
@super_admin_required
def edit_admin(admin_id):
    admin = Admin.query.get_or_404(admin_id)
    
    # Không cho phép sửa chính mình
    if admin.id == current_user.id:
        flash('Không thể sửa tài khoản của chính mình.', 'danger')
        return redirect(url_for('admin.manage_admins'))
    
    if request.method == 'POST':
        admin.full_name = request.form.get('full_name')
        admin.is_super_admin = request.form.get('is_super_admin') == 'on'
        
        # Cập nhật các quyền
        if admin.is_super_admin:
            admin.can_manage_admins = True
            admin.can_approve_changes = True
            admin.can_view_all_stats = True
            admin.can_manage_users = True
        else:
            admin.can_manage_admins = False
            admin.can_approve_changes = False
            
        db.session.commit()
        flash('Cập nhật admin thành công!', 'success')
        return redirect(url_for('admin.manage_admins'))
        
    return render_template('admin/edit_admin.html', admin=admin)

@admin_bp.route('/delete-admin/<int:admin_id>', methods=['POST'])
@login_required
@super_admin_required
def delete_admin(admin_id):
    admin = Admin.query.get_or_404(admin_id)
    
    # Không cho phép xóa chính mình
    if admin.id == current_user.id:
        flash('Không thể xóa tài khoản của chính mình.', 'danger')
        return redirect(url_for('admin.manage_admins'))
    
    db.session.delete(admin)
    db.session.commit()
    
    flash('Xóa admin thành công!', 'success')
    return redirect(url_for('admin.manage_admins'))

@admin_bp.route('/set-super-admin')
@login_required
def set_super_admin():
    if not isinstance(current_user, Admin):
        flash('Bạn không có quyền thực hiện thao tác này!', 'danger')
        return redirect(url_for('home'))
    
    # Kiểm tra xem đã có super admin nào chưa
    existing_super_admin = Admin.query.filter_by(is_super_admin=True).first()
    
    if not existing_super_admin:
        # Nếu chưa có super admin nào, set tài khoản hiện tại thành super admin
        current_user.is_super_admin = True
        current_user.can_manage_admins = True
        current_user.can_approve_changes = True
        current_user.can_view_all_stats = True
        current_user.can_manage_users = True
        
        db.session.commit()
        flash('Bạn đã được set làm Super Admin!', 'success')
    else:
        flash('Đã có Super Admin trong hệ thống!', 'warning')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/add-owner', methods=['POST'])
@login_required
def add_owner():
    if not isinstance(current_user, Admin):
        return jsonify({'error': 'Bạn không có quyền thực hiện thao tác này'}), 401
    
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirm_password')
    
    # Kiểm tra dữ liệu đầu vào
    if not username:
        return jsonify({'error': 'Vui lòng nhập tên đăng nhập'}), 400
    if not email:
        return jsonify({'error': 'Vui lòng nhập email'}), 400
    if not password:
        return jsonify({'error': 'Vui lòng nhập mật khẩu'}), 400
    if not confirm_password:
        return jsonify({'error': 'Vui lòng xác nhận mật khẩu'}), 400
    
    # Kiểm tra mật khẩu khớp nhau
    if password != confirm_password:
        return jsonify({'error': 'Mật khẩu xác nhận không khớp'}), 400
        
    # Kiểm tra username và email đã tồn tại chưa
    if Owner.query.filter_by(username=username).first():
        return jsonify({'error': 'Tên đăng nhập đã tồn tại'}), 400
        
    if Owner.query.filter_by(email=email).first():
        return jsonify({'error': 'Email đã được sử dụng'}), 400
    
    try:
        # Tạo owner mới
        new_owner = Owner(
            username=username,
            email=email,
            full_name=username  # Tạm thời dùng username làm full_name
        )
        new_owner.set_password(password)
        
        db.session.add(new_owner)
        db.session.commit()
        
        return jsonify({
            'message': 'Tạo tài khoản owner thành công',
            'owner': {
                'id': new_owner.id,
                'username': new_owner.username,
                'email': new_owner.email
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Lỗi khi tạo tài khoản: {str(e)}'}), 500

@admin_bp.route('/seed-owners')
@login_required
def seed_owners():
    if not isinstance(current_user, Admin):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        from scripts.seed_data import seed_owners
        seed_owners()
        return jsonify({'message': 'Đã thêm dữ liệu mẫu thành công!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/owner/<int:owner_id>/toggle-status', methods=['POST'])
@login_required
def toggle_owner_status(owner_id):
    if not isinstance(current_user, Admin):
        return jsonify({'error': 'Bạn không có quyền thực hiện thao tác này'}), 401
    
    owner = Owner.query.get_or_404(owner_id)
    reason = request.form.get('reason')
    
    try:
        owner.is_active = not owner.is_active
        if not owner.is_active:  # Nếu vô hiệu hóa
            if not reason:
                return jsonify({'error': 'Vui lòng nhập lý do vô hiệu hóa'}), 400
            owner.reason = reason
        
        db.session.commit()
        message = 'Kích hoạt tài khoản thành công!' if owner.is_active else 'Vô hiệu hóa tài khoản thành công!'
        return jsonify({
            'success': True,
            'message': message
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/owner/<int:owner_id>/reason')
@login_required
def get_owner_reason(owner_id):
    if not isinstance(current_user, Admin):
        return jsonify({'error': 'Unauthorized'}), 401
    
    owner = Owner.query.get_or_404(owner_id)
    return jsonify({'reason': owner.reason})

@admin_bp.route('/owner/<int:owner_id>')
@login_required
def owner_detail(owner_id):
    if not isinstance(current_user, Admin):
        flash("You are not authorized!", "danger")
        return redirect(url_for('auth.login'))
    
    owner = Owner.query.get_or_404(owner_id)
    return render_template('admin/owner_detail.html', owner=owner)

@admin_bp.route('/owner/<int:owner_id>/delete', methods=['POST'])
@login_required
def delete_owner(owner_id):
    if not isinstance(current_user, Admin):
        flash("You are not authorized!", "danger")
        return redirect(url_for('auth.login'))
    
    owner = Owner.query.get_or_404(owner_id)
    try:
        db.session.delete(owner)
        db.session.commit()
        flash('Tài khoản đã được xóa thành công', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi khi xóa tài khoản: {str(e)}', 'danger')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/create-admin-ajax', methods=['POST'])
@login_required
@super_admin_required
def create_admin_ajax():
    try:
        data = request.get_json()
        
        username = data.get('username')
        email = data.get('email')
        full_name = data.get('full_name')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        is_super_admin = data.get('is_super_admin', False)
        
        # Validate required fields
        if not all([username, email, full_name, password, confirm_password]):
            return jsonify({'success': False, 'message': 'Vui lòng điền đầy đủ thông tin!'}), 400
        
        # Validate password match
        if password != confirm_password:
            return jsonify({'success': False, 'message': 'Mật khẩu xác nhận không khớp!'}), 400
        
        # Check if username exists
        if Admin.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': 'Username đã tồn tại!'}), 400
        
        # Check if email exists
        if Admin.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Email đã được sử dụng!'}), 400
        
        # Create new admin
        new_admin = Admin(
            username=username,
            email=email,
            full_name=full_name,
            is_super_admin=is_super_admin
        )
        
        # Set admin permissions based on super admin status
        if is_super_admin:
            new_admin.can_manage_admins = True
            new_admin.can_approve_changes = True
            new_admin.can_view_all_stats = True
            new_admin.can_manage_users = True
        
        new_admin.set_password(password)
        
        db.session.add(new_admin)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Tạo admin {username} thành công!'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'}), 500
