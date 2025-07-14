#!/usr/bin/env python3
"""
Master database seeding script for the Staycation website.
Run this script to populate the database with all necessary data.
"""

import sys
import os
import random
from datetime import datetime, timedelta
import importlib.util

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def run_seed_locations():
    """Run location seeding script"""
    try:
        print("🏙️ Seeding locations (provinces, districts, wards)...")
        
        # Import and run locations seeding
        from scripts.seed.seed_locations_fixed import seed_locations
        result = seed_locations()
        
        if result:
            print("✅ Locations seeded successfully!")
        else:
            print("⚠️ Locations seeding completed with warnings")
        return True
        
    except Exception as e:
        print(f"❌ Error seeding locations: {str(e)}")
        return False

def run_seed_amenities():
    """Run amenities seeding script"""
    try:
        print("🏠 Seeding amenities...")
        
        # Import and run amenities seeding
        from scripts.seed.seed_amenities import import_amenity_data
        from flask import Flask
        from config.config import Config
        from app.models.models import db
        
        app = Flask(__name__)
        app.config.from_object(Config)
        db.init_app(app)
        
        with app.app_context():
            import_amenity_data()
        
        print("✅ Amenities seeded successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error seeding amenities: {str(e)}")
        return False

def run_seed_rules():
    """Run rules seeding script"""
    try:
        print("📋 Seeding rules...")
        
        # Import and run rules seeding
        from scripts.seed.seed_rules import seed_rules
        result = seed_rules()
        
        print("✅ Rules seeded successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error seeding rules: {str(e)}")
        return False

