from abc import ABC, abstractmethod
from enums import PieceColor
from utils import validate_positions, is_valid_pos
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from board import Board


class Piece(ABC):
    """Base class for all chess pieces."""

    def __init__(self, color: PieceColor, pos: tuple[int, int]):
        self.color = color
        self.pos = pos
        self.has_moved = False  # If the pice has moved from its starting position

    @validate_positions(1)
    def can_move_to(self, end: tuple[int, int], board: "Board") -> bool:
        """Checks if the destination is valid and then calls `_specific_move_check`.

        Args:
            end (tuple[int, int]): The position to move to.
            board (Board): The chessboard this piece belongs to.

        Returns:
            bool: True if checks are passed and `_specific_move_check` returns True
        """
        if self.pos == end:  # Ensure piece is actually moving
            return False

        piece_at_end = board.get_piece(end)
        if piece_at_end and piece_at_end.color == self.color:  # Can't capture own piece
            return False

        return self._specific_move_check(end, board)

    @abstractmethod
    def _specific_move_check(self, end: tuple[int, int], board: "Board") -> bool:
        """
        Returns whether this piece can move from its current position to `end`.

        Args:
            end (tuple[int, int]): The position to move to.
            board (Board): The board the piece belongs to.

        Returns:
            bool: True if `end` is a valid position to move to.
        """
        pass

    @property
    def pos(self) -> tuple[int, int]:
        """Getter for pos."""
        return self._pos

    @pos.setter
    def pos(self, new_pos: tuple[int, int]):
        """
        Setter with validation for position.

        Args:
            new_pos (tuple[int, int]): New position of the piece on the board.
        """
        if not is_valid_pos(new_pos):
            raise ValueError(
                f"Invalid position: {new_pos}. Must be a (row, col) tuple within (0-7, 0-7)."
            )
        self._pos = new_pos


class SlidingPiece(Piece, ABC):
    """
    Base class for sliding pieces (Rook, Bishop, Queen).
    Handles movement along straight lines.
    """

    @abstractmethod
    def _get_move_directions(self) -> set[tuple[int, int]]:
        """Subclasses must define their allowed move directions.

        Returns:
            set[tuple[int, int]]: A set containing all directions a piece can move.
        """
        pass

    def _specific_move_check(self, end, board):
        row_diff, col_diff = (end[0] - self.pos[0], end[1] - self.pos[1])

        # Determine movement direction
        row_step = 1 if row_diff > 0 else -1 if row_diff < 0 else 0
        col_step = 1 if col_diff > 0 else -1 if col_diff < 0 else 0

        if (row_step, col_step) not in self._get_move_directions():
            return False  # Invalid movement direction

        return board.is_path_clear(self.pos, end)  # Final path check


class Pawn(Piece):
    def __init__(self, color, pos):
        super().__init__(color, pos)
        self.direction = 1 if color == PieceColor.BLACK else -1

    def _specific_move_check(self, end, board):
        start_row, start_col = self.pos
        end_row, end_col = end

        piece_at_end = board.get_piece(end)

        # Move forward two squares (Only on first move)
        if not self.has_moved:
            if end_col == start_col and start_row + (2 * self.direction) == end_row:
                if (
                    piece_at_end is None
                    and board.get_piece((start_row + self.direction, start_col)) is None
                ):
                    return True

        # Make sure pawn moved one square forward
        one_forward = start_row + self.direction == end_row

        if one_forward:
            # Move forward one square
            if end_col == start_col and piece_at_end is None:
                return True

            if abs(end_col - start_col) == 1:
                # Capture Diagonally
                if piece_at_end:
                    return True

                # En passant
                en_passant_target = board.get_piece((start_row, end_col))
                if en_passant_target == board.en_passant_target:
                    return True

        return False


class Rook(SlidingPiece):
    def _get_move_directions(self):
        return {(1, 0), (-1, 0), (0, 1), (0, -1)}


class Bishop(SlidingPiece):
    def _get_move_directions(self):
        return {(1, 1), (-1, -1), (1, -1), (-1, 1)}


class Knight(Piece):
    def _specific_move_check(self, end, board):
        start_row, start_col = self.pos
        end_row, end_col = end

        row_diff = end_row - start_row
        col_diff = end_col - start_col

        allowed_moves_abs = {(1, 2), (2, 1)}

        # L-shape move. 2 in one direction, 1 in the other.
        if (abs(row_diff), abs(col_diff)) in allowed_moves_abs:
            return True

        return False


class Queen(SlidingPiece):
    def _get_move_directions(self):
        return {
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
    def _specific_move_check(self, end, board):
        start_row, start_col = self.pos
        end_row, end_col = end

        row_diff = end_row - start_row
        col_diff = end_col - start_col

        allowed_moves_abs = {(0, 1), (1, 0), (1, 1)}

        enemy_color = (
            PieceColor.BLACK if self.color == PieceColor.WHITE else PieceColor.WHITE
        )

        # One square any direction
        if (abs(row_diff), abs(col_diff)) in allowed_moves_abs:
            # Ensure square is not under attack by other team
            if not board.is_under_attack(end, enemy_color):
                return True

        # Castling with Rook
        if row_diff == 0 and abs(col_diff) == 2 and not self.has_moved:
            # Ensure King isn't currently in check. Castling not allowed if King is in check.
            if board.is_under_attack(self.pos, enemy_color):
                return False

            direction, rook_col = (1, 7) if col_diff > 0 else (-1, 0)
            corner_rook = board.get_piece((start_row, rook_col))

            # Ensure corner Rook exists and has not moved
            if not corner_rook or corner_rook.has_moved:
                return False

            # Ensure path between King and Rook is clear and no squares in King's path are under attack
            if board.is_path_clear(self.pos, corner_rook.pos):
                # Grab position one over from King towards end position
                one_over_pos = (start_row, start_col + direction)

                # Ensure the two spaces the king is moving are not under attack
                if not (
                    board.is_under_attack(one_over_pos, enemy_color)
                    or board.is_under_attack(end, enemy_color)
                ):
                    return True

        return False
