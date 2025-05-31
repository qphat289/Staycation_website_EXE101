from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from database import db

class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    display_name = db.Column(db.String(80))
    avatar = db.Column(db.String(200))
    role = db.Column(db.String(20), default='admin')
    is_super_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Các quyền của admin
    can_manage_admins = db.Column(db.Boolean, default=False)
    can_approve_changes = db.Column(db.Boolean, default=False)
    can_view_all_stats = db.Column(db.Boolean, default=True)
    can_manage_users = db.Column(db.Boolean, default=True)
    
    def __init__(self, username, email, display_name=None, is_super_admin=False):
        self.username = username
        self.email = email
        self.display_name = display_name or username
        self.is_super_admin = is_super_admin
        
        # Tự động set quyền dựa vào loại admin
        if is_super_admin:
            self.can_manage_admins = True
            self.can_approve_changes = True
            self.can_view_all_stats = True
            self.can_manage_users = True
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    # Kiểm tra các quyền
    def can_create_admin(self):
        return self.is_super_admin and self.can_manage_admins
    
    def can_delete_admin(self):
        return self.is_super_admin and self.can_manage_admins
    
    def can_modify_admin(self):
        return self.is_super_admin and self.can_manage_admins
    
    def can_approve_system_changes(self):
        return self.is_super_admin and self.can_approve_changes 