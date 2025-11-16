from flask import request, jsonify, Blueprint
import threading

main_bp = Blueprint('main', __name__)

try:
    from app.poker import poker_engine
except ImportError as e: # Dobrą praktyką jest złapanie wyjątku jako 'e'
    print("="*50)
    # Teraz możemy nawet wydrukować prawdziwy błąd, jeśli nadal występuje
    print(f"WARNING: Could not import 'app.poker.poker_engine'. Error: {e}")
    print("Server will run, but starting a game will fail.")
    print("="*50)
    poker_engine = None


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