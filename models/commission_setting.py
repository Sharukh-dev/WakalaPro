from extensions import db
from datetime import datetime

class CommissionSetting(db.Model):
    __tablename__ = 'commission_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    network = db.Column(db.String(50), nullable=False)  # Vodacom, Airtel, Tigo, Halotel, Zantel, CRDB, NMB
    transaction_type = db.Column(db.String(20), default='all')  # deposit, withdraw, transfer, payment, all
    rate = db.Column(db.Float, default=0.0)  # Percentage e.g. 1.5 = 1.5% - KEEP DECIMAL
    fixed_amount = db.Column(db.Float, default=0.0)  # Fixed amount per transaction - KEEP DECIMAL
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Ensure unique combination of network and transaction_type
    __table_args__ = (
        db.UniqueConstraint('network', 'transaction_type', name='unique_network_transaction'),
    )
    
    def __repr__(self):
        return f'<CommissionSetting {self.network} - {self.transaction_type}: {self.rate}%>'