import sys
import os
import random
from datetime import datetime, timedelta
from faker import Faker

# Add the project root to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)

from flask import Flask
from config.config import Config
from app.models.models import db, Booking, Home, Renter

# Initialize Faker for generating realistic data
fake = Faker(['vi_VN', 'en_US'])  # Vietnamese and English locales

# Create Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

def calculate_total_hours(start_time, end_time):
    """Calculate total hours between start and end time"""
    return int((end_time - start_time).total_seconds() / 3600)

def calculate_price(home, booking_type, total_hours, start_time):
    """Calculate booking price based on home's enhanced pricing structure"""
    total_price = 0
    
    # Ensure we have valid inputs
    if total_hours <= 0:
        return 0
    
    if booking_type == 'hourly':
        # Use enhanced hourly pricing structure
        if total_hours <= 2 and home.price_first_2_hours:
            total_price = home.price_first_2_hours
        elif home.price_first_2_hours and home.price_per_additional_hour:
            # First 2 hours + additional hours
            total_price = home.price_first_2_hours
            additional_hours = total_hours - 2
            if additional_hours > 0:
                total_price += home.price_per_additional_hour * additional_hours
        elif home.price_per_additional_hour:
            # Fallback to per additional hour rate for all hours
            total_price = home.price_per_additional_hour * total_hours
        else:
            # Fallback default price
            total_price = 50000 * total_hours
        
        # Check for special time-based pricing
        hour = start_time.hour
        if 21 <= hour or hour <= 8:  # Overnight (9 PM to 8 AM)
            if home.price_overnight:
                total_price = max(total_price, home.price_overnight)
        elif 9 <= hour <= 20:  # Daytime (9 AM to 8 PM) 
            if home.price_daytime and total_hours >= 8:  # Full day booking
                total_price = max(total_price, home.price_daytime)
                
    else:  # daily/nightly booking
        if home.price_per_day:
            nights = max(1, total_hours // 24)
            total_price = home.price_per_day * nights
        elif home.price_first_2_hours:
            # Fallback: estimate daily price from hourly
            total_price = home.price_first_2_hours * 12  # Rough daily estimate
        else:
            # Default daily price
            total_price = 500000 * max(1, total_hours // 24)
    
    # Apply seasonal/weekend pricing
    if start_time.weekday() >= 5:  # Weekend (Saturday, Sunday)
        total_price *= 1.2  # 20% weekend surcharge
    
    # Holiday seasons (Tet, summer vacation)
    if start_time.month in [1, 2, 7, 8]:  # Tet and summer
        total_price *= 1.15  # 15% holiday surcharge
    
    # Special event pricing (assuming some dates have events)
    special_dates = [
        (4, 30),   # Liberation Day
        (9, 2),    # National Day
        (12, 24),  # Christmas Eve
        (12, 31),  # New Year's Eve
    ]
    if (start_time.month, start_time.day) in special_dates:
        total_price *= 1.3  # 30% special event surcharge
    
    return int(total_price)

def get_customer_type():
    """Generate customer behavior patterns"""
    customer_types = [
        {
            'type': 'business_traveler',
            'weight': 0.25,
            'booking_preferences': {
                'advance_booking_days': (3, 21),  # Books 3-21 days ahead
                'preferred_duration': (1, 3),     # 1-3 days
                'preferred_times': [(6, 9), (17, 20)],  # Early morning or evening
                'payment_methods': ['credit_card', 'bank_transfer'],
                'cancellation_rate': 0.1
            }
        },
        {
            'type': 'leisure_traveler',
            'weight': 0.35,
            'booking_preferences': {
                'advance_booking_days': (7, 60),   # Books 1 week to 2 months ahead
                'preferred_duration': (2, 7),      # 2-7 days
                'preferred_times': [(10, 16)],     # Daytime check-in
                'payment_methods': ['momo', 'credit_card', 'payos'],
                'cancellation_rate': 0.15
            }
        },
        {
            'type': 'local_resident',
            'weight': 0.2,
            'booking_preferences': {
                'advance_booking_days': (0, 7),    # Last minute to 1 week
                'preferred_duration': (0.25, 1),   # Few hours to 1 day
                'preferred_times': [(18, 23)],     # Evening/night
                'payment_methods': ['momo', 'cash'],
                'cancellation_rate': 0.2
            }
        },
        {
            'type': 'group_traveler',
            'weight': 0.15,
            'booking_preferences': {
                'advance_booking_days': (14, 90),  # 2 weeks to 3 months ahead
                'preferred_duration': (2, 5),      # 2-5 days
                'preferred_times': [(14, 18)],     # Afternoon
                'payment_methods': ['bank_transfer', 'credit_card'],
                'cancellation_rate': 0.25  # Higher due to coordination challenges
            }
        },
        {
            'type': 'staycation',
            'weight': 0.05,
            'booking_preferences': {
                'advance_booking_days': (1, 14),   # 1 day to 2 weeks
                'preferred_duration': (1, 3),      # 1-3 days
                'preferred_times': [(15, 17)],     # Standard check-in
                'payment_methods': ['momo', 'payos'],
                'cancellation_rate': 0.1
            }
        }
    ]
    
    weights = [ct['weight'] for ct in customer_types]
    return random.choices(customer_types, weights=weights)[0]

def generate_seasonal_booking_volume(date):
    """Generate booking volume multiplier based on season"""
    month = date.month
    
    # High season: Summer vacation (June-August), Tet (Jan-Feb), holidays
    if month in [6, 7, 8, 1, 2]:
        return 1.5  # 50% more bookings
    # Medium season: Spring (March-May), Fall (September-November) 
    elif month in [3, 4, 5, 9, 10, 11]:
        return 1.0  # Normal booking volume
    # Low season: December (post-holiday)
    else:
        return 0.7  # 30% fewer bookings

def create_sample_renters():
    """Create sample renters with different profiles"""
    try:
        sample_renters = []
        
        # Create diverse renter profiles
        renter_profiles = [
            # Business travelers
            {
                'username': 'nguyen_business',
                'email': 'nguyen.business@company.com',
                'full_name': 'Nguyễn Văn Doanh',
                'phone': '0901234567'
            },
            {
                'username': 'le_executive',
                'email': 'le.exec@corporation.vn',
                'full_name': 'Lê Thị Quản',
                'phone': '0907654321'
            },
            # Leisure travelers
            {
                'username': 'tran_family',
                'email': 'tran.family@gmail.com',
                'full_name': 'Trần Văn Gia',
                'phone': '0912345678'
            },
            {
                'username': 'pham_tourist',
                'email': 'pham.travel@yahoo.com',
                'full_name': 'Phạm Thị Du',
                'phone': '0923456789'
            },
            {
                'username': 'hoang_backpacker',
                'email': 'hoang.adventure@outlook.com',
                'full_name': 'Hoàng Văn Phượt',
                'phone': '0934567890'
            },
            # Local residents
            {
                'username': 'vu_local',
                'email': 'vu.local@email.vn',
                'full_name': 'Vũ Thị Địa',
                'phone': '0945678901'
            },
            {
                'username': 'dao_resident',
                'email': 'dao.resident@gmail.com',
                'full_name': 'Đào Văn Dân',
                'phone': '0956789012'
            },
            # Group travelers
            {
                'username': 'group_organizer',
                'email': 'organizer@groups.vn',
                'full_name': 'Nhóm Du Lịch ABC',
                'phone': '0967890123'
            },
            {
                'username': 'company_event',
                'email': 'events@company.com',
                'full_name': 'Công Ty Sự Kiện',
                'phone': '0978901234'
            },
            # Staycation users
            {
                'username': 'staycation_user',
                'email': 'staycation@local.vn',
                'full_name': 'Nguyễn Thị Nghỉ',
                'phone': '0989012345'
            }
        ]
        
        for data in renter_profiles:
            renter = Renter(
                username=data['username'],
                email=data['email'],
                full_name=data['full_name'],
                phone=data['phone']
            )
            renter.set_password('password123')  # Default password
            sample_renters.append(renter)
        
        # Save to database
        db.session.bulk_save_objects(sample_renters)
        db.session.commit()
        
        print(f"Created {len(sample_renters)} sample renters with diverse profiles")
        return Renter.query.all()  # Return fresh list from database
        
    except Exception as e:
        print(f"Error creating sample renters: {e}")
        db.session.rollback()
        return None

def generate_payment_reference(payment_method, booking_id):
    """Generate realistic payment reference based on method"""
    if payment_method == 'credit_card':
        return f"CC{random.randint(100000, 999999)}"
    elif payment_method == 'momo':
        return f"MOMO{random.randint(1000000, 9999999)}"
    elif payment_method == 'bank_transfer':
        return f"BANK{random.randint(100000, 999999)}"
    elif payment_method == 'payos':
        return f"PAYOS{random.randint(10000000, 99999999)}"
    elif payment_method == 'cash':
        return f"CASH{booking_id}"
    else:
        return f"PAY{random.randint(100000, 999999)}"

def create_enhanced_booking_data():
    """Create diverse and realistic booking data with customer behavior patterns"""
    
    # Get existing homes and renters
    homes = Home.query.all()
    renters = Renter.query.all()
    
    if not homes:
        print("Error: No homes found in database. Please seed homes first.")
        return
    
    # Create sample renters if none exist
    if not renters:
        print("No renters found. Creating sample renters...")
        renters = create_sample_renters()
        if not renters:
            print("Failed to create sample renters.")
            return
    
    print(f"Found {len(homes)} homes and {len(renters)} renters")
    
    # Filter homes that have valid pricing data
    valid_homes = []
    for home in homes:
        has_pricing = (
            (home.price_first_2_hours and home.price_first_2_hours > 0) or
            (home.price_per_additional_hour and home.price_per_additional_hour > 0) or
            (home.price_overnight and home.price_overnight > 0) or
            (home.price_daytime and home.price_daytime > 0) or
            (home.price_per_day and home.price_per_day > 0)
        )
        if has_pricing:
            valid_homes.append(home)
    
    if not valid_homes:
        print("Warning: No homes with valid pricing found. Using all homes with default pricing.")
        valid_homes = homes
    else:
        print(f"Found {len(valid_homes)} homes with valid pricing data")
    
    homes = valid_homes
    
    # Enhanced booking status options with realistic distribution
    status_options = [
        ('completed', 0.35),     # 35% completed
        ('confirmed', 0.25),     # 25% confirmed/upcoming
        ('cancelled', 0.15),     # 15% cancelled
        ('pending', 0.1),        # 10% pending
        ('active', 0.05),        # 5% currently active
        ('checked_out', 0.05),   # 5% checked out
        ('no_show', 0.03),       # 3% no show
        ('disputed', 0.02)       # 2% disputed
    ]
    
    # Enhanced payment methods with Vietnamese market preferences
    payment_methods = [
        ('momo', 0.35),          # 35% MoMo (very popular in Vietnam)
        ('bank_transfer', 0.25), # 25% bank transfer
        ('payos', 0.18),         # 18% PayOS
        ('credit_card', 0.15),   # 15% credit card
        ('cash', 0.05),          # 5% cash
        ('zalopay', 0.02)        # 2% ZaloPay
    ]
    
    # Enhanced payment status distribution
    payment_status_map = {
        'completed': ['paid', 'paid', 'paid', 'refunded'],
        'confirmed': ['paid', 'paid', 'pending'],
        'cancelled': ['refunded', 'failed', 'cancelled'],
        'pending': ['pending', 'pending', 'failed'],
        'active': ['paid'],
        'checked_out': ['paid'],
        'no_show': ['paid', 'refunded'],
        'disputed': ['paid', 'on_hold', 'refunded']
    }
    
    bookings = []
    
    # Generate bookings for different time periods with varying volume
    base_date = datetime.now() - timedelta(days=365)  # Start 1 year ago
    end_date = datetime.now() + timedelta(days=180)   # 6 months from now
    
    current_date = base_date
    total_bookings_created = 0
    
    while current_date < end_date:
        # Calculate daily booking volume based on season and day of week
        seasonal_multiplier = generate_seasonal_booking_volume(current_date)
        
        # Weekend effect
        if current_date.weekday() >= 5:  # Weekend
            day_multiplier = 1.4
        else:
            day_multiplier = 1.0
        
        # Base bookings per day
        base_bookings_per_day = 3
        daily_bookings = int(base_bookings_per_day * seasonal_multiplier * day_multiplier)
        daily_bookings = max(1, daily_bookings)  # At least 1 booking per day
        
        # Generate bookings for this day
        for _ in range(daily_bookings):
            if total_bookings_created >= 400:  # Limit total bookings
                break
                
            # Select random home and renter
            home = random.choice(homes)
            renter = random.choice(renters)
            
            # Get customer behavior pattern
            customer_profile = get_customer_type()
            prefs = customer_profile['booking_preferences']
            
            # Generate booking date based on customer behavior
            advance_days = random.randint(*prefs['advance_booking_days'])
            if current_date <= datetime.now():
                # Historical booking
                booking_created_date = current_date - timedelta(days=advance_days)
                start_time = current_date
            else:
                # Future booking
                booking_created_date = datetime.now() - timedelta(days=advance_days)
                start_time = current_date
            
            # Adjust start time based on customer preferences
            preferred_time_ranges = prefs['preferred_times']
            time_range = random.choice(preferred_time_ranges)
            start_hour = random.randint(time_range[0], time_range[1])
            start_time = start_time.replace(hour=start_hour, minute=random.choice([0, 30]))
            
            # Determine booking type and duration based on customer profile
            duration_range = prefs['preferred_duration']
            if duration_range[1] <= 1:  # Hourly booking
                booking_type = 'hourly'
                duration_hours = random.uniform(duration_range[0], duration_range[1]) * 24
                duration_hours = max(2, int(duration_hours))  # Minimum 2 hours
            else:  # Daily booking
                booking_type = 'daily'
                duration_days = random.uniform(duration_range[0], duration_range[1])
                duration_hours = max(24, int(duration_days * 24))
            
            end_time = start_time + timedelta(hours=duration_hours)
            
            # Calculate pricing
            total_hours = calculate_total_hours(start_time, end_time)
            total_price = calculate_price(home, booking_type, total_hours, start_time)
            
            # Apply customer-specific pricing adjustments
            if customer_profile['type'] == 'group_traveler':
                total_price *= 1.1  # 10% group surcharge
            elif customer_profile['type'] == 'business_traveler':
                total_price *= 1.05  # 5% business rate
            elif customer_profile['type'] == 'local_resident' and booking_type == 'hourly':
                total_price *= 0.95  # 5% local discount for short bookings
            
            # Ensure minimum price
            if total_price < 20000:  # Minimum 20,000 VND
                total_price = 20000
            
            # Determine booking status based on timing and customer behavior
            if start_time < datetime.now() - timedelta(days=1):
                # Past bookings
                if random.random() < prefs['cancellation_rate']:
                    status = 'cancelled'
                else:
                    status = random.choices(['completed', 'no_show'], weights=[0.95, 0.05])[0]
            elif start_time < datetime.now() + timedelta(hours=6):
                # Current/very near future
                status = random.choices(['active', 'checked_out', 'confirmed'], weights=[0.4, 0.3, 0.3])[0]
            else:
                # Future bookings
                if random.random() < prefs['cancellation_rate']:
                    status = 'cancelled'
                else:
                    status = random.choices(['confirmed', 'pending'], weights=[0.8, 0.2])[0]
            
            # Choose payment method based on customer profile
            preferred_methods = prefs['payment_methods']
            payment_method = random.choice(preferred_methods)
            
            # Choose payment status
            payment_status = random.choice(payment_status_map[status])
            
            # Generate payment details
            payment_date = None
            payment_reference = None
            
            if payment_status in ['paid', 'refunded', 'on_hold']:
                if booking_type == 'daily':
                    # Daily bookings usually paid in advance
                    payment_date = booking_created_date + timedelta(hours=random.randint(1, 48))
                else:
                    # Hourly bookings might be paid closer to check-in
                    payment_date = start_time - timedelta(hours=random.randint(1, 24))
                payment_reference = generate_payment_reference(payment_method, total_bookings_created + 1)
            elif payment_status == 'failed':
                payment_date = booking_created_date + timedelta(minutes=random.randint(5, 120))
                payment_reference = generate_payment_reference(payment_method, total_bookings_created + 1)
            
            # Create booking
            booking = Booking(
                start_time=start_time,
                end_time=end_time,
                total_hours=total_hours,
                total_price=total_price,
                status=status,
                home_id=home.id,
                renter_id=renter.id,
                payment_status=payment_status,
                payment_date=payment_date,
                payment_method=payment_method,
                payment_reference=payment_reference,
                booking_type=booking_type,
                created_at=booking_created_date
            )
            
            bookings.append(booking)
            total_bookings_created += 1
        
        current_date += timedelta(days=1)
        
        if total_bookings_created >= 400:
            break
    
    # Add special scenario bookings
    special_bookings = create_special_scenario_bookings(homes, renters)
    bookings.extend(special_bookings)
    
    return bookings

def create_special_scenario_bookings(homes, renters):
    """Create special scenario bookings for testing various edge cases and realistic situations"""
    special_bookings = []
    
    if not homes or not renters:
        return special_bookings
    
    # Scenario 1: Corporate long-term booking (1 month)
    home = random.choice(homes)
    renter = random.choice(renters)
    start_time = datetime.now() - timedelta(days=60)
    end_time = start_time + timedelta(days=30)
    total_hours = calculate_total_hours(start_time, end_time)
    total_price = calculate_price(home, 'daily', total_hours, start_time) * 0.85  # 15% corporate discount
    
    special_bookings.append(Booking(
        start_time=start_time,
        end_time=end_time,
        total_hours=total_hours,
        total_price=total_price,
        status='completed',
        home_id=home.id,
        renter_id=renter.id,
        payment_status='paid',
        payment_date=start_time - timedelta(days=7),
        payment_method='bank_transfer',
        payment_reference='CORP_LONGTERM_001',
        booking_type='daily',
        created_at=start_time - timedelta(days=14)
    ))
    
    # Scenario 2: Last-minute emergency booking
    home = random.choice(homes)
    renter = random.choice(renters)
    start_time = datetime.now() + timedelta(hours=2)
    end_time = start_time + timedelta(hours=8)
    total_hours = calculate_total_hours(start_time, end_time)
    total_price = calculate_price(home, 'hourly', total_hours, start_time) * 1.2  # 20% emergency surcharge
    
    special_bookings.append(Booking(
        start_time=start_time,
        end_time=end_time,
        total_hours=total_hours,
        total_price=total_price,
        status='confirmed',
        home_id=home.id,
        renter_id=renter.id,
        payment_status='paid',
        payment_date=datetime.now() + timedelta(minutes=15),
        payment_method='momo',
        payment_reference='EMERGENCY_001',
        booking_type='hourly',
        created_at=datetime.now()
    ))
    
    # Scenario 3: Wedding/event booking (3 days)
    home = random.choice(homes)
    renter = random.choice(renters)
    next_month = datetime.now() + timedelta(days=30)
    # Find next Saturday
    days_until_saturday = (5 - next_month.weekday()) % 7
    wedding_date = next_month + timedelta(days=days_until_saturday)
    start_time = wedding_date.replace(hour=12, minute=0)
    end_time = start_time + timedelta(days=3)
    total_hours = calculate_total_hours(start_time, end_time)
    total_price = calculate_price(home, 'daily', total_hours, start_time) * 1.5  # 50% event premium
    
    special_bookings.append(Booking(
        start_time=start_time,
        end_time=end_time,
        total_hours=total_hours,
        total_price=total_price,
        status='confirmed',
        home_id=home.id,
        renter_id=renter.id,
        payment_status='paid',
        payment_date=datetime.now() - timedelta(days=5),
        payment_method='bank_transfer',
        payment_reference='WEDDING_EVENT_001',
        booking_type='daily',
        created_at=datetime.now() - timedelta(days=21)
    ))
    
    # Scenario 4: Payment dispute case
    home = random.choice(homes)
    renter = random.choice(renters)
    start_time = datetime.now() - timedelta(days=15)
    end_time = start_time + timedelta(days=2)
    total_hours = calculate_total_hours(start_time, end_time)
    total_price = calculate_price(home, 'daily', total_hours, start_time)
    
    special_bookings.append(Booking(
        start_time=start_time,
        end_time=end_time,
        total_hours=total_hours,
        total_price=total_price,
        status='disputed',
        home_id=home.id,
        renter_id=renter.id,
        payment_status='on_hold',
        payment_date=start_time - timedelta(days=3),
        payment_method='credit_card',
        payment_reference='DISPUTE_001',
        booking_type='daily',
        created_at=start_time - timedelta(days=10)
    ))
    
    # Scenario 5: Tet holiday premium booking
    tet_2024 = datetime(2024, 2, 10, 15, 0)  # Tet 2024
    if tet_2024 > datetime.now() - timedelta(days=365):  # If within our data range
        home = random.choice(homes)
        renter = random.choice(renters)
        start_time = tet_2024
        end_time = start_time + timedelta(days=5)
        total_hours = calculate_total_hours(start_time, end_time)
        total_price = calculate_price(home, 'daily', total_hours, start_time)  # Already includes Tet premium
        
        special_bookings.append(Booking(
            start_time=start_time,
            end_time=end_time,
            total_hours=total_hours,
            total_price=total_price,
            status='completed' if start_time < datetime.now() else 'confirmed',
            home_id=home.id,
            renter_id=renter.id,
            payment_status='paid',
            payment_date=start_time - timedelta(days=30),
            payment_method='bank_transfer',
            payment_reference='TET_HOLIDAY_001',
            booking_type='daily',
            created_at=start_time - timedelta(days=45)
        ))
    
    # Scenario 6: Repeat customer loyalty booking
    home = random.choice(homes)
    renter = random.choice(renters)
    start_time = datetime.now() + timedelta(days=14)
    end_time = start_time + timedelta(days=2)
    total_hours = calculate_total_hours(start_time, end_time)
    total_price = calculate_price(home, 'daily', total_hours, start_time) * 0.9  # 10% loyalty discount
    
    special_bookings.append(Booking(
        start_time=start_time,
        end_time=end_time,
        total_hours=total_hours,
        total_price=total_price,
        status='confirmed',
        home_id=home.id,
        renter_id=renter.id,
        payment_status='paid',
        payment_date=datetime.now() - timedelta(days=2),
        payment_method='momo',
        payment_reference='LOYALTY_001',
        booking_type='daily',
        created_at=datetime.now() - timedelta(days=5)
    ))
    
    print(f"Created {len(special_bookings)} special scenario bookings")
    return special_bookings

def print_pricing_debug_info(homes):
    """Print pricing information for homes to help debug"""
    print(f"\n=== HOME PRICING DEBUG INFO ===")
    
    homes_with_hourly = 0
    homes_with_daily = 0
    homes_with_both = 0
    homes_with_none = 0
    
    for home in homes[:5]:  # Show first 5 homes
        print(f"\nHome ID {home.id}: {home.title[:30]}...")
        print(f"  First 2 hours: {home.price_first_2_hours or 'Not set'}")
        print(f"  Additional hour: {home.price_per_additional_hour or 'Not set'}")
        print(f"  Overnight: {home.price_overnight or 'Not set'}")
        print(f"  Daytime: {home.price_daytime or 'Not set'}")
        print(f"  Per day: {home.price_per_day or 'Not set'}")
        
        has_hourly = any([home.price_first_2_hours, home.price_per_additional_hour, 
                         home.price_overnight, home.price_daytime])
        has_daily = bool(home.price_per_day)
        
        if has_hourly and has_daily:
            homes_with_both += 1
        elif has_hourly:
            homes_with_hourly += 1
        elif has_daily:
            homes_with_daily += 1
        else:
            homes_with_none += 1
    
    total_homes = len(homes)
    print(f"\n=== PRICING SUMMARY (Total: {total_homes} homes) ===")
    print(f"Homes with hourly pricing only: {homes_with_hourly}")
    print(f"Homes with daily pricing only: {homes_with_daily}")
    print(f"Homes with both pricing types: {homes_with_both}")
    print(f"Homes with no pricing: {homes_with_none}")

def print_booking_statistics(bookings):
    """Print statistics about generated bookings"""
    print(f"\n=== BOOKING STATISTICS ===")
    print(f"Total bookings generated: {len(bookings)}")
    
    # Status distribution
    status_counts = {}
    for booking in bookings:
        status_counts[booking.status] = status_counts.get(booking.status, 0) + 1
    
    print(f"\nStatus distribution:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count} ({count/len(bookings)*100:.1f}%)")
    
    # Booking type distribution
    type_counts = {}
    for booking in bookings:
        type_counts[booking.booking_type] = type_counts.get(booking.booking_type, 0) + 1
    
    print(f"\nBooking type distribution:")
    for booking_type, count in sorted(type_counts.items()):
        print(f"  {booking_type}: {count} ({count/len(bookings)*100:.1f}%)")
    
    # Payment method distribution
    payment_counts = {}
    for booking in bookings:
        if booking.payment_method:
            payment_counts[booking.payment_method] = payment_counts.get(booking.payment_method, 0) + 1
    
    print(f"\nPayment method distribution:")
    for method, count in sorted(payment_counts.items()):
        print(f"  {method}: {count} ({count/len(bookings)*100:.1f}%)")
    
    # Payment status distribution
    payment_status_counts = {}
    for booking in bookings:
        payment_status_counts[booking.payment_status] = payment_status_counts.get(booking.payment_status, 0) + 1
    
    print(f"\nPayment status distribution:")
    for status, count in sorted(payment_status_counts.items()):
        print(f"  {status}: {count} ({count/len(bookings)*100:.1f}%)")
    
    # Price statistics
    prices = [booking.total_price for booking in bookings]
    print(f"\nPrice statistics:")
    print(f"  Average price: {sum(prices)/len(prices):,.0f} VND")
    print(f"  Min price: {min(prices):,.0f} VND")
    print(f"  Max price: {max(prices):,.0f} VND")
    
    # Time range
    start_times = [booking.start_time for booking in bookings]
    print(f"\nTime range:")
    print(f"  Earliest booking: {min(start_times).strftime('%Y-%m-%d %H:%M')}")
    print(f"  Latest booking: {max(start_times).strftime('%Y-%m-%d %H:%M')}")

if __name__ == "__main__":
    with app.app_context():
        try:
            # Clear existing bookings (optional - comment out to keep existing data)
            print("Clearing existing bookings...")
            Booking.query.delete()
            db.session.commit()
            
            # Show pricing debug info
            homes = Home.query.all()
            if homes:
                print_pricing_debug_info(homes)
            
            # Generate new bookings
            print("Generating enhanced booking data...")
            bookings = create_enhanced_booking_data()
            
            if bookings:
                # Save to database
                print(f"Saving {len(bookings)} bookings to database...")
                db.session.bulk_save_objects(bookings)
                db.session.commit()
                
                # Print statistics
                print_booking_statistics(bookings)
                
                print(f"\n✅ Successfully created {len(bookings)} diverse bookings!")
                print("The bookings include:")
                print("- Realistic time patterns and durations")
                print("- Various payment methods and statuses")
                print("- Seasonal and weekend pricing")
                print("- Special scenarios (long-term, same-day, etc.)")
                print("- Historical data spanning 2 years")
                print("- Future bookings for testing")
            else:
                print("❌ No bookings were generated. Please check if homes and renters exist.")
                
        except Exception as e:
            print(f"❌ Error generating booking data: {str(e)}")
            db.session.rollback()