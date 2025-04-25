from flask import Blueprint, render_template, request, jsonify
from app import state
from bitboarder import Move, WHITE

main = Blueprint("main", __name__)


@main.route("/")
def index():
    state.active_mode = None
    return render_template("index.html")


@main.route("/play")
def play():
    color = request.args.get("color")
    mode = request.args.get("mode")

    if mode == "pvp":
        state.active_mode = "pvp"
    elif mode == "ai":
        state.active_mode = f"ai_{color}" if color else "ai_menu"
    else:
        state.active_mode = None

    return render_template(
        "play.html",
        mode=mode if mode else "unknown",
        color=color,
        chr=chr,
    )


@main.route("/get/turn")
def get_turn():
    if state.active_mode in state.game_states:
        board = state.game_states[state.active_mode].board
    else:
        return jsonify({"error": "Invalid game mode"})

    turn = "w" if board.active_color == WHITE else "b"
    return jsonify({"turn": turn})


@main.route("/get/board")
def get_board():
    if state.active_mode in state.game_states:
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


@main.route("/get/stats")
def get_stats():
    game = state.game_states.get(state.active_mode)
    if not game:
        return jsonify({"error": "Invalid game mode"}), 400

    board = game.board
    ac, cr, eps, hc, fc = board.get_fen_stats()

    try:
        fullmove_count = int(fc)
        halfmove_clock = int(hc)
    except ValueError:
        return jsonify({"error": "Invalid FEN values"}), 500

    ply = (fullmove_count - 1) * 2 + (1 if ac == "b" else 0)

    checkmate = board.is_checkmate()
    draw = board.is_draw()

    winner = "b" if board.active_color == WHITE else "w" if checkmate or draw else None

    return jsonify(
        {
            "active_color": ac,
            "castling": cr,
            "en_passant": eps,
            "halfmove_clock": halfmove_clock,
            "fullmove_count": fullmove_count,
            "ply": ply,
            "in_check": board.is_in_check(),
            "checkmate": board.is_checkmate(),
            "draw": board.is_draw(),
            "winner": winner,
        }
    )


@main.route("/reset", methods=["POST"])
def reset_board():
    if state.active_mode not in state.game_states:
        return jsonify({"error": "Invalid game mode"}), 400

    game = state.game_states[state.active_mode]
    game.board.reset()
    return jsonify({"success": True})


@main.route("/undo", methods=["POST"])
def undo_move():
    if state.active_mode not in state.game_states:
        return jsonify({"error": "Invalid game mode"}), 400

    game = state.game_states[state.active_mode]
    success = game.board.undo()
    return jsonify({"success": success})


@main.route("/can_move/<from_uci>/<to_uci>")
def can_move(from_uci, to_uci):
    if state.active_mode not in state.game_states:
        return jsonify({"can_move": False})

    board = state.game_states[state.active_mode].board
    return jsonify({"can_move": board.can_move_to(from_uci, to_uci)})
