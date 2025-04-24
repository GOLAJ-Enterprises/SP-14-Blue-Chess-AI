from flask import Blueprint, render_template, request, jsonify
from app.decorators import requires_mode, local_only, requires_lan_player
from app import state
from bitboarder import Move, WHITE
import uuid
import socket


main = Blueprint("main", __name__)


@main.route("/")
def index():
    state.active_mode = None
    return render_template("index.html")


@main.route("/play")
def play():
    color = request.args.get("color")
    create = request.args.get("create")
    game = request.args.get("game")

    if request.args.get("pvp") == "true":
        state.active_mode = "pvp"
    elif request.args.get("ai") == "true":
        state.active_mode = f"ai_{color}" if color else "ai"
    elif request.args.get("lan") == "true":
        state.active_mode = "lan"
    else:
        state.active_mode = None

    return render_template(
        "play.html",
        mode=state.active_mode if state.active_mode else "unknown",
        color=color,
        create=create,
        game=game,
        chr=chr,
    )


@main.route("/get/turn")
def get_turn():
    if state.active_mode == "lan":
        if not state.active_lan_game:
            return jsonify({"error": "No active LAN game"})
        board = state.active_lan_game.board
    elif state.active_mode in state.game_states:
        board = state.game_states[state.active_mode].board
    else:
        return jsonify({"error": "Invalid game mode"})

    turn = "w" if board.active_color == WHITE else "b"
    return jsonify({"turn": turn})


@main.route("/get/board")
def get_board():
    if state.active_mode == "lan":
        if not state.active_lan_game:
            return jsonify({"error": "No active LAN game"})
        board = state.active_lan_game.board
    elif state.active_mode in state.game_states:
        board = state.game_states[state.active_mode].board
    else:
        return jsonify({"error": "Invalid game mode"})

    return jsonify({"board": board.serialize()})


@main.route("/move/local_player", methods=["POST"])
def move_local_player():
    board = state.game_states["pvp"].board
    uci = request.get_data(as_text=True).strip()

    move = Move.from_uci(uci)
    success = board.push(move)

    return jsonify({"success": success})


@main.route("/move/ai_player", methods=["POST"])
def move_ai_player():
    game = state.game_states[state.active_mode]

    uci = request.get_data(as_text=True).strip()
    move = Move.from_uci(uci)
    success = game.board.push(move)

    return jsonify({"success": success})


@main.route("/move/ai_bot")
def move_ai_bot():
    game = state.game_states[state.active_mode]

    uci_pred = game.ai.predict(use_mcts=True, visits=10)
    move = Move.from_uci(uci_pred)
    success = game.board.push(move)

    return jsonify({"success": success, "uci": uci_pred})


@main.route("/move/lan_player", methods=["POST"])
def move_lan_player():
    if not state.active_lan_game:
        return jsonify({"error": "No active LAN game"}), 400

    uci = request.get_data(as_text=True).strip()
    board = state.active_lan_game.board

    move = Move.from_uci(uci)
    success = board.push(move)
    return jsonify({"success": success})


@main.route("/lan/create", methods=["POST"])
def create_lan_game():
    game_id = str(uuid.uuid4())[:8]
    color = request.json.get("color")
    ip = request.remote_addr

    game = state.LANGame(game_id)

    if color == "w":
        game.white_ip = ip
        game.white_token = str(uuid.uuid4())
    else:
        game.black_ip = ip
        game.black_token = str(uuid.uuid4())

    # Overwrite existing LAN game
    state.active_lan_game = game

    # Get local IP to broadcast
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    # Start broadcasting this new game
    state.broadcast_game(game_id, local_ip)

    return jsonify(
        {
            "game_id": game_id,
            "color": color,
            "token": game.white_token if color == "w" else game.black_token,
        }
    )


@main.route("/lan/discovered", methods=["GET"])
def get_discovered_lan_games():
    local_ip = socket.gethostbyname(socket.gethostname())

    games = []
    for game in state.discovered_lan_games.values():
        is_local = game["ip"] == local_ip
        games.append({**game, "local": is_local})

    return jsonify({"games": games})


@main.route("/lan/join/<game_id>", methods=["POST"])
def join_lan_game(game_id):
    ip = request.remote_addr
    game = state.active_lan_game

    if not game or game.game_id != game_id:
        return jsonify({"error": "Game not found"}), 404

    # Check if this IP already joined
    if ip in game.joined_clients:
        return jsonify(game.joined_clients[ip])

    if not game.white_ip:
        game.white_ip = ip
        token = str(uuid.uuid4())
        game.white_token = token
        game.joined_clients[ip] = {"color": "w", "token": token}
    elif not game.black_ip:
        game.black_ip = ip
        token = str(uuid.uuid4())
        game.black_token = token
        game.joined_clients[ip] = {"color": "b", "token": token}
    else:
        return jsonify({"error": "Game full"}), 403

    return jsonify(game.joined_clients[ip])
