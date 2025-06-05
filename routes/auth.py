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
from urllib.parse import urlparse
from sqlalchemy.exc import IntegrityError
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Initialize empty form_data
    form_data = {}
    
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Store form data for repopulating the form
        form_data = {
            'first_name': first_name,
            'last_name': last_name,
            'username': username,
            'email': email,
            'phone': phone
        }
        
        # Validate required fields
        if not all([first_name, last_name, username, email, phone, password, confirm_password]):
            flash('Vui lòng điền đầy đủ thông tin bắt buộc', 'danger')
            return render_template('auth/register.html', form_data=form_data)
        
        # Validate password match
        if password != confirm_password:
            flash('Mật khẩu xác nhận không khớp', 'danger')
            return render_template('auth/register.html', form_data=form_data)
        
        # Check if username exists
        if Renter.query.filter_by(username=username).first():
            flash('Tên đăng nhập đã tồn tại', 'danger')
            return render_template('auth/register.html', form_data=form_data)
        
        # Check if email exists
        if Renter.query.filter_by(email=email).first():
            flash('Email đã được sử dụng', 'danger')
            return render_template('auth/register.html', form_data=form_data)
        
        # Check if phone exists
        if phone and Renter.query.filter_by(phone=phone).first():
            flash('Số điện thoại đã được sử dụng', 'danger')
            return render_template('auth/register.html', form_data=form_data)
        
        # Create new renter
        new_renter = Renter(
            username=username,
            email=email,
            phone=phone,
            full_name=f"{first_name} {last_name}"
        )
        new_renter.set_password(password)
        
        try:
            db.session.add(new_renter)
            db.session.commit()
            flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Có lỗi xảy ra. Vui lòng thử lại.', 'danger')
            return render_template('auth/register.html', form_data=form_data)
    
    # GET request - render form with empty form_data
    return render_template('auth/register.html', form_data=form_data)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_owner():
            return redirect(url_for('owner.dashboard'))
        elif current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('home'))
    
    # Initialize form_data, check for username from URL parameters
    username_param = request.args.get('username', '')
    form_data = {'username': username_param} if username_param else {}
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Store username for form repopulation if login fails
        form_data = {'username': username}
        
        # Try to find the user by username or email (only regular users, not Google users)
        admin = (Admin.query.filter_by(username=username).first() or 
                Admin.query.filter_by(email=username).first())
        owner = (Owner.query.filter_by(username=username).first() or 
                Owner.query.filter_by(email=username).first())
        renter = (Renter.query.filter_by(username=username).first() or 
                 Renter.query.filter_by(email=username).first())
        
        user = admin or owner or renter
        
        if user and user.check_password(password):
            # Valid credentials, log in the user
            login_user(user)
            
            # Set the user role in session
            if isinstance(user, Admin):
                session['user_role'] = 'admin'
                # Kiểm tra và set super admin nếu chưa có super admin nào
                existing_super_admin = Admin.query.filter_by(is_super_admin=True).first()
                if not existing_super_admin:
                    user.is_super_admin = True
                    user.can_manage_admins = True
                    user.can_approve_changes = True
                    user.can_view_all_stats = True
                    user.can_manage_users = True
                    db.session.commit()
                    flash('Bạn đã được set làm Super Admin!', 'success')
                next_page = url_for('admin.dashboard', login_success='1')
                
            elif isinstance(user, Owner):
                session['user_role'] = 'owner'
                next_page = url_for('owner.dashboard', login_success='1')
                
            else:  # Renter
                session['user_role'] = 'renter'
                next_page = url_for('home', login_success='1')
                
            # Override next_page if 'next' parameter exists and is safe
            next_param = request.args.get('next')
            if next_param and not urlparse(next_param).netloc:
                separator = '&' if '?' in next_param else '?'
                next_page = next_param + separator + 'login_success=1'
                
            return redirect(next_page)
        else:
            # Invalid credentials - redirect with error parameter and preserve username
            return redirect(url_for('auth.login', login_error='1', username=username))
                
    return render_template('auth/login.html', form_data=form_data)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home', logout_success='1'))

