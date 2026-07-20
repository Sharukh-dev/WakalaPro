from extensions import db
from datetime import datetime, timedelta

class License(db.Model):
    __tablename__ = 'licenses'
    
    id = db.Column(db.Integer, primary_key=True)
    license_key = db.Column(db.String(100), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_used = db.Column(db.Boolean, default=False)
    customer_name = db.Column(db.String(100))
    customer_email = db.Column(db.String(120))
    customer_phone = db.Column(db.String(20))
    duration_days = db.Column(db.Integer, default=30)
    activated_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    days_remaining = db.Column(db.Integer, default=30)
    used_by = db.Column(db.String(100))
    used_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    
    # Reminders
    reminder_sent_7 = db.Column(db.Boolean, default=False)
    reminder_sent_3 = db.Column(db.Boolean, default=False)
    reminder_sent_1 = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def is_expired(self):
        """Check if license is expired"""
        if not self.is_active:
            return True
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Check if license is valid and not used"""
        return self.is_active and not self.is_used and not self.is_expired()
    
    def get_days_remaining(self):
        """Get remaining days"""
        if self.is_expired():
            return 0
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)
    
    def get_hours_remaining(self):
        """Get remaining hours"""
        if self.is_expired():
            return 0
        delta = self.expires_at - datetime.utcnow()
        return max(0, int(delta.total_seconds() / 3600))
    
    def use_license(self, username=None):
        """Mark license as used"""
        self.is_used = True
        self.is_active = True
        self.used_by = username or 'system'
        self.used_at = datetime.utcnow()
        db.session.commit()
        return True
    
    def extend_license(self, days=30):
        """Extend license by days and reset one-time use"""
        self.expires_at = self.expires_at + timedelta(days=days)
        self.days_remaining = self.get_days_remaining()
        self.is_active = True
        self.is_used = False
        self.used_by = None
        self.used_at = None
        self.reminder_sent_7 = False
        self.reminder_sent_3 = False
        self.reminder_sent_1 = False
        db.session.commit()
        return self.days_remaining
    
    def should_send_reminder(self):
        """Check if reminder should be sent"""
        days = self.get_days_remaining()
        
        if self.is_used or not self.is_active:
            return None
        
        if days <= 7 and days > 3 and not self.reminder_sent_7:
            self.reminder_sent_7 = True
            db.session.commit()
            return '7_days'
        
        if days <= 3 and days > 1 and not self.reminder_sent_3:
            self.reminder_sent_3 = True
            db.session.commit()
            return '3_days'
        
        if days <= 1 and days > 0 and not self.reminder_sent_1:
            self.reminder_sent_1 = True
            db.session.commit()
            return '1_day'
        
        if days <= 0 and self.is_active:
            self.is_active = False
            db.session.commit()
            return 'expired_today'
        
        return None
    
    def __repr__(self):
        return f'<License {self.license_key} - {self.days_remaining} days>'