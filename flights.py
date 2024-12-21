import sqlite3
import os
from flask_mail import Message
import dbinit
from dbinit import mail, app
from flask import request, render_template, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user

# creates new user account into user database
def create_user(email, password, first_name, last_name):
    new_user = [email, password, first_name, last_name]

    conn = sqlite3.connect('airline_reservation.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO users (email, password, first_name, last_name)
        Values (?, ?, ?, ?)
    ''', (new_user[0], new_user[1], new_user[2], new_user[3]))
    conn.commit()
    conn.close()

# Function to add an assortment of flights to the database
def add_flights():
    flights_data = [
        ('Jacksonville', 'San Francisco', '2024-11-27', 100),
        ('Anchorage', 'Las Vegas', '2024-11-26', 50),
        ('Chicago', 'Las Vegas', '2024-11-25', 75),
        ('Houston', 'Boston', '2024-11-24', 60),
        ('Dallas', 'Denver', '2024-11-23', 80),
        ('Raleigh', 'Dallas', '2024-11-22', 90),
        ('Dallas', 'Tampa', '2024-11-22', 30)
    ]

    conn = sqlite3.connect('airline_reservation.db')
    cursor = conn.cursor()

    for flight in flights_data:
        # Check if the flight already exists
        cursor.execute('''
            SELECT COUNT(*) FROM flights
            WHERE origin = ? AND destination = ? AND date = ?
        ''', (flight[0], flight[1], flight[2]))

        exists = cursor.fetchone()[0]

        # Only insert if the flight does not exist
        if exists == 0:
            cursor.execute('''
                INSERT INTO flights (origin, destination, date, seats_available, ticket_price, status)
                VALUES (?, ?, ?, ?, 100, 'Scheduled')
            ''', flight)

    conn.commit()
    conn.close()

# Function to delete duplicate flight entries from the database
def delete_duplicate_flights():
    conn = sqlite3.connect('airline_reservation.db')
    cursor = conn.cursor()

    # Create a temporary table to hold unique records
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flights_temp AS
        SELECT MIN(rowid) AS rowid, origin, destination, date, seats_available
        FROM flights
        GROUP BY origin, destination, date;
    ''')

    # Delete all records from the original flights table
    cursor.execute('DELETE FROM flights')

    # Insert unique records back into the original flights table
    cursor.execute('''
        INSERT INTO flights (origin, destination, date, seats_available)
        SELECT origin, destination, date, seats_available
        FROM flights_temp;
    ''')

    # Drop the temporary table
    cursor.execute('DROP TABLE flights_temp')

    conn.commit()
    conn.close()

# Searches flights by a set of user defined criteria
def search_details(flight_id=None, origin=None, destination=None, date=None, seats_available=None):
    # Connect to the SQLite database
    conn = sqlite3.connect('airline_reservation.db')
    cursor = conn.cursor()

    # Base SQL query
    query = "SELECT * FROM flights WHERE 1=1"  # The `1=1` is a trick to facilitate appending conditions
    parameters = []

    # Append conditions based on user inputs
    if flight_id:
        query += " AND flight_id = ?"
        parameters.append(flight_id)
    if origin:
        query += " AND origin LIKE ?"
        parameters.append("%" + origin + "%")
    if destination:
        query += " AND destination LIKE ?"
        parameters.append("%" + destination + "%")
    if date:
        query += " AND date = ?"
        parameters.append(date)
    if seats_available:
        query += " AND seats_available >= ?"
        parameters.append(seats_available)

    # Execute the query
    cursor.execute(query, parameters)

    # Fetch all matching records
    flights = cursor.fetchall()

    flight_details = []
    for flight in flights:
        flight_info = {
            'flight_id': flight[0],
            'origin': flight[1],
            'destination': flight[2],
            'date': flight[3],
            'seats_available': flight[4],
            'ticket_price': ('$'+str(float(flight[5])/100)),
            'status': flight[6]
        }
        flight_details.append(flight_info)

    # Close the cursor and connection
    cursor.close()
    conn.close()
    return flight_details

