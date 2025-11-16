from flask import request, jsonify, Blueprint
import threading

main_bp = Blueprint('main', __name__)

try:
    import poker_engine
except ImportError:
    print("="*50)
    print("OSTRZEŻENIE: Nie można zaimportować 'poker_engine'.")
    print("Serwer będzie działał, ale nie będzie można uruchomić gry.")
    print("="*50)
    poker_engine = None #TODO


@main_bp.route('/game/start', methods=['POST'])
def start_game():
    """
    Endpoint HTTP POST do rozpoczynania nowej gry.
    Przyjmuje konfigurację gry i uruchamia game_engine w osobnym wątku.
    """
    game_config = request.get_json()

    if not game_config or 'players' not in game_config:
        return jsonify({"error": "Brak konfiguracji graczy ('players')"}), 400

    if not poker_engine:
        return jsonify({"error": "Silnik gry (poker_engine) nie jest dostępny."}), 500

    print(f"[Routes] Otrzymano żądanie startu gry z graczami: {game_config.get('players')}")

    game_thread = threading.Thread(
        target=poker_engine.start_game_session, #TODO: metoda start_game_session
        args=(game_config,)
    )
    game_thread.start()

    return jsonify({"status": "Game session started"}), 202