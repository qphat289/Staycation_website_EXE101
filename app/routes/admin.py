from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models.models import db, Admin, Owner, Renter, Home, Booking, Statistics, Review
from app.utils.utils import allowed_file
from sqlalchemy.exc import IntegrityError
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from functools import wraps
import uuid
import json
from sqlalchemy import func, distinct

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')



@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not isinstance(current_user, Admin):
        flash("You are not authorized!", "danger")
        return redirect(url_for('auth.login'))
      # Get filter parameters
    page = request.args.get('page', 1, type=int)
    per_page = 5
    status_filter = request.args.get('status', 'all')
    role_filter = request.args.get('role', 'all')
    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort', 'id_asc')
    
    def get_all_users():
        """Get all users combined with role information (excluding admins)"""
        users = []
        
        # Get owners
        owners = Owner.query.all()
        for owner in owners:
            # Lấy commission_percent của phòng đầu tiên (nếu có)
            commission_percent = None
            total_revenue = 0
            if owner.rooms and len(owner.rooms) > 0:
                commission_percent = owner.rooms[0].commission_percent
                # Tính tổng doanh thu các phòng
                total_revenue = sum([room.revenue or 0 for room in owner.rooms])
            users.append({
                'id': owner.id,
                'username': owner.username,
                'email': owner.email,
                'phone': getattr(owner, 'phone', 'Chưa cập nhật'),
                'full_name': getattr(owner, 'full_name', 'Chưa cập nhật'),
                'is_active': getattr(owner, 'is_active', True),
                'role': 'Owner',
                'role_type': 'owner',
                'created_at': getattr(owner, 'created_at', None),
                'commission_percent': commission_percent,
                'total_revenue': total_revenue
            })
        
        # Get renters
        renters = Renter.query.all()
        for renter in renters:
            users.append({
                'id': renter.id,
                'username': renter.username,
                'email': renter.email,
                'phone': getattr(renter, 'phone', 'Chưa cập nhật'),
                'full_name': getattr(renter, 'full_name', 'Chưa cập nhật'),
                'is_active': getattr(renter, 'is_active', True),
                'role': 'Renter',
                'role_type': 'renter',
                'created_at': getattr(renter, 'created_at', None)
            })
        
        # Note: Admins are excluded from the unified user list
        # They are managed separately in the "Quản lý admin" section
        
        return users
    
    # Get all users
    all_users = get_all_users()
    owners = Owner.query.all()  # Thêm dòng này để lấy danh sách Owner thực sự
      # Apply role filter (only owner and renter, no admin)
    if role_filter != 'all':
        if role_filter in ['owner', 'renter']:
            all_users = [user for user in all_users if user['role_type'] == role_filter]
        # If role_filter is 'admin', redirect to 'all' since we don't show admins here
        elif role_filter == 'admin':
            return redirect(url_for('admin.dashboard', role='all', status=status_filter, search=search_query))
    
    # Apply status filter
    if status_filter != 'all':
        if status_filter == 'active':
            all_users = [user for user in all_users if user['is_active']]
        elif status_filter == 'inactive':
            all_users = [user for user in all_users if not user['is_active']]
    
    # Apply search filter
    if search_query:
        search_term = search_query.lower()
        filtered_users = []
        for user in all_users:
            if (search_term in user['username'].lower() or
                search_term in user['email'].lower() or
                search_term in str(user['phone']).lower() or
                search_term in str(user['full_name']).lower()):
                filtered_users.append(user)
        all_users = filtered_users
    
    # Apply sorting
    if sort_by == 'id_asc':
        all_users.sort(key=lambda x: x['id'])
    elif sort_by == 'id_desc':
        all_users.sort(key=lambda x: x['id'], reverse=True)
    elif sort_by == 'name_asc':
        all_users.sort(key=lambda x: x['full_name'] or x['username'])
    elif sort_by == 'name_desc':
        all_users.sort(key=lambda x: x['full_name'] or x['username'], reverse=True)
    elif sort_by == 'date_desc':
        all_users.sort(key=lambda x: x['created_at'] or datetime.min, reverse=True)
    elif sort_by == 'date_asc':
        all_users.sort(key=lambda x: x['created_at'] or datetime.min)
    
    # Manual pagination
    total_users = len(all_users)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_users = all_users[start_idx:end_idx]
    
    # Create pagination object
    class PaginationMock:
        def __init__(self, items, page, per_page, total):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1 if self.has_prev else None
            self.next_num = page + 1 if self.has_next else None
    
    users = PaginationMock(paginated_users, page, per_page, total_users)
      # Calculate counts (excluding admins)
    total_owners = Owner.query.count()
    total_renters = Renter.query.count()
    total_all = total_owners + total_renters  # No admin count
    
    active_owners = Owner.query.filter_by(is_active=True).count()
    inactive_owners = Owner.query.filter_by(is_active=False).count()
    active_renters = Renter.query.filter_by(is_active=True).count()
    inactive_renters = Renter.query.filter_by(is_active=False).count()
    
    total_active = active_owners + active_renters  # No admin count
    total_inactive = inactive_owners + inactive_renters
    
    # Set counts based on current filter
    if role_filter == 'owner':
        total_count = total_owners
        active_count = active_owners
        inactive_count = inactive_owners
    elif role_filter == 'renter':
        total_count = total_renters
        active_count = active_renters
        inactive_count = inactive_renters
    else:  # all (owners + renters only, no admins)
        total_count = total_all
        active_count = total_active
        inactive_count = total_inactive

    # --- PHẦN 2: LOGIC THỐNG KÊ ---
    try:
        today = datetime.now().date()
        stats = Statistics.query.filter_by(date=today).first()

        # Bước 1: Nếu chưa có thống kê cho hôm nay, tạo một đối tượng rỗng với giá trị mặc định
        if not stats:
            stats = Statistics(
                date=today,
                total_users=0,
                total_owners=0,
                total_renters=0,
                total_homes=0,
                total_bookings=0,
                hourly_bookings=0,
                overnight_bookings=0,
                total_hours=0,
                booking_rate=0.0,
                common_type="N/A",
                average_rating=0.0,
                hourly_stats=json.dumps({'labels': [], 'data': []}),
                overnight_stats=json.dumps({'labels': [], 'data': []}),
                top_homes=json.dumps([])
            )
            db.session.add(stats)

        # Bước 2: Luôn tính toán và gán lại dữ liệu THẬT
        stats.total_owners = Owner.query.count()
        stats.total_renters = Renter.query.count()
        stats.total_users = stats.total_owners + stats.total_renters
        stats.total_homes = Home.query.count()
        
        completed_bookings = Booking.query.filter_by(status='completed').all()
        stats.total_bookings = len(completed_bookings)
        
        avg_rating_real = db.session.query(func.avg(Review.rating)).scalar()
        stats.average_rating = round(avg_rating_real, 1) if avg_rating_real is not None else 0.0

        # Calculate weekly statistics (records added this week)
        from datetime import timedelta
        
        # Get the start of current week (Monday)
        days_since_monday = today.weekday()  # Monday is 0, Sunday is 6
        week_start = today - timedelta(days=days_since_monday)
        week_start_datetime = datetime.combine(week_start, datetime.min.time())
        
        # Calculate new records added this week
        new_owners_this_week = Owner.query.filter(Owner.created_at >= week_start_datetime).count()
        new_renters_this_week = Renter.query.filter(Renter.created_at >= week_start_datetime).count()
        new_homes_this_week = Home.query.filter(Home.created_at >= week_start_datetime).count()
        new_bookings_this_week = Booking.query.filter(Booking.created_at >= week_start_datetime).count()
        
        # Calculate booking growth rate (compared to total)
        booking_growth_rate = 0
        if stats.total_bookings > 0:
            booking_growth_rate = round((new_bookings_this_week / stats.total_bookings) * 100, 1)

        # Calculate monthly statistics (records added this month)
        month_start = today.replace(day=1)
        month_start_datetime = datetime.combine(month_start, datetime.min.time())
        
        # Calculate new records added this month
        new_owners_this_month = Owner.query.filter(Owner.created_at >= month_start_datetime).count()
        new_renters_this_month = Renter.query.filter(Renter.created_at >= month_start_datetime).count()
        new_homes_this_month = Home.query.filter(Home.created_at >= month_start_datetime).count()
        new_bookings_this_month = Booking.query.filter(Booking.created_at >= month_start_datetime).count()

        # Calculate most popular rental type based on homestay count (not booking count)
        all_active_homes = Home.query.filter_by(is_active=True).all()
        hourly_homestays_count = 0
        nightly_homestays_count = 0
        
        for home in all_active_homes:
            # Use same logic as owner.py line 612 to determine rental type
            if home.price_per_night and home.price_per_night > 0:
                nightly_homestays_count += 1
            else:
                hourly_homestays_count += 1
          # Determine most popular type based on homestay count
        if hourly_homestays_count > nightly_homestays_count:
            stats.common_type = "Theo giờ"
        elif nightly_homestays_count > hourly_homestays_count:
            stats.common_type = "Theo ngày"
        else:
            stats.common_type = "N/A"  # Equal numbers or no homestays

        # Calculate admin commission (10% from all completed bookings)
        total_revenue_all_bookings = sum(booking.total_price for booking in completed_bookings)
        admin_commission = int(total_revenue_all_bookings * 0.1)  # 10% commission

        if completed_bookings:
            stats.total_hours = int(sum((b.end_time - b.start_time).total_seconds() / 3600 for b in completed_bookings))
            hourly_count = sum(1 for b in completed_bookings if ((b.end_time - b.start_time).total_seconds() / 3600) <= 24)
            stats.hourly_bookings = hourly_count
            stats.overnight_bookings = stats.total_bookings - hourly_count
        else:
            stats.total_hours = 0
            stats.hourly_bookings = 0
            stats.overnight_bookings = 0        # Calculate real top homestays by booking count - Group by Owner (homestay)
        top_homestays_query = db.session.query(
            Owner.id,
            Owner.full_name,
            func.count(distinct(Home.id)).label('home_count'),
            func.count(Booking.id).label('booking_count'),
            func.sum(Booking.total_price).label('total_revenue'),
            func.avg(Review.rating).label('avg_rating')
        ).join(Home, Owner.id == Home.owner_id) \
         .outerjoin(Booking, Home.id == Booking.home_id) \
         .outerjoin(Review, Home.id == Review.home_id) \
         .filter(Home.is_active == True) \
         .group_by(Owner.id, Owner.full_name) \
         .order_by(func.count(Booking.id).desc()) \
         .limit(5).all()

        top_homestays_list = []
        for homestay in top_homestays_query:
            # Calculate admin commission (10%) from this homestay's revenue
            homestay_revenue = int(homestay.total_revenue) if homestay.total_revenue else 0
            admin_commission_homestay = int(homestay_revenue * 0.1)  # 10% commission
            
            homestay_data = {
                'name': homestay.full_name or f'Homestay {homestay.id}',
                'home_count': homestay.home_count,  # Number of homes instead of rental type
                'revenue': homestay_revenue,
                'admin_commission': admin_commission_homestay,  # Add admin commission for this homestay
                'bookings': homestay.booking_count,
                'rating': round(homestay.avg_rating, 1) if homestay.avg_rating else 0.0
            }
            top_homestays_list.append(homestay_data)

        stats.top_homes = json.dumps(top_homestays_list)

        # Create empty chart data if no real data exists
        if not stats.hourly_stats:
            stats.hourly_stats = json.dumps({
                'labels': [],
                'data': []
            })
            
        if not stats.overnight_stats:
            stats.overnight_stats = json.dumps({
                'labels': [],
                'data': []
            })

        # Create real user growth data based on actual database counts
        user_growth_data = {
            'labels': ['Today'],
            'owner_data': [stats.total_owners],
            'renter_data': [stats.total_renters]
        }        # Commit changes to database
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        print(f"CRITICAL ERROR in statistics calculation: {e}")
        # Create an empty stats object to prevent page crash with proper initialization
        stats = Statistics(
            date=datetime.now().date(),
            total_users=0,
            total_owners=0,
            total_renters=0,
            total_homes=0,
            total_bookings=0,
            hourly_bookings=0,
            overnight_bookings=0,
            total_hours=0,
            booking_rate=0.0,
            common_type="N/A",
            average_rating=0.0,
            hourly_stats=json.dumps({'labels': [], 'data': []}),
            overnight_stats=json.dumps({'labels': [], 'data': []}),
            top_homes=json.dumps([])
        )
        admin_commission = 0  # Default admin commission when error occurs
        # Create default empty data for charts when error occurs
        user_growth_data = {
            'labels': ['Today'],
            'owner_data': [0],
            'renter_data': [0]
        }
        # Default weekly stats when error occurs
        new_owners_this_week = 0
        new_renters_this_week = 0
        new_homes_this_week = 0
        new_bookings_this_week = 0
        booking_growth_rate = 0
        new_owners_this_month = 0
        new_renters_this_month = 0
        new_homes_this_month = 0
        new_bookings_this_month = 0
    
    # --- RETURN TEMPLATE ---
    return render_template('admin/dashboard.html', 
                          users=users,  # Changed from owners to users
                          owners=owners,  # Truyền đúng đối tượng Owner
                          total_count=total_count,
                          active_count=active_count,
                          inactive_count=inactive_count,
                          current_filter=status_filter,
                          current_role_filter=role_filter,
                          search_query=search_query,
                          sort_by=sort_by,
                          stats=stats,
                          admins=Admin.query.all(),  # Always fetch all admins for admin section
                          admin_commission=admin_commission,
                          user_growth_data=user_growth_data,
                          weekly_stats={
                              'new_owners': new_owners_this_week,
                              'new_renters': new_renters_this_week,
                              'new_homes': new_homes_this_week,
                              'new_bookings': new_bookings_this_week,
                              'booking_growth_rate': booking_growth_rate,
                              'new_owners_month': new_owners_this_month,
                              'new_renters_month': new_renters_this_month,
                              'new_homes_month': new_homes_this_month,
                              'new_bookings_month': new_bookings_this_month
                          })

        
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
    total_homestays = Home.query.count() or 0
    
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
    
    homestay = Home.query.get_or_404(homestay_id)
    return render_template('admin/homestay_details.html', homestay=homestay)

