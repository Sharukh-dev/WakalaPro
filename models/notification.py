from extensions import db
from datetime import datetime

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), default='general')
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id])
    
    def __repr__(self):
        return f'<Notification {self.title}>'
# models/notification.py - Ongeza hii
def check_low_float():
    """Check all merchants for low float"""
    merchants = Merchant.query.all()
    for merchant in merchants:
        # Check network balances
        networks = ['vodacom', 'airtel', 'tigo', 'halotel', 'zantel']
        for network in networks:
            balance = getattr(merchant, f'balance_{network}', 0)
            if balance < 50000:  # Low float threshold
                # Send notification
                notification = Notification(
                    user_id=merchant.id,
                    title=f'Low Float Alert - {network.capitalize()}',
                    message=f'Balance is TSh {balance:,.0f}. Please top up.',
                    notification_type='float_alert'
                )
                db.session.add(notification)
    db.session.commit()