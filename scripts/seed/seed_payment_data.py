import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
from app.models.models import db, Payment, Booking, Owner
from datetime import datetime


def seed_payments():
    owner = Owner.query.filter_by(username='owner').first()
    bookings = Booking.query.all()
    count = 0
    for i, booking in enumerate(bookings):
        # Kiểm tra đã có payment cho booking này chưa
        existing = Payment.query.filter_by(booking_id=booking.id).first()
        if existing:
            continue
        payment = Payment(
            payment_code=f"PAY-SEED-{i+1}",
            order_code=f"ORDER-SEED-{i+1}",
            amount=booking.total_price,
            currency='VND',
            status='success',
            payment_method='PayOS',
            created_at=datetime.utcnow(),
            paid_at=datetime.utcnow(),
            booking_id=booking.id,
            owner_id=owner.id,
            renter_id=booking.renter_id
        )
        db.session.add(payment)
        count += 1
    db.session.commit()
    print(f"✅ Seeded {count} payments for all bookings!")

if __name__ == '__main__':
    from flask import Flask
    from config.config import Config
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    with app.app_context():
        seed_payments() 