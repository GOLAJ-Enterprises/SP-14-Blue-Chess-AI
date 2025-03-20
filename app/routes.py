from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from chess import ChessEngine

main = Blueprint("main", __name__)
engine = ChessEngine()


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/get/board", methods=["GET"])
def get_board():
    board = engine.serialize_board()
    return jsonify({"board": board})


@main.route("/get/stats", methods=["GET"])
def get_stats():
    stats = engine.stats
    active_color = stats["active_color"]
    castling_availability = stats["castling_availability"]
    en_passant_target = stats["en_passant_target"]
    halfmove_clock = stats["halfmove_clock"]
    fullmove_num = stats["fullmove_num"]

    return jsonify(
        {
            "color": active_color,
            "castling_rights": castling_availability,
            "en_passant": en_passant_target,
            "halfmove": halfmove_clock,
            "fullmove": fullmove_num,
        }
    )


@main.route("/load_fen", methods=["POST"])
def load_fen():
    fen_string = request.form.get("fen")
    if not fen_string:
        flash("Field is empty. Input a valid FEN string.", "error")
        return redirect(url_for("main.index"))

    success = engine.set_board_state(fen_string)

    if not success:
        flash("Invalid FEN string. Please try again.", "error")
        return redirect(url_for("main.index"))

    flash("FEN loaded successfully!", "success")
    return redirect(url_for("main.index"))


@main.route("/move", methods=["POST"])
def move_piece():
    data = request.get_json()
    from_square = data.get("from")
    to_square = data.get("to")
    success = engine.move_piece(from_square, to_square)

    return jsonify({"success": success})


@main.route("/reset", methods=["POST"])
def reset_board():
    success = engine.reset()
    return jsonify({"success": success})
