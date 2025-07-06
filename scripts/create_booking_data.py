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
    """Calculate booking price based on home, type, and duration"""
    base_price = 0
    
    if booking_type == 'hourly':
        base_price = home.price_per_hour or 50000  # Default hourly price
        total_price = base_price * total_hours
    else:  # nightly
        base_price = home.price_per_night or home.price_per_hour * 24 if home.price_per_hour else 500000
        nights = max(1, total_hours // 24)
        total_price = base_price * nights
    
    # Apply seasonal/weekend pricing
    if start_time.weekday() >= 5:  # Weekend (Saturday, Sunday)
        total_price *= 1.2  # 20% weekend surcharge
    
    # Holiday seasons (Tet, summer vacation)
    if start_time.month in [1, 2, 7, 8]:  # Tet and summer
        total_price *= 1.15  # 15% holiday surcharge
    
    return int(total_price)

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
    
    if not homes or not renters:
        print("Error: No homes or renters found in database. Please seed homes and renters first.")
        return
    
    print(f"Found {len(homes)} homes and {len(renters)} renters")
    
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
        ('nightly', 0.7),       # 70% nightly bookings
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
        
        # Choose booking type based on distribution
        booking_type = random.choices(
            [bt[0] for bt in booking_types],
            weights=[bt[1] for bt in booking_types]
        )[0]
        
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
        else:  # nightly
            # Nightly bookings: 1-14 nights
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
    total_price = calculate_price(home, 'nightly', total_hours, start_time)
    
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
        booking_type='nightly',
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
    total_price = calculate_price(home, 'nightly', total_hours, start_time)
    
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
        booking_type='nightly',
        created_at=datetime.now() - timedelta(days=5)
    ))
    
    # Scenario 4: Cancelled booking with refund
    home = random.choice(homes)
    renter = random.choice(renters)
    start_time = datetime.now() + timedelta(days=10)
    end_time = start_time + timedelta(days=3)
    total_hours = calculate_total_hours(start_time, end_time)
    total_price = calculate_price(home, 'nightly', total_hours, start_time)
    
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
        booking_type='nightly',
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