def get_google_provider_cfg():
    return requests.get(current_app.config['GOOGLE_DISCOVERY_URL']).json()

@auth_bp.route('/login/google')
def login_google():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Generate random state for CSRF protection
    session["google_state"] = secrets.token_urlsafe(16)

    # Use hardcoded callback URL (must match exactly what's in Google Cloud Console)
    callback_url = "http://127.0.0.1:5000/auth/callback/google"
    
    # Debug: Print the callback URL
    print(f"Using callback URL: {callback_url}")
    
    request_uri = authorization_endpoint + "?" + urlencode({
        'client_id': current_app.config['GOOGLE_CLIENT_ID'],
        'redirect_uri': callback_url,
        'scope': 'openid email profile',
        'response_type': 'code',
        'state': session["google_state"],
        'prompt': 'select_account'
    })
    
    return redirect(request_uri)

@auth_bp.route('/callback/google')  # This becomes /auth/callback/google with prefix
def callback_google():
    # Verify state parameter
    if request.args.get('state') != session.get("google_state"):
        flash("Authentication failed: Invalid state parameter", "danger")
        return redirect(url_for('auth.login'))
    
    code = request.args.get("code")
    
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    
    # Use the same hardcoded callback URL
    callback_url = "http://127.0.0.1:5000/auth/callback/google"
    
    # Debug: Print the callback URL
    print(f"Token exchange using callback URL: {callback_url}")
    
    # Exchange code for tokens
    token_response = requests.post(
        token_endpoint,
        data={
            'client_id': current_app.config['GOOGLE_CLIENT_ID'],
            'client_secret': current_app.config['GOOGLE_CLIENT_SECRET'],
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': callback_url
        }
    )
    
    # Parse the tokens
    token_json = token_response.json()
    
    # Get the ID token from Google
    id_token = token_json['id_token']
    access_token = token_json['access_token']
    
    # Get user info from Google
    userinfo_endpoint = google_provider_cfg['userinfo_endpoint']
    userinfo_response = requests.get(
        userinfo_endpoint, 
        headers={'Authorization': f'Bearer {access_token}'}
    )
    
    # Process the user information
    userinfo = userinfo_response.json()
    
    # Get the user's Google Account email
    google_id = userinfo['sub']
    google_email = userinfo['email']
    google_name = userinfo.get('name', '')
    
    # Check if this Google account is already linked to a user
    existing_renter = Renter.query.filter_by(google_id=google_id).first()
    
    if existing_renter:
        # User exists, log them in
        login_user(existing_renter)
        session['user_role'] = 'renter'
        flash("Successfully logged in with Google!", "success")
        return redirect(url_for('home', login_success='google'))
    else:
        # User doesn't exist, store info in session and redirect to complete profile
        session['google_id'] = google_id
        session['google_email'] = google_email
        session['google_name'] = google_name
        return redirect(url_for('auth.complete_google_signup'))