# Function to get available flights based on search criteria
def get_flight_with_id(flight_id):
    # Connect to the SQLite database
    conn = sqlite3.connect('airline_reservation.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM flights 
        WHERE flight_id = ?
        ''', (flight_id,))

    # Fetch flight in question
    flight = cursor.fetchone()

    # Close the cursor and connection
    cursor.close()
    conn.close()

    if flight:
        # Format the flight details into a dictionary
        flight_info = {
            'flight_id': flight[0],
            'origin': flight[1],
            'destination': flight[2],
            'date': flight[3],
            'seats_available': flight[4],
            'ticket_price': str(float(flight[5])/100),
            'status': flight[6]
        }
        return flight_info

    return

# returns flights based off of the users email address
def get_flights_by_user_email(user_email):
    # Connect to the SQLite database
    conn = sqlite3.connect('airline_reservation.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM reservations 
        WHERE email = ?
        ''', (user_email,))

    reservations = cursor.fetchall()

    query = "SELECT * FROM flights WHERE "  # The `1=1` is a trick to facilitate appending conditions
    base_query = query
    parameters = []

    for reservation in reservations:
        if parameters == []:
            query += "flight_id = ?"
            parameters.append(reservation[1])
        else:
            query += " OR flight_id = ?"
            parameters.append(reservation[1])

    # checks if there are any query parameters, if not does not run query. It will break the page otherwise
    if query != base_query:
        cursor.execute(query, parameters)
        flights = cursor.fetchall()

        # Close the cursor and connection
        cursor.close()
        conn.close()

        flight_details = []
        for flight in flights:
            flight_info = {
                'flight_id': flight[0],
                'origin': flight[1],
                'destination': flight[2],
                'date': flight[3],
                'status': flight[6]
            }
            flight_details.append(flight_info)

        return flight_details

    return

# function to search employees based on their ID
def check_employee_stats(user_id):
    # Connect to the SQLite database
    conn = sqlite3.connect('airline_reservation.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM users 
        WHERE employee_status = 'True' AND user_id = ?
        ''', (user_id,))

    # Fetch flight in question
    user = cursor.fetchone()

    # Close the cursor and connection
    cursor.close()
    conn.close()

    if user:
        # Format the flight details into a dictionary
        user_info = {
            'user_id': user[0],
            'first_name': user[1],
            'last_name': user[2],
            'email': user[3],
            'sales': user[6]
        }
        return user_info

    return

# Creates new flights
def create_new_flight(new_flight_info):
    conn = sqlite3.connect('airline_reservation.db')
    cursor = conn.cursor()

    # create flight information
    cursor.execute('''
        INSERT INTO flights (origin, destination, date, seats_available, ticket_price, status)
        Values (?, ?, ?, ?, ?, ?)
    ''', (new_flight_info['origin'],
          new_flight_info['destination'],
          new_flight_info['date'],
          new_flight_info['seats_available'],
          new_flight_info['ticket_price'],
          new_flight_info['status']))

    conn.commit()

    # gets new flight id to pass to the new page
    flight_id = cursor.lastrowid
    conn.close()

    return flight_id

# updates existing flight information
def update_flight(new_flight_info):
    conn = sqlite3.connect('airline_reservation.db')
    cursor = conn.cursor()

    # Base SQL query
    query = 'UPDATE flights SET '

    # base query so that it can be compared against to determine if an and is need
    base_query = query
    parameters = []

    # Append conditions based on user inputs; ', ' added as need
    if new_flight_info['origin']:
        if query != base_query:
            query += ", "
        query += "origin = ?"
        parameters.append(new_flight_info['origin'])

    if new_flight_info['destination']:
        if query != base_query:
            query += ", "
        query += "destination = ?"
        parameters.append(new_flight_info['destination'])

    if new_flight_info['date']:
        if query != base_query:
            query += ", "
        query += "date = ?"
        parameters.append(new_flight_info['date'])

    if new_flight_info['seats_available']:
        if query != base_query:
            query += ", "
        query += "seats_available = ?"
        parameters.append(new_flight_info['seats_available'])

    if new_flight_info['ticket_price']:
        if query != base_query:
            query += ", "
        query += "ticket_price = ?"
        parameters.append(new_flight_info['ticket_price'])

    if new_flight_info['status']:
        if query != base_query:
            query += ", "
        query += "status = ?"
        parameters.append(new_flight_info['status'])

    query += " WHERE flight_id = ?"
    parameters.append(new_flight_info['flight_id'])

    # Execute the query
    cursor.execute(query, parameters)
    conn.commit()
    conn.close()

    flight_info = get_flight_with_id(new_flight_info['flight_id'])

    return flight_info

# Handles login logic
def login_attempt(email, password):
    # Connect to the SQLite database
    conn = sqlite3.connect('airline_reservation.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM users 
        WHERE email = ? and password = ?
        ''', (email, password))

    # Fetch flight in question
    user = cursor.fetchone()

    # Close the cursor and connection
    cursor.close()
    conn.close()

    if user:
        # Format the flight details into a dictionary
        login_info = {
            'user_id': user[0],
            'first_name': user[1],
            'employee_status': user[5]
        }
        return login_info

    return

