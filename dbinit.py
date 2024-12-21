import os
import sqlite3
import stripe
from flask import Flask
from flask_login import LoginManager, UserMixin
from flask_mail import Mail
#from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_default_secret_key')

# Stripe configuration
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'redacted'  # Use your actual Gmail address
app.config['MAIL_PASSWORD'] = 'redacted'     # Use your generated App Password
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)

# Flask-Login configuration
login_manager = LoginManager()
login_manager.init_app(app)

# User loader
class User(UserMixin):
    def __init__(self, user_id, first_name, last_name, email, employee_status):
        self.id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.employee_status = employee_status

@login_manager.user_loader
def load_user_by_id(user_id):
    conn = sqlite3.connect('airline_reservation.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user_row = cursor.fetchone()
    conn.close()
    return User(user_row[0], user_row[1], user_row[2], user_row[3], user_row[5]) if user_row else None

# Database initialization
def init_db():
    conn = sqlite3.connect('airline_reservation.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flights (
            flight_id INTEGER PRIMARY KEY,
            origin TEXT,
            destination TEXT,
            date TEXT,
            seats_available INTEGER,
            ticket_price FLOAT,
            status TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            reservation_id INTEGER PRIMARY KEY,
            flight_id INTEGER,
            email INTEGER,
            FOREIGN KEY (flight_id) REFERENCES flights (flight_id)
            FOREIGN KEY (email) REFERENCES users (email)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            employee_status BOOLEAN,
            sales INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            payment_id INTEGER PRIMARY KEY,
            reservation_id INTEGER,
            amount REAL,
            status TEXT,
            FOREIGN KEY (reservation_id) REFERENCES reservations (reservation_id)
        )
    ''')

    conn.commit()
    conn.close()
