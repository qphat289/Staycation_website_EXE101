from flask import Flask, render_template
from flask_login import LoginManager
import os
from models import db, User, Homestay, Booking

def create_app():
    # Initialize Flask app
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Initialize database
    db.init_app(app)

    with app.app_context():
        existing_admin = User.query.filter_by(username='admin').first()
        if not existing_admin:
            admin_user = User(username='admin', email='admin@example.com')
            admin_user.set_password('123')
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created.")
        else:
            print("Admin user already exists. Skipping creation.")

    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Create database tables
    with app.app_context():
        db.create_all()

    # Register blueprints
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.owner import owner_bp
    from routes.renter import renter_bp

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

    # Return the Flask app instance
    return app

if __name__ == '__main__':
    myapp = create_app()
    myapp.run(debug=True)
