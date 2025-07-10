#!/usr/bin/env python3
"""
Database seeding script for the Staycation website.
Run this script to populate the database with sample data.
"""

import sys
import os
from datetime import datetime
import importlib.util

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def seed_database():
    """Seed the database with sample data"""
    try:
        print("=== Database Seeding Tool ===")
        print("Initializing database connection...")
        
        # Import after path setup
        from app.models.models import db, Owner, Renter, Admin, Home
        from werkzeug.security import generate_password_hash
        
        # Import Flask app from root app.py
        app_path = os.path.join(project_root, 'app.py')
        spec = importlib.util.spec_from_file_location("app_module", app_path)
        app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_module)
        
        with app_module.app.app_context():
            print("Connected to database successfully!")
            
            # Check if data already exists
            if Owner.query.count() > 0:
                print("Owners already exist in database. Skipping seeding.")
                return
                
            print("Seeding sample data...")
            
            # Create sample owners
            owners_data = [
                {
                    'username': 'owner',
                    'email': 'owner1@example.com',
                    'full_name': 'Nguyễn Văn A',
                    'first_name': 'Văn A',
                    'last_name': 'Nguyễn',
                    'phone': '0901234567',
                    'address': '123 Đường ABC, Quận 1, TP.HCM',
                    'business_name': 'Homestay Sài Gòn'
                }
            ]
            
            for owner_data in owners_data:
                owner = Owner(
                    username=owner_data['username'],
                    email=owner_data['email'],
                    full_name=owner_data['full_name'],
                    first_name=owner_data['first_name'],
                    last_name=owner_data['last_name'],
                    phone=owner_data['phone'],
                    address=owner_data['address'],
                    business_name=owner_data['business_name']
                )
                owner.set_password('123')
                db.session.add(owner)
            
            # Create sample renters
            renters_data = [
                {
                    'username': 'renter',
                    'email': 'renter1@example.com',
                    'full_name': 'Phạm Văn D',
                    'phone': '0934567890'
                }
            ]
            
            for renter_data in renters_data:
                renter = Renter(
                    username=renter_data['username'],
                    email=renter_data['email'],
                    full_name=renter_data['full_name'],
                    phone=renter_data['phone']
                )
                renter.set_password('123')
                db.session.add(renter)
            
            # Commit the changes
            db.session.commit()
            print(f"✓ Created {len(owners_data)} owners")
            print(f"✓ Created {len(renters_data)} renters")
            
            # Create sample homes
            owners = Owner.query.all()
            if owners:
                homes_data = [
                    {
                        'title': 'Căn hộ cao cấp Quận 1',
                        'home_type': 'Deluxe',
                        'accommodation_type': 'entire_home',
                        'address': '123 Đường Nguyễn Huệ, Quận 1, TP.HCM',
                        'city': 'TP.HCM',
                        'district': 'Quận 1',
                        'bed_count': 2,
                        'bathroom_count': 2,
                        'max_guests': 4,
                        'price_per_hour': 150000,
                        'price_per_night': 1500000,
                        'description': 'Căn hộ cao cấp với view đẹp'
                    },
                    {
                        'title': 'Villa sang trọng Quận 7',
                        'home_type': 'Suite',
                        'accommodation_type': 'entire_home',
                        'address': '456 Đường Nguyễn Văn Linh, Quận 7, TP.HCM',
                        'city': 'TP.HCM',
                        'district': 'Quận 7',
                        'bed_count': 4,
                        'bathroom_count': 3,
                        'max_guests': 8,
                        'price_per_hour': 300000,
                        'price_per_night': 3000000,
                        'description': 'Villa sang trọng với hồ bơi'
                    }
                ]
                
                for i, home_data in enumerate(homes_data):
                    home = Home(
                        title=home_data['title'],
                        home_type=home_data['home_type'],
                        accommodation_type=home_data['accommodation_type'],
                        address=home_data['address'],
                        city=home_data['city'],
                        district=home_data['district'],
                        bed_count=home_data['bed_count'],
                        bathroom_count=home_data['bathroom_count'],
                        max_guests=home_data['max_guests'],
                        price_per_hour=home_data['price_per_hour'],
                        price_per_night=home_data['price_per_night'],
                        description=home_data['description'],
                        owner_id=owners[i % len(owners)].id
                    )
                    db.session.add(home)
                
                db.session.commit()
                print(f"✓ Created {len(homes_data)} homes")
            
            print("\n🎉 Database seeding completed successfully!")
            print("\nSample accounts created:")
            print("Owners: owner1@example.com, owner2@example.com (password: password123)")
            print("Renters: renter1@example.com, renter2@example.com (password: password123)")
            
    except Exception as e:
        print(f"❌ Error seeding database: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    print("Starting database seeding...")
    success = seed_database()
    if success:
        print("\nSeeding completed successfully!")
    else:
        print("\nSeeding failed!")
        sys.exit(1) 