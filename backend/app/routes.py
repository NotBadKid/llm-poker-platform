from flask import request, jsonify, Blueprint
import threading

main_bp = Blueprint('main', __name__)

try:
    import poker_engine
except ImportError:
    print("="*50)
    print("WARNING: Could not import 'poker_engine'.")
    print("Serwer will work, without possibility to run game.")
    print("="*50)
    poker_engine = None #TODO


@main_bp.route('/game/start', methods=['POST'])
def start_game():
    """
    HTTP POST Endpoint for starting the game.
    Gets the configuration and starts the game in a seperate thread.
    """
    game_config = request.get_json()

    if not game_config or 'players' not in game_config:
        return jsonify({"error": "Missing player config ('players')"}), 400

    if not poker_engine:
        return jsonify({"error": "poker_engine not available."}), 500

    print(f"[Routes] Received start game request with players: {game_config.get('players')}")

    game_thread = threading.Thread(
        target=poker_engine.start_game_session, #TODO: metoda start_game_session
        args=(game_config,)
    )
    game_thread.start()

    return jsonify({"status": "Game session started"}), 202