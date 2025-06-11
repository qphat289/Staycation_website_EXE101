from app import app, db
from app.models.models import Room, RoomImage

with app.app_context():
    room = Room.query.filter_by(title="Vitamin Homestay").first()
    if room:
        print(f"Room ID: {room.id}")
        print(f"Room Images: {len(room.images)}")
        for img in room.images:
            print(f"  - {img.image_path} (featured: {img.is_featured})")
    else:
        print("Không tìm thấy phòng") 