from flask import Flask, render_template, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import os
from config import Config
from models import db, Admin, Owner, Renter, Homestay

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Khởi tạo database, migrations, login manager
    db.init_app(app)
    migrate = Migrate(app, db)
    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        role = session.get('user_role')
        if role == 'admin':
            return Admin.query.get(int(user_id))
        elif role == 'owner':
            return Owner.query.get(int(user_id))
        elif role == 'renter':
            return Renter.query.get(int(user_id))
        return None

    # Tạo bảng và thêm admin nếu cần
    with app.app_context():
        db.create_all()
        print("Database tables created successfully.")

        # Thay vì User, ta dùng Admin để kiểm tra admin
        existing_admin = Admin.query.filter_by(username='admin').first()
        if existing_admin:
            print("Admin user already exists and is an admin.")
        else:
            admin_user = Admin(username='admin', email='admin@example.com')
            admin_user.set_password('123')
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created.")

    # Import và đăng ký các blueprint
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
        # Lấy một số homestay nổi bật để hiển thị trên trang chủ
        homestays = Homestay.query.limit(6).all()
        return render_template('home.html', homestays=homestays)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)