# Generate and send cancellation emails
def cancel_notification(flight_id):
    # Connect to SQLite database
    conn = sqlite3.connect('airline_reservation.db')
    cursor = conn.cursor()
    query = """
           SELECT 
                r.reservation_id,
                r.flight_id,
                r.last_notification_received,
                u.first_name,
                u.last_name,
                u.email,
                f.status
            FROM reservations r
            JOIN users u ON r.email = u.email
            JOIN flights f ON r.flight_id = f.flight_id
            WHERE r.flight_id = ?
        """

    try:
        # Get all reservations, user info, and flight status for the specified flight
        cursor.execute(query, (flight_id,))
        # make list of tuples
        affected_reservations = cursor.fetchall()
        # unpack tuples

        for reservation in affected_reservations:
            (reservation_id, flight_id, last_notification_received,
             first_name, last_name, email, status) = reservation
            print(f"flight_status: {status}")
            # HTML email template with integrated CSS
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    .email-container {{
                        font-family: Arial, sans-serif;
                        max-width: 600px;
                        margin: 0 auto;
                        background-color: white;
                    }}
                    .header {{
                        background-color: #4CAF50;
                        color: white;
                        padding: 20px;
                        text-align: center;
                    }}
                    .content {{
                        padding: 20px;
                        line-height: 1.6;
                    }}
                    .info-box {{
                        background-color: #f9f9f9;
                        border-left: 4px solid #4CAF50;
                        padding: 15px;
                        margin: 10px 0;
                    }}
                    .footer {{
                        background-color: #4CAF50;
                        color: white;
                        padding: 10px;
                        text-align: center;
                        font-size: 12px;
                    }}
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="header">
                        <h2>Flight Status Update</h2>
                    </div>
                    <div class="content">
                        <p>Hello, {first_name} {last_name},</p>
                        <p>Your flight status has changed.</p>

                        <div class="info-box">
                            <p><strong>Reservation ID:</strong> {reservation_id}</p>
                            <p><strong>Flight ID:</strong> {flight_id}</p>
                            <p><strong>Status:</strong> {status}</p>
                            <p><strong>Date:</strong> {last_notification_received}</p>
                        </div>
                    </div>
                    <div class="footer">
                        <p>If you have any questions, please contact our support team.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            try:
                # Prepare and send email
                msg = Message(
                    subject=f'Flight Status Update: {status}',
                    sender=os.getenv('MAIL_USERNAME'),
                    recipients=[email]
                )
                msg.html = html_content
                with app.app_context():
                    mail.send(msg)

            except Exception as e:
                print(f"Error sending notification for reservation id: {reservation_id}: {str(e)}")

    except Exception as e:
        print(f"Database error: {str(e)}")

    finally:
        cursor.close()
        conn.close()

# Route for the homepage
@dbinit.app.route('/')
def index():
    return render_template('index.html')

