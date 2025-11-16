from flask import Blueprint, jsonify, request
from .poker.game_manager import game_manager

routes_bp = Blueprint("routes", __name__)


@routes_bp.route("/state", methods=["GET"])
def get_state():
    return jsonify(game_manager.export_state())


@routes_bp.route("/action", methods=["POST"])
def post_action():
    data = request.json
    player_id = data.get("player_id")
    action = data.get("action")

    game_manager.handle_action(player_id, action)
    return jsonify({"status": "ok"})
