from app import app
from extensions import db
from models.user import User

with app.app_context():
    # Check if admin already exists
    existing_user = User.query.filter_by(
        username="admin"
    ).first()

    if existing_user:
        print("Admin user already exists")
    else:
        user = User(
            username="admin",
            role="admin"
        )
        user.set_password("admin123")
        db.session.add(user)
        db.session.commit()
        print("Admin created successfully")