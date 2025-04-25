from __future__ import annotations
from bitboarder import Board
from app.ai import ChessCNN


active_mode = None


class PvPGame:
    def __init__(self):
        self.board = Board()


class AIGame:
    def __init__(self):
        self.board = Board()
        self.ai = ChessCNN(self.board, "cpu")


game_states = {
    "pvp": PvPGame(),
    "ai_w": AIGame(),
    "ai_b": AIGame(),
}
