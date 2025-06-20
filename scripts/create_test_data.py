#!/usr/bin/env python3
"""
Quick script to create test data for owner statistics
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now import the necessary modules
from datetime import datetime, timedelta
import random

# Import models first
from app.models.models import db, Owner, Room, Booking, Review, Renter

def create_test_data():
    """Create test data for statistics"""
    # Import the Flask app from the main app.py file
    import app
    
    # Since app.py creates the app directly, we need to access it
    # Check if we have the Flask app instance
    flask_app = None
    for attr_name in dir(app):
        attr = getattr(app, attr_name)
        if hasattr(attr, 'app_context'):  # This is likely the Flask app
            flask_app = attr
            break
    
    if not flask_app:
        # Alternative approach - look for common Flask app attributes
        for attr_name in ['app', 'application', 'flask_app']:
            if hasattr(app, attr_name):
                flask_app = getattr(app, attr_name)
                break
    
    # If still not found, let's create our own app context
    if not flask_app:
        print("Looking for Flask app in app module...")
        # Import the Flask class and create minimal context
        from flask import Flask
        from config.config import Config
        temp_app = Flask(__name__)
        temp_app.config.from_object(Config)
        db.init_app(temp_app)
        flask_app = temp_app
    
    with flask_app.app_context():
        print("🚀 Creating test data for owner statistics...")
        
        # Get owner with ID 3
        owner = Owner.query.get(3)
        if not owner:
            print("❌ Owner with ID 3 not found")
            return
            
        print(f"📋 Found owner: {owner.username}")
        
        # Get or create rooms
        rooms = Room.query.filter_by(owner_id=owner.id).all()
        if not rooms:
            print("📝 Creating test rooms...")
            rooms = [
                Room(
                    name="Downtown Apartment",
                    description="Cozy downtown apartment",
                    price_per_hour=50000,
                    price_per_night=300000,
                    max_guests=4,
                    address="123 Main St",
                    owner_id=owner.id,
                    status='available',
                    is_active=True
                ),
                Room(
                    name="Luxury Villa",
                    description="Beautiful villa with pool",
                    price_per_hour=100000,
                    price_per_night=600000,
                    max_guests=8,
                    address="456 Beach Rd",
                    owner_id=owner.id,
                    status='available',
                    is_active=True
                )
            ]
            db.session.add_all(rooms)
            db.session.commit()
            print(f"✅ Created {len(rooms)} rooms")
        
        # Get or create renters
        renters = Renter.query.limit(5).all()
        if not renters:
            print("📝 Creating test renters...")
            for i in range(3):
                renter = Renter(
                    username=f'renter{i}',
                    email=f'renter{i}@test.com',
                    full_name=f'Test Renter {i}',
                    phone=f'09012345{i}{i}{i}'
                )
                renter.set_password('password')
                db.session.add(renter)
            db.session.commit()
            renters = Renter.query.limit(5).all()
            print(f"✅ Created {len(renters)} renters")
        
        # Create bookings for the last 14 days
        print("📝 Creating test bookings...")
        bookings_created = 0
        reviews_created = 0
        
        for days_ago in range(14):
            date = datetime.now() - timedelta(days=days_ago)
            
            # Create 1-3 bookings per day
            for _ in range(random.randint(1, 3)):
                room = random.choice(rooms)
                renter = random.choice(renters)
                booking_type = random.choice(['hourly', 'nightly'])
                status = random.choice(['completed', 'completed', 'confirmed'])  # More completed
                
                if booking_type == 'hourly':
                    hours = random.randint(2, 6)
                    amount = room.price_per_hour * hours
                    check_in = date.replace(hour=random.randint(10, 16))
                    check_out = check_in + timedelta(hours=hours)
                else:
                    nights = random.randint(1, 3)
                    amount = room.price_per_night * nights
                    check_in = date.replace(hour=15)
                    check_out = check_in + timedelta(days=nights)
                
                booking = Booking(
                    room_id=room.id,
                    renter_id=renter.id,
                    check_in=check_in,
                    check_out=check_out,
                    guests=random.randint(1, room.max_guests),
                    total_amount=amount,
                    booking_type=booking_type,
                    status=status
                )
                db.session.add(booking)
                bookings_created += 1
                
                # Add review for completed bookings
                if status == 'completed' and random.random() > 0.3:
                    review = Review(
                        booking_id=booking.id,
                        renter_id=renter.id,
                        room_id=room.id,
                        rating=random.choice([4, 4, 5, 5, 5]),
                        comment="Great place to stay!",
                        created_at=check_out + timedelta(days=1)
                    )
                    db.session.add(review)
                    reviews_created += 1
        
        try:
            db.session.commit()
            print(f"✅ Created {bookings_created} bookings and {reviews_created} reviews")
            print("🎯 Test data ready! Visit /owner/statistics to see the results")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {e}")

if __name__ == '__main__':
    create_test_data() 