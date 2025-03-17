from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from flask_login import login_user, logout_user, current_user, login_required
from models import Admin, Owner, Renter, db
from urllib.parse import urlparse

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    role = "renter"
    """Handle renter registration"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        personal_id = request.form.get('personal_id')

        # Validate form data
        if not all([username, email, password, full_name, phone, personal_id]):
            flash('All fields are required', 'danger')
            return render_template('auth/register.html')
            
        # Check if username, email, or personal_id already exists in Renter table
        if Renter.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('auth/register.html')
            
        if Renter.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return render_template('auth/register.html')
            
        if Renter.query.filter_by(personal_id=personal_id).first():
            flash('Personal ID already exists', 'danger')
            return render_template('auth/register.html')
        
        # Create new renter
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
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        # Try to find user in Admin table
        user = Admin.query.filter_by(username=username).first()
        role = None
        if user and user.check_password(password):
            role = 'admin'
        else:
            # Try in Owner table
            user = Owner.query.filter_by(username=username).first()
            if user and user.check_password(password):
                role = 'owner'
            else:
                # Try in Renter table
                user = Renter.query.filter_by(username=username).first()
                if user and user.check_password(password):
                    role = 'renter'
        
        if not user:
            flash('Invalid username or password!', 'danger')
            return render_template('auth/login.html')
            
        login_user(user, remember=remember)
        session['user_role'] = role  # Save user role in session
        
        # Redirect based on role
        if role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif role == 'owner':
            return redirect(url_for('owner.dashboard'))
        else:
            return redirect(url_for('renter.dashboard'))
        
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))