@auth_bp.route('/complete-google-signup', methods=['GET', 'POST'])
def complete_google_signup():
    # Check if we have Google data in session
    if not session.get('google_id') or not session.get('google_email'):
        flash("Google authentication data missing", "danger")
        return redirect(url_for('auth.login'))
    
    # Pre-populate form with Google data
    form_data = {
        'email': session.get('google_email', ''),
        'google_name': session.get('google_name', ''),
        'full_name': ''  # Empty by default so user can enter their own full name
    }
    
    if request.method == 'POST':
        # Get form data
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        personal_id = request.form.get('personal_id')
        
        # Validate required fields
        if not all([full_name, phone, personal_id]):
            flash("All fields are required", "danger")
            form_data = {
                'full_name': full_name,
                'phone': phone,
                'personal_id': personal_id,
                'email': session.get('google_email', ''),
                'google_name': session.get('google_name', '')
            }
            return render_template('auth/complete_google_signup.html', form_data=form_data)
        
        # Check if phone exists
        if Renter.query.filter_by(phone=phone).first() or Owner.query.filter_by(phone=phone).first():
            flash("Phone number already exists", "danger")
            return render_template('auth/complete_google_signup.html', form_data=form_data)
        
        # Check if personal_id exists
        if Renter.query.filter_by(personal_id=personal_id).first() or Owner.query.filter_by(personal_id=personal_id).first():
            flash("Personal ID already exists", "danger")
            return render_template('auth/complete_google_signup.html', form_data=form_data)
        
        # Create new renter with Google data
        # Note: username field can be NULL for Google users
        new_renter = Renter(
            username=None,  # No regular username for Google users
            google_username=session.get('google_name', 'Google User'),  # Use Google name as google_username
            email=session['google_email'],
            full_name=full_name,  # User-provided full name
            phone=phone,
            personal_id=personal_id,
            google_id=session['google_id'],
        )
        
        # Generate a random password for Google users - they'll use Google to login
        random_password = secrets.token_urlsafe(16)
        new_renter.set_password(random_password)
        
        db.session.add(new_renter)
        db.session.commit()
        
        # Log in the new user
        login_user(new_renter)
        session['user_role'] = 'renter'
        
        # Clear Google session data
        session.pop('google_id', None)
        session.pop('google_email', None)
        session.pop('google_name', None)
        
        flash(f"Your account has been created successfully!", "success")
        return redirect(url_for('home'))
    
    # GET request - render the form
    return render_template('auth/complete_google_signup.html', form_data=form_data)

# Add Facebook login route
@auth_bp.route('/login/facebook')
def login_facebook():
    # Generate random state for CSRF protection
    session["facebook_state"] = secrets.token_urlsafe(16)
    
    # Define Facebook OAuth parameters
    callback_url = current_app.config['FACEBOOK_CALLBACK_URL']
    
    # Facebook authorization URL
    facebook_auth_url = "https://www.facebook.com/v16.0/dialog/oauth"
    
    # Create authorization URL
    request_uri = facebook_auth_url + "?" + urlencode({
        'client_id': current_app.config['FACEBOOK_CLIENT_ID'],
        'redirect_uri': callback_url,
        'state': session["facebook_state"],
        'scope': 'email,public_profile',
        'response_type': 'code'
    })
    
    return redirect(request_uri)

@auth_bp.route('/facebook/callback')
def facebook_callback():
    # Get the authorization code from the request
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        flash(f"Facebook authorization error: {error}", "danger")
        return redirect(url_for('auth.login'))
    
    if not code:
        flash("Authorization failed: No code provided", "danger")
        return redirect(url_for('auth.login'))
    
    # Exchange the code for an access token
    facebook_client_id = current_app.config['FACEBOOK_CLIENT_ID']
    facebook_client_secret = current_app.config['FACEBOOK_CLIENT_SECRET']
    callback_url = current_app.config['FACEBOOK_CALLBACK_URL']
    
    token_url = 'https://graph.facebook.com/v18.0/oauth/access_token'
    token_payload = {
        'client_id': facebook_client_id,
        'client_secret': facebook_client_secret,
        'code': code,
        'redirect_uri': callback_url
    }
    
    try:
        token_response = requests.get(token_url, params=token_payload)
        token_response.raise_for_status()  # Raise exception for HTTP errors
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        
        # Get user information using the access token
        user_info_url = 'https://graph.facebook.com/me'
        user_info_payload = {
            'fields': 'id,name,email',
            'access_token': access_token
        }
        
        user_info_response = requests.get(user_info_url, params=user_info_payload)
        user_info_response.raise_for_status()
        user_info = user_info_response.json()
        
        # Get the user's Facebook ID, name, and email
        facebook_id = user_info.get('id')
        name = user_info.get('name')
        email = user_info.get('email')
        
        if not facebook_id:
            flash("Facebook login failed: Could not retrieve user ID", "danger")
            return redirect(url_for('auth.login'))
        
        existing_renter = Renter.query.filter_by(facebook_id=facebook_id).first()
        
        if existing_renter:
            # User exists, log them in
            login_user(existing_renter)
            session['user_role'] = 'renter'
            flash(f"Welcome back, {name}! You've successfully logged in with Facebook.", "success")
            return redirect(url_for('home', login_success='facebook'))
        else:
            # User doesn't exist, store info in session and redirect to complete profile
            session['facebook_id'] = facebook_id
            session['facebook_email'] = email
            session['facebook_name'] = name
            return redirect(url_for('auth.complete_facebook_signup'))
        
    except requests.exceptions.RequestException as e:
        flash(f"Error during Facebook authentication: {str(e)}", "danger")
        return redirect(url_for('auth.login'))

