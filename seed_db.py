from app import create_app
from scripts.seed_data import seed_owners

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        seed_owners()
        print("Seeded database successfully!") 