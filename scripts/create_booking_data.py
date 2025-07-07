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
    
    return int(total_price)

def create_sample_renters():
    """Create sample renters if none exist in database"""
    try:
        sample_renters = []
        
        # Create 5 sample renters with realistic Vietnamese data
        renter_data = [
            {
                'username': 'nguyen_van_a',
                'email': 'nguyenvana@email.com',
                'full_name': 'Nguyễn Văn A',
                'phone': '0901234567'
            },
            {
                'username': 'tran_thi_b',
                'email': 'tranthib@email.com', 
                'full_name': 'Trần Thị B',
                'phone': '0987654321'
            },
            {
                'username': 'le_van_c',
                'email': 'levanc@email.com',
                'full_name': 'Lê Văn C', 
                'phone': '0912345678'
            },
            {
                'username': 'pham_thi_d',
                'email': 'phamthid@email.com',
                'full_name': 'Phạm Thị D',
                'phone': '0923456789'
            },
            {
                'username': 'hoang_van_e',
                'email': 'hoangvane@email.com',
                'full_name': 'Hoàng Văn E',
                'phone': '0934567890'
            }
        ]
        
        for data in renter_data:
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
        
        print(f"Created {len(sample_renters)} sample renters")
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
    """Create diverse and realistic booking data"""
    
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
    
    # Booking status options with realistic distribution
    status_options = [
        ('completed', 0.4),     # 40% completed
        ('confirmed', 0.25),    # 25% confirmed/upcoming
        ('cancelled', 0.15),    # 15% cancelled
        ('pending', 0.1),       # 10% pending
        ('active', 0.05),       # 5% currently active
        ('checked_out', 0.05)   # 5% checked out
    ]
    
    # Payment methods with realistic distribution
    payment_methods = [
        ('momo', 0.3),          # 30% MoMo (popular in Vietnam)
        ('bank_transfer', 0.25), # 25% bank transfer
        ('credit_card', 0.2),   # 20% credit card
        ('payos', 0.15),        # 15% PayOS
        ('cash', 0.1)           # 10% cash
    ]
    
    # Payment status distribution
    payment_status_map = {
        'completed': ['paid', 'paid', 'paid', 'refunded'],  # Most completed are paid, some refunded
        'confirmed': ['paid', 'paid', 'pending'],           # Most confirmed are paid
        'cancelled': ['refunded', 'failed', 'cancelled'],   # Cancelled bookings
        'pending': ['pending', 'pending', 'failed'],        # Pending bookings
        'active': ['paid'],                                  # Active bookings are paid
        'checked_out': ['paid']                              # Checked out bookings are paid
    }
    
    # Booking types with seasonal patterns
    booking_types = [
        ('daily', 0.7),         # 70% daily bookings  
        ('hourly', 0.3)         # 30% hourly bookings
    ]
    
    bookings = []
    
    # Generate bookings for the past 2 years and next 6 months
    start_date = datetime.now() - timedelta(days=730)  # 2 years ago
    end_date = datetime.now() + timedelta(days=180)    # 6 months from now
    
    # Generate 200-300 bookings for variety
    num_bookings = random.randint(200, 300)
    
    for i in range(num_bookings):
        # Select random home and renter
        home = random.choice(homes)
        renter = random.choice(renters)
        
        # Generate booking date within range
        booking_date = fake.date_time_between(start_date=start_date, end_date=end_date)
        
        # Choose booking type based on home's available pricing and distribution
        available_types = []
        type_weights = []
        
        # Check if home supports hourly booking
        if (home.price_first_2_hours and home.price_first_2_hours > 0) or \
           (home.price_per_additional_hour and home.price_per_additional_hour > 0) or \
           (home.price_overnight and home.price_overnight > 0) or \
           (home.price_daytime and home.price_daytime > 0):
            available_types.append('hourly')
            type_weights.append(0.3)
        
        # Check if home supports daily booking
        if home.price_per_day and home.price_per_day > 0:
            available_types.append('daily')
            type_weights.append(0.7)
        
        # Fallback if no pricing is available
        if not available_types:
            available_types = ['hourly', 'daily']
            type_weights = [0.3, 0.7]
        
        # Normalize weights
        total_weight = sum(type_weights)
        type_weights = [w/total_weight for w in type_weights]
        
        booking_type = random.choices(available_types, weights=type_weights)[0]
        
        # Generate booking duration based on type
        if booking_type == 'hourly':
            # Hourly bookings: 2-12 hours
            duration_hours = random.choices(
                [2, 3, 4, 6, 8, 12],
                weights=[0.2, 0.25, 0.25, 0.15, 0.1, 0.05]
            )[0]
            start_time = booking_date.replace(
                hour=random.randint(8, 20),  # 8 AM to 8 PM
                minute=random.choice([0, 30])  # On the hour or half hour
            )
        else:  # daily
            # Daily bookings: 1-14 days
            duration_days = random.choices(
                [1, 2, 3, 4, 5, 7, 10, 14],
                weights=[0.3, 0.25, 0.15, 0.1, 0.08, 0.07, 0.03, 0.02]
            )[0]
            duration_hours = duration_days * 24
            start_time = booking_date.replace(
                hour=random.choice([14, 15, 16]),  # Check-in time
                minute=0
            )
        
        end_time = start_time + timedelta(hours=duration_hours)
        
        # Calculate total hours and price
        total_hours = calculate_total_hours(start_time, end_time)
        total_price = calculate_price(home, booking_type, total_hours, start_time)
        
        # Ensure minimum price
        if total_price < 10000:  # Minimum 10,000 VND
            total_price = 10000
        
        # Choose status based on booking date
        if booking_date < datetime.now() - timedelta(days=7):
            # Past bookings are mostly completed
            status = random.choices(['completed', 'cancelled'], weights=[0.85, 0.15])[0]
        elif booking_date < datetime.now():
            # Recent bookings
            status = random.choices(['completed', 'active', 'checked_out'], weights=[0.7, 0.2, 0.1])[0]
        else:
            # Future bookings
            status = random.choices(['confirmed', 'pending', 'cancelled'], weights=[0.7, 0.2, 0.1])[0]
        
        # Choose payment method
        payment_method = random.choices(
            [pm[0] for pm in payment_methods],
            weights=[pm[1] for pm in payment_methods]
        )[0]
        
        # Choose payment status based on booking status
        payment_status = random.choice(payment_status_map[status])
        
        # Generate payment date and reference
        payment_date = None
        payment_reference = None
        
        if payment_status in ['paid', 'refunded']:
            if status == 'completed':
                # Payment was made before or during the booking
                payment_date = start_time - timedelta(hours=random.randint(1, 72))
            else:
                # Payment was made when booking was created
                payment_date = booking_date + timedelta(minutes=random.randint(5, 120))
            payment_reference = generate_payment_reference(payment_method, i + 1)
        elif payment_status == 'failed':
            payment_date = booking_date + timedelta(minutes=random.randint(5, 60))
            payment_reference = generate_payment_reference(payment_method, i + 1)
        
        # Create booking with varied created_at times
        created_at = booking_date
        if booking_date > datetime.now():
            # Future bookings were created some time ago
            created_at = datetime.now() - timedelta(days=random.randint(1, 30))
        
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
            created_at=created_at
        )
        
        bookings.append(booking)
    
    # Add some special scenario bookings
    special_bookings = create_special_scenario_bookings(homes, renters)
    bookings.extend(special_bookings)
    
    return bookings

