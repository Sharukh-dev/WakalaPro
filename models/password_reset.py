from extensions import db
from datetime import datetime, timedelta
import secrets

class PasswordReset(db.Model):
    __tablename__ = 'password_resets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', foreign_keys=[user_id])
    
    @classmethod
    def generate_token(cls, user_id):
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        reset = cls(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        db.session.add(reset)
        db.session.commit()
        return token
    
    @classmethod
    def verify_token(cls, token):
        reset = cls.query.filter_by(token=token, is_used=False).first()
        
        if not reset:
            return None
        
        if datetime.utcnow() > reset.expires_at:
            return None
        
        return reset
    
    def mark_used(self):
        self.is_used = True
        db.session.commit()