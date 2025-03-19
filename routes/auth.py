# routes/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user, login_required
from models import Admin, Owner, Renter, db
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user, login_required
from models import Admin, Owner, Renter, db
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Nếu đã đăng nhập thì về trang home
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    # Tạo sẵn một dict rỗng
    form_data = {}

    if request.method == 'POST':
        full_name   = request.form.get('full_name')
        username    = request.form.get('username')
        email       = request.form.get('email')
        phone       = request.form.get('phone')
        personal_id = request.form.get('personal_id')
        password    = request.form.get('password')
        confirm_pw  = request.form.get('confirm_password')

        # Gán lại vào form_data để nếu lỗi thì template giữ nguyên
        form_data = {
            'full_name': full_name,
            'username': username,
            'email': email,
            'phone': phone,
            'personal_id': personal_id,
        }

        # Kiểm tra trường trống
        if not all([full_name, username, email, phone, personal_id, password, confirm_pw]):
            flash("All fields are required", "danger")
            return render_template('auth/register.html', form_data=form_data)

        # Kiểm tra khớp password
        if password != confirm_pw:
            flash("Passwords do not match", "danger")
            return render_template('auth/register.html', form_data=form_data)

        # Kiểm tra tính duy nhất username, email, phone, personal_id
        if (Admin.query.filter_by(username=username).first() or
            Owner.query.filter_by(username=username).first() or
            Renter.query.filter_by(username=username).first()):
            flash("Username already exists", "danger")
            return render_template('auth/register.html', form_data=form_data)

        if (Admin.query.filter_by(email=email).first() or
            Owner.query.filter_by(email=email).first() or
            Renter.query.filter_by(email=email).first()):
            flash("Email already exists", "danger")
            return render_template('auth/register.html', form_data=form_data)

        if (Owner.query.filter_by(phone=phone).first() or
            Renter.query.filter_by(phone=phone).first()):
            flash("Phone number already exists", "danger")
            return render_template('auth/register.html', form_data=form_data)

        if (Owner.query.filter_by(personal_id=personal_id).first() or
            Renter.query.filter_by(personal_id=personal_id).first()):
            flash("Personal ID already exists", "danger")
            return render_template('auth/register.html', form_data=form_data)

        # Tạo tài khoản Renter
        new_renter = Renter(
            username=username,
            email=email,
            full_name=full_name,
            phone=phone,
            personal_id=personal_id
        )
        new_renter.set_password(password)
        db.session.add(new_renter)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('auth.login'))

    # Nếu là GET, chưa có gì -> form_data rỗng
    return render_template('auth/register.html', form_data=form_data)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        # Tìm user theo thứ tự: Admin -> Owner -> Renter
        user = Admin.query.filter_by(username=username).first()
        role = None
        if user and user.check_password(password):
            role = 'admin'
        else:
            user = Owner.query.filter_by(username=username).first()
            if user and user.check_password(password):
                role = 'owner'
            else:
                user = Renter.query.filter_by(username=username).first()
                if user and user.check_password(password):
                    role = 'renter'
        
        if not user:
            flash('Invalid username or password!', 'danger')
            return render_template('auth/login.html')
            
        # Đăng nhập user
        login_user(user, remember=remember)
        session['user_role'] = role  # Lưu role vào session
        
        # Tạm thời, chuyển hướng về home
        return redirect(url_for('home'))
        
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))
