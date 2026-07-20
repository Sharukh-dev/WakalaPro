from extensions import db
from datetime import datetime

class Merchant(db.Model):
    __tablename__ = 'merchants'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(200), default='')
    network = db.Column(db.String(20), default='')  # Inaweza kuwa empty
    cash_in_hand = db.Column(db.Float, default=0.0)
    opening_balance = db.Column(db.Float, default=0.0)
    current_balance = db.Column(db.Float, default=0.0)
    
    # Bank Balances (simple - one balance each)
    crdb_balance = db.Column(db.Float, default=0.0)
    nmb_balance = db.Column(db.Float, default=0.0)
    
    # Network balances (kila network ina balance yake)
    balance_vodacom = db.Column(db.Float, default=0.0)
    balance_airtel = db.Column(db.Float, default=0.0)
    balance_tigo = db.Column(db.Float, default=0.0)
    balance_halotel = db.Column(db.Float, default=0.0)
    balance_zantel = db.Column(db.Float, default=0.0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_network_total(self):
        """Get total network balance across all networks"""
        return (self.balance_vodacom + self.balance_airtel + self.balance_tigo + 
                self.balance_halotel + self.balance_zantel)
    
    def get_network_balance(self, network):
        """Get balance for specific network"""
        mapping = {
            'Vodacom': self.balance_vodacom,
            'Airtel': self.balance_airtel,
            'Tigo': self.balance_tigo,
            'Halotel': self.balance_halotel,
            'Zantel': self.balance_zantel
        }
        return mapping.get(network, 0)

    def get_total_balance(self):
        """Get total balance (cash + networks + banks)"""
        return (self.cash_in_hand + self.get_network_total() + 
                self.crdb_balance + self.nmb_balance)

    def __repr__(self):
        return f'<Merchant {self.name}>'