# Route for searching flight details
@dbinit.app.route('/search_flights', methods=['GET', 'POST'])
def search_flights():
    if request.method == 'POST':
        flight_id = request.form.get('flight_id')
        origin = request.form.get('origin')
        destination = request.form.get('destination')
        date = request.form.get('date')
        seats_available = request.form.get('seats_available')

        # Call search_details to get the flights based on the parameters provided
        flights = search_details(flight_id, origin, destination, date, seats_available)

        if flights:
            # Render the HTML template with the fetched flights
            return render_template('search_flights.html', flights=flights)
        else:
            return render_template('search_flights.html', searchError=True)

    # If not a POST request, simply render the page with an empty list of flights
    return render_template('search_flights.html')

# payment page for bookings
@dbinit.app.route('/payment/<int:flight_id>', methods=['GET', 'POST'])
def book_flight(flight_id):
    if request.method == 'POST':

        # Call search_details to get the flights based on the parameters provided
        flight_info = get_flight_with_id(flight_id)

        if current_user.is_authenticated:
            if flight_info:
                return render_template('payment.html', flight=flight_info, first_name=current_user.first_name, last_name=current_user.last_name, email=current_user.email)
            else:
                return render_template('payment.html')
        else:
            if flight_info:
                # Render the HTML template with the fetched flights
                return render_template('payment.html', flight=flight_info)
            else:
                return render_template('payment.html')

    flight_info = get_flight_with_id(flight_id)

    if current_user.is_authenticated:
        if flight_info:
            return render_template('payment.html', flight=flight_info, first_name=current_user.first_name, last_name=current_user.last_name, email=current_user.email)
        else:
            return render_template('payment.html')
    else:
        if flight_info:
            return render_template('payment.html', flight=flight_info)
        else:
            return render_template('payment.html')

# payment page for agents helping customers,
@dbinit.app.route('/teller/<int:flight_id>', methods=['GET', 'POST'])
def book_flight_for_customer(flight_id):
    if request.method == 'POST':

        # Call search_details to get the flights based on the parameters provided
        flight_info = get_flight_with_id(flight_id)

        # checks if user is logged in and sends stats as need
        if current_user.is_authenticated:
            if flight_info:
                return render_template('payment.html', flight=flight_info, teller=True)
            else:
                return render_template('payment.html')
        else:
            if flight_info:
                # Render the HTML template with the fetched flights
                return render_template('payment.html', flight=flight_info, teller=False)
            else:
                return render_template('payment.html')

    flight_info = get_flight_with_id(flight_id)

    if current_user.is_authenticated:
        if flight_info:
            return render_template('payment.html', flight=flight_info, teller=True)
        else:
            return render_template('payment.html')
    else:
        if flight_info:
            return render_template('payment.html', flight=flight_info, teller=False)
        else:
            return render_template('payment.html')

@dbinit.app.route('/flight_information', methods=['GET','POST'])
def flight_information():
    if request.method == 'POST':
        flight_id = request.form.get('flight_id')    # Connect to the SQLite database
        flight_info = get_flight_with_id(flight_id)

        # checks if user is logged in and sends stats as need
        if current_user.is_authenticated:
            if flight_info:
                return render_template('flight_information.html', flight=flight_info, employee=current_user.employee_status)
            else:
                # If not a POST request, simply render the page with an empty list of flights
                return render_template('flight_information.html', searchError=True)
        else:
            if flight_info:
                return render_template('flight_information.html', flight=flight_info, employee=False)
            else:
                # If not a POST request, simply render the page with an empty list of flights
                return render_template('flight_information.html', searchError=True)

    else:
        # If not a POST request, simply render the page with an empty list of flights
        return render_template('flight_information.html')

