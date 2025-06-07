from app import app, db
from models import Room, RoomImage
import os
import shutil

with app.app_context():
    # Tìm phòng Vitamin Homestay
    room = Room.query.filter_by(title="Vitamin Homestay").first()
    if not room:
        print("Không tìm thấy phòng Vitamin Homestay")
        exit()
    
    print(f"Tìm thấy phòng: {room.title} (ID: {room.id})")
    
    # Tạo folder cho phòng này
    room_folder = os.path.join('static', 'uploads', f'room_{room.id}')
    os.makedirs(room_folder, exist_ok=True)
    print(f"Tạo folder: {room_folder}")
    
    # Xử lý ảnh chính
    main_image_path = 'static/temp/temp_main_20250607192423_487450997_122126904968650841_6112939320948822812_n.jpg'
    if os.path.exists(main_image_path):
        new_filename = 'main_image.jpg'
        new_path = os.path.join(room_folder, new_filename)
        shutil.copy2(main_image_path, new_path)
        print(f"Copy ảnh chính: {main_image_path} -> {new_path}")
        
        # Tạo record trong database
        main_img = RoomImage(
            image_path=f"uploads/room_{room.id}/{new_filename}",
            room_id=room.id,
            is_featured=True
        )
        db.session.add(main_img)
        print("Tạo record ảnh chính trong database")
    
    # Xử lý các ảnh khác
    other_images = [
        'static/temp/temp_20250607192423942_487784143_122126904974650841_7931302405065570669_n.jpg',
        'static/temp/temp_20250607192423942_491228319_122129269718650841_24205744731069936_n.jpg',
        'static/temp/temp_20250607192423943_491752661_122129269736650841_8240912436428560810_n.jpg',
        'static/temp/temp_20250607192423943_494088373_122132381822650841_5673470517377745263_n.jpg',
        'static/temp/temp_20250607192423944_494738597_122132381684650841_4317289004997217671_n.jpg',
        'static/temp/temp_20250607192423946_496859043_122134882850650841_2578057475203246396_n.jpg'
    ]
    
    for i, image_path in enumerate(other_images):
        if os.path.exists(image_path):
            new_filename = f'image_{i+1}_photo.jpg'
            new_path = os.path.join(room_folder, new_filename)
            shutil.copy2(image_path, new_path)
            print(f"Copy ảnh {i+1}: {image_path} -> {new_path}")
            
            # Tạo record trong database
            img = RoomImage(
                image_path=f"uploads/room_{room.id}/{new_filename}",
                room_id=room.id,
                is_featured=False
            )
            db.session.add(img)
            print(f"Tạo record ảnh {i+1} trong database")
    
    # Commit tất cả thay đổi
    db.session.commit()
    print("✅ Đã migrate tất cả ảnh thành công!")
    
    # Kiểm tra kết quả
    room = Room.query.get(room.id)  # Reload để lấy ảnh mới
    db.session.refresh(room)
    print(f"Phòng hiện có {len(room.images)} ảnh:")
    for img in room.images:
        print(f"  - {img.image_path} (featured: {img.is_featured})") 