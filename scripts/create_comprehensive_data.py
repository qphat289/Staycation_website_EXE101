#!/usr/bin/env python3
"""
Comprehensive script to create diverse dummy data for statistics testing
Includes data for multiple months with various patterns and scenarios
"""

import os
import sys
from datetime import datetime, timedelta
import random
import calendar

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config.config import Config
from app.models.models import db, Owner, Home, Booking, Review, Renter

# Create a simple Flask app
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def create_comprehensive_data():
    """Create comprehensive dummy data with multiple scenarios"""
    with app.app_context():
        print("🚀 Creating comprehensive dummy data for statistics...")
        
        # Get owner with ID 3
        owner = Owner.query.get(3)
        if not owner:
            print("❌ Owner with ID 3 not found!")
            return
        
        print(f"📋 Found owner: {owner.username}")
        
        # Create more test renters for diversity
        print("📝 Creating diverse test renters...")
        renter_profiles = [
            ("business_traveler", "Business Traveler", "business@company.com"),
            ("family_vacation", "Family Vacation", "family@email.com"), 
            ("young_couple", "Young Couple", "couple@gmail.com"),
            ("solo_backpacker", "Solo Backpacker", "solo@travel.com"),
            ("group_friends", "Group of Friends", "friends@party.com"),
            ("digital_nomad", "Digital Nomad", "nomad@remote.com"),
            ("elderly_couple", "Elderly Couple", "elderly@retired.com"),
            ("local_staycation", "Local Staycation", "local@city.com"),
            ("international_tourist", "International Tourist", "tourist@global.com"),
            ("weekend_getaway", "Weekend Getaway", "weekend@escape.com")
        ]
        
        for i, (username, full_name, email) in enumerate(renter_profiles):
            if not Renter.query.filter_by(email=email).first():
                renter = Renter(
                    username=f'{username}_{i}',
                    email=email,
                    full_name=full_name,
                    phone=f'0901{random.randint(100000, 999999)}'
                )
                renter.set_password('password')
                db.session.add(renter)
        
        db.session.commit()
        
        # Get owner's homes
        homes = Home.query.filter_by(owner_id=owner.id).all()
        if not homes:
            print("❌ No homes found for this owner!")
            return
        
        print(f"📋 Found {len(homes)} homes")
        
        # Get renters
        renters = Renter.query.all()
        print(f"📋 Found {len(renters)} renters")
        
        # Clear existing data
        home_ids = [r.id for r in homes]
        Booking.query.filter(Booking.home_id.in_(home_ids)).delete(synchronize_session=False)
        Review.query.filter(Review.home_id.in_(home_ids)).delete(synchronize_session=False)
        db.session.commit()
        print("🧹 Cleared existing bookings and reviews")
        
        # Generate data for the last 6 months with different patterns
        bookings_created = 0
        reviews_created = 0
        
        # Start from 6 months ago
        start_date = datetime.now() - timedelta(days=180)
        
        print("📊 Generating data with seasonal patterns...")
        
        for day_offset in range(180):
            current_date = start_date + timedelta(days=day_offset)
            
            # Determine booking patterns based on various factors
            is_weekend = current_date.weekday() >= 5  # Saturday = 5, Sunday = 6
            is_holiday = is_holiday_period(current_date)
            is_peak_season = is_peak_tourist_season(current_date)
            month_factor = get_monthly_booking_factor(current_date.month)
            
            # Calculate number of bookings based on patterns
            base_bookings = 2
            if is_weekend:
                base_bookings += 2  # More bookings on weekends
            if is_holiday:
                base_bookings += 3  # Much more during holidays
            if is_peak_season:
                base_bookings += 1  # Slightly more in peak season
            
            # Apply monthly factor
            base_bookings = int(base_bookings * month_factor)
            
            # Add some randomness
            num_bookings = random.randint(max(1, base_bookings - 1), base_bookings + 2)
            
            # Create bookings for this day
            for _ in range(num_bookings):
                home = select_home_by_popularity(homes, current_date)
                renter = select_renter_by_pattern(renters, current_date, is_weekend, is_holiday)
                
                # Determine booking type based on day patterns
                booking_type = get_booking_type_by_pattern(current_date, is_weekend, is_holiday, renter)
                
                # Determine status with realistic patterns
                status = get_booking_status_by_pattern(current_date, booking_type, is_holiday)
                
                # Calculate pricing with seasonal adjustments
                if booking_type == 'hourly':
                    hours = get_hourly_duration(current_date, is_weekend, renter)
                    base_price = home.price_per_hour if home.price_per_hour else 50000
                    seasonal_multiplier = get_seasonal_price_multiplier(current_date, is_holiday, is_peak_season)
                    total_price = base_price * hours * seasonal_multiplier
                    
                    start_time = get_hourly_start_time(current_date, is_weekend)
                    end_time = start_time + timedelta(hours=hours)
                    total_hours = hours
                else:  # nightly
                    nights = get_nightly_duration(current_date, is_weekend, is_holiday, renter)
                    base_price = home.price_per_night if home.price_per_night else 300000
                    seasonal_multiplier = get_seasonal_price_multiplier(current_date, is_holiday, is_peak_season)
                    total_price = base_price * nights * seasonal_multiplier
                    
                    start_time = current_date.replace(hour=15, minute=0, second=0, microsecond=0)
                    end_time = start_time + timedelta(days=nights)
                    total_hours = nights * 24
                
                # Create booking
                booking = Booking(
                    home_id=home.id,
                    renter_id=renter.id,
                    start_time=start_time,
                    end_time=end_time,
                    total_hours=total_hours,
                    total_price=int(total_price),
                    booking_type=booking_type,
                    status=status,
                    created_at=start_time - timedelta(days=random.randint(1, 14))
                )
                
                db.session.add(booking)
                db.session.flush()
                bookings_created += 1
                
                # Create reviews with realistic patterns
                if should_create_review(status, booking_type, renter, current_date):
                    rating = get_realistic_rating(home, renter, booking_type, current_date)
                    comment = get_realistic_comment(rating, booking_type, renter)
                    
                    review_date = end_time + timedelta(days=random.randint(1, 14))
                    
                    review = Review(
                        renter_id=renter.id,
                        home_id=home.id,
                        rating=rating,
                        content=comment,
                        created_at=review_date
                    )
                    
                    db.session.add(review)
                    reviews_created += 1
            
            # Show progress every 30 days
            if day_offset % 30 == 0:
                print(f"  📅 Generated data for {current_date.strftime('%B %Y')}...")
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\n✅ Successfully created {bookings_created} bookings and {reviews_created} reviews!")
            
            # Show comprehensive statistics
            show_comprehensive_stats(home_ids)
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating data: {e}")
            import traceback
            traceback.print_exc()

