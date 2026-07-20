from extensions import db
from datetime import datetime

class Operator(db.Model):
    __tablename__ = 'operators'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    address = db.Column(db.String(200))
    status = db.Column(db.String(20), default='active')
    
    # Network Commissions - DECIMAL (Float)
    # Airtel
    airtel_deposit = db.Column(db.Float, default=0.0)
    airtel_withdraw = db.Column(db.Float, default=0.0)
    airtel_airtime = db.Column(db.Float, default=0.0)
    
    # Vodacom
    vodacom_deposit = db.Column(db.Float, default=0.0)
    vodacom_withdraw = db.Column(db.Float, default=0.0)
    vodacom_airtime = db.Column(db.Float, default=0.0)
    
    # Tigo
    tigo_deposit = db.Column(db.Float, default=0.0)
    tigo_withdraw = db.Column(db.Float, default=0.0)
    tigo_airtime = db.Column(db.Float, default=0.0)
    
    # Halotel
    halotel_deposit = db.Column(db.Float, default=0.0)
    halotel_withdraw = db.Column(db.Float, default=0.0)
    halotel_airtime = db.Column(db.Float, default=0.0)
    
    # Zantel
    zantel_deposit = db.Column(db.Float, default=0.0)
    zantel_withdraw = db.Column(db.Float, default=0.0)
    zantel_airtime = db.Column(db.Float, default=0.0)
    
    # Bank Commissions - DECIMAL (Float)
    # CRDB
    crdb_deposit = db.Column(db.Float, default=0.0)
    crdb_withdraw = db.Column(db.Float, default=0.0)
    crdb_payment = db.Column(db.Float, default=0.0)
    
    # NMB
    nmb_deposit = db.Column(db.Float, default=0.0)
    nmb_withdraw = db.Column(db.Float, default=0.0)
    nmb_payment = db.Column(db.Float, default=0.0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with User
    user = db.relationship('User', back_populates='operator', foreign_keys=[user_id])
    
    def get_network_commission(self, network, transaction_type):
        """Get commission for specific network and transaction type - returns float"""
        mapping = {
            'Airtel': {
                'deposit': self.airtel_deposit,
                'withdraw': self.airtel_withdraw,
                'airtime': self.airtel_airtime
            },
            'Vodacom': {
                'deposit': self.vodacom_deposit,
                'withdraw': self.vodacom_withdraw,
                'airtime': self.vodacom_airtime
            },
            'Tigo': {
                'deposit': self.tigo_deposit,
                'withdraw': self.tigo_withdraw,
                'airtime': self.tigo_airtime
            },
            'Halotel': {
                'deposit': self.halotel_deposit,
                'withdraw': self.halotel_withdraw,
                'airtime': self.halotel_airtime
            },
            'Zantel': {
                'deposit': self.zantel_deposit,
                'withdraw': self.zantel_withdraw,
                'airtime': self.zantel_airtime
            }
        }
        return mapping.get(network, {}).get(transaction_type, 0.0)
    
    def get_bank_commission(self, bank, transaction_type):
        """Get commission for specific bank and transaction type - returns float"""
        mapping = {
            'CRDB': {
                'deposit': self.crdb_deposit,
                'withdraw': self.crdb_withdraw,
                'payment': self.crdb_payment
            },
            'NMB': {
                'deposit': self.nmb_deposit,
                'withdraw': self.nmb_withdraw,
                'payment': self.nmb_payment
            }
        }
        return mapping.get(bank, {}).get(transaction_type, 0.0)

    def __repr__(self):
        return f'<Operator {self.full_name}>'