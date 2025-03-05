from enums.game_state import GameState
from enums.piece_color import PieceColor
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chess_board import ChessBoard


class ChessGame:
    def __init__(self):
        self.board = ChessBoard()
        self.game_state = GameState.ACTIVE
        self.turn = PieceColor.WHITE

    def switch_turn(self):
        if self.turn == PieceColor.WHITE:
            self.turn = PieceColor.BLACK
        else:
            self.turn = PieceColor.WHITE

    def move_piece(self, start: tuple[int, int], end: tuple[int, int]) -> bool:
        """Calls the board to move a piece after validating `start` and `end`
        are valid board positions.

        Args:
            start (tuple[int, int]): The position of the piece to move.
            end (tuple[int, int]): The position to move the piece to.

        Returns:
            bool: True if piece is successfully moved.
        """
        if start == end:
            return False  # Piece must move

        if not self._validate_positions(start, end):
            return (
                False  # `start` and/or `end` are not valid board positions (0-7, 0-7)
            )

        start_piece = self.board.get_piece(start)
        end_piece = self.board.get_piece(end)

        if not start_piece:
            return False  # Piece does not exist at start position
        if end_piece and end_piece.color == start_piece.color:
            return False  # The pieces are the same color

        return self.board.move_piece(start_piece, end)

    def _validate_positions(*positions: tuple[int, int]) -> bool:
        """Returns whether every position given as an argument are valid chessboard positions.

        Returns:
            bool: True if every position is a valid position.
        """
        for pos in positions:
            if not (
                isinstance(pos, tuple)
                and len(pos) == 2
                and all(isinstance(i, int) and 0 <= i < 8 for i in pos)
            ):
                return False
        return True
