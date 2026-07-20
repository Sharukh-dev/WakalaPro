from extensions import db
from datetime import datetime

class MerchantOperatorBalance(db.Model):
    __tablename__ = 'merchant_operator_balance'
    
    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchants.id'), nullable=False)
    operator_id = db.Column(db.Integer, db.ForeignKey('operators.id'), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    merchant = db.relationship('Merchant', foreign_keys=[merchant_id])
    operator = db.relationship('Operator', foreign_keys=[operator_id])
    
    def __repr__(self):
        return f'<MerchantOperatorBalance {self.merchant_id}-{self.operator_id}>'