def is_holiday_period(date):
    """Check if date is in a holiday period"""
    month, day = date.month, date.day
    
    # Vietnamese holidays and international holidays
    holidays = [
        (1, 1),   # New Year
        (2, 14),  # Valentine's Day  
        (4, 30),  # Liberation Day
        (5, 1),   # Labor Day
        (9, 2),   # National Day
        (12, 24), # Christmas Eve
        (12, 25), # Christmas
        (12, 31), # New Year's Eve
    ]
    
    # Tet period (around February)
    if month == 2 and 10 <= day <= 20:
        return True
    
    # Summer vacation period
    if month in [6, 7, 8]:
        return True
        
    return (month, day) in holidays

def is_peak_tourist_season(date):
    """Check if date is in peak tourist season"""
    month = date.month
    # Peak season: December-February, June-August
    return month in [12, 1, 2, 6, 7, 8]

def get_monthly_booking_factor(month):
    """Get booking multiplier based on month"""
    factors = {
        1: 1.3,   # January - High (Tet)
        2: 1.4,   # February - Peak (Tet)
        3: 1.0,   # March - Normal
        4: 1.1,   # April - Slightly higher
        5: 1.0,   # May - Normal
        6: 1.3,   # June - High (Summer)
        7: 1.4,   # July - Peak (Summer)
        8: 1.3,   # August - High (Summer)
        9: 1.0,   # September - Normal
        10: 1.1,  # October - Slightly higher
        11: 1.0,  # November - Normal
        12: 1.2,  # December - Higher (Christmas)
    }
    return factors.get(month, 1.0)

def select_home_by_popularity(homes, date):
    """Select home based on popularity patterns"""
    # Some homes are more popular than others
    if len(homes) >= 2:
        # 60% chance for first home, 40% for others
        if random.random() < 0.6:
            return homes[0]
        else:
            return random.choice(homes[1:])
    return random.choice(homes)

