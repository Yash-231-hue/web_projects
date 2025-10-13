from app import app
from models import db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    # Check if admin123 exists
    existing = User.query.filter_by(username='admin123').first()
    if existing:
        print("User admin123 already exists")
        print(f"Admin: {existing.is_admin}")
        print(f"Hash: {existing.password_hash}")
        # Update to admin if not already
        if not existing.is_admin:
            existing.is_admin = True
            db.session.commit()
            print("Updated to admin")
    else:
        # Create new admin user with unique email
        hashed = generate_password_hash('admin@123')
        admin = User(
            username='admin123',
            email='admin123@example.com',  # Changed to avoid duplicate
            password_hash=hashed,
            contact='+91-XXXXXXXXXX',
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully")
        print(f"Username: admin123")
        print(f"Password: admin@123")
        print(f"Hash: {hashed}")
