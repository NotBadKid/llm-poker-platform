from flask import Flask
from flask_socketio import SocketIO
import config

socketio = SocketIO(async_mode='threading', cors_allowed_origins="*")


def create_app():
    """Creates and configures the Flask app."""

    app = Flask(__name__)
    app.config["SECRET_KEY"] = "bardzo_tajny_klucz_do_zmiany!"  # required by SocketIO

    socketio.init_app(app)

    from .routes import main_bp

    app.register_blueprint(main_bp)

    from . import ws_events

    return app