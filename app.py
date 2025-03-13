from flask import Flask, render_template
from flask_login import LoginManager
import os
from models import db, User, Homestay, Booking
from flask_migrate import Migrate

# Initialize Flask app
app = Flask(__name__)
app.config.from_object('config.Config')

# Initialize database
db.init_app(app)
migrate = Migrate(app, db)

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
from routes.owner import owner_bp
from routes.renter import renter_bp
app.register_blueprint(auth_bp)
app.register_blueprint(owner_bp)
app.register_blueprint(renter_bp)



# Home route
@app.route('/')
def home():
    # Get some featured homestays to display on homepage
    homestays = Homestay.query.limit(6).all()
    return render_template('home.html', homestays=homestays)

if __name__ == '__main__':
    app.run(debug=True)