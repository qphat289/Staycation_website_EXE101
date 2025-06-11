from app import app, db
from app.models.models import Room

with app.app_context():
    # Update tất cả phòng có room_type = 'Standard' thành 'Mô hình chuẩn'
    rooms = Room.query.filter_by(room_type='Standard').all()
    
    for room in rooms:
        print(f"Updating room: {room.title} - '{room.room_type}' -> 'Mô hình chuẩn'")
        room.room_type = 'Mô hình chuẩn'
    
    db.session.commit()
    print(f"Updated {len(rooms)} rooms successfully!")
    
    # Verify the changes
    print("\nCurrent room types:")
    all_rooms = Room.query.all()
    for room in all_rooms:
        print(f"- {room.title}: '{room.room_type}'") 