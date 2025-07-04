import sys
import os
import importlib.util
from datetime import datetime

# Đảm bảo đường dẫn project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import app và db từ app.py bằng importlib
app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app.py'))
spec = importlib.util.spec_from_file_location('app', app_path)
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)
app = app_module.app
db = app_module.db
from app.models.models import Booking

with app.app_context():
    bookings = [
        Booking(
            start_time=datetime(2024, 6, 1, 14, 0),
            end_time=datetime(2024, 6, 5, 12, 0),
            total_hours=None,
            total_price=2500000,
            status='completed',
            home_id=2,
            renter_id=1,
            payment_status='paid',
            payment_date=datetime(2024, 6, 1, 15, 0),
            payment_method='credit_card',
            payment_reference='PAY123456',
            booking_type='nightly'
        ),
        Booking(
            start_time=datetime(2024, 7, 10, 14, 0),
            end_time=datetime(2024, 7, 15, 12, 0),
            total_hours=None,
            total_price=6000000,
            status='upcoming',
            home_id=3,
            renter_id=2,
            payment_status='pending',
            booking_type='nightly'
        ),
        Booking(
            start_time=datetime(2023, 12, 20, 14, 0),
            end_time=datetime(2023, 12, 25, 12, 0),
            total_hours=None,
            total_price=3500000,
            status='completed',
            home_id=1,
            renter_id=3,
            payment_status='paid',
            payment_date=datetime(2023, 12, 20, 15, 0),
            payment_method='momo',
            payment_reference='MOMO987654',
            booking_type='nightly'
        ),
        Booking(
            start_time=datetime(2024, 8, 1, 8, 0),
            end_time=datetime(2024, 8, 3, 12, 0),
            total_hours=None,
            total_price=1200000,
            status='upcoming',
            home_id=4,
            renter_id=4,
            payment_status='pending',
            booking_type='nightly'
        ),
        Booking(
            start_time=datetime(2024, 5, 15, 10, 0),
            end_time=datetime(2024, 5, 18, 12, 0),
            total_hours=None,
            total_price=1800000,
            status='cancelled',
            home_id=2,
            renter_id=5,
            payment_status='refunded',
            payment_date=datetime(2024, 5, 15, 11, 0),
            payment_method='bank_transfer',
            payment_reference='BANK555888',
            booking_type='nightly'
        ),
        Booking(
            start_time=datetime(2024, 9, 10, 14, 0),
            end_time=datetime(2024, 9, 20, 12, 0),
            total_hours=None,
            total_price=12000000,
            status='upcoming',
            home_id=5,
            renter_id=1,
            payment_status='pending',
            booking_type='nightly'
        ),
        Booking(
            start_time=datetime(2024, 3, 1, 8, 0),
            end_time=datetime(2024, 3, 3, 12, 0),
            total_hours=None,
            total_price=900000,
            status='completed',
            home_id=1,
            renter_id=2,
            payment_status='paid',
            payment_date=datetime(2024, 3, 1, 9, 0),
            payment_method='credit_card',
            payment_reference='PAY654321',
            booking_type='nightly'
        ),
        Booking(
            start_time=datetime(2024, 10, 5, 14, 0),
            end_time=datetime(2024, 10, 10, 12, 0),
            total_hours=None,
            total_price=7500000,
            status='upcoming',
            home_id=3,
            renter_id=3,
            payment_status='pending',
            booking_type='nightly'
        ),
        Booking(
            start_time=datetime(2024, 4, 15, 14, 0),
            end_time=datetime(2024, 4, 18, 12, 0),
            total_hours=None,
            total_price=2100000,
            status='completed',
            home_id=2,
            renter_id=4,
            payment_status='paid',
            payment_date=datetime(2024, 4, 15, 15, 0),
            payment_method='momo',
            payment_reference='MOMO123789',
            booking_type='nightly'
        ),
        Booking(
            start_time=datetime(2024, 11, 1, 14, 0),
            end_time=datetime(2024, 11, 5, 12, 0),
            total_hours=None,
            total_price=3200000,
            status='upcoming',
            home_id=4,
            renter_id=5,
            payment_status='pending',
            booking_type='nightly'
        ),
    ]

    db.session.bulk_save_objects(bookings)
    db.session.commit()
    print("Seeded bookings successfully!")