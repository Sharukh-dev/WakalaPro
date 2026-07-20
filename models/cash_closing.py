from extensions import db
from datetime import datetime, date

class CashClosing(db.Model):
    __tablename__ = 'cash_closings'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=date.today, unique=True)
    opening_cash = db.Column(db.Float, default=0.0)
    total_deposit = db.Column(db.Float, default=0.0)
    total_withdraw = db.Column(db.Float, default=0.0)
    total_airtime = db.Column(db.Float, default=0.0)
    total_commission = db.Column(db.Float, default=0.0)
    total_expenses = db.Column(db.Float, default=0.0)
    closing_cash = db.Column(db.Float, default=0.0)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id])
    
    def __repr__(self):
        return f'<CashClosing {self.date}>'