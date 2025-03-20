# routes/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user, login_required
from models import Admin, Owner, Renter, db
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import json
from flask import current_app
from urllib.parse import urlencode
import secrets

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

def get_google_provider_cfg():
    return requests.get(current_app.config['GOOGLE_DISCOVERY_URL']).json()

# @auth_bp.route('/login/google')
# def login_google():
#     # Find out what URL to hit for Google login
#     google_provider_cfg = get_google_provider_cfg()
#     authorization_endpoint = google_provider_cfg["authorization_endpoint"]

#     # Generate random state for CSRF protection
#     session["google_state"] = secrets.token_urlsafe(16)

#     # Use hardcoded callback URL (must match exactly what's in Google Cloud Console)
#     callback_url = "http://127.0.0.1:5000/auth/callback/google"
    
#     # Debug: Print the callback URL
#     print(f"Using callback URL: {callback_url}")
    
#     request_uri = authorization_endpoint + "?" + urlencode({
#         'client_id': current_app.config['GOOGLE_CLIENT_ID'],
#         'redirect_uri': callback_url,
#         'scope': 'openid email profile',
#         'response_type': 'code',
#         'state': session["google_state"],
#         'prompt': 'select_account'
#     })
    
#     return redirect(request_uri)

# @auth_bp.route('/callback/google')  # This becomes /auth/callback/google with prefix
# def callback_google():
#     # Verify state parameter
#     if request.args.get('state') != session.get("google_state"):
#         flash("Authentication failed: Invalid state parameter", "danger")
#         return redirect(url_for('auth.login'))
    
#     code = request.args.get("code")
    
#     google_provider_cfg = get_google_provider_cfg()
#     token_endpoint = google_provider_cfg["token_endpoint"]
    
#     # Use the same hardcoded callback URL
#     callback_url = "http://127.0.0.1:5000/auth/callback/google"
    
#     # Debug: Print the callback URL
#     print(f"Token exchange using callback URL: {callback_url}")
    
#     # Exchange code for tokens
#     token_response = requests.post(
#         token_endpoint,
#         data={
#             'client_id': current_app.config['GOOGLE_CLIENT_ID'],
#             'client_secret': current_app.config['GOOGLE_CLIENT_SECRET'],
#             'code': code,
#             'grant_type': 'authorization_code',
#             'redirect_uri': callback_url
#         }
#     )
    
#     # Parse the tokens
#     token_json = token_response.json()
    
#     # Get the ID token from Google
#     id_token = token_json['id_token']
#     access_token = token_json['access_token']
    
#     # Get user info from Google
#     userinfo_endpoint = google_provider_cfg['userinfo_endpoint']
#     userinfo_response = requests.get(
#         userinfo_endpoint, 
#         headers={'Authorization': f'Bearer {access_token}'}
#     )
    
#     # Process the user information
#     userinfo = userinfo_response.json()
    
#     # Get the user's Google Account email
#     google_id = userinfo['sub']
#     google_email = userinfo['email']
#     google_name = userinfo.get('name', '')
    
#     # Check if this Google account is already linked to a user
#     existing_renter = Renter.query.filter_by(google_id=google_id).first()
    
#     if existing_renter:
#         # User exists, log them in
#         login_user(existing_renter)
#         session['user_role'] = 'renter'
#         flash("Successfully logged in with Google!", "success")
#         return redirect(url_for('home'))
#     else:
#         # User doesn't exist, store info in session and redirect to complete profile
#         session['google_id'] = google_id
#         session['google_email'] = google_email
#         session['google_name'] = google_name
#         return redirect(url_for('auth.complete_google_signup'))

# @auth_bp.route('/complete-google-signup', methods=['GET', 'POST'])
# def complete_google_signup():
#     # Check if we have Google data in session
#     if not session.get('google_id') or not session.get('google_email'):
#         flash("Google authentication data missing", "danger")
#         return redirect(url_for('auth.login'))
    
#     # Pre-populate form with Google data
#     form_data = {
#         'email': session.get('google_email', ''),
#         'full_name': session.get('google_name', '')
#     }
    
#     if request.method == 'POST':
#         # Get form data
#         username = request.form.get('username')
#         full_name = request.form.get('full_name')
#         phone = request.form.get('phone')
#         personal_id = request.form.get('personal_id')
        
#         # Validate required fields
#         if not all([username, full_name, phone, personal_id]):
#             flash("All fields are required", "danger")
#             form_data = {
#                 'username': username,
#                 'full_name': full_name,
#                 'phone': phone,
#                 'personal_id': personal_id,
#                 'email': session.get('google_email', '')
#             }
#             return render_template('auth/complete_google_signup.html', form_data=form_data)
        
#         # Check if username exists
#         if Renter.query.filter_by(username=username).first() or Owner.query.filter_by(username=username).first() or Admin.query.filter_by(username=username).first():
#             flash("Username already exists", "danger")
#             return render_template('auth/complete_google_signup.html', form_data=form_data)
        
#         # Check if phone exists
#         if Renter.query.filter_by(phone=phone).first() or Owner.query.filter_by(phone=phone).first():
#             flash("Phone number already exists", "danger")
#             return render_template('auth/complete_google_signup.html', form_data=form_data)
        
#         # Check if personal_id exists
#         if Renter.query.filter_by(personal_id=personal_id).first() or Owner.query.filter_by(personal_id=personal_id).first():
#             flash("Personal ID already exists", "danger")
#             return render_template('auth/complete_google_signup.html', form_data=form_data)
        
#         # Create new renter with Google data
#         new_renter = Renter(
#             username=username,
#             email=session['google_email'],
#             full_name=full_name,
#             phone=phone,
#             personal_id=personal_id,
#             google_id=session['google_id'],
#         )
        
#         # Generate a random password for Google users - they'll use Google to login
#         random_password = secrets.token_urlsafe(16)
#         new_renter.set_password(random_password)
        
#         db.session.add(new_renter)
#         db.session.commit()
        
#         # Log in the new user
#         login_user(new_renter)
#         session['user_role'] = 'renter'
        
#         # Clear Google session data
#         session.pop('google_id', None)
#         session.pop('google_email', None)
#         session.pop('google_name', None)
        
#         flash("Your account has been created successfully!", "success")
#         return redirect(url_for('home'))
    
#     # GET request - render the form
#     return render_template('auth/complete_google_signup.html', form_data=form_data)
