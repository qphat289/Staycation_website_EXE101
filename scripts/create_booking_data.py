#!/usr/bin/env python3
"""
Database seeding script for the Staycation website.
Run this script to populate the database with sample data.
"""

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

def check_booking_overlap(start_time, end_time, home_id, existing_bookings):
    """
    Check if a new booking overlaps with existing bookings for the same home.
    Returns True if there's an overlap (conflict), False if it's safe to book.
    """
    for booking in existing_bookings:
        if booking.home_id != home_id:
            continue
            
        # Skip cancelled bookings as they don't block availability
        if booking.status in ['cancelled', 'no_show']:
            continue
            
        # Check for overlap: new booking conflicts if it starts before existing ends
        # and ends after existing starts
        if (start_time < booking.end_time and end_time > booking.start_time):
            return True
    
    return False

def find_available_time_slot(home, duration_hours, preferred_start_time, existing_bookings, max_attempts=20):
    """
    Find an available time slot for a booking that doesn't overlap with existing bookings.
    Returns (start_time, end_time) if found, or None if no slot available.
    """
    
    for attempt in range(max_attempts):
        # Add some randomness to the preferred start time
        random_offset_hours = random.randint(-12, 12)
        start_time = preferred_start_time + timedelta(hours=random_offset_hours)
        end_time = start_time + timedelta(hours=duration_hours)
        
        # Ensure the booking is within our target time range (past week to next week)
        now = datetime.now()
        earliest_allowed = now - timedelta(days=7)
        latest_allowed = now + timedelta(days=7)
        
        if start_time < earliest_allowed or end_time > latest_allowed:
            continue
            
        # Check for conflicts
        if not check_booking_overlap(start_time, end_time, home.id, existing_bookings):
            return start_time, end_time
    
    return None

def get_customer_type():
    """Generate customer behavior patterns"""
    customer_types = [
        {
            'type': 'business_traveler',
            'weight': 0.25,
            'booking_preferences': {
                'advance_booking_days': (1, 7),    # Books 1-7 days ahead
                'preferred_duration': (4, 24),     # 4-24 hours 
                'preferred_times': [(6, 9), (17, 20)],  # Early morning or evening
                'payment_methods': ['credit_card', 'bank_transfer'],
                'cancellation_rate': 0.1
            }
        },
        {
            'type': 'leisure_traveler',
            'weight': 0.35,
            'booking_preferences': {
                'advance_booking_days': (2, 14),   # Books 2 days to 2 weeks ahead
                'preferred_duration': (24, 72),    # 1-3 days
                'preferred_times': [(10, 16)],     # Daytime check-in
                'payment_methods': ['momo', 'credit_card', 'payos'],
                'cancellation_rate': 0.15
            }
        },
        {
            'type': 'local_resident',
            'weight': 0.2,
            'booking_preferences': {
                'advance_booking_days': (0, 3),    # Same day to 3 days
                'preferred_duration': (2, 8),      # Few hours
                'preferred_times': [(18, 23)],     # Evening/night
                'payment_methods': ['momo', 'cash'],
                'cancellation_rate': 0.2
            }
        },
        {
            'type': 'group_traveler',
            'weight': 0.15,
            'booking_preferences': {
                'advance_booking_days': (7, 14),   # 1-2 weeks ahead
                'preferred_duration': (48, 120),   # 2-5 days
                'preferred_times': [(14, 18)],     # Afternoon
                'payment_methods': ['bank_transfer', 'credit_card'],
                'cancellation_rate': 0.25
            }
        },
        {
            'type': 'staycation',
            'weight': 0.05,
            'booking_preferences': {
                'advance_booking_days': (1, 7),    # 1 day to 1 week
                'preferred_duration': (24, 48),    # 1-2 days
                'preferred_times': [(15, 17)],     # Standard check-in
                'payment_methods': ['momo', 'payos'],
                'cancellation_rate': 0.1
            }
        }
    ]
    
    weights = [ct['weight'] for ct in customer_types]
    return random.choices(customer_types, weights=weights)[0]

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
            # Local residents
            {
                'username': 'hoang_local',
                'email': 'hoang.local@gmail.com',
                'full_name': 'Hoàng Văn Địa',
                'phone': '0934567890'
            },
            {
                'username': 'vo_resident',
                'email': 'vo.resident@outlook.com',
                'full_name': 'Võ Thị Phương',
                'phone': '0945678901'
            },
            # Group travelers
            {
                'username': 'group_leader',
                'email': 'leader@group-travel.vn',
                'full_name': 'Đặng Văn Nhóm',
                'phone': '0956789012'
            },
            # Staycation customers
            {
                'username': 'staycation_user',
                'email': 'stay@home.vn',
                'full_name': 'Lý Thị Nghỉ',
                'phone': '0967890123'
            }
        ]
        
        for profile in renter_profiles:
            # Check if renter already exists
            existing_renter = Renter.query.filter_by(email=profile['email']).first()
            if existing_renter:
                sample_renters.append(existing_renter)
                continue
            
            renter = Renter(
                username=profile['username'],
                email=profile['email'],
                full_name=profile['full_name'],
                phone=profile['phone']
            )
            renter.set_password('123')  # Default password
            db.session.add(renter)
            sample_renters.append(renter)
        
        db.session.commit()
        print(f"Created/found {len(sample_renters)} renters")
        return sample_renters
        
    except Exception as e:
        print(f"Error creating sample renters: {str(e)}")
        db.session.rollback()
        return []