def create_owner_and_homes():
    """Create 1 owner with 5 diverse homes"""
    try:
        print("👤 Creating owner and homes...")
        
        from app.models.models import db, Owner, Home, Amenity, Rule
        from werkzeug.security import generate_password_hash
        
        # Create owner
        existing_owner = Owner.query.filter_by(username='owner').first()
        if existing_owner:
            print("  Owner 'owner' already exists")
            owner = existing_owner
        else:
            owner = Owner(
                username='owner',
                email='owner@staycation.vn',
                full_name='Nguyễn Văn Chủ',
                first_name='Văn Chủ',
                last_name='Nguyễn',
                phone='0901234567',
                address='123 Đường Nguyễn Huệ, Quận 1, TP.HCM',
                business_name='Staycation Properties',
                gender='Nam',
                email_verified=True,
                first_login=False,
                # Thêm các trường mới nếu có
                tax_code=None,
                bank_name=None,
                bank_account=None
            )
            owner.set_password('123')
            db.session.add(owner)
            db.session.flush()  # Get ID
            print(f"  ✅ Created owner: {owner.username}")
        
        # Get some amenities and rules for homes
        amenities = Amenity.query.limit(10).all()
        rules = Rule.query.limit(8).all()
        
        # Sample home data
        homes_data = [
            {
                'title': 'Villa Cao Cấp Quận 1 - View Sông Sài Gòn',
                'home_type': 'Villa',
                'accommodation_type': 'entire_home',
                'address': '100 Đường Nguyễn Huệ, Phường Bến Nghé, Quận 1, TP.HCM',
                'city': 'TP.HCM',
                'district': 'Quận 1',
                'floor_number': 3,
                'bed_count': 4,
                'bathroom_count': 3,
                'max_guests': 8,
                'price_first_2_hours': 500000,
                'price_per_additional_hour': 200000,
                'price_overnight': 2000000,
                'price_daytime': 1500000,
                'price_per_day': 3500000,
                'description': 'Villa sang trọng với view sông Sài Gòn tuyệt đẹp, nội thất cao cấp, thích hợp cho gia đình và nhóm bạn.'
            },
            {
                'title': 'Homestay Cozy Quận 3 - Gần Chợ Bến Thành',
                'home_type': 'Deluxe',
                'accommodation_type': 'entire_home',
                'address': '45 Đường Võ Văn Tần, Phường 6, Quận 3, TP.HCM',
                'city': 'TP.HCM',
                'district': 'Quận 3',
                'floor_number': 2,
                'bed_count': 2,
                'bathroom_count': 2,
                'max_guests': 4,
                'price_first_2_hours': 300000,
                'price_per_additional_hour': 150000,
                'price_overnight': 1200000,
                'price_daytime': 900000,
                'price_per_day': 2200000,
                'description': 'Homestay ấm cúng trong lòng thành phố, gần chợ Bến Thành và các điểm du lịch nổi tiếng.'
            },
            {
                'title': 'Studio Modern Quận 7 - Perfect for Business',
                'home_type': 'Standard',
                'accommodation_type': 'private_room',
                'address': '88 Đường Nguyễn Văn Linh, Phường Tân Phú, Quận 7, TP.HCM',
                'city': 'TP.HCM',
                'district': 'Quận 7',
                'floor_number': 15,
                'bed_count': 1,
                'bathroom_count': 1,
                'max_guests': 2,
                'price_first_2_hours': 200000,
                'price_per_additional_hour': 100000,
                'price_overnight': 800000,
                'price_daytime': 600000,
                'price_per_day': 1500000,
                'description': 'Studio hiện đại với đầy đủ tiện nghi, thích hợp cho doanh nhân và cặp đôi.'
            },
            {
                'title': 'Penthouse Luxury Thủ Đức - Sky High Experience',
                'home_type': 'Suite',
                'accommodation_type': 'entire_home',
                'address': '200 Đường Võ Văn Ngân, Phường Linh Chiểu, Thành phố Thủ Đức, TP.HCM',
                'city': 'TP.HCM',
                'district': 'Thành phố Thủ Đức',
                'floor_number': 25,
                'bed_count': 3,
                'bathroom_count': 2,
                'max_guests': 6,
                'price_first_2_hours': 800000,
                'price_per_additional_hour': 300000,
                'price_overnight': 2500000,
                'price_daytime': 2000000,
                'price_per_day': 4500000,
                'description': 'Penthouse cao cấp với tầm nhìn toàn cảnh thành phố, nội thất xa xỉ và tiện nghi 5 sao.'
            },
            {
                'title': 'Family House Quận 10 - Traditional Vietnamese Style',
                'home_type': 'Deluxe',
                'accommodation_type': 'entire_home',
                'address': '25 Đường 3 Tháng 2, Phường 11, Quận 10, TP.HCM',
                'city': 'TP.HCM',
                'district': 'Quận 10',
                'floor_number': 2,
                'bed_count': 3,
                'bathroom_count': 2,
                'max_guests': 6,
                'price_first_2_hours': 350000,
                'price_per_additional_hour': 180000,
                'price_overnight': 1400000,
                'price_daytime': 1100000,
                'price_per_day': 2800000,
                'description': 'Nhà gia đình phong cách truyền thống Việt Nam, không gian rộng rãi và thân thiện.'
            }
        ]
        
        # Create homes
        homes_created = 0
        for home_data in homes_data:
            existing_home = Home.query.filter_by(title=home_data['title']).first()
            if existing_home:
                print(f"  Home '{home_data['title'][:30]}...' already exists")
                continue
                
            home = Home(
                title=home_data['title'],
                home_type=home_data['home_type'],
                accommodation_type=home_data['accommodation_type'],
                address=home_data['address'],
                city=home_data['city'],
                district=home_data['district'],
                floor_number=home_data['floor_number'],
                bed_count=home_data['bed_count'],
                bathroom_count=home_data['bathroom_count'],
                max_guests=home_data['max_guests'],
                price_first_2_hours=home_data['price_first_2_hours'],
                price_per_additional_hour=home_data['price_per_additional_hour'],
                price_overnight=home_data['price_overnight'],
                price_daytime=home_data['price_daytime'],
                price_per_day=home_data['price_per_day'],
                description=home_data['description'],
                owner_id=owner.id,
                is_active=True
            )
            
            # Add random amenities (3-6 amenities per home)
            if amenities:
                selected_amenities = random.sample(amenities, min(random.randint(3, 6), len(amenities)))
                home.amenities.extend(selected_amenities)
            
            # Add random rules (3-5 rules per home)
            if rules:
                selected_rules = random.sample(rules, min(random.randint(3, 5), len(rules)))
                home.rules.extend(selected_rules)
            
            db.session.add(home)
            homes_created += 1
            print(f"  ✅ Created home: {home.title[:40]}...")
        
        db.session.commit()
        print(f"✅ Created owner with {homes_created} new homes!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating owner and homes: {str(e)}")
        db.session.rollback()
        return False