def select_renter_by_pattern(renters, date, is_weekend, is_holiday):
    """Select renter based on patterns"""
    if is_holiday:
        # Families and tourists more likely during holidays
        family_keywords = ['family', 'couple', 'tourist', 'group']
    elif is_weekend:
        # More leisure travelers on weekends  
        family_keywords = ['couple', 'friends', 'weekend', 'staycation']
    else:
        # Business travelers more likely on weekdays
        family_keywords = ['business', 'nomad', 'solo']
    
    # Try to find matching renter type
    matching_renters = [r for r in renters if any(keyword in r.username.lower() for keyword in family_keywords)]
    
    if matching_renters:
        return random.choice(matching_renters)
    return random.choice(renters)

def get_booking_type_by_pattern(date, is_weekend, is_holiday, renter):
    """Determine booking type based on patterns"""
    
    # Business travelers prefer hourly
    if 'business' in renter.username.lower():
        return 'hourly' if random.random() < 0.8 else 'nightly'
    
    # Families and tourists prefer nightly
    if any(keyword in renter.username.lower() for keyword in ['family', 'tourist', 'couple']):
        return 'nightly' if random.random() < 0.8 else 'hourly'
    
    # Weekend patterns
    if is_weekend:
        return 'nightly' if random.random() < 0.7 else 'hourly'
    
    # Holiday patterns
    if is_holiday:
        return 'nightly' if random.random() < 0.8 else 'hourly'
    
    # Default: slight preference for hourly on weekdays
    return 'hourly' if random.random() < 0.6 else 'nightly'

def get_booking_status_by_pattern(date, booking_type, is_holiday):
    """Determine booking status with realistic patterns"""
    days_ago = (datetime.now() - date).days
    
    # Older bookings more likely to be completed
    if days_ago > 30:
        return random.choices(['completed', 'cancelled'], weights=[85, 15])[0]
    elif days_ago > 7:
        return random.choices(['completed', 'confirmed', 'cancelled'], weights=[70, 25, 5])[0]
    else:
        return random.choices(['confirmed', 'completed', 'cancelled'], weights=[60, 35, 5])[0]

def get_hourly_duration(date, is_weekend, renter):
    """Get realistic hourly duration"""
    if 'business' in renter.username.lower():
        return random.randint(2, 4)  # Shorter business meetings
    elif is_weekend:
        return random.randint(3, 8)  # Longer leisure time
    else:
        return random.randint(2, 6)  # Regular duration

def get_nightly_duration(date, is_weekend, is_holiday, renter):
    """Get realistic nightly duration"""
    if is_holiday:
        return random.randint(2, 7)  # Longer holiday stays
    elif 'family' in renter.username.lower() or 'tourist' in renter.username.lower():
        return random.randint(2, 5)  # Multi-day family trips
    elif is_weekend:
        return random.randint(1, 3)  # Weekend getaways
    else:
        return random.randint(1, 2)  # Short business trips

def get_hourly_start_time(date, is_weekend):
    """Get realistic start time for hourly bookings"""
    if is_weekend:
        # More flexible timing on weekends
        hour = random.randint(8, 20)
    else:
        # Business hours on weekdays
        hour = random.randint(9, 17)
    
    return date.replace(hour=hour, minute=random.choice([0, 30]), second=0, microsecond=0)

def get_seasonal_price_multiplier(date, is_holiday, is_peak_season):
    """Get price multiplier based on demand"""
    multiplier = 1.0
    
    if is_holiday:
        multiplier *= random.uniform(1.2, 1.5)  # 20-50% increase
    elif is_peak_season:
        multiplier *= random.uniform(1.1, 1.3)  # 10-30% increase
    
    # Weekend premium
    if date.weekday() >= 5:
        multiplier *= random.uniform(1.05, 1.15)  # 5-15% increase
    
    return multiplier

def should_create_review(status, booking_type, renter, date):
    """Determine if a review should be created"""
    if status != 'completed':
        return False
    
    # Base review rate
    review_rate = 0.7
    
    # Some renter types more likely to review
    if any(keyword in renter.username.lower() for keyword in ['family', 'tourist']):
        review_rate += 0.15
    elif 'business' in renter.username.lower():
        review_rate -= 0.2  # Business travelers review less
    
    # Longer stays more likely to get reviews
    if booking_type == 'nightly':
        review_rate += 0.1
    
    return random.random() < review_rate

