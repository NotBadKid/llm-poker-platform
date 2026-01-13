from app import socketio


def broadcast_game_state(state_json: dict,game_id):
    """
    Sends game state to all connected clients (in our case the frontend) through websockets.

    Function called after every game state update
    """

    # frontend should listen for this event name
    event_name = "game_update/"+game_id

    print(f"[Broadcaster] Broadcasting the event: '{event_name}'...")

    # socketio.emit() z broadcast=True wysyła wiadomość do wszystkich podłączonych klientów w domyślnej przestrzeni nazw.
    socketio.emit(event_name, state_json)