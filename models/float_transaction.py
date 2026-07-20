from extensions import db
from datetime import datetime


class FloatTransaction(db.Model):

    __tablename__ = "float_transaction"


    id = db.Column(
        db.Integer,
        primary_key=True
    )


    operator_id = db.Column(
        db.Integer,
        db.ForeignKey("operator.id"),
        nullable=False
    )


    merchant_id = db.Column(
        db.Integer,
        db.ForeignKey("merchant.id"),
        nullable=False
    )


    action = db.Column(
        db.String(20),
        nullable=False
    )
    # ADD or REMOVE


    amount = db.Column(
        db.Float,
        nullable=False
    )


    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


    operator = db.relationship(
        "Operator",
        back_populates="float_transactions"
    )


    merchant = db.relationship(
        "Merchant",
        back_populates="float_transactions"
    )