# Route to check flight status by flight ID
@dbinit.app.route('/flight_information/<int:flight_id>', methods=['GET'])
def flight_status(flight_id):
    flight_info = get_flight_with_id(flight_id)

    #checks if user is logged in and sends stats as need
    if current_user.is_authenticated:
        if flight_info:
            return render_template('flight_information.html', flight=flight_info, employee=current_user.employee_status)
        else:
            # If not a POST request, simply render the page with an empty list of flights
            return render_template('flight_information.html', searchError=True)

    else:
        if flight_info:
            return render_template('flight_information.html', flight=flight_info, employee=False)
        else:
            # If not a POST request, simply render the page with an empty list of flights
            return render_template('flight_information.html', searchError=True)

# Employee only page
@dbinit.app.route('/create_flight', methods=['GET','POST'])
def create_flight():
    if request.method == 'POST':
        new_flight_info = {
            'origin': request.form.get('add_origin'),
            'destination': request.form.get('add_destination'),
            'date': request.form.get('add_date'),
            'seats_available': request.form.get('add_seats_available'),
            'ticket_price': request.form.get('add_ticket_price'),
            'status': 'Scheduled'
        }
        # get flight id to pass it to flight status page
        flight_id = create_new_flight(new_flight_info)
        # redirecting to flight status page
        return redirect(url_for('flight_status', flight_id=flight_id))

    return render_template('create_flight.html', name=current_user.first_name, employee=current_user.employee_status)

# search user database for any user with the empolyee tag and id specified
@dbinit.app.route('/search_employee', methods=['GET','POST'])
def search_employee():
    if request.method == 'POST':
        user_id = request.form.get('employee_id')
        user_info = check_employee_stats(user_id)
        return render_template('search_employee.html', user=user_info, name=current_user.first_name, employee=current_user.employee_status)

    return render_template('search_employee.html', name=current_user.first_name, employee=current_user.employee_status)

# Page to modify currenly exsiting flights in database
@dbinit.app.route('/mod_flight', methods=['GET','POST'])
def mod_flight():
    if request.method == 'POST':
        new_flight_info = {
            'flight_id': request.form.get('flight_id'),
            'origin': request.form.get('mod_origin'),
            'destination': request.form.get('mod_destination'),
            'date': request.form.get('mod_date'),
            'seats_available': request.form.get('mod_seats_available'),
            'ticket_price': request.form.get('mod_ticket_price'),
            'status': request.form.get('mod_flight_status')
        }
        #update flight information
        update_flight(new_flight_info)

        # get flight id to pass it to flight status page
        flight_id = request.form.get('flight_id')

        if request.form.get('mod_flight_status') == 'Canceled':
            try:
                cancel_notification(flight_id)
            except Exception as e:
                print(f"Error in cancel_notification: {str(e)}")

        return redirect(url_for('flight_status', flight_id=flight_id))

    return render_template('mod_flights.html', name=current_user.first_name, employee=current_user.employee_status)

# Route for the login page
@dbinit.app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')

        # check to see if user is in database
        conn = sqlite3.connect('airline_reservation.db')
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))

        # attempt to fetch email from database to check if they have already signed up
        is_in_database = cursor.fetchone()

        # Close the cursor and connection
        cursor.close()
        conn.close()

        if is_in_database:
            return render_template('register.html', failed=True)

        else:
            create_user(email, password, first_name, last_name)
            login_info = login_attempt(email, password)
            user = dbinit.load_user_by_id(login_info['user_id'])
            login_user(user)
            return render_template('register.html', success=True)
    # Intial page load
    return render_template('register.html')

# Route for the login page
@dbinit.app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        login_info = login_attempt(email, password)

        if login_info:
            # Render the HTML template with the fetched flights
            user = dbinit.load_user_by_id(login_info['user_id'])
            login_user(user)
            return render_template('login.html', success=True)
        else:
            return render_template('login.html', failed=True, not_logged_in=True)
    return render_template('login.html', not_logged_in=True)

#page to logout users, can only be accessed if logged in
@dbinit.app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Route for the account page
@dbinit.app.route('/account', methods=['GET','POST'])
def account():
    # check if user is logged in
    if current_user.is_authenticated:
        flight_details = get_flights_by_user_email(current_user.email)

        return render_template('account.html', name=current_user.first_name, employee=current_user.employee_status, flights=flight_details)

    return render_template('account.html')