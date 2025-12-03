from app import create_app, socketio
# We must import 'db' to create tables.
# Assuming db is defined in app/database.py or app/extensions.py
from app.database import db
from dotenv import load_dotenv
import os

# Load env variables from .env file
load_dotenv()

# Create the Flask application instance
app = create_app()

if __name__ == '__main__':
    # ---------------------------------------------------------
    # DATABASE INITIALIZATION
    # ---------------------------------------------------------
    # We must push the application context to interact with the DB
    # because 'db' is bound to the app instance created above.
    with app.app_context():
        print("Checking and creating database tables...")
        try:
            db.create_all()
            print("Database tables are ready.")
        except Exception as e:
            print(f"Error creating tables: {e}")

    # ---------------------------------------------------------
    # RUN SERVER
    # ---------------------------------------------------------
    print("Running server LLM Poker (Flask + SocketIO)...")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)