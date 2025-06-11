from app import app
from models import db

def recreate_database():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        print("✓ Đã xóa tất cả các bảng")
        
        # Create all tables
        db.create_all()
        print("✓ Đã tạo lại tất cả các bảng")
        
        print("\nĐã tạo lại database thành công!")

if __name__ == "__main__":
    recreate_database() 