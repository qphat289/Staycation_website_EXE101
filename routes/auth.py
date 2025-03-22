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
    
    # Initialize empty form_data
    form_data = {}
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Store username for form repopulation if login fails
        form_data = {'username': username}
        
        # Try to find the user by username (only regular users, not Google users)
        admin = Admin.query.filter_by(username=username).first()
        owner = Owner.query.filter_by(username=username).first()
        renter = Renter.query.filter_by(username=username).first()  # Only finds regular users, not Google users
        
        user = admin or owner or renter
        
        if user and user.check_password(password):
            # Valid credentials, log in the user
            login_user(user)
            
            # Set the user role in session
            if admin:
                session['user_role'] = 'admin'
            elif owner:
                session['user_role'] = 'owner'
            elif renter:
                session['user_role'] = 'renter'
                
            # Redirect to the appropriate page
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('home')
                
            return redirect(next_page)
        else:
            # Invalid credentials
            flash("Invalid username or password. Please try again.", "danger")
                
    return render_template('auth/login.html', form_data=form_data)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))

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
        return redirect(url_for('home'))
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

# Add Facebook callback route
@auth_bp.route('/callback/facebook')
def callback_facebook():
    # Verify state parameter
    if request.args.get('state') != session.get("facebook_state"):
        flash("Authentication failed: Invalid state parameter", "danger")
        return redirect(url_for('auth.login'))
    
    # Check for error response
    if request.args.get('error'):
        flash(f"Facebook authorization error: {request.args.get('error_description', 'Unknown error')}", "danger")
        return redirect(url_for('auth.login'))
    
    # Get authorization code
    code = request.args.get("code")
    
    # Prepare for token exchange
    callback_url = current_app.config['FACEBOOK_CALLBACK_URL']
    token_url = "https://graph.facebook.com/v16.0/oauth/access_token"
    
    # Exchange code for access token
    token_response = requests.get(token_url, params={
        'client_id': current_app.config['FACEBOOK_CLIENT_ID'],
        'client_secret': current_app.config['FACEBOOK_CLIENT_SECRET'],
        'code': code,
        'redirect_uri': callback_url
    })
    
    # Parse token response
    token_data = token_response.json()
    
    if 'error' in token_data:
        flash(f"Error getting access token: {token_data.get('error_description', 'Unknown error')}", "danger")
        return redirect(url_for('auth.login'))
    
    # Get access token
    access_token = token_data['access_token']
    
    # Get user info from Facebook Graph API
    user_info_url = "https://graph.facebook.com/me"
    user_response = requests.get(user_info_url, params={
        'fields': 'id,name,email',
        'access_token': access_token
    })
    
    user_info = user_response.json()
    
    # Extract user data
    facebook_id = user_info['id']
    facebook_email = user_info.get('email')  # May be None if user hasn't shared their email
    facebook_name = user_info.get('name', '')
    
    # Check if this Facebook account is already linked to a user
    existing_renter = Renter.query.filter_by(facebook_id=facebook_id).first()
    
    if existing_renter:
        # User exists, log them in
        login_user(existing_renter)
        session['user_role'] = 'renter'
        flash("Successfully logged in with Facebook!", "success")
        return redirect(url_for('home'))
    else:
        # User doesn't exist, store info in session and redirect to complete profile
        session['facebook_id'] = facebook_id
        session['facebook_email'] = facebook_email
        session['facebook_name'] = facebook_name
        return redirect(url_for('auth.complete_facebook_signup'))

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