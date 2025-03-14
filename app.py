from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import os
from config import Config
from models import db, User, Homestay  # Adjust imports to your structure
from routes.renter import get_rank_info

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize database, migrations, login manager
    db.init_app(app)
    migrate = Migrate(app, db)
    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Create tables, add admin user if needed
    with app.app_context():
        db.create_all()
        print("Database tables created successfully.")

        existing_admin = User.query.filter_by(username='admin').first()
        if existing_admin: 
            if existing_admin.role != 'admin':
                existing_admin.role = 'admin'
                db.session.commit()
                print("Existing admin user updated to role='admin'.")
        else:
            print("Admin user already exists and is an admin.")
        if not existing_admin:
            admin_user = User(username='admin', email='admin@example.com')
            admin_user.set_password('123')
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created.")
        else:
            print("Admin user already exists. Skipping creation.")
            
    # Register a Jinja filter for rank info
    @app.template_filter('rank_info')
    def rank_info_filter(xp):
        """Wraps get_rank_info to make it a Jinja filter."""
        return get_rank_info(xp)

    # Import and register blueprints
    from routes.auth import auth_bp
    from routes.owner import owner_bp
    from routes.renter import renter_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(owner_bp)
    app.register_blueprint(renter_bp)
    app.register_blueprint(admin_bp)

    # Home route
    @app.route('/')
    def home():
        # Get some featured homestays to display on homepage
        homestays = Homestay.query.limit(6).all()
        return render_template('home.html', homestays=homestays)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
