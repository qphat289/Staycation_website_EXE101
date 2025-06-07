from app import app, db
from models import Room

with app.app_context():
    rooms = Room.query.all()
    for room in rooms:
        print(f"Room: {room.title} - Type: '{room.room_type}'") 