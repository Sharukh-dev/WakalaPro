from extensions import db
from datetime import datetime

class BusinessSettings(db.Model):
    __tablename__ = 'business_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(200), default='')
    phone = db.Column(db.String(20), default='')
    address = db.Column(db.String(200), default='')
    currency = db.Column(db.String(10), default='TSh')
    receipt_footer = db.Column(db.Text, default='Thank you for using WakalaPro')
    email = db.Column(db.String(100), default='')
    website = db.Column(db.String(100), default='')
    tax_id = db.Column(db.String(50), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_settings(cls):
        """Get or create settings"""
        settings = cls.query.first()
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings
    
    def __repr__(self):
        return f'<BusinessSettings {self.business_name}>'