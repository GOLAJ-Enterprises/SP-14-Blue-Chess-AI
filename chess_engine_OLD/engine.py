from collections import defaultdict
import re

from ._board import Board
from ._utils import algebraic_to_coord


class ChessEngine:
    def __init__(self):
        self.board = Board()
        self.state_counts = defaultdict(int, {self.board.fen: 1})
        self.states_list = [self.board.fen]
        self.states_list_idx = 0
        self.stats = {
            "active_color": self.board.active_color,
            "castling_availability": self.board.castling_availability,
            "en_passant_target": self.board.en_passant_target,
            "halfmove_clock": self.board.halfmove_clock,
            "fullmove_num": self.board.fullmove_num,
        }

    def move_piece(self, start: str, end: str) -> bool:
        if len(start) != 2 or len(end) not in {2, 3}:
            return False

        promotion_piece = end[-1] if len(end) == 3 else ""
        start_pos = algebraic_to_coord(start)
        end_pos = algebraic_to_coord(end if len(end) == 2 else end[0:2])

        status = self.board.move_piece(start_pos, end_pos, promotion_piece)
        success = status["success"]

        if success:
            self._update_stats()
            # while self.states_list_idx < len(self.states_list) - 1:
            #    self.state_counts[self.states_list[-1]] -= 1
            #    del self.states_list[-1]

            # self.state_counts[self.board.fen] += 1
            # self.states_list.append(self.board.fen)
            # self.states_list_idx += 1
            # self.active_color = Color(self.board.active_color)

        return status

    def promote_pawn(self, piece_type: str) -> bool:
        return self.board.promote_pawn(piece_type)

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
        self._update_stats()

        return True

    def undo(self):
        pass

    def redo(self):
        pass

    def reset(self):
        return self.set_board_state(
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        )

    def serialize_board(self):
        return [
            [
                str(self.board.get_piece_at((row, col)))
                if self.board.get_piece_at((row, col)) is not None
                else ""
                for col in range(8)
            ]
            for row in range(8)
        ]

    def _update_stats(self) -> None:
        self.stats["active_color"] = self.board.active_color
        self.stats["castling_availability"] = self.board.castling_availability
        self.stats["en_passant_target"] = self.board.en_passant_target
        self.stats["halfmove_clock"] = self.board.halfmove_clock
        self.stats["fullmove_num"] = self.board.fullmove_num
