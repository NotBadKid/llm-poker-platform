from flask import request, jsonify, Blueprint
import threading
import app.database as db


from .database import db, HandResult, get_aggregated_stats,  save_hand_result

main_bp = Blueprint('main', __name__)

try:
    from app.poker import poker_engine
except ImportError as e:
    print("="*50)
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

    log_player_strategies(game_config.get('players', []))

    if not game_config or 'players' not in game_config:
        return jsonify({"error": "Missing player config ('players')"}), 400

    if not poker_engine:
        return jsonify({"error": "poker_engine not available."}), 500

    print(f"[Routes] Received start game request with players: {game_config.get('players')}")

    game_thread = threading.Thread(
        target=poker_engine.start_game_session,
        args=(game_config,)
    )
    game_thread.start()

    return jsonify({"status": "Game session started"}), 202

@main_bp.route('/stats', methods=['GET'])
def get_stats():
    """
    HTTP GET Endpoint for retrieving aggregated game statistics.
    """
    stats = db.get_aggregated_stats()
    return jsonify(stats), 200

@main_bp.route('/api/hand/record', methods=['POST'])
def record_hand_result():
    """Records a SINGLE hand result for ONE player."""
    data = request.get_json()

    try:
        save_hand_result(data)
        return jsonify({"status": "success"}), 201

    except KeyError as e:
        return jsonify({"error": f"Missing required field: {e}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/hand/read_all', methods=['GET'])
def read_all_hands():
    """Fetches all hand results efficiently."""
    try:
        # 1. Fetch data
        results = db.session.execute(db.select(HandResult)).scalars().all()

        # 2. Serialize to JSON (List comprehension is faster and cleaner)
        data = [{
            "id": r.id,
            "game_id": r.game_id,
            "hand": r.hand_number,
            "player": r.player_name,
            "model": r.model_id,
            "net_change": r.net_change,
            "winner": r.is_winner,
            "timestamp": r.timestamp.isoformat()
        } for r in results]

        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def log_player_strategies(players_list: list):
    """
    Helper function to print player strategies to the console.
    """
    print(f"\n[Routes] Received start game request.")
    print("=" * 40)
    print("PLAYER STRATEGY CHECK:")

    if not players_list:
        print("No players found in config.")
        return

    for i, p in enumerate(players_list):
        name = p.get('name', f"Player {i + 1}")
        model = p.get('model_id', "Unknown Model")
        strategy = p.get('user_prompt')

        print(f"User {i + 1}: [{name}] ({model})")
        if strategy:
            preview = (strategy[:75] + '...') if len(strategy) > 75 else strategy
            print(f"   └── Strategy: \"{preview}\"")
        else:
            print(f"   └── Strategy: [NONE] -> Will use Default (Optimal/GTO)")

    print("=" * 40 + "\n")