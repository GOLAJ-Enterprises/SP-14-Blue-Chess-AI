from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
import chess

main = Blueprint("main", __name__)
chess_board = chess.Board()


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/get/board", methods=["GET"])
def get_board():
    board = chess_board.serialize()
    return jsonify({"board": board})


@main.route("/get/stats", methods=["GET"])
def get_stats():
    pass


@main.route("/load_fen", methods=["POST"])
def load_fen():
    pass


@main.route("/move", methods=["POST"])
def move_piece():
    pass


@main.route("/promote", methods=["POST"])
def promote_pawn():
    pass


@main.route("/reset", methods=["POST"])
def reset_board():
    pass
