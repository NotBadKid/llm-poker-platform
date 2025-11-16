from flask_socketio import emit
from app.poker.game_manager import game_manager

def register_socket_handlers(socketio):

    @socketio.on("connect")
    def handle_connect():
        print("Client connected")
        emit("state_update", game_manager.export_state())

    @socketio.on("disconnect")
    def handle_disconnect():
        print("Client disconnected")

    @socketio.on("player_action")
    def handle_player_action(data):
        """
        data = {
            "player_id": "...",
            "action": "bet",
            "amount": 200
        }
        """
        game_manager.handle_action(data["player_id"], data)
        socketio.emit("state_update", game_manager.export_state())

    @socketio.on("llm_message")
    def handle_llm_message(data):
        """
        data = {
            "player_id": "...",
            "message": "some text"
        }
        """
        socketio.emit("chat_message", data)
