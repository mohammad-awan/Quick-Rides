import os

from app import db
from app.models import Admin
from werkzeug.security import generate_password_hash


def create_admin_if_not_exists():
    admin_username = os.environ.get('DEFAULT_ADMIN_USERNAME', 'admin@example.com')
    existing_admin = Admin.query.filter_by(username=admin_username).first()
    if not existing_admin:
        admin = Admin(
            first_name=os.environ.get('DEFAULT_ADMIN_FIRST_NAME', 'Muhammad'),
            last_name=os.environ.get('DEFAULT_ADMIN_LAST_NAME', 'Awan'),
            username=admin_username,
            password=generate_password_hash(os.environ.get('DEFAULT_ADMIN_PASSWORD', 'change-me'))
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin created.")