@admin_bp.route('/homestay/<int:homestay_id>/toggle-status', methods=['POST'])
@login_required
def toggle_homestay_status(homestay_id):
    if not isinstance(current_user, Admin):
        flash("Bạn không có quyền thực hiện thao tác này!", "danger")
        return redirect(url_for('auth.login'))
    
    homestay = Home.query.get_or_404(homestay_id)
    
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
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        is_super_admin = request.form.get('is_super_admin') == 'on'
          # Validate required fields
        if not all([username, email, password, confirm_password, full_name]):
            flash('Vui lòng điền đầy đủ thông tin bắt buộc', 'danger')
            return render_template('admin/create_admin.html')
        
        # Validate username format (4-20 characters, letters, numbers, underscores)
        import re
        if not re.match(r'^[a-zA-Z0-9_]{4,20}$', username):
            flash('Username phải từ 4-20 ký tự, chỉ bao gồm chữ cái, số và dấu gạch dưới', 'danger')
            return render_template('admin/create_admin.html')
        
        # Validate password complexity
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$', password):
            flash('Mật khẩu phải có ít nhất 8 ký tự, bao gồm chữ hoa, chữ thường và số', 'danger')
            return render_template('admin/create_admin.html')
        
        # Validate password match
        if password != confirm_password:
            flash('Mật khẩu xác nhận không khớp', 'danger')
            return render_template('admin/create_admin.html')
        
        # Check if username exists
        if Admin.query.filter_by(username=username).first():
            flash('Username đã tồn tại.', 'danger')
            return render_template('admin/create_admin.html')
            
        # Check if email exists
        if Admin.query.filter_by(email=email).first():
            flash('Email đã tồn tại.', 'danger')
            return render_template('admin/create_admin.html')
        
        try:
            # Tạo admin mới
            new_admin = Admin(username=username, email=email, full_name=full_name, is_super_admin=is_super_admin)
            new_admin.set_password(password)
            
            db.session.add(new_admin)
            db.session.commit()
            
            flash('Tạo admin mới thành công!', 'success')
            return redirect(url_for('admin.manage_admins'))
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi khi tạo admin: {str(e)}', 'danger')
            return render_template('admin/create_admin.html')
        
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
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        full_name = data.get('full_name')
        is_super_admin = data.get('is_super_admin') == 'on'
        
        # Validate required fields
        if not all([username, email, password, confirm_password, full_name]):
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