def generate_payment_reference(payment_method, booking_id):
    """Generate realistic payment reference numbers"""
    if payment_method == 'momo':
        return f"MOMO{random.randint(1000000000, 9999999999)}"
    elif payment_method == 'payos':
        return f"PAYOS{random.randint(100000, 999999)}"
    elif payment_method == 'bank_transfer':
        return f"BANK{random.randint(10000000, 99999999)}"
    elif payment_method == 'credit_card':
        return f"CC{random.randint(1000000, 9999999)}"
    elif payment_method == 'zalopay':
        return f"ZALO{random.randint(100000, 999999)}"
    else:
        return f"PAY{random.randint(100000, 999999)}"

def create_enhanced_booking_data():
    """Create exactly ~50 diverse booking data with no time conflicts"""
    
    # Get existing homes and renters
    homes = Home.query.all()
    renters = Renter.query.all()
    
    if not homes:
        print("Error: No homes found in database. Please seed homes first.")
        return []
    
    # Create sample renters if none exist
    if not renters:
        print("No renters found. Creating sample renters...")
        renters = create_sample_renters()
        if not renters:
            print("Failed to create sample renters.")
            return []
    
    # Check if we need more renters for diversity
    if len(renters) < 5:
        print(f"Creating additional renters for diversity (current: {len(renters)})...")
        additional_renters = create_sample_renters()
        renters.extend(additional_renters)
    
    print(f"Found {len(homes)} homes and {len(renters)} renters")
    
    # Calculate theoretical capacity
    timeframe_hours = 14 * 24  # 2 weeks in hours
    capacity_per_home = timeframe_hours // 4  # Assuming average 4-hour bookings
    total_capacity = len(homes) * capacity_per_home
    print(f"Estimated booking capacity: {total_capacity} bookings across {len(homes)} homes")
    
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
    
    # Booking configuration - adjust based on actual capacity
    base_target = 50
    TARGET_BOOKINGS = min(base_target, total_capacity)
    if TARGET_BOOKINGS < base_target:
        print(f"⚠️  Adjusted target to {TARGET_BOOKINGS} bookings due to limited home capacity")
    else:
        print(f"🎯 Target: {TARGET_BOOKINGS} bookings")
    status_options = [
        ('completed', 0.30),     # 30% completed (past bookings)
        ('confirmed', 0.25),     # 25% confirmed (future bookings)
        ('cancelled', 0.15),     # 15% cancelled
        ('pending', 0.10),       # 10% pending
        ('active', 0.10),        # 10% currently active 
        ('checked_out', 0.05),   # 5% checked out
        ('no_show', 0.03),       # 3% no show
        ('disputed', 0.02)       # 2% disputed
    ]
    
    payment_methods = [
        ('momo', 0.35),          # 35% MoMo
        ('bank_transfer', 0.25), # 25% bank transfer
        ('payos', 0.18),         # 18% PayOS
        ('credit_card', 0.15),   # 15% credit card
        ('cash', 0.05),          # 5% cash
        ('zalopay', 0.02)        # 2% ZaloPay
    ]
    
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
    all_existing_bookings = []  # Track all bookings to prevent conflicts
    
    # Time range: 1 week ago to 1 week from now
    now = datetime.now()
    start_date = now - timedelta(days=7)
    end_date = now + timedelta(days=7)
    
    print(f"Creating bookings from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Get existing bookings to avoid conflicts
    existing_bookings = Booking.query.filter(
        Booking.start_time >= start_date,
        Booking.end_time <= end_date
    ).all()
    all_existing_bookings.extend(existing_bookings)
    
    attempts = 0
    max_attempts = TARGET_BOOKINGS * 3  # Allow multiple attempts
    
    while len(bookings) < TARGET_BOOKINGS and attempts < max_attempts:
        attempts += 1
        
        # Select random home and renter
        home = random.choice(homes)
        renter = random.choice(renters)
        
        # Get customer behavior pattern
        customer_profile = get_customer_type()
        prefs = customer_profile['booking_preferences']
        
        # Generate booking timing
        advance_days = random.randint(*prefs['advance_booking_days'])
        
        # Determine if this is a past or future booking
        if random.random() < 0.4:  # 40% past bookings
            booking_date = now - timedelta(days=random.randint(1, 7))
            booking_created_date = booking_date - timedelta(days=advance_days)
        else:  # 60% future bookings
            booking_date = now + timedelta(days=random.randint(0, 7))
            booking_created_date = now - timedelta(days=advance_days)
        
        # Adjust start time based on customer preferences
        preferred_time_ranges = prefs['preferred_times']
        time_range = random.choice(preferred_time_ranges)
        start_hour = random.randint(time_range[0], time_range[1])
        preferred_start_time = booking_date.replace(hour=start_hour, minute=random.choice([0, 30]))
        
        # Determine duration
        duration_range = prefs['preferred_duration']
        duration_hours = random.randint(int(duration_range[0]), int(duration_range[1]))
        duration_hours = max(2, duration_hours)  # Minimum 2 hours
        
        # Find available time slot
        time_slot = find_available_time_slot(
            home, duration_hours, preferred_start_time, all_existing_bookings
        )
        
        # If can't find slot with preferred duration, try shorter durations
        if not time_slot and duration_hours > 2:
            for shorter_duration in [duration_hours // 2, 4, 3, 2]:
                if shorter_duration < 2:
                    break
                time_slot = find_available_time_slot(
                    home, shorter_duration, preferred_start_time, all_existing_bookings
                )
                if time_slot:
                    duration_hours = shorter_duration
                    break
        
        if not time_slot:
            continue  # Try again with different parameters
        
        start_time, end_time = time_slot
        
        # Determine booking type
        booking_type = 'daily' if duration_hours >= 24 else 'hourly'
        
        # Calculate pricing
        total_hours = calculate_total_hours(start_time, end_time)
        total_price = calculate_price(home, booking_type, total_hours, start_time)
        
        # Apply customer-specific pricing adjustments
        if customer_profile['type'] == 'group_traveler':
            total_price *= 1.1  # 10% group surcharge
        elif customer_profile['type'] == 'business_traveler':
            total_price *= 1.05  # 5% business rate
        elif customer_profile['type'] == 'local_resident' and booking_type == 'hourly':
            total_price *= 0.95  # 5% local discount
        
        # Ensure minimum price
        total_price = max(total_price, 20000)  # Minimum 20,000 VND
        
        # Determine booking status based on timing
        if start_time < now - timedelta(hours=1):
            # Past bookings
            if random.random() < prefs['cancellation_rate']:
                status = 'cancelled'
            else:
                status = random.choices(['completed', 'no_show'], weights=[0.95, 0.05])[0]
        elif start_time < now + timedelta(hours=2):
            # Current/very near future
            status = random.choices(['active', 'checked_out', 'confirmed'], weights=[0.5, 0.3, 0.2])[0]
        else:
            # Future bookings
            if random.random() < prefs['cancellation_rate'] * 0.5:  # Lower cancellation for future
                status = 'cancelled'
            else:
                status = random.choices(['confirmed', 'pending'], weights=[0.8, 0.2])[0]
        
        # Choose payment method and status
        payment_method_weights = [weight for _, weight in payment_methods]
        payment_method = random.choices([method for method, _ in payment_methods], weights=payment_method_weights)[0]
        payment_status = random.choice(payment_status_map[status])
        
        # Generate payment details
        payment_date = None
        payment_reference = None
        
        if payment_status in ['paid', 'refunded', 'on_hold']:
            if booking_type == 'daily':
                payment_date = booking_created_date + timedelta(hours=random.randint(1, 48))
            else:
                payment_date = start_time - timedelta(hours=random.randint(1, 24))
            payment_reference = generate_payment_reference(payment_method, len(bookings) + 1)
        elif payment_status == 'failed':
            payment_date = booking_created_date + timedelta(minutes=random.randint(5, 120))
            payment_reference = generate_payment_reference(payment_method, len(bookings) + 1)
        
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
        all_existing_bookings.append(booking)  # Add to tracking list
        
        print(f"Created booking {len(bookings)}/{TARGET_BOOKINGS}: {home.title[:30]}... from {start_time.strftime('%m-%d %H:%M')} to {end_time.strftime('%m-%d %H:%M')}")
    
    print(f"Successfully created {len(bookings)} bookings with no time conflicts!")
    return bookings

def print_pricing_debug_info(homes):
    """Print pricing information for homes to help debug"""
    print(f"\n=== HOME PRICING DEBUG INFO ===")
    print(f"Total homes available: {len(homes)}")
    
    homes_with_pricing = 0
    for home in homes[:3]:  # Show first 3 homes
        print(f"\nHome ID {home.id}: {home.title[:40]}...")
        print(f"  First 2 hours: {home.price_first_2_hours or 'Not set'}")
        print(f"  Additional hour: {home.price_per_additional_hour or 'Not set'}")
        print(f"  Per day: {home.price_per_day or 'Not set'}")
        
        has_pricing = any([home.price_first_2_hours, home.price_per_additional_hour, home.price_per_day])
        if has_pricing:
            homes_with_pricing += 1
    
    print(f"Homes with valid pricing: {homes_with_pricing}/{len(homes)}")

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
            print("🚀 Starting booking data generation...")
            print("=" * 50)
            
            # Show pricing debug info
            homes = Home.query.all()
            if homes:
                print_pricing_debug_info(homes)
            
            # Option to clear existing bookings in time range
            print(f"\n📊 Checking existing bookings in target range...")
            now = datetime.now()
            existing_count = Booking.query.filter(
                Booking.start_time >= now - timedelta(days=7),
                Booking.end_time <= now + timedelta(days=7)
            ).count()
            
            if existing_count > 0:
                print(f"Found {existing_count} existing bookings in target time range")
                response = input("Clear existing bookings in this range? (y/N): ").lower()
                if response == 'y':
                    Booking.query.filter(
                        Booking.start_time >= now - timedelta(days=7),
                        Booking.end_time <= now + timedelta(days=7)
                    ).delete()
                    db.session.commit()
                    print("✅ Cleared existing bookings in target range")
            else:
                print("No existing bookings found in target range")
            
            # Generate new bookings
            print("\n🎯 Generating ~50 diverse bookings with no time conflicts...")
            print("Time range: 1 week ago to 1 week from now")
            print("=" * 50)
            
            bookings = create_enhanced_booking_data()
            
            if bookings:
                # Save to database
                print(f"\n💾 Saving {len(bookings)} bookings to database...")
                db.session.bulk_save_objects(bookings)
                db.session.commit()
                
                # Print statistics
                print_booking_statistics(bookings)
                
                print(f"\n🎉 SUCCESS! Created {len(bookings)} bookings with features:")
                print("✅ No time conflicts between bookings")
                print("✅ Diverse customer behavior patterns")
                print("✅ Realistic payment methods and statuses")
                print("✅ Weekend and seasonal pricing")
                print("✅ Mix of past and future bookings")
                print("✅ Focus on recent timeframe (±1 week)")
            else:
                print("❌ No bookings were generated. Please check if homes and renters exist.")
                
        except Exception as e:
            print(f"❌ Error generating booking data: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()