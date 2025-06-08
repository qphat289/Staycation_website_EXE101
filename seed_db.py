from app import *
from scripts.seed_data import seed_owners

if __name__ == '__main__':
    with app.app_context():
        seed_owners()
        print("Seeded database successfully!") 