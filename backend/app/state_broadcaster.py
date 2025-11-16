from app import socketio


def broadcast_game_state(state_json: dict):
    """
    Wysyła aktualny stan gry (JSON) do wszystkich podłączonych
    klientów (frontendów) przez WebSocket.

    Tę funkcję wywoła game_engine po każdej zmianie stanu.
    """

    # Używamy zdefiniowanej nazwy zdarzenia, na którą frontend będzie nasłuchiwał
    event_name = "game_update"

    print(f"[Broadcaster] Rozgłaszanie eventu '{event_name}'...")

    # socketio.emit() z broadcast=True wysyła wiadomość do wszystkich podłączonych klientów w domyślnej przestrzeni nazw.
    socketio.emit(event_name, state_json, broadcast=True)