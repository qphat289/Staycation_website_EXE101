from app import app, db
from app.models.models import Home

with app.app_context():
    # Update tất cả nhà có home_type = 'Standard' thành 'Mô hình chuẩn'
    homes = Home.query.filter_by(home_type='Standard').all()
    
    for home in homes:
        print(f"Updating home: {home.title} - '{home.home_type}' -> 'Mô hình chuẩn'")
        home.home_type = 'Mô hình chuẩn'
    
    db.session.commit()
    print(f"Updated {len(homes)} homes successfully!")
    
    # Verify the changes
    print("\nCurrent home types:")
    all_homes = Home.query.all()
    for home in all_homes:
        print(f"- {home.title}: '{home.home_type}'") 