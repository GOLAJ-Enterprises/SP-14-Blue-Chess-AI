from collections import defaultdict

from board import Board
from _color import Color


class ChessEngine:
    def __init__(self):
        self.board = Board()
        self.active_color = Color(self.board.active_color)
        self.state_counts = defaultdict(int, {self.board.fen: 1})
        self.states_list = [self.board.fen]
        self.states_list_idx = 0

    def move_piece(self, start: tuple[int, int], end: tuple[int, int]) -> bool:
        success = self.board.move_piece(start, end)

        if success:
            while self.states_list_idx < len(self.states_list) - 1:
                self.state_counts[self.states_list[-1]] -= 1
                del self.states_list[-1]

            self.state_counts[self.board.fen] += 1
            self.states_list.append(self.board.fen)
            self.states_list_idx += 1
            self.active_color = Color(self.board.active_color)

    def undo(self):
        pass

    def redo(self):
        pass
