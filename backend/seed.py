from extensions import db
from models import User
import bcrypt

def seed_admin():
    if User.query.filter_by(role="admin").first():
        return
    pw = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
    db.session.add(User(email="admin@placement.com", password=pw, role="admin", is_active=True))
    db.session.commit()
    print("Admin seeded: admin@placement.com / admin123")