def create_special_scenario_bookings(homes, renters):
    """Create special scenario bookings for testing edge cases"""
    special_bookings = []
    
    if not homes or not renters:
        return special_bookings
    
    # Scenario 1: Long-term booking (1 month)
    home = random.choice(homes)
    renter = random.choice(renters)
    start_time = datetime.now() - timedelta(days=45)
    end_time = start_time + timedelta(days=30)
    total_hours = calculate_total_hours(start_time, end_time)
    total_price = calculate_price(home, 'daily', total_hours, start_time)
    
    special_bookings.append(Booking(
        start_time=start_time,
        end_time=end_time,
        total_hours=total_hours,
        total_price=total_price * 0.9,  # 10% discount for long-term
        status='completed',
        home_id=home.id,
        renter_id=renter.id,
        payment_status='paid',
        payment_date=start_time - timedelta(days=2),
        payment_method='bank_transfer',
        payment_reference='BANK_LONGTERM_001',
        booking_type='daily',
        created_at=start_time - timedelta(days=7)
    ))
    
    # Scenario 2: Same-day booking
    home = random.choice(homes)
    renter = random.choice(renters)
    today = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    start_time = today + timedelta(hours=4)
    end_time = start_time + timedelta(hours=6)
    total_hours = calculate_total_hours(start_time, end_time)
    total_price = calculate_price(home, 'hourly', total_hours, start_time)
    
    special_bookings.append(Booking(
        start_time=start_time,
        end_time=end_time,
        total_hours=total_hours,
        total_price=total_price * 1.1,  # 10% surcharge for same-day
        status='confirmed',
        home_id=home.id,
        renter_id=renter.id,
        payment_status='paid',
        payment_date=today + timedelta(minutes=30),
        payment_method='momo',
        payment_reference='MOMO_SAMEDAY_001',
        booking_type='hourly',
        created_at=today
    ))
    
    # Scenario 3: Weekend premium booking
    home = random.choice(homes)
    renter = random.choice(renters)
    next_saturday = datetime.now() + timedelta(days=(5 - datetime.now().weekday()) % 7)
    start_time = next_saturday.replace(hour=15, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(days=2)
    total_hours = calculate_total_hours(start_time, end_time)
    total_price = calculate_price(home, 'daily', total_hours, start_time)
    
    special_bookings.append(Booking(
        start_time=start_time,
        end_time=end_time,
        total_hours=total_hours,
        total_price=total_price,
        status='confirmed',
        home_id=home.id,
        renter_id=renter.id,
        payment_status='paid',
        payment_date=datetime.now() - timedelta(days=3),
        payment_method='credit_card',
        payment_reference='CC_WEEKEND_001',
        booking_type='daily',
        created_at=datetime.now() - timedelta(days=5)
    ))
    
    # Scenario 4: Cancelled booking with refund
    home = random.choice(homes)
    renter = random.choice(renters)
    start_time = datetime.now() + timedelta(days=10)
    end_time = start_time + timedelta(days=3)
    total_hours = calculate_total_hours(start_time, end_time)
    total_price = calculate_price(home, 'daily', total_hours, start_time)
    
    special_bookings.append(Booking(
        start_time=start_time,
        end_time=end_time,
        total_hours=total_hours,
        total_price=total_price,
        status='cancelled',
        home_id=home.id,
        renter_id=renter.id,
        payment_status='refunded',
        payment_date=datetime.now() - timedelta(days=2),
        payment_method='payos',
        payment_reference='PAYOS_CANCELLED_001',
        booking_type='daily',
        created_at=datetime.now() - timedelta(days=7)
    ))
    
    # Scenario 5: Currently active booking
    home = random.choice(homes)
    renter = random.choice(renters)
    start_time = datetime.now() - timedelta(hours=2)
    end_time = start_time + timedelta(hours=8)
    total_hours = calculate_total_hours(start_time, end_time)
    total_price = calculate_price(home, 'hourly', total_hours, start_time)
    
    special_bookings.append(Booking(
        start_time=start_time,
        end_time=end_time,
        total_hours=total_hours,
        total_price=total_price,
        status='active',
        home_id=home.id,
        renter_id=renter.id,
        payment_status='paid',
        payment_date=start_time - timedelta(hours=3),
        payment_method='momo',
        payment_reference='MOMO_ACTIVE_001',
        booking_type='hourly',
        created_at=start_time - timedelta(hours=4)
    ))
    
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