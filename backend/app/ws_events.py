from app import socketio

@socketio.on('connect')
def handle_connect():
    """
    Logs info when new connection was established with websocket.
    """
    print("[SocketIO] New client connected!.")

@socketio.on('disconnect')
def handle_disconnect():
    """
    Logs info when client disconnected
    """
    print("[SocketIO] Client disconnected!.")