def get_realistic_rating(home, renter, booking_type, date):
    """Get realistic rating based on various factors"""
    # Base ratings tend to be good
    base_ratings = [3, 4, 4, 4, 5, 5, 5]
    
    # Some renter types are more critical
    if 'business' in renter.username.lower():
        # Business travelers might be more demanding
        if random.random() < 0.3:
            return random.choice([3, 4])
    
    # Holiday periods might have higher satisfaction
    if is_holiday_period(date):
        base_ratings = [4, 4, 5, 5, 5]
    
    return random.choice(base_ratings)

def get_realistic_comment(rating, booking_type, renter):
    """Get realistic comment based on rating and context"""
    
    excellent_comments = [
        "Outstanding place! Everything was perfect.",
        "Exceeded all expectations. Highly recommend!",
        "Amazing experience from start to finish.",
        "Perfect location and incredible amenities.",
        "Host was fantastic and very helpful.",
        "Could not have asked for better accommodation.",
        "Will definitely stay here again!",
        "Absolutely loved every moment of our stay."
    ]
    
    good_comments = [
        "Great place to stay, very comfortable.",
        "Clean, well-maintained, and good location.",
        "Good value for money, would recommend.",
        "Nice amenities and friendly host.",
        "Solid choice for accommodation.",
        "Met all our expectations.",
        "Good experience overall.",
        "Comfortable and convenient location."
    ]
    
    average_comments = [
        "Decent place, nothing special but adequate.",
        "Average accommodation, could be improved.",
        "Okay for the price, basic amenities.",
        "Home was fine, nothing to complain about.",
        "Standard accommodation, meets basic needs.",
        "Fair value, reasonable for a short stay.",
        "Acceptable but has home for improvement.",
        "Basic but clean and functional."
    ]
    
    if rating >= 5:
        return random.choice(excellent_comments)
    elif rating >= 4:
        return random.choice(good_comments)
    else:
        return random.choice(average_comments)

def show_comprehensive_stats(home_ids):
    """Show comprehensive statistics summary"""
    print(f"\n📊 Comprehensive Statistics Summary:")
    
    # Overall stats
    all_bookings = Booking.query.filter(Booking.home_id.in_(home_ids)).all()
    completed_bookings = [b for b in all_bookings if b.status == 'completed']
    all_reviews = Review.query.filter(Review.home_id.in_(home_ids)).all()
    
    total_revenue = sum(b.total_price for b in completed_bookings)
    hourly_count = len([b for b in completed_bookings if b.booking_type == 'hourly'])
    nightly_count = len([b for b in completed_bookings if b.booking_type == 'nightly'])
    
    print(f"  💰 Total Revenue: {total_revenue:,}đ")
    print(f"  📅 Total Bookings: {len(all_bookings)}")
    print(f"  ✅ Completed Bookings: {len(completed_bookings)}")
    print(f"  ⏰ Hourly Bookings: {hourly_count}")
    print(f"  🌙 Nightly Bookings: {nightly_count}")
    print(f"  ⭐ Total Reviews: {len(all_reviews)}")
    
    if all_reviews:
        avg_rating = sum(r.rating for r in all_reviews) / len(all_reviews)
        print(f"  🏆 Average Rating: {avg_rating:.1f}/5")
    
    # Monthly breakdown
    print(f"\n📈 Monthly Breakdown:")
    monthly_stats = {}
    for booking in completed_bookings:
        month_key = booking.start_time.strftime('%Y-%m')
        if month_key not in monthly_stats:
            monthly_stats[month_key] = {'count': 0, 'revenue': 0}
        monthly_stats[month_key]['count'] += 1
        monthly_stats[month_key]['revenue'] += booking.total_price
    
    for month, stats in sorted(monthly_stats.items()):
        month_name = datetime.strptime(month, '%Y-%m').strftime('%B %Y')
        print(f"  📅 {month_name}: {stats['count']} bookings, {stats['revenue']:,}đ")
    
    print(f"\n🎯 Ready to test comprehensive statistics at: /owner/statistics")

if __name__ == '__main__':
    create_comprehensive_data() 