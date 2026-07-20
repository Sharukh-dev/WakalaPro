from app import app
from extensions import db

from models.setting import Setting


with app.app_context():


    settings = [

        Setting(
            name="Deposit",
            value=1
        ),

        Setting(
            name="Withdrawal",
            value=0.5
        ),

        Setting(
            name="Airtime",
            value=2
        )

    ]


    for s in settings:

        exists = Setting.query.filter_by(
            name=s.name
        ).first()


        if not exists:

            db.session.add(s)



    db.session.commit()


    print("Commission settings created")