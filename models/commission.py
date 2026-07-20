from extensions import db
from datetime import datetime

class Commission(db.Model):
    __tablename__ = 'commissions'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=False)
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchants.id'), nullable=False)
    operator_id = db.Column(db.Integer, db.ForeignKey('operators.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    transaction = db.relationship('Transaction', foreign_keys=[transaction_id])
    merchant = db.relationship('Merchant', foreign_keys=[merchant_id])
    operator = db.relationship('Operator', foreign_keys=[operator_id])
    
    def __repr__(self):
        return f'<Commission {self.id}>'