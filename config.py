import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
    STRIPE_SECRET_KEY = os.getenv('redacted')
    MAIL_USERNAME = os.getenv('redacted')
    MAIL_PASSWORD = os.getenv('redacted')
