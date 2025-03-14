# routes/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Owner, User
from sqlalchemy.exc import IntegrityError
from routes.renter import get_rank_info

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin():
        flash("You are not authorized!", "danger")
        return redirect(url_for('auth.login'))
    owners = Owner.query.all()
    return render_template('admin/dashboard.html', owners=owners)

@admin_bp.route('/create_owner', methods=['GET', 'POST'])
@login_required
def create_owner():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        personal_id = request.form.get('personal_id')
        username = request.form.get('username')
        password = request.form.get('password')

        if not all([full_name, email, personal_id, username, password]):
            flash("All required fields must be filled!", "danger")
            return render_template('admin/create_owner.html')

        try:
            # Tạo Owner
            new_owner = Owner(
                full_name=full_name,
                email=email,
                phone=phone,
                personal_id=personal_id,
                username=username
            )
            new_owner.set_password(password)
            db.session.add(new_owner)
            db.session.commit()

            # Tạo entry cho User với role 'owner'
            new_user = User(
                username=username,
                email=email,
                full_name=full_name,
                phone=phone,
                personal_id=personal_id,
                role='owner'
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            flash("Owner created successfully in both Owner and User tables!", "success")
            return redirect(url_for('admin.dashboard'))

        except IntegrityError as e:
            db.session.rollback()
            flash("Error: The personal ID (or other unique field) already exists. Please use a different one.", "danger")
            return render_template('admin/create_owner.html')

    return render_template('admin/create_owner.html')