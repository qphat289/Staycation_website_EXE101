from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from models import db, User, ROLE_RENTER, ROLE_OWNER
from urllib.parse import urlparse

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    role = "renter"
    """Handle user registration"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        personal_id = request.form.get('personal_id')  # New field for personal ID

        # Validate form data
        if not all([username, email, password, full_name, phone, personal_id]):
            flash('All fields are required', 'danger')
            return render_template('auth/register.html')
            
        # Check if username, email, or personal_id already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('auth/register.html')
            
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return render_template('auth/register.html')
            
        if User.query.filter_by(personal_id=personal_id).first():
            flash('Personal ID already exists', 'danger')
            return render_template('auth/register.html')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            role=role,
            full_name=full_name,
            phone=phone,
            personal_id=personal_id
        )
        user.set_password(password)
        
        db.session.add(user)
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
        
        user = User.query.filter_by(username=username).first()
        
        # Validate username/password
        if not user or not user.check_password(password):
            flash('Invalid username or password!', 'danger')
            return render_template('auth/login.html')
            
        login_user(user, remember=remember)
        
        # Redirect to next page or appropriate dashboard
        next_page = request.args.get('next')
        
        # If next_page is empty or unsafe, pick a default based on user role
        if not next_page or urlparse(next_page).netloc != '':
            if user.role == 'admin':
                # Adjust if your blueprint is named differently
                next_page = url_for('admin.dashboard')  
            elif user.is_owner():
                next_page = url_for('owner.dashboard')
            else:
                next_page = url_for('renter.dashboard')
                
        return redirect(next_page)
        
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))