# routes/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Owner, User

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin():
        flash("You are not authorized!", "danger")
        return redirect(url_for('auth.admin_login'))
    return render_template('admin/dashboard.html')

@admin_bp.route('/create_owner', methods=['GET', 'POST'])
@login_required
def create_owner():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        personal_id = request.form.get('personal_id')
        username = request.form.get('username')  # Lấy username
        password = request.form.get('password')  # Lấy password

        # Kiểm tra trống
        if not all([full_name, email, personal_id, username, password]):
            flash("All required fields must be filled!", "danger")
            return render_template('admin/create_owner.html')

        # Tạo Owner
        new_owner = Owner(
            full_name=full_name,
            email=email,
            phone=phone,
            personal_id=personal_id,
            username=username
        )

        # Gọi set_password để băm mật khẩu cho Owner
        new_owner.set_password(password)

        # Add to Owner table
        db.session.add(new_owner)
        db.session.commit()

        # Also create a User entry for this Owner (to make it a User too)
        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            phone=phone,
            personal_id=personal_id,
            role='owner'  # Set role as 'owner'
        )
        
        # Set password for the user as well
        new_user.set_password(password)

        # Add to User table
        db.session.add(new_user)
        db.session.commit()

        flash("Owner created successfully in both Owner and User tables!", "success")
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/create_owner.html')
