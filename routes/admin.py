from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Admin, Owner, Renter
from sqlalchemy.exc import IntegrityError

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not isinstance(current_user, Admin):
        flash("You are not authorized!", "danger")
        return redirect(url_for('auth.login'))
    owners = Owner.query.all()
    return render_template('admin/dashboard.html', owners=owners)

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
