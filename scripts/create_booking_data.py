#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config.config import Config
from app.models.models import db, Booking, Home, Renter
from datetime import datetime, timedelta
import random

def create_app():
    """Tạo Flask app cho script"""
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def create_booking_data():
    app = create_app()
    
    with app.app_context():
        print("🏠 Bắt đầu tạo dữ liệu booking...")
        
        # Lấy tất cả homes và renters có sẵn
        homes = Home.query.filter_by(is_active=True).all()
        renters = Renter.query.filter_by(is_active=True).all()
        
        if not homes:
            print("❌ Không có home nào trong database!")
            return
            
        if not renters:
            print("❌ Không có renter nào trong database!")
            return
            
        print(f"📋 Tìm thấy {len(homes)} homes và {len(renters)} renters")
        
        # Tạo booking cho 30 ngày gần đây
        today = datetime.now()
        bookings_created = 0
        
        for i in range(30):
            # Ngày tạo booking (từ 30 ngày trước đến hôm nay)
            booking_date = today - timedelta(days=30-i)
            
            # Tạo 1-5 booking ngẫu nhiên mỗi ngày
            num_bookings = random.randint(1, 5)
            
            for j in range(num_bookings):
                # Chọn ngẫu nhiên home và renter
                home = random.choice(homes)
                renter = random.choice(renters)
                
                # Quyết định loại booking (70% theo giờ, 30% theo đêm)
                booking_type = 'hourly' if random.random() < 0.7 else 'nightly'
                
                if booking_type == 'hourly':
                    # Booking theo giờ: 2-8 giờ
                    hours = random.randint(2, 8)
                    start_hour = random.randint(8, 16)  # Bắt đầu từ 8h-16h
                    
                    start_time = booking_date.replace(
                        hour=start_hour, 
                        minute=random.choice([0, 30]), 
                        second=0, 
                        microsecond=0
                    )
                    end_time = start_time + timedelta(hours=hours)
                    
                    # Tính giá theo giờ
                    if home.price_per_hour:
                        total_price = home.price_per_hour * hours
                    else:
                        total_price = 50000 * hours  # Giá mặc định 50k/giờ
                        
                else:
                    # Booking theo đêm: 1-3 đêm
                    nights = random.randint(1, 3)
                    
                    # Check-in vào buổi chiều (14h-18h)
                    start_time = booking_date.replace(
                        hour=random.randint(14, 18), 
                        minute=random.choice([0, 30]), 
                        second=0, 
                        microsecond=0
                    )
                    # Check-out vào buổi sáng ngày hôm sau (10h-12h)
                    end_time = start_time + timedelta(days=nights)
                    end_time = end_time.replace(hour=random.randint(10, 12))
                    
                    hours = int((end_time - start_time).total_seconds() / 3600)
                    
                    # Tính giá theo đêm
                    if home.price_per_night:
                        total_price = home.price_per_night * nights
                    else:
                        total_price = 200000 * nights  # Giá mặc định 200k/đêm
                
                # Tạo booking
                booking = Booking(
                    start_time=start_time,
                    end_time=end_time,
                    total_hours=hours,
                    total_price=total_price,
                    status=random.choice(['completed', 'completed', 'completed', 'cancelled']),  # 75% completed
                    home_id=home.id,
                    renter_id=renter.id,
                    booking_type=booking_type,
                    payment_status='completed' if random.random() < 0.9 else 'pending',
                    payment_date=start_time - timedelta(hours=random.randint(1, 24)),
                    payment_method=random.choice(['vnpay', 'momo', 'banking']),
                    created_at=start_time - timedelta(hours=random.randint(1, 48))
                )
                
                try:
                    db.session.add(booking)
                    bookings_created += 1
                except Exception as e:
                    print(f"❌ Lỗi tạo booking: {e}")
                    continue
        
        # Commit tất cả booking
        try:
            db.session.commit()
            print(f"✅ Đã tạo thành công {bookings_created} booking!")
            
            # Hiển thị thống kê
            total_bookings = Booking.query.count()
            hourly_bookings = Booking.query.filter_by(booking_type='hourly').count()
            nightly_bookings = Booking.query.filter_by(booking_type='nightly').count()
            total_revenue = db.session.query(db.func.sum(Booking.total_price)).filter(
                Booking.status == 'completed'
            ).scalar() or 0
            
            print(f"""
📊 THỐNG KÊ BOOKING:
- Tổng số booking: {total_bookings}
- Booking theo giờ: {hourly_bookings}
- Booking theo đêm: {nightly_bookings}
- Tổng doanh thu: {total_revenue:,.0f}đ
            """)
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Lỗi khi lưu database: {e}")

if __name__ == '__main__':
    create_booking_data() 