from enums.piece_color import PieceColor
from abc import ABC, abstractmethod
from _move import Move
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from chess_board import ChessBoard


class Piece(ABC):
    """Base class for all chess pieces."""

    def __init__(self, color: PieceColor, pos: tuple[int, int]):
        self.color = color
        self.pos = pos
        self.has_moved = False

    @abstractmethod
    def get_move(self, end: tuple[int, int], board: "ChessBoard") -> Optional[Move]:
        """Returns a `Move` object containing the move's information.
        Returns `None` if there is no valid move.

        Args:
            end (tuple[int, int]): The position to move to.
            board (ChessBoard): The chessboard this piece belongs to.

        Returns:
            Move: The object holding information about the move.
        """
        pass


class SlidingPiece(Piece, ABC):
    """Base class for sliding pieces (Rook, Bishop, Queen)."""

    @abstractmethod
    def _get_directions_list(self) -> set[tuple[int, int]]:
        """Subclasses must implement this.
        Gives a list of directions the piece can move to
        separate each subclass from each other."""
        pass

    def get_move(self, end, board):
        sr, sc = self.pos
        er, ec = end
        row_diff = er - sr
        col_diff = ec - sc

        # Determine movement direction
        row_step = 1 if row_diff > 0 else -1 if row_diff < 0 else 0
        col_step = 1 if col_diff > 0 else -1 if col_diff < 0 else 0

        # Separate Rook, Bishop, and Queen
        if (row_step, col_step) not in self._get_directions_list():
            return None  # Invalid movement direction

        if not board.is_path_clear(self.pos, end):
            return None  # Path is not clear between piece's pos and `end`

        return Move(self.pos, end)


class Pawn(Piece):
    def __init__(self, color, pos):
        super().__init__(color, pos)
        self.direction = 1 if self.color == PieceColor.BLACK else -1

    def get_move(self, end, board):
        sr, sc = self.pos
        er, ec = end
        promotion = False
        col_diff = ec - sc

        # Move forward two spaces on first turn
        if not self.has_moved:
            if col_diff == 0 and er == sr + (2 * self.direction):
                if board.is_path_clear(self.pos, end, include_end=True):
                    return Move(self.pos, end, moved_two=True)

        # From this point on, must only move one square forward
        if er != sr + self.direction:
            return None

        # Check pawn promotion
        if (self.color == PieceColor.WHITE and er == 0) or (
            self.color == PieceColor.BLACK and er == 7
        ):
            promotion = True

        other_piece = board.get_piece(end)

        # Moves diagonally to capture
        if abs(col_diff) == 1:
            if other_piece:  # Pawn capturing piece
                return Move(self.pos, end, promote_pawn=promotion)
            elif self._en_passant_check(end, board):  # En Passant
                return Move(self.pos, end, promote_pawn=promotion, en_passant=True)

        # Moves forward one space
        if col_diff == 0 and not other_piece:
            return Move(self.pos, end, promote_pawn=promotion)

        return None

    def _en_passant_check(self, end: tuple[int, int], board: "ChessBoard") -> bool:
        """Returns if the current En Passant target pawn is behind one space
        where this pawn will move to.

        Args:
            end (tuple[int, int]): The position this pawn will move to.
            board (ChessBoard): The chessboard this piece belongs to.

        Returns:
            bool: True if En Passant target is in correct position to be captured.
        """
        en_passant_target = board.get_piece((self.pos[0], end[1]))
        return board.en_passant_target and en_passant_target == board.en_passant_target


class Rook(SlidingPiece):
    def _get_directions_list(self):
        return {(1, 0), (-1, 0), (0, 1), (0, -1)}


class Bishop(SlidingPiece):
    def _get_directions_list(self):
        return {(1, 1), (-1, -1), (1, -1), (-1, 1)}


class Knight(Piece):
    def get_move(self, end, board):
        sr, sc = self.pos
        er, ec = end
        row_diff = er - sr
        col_diff = ec - sc

        allowed_moves_abs = {(1, 2), (2, 1)}

        # L-shape move. 2 in one direction, 1 in the other.
        if (abs(row_diff), abs(col_diff)) in allowed_moves_abs:
            return Move(self.pos, end)

        return None


class Queen(SlidingPiece):
    def _get_directions_list(self):
        return {  # Queen is a combination of Rook and Bishop
            (1, 0),  # Rook moves
            (-1, 0),
            (0, 1),
            (0, -1),
            (1, 1),  # Bishop moves
            (-1, -1),
            (1, -1),
            (-1, 1),
        }


class King(Piece):
    def get_move(self, end, board):
        sr, sc = self.pos
        er, ec = end
        row_diff = er - sr
        col_diff = ec - sc

        enemy_color = (
            PieceColor.WHITE if self.color == PieceColor.BLACK else PieceColor.BLACK
        )
        allowed_moves_abs = {(0, 1), (1, 0), (1, 1)}

        # Castling
        if row_diff == 0 and abs(col_diff) == 2 and not self.has_moved:
            if board.is_under_attack(self.pos, enemy_color):
                return None  # King is currently under attack

            # Grab the corner rook
            rook_col = 0 if col_diff < 0 else 7
            corner_rook = board.get_piece((sr, rook_col))

            if not corner_rook or corner_rook.has_moved:
                return None  # Corner rook does not exist at position or a piece exists that has moved

            if not board.is_path_clear(self.pos, corner_rook.pos):
                return None  # Path between King and corner rook is obstructed by another piece

            # Ensure the 2 spaces the King travels are not under attack
            col_dir = 1 if col_diff > 0 else -1
            if board.is_under_attack(end, enemy_color) or board.is_under_attack(
                (sr, sc + col_dir)
            ):
                return None

            return Move(self.pos, end, castling=True)

        # Single space move
        if (abs(row_diff), abs(col_diff)) in allowed_moves_abs:
            if not board.is_under_attack(end, enemy_color):
                return Move(self.pos, end)

        return None
