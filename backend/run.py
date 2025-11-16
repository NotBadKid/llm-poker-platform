from app import create_app, socketio
from dotenv import load_dotenv

# Load env variables from .env file
load_dotenv()

app = create_app()

if __name__ == '__main__':
    print("Uruchamianie serwera LLM Poker (Flask + SocketIO)...")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)