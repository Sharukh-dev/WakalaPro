from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from extensions import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)  # ADDED: Email field
    phone_number = db.Column(db.String(20), unique=True, nullable=True)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='cashier')
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key to Merchant - cashier assigned to specific merchant
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchants.id'), nullable=True)

    # Relationships
    operator = db.relationship('Operator', back_populates='user', uselist=False, cascade='all, delete-orphan')
    merchant = db.relationship('Merchant', foreign_keys=[merchant_id], backref='users')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_permission(self, required_role):
        """Check if user has required role permission"""
        roles = {
            'admin': 4,
            'manager': 3,
            'cashier': 2,
            'viewer': 1
        }
        user_level = roles.get(self.role.lower(), 1)
        required_level = roles.get(required_role.lower(), 1)
        return user_level >= required_level

    def __repr__(self):
        return f'<User {self.username}>'