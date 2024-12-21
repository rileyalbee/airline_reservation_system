from dotenv import load_dotenv

import dbinit
import flights
import payments

# Load environment variables from .env file
load_dotenv()

# Main block
if __name__ == '__main__':
    dbinit.init_db()  # Initialize the database on startup if not already created
    flights.add_flights() # Add flights to the database
    payments.process_payment #process payments
    dbinit.app.run(debug=True)
