from app import socketio

@socketio.on('connect')
def handle_connect():
    """
    Loguje informacje, gdy nowy klient (przeglądarka)
    pomyślnie połączy się przez WebSocket.
    """
    print("[SocketIO] Nowy klient połączony.")

@socketio.on('disconnect')
def handle_disconnect():
    """
    Loguje informacje, gdy klient się rozłączy.
    """
    print("[SocketIO] Klient rozłączony.")