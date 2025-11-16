from flask import Flask
from flask_cors import CORS
from .routes import routes_bp
from .socket import socketio

def create_app():
    app = Flask(__name__)
    CORS(app)

    # rejestracja routingu
    app.register_blueprint(routes_bp)

    # websockety
    socketio.init_app(app, cors_allowed_origins="*")

    return app
