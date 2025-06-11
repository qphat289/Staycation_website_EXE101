from app import create_app
from models import db, Admin, Owner, Renter, Homestay, Room, Booking, Review, Statistics

def clear_database():
    app = create_app()
    with app.app_context():
        try:
            # Lưu lại admin user
            admin = Admin.query.first()
            
            # Xóa tất cả dữ liệu từ các bảng theo thứ tự (để tránh lỗi foreign key)
            print("Đang xóa dữ liệu...")
            
            # Xóa reviews
            Review.query.delete()
            print("✓ Đã xóa reviews")
            
            # Xóa bookings
            Booking.query.delete()
            print("✓ Đã xóa bookings")
            
            # Xóa rooms
            Room.query.delete()
            print("✓ Đã xóa rooms")
            
            # Xóa homestays
            Homestay.query.delete()
            print("✓ Đã xóa homestays")
            
            # Reset statistics
            Statistics.query.delete()
            print("✓ Đã xóa statistics")
            
            # Xóa tất cả users trừ admin
            if admin:
                Owner.query.delete()
                Renter.query.delete()
                print("✓ Đã xóa owners và renters (giữ lại admin)")
            else:
                print("! Không tìm thấy tài khoản admin")
            
            # Commit các thay đổi
            db.session.commit()
            print("\nĐã xóa thành công tất cả dữ liệu (giữ lại admin)")
            
            if admin:
                print(f"\nThông tin admin còn lại:")
                print(f"Username: {admin.username}")
                print(f"Email: {admin.email}")
                print(f"Role: {admin.role}")
            
        except Exception as e:
            db.session.rollback()
            print(f"\nLỗi khi xóa dữ liệu: {str(e)}")
            raise e

if __name__ == "__main__":
    clear_database() 