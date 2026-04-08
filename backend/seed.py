from extensions import db
from models import User
import bcrypt


def seed_admin():
    existing = User.query.filter_by(role="admin").first()
    if existing:
        return

    password_hash = bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    admin = User(
        email="admin@placement.com",
        password=password_hash,
        role="admin",
        is_active=True,
    )

    db.session.add(admin)
    db.session.commit()
    print("Admin user created: admin@placement.com / admin123")
