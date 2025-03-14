from collections import defaultdict
import re

from .board import Board
from ._color import Color


class ChessEngine:
    def __init__(self):
        self.board = Board()
        self.active_color = Color(self.board.active_color)
        self.state_counts = defaultdict(int, {self.board.fen: 1})
        self.states_list = [self.board.fen]
        self.states_list_idx = 0

    def move_piece(self, start: tuple[int, int], end: tuple[int, int]) -> bool:
        success = self.board.move_piece(start, end)
        return success

        # if success:
        #    while self.states_list_idx < len(self.states_list) - 1:
        #        self.state_counts[self.states_list[-1]] -= 1
        #        del self.states_list[-1]

    #
    #    self.state_counts[self.board.fen] += 1
    #    self.states_list.append(self.board.fen)
    #    self.states_list_idx += 1
    #    self.active_color = Color(self.board.active_color)

    def set_board_state(self, fen: str) -> bool:
        parts = fen.strip().split()

        if len(parts) != 6:
            return False

        (
            piece_placement,
            active_color,
            castling,
            en_passant,
            halfmove_clock,
            fullmove_number,
        ) = parts

        # Validate piece placement
        ranks = piece_placement.split("/")
        if len(ranks) != 8:
            return False

        for rank in ranks:
            count = 0
            for char in rank:
                if char.isdigit():
                    count += int(char)
                elif char in "prnbqkPRNBQK":
                    count += 1
                else:
                    return False
            if count != 8:
                return False

        # Validate active color
        if active_color not in {"w", "b"}:
            return False

        # Validate castling availability
        if castling != "-" and not re.fullmatch(r"[KQkq]+", castling):
            return False

        # Validate en passant target square
        if en_passant != "-" and not re.fullmatch(r"^[a-h][36]$", en_passant):
            return False

        # Validate halfmove clock
        if not halfmove_clock.isdigit():
            return False

        # Validate fullmove number
        if not fullmove_number.isdigit() or int(fullmove_number) < 1:
            return False

        # Set fen string as board state
        self.board.fen = fen
        self.board.parse_fen()

        return True

    def undo(self):
        pass

    def redo(self):
        pass
