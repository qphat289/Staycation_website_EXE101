#!/usr/bin/env python3
"""
Script to generate dummy data for testing owner statistics
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask app and database
from app.models.models import db, Owner, Room, Booking, Review, Renter
from datetime import datetime, timedelta
import random

def create_dummy_statistics_data():
    """Create dummy bookings and reviews for statistics testing"""
    
    # Import the Flask app instance directly
    from app import app
    
    with app.app_context():
        # Get the owner with ID 3 (from the logs)
        owner = Owner.query.get(3)
        if not owner:
            print("Owner with ID 3 not found. Please check if the owner exists.")
            return
        
        print(f"Creating dummy data for owner: {owner.username}")
        
        # Get owner's rooms
        rooms = Room.query.filter_by(owner_id=owner.id).all()
        if not rooms:
            print("No rooms found for this owner. Creating some test rooms first...")
            # Create some test rooms
            room1 = Room(
                name="Cozy Downtown Apartment",
                description="Beautiful apartment in the city center",
                price_per_hour=50000,
                price_per_night=300000,
                max_guests=4,
                address="123 Main St, District 1",
                owner_id=owner.id,
                status='available',
                is_active=True
            )
            
            room2 = Room(
                name="Luxury Villa with Pool",
                description="Spacious villa with private pool",
                price_per_hour=80000,
                price_per_night=500000,
                max_guests=8,
                address="456 Beach Rd, District 7",
                owner_id=owner.id,
                status='available',
                is_active=True
            )
            
            room3 = Room(
                name="Modern Studio",
                description="Perfect for solo travelers",
                price_per_hour=30000,
                price_per_night=200000,
                max_guests=2,
                address="789 Art St, District 3",
                owner_id=owner.id,
                status='available',
                is_active=True
            )
            
            db.session.add_all([room1, room2, room3])
            db.session.commit()
            rooms = [room1, room2, room3]
            print(f"Created {len(rooms)} test rooms")
        
        # Create some test renters if they don't exist
        test_renters = []
        for i in range(5):
            renter = Renter.query.filter_by(email=f'test_renter_{i}@example.com').first()
            if not renter:
                renter = Renter(
                    username=f'test_renter_{i}',
                    email=f'test_renter_{i}@example.com',
                    full_name=f'Test Renter {i+1}',
                    phone=f'090{i}{i}{i}{i}{i}{i}{i}{i}'
                )
                renter.set_password('password')
                db.session.add(renter)
                test_renters.append(renter)
        
        db.session.commit()
        
        # Get all renters for booking creation
        renters = Renter.query.limit(10).all()
        if not renters:
            print("No renters found in database")
            return
        
        print(f"Found {len(rooms)} rooms and {len(renters)} renters")
        
        # Generate bookings for the last 30 days
        base_date = datetime.now() - timedelta(days=30)
        booking_statuses = ['confirmed', 'completed', 'cancelled']
        booking_types = ['hourly', 'nightly']
        
        bookings_created = 0
        reviews_created = 0
        
        for day in range(30):
            current_date = base_date + timedelta(days=day)
            
            # Create 1-5 random bookings per day
            num_bookings = random.randint(1, 5)
            
            for _ in range(num_bookings):
                room = random.choice(rooms)
                renter = random.choice(renters)
                booking_type = random.choice(booking_types)
                status = random.choices(
                    booking_statuses, 
                    weights=[20, 60, 20]  # More completed bookings for better stats
                )[0]
                
                if booking_type == 'hourly':
                    duration = random.randint(2, 8)  # 2-8 hours
                    total_amount = room.price_per_hour * duration
                    check_in = current_date.replace(
                        hour=random.randint(9, 18),
                        minute=random.choice([0, 30])
                    )
                    check_out = check_in + timedelta(hours=duration)
                else:  # nightly
                    duration = random.randint(1, 5)  # 1-5 nights
                    total_amount = room.price_per_night * duration
                    check_in = current_date.replace(hour=15, minute=0)
                    check_out = check_in + timedelta(days=duration, hours=11)  # 11 AM checkout
                
                # Create booking
                booking = Booking(
                    room_id=room.id,
                    renter_id=renter.id,
                    check_in=check_in,
                    check_out=check_out,
                    guests=random.randint(1, room.max_guests),
                    total_amount=total_amount,
                    booking_type=booking_type,
                    status=status,
                    created_at=current_date - timedelta(days=random.randint(0, 2))
                )
                
                db.session.add(booking)
                bookings_created += 1
                
                # Create review for completed bookings (70% chance)
                if status == 'completed' and random.random() < 0.7:
                    rating = random.choices(
                        [3, 4, 5], 
                        weights=[10, 30, 60]  # More good ratings
                    )[0]
                    
                    review_comments = [
                        "Great place, highly recommended!",
                        "Clean and comfortable accommodation.",
                        "Perfect location, very convenient.",
                        "The host was very helpful and friendly.",
                        "Good value for money.",
                        "Nice amenities and well-maintained.",
                        "Exactly as described, no surprises.",
                        "Would definitely stay here again!",
                        "Peaceful and quiet environment.",
                        "Easy check-in process."
                    ]
                    
                    review = Review(
                        booking_id=booking.id,
                        renter_id=renter.id,
                        room_id=room.id,
                        rating=rating,
                        comment=random.choice(review_comments),
                        created_at=check_out + timedelta(days=random.randint(1, 7))
                    )
                    
                    db.session.add(review)
                    reviews_created += 1
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"✅ Successfully created {bookings_created} bookings and {reviews_created} reviews")
            
            # Print some statistics
            print("\n📊 Generated Statistics Preview:")
            
            completed_bookings = Booking.query.filter_by(status='completed').filter(
                Booking.room_id.in_([r.id for r in rooms])
            ).all()
            
            total_revenue = sum(b.total_amount for b in completed_bookings)
            total_bookings = len(Booking.query.filter(
                Booking.room_id.in_([r.id for r in rooms])
            ).all())
            
            hourly_bookings = len([b for b in completed_bookings if b.booking_type == 'hourly'])
            nightly_bookings = len([b for b in completed_bookings if b.booking_type == 'nightly'])
            
            all_reviews = Review.query.filter(
                Review.room_id.in_([r.id for r in rooms])
            ).all()
            avg_rating = sum(r.rating for r in all_reviews) / len(all_reviews) if all_reviews else 0
            
            print(f"  💰 Total Revenue: {total_revenue:,}đ")
            print(f"  📅 Total Bookings: {total_bookings}")
            print(f"  ⏰ Hourly Bookings: {hourly_bookings}")
            print(f"  🌙 Nightly Bookings: {nightly_bookings}")
            print(f"  ⭐ Average Rating: {avg_rating:.1f}/5")
            print(f"  💬 Total Reviews: {len(all_reviews)}")
            
            print(f"\n🎯 Ready to test statistics at: /owner/statistics")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating dummy data: {e}")

if __name__ == '__main__':
    print("🚀 Creating dummy data for statistics testing...")
    create_dummy_statistics_data() 