@admin_bp.route('/add-admin', methods=['POST'])
@login_required
@super_admin_required
def add_admin_ajax():
    """Handle AJAX request to create a new admin user from the modal"""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Extract form data
        username = data.get('username', '')
        email = data.get('email', '')
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        role = data.get('role', '')
        is_super_admin = role == 'super_admin'
        
        # Basic validation
        if not all([username, email, password]):
            return jsonify({'success': False, 'error': 'Vui lòng điền đầy đủ thông tin bắt buộc'}), 400
            
        # Validate password match
        if password != confirm_password:
            return jsonify({'success': False, 'error': 'Mật khẩu xác nhận không khớp!'}), 400
        
        # Check if username exists
        if Admin.query.filter_by(username=username).first():
            return jsonify({'success': False, 'error': 'Username đã tồn tại'}), 400
            
        # Check if email exists
        if Admin.query.filter_by(email=email).first():
            return jsonify({'success': False, 'error': 'Email đã được sử dụng'}), 400
        
        # Create new admin
        new_admin = Admin(
            username=username,
            email=email,
            full_name=username,  # Default to username if no full name provided
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
        return jsonify({'success': False, 'error': f'Lỗi: {str(e)}'}), 500

# --- THỐNG KÊ TUẦN ---
@admin_bp.route('/weekly-statistics')
@login_required
def weekly_statistics():
    if not isinstance(current_user, Admin):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Calculate weekly statistics (records added this week)
        from datetime import timedelta
        
        # Get the start of current week (Monday)
        today = datetime.now().date()
        days_since_monday = today.weekday()  # Monday is 0, Sunday is 6
        week_start = today - timedelta(days=days_since_monday)
        week_start_datetime = datetime.combine(week_start, datetime.min.time())
        
        # Calculate new records added this week
        new_owners_this_week = Owner.query.filter(Owner.created_at >= week_start_datetime).count()
        new_renters_this_week = Renter.query.filter(Renter.created_at >= week_start_datetime).count()
        new_homes_this_week = Home.query.filter(Home.created_at >= week_start_datetime).count()
        new_bookings_this_week = Booking.query.filter(Booking.created_at >= week_start_datetime).count()
        
        # Get total counts for growth rate calculation
        total_bookings = Booking.query.count()
        
        # Calculate booking growth rate (compared to total)
        booking_growth_rate = 0
        if total_bookings > 0:
            booking_growth_rate = round((new_bookings_this_week / total_bookings) * 100, 1)

        # Prepare response data
        response_data = {
            'new_owners': new_owners_this_week,
            'new_renters': new_renters_this_week,
            'new_homes': new_homes_this_week,
            'new_bookings': new_bookings_this_week,
            'booking_growth_rate': booking_growth_rate
        }        
        return jsonify({'success': True, 'data': response_data}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# --- API THỐNG KÊ TĂNG TRƯỞNG NGƯỜI DÙNG ---
@admin_bp.route('/api/user-growth-data/<period>')
@login_required
def get_user_growth_data(period):
    """API endpoint to get user growth data for line chart"""
    if not isinstance(current_user, Admin):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        from datetime import timedelta
        
        today = datetime.now().date()
        
        # Determine date range based on period
        if period == 'week':
            days = 7
            date_format = 'weekday'
        elif period == 'month':
            days = 30
            date_format = 'day'
        elif period == 'year':
            days = 365
            date_format = 'month'
        else:
            return jsonify({'error': 'Invalid period'}), 400
        
        # Generate data for the specified period
        owners_data = []
        renters_data = []
        labels = []
        
        for i in range(days - 1, -1, -1):
            current_date = today - timedelta(days=i)
            
            if period == 'week':
                # Count users created on this specific day
                start_datetime = datetime.combine(current_date, datetime.min.time())
                end_datetime = datetime.combine(current_date, datetime.max.time())
                
                owners_count = Owner.query.filter(
                    Owner.created_at >= start_datetime,
                    Owner.created_at <= end_datetime
                ).count()
                
                renters_count = Renter.query.filter(
                    Renter.created_at >= start_datetime,
                    Renter.created_at <= end_datetime
                ).count()
                
                # Format label for week view
                label = current_date.strftime('%a %d')  # Mon 01
                
            elif period == 'month':
                # Count users created on this specific day
                start_datetime = datetime.combine(current_date, datetime.min.time())
                end_datetime = datetime.combine(current_date, datetime.max.time())
                
                owners_count = Owner.query.filter(
                    Owner.created_at >= start_datetime,
                    Owner.created_at <= end_datetime
                ).count()
                
                renters_count = Renter.query.filter(
                    Renter.created_at >= start_datetime,
                    Renter.created_at <= end_datetime
                ).count()
                
                # Format label for month view (show every 3rd day to avoid crowding)
                if i % 3 == 0 or i == 0:
                    label = current_date.strftime('%d')
                else:
                    label = ''
                    
            else:  # year
                # For year view, group by week and show weekly totals
                week_start = current_date - timedelta(days=current_date.weekday())
                week_end = week_start + timedelta(days=6)
                
                start_datetime = datetime.combine(week_start, datetime.min.time())
                end_datetime = datetime.combine(week_end, datetime.max.time())
                
                owners_count = Owner.query.filter(
                    Owner.created_at >= start_datetime,
                    Owner.created_at <= end_datetime
                ).count()
                
                renters_count = Renter.query.filter(
                    Renter.created_at >= start_datetime,
                    Renter.created_at <= end_datetime
                ).count()
                
                # Format label for year view (show every 30th day)
                if i % 30 == 0 or i == 0:
                    label = current_date.strftime('%b')
                else:
                    label = ''
            
            owners_data.append(owners_count)
            renters_data.append(renters_count)
            labels.append(label)
        
        # For year view, we need to aggregate data by weeks to reduce data points
        if period == 'year':
            # Group data by weeks (every 7 days)
            weekly_owners = []
            weekly_renters = []
            weekly_labels = []
            
            for i in range(0, len(owners_data), 7):
                week_owners = sum(owners_data[i:i+7])
                week_renters = sum(renters_data[i:i+7])
                week_label = labels[i] if labels[i] else f'W{i//7 + 1}'
                
                weekly_owners.append(week_owners)
                weekly_renters.append(week_renters)
                weekly_labels.append(week_label)
            
            owners_data = weekly_owners
            renters_data = weekly_renters
            labels = weekly_labels
        
        response_data = {
            'owners': owners_data,
            'renters': renters_data,
            'labels': labels,
            'period': period
        }
        
        return jsonify({'success': True, 'data': response_data}), 200
        
    except Exception as e:
        print(f"Error getting user growth data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

    # --- API THỐNG KÊ LƯỢT ĐẶT NHÀ THEO LOẠI ---
@admin_bp.route('/api/booking-stats-data/<period>')
@login_required
def get_booking_stats_data(period):
    """API endpoint to get booking statistics data by type (hourly/nightly)"""
    if not isinstance(current_user, Admin):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        from datetime import timedelta
        
        today = datetime.now().date()
        
        # Determine date range based on period
        if period == 'week':
            days = 7
            date_format = 'weekday'
        elif period == 'month':
            days = 30
            date_format = 'day'
        elif period == 'year':
            days = 365
            date_format = 'month'
        else:
            return jsonify({'error': 'Invalid period'}), 400
        
        # Generate data for the specified period
        hourly_data = []
        nightly_data = []
        labels = []
        
        for i in range(days - 1, -1, -1):
            current_date = today - timedelta(days=i)
            
            if period == 'week':
                # Count bookings created on this specific day
                start_datetime = datetime.combine(current_date, datetime.min.time())
                end_datetime = datetime.combine(current_date, datetime.max.time())
                
                # Count hourly bookings (homes with hourly pricing)
                hourly_bookings = db.session.query(Booking).join(Home).filter(
                    Booking.created_at >= start_datetime,
                    Booking.created_at <= end_datetime,
                    Home.price_per_hour.isnot(None),
                    Home.price_per_hour > 0,
                    Booking.status == 'completed'
                ).count()
                
                # Count nightly bookings (homes with nightly pricing)
                nightly_bookings = db.session.query(Booking).join(Home).filter(
                    Booking.created_at >= start_datetime,
                    Booking.created_at <= end_datetime,
                    Home.price_per_night.isnot(None),
                    Home.price_per_night > 0,
                    Booking.status == 'completed'
                ).count()
                
                # Format label for week view
                label = current_date.strftime('%a %d')  # Mon 01
                
            elif period == 'month':
                # Count bookings created on this specific day
                start_datetime = datetime.combine(current_date, datetime.min.time())
                end_datetime = datetime.combine(current_date, datetime.max.time())
                
                # Count hourly bookings
                hourly_bookings = db.session.query(Booking).join(Home).filter(
                    Booking.created_at >= start_datetime,
                    Booking.created_at <= end_datetime,
                    Home.price_per_hour.isnot(None),
                    Home.price_per_hour > 0,
                    Booking.status == 'completed'
                ).count()
                
                # Count nightly bookings
                nightly_bookings = db.session.query(Booking).join(Home).filter(
                    Booking.created_at >= start_datetime,
                    Booking.created_at <= end_datetime,
                    Home.price_per_night.isnot(None),
                    Home.price_per_night > 0,
                    Booking.status == 'completed'
                ).count()
                
                # Format label for month view (show every 3rd day to avoid crowding)
                if i % 3 == 0 or i == 0:
                    label = current_date.strftime('%d')
                else:
                    label = ''
                    
            else:  # year
                # For year view, group by week and show weekly totals
                week_start = current_date - timedelta(days=current_date.weekday())
                week_end = week_start + timedelta(days=6)
                
                start_datetime = datetime.combine(week_start, datetime.min.time())
                end_datetime = datetime.combine(week_end, datetime.max.time())
                
                # Count hourly bookings for the week
                hourly_bookings = db.session.query(Booking).join(Home).filter(
                    Booking.created_at >= start_datetime,
                    Booking.created_at <= end_datetime,
                    Home.price_per_hour.isnot(None),
                    Home.price_per_hour > 0,
                    Booking.status == 'completed'
                ).count()
                
                # Count nightly bookings for the week
                nightly_bookings = db.session.query(Booking).join(Home).filter(
                    Booking.created_at >= start_datetime,
                    Booking.created_at <= end_datetime,
                    Home.price_per_night.isnot(None),
                    Home.price_per_night > 0,
                    Booking.status == 'completed'
                ).count()
                
                # Format label for year view (show every 30th day)
                if i % 30 == 0 or i == 0:
                    label = current_date.strftime('%b')
                else:
                    label = ''
            
            hourly_data.append(hourly_bookings)
            nightly_data.append(nightly_bookings)
            labels.append(label)
        
        # For year view, we need to aggregate data by weeks to reduce data points
        if period == 'year':
            # Group data by weeks (every 7 days)
            weekly_hourly = []
            weekly_nightly = []
            weekly_labels = []
            
            for i in range(0, len(hourly_data), 7):
                week_hourly = sum(hourly_data[i:i+7])
                week_nightly = sum(nightly_data[i:i+7])
                week_label = labels[i] if labels[i] else f'W{i//7 + 1}'
                
                weekly_hourly.append(week_hourly)
                weekly_nightly.append(week_nightly)
                weekly_labels.append(week_label)
            
            hourly_data = weekly_hourly
            nightly_data = weekly_nightly
            labels = weekly_labels
        
        response_data = {
            'hourly': hourly_data,
            'nightly': nightly_data,
            'labels': labels,
            'period': period
        }
        
        return jsonify({'success': True, 'data': response_data}), 200
        
    except Exception as e:
        print(f"Error getting booking stats data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# --- API THỐNG KÊ DOANH THU THEO THÁNG ---
@admin_bp.route('/api/revenue-stats-data/<int:year>')
@login_required
def get_revenue_stats_data(year):
    """API endpoint to get monthly revenue statistics data"""
    if not isinstance(current_user, Admin):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        from datetime import date
        from sqlalchemy import extract, func
        
        # Validate year - only allow 2025
        if year != 2025:
            return jsonify({'error': 'Only year 2025 is supported'}), 400
        
        # Get current date to determine which months to show
        current_date = date.today()
        current_year = current_date.year
        current_month = current_date.month if current_year == 2025 else 12
        
        # Generate data for all 12 months
        monthly_data = {
            'hourly_revenue': [],
            'nightly_revenue': [],
            'total_revenue': [],
            'labels': [],
            'year': year
        }
        
        # Always process all 12 months
        for month in range(1, 13):
            # Calculate revenue for hourly bookings in this month
            hourly_revenue = db.session.query(
                func.sum(Booking.total_price * 0.1)  # 10% commission
            ).join(Home).filter(
                extract('year', Booking.created_at) == year,
                extract('month', Booking.created_at) == month,
                Home.price_per_hour.isnot(None),
                Home.price_per_hour > 0,
                Booking.status == 'completed'
            ).scalar() or 0
            
            # Calculate revenue for nightly bookings in this month
            nightly_revenue = db.session.query(
                func.sum(Booking.total_price * 0.1)  # 10% commission
            ).join(Home).filter(
                extract('year', Booking.created_at) == year,
                extract('month', Booking.created_at) == month,
                Home.price_per_night.isnot(None),
                Home.price_per_night > 0,
                Booking.status == 'completed'
            ).scalar() or 0
            
            # Convert to float and ensure non-negative
            hourly_revenue = max(float(hourly_revenue), 0)
            nightly_revenue = max(float(nightly_revenue), 0)
            total_revenue = hourly_revenue + nightly_revenue
            
            monthly_data['hourly_revenue'].append(hourly_revenue)
            monthly_data['nightly_revenue'].append(nightly_revenue)
            monthly_data['total_revenue'].append(total_revenue)
            
            # Add month label
            month_names = [
                'Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6',
                'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'
            ]
            monthly_data['labels'].append(month_names[month - 1])
        
        # Add metadata about which months are shown
        monthly_data['months_shown'] = current_month if current_year == 2025 else 12
        monthly_data['current_month'] = current_month if current_year == 2025 else 12
        
        return jsonify({'success': True, 'data': monthly_data}), 200
        
    except Exception as e:
        print(f"Error getting revenue stats data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/renter/<int:renter_id>/toggle-status', methods=['POST'])
@login_required
def toggle_renter_status(renter_id):
    if not isinstance(current_user, Admin):
        return jsonify({'error': 'Bạn không có quyền thực hiện thao tác này'}), 401
    
    renter = Renter.query.get_or_404(renter_id)
    reason = request.form.get('reason')
    
    try:
        renter.is_active = not renter.is_active
        if not renter.is_active:  # Nếu vô hiệu hóa
            if not reason:
                return jsonify({'error': 'Vui lòng nhập lý do vô hiệu hóa'}), 400
            # Note: Renter model may not have reason field, add if needed
            if hasattr(renter, 'reason'):
                renter.reason = reason
        
        db.session.commit()
        message = 'Kích hoạt tài khoản renter thành công!' if renter.is_active else 'Vô hiệu hóa tài khoản renter thành công!'
        return jsonify({
            'success': True,
            'message': message
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/renter/<int:renter_id>/reason')
@login_required
def get_renter_reason(renter_id):
    if not isinstance(current_user, Admin):
        return jsonify({'error': 'Unauthorized'}), 401
    
    renter = Renter.query.get_or_404(renter_id)
    reason = getattr(renter, 'reason', 'Không có lý do') if hasattr(renter, 'reason') else 'Không có lý do'
    return jsonify({'reason': reason})

# Unified user action endpoints for the new dashboard
@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    if not isinstance(current_user, Admin):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        user_type = data.get('user_type')
        action = data.get('action')
        
        if user_type == 'owner':
            user = Owner.query.get_or_404(user_id)
            model_name = 'Owner'
        elif user_type == 'renter':
            user = Renter.query.get_or_404(user_id)
            model_name = 'Renter'
        elif user_type == 'admin':
            user = Admin.query.get_or_404(user_id)
            model_name = 'Admin'
            # Prevent non-super admins from toggling admin status
            if not current_user.is_super_admin:
                return jsonify({'error': 'Chỉ Super Admin mới có thể thay đổi trạng thái Admin'}), 403
        else:
            return jsonify({'error': 'Invalid user type'}), 400
        
        if action == 'activate':
            user.is_active = True
            if hasattr(user, 'reason'):
                user.reason = None
            message = f'{model_name} đã được kích hoạt thành công'
        elif action == 'deactivate':
            user.is_active = False
            reason = data.get('reason', 'Không có lý do')
            if hasattr(user, 'reason'):
                user.reason = reason
            message = f'{model_name} đã được vô hiệu hóa thành công'
        else:
            return jsonify({'error': 'Invalid action'}), 400
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>/delete', methods=['DELETE'])
@login_required
def delete_user(user_id):
    if not isinstance(current_user, Admin):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        user_type = data.get('user_type')
        
        if user_type == 'owner':
            user = Owner.query.get_or_404(user_id)
            model_name = 'Owner'
            # Check if owner has active bookings or rooms
            if user.rooms.count() > 0:
                return jsonify({'error': 'Không thể xóa Owner có nhà đang hoạt động'}), 400
        elif user_type == 'renter':
            user = Renter.query.get_or_404(user_id)
            model_name = 'Renter'
            # Check if renter has active bookings
            active_bookings = Booking.query.filter_by(
                renter_id=user_id,
                status='confirmed'
            ).count()
            if active_bookings > 0:
                return jsonify({'error': 'Không thể xóa Renter có booking đang hoạt động'}), 400
        elif user_type == 'admin':
            user = Admin.query.get_or_404(user_id)
            model_name = 'Admin'
            # Prevent deletion of current user and super admin restrictions
            if user.id == current_user.id:
                return jsonify({'error': 'Không thể xóa chính mình'}), 400
            if not current_user.is_super_admin:
                return jsonify({'error': 'Chỉ Super Admin mới có thể xóa Admin'}), 403
            if user.is_super_admin and Admin.query.filter_by(is_super_admin=True).count() <= 1:
                return jsonify({'error': 'Không thể xóa Super Admin cuối cùng'}), 400
        else:
            return jsonify({'error': 'Invalid user type'}), 400
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{model_name} đã được xóa thành công'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# @admin_bp.route('/advanced-visualize')
# @login_required
# def advanced_visualize():
#     if not isinstance(current_user, Admin):
#         flash("You are not authorized!", "danger")
#         return redirect(url_for('auth.login'))
#     return render_template('admin/advanced_visualize.html')

@admin_bp.route('/api/owner-revenue')
@login_required
def api_owner_revenue():
    if not isinstance(current_user, Admin):
        return jsonify({'error': 'Unauthorized'}), 401
    from sqlalchemy import func, distinct
    from app.models.models import Owner, Room, Booking, Review
    owners = db.session.query(
        Owner.id,
        Owner.full_name,
        func.count(distinct(Room.id)).label('room_count'),
        func.count(Booking.id).label('booking_count'),
        func.sum(Booking.total_price).label('total_revenue'),
        func.avg(Review.rating).label('avg_rating')
    ).join(Room, Owner.id == Room.owner_id) \
     .outerjoin(Booking, Room.id == Booking.room_id) \
     .outerjoin(Review, Room.id == Review.room_id) \
     .filter(Room.is_active == True) \
     .group_by(Owner.id, Owner.full_name) \
     .order_by(func.sum(Booking.total_price).desc()) \
     .all()
    result = []
    for o in owners:
        result.append({
            'id': o.id,
            'full_name': o.full_name or f'Chủ nhà {o.id}',
            'room_count': o.room_count,
            'booking_count': o.booking_count,
            'total_revenue': int(o.total_revenue) if o.total_revenue else 0,
            'avg_rating': round(o.avg_rating, 1) if o.avg_rating else 0.0
        })
    return jsonify({'success': True, 'data': result}), 200

@admin_bp.route('/api/room/<int:room_id>/commission', methods=['POST'])
@login_required
def update_room_commission(room_id):
    if not isinstance(current_user, Admin):
        return jsonify({'success': False, 'error': 'Bạn không có quyền thực hiện thao tác này!'}), 403
    data = request.get_json()
    percent = data.get('commission_percent')
    if percent is None:
        return jsonify({'success': False, 'error': 'Thiếu dữ liệu phần trăm hoa hồng!'}), 400
    try:
        percent = float(percent)
        if percent < 0 or percent > 100:
            return jsonify({'success': False, 'error': 'Phần trăm hoa hồng phải từ 0 đến 100!'}), 400
    except Exception:
        return jsonify({'success': False, 'error': 'Dữ liệu hoa hồng không hợp lệ!'}), 400
    room = Room.query.get(room_id)
    if not room:
        return jsonify({'success': False, 'error': 'Không tìm thấy phòng!'}), 404
    room.commission_percent = percent
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Cập nhật hoa hồng thành công!', 'commission_percent': percent})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Lỗi khi lưu dữ liệu: ' + str(e)}), 500

@admin_bp.route('/api/owner/<int:owner_id>/commission', methods=['POST'])
@login_required
def update_owner_commission(owner_id):
    if not isinstance(current_user, Admin):
        return jsonify({'success': False, 'error': 'Bạn không có quyền thực hiện thao tác này!'}), 403
    data = request.get_json()
    percent = data.get('commission_percent')
    if percent is None:
        return jsonify({'success': False, 'error': 'Thiếu dữ liệu phần trăm hoa hồng!'}), 400
    try:
        percent = float(percent)
        if percent < 0 or percent > 100:
            return jsonify({'success': False, 'error': 'Phần trăm hoa hồng phải từ 0 đến 100!'}), 400
    except Exception:
        return jsonify({'success': False, 'error': 'Dữ liệu hoa hồng không hợp lệ!'}), 400
    owner = Owner.query.get(owner_id)
    if not owner:
        return jsonify({'success': False, 'error': 'Không tìm thấy owner!'}), 404
    rooms = owner.rooms
    if not rooms:
        return jsonify({'success': False, 'error': 'Owner chưa có phòng nào!'}), 400
    for room in rooms:
        room.commission_percent = percent
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Cập nhật hoa hồng cho tất cả phòng thành công!', 'commission_percent': percent})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Lỗi khi lưu dữ liệu: ' + str(e)}), 500


