# routes/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Owner, Admin
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
            
            flash("Owner created successfully!", "success")
            return redirect(url_for('admin.dashboard'))
        except IntegrityError:
            db.session.rollback()
            flash("Error: A unique field already exists. Please use different information.", "danger")
            return render_template('admin/create_owner.html')
            
    return render_template('admin/create_owner.html')