from flask import Flask

def create_app():
    app = Flask(__name__)
    # Thêm các cấu hình, đăng ký blueprint, db... nếu cần
    return app

# Flask app package
