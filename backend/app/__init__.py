from flask import Flask
from flask_socketio import SocketIO

socketio = SocketIO(cors_allowed_origins="*")

def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.Config")

    from .socket import register_socket_handlers
    register_socket_handlers(socketio)

    return app
