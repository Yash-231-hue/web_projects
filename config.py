import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super_secret_key_123'

    # MySQL database configuration
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://yash:Yash%402005@localhost:3306/clinicdb'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Admin contact info
    ADMIN_EMAIL = 'admin@example.com'
    ADMIN_CONTACT = '+91-XXXXXXXXXX'
