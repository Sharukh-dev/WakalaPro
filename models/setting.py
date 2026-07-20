from extensions import db


class Setting(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )


    name = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )


    value = db.Column(
        db.Float,
        nullable=False
    )