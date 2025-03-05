from enums.piece_color import PieceColor
from pieces import Piece, Pawn, Rook, Bishop, Knight, Queen, King
from typing import Optional, TYPE_CHECKING
import copy

if TYPE_CHECKING:
    from _move import Move


class ChessBoard:
    def __init__(self):
        self.board_arr = [[None for _ in range(8)] for _ in range(8)]
        self.piece_list: dict[PieceColor, set[Piece]] = {
            PieceColor.WHITE: set(),
            PieceColor.BLACK: set(),
        }
        self.en_passant_target = None  # Keep track of which Pawn is under En Passant
        self._initialize_board()

    def _initialize_board(self):
        """Places pieces in their respective starting positions on the board."""
        piece_order = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]

        for col, piece in enumerate(piece_order):
            # Place black pieces
            self.add_piece(piece, PieceColor.BLACK, (0, col))
            self.add_piece(Pawn, PieceColor.BLACK, (1, col))
            # Place white pieces
            self.add_piece(Pawn, PieceColor.WHITE, (6, col))
            self.add_piece(piece, PieceColor.WHITE, (7, col))

    def get_piece(self, pos: tuple[int, int]) -> Optional[Piece]:
        """Returns the piece at a given position.
        May return None if no piece is present.

        Args:
            pos (tuple[int, int]): The position of the piece to get.

        Returns:
            Optional[Piece]: May return a Piece or None
        """
        try:
            row, col = pos
            return self.board_arr[row][col]
        except (IndexError, ValueError):
            return None

    def add_piece(
        self, piece_obj: type[Piece], color: PieceColor, pos: tuple[int, int]
    ) -> Optional[Piece]:
        """Adds a piece at a position on the chessboard.

        Args:
            piece_obj (type[Piece]): The callable type of the chess piece (Pawn, Rook, ...).
            color (PieceColor): The color of the piece.
            pos (tuple[int, int]): The position of the piece.

        Returns:
            Optional[Piece]: The piece that was added if operation successful.
        """
        row, col = pos[0], pos[1]

        piece = piece_obj(color, pos)

        if self.get_piece(pos):
            return None  # A piece is already at position

        self.board_arr[row][col] = piece
        self.piece_list[color].add(piece)
        return piece  # Piece successfully added

    def remove_piece(self, pos: tuple[int, int]) -> Optional[Piece]:
        """Removes a piece at a position on the chessboard.

        Args:
            pos (tuple[int, int]): The position of the piece on the board.

        Returns:
            Optional[Piece]: The piece that was removed if operation successful.
        """
        piece = self.get_piece(pos)

        if not piece:
            return None  # Piece does not exist at position

        row, col = pos
        self.board_arr[row][col] = None
        self.piece_list[piece.color].remove(piece)
        return piece  # Piece successfully removed

    def move_piece(self, piece: Piece, end: tuple[int, int]) -> bool:
        """Moves a piece on the chessboard.

        Args:
            start (tuple[int, int]): The position of the piece to move.
            end (tuple[int, int]): The position to move the piece to.

        Returns:
            bool: True if piece was successfully moved.
        """
        move: "Move" = piece.get_move(end)

        if not move:
            return False  # Make sure move didn't return `None`

        # Make sure King is not in check after move is completed
        if not isinstance(piece, King):  # King manages itself
            if self._causes_king_check(move):
                return False

        # En Passant check
        if move.en_passant:
            assert self.en_passant_target and isinstance(piece, Pawn)
            self.remove_piece(self.en_passant_target.pos)

        # Pawn moved 2 spaces
        if move.moved_two:
            assert isinstance(piece, Pawn) and not piece.has_moved
            self.en_passant_target = piece
        else:
            self.en_passant_target = None

        # Pawn Promotion check
        if move.promote_pawn:
            assert isinstance(piece, Pawn)

            color = piece.color
            pos = piece.pos

            # Swap Pawn to user's choice of Queen, Rook, Bishop, or Knight
            self.remove_piece(piece.pos)
            piece = self.add_piece(Queen, color, pos)  # TODO Let user choose

        sr, sc = move.start
        er, ec = move.end

        # King Castling check
        if move.castling:
            assert isinstance(piece, King) and not piece.has_moved

            col_diff = ec - sc
            rook_col, new_rook_col = (0, 3) if col_diff < 0 else (7, 5)

            corner_rook = self.get_piece((sr, rook_col))
            assert isinstance(corner_rook, Rook) and not corner_rook.has_moved

            self.board_arr[sr][rook_col] = None
            self.board_arr[sr][new_rook_col] = corner_rook
            corner_rook.pos = (sr, new_rook_col)
            corner_rook.has_moved = True

        possible_piece = self.get_piece(move.end)

        if possible_piece:  # Remove enemy piece getting captured
            self.remove_piece(possible_piece.pos)

        # Move piece
        self.board_arr[sr][sc] = None
        self.board_arr[er][ec] = piece
        piece.pos = move.end
        piece.has_moved = True

        return True

    def is_path_clear(
        self, start: tuple[int, int], end: tuple[int, int], include_end: bool = False
    ) -> bool:
        """Returns if the path between start (exclusive) and end (inclusive or exclusive) is clear of pieces.
        `start` and `end` must be orthogonal or diagonal to each other.

        Args:
            start (tuple[int, int]): The starting position on the chessboard.
            end (tuple[int, int]): The end position on the chessboard.
            include_end (bool, optional): Whether or not to check the end position too. Defaults to False.

        Returns:
            bool: True if path is clear of pieces.
        """
        sr, sc = start
        er, ec = end

        row_diff = er - sr
        col_diff = ec - sc

        # Ensure `end` is orthogonal or diagonal to `start`
        if sr != er and sc != ec and abs(row_diff) != abs(col_diff):
            return False

        # Determine movement direction
        row_step = 1 if row_diff > 0 else -1 if row_diff < 0 else 0
        col_step = 1 if col_diff > 0 else -1 if col_diff < 0 else 0

        # Check from first step to end
        current = (sr + row_step, sc + col_step)
        if include_end:
            end = (er + row_step, ec + col_step)

        while current != end:
            possible_piece = self.get_piece(current)

            if possible_piece:
                return False

            current = (current[0] + row_step, current[1] + col_step)

        return True

    def is_under_attack(self, pos: tuple[int, int], enemy_color: PieceColor) -> bool:
        """Returns if the position `pos` is under attack by team `enemy_color`.

        Args:
            pos (tuple[int, int]): The position to check.
            enemy_color (PieceColor): The enemy piece color.

        Returns:
            bool: True if position is under attack by enemy team `enemy_color`.
        """
        for enemy in self.piece_list[enemy_color]:
            if isinstance(enemy, King):
                # To avoid infinite recursion, check if `pos` is adjacent to enemy king
                er, ec = enemy.pos
                pr, pc = pos

                if max(abs(er - pr), abs(ec - pc)) == 1:
                    return True
            elif enemy.get_move(pos, self):  # If enemy can move to `pos`
                return True

        return False

    def _causes_king_check(self, move: "Move") -> bool:
        """Returns if the given `move` will leave the team's King in check.

        Args:
            move (Move): The move to perform.

        Returns:
            bool: If the King is in check after the move.
        """
        # Make a deep copy of the class object
        board_copy = copy.deepcopy(self)

        # Move piece from `move.start` to `move.end`
        start_piece = board_copy.get_piece(move.start)
        end_piece = board_copy.get_piece(move.end)

        assert start_piece

        sr, sc = move.start
        er, ec = move.end

        if end_piece:  # Remove enemy piece being captured
            board_copy.remove_piece(end_piece.pos)

        board_copy.board_arr[sr][sc] = None
        board_copy.board_arr[er][ec] = start_piece

        # Locate friendly King and check if it's under attack
        for piece in board_copy.piece_list[start_piece.color]:
            if isinstance(piece, King):
                enemy_color = (
                    PieceColor.WHITE
                    if piece.color == PieceColor.BLACK
                    else PieceColor.BLACK
                )

                if board_copy.is_under_attack(piece.pos, enemy_color):
                    return True

                break

        return False
