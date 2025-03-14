from __future__ import annotations
from typing import TYPE_CHECKING

from .pieces import Pawn, Rook, Bishop, Knight, Queen, King
from ._color import Color
from ._utils import algebraic_to_coord, coord_to_algebraic, is_valid_coord
from ._eval import Evaluator

if TYPE_CHECKING:
    from .pieces import Piece
    from ._move import Move


class Board:
    def __init__(self):
        self.fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        self.board_arr = []
        self.active_color = ""
        self.castling_availability = ""
        self.en_passant_target = ""
        self.halfmove_clock = 0
        self.fullmove_num = 1

        self.kings = {Color.WHITE: None, Color.BLACK: None}

        self.parse_fen()

    def get_piece_at(self, pos: tuple[int, int]) -> Piece | None:
        if not is_valid_coord(pos):
            return None
        row, col = pos
        return self.board_arr[row][col]

    def move_piece(self, start: tuple[int, int], end: tuple[int, int]) -> bool:
        # Validation coordinates and existence of the piece
        if not is_valid_coord(start) or not is_valid_coord(end):
            print(1)
            return False

        piece = self.get_piece_at(start)
        if piece is None or piece.color.value != self.active_color:
            print(2)
            return False  # Piece does not exist or not that color's turn

        # Ensure piece can move from `start` to `end`
        move: Move = piece.find_move(self, end)
        if move is None:
            print(3)
            return False

        # Make sure king is not in check after the move
        if Evaluator.move_causes_own_check(self, move):
            print(4)
            return False

        # Update the halfmove clock
        self._update_halfmove_clock(piece, end)

        # Increment fullmove number if black moved
        if self.active_color == "b":
            self.fullmove_num += 1

        if move.en_passant:
            self._handle_en_passant(piece)

        if move.moved_two:
            self._set_en_passant_target(piece)
        else:
            self.en_passant_target = "-"

        if move.promote_pawn:
            piece = self._handle_promotion(piece, end)

        if move.castling:
            self._handle_castling(piece, start, end)

        # Handle castling availability
        if isinstance(piece, (Rook, King)):
            self._handle_castling_availability(piece)

        # Move piece
        self._apply_move(piece, start, end)

        # Post move updates
        self._post_move_updates(piece)

        return True

    def parse_fen(self) -> None:
        parts = self.fen.split()

        # Update board state
        self._set_board_from_fen(parts[0])
        self.active_color = parts[1]
        self.castling_availability = parts[2]
        self.en_passant_target = parts[3]
        self.halfmove_clock = int(parts[4])
        self.fullmove_num = int(parts[5])

    def _update_fen(self) -> None:
        # Generate the board part of the FEN string
        fen_rows = []
        for row in self.board_arr:
            empty_squares = 0
            fen_row = ""
            for square in row:
                if square is None:
                    empty_squares += 1
                else:
                    if empty_squares > 0:
                        fen_row += str(empty_squares)
                        empty_squares = 0
                    fen_row += str(square)
            if empty_squares > 0:
                fen_row += str(empty_squares)
            fen_rows.append(fen_row)
        board_fen = "/".join(fen_rows)

        # Combine all parts to form the FEN string and update FEN string
        self.fen = f"{board_fen} {self.active_color} {self.castling_availability} {self.en_passant_target} {self.halfmove_clock} {self.fullmove_num}"

    def _set_board_from_fen(self, board_str: str) -> None:
        piece_map = {
            "p": Pawn,
            "r": Rook,
            "b": Bishop,
            "n": Knight,
            "q": Queen,
            "k": King,
        }

        rows = board_str.split("/")
        board_arr = []
        for i, row in enumerate(rows):
            board_row = []
            j = 0
            for char in row:
                if char.isdigit():
                    empty_squares = int(char)
                    j += empty_squares
                    board_row.extend([None] * empty_squares)
                else:
                    piece_type = piece_map[char.lower()]
                    color = Color.WHITE if char.isupper() else Color.BLACK
                    pos = (i, j)
                    piece = piece_type(color, pos)

                    if isinstance(piece, King):
                        self.kings[piece.color] = piece

                    board_row.append(piece)
                    j += 1
            board_arr.append(board_row)

        self.board_arr = board_arr

    def _update_halfmove_clock(self, piece: Piece, end: tuple[int, int]) -> None:
        piece_at_end = self.get_piece_at(end)
        if isinstance(piece, Pawn) or piece_at_end is not None:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

    def _handle_en_passant(self, pawn: Pawn) -> None:
        assert self.en_passant_target != "-"
        _, tc = algebraic_to_coord(self.en_passant_target)
        self.board_arr[pawn.pos[0]][tc] = None

    def _set_en_passant_target(self, pawn: Pawn) -> None:
        assert not pawn.has_moved
        middle_row = pawn.pos[0] + pawn.direction
        target_coord = (middle_row, pawn.pos[1])
        self.en_passant_target = coord_to_algebraic(target_coord)

    def _handle_promotion(self, pawn: Pawn, end: tuple[int, int]) -> Piece:
        er, _ = end
        assert (pawn.color is Color.BLACK and er == 7) or (
            pawn.color is Color.WHITE and er == 0
        )
        # TODO Get user choice; defaulting to Queen for now
        return Queen(pawn.color, pawn.pos)

    def _handle_castling(
        self, piece: King, start: tuple[int, int], end: tuple[int, int]
    ) -> None:
        sr, sc = start
        _, ec = end

        assert not piece.has_moved and self.castling_availability != "-"

        rook_col, new_rook_col = (0, 3) if ec < sc else (7, 5)
        corner_rook = self.get_piece_at((sr, rook_col))
        assert isinstance(corner_rook, Rook) and not corner_rook.has_moved

        self.board_arr[sr][rook_col] = None
        self.board_arr[sr][new_rook_col] = corner_rook
        corner_rook.pos = (sr, new_rook_col)
        corner_rook.has_moved = True

    def _handle_castling_availability(self, piece: Rook | King) -> None:
        k, q = ("K", "Q") if piece.color is Color.WHITE else ("k", "q")

        if isinstance(piece, Rook) and not piece.has_moved:
            _, rook_col = piece.pos
            self.castling_availability = (
                self.castling_availability.replace(k if rook_col == 7 else q, "") or "-"
            )
        elif isinstance(piece, King):
            self.castling_availability = (
                self.castling_availability.replace(k, "").replace(q, "") or "-"
            )

    def _apply_move(
        self, piece: Piece, start: tuple[int, int], end: tuple[int, int]
    ) -> None:
        sr, sc = start
        er, ec = end
        self.board_arr[sr][sc] = None
        self.board_arr[er][ec] = piece
        piece.pos = end
        piece.has_moved = True

    def _post_move_updates(self, piece: Piece) -> None:
        self.active_color = "w" if piece.color is Color.BLACK else "b"
        self._update_fen()
