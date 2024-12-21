import os
import sqlite3
from datetime import datetime

import stripe
from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import current_user

from dbinit import app

stripe.api_key = 'sk_test_...'  # Replace with your actual Stripe secret key


@app.route('/process_payment', methods=['POST'])
def process_payment():
    try:
        # Retrieve JSON data from the request
        data = request.get_json()

        # Extract information from the JSON
        payment_method_id = data.get('payment_method_id')
        amount = data.get('amount')
        flight_id = data.get('flight_id')
        first_name = data.get('firstName')
        last_name = data.get('lastName')
        email = data.get('email')

        # Print the retrieved data for debugging
        print(
            f"Received payment details: Payment Method ID: {payment_method_id}, Amount: {amount}, Flight ID: {flight_id}, First Name: {first_name}, Last Name: {last_name}, Email: {email}")

        # Get current date and time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Insert into reservations table
        conn = sqlite3.connect('airline_reservation.db')
        cursor = conn.cursor()

        # Include current_time in the last_notification_received column
        cursor.execute("INSERT INTO reservations (flight_id, email, last_notification_received) VALUES (?, ?, ?)",
                       (flight_id, email, current_time))
        reservation_id = cursor.lastrowid

        # Insert into payments table
        cursor.execute("INSERT INTO payments (reservation_id, amount) VALUES (?, ?)",
                       (reservation_id, amount))

        # adds a function to add one to the employee's sales if they are who is buying the flight
        if current_user.is_authenticated and current_user.employee_status and (current_user.email != email):
            # Connect to the SQLite database
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (current_user.id,))

            # Fetch flight in question
            user = cursor.fetchone()

            new_user_sales = user[6] + 1

            # Base SQL query
            cursor.execute('UPDATE users SET sales = ? WHERE user_id = ?', (new_user_sales, user[0]))

        # Commit the changes and close the connection
        conn.commit()
        conn.close()

        return jsonify({'success': True}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400