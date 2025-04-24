from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
import bitboarder
from app.ai import ChessCNN

main = Blueprint("main", __name__)

chess_board = bitboarder.Board()
ai = ChessCNN(chess_board, "cpu")


@main.route("/")
def index():
    return render_template("index.html", chr=chr)
