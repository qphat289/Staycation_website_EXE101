from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
import os

# Xóa file database cũ nếu tồn tại
if os.path.exists('instance/homestay.db'):
    os.remove('instance/homestay.db')

# Tạo ứng dụng Flask
app = Flask(__name__)
app.config.from_object(Config)

# Khởi tạo database
db = SQLAlchemy(app)

# Import các model sau khi đã khởi tạo db
from models import Admin, Owner, Renter, Room, Booking, Review, Amenity, RoomImage, Statistics

# Tạo tất cả các bảng
with app.app_context():
    db.create_all()
    print("Đã tạo database mới thành công!") 