from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
import chess

main = Blueprint("main", __name__)
chess_board = chess.Board()


@main.route("/")
def index():
    return render_template("index.html", chr=chr)


@main.route("/get/board", methods=["GET"])
def get_board():
    board = chess_board.serialize()
    return jsonify({"board": board})


@main.route("/get/stats", methods=["GET"])
def get_stats():
    stats = chess_board.get_fen_stats()
    return jsonify(
        {
            "color": stats[0],
            "castling_rights": stats[1],
            "en_passant": stats[2],
            "halfmove": stats[3],
            "fullmove": stats[4],
        }
    )


@main.route("/get/state", methods=["GET"])
def get_state():
    state = chess_board.get_board_state()
    return jsonify({"state": state})


@main.route("/load_fen", methods=["POST"])
def load_fen():
    fen_str = request.form.get("fen")
    if not fen_str:
        flash("Please enter a FEN string.", "error")
    else:
        success = chess_board.set_from_fen(fen_str)
        if success:
            flash("Successfully set chessboard from FEN!", "success")
        else:
            flash("Failed to set chessboard from FEN.", "error")

    return redirect(url_for("main.index"))


@main.route("/move", methods=["POST"])
def move():
    uci = request.get_data(as_text=True)
    move = chess.Move.from_uci(uci)

    success = chess_board.push(move)
    return jsonify({"success": success})


@main.route("/reset", methods=["POST"])
def reset():
    chess_board.reset()
    return "", 204


@main.route("/undo", methods=["POST"])
def undo():
    chess_board.undo()
    return "", 204