def create_renter():
    """Create 1 renter account"""
    try:
        print("👥 Creating renter...")
        
        from app.models.models import db, Renter
        
        existing_renter = Renter.query.filter_by(username='renter').first()
        if existing_renter:
            print("  Renter 'renter' already exists")
            return True
        
        renter = Renter(
            username='renter',
            email='renter@staycation.vn',
            full_name='Trần Thị Khách',
            first_name='Thị Khách',
            last_name='Trần',
            phone='0987654321',
            address='456 Đường Lê Lợi, Quận 1, TP.HCM',
            gender='Nữ',
            email_verified=True,
            first_login=True,
            # Thêm các trường mới nếu có
            is_google=False,
            is_facebook=False,
            google_id=None,
            facebook_id=None,
            google_username=None,
            facebook_username=None
        )
        renter.set_password('123')
        db.session.add(renter)
        db.session.commit()
        
        print(f"  ✅ Created renter: {renter.username}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating renter: {str(e)}")
        db.session.rollback()
        return False

def setup_payos_payment():
    """Setup PayOS payment configuration for the owner"""
    try:
        print("💳 Setting up PayOS payment configuration...")
        
        from app.models.models import db, Owner, PaymentConfig
        
        # Find the owner
        owner = Owner.query.filter_by(username='owner').first()
        if not owner:
            print("  ❌ Owner not found! Please create owner first.")
            return False
        
        # Check if PayOS config already exists
        existing_config = PaymentConfig.query.filter_by(owner_id=owner.id).first()
        
        if existing_config:
            print("  PayOS config already exists, updating...")
            existing_config.payos_client_id = '0c4f23f9-5321-439b-a909-c74641f98de9'
            existing_config.payos_api_key = 'bde40f77-1af5-4b74-bfe7-540165dd465f'
            existing_config.payos_checksum_key = '041db3b7e1158179d9ba8774fae25346b284073674dc57fd4f4d6a0f9ec3a14e'
            existing_config.is_active = True
            existing_config.updated_at = datetime.utcnow()
            print("  ✅ Updated PayOS config")
        else:
            print("  Creating new PayOS config...")
            config = PaymentConfig(
                owner_id=owner.id,
                payos_client_id='0c4f23f9-5321-439b-a909-c74641f98de9',
                payos_api_key='bde40f77-1af5-4b74-bfe7-540165dd465f',
                payos_checksum_key='041db3b7e1158179d9ba8774fae25346b284073674dc57fd4f4d6a0f9ec3a14e',
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(config)
            print("  ✅ Created new PayOS config")
        
        db.session.commit()
        
        print("✅ PayOS payment configuration setup completed!")
        print("  📋 PayOS Configuration Details:")
        print(f"    - Owner: {owner.username} ({owner.full_name})")
        print(f"    - Client ID: 0c4f23f9-5321-439b-a909-c74641f98de9")
        print(f"    - API Key: bde40f77-1af5-4b74-bfe7-540165dd465f")
        print(f"    - Checksum Key: 041db3b7e1158179d9ba8774fae25346b284073674dc57fd4f4d6a0f9ec3a14e")
        print(f"    - Status: Active")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up PayOS payment: {str(e)}")
        db.session.rollback()
        return False

def run_booking_data():
    """Run booking data creation script"""
    try:
        print("📅 Creating booking data...")
        
        # Import and run booking creation
        script_path = os.path.join(project_root, 'scripts', 'create_booking_data.py')
        spec = importlib.util.spec_from_file_location("booking_module", script_path)
        booking_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(booking_module)
        
        # Run the booking creation
        with booking_module.app.app_context():
            bookings = booking_module.create_enhanced_booking_data()
            if bookings:
                booking_module.db.session.bulk_save_objects(bookings)
                booking_module.db.session.commit()
                print(f"  ✅ Created {len(bookings)} bookings")
            else:
                print("  ⚠️ No bookings created")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating booking data: {str(e)}")
        return False

def seed_database():
    """Master seeding function that runs all seeding operations"""
    print("🚀 STARTING MASTER DATABASE SEEDING")
    print("=" * 60)
    
    # Initialize database connection
    try:
        from app.models.models import db
        from flask import Flask
        from config.config import Config
        
        app = Flask(__name__)
        app.config.from_object(Config)
        db.init_app(app)
        
        with app.app_context():
            print("Connected to database successfully!")
            
            # Check if we should clear existing data
            from app.models.models import Owner
            existing_owners = Owner.query.count()
            
            if existing_owners > 0:
                print(f"\n⚠️ Found {existing_owners} existing owners in database")
                response = input("Clear existing data and reseed? (y/N): ").lower()
                
                if response == 'y':
                    print("🗑️ Clearing existing data...")
                    # Clear in correct order to avoid foreign key constraints
                    from sqlalchemy import text
                    db.session.execute(text('DELETE FROM payment_config'))
                    db.session.execute(text('DELETE FROM home_amenities'))
                    db.session.execute(text('DELETE FROM home_rules'))
                    db.session.execute(text('DELETE FROM booking'))
                    db.session.execute(text('DELETE FROM home'))
                    db.session.execute(text('DELETE FROM owner'))
                    db.session.execute(text('DELETE FROM renter'))
                    db.session.execute(text('DELETE FROM amenity'))
                    db.session.execute(text('DELETE FROM amenity_category'))
                    db.session.execute(text('DELETE FROM rule'))
                    db.session.execute(text('DELETE FROM ward'))
                    db.session.execute(text('DELETE FROM district'))
                    db.session.execute(text('DELETE FROM province'))
                    db.session.commit()
                    print("✅ Existing data cleared")
                else:
                    print("Keeping existing data, will add/update as needed")
            
            # Run all seeding operations
            steps = [
                ("1️⃣ Locations", run_seed_locations),
                ("2️⃣ Amenities", run_seed_amenities),
                ("3️⃣ Rules", run_seed_rules),
                ("4️⃣ Owner & Homes", create_owner_and_homes),
                ("5️⃣ Renter", create_renter),
                ("6️⃣ PayOS Payment Setup", setup_payos_payment),
                ("7️⃣ Booking Data", run_booking_data)
            ]
            
            success_count = 0
            
            for step_name, step_function in steps:
                print(f"\n{step_name}")
                print("-" * 40)
                
                try:
                    if step_function():
                        success_count += 1
                    else:
                        print(f"⚠️ {step_name} completed with warnings")
                except Exception as e:
                    print(f"❌ {step_name} failed: {str(e)}")
            
            # Final summary
            print("\n" + "=" * 60)
            print("🎯 SEEDING COMPLETED!")
            print(f"✅ {success_count}/{len(steps)} steps completed successfully")
            
            if success_count == len(steps):
                print("\n🎉 All data seeded successfully!")
                print("\n📋 ACCOUNT INFORMATION:")
                print("👤 Owner Account:")
                print("   Username: owner")
                print("   Password: 123")
                print("   Email: owner@staycation.vn")
                print("\n👥 Renter Account:")
                print("   Username: renter")
                print("   Password: 123")
                print("   Email: renter@staycation.vn")
                print("\n💳 PayOS Configuration:")
                print("   Client ID: 0c4f23f9-5321-439b-a909-c74641f98de9")
                print("   API Key: bde40f77-1af5-4b74-bfe7-540165dd465f")
                print("   Checksum Key: 041db3b7e1158179d9ba8774fae25346b284073674dc57fd4f4d6a0f9ec3a14e")
                print("   Status: Active")
                print("\n🏠 Created 5 diverse homes with different types and pricing")
                print("📅 Generated realistic booking data with no time conflicts")
                print("🏙️ Seeded location data for Vietnam")
                print("🏠 Added amenities and rules for homes")
            else:
                print("\n⚠️ Some steps had issues. Please check the logs above.")
            
            return success_count == len(steps)
            
    except Exception as e:
        print(f"❌ Database connection error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🌟 Staycation Database Master Seeding Tool")
    print("This will seed all necessary data for the application")
    print()
    
    success = seed_database()
    
    if success:
        print("\n🎊 Seeding completed successfully!")
        print("You can now start using the application with the seeded data.")
    else:
        print("\n💥 Seeding failed!")
        print("Please check the error messages above and try again.")
        sys.exit(1) 