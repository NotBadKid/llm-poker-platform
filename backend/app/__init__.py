from flask_socketio import SocketIO

from flask import Flask
from config import config_by_name


socketio = SocketIO(cors_allowed_origins="*")
def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    socketio.init_app(app)
    from . import events
    return app