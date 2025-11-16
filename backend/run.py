# /run.py
import os
from app import create_app, socketio

config_name = os.environ.get('FLASK_CONFIG') or 'default'
app = create_app(config_name)

if __name__ == '__main__':
    print("Starting Flask-SocketIO server with eventlet...")
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)