from app import app, db
from app.models.models import Home

with app.app_context():
    homes = Home.query.all()
    for home in homes:
        print(f"Home: {home.title} - Type: '{home.home_type}'") 