# Add Facebook signup completion route
@auth_bp.route('/complete-facebook-signup', methods=['GET', 'POST'])
def complete_facebook_signup():
    # Check if we have Facebook data in session
    if not session.get('facebook_id'):
        flash("Facebook authentication data missing", "danger")
        return redirect(url_for('auth.login'))
    
    # Pre-populate form with Facebook data
    form_data = {
        'email': session.get('facebook_email', ''),
        'facebook_name': session.get('facebook_name', ''),
        'full_name': session.get('facebook_name', '')  # Suggest using Facebook name as a starting point
    }
    
    if request.method == 'POST':
        # Get form data
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        personal_id = request.form.get('personal_id')
        email = request.form.get('email')  # Allow them to provide email if not from Facebook
        
        # Validate required fields
        if not all([full_name, phone, personal_id]) or (not session.get('facebook_email') and not email):
            flash("All fields are required", "danger")
            form_data = {
                'full_name': full_name,
                'phone': phone,
                'personal_id': personal_id,
                'email': email or session.get('facebook_email', ''),
                'facebook_name': session.get('facebook_name', '')
            }
            return render_template('auth/complete_facebook_signup.html', form_data=form_data)
        
        # Check if phone exists
        if Renter.query.filter_by(phone=phone).first() or Owner.query.filter_by(phone=phone).first():
            flash("Phone number already exists", "danger")
            return render_template('auth/complete_facebook_signup.html', form_data=form_data)
        
        # Check if personal_id exists
        if Renter.query.filter_by(personal_id=personal_id).first() or Owner.query.filter_by(personal_id=personal_id).first():
            flash("Personal ID already exists", "danger")
            return render_template('auth/complete_facebook_signup.html', form_data=form_data)
        
        # Use email from form if Facebook didn't provide one
        final_email = session.get('facebook_email') or email
        
        # Check if email exists
        if final_email and (Renter.query.filter_by(email=final_email).first() or 
                          Owner.query.filter_by(email=final_email).first() or 
                          Admin.query.filter_by(email=final_email).first()):
            flash("Email already exists", "danger")
            return render_template('auth/complete_facebook_signup.html', form_data=form_data)
        
        # Create new renter with Facebook data
        new_renter = Renter(
            username=None,  # No regular username for Facebook users
            facebook_username=session.get('facebook_name', 'Facebook User'),
            email=final_email,
            full_name=full_name,
            phone=phone,
            personal_id=personal_id,
            facebook_id=session['facebook_id'],
        )
        
        # Generate a random password for Facebook users
        random_password = secrets.token_urlsafe(16)
        new_renter.set_password(random_password)
        
        db.session.add(new_renter)
        db.session.commit()
        
        # Log in the new user
        login_user(new_renter)
        session['user_role'] = 'renter'
        
        # Clear Facebook session data
        session.pop('facebook_id', None)
        session.pop('facebook_email', None)
        session.pop('facebook_name', None)
        
        flash(f"Your account has been created successfully!", "success")
        return redirect(url_for('home'))
    
    # GET request - render the form
    return render_template('auth/complete_facebook_signup.html', form_data=form_data)