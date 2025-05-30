from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from models import db, Admin, Owner, Renter, Homestay
from sqlalchemy.exc import IntegrityError
import os
from werkzeug.utils import secure_filename

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
    owners = Owner.query.all()
    return render_template('admin/dashboard.html', owners=owners)

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
                
                if avatar and avatar.filename != '':
                    if not allowed_file(avatar.filename):
                        flash("File type not allowed. Please use: png, jpg, jpeg, gif, or webp", "danger")
                        return redirect(url_for('admin.profile'))
                    
                    try:
                        # Ensure upload folder exists
                        upload_folder = current_app.config['UPLOAD_FOLDER']
                        print(f"Upload folder path: {upload_folder}")
                        
                        if not os.path.exists(upload_folder):
                            print(f"Creating upload folder: {upload_folder}")
                            os.makedirs(upload_folder, exist_ok=True)
                        
                        # Generate secure filename and save file
                        filename = secure_filename(avatar.filename)
                        filepath = os.path.join(upload_folder, filename)
                        print(f"Saving file to: {filepath}")
                        
                        # Save file
                        avatar.save(filepath)
                        
                        if not os.path.exists(filepath):
                            raise Exception(f"File was not saved successfully to {filepath}")
                        
                        print(f"File saved successfully. Size: {os.path.getsize(filepath)} bytes")
                        
                        # Delete old avatar if exists
                        if current_user.avatar:
                            old_avatar_path = os.path.join(upload_folder, current_user.avatar)
                            if os.path.exists(old_avatar_path):
                                os.remove(old_avatar_path)
                                print(f"Deleted old avatar: {old_avatar_path}")
                        
                        # Update the avatar field in the admin's profile
                        current_user.avatar = filename
                        print(f"Updated admin avatar in database: {filename}")
                        
                    except Exception as e:
                        print(f"Error during file operations: {str(e)}")
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
    total_homestays = Homestay.query.count() or 0
    
    return render_template("user/profile.html", 
                          total_users=total_users,
                          total_homestays=total_homestays)

@admin_bp.route('/create_owner', methods=['GET', 'POST'])
@login_required
def create_owner():
    if not isinstance(current_user, Admin):
        flash("You are not authorized!", "danger")
        return redirect(url_for('auth.login'))
    
    form_data = {}
    
    if request.method == 'POST':
        full_name   = request.form.get('full_name')
        username    = request.form.get('username')
        email       = request.form.get('email')
        phone       = request.form.get('phone')
        personal_id = request.form.get('personal_id')
        password    = request.form.get('password')
        confirm_pw  = request.form.get('confirm_password')
        
        # Lưu dữ liệu đã nhập vào form_data
        form_data = {
            'full_name': full_name,
            'username': username,
            'email': email,
            'phone': phone,
            'personal_id': personal_id
        }
        
        # Kiểm tra tất cả các trường bắt buộc
        if not all([full_name, username, email, phone, personal_id, password, confirm_pw]):
            flash("All required fields must be filled!", "danger")
            return render_template('admin/create_owner.html', form_data=form_data)
        
        # Kiểm tra mật khẩu khớp
        if password != confirm_pw:
            flash("Passwords do not match", "danger")
            return render_template('admin/create_owner.html', form_data=form_data)
        
        # Kiểm tra trùng lặp trên toàn hệ thống
        if (Admin.query.filter_by(username=username).first() or 
            Owner.query.filter_by(username=username).first() or 
            Renter.query.filter_by(username=username).first()):
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
        
        if (Owner.query.filter_by(personal_id=personal_id).first() or 
            Renter.query.filter_by(personal_id=personal_id).first()):
            flash("Personal ID already exists", "danger")
            return render_template('admin/create_owner.html', form_data=form_data)
        
        try:
            new_owner = Owner(
                full_name=full_name,
                username=username,
                email=email,
                phone=phone,
                personal_id=personal_id
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
    
    homestay = Homestay.query.get_or_404(homestay_id)
    return render_template('admin/homestay_details.html', homestay=homestay)

@admin_bp.route('/homestay/<int:homestay_id>/toggle-status', methods=['POST'])
@login_required
def toggle_homestay_status(homestay_id):
    if not isinstance(current_user, Admin):
        flash("Bạn không có quyền thực hiện thao tác này!", "danger")
        return redirect(url_for('auth.login'))
    
    homestay = Homestay.query.get_or_404(homestay_id)
    
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
