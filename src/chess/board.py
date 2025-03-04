from enums import PieceColor
from utils import validate_positions
from typing import Optional
from pieces import Piece, Pawn, Rook, Bishop, Knight, Queen, King
import copy


class Board:
    def __init__(self):
        self.board_arr = [[None for _ in range(8)] for _ in range(8)]
        self.piece_list: dict[PieceColor, set[Piece]] = {
            PieceColor.WHITE: set(),
            PieceColor.BLACK: set(),
        }
        self.en_passant_target = None
        self._initialize_board()

    def _initialize_board(self):
        """Places pieces in their respective starting positions on the board."""
        piece_order = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]

        # Place black pieces
        for col, piece in enumerate(piece_order):
            # Place black pieces
            self.add_piece(piece, PieceColor.BLACK, (0, col))
            self.add_piece(Pawn, PieceColor.BLACK, (1, col))
            # Place white pieces
            self.add_piece(Pawn, PieceColor.WHITE, (6, col))
            self.add_piece(piece, PieceColor.WHITE, (7, col))

        # Keep track of board states to be able to undo turns
        self.board_states: list[
            tuple[list[list[Optional[Piece]]], dict[PieceColor, set[Piece]]]
        ] = [(copy.deepcopy(self.board_arr), copy.deepcopy(self.piece_list))]
        self.board_states_idx = 0

    @validate_positions(3)
    def add_piece(
        self,
        piece_obj: type[Piece],
        color: PieceColor,
        pos: tuple[int, int],
    ) -> bool:
        """Adds a piece at a position on the chessboard.

        Args:
            piece_obj (type[Piece]): The callable type of the chess piece (Pawn, Rook, ...).
            color (PieceColor): The color of the piece.
            pos (tuple[int, int]): The position of the piece.

        Returns:
            bool: True if piece was successfully added.
        """
        if not issubclass(piece_obj, Piece):
            return False

        row, col = pos[0], pos[1]

        if self.board_arr[row][col]:
            return False

        piece = piece_obj(color, pos)

        self.board_arr[row][col] = piece
        self.piece_list[piece.color].add(piece)
        return True

    @validate_positions(1)
    def remove_piece(self, pos: tuple[int, int]) -> bool:
        """Removes a piece at a position on the chessboard.

        Returns:
            bool: True if piece was successfully removed.
        """
        piece = self.get_piece(pos)
        if piece is None:
            return False

        if piece not in self.piece_list[piece.color]:
            print(
                f"Warning: Removing piece {piece} at {pos} but it was not found in piece_list."
            )
        else:
            self.piece_list[piece.color].remove(piece)

        row, col = pos
        self.board_arr[row][col] = None
        return True

    @validate_positions(2)
    def move_piece(self, piece: Piece, new_pos: tuple[int, int]) -> bool:
        """Moves a piece to a new location on the chessboard.

        Args:
            piece (Piece): The piece to move.
            new_pos (tuple[int, int]): The new position of the piece.

        Returns:
            bool: If the piece was successfully moved.
        """
        # Verify piece is a Piece
        if not isinstance(piece, Piece):
            return False

        # Verify piece can move to new position
        if not piece.can_move_to(new_pos, self):
            return False

        # Verify King won't be in check after the move
        if not self._is_king_safe_after_move(piece.pos, new_pos):
            return False

        # Attacking another piece
        target = self.get_piece(new_pos)
        if target:
            self.piece_list[target.color].remove(target)

        old_row, old_col = piece.pos
        new_row, new_col = new_pos

        if isinstance(piece, Pawn):
            # En Passant Check
            # Check if pawn moved diagonally into an empty square
            if (
                self.en_passant_target
                and target is None
                and abs(new_col - old_col) == 1
            ):
                en_passant_target = self.get_piece((old_row, new_col))

                if en_passant_target == self.en_passant_target:
                    self.board_arr[old_row][new_col] = None  # Remove En Passant pawn
                    self.piece_list[en_passant_target.color].remove(en_passant_target)

            # Enable pawn to be captured via En Passant if moved 2 spaces on first turn
            if not piece.has_moved and abs(new_row - old_row) == 2:
                self.en_passant_target = piece
            else:
                self.en_passant_target = None

            # Check if pawn needs promotion
            if (piece.color == PieceColor.BLACK and new_pos[0] == 7) or (
                piece.color == PieceColor.WHITE and new_pos[0] == 0
            ):
                self.piece_list[piece.color].remove(piece)
                piece = Queen(piece.color, new_pos)  # TODO Give player the choice.
                self.piece_list[piece.color].add(piece)
        else:
            self.en_passant_target = None

        # Castling Check
        col_diff = new_col - old_col
        if isinstance(piece, King) and abs(col_diff) == 2:
            rook_col, new_rook_col = (7, 5) if col_diff > 0 else (0, 3)
            corner_rook = self.get_piece((old_row, rook_col))

            # Move corner rook to the other side of the King
            self.board_arr[old_row][rook_col] = None
            self.board_arr[old_row][new_rook_col] = corner_rook
            corner_rook.pos = (old_row, new_rook_col)
            corner_rook.has_moved = True

        # Move the piece
        self.board_arr[old_row][old_col] = None
        self.board_arr[new_row][new_col] = piece
        piece.pos = new_pos
        piece.has_moved = True

        # Delete all saved board states after current index
        if self.board_states_idx < len(self.board_states) - 1:
            del self.board_states[self.board_states_idx + 1 :]

        # Update board states list
        self.board_states.append(
            (copy.deepcopy(self.board_arr), copy.deepcopy(self.piece_list))
        )
        self.board_states_idx += 1

        return True

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
        except (IndexError, ValueError):  # Catches out of bounds error
            return None

    def undo_turns(self, num_turns: int) -> bool:
        """Undoes `num_turns` amount of turns.

        Args:
            num_turns (int): The amount of turns to go back.

        Returns:
            bool: True if turns successfully undone.
        """
        # Make sure to only undo until one turn left
        if self.board_states_idx == 0:
            return False

        # Ensure `num_turns` has enough turns to undo
        if num_turns < 1 or num_turns > self.board_states_idx:
            return False

        self.board_states_idx -= num_turns
        self.board_arr, self.piece_list = self.board_states[self.board_states_idx]

        return True

    def redo_turns(self, num_turns: int) -> bool:
        """Redoes `num_turns` amount of turns if turns have been undone using `undo_turns`.

        Args:
            num_turns (int): The amount of turns to redo

        Returns:
            bool: True if turns successfully redone.
        """
        # Make sure to only redo until last turn in list
        if self.board_states_idx == len(self.board_states) - 1:
            return False

        # Make sure `num_turns` is between 1 and the distance between `self.board_states_idx` and len(self.board_states) - 1
        if num_turns < 1 or num_turns > (
            len(self.board_states) - 1 - self.board_states_idx
        ):
            return False

        self.board_states_idx += num_turns
        self.board_arr, self.piece_list = self.board_states[self.board_states_idx]

        return True

    @validate_positions(1, 2)
    def is_path_clear(
        self,
        start: tuple[int, int],
        end: tuple[int, int],
    ) -> bool:
        """Checks if the path between start and end is clear of obstacles.
        The end must be orthogonal or diagonal to the start.

        Args:
            start (tuple[int, int]): The start position.
            end (tuple[int, int]): The end position.

        Returns:
            bool: True if path between start and end is clear.
        """
        row_diff, col_diff = end[0] - start[0], end[1] - start[1]

        # Ensure movement is either orthogonal or diagonal
        if start[0] != end[0] and start[1] != end[1] and abs(row_diff) != abs(col_diff):
            return False

        # Determine movement direction
        row_step = 1 if row_diff > 0 else -1 if row_diff < 0 else 0
        col_step = 1 if col_diff > 0 else -1 if col_diff < 0 else 0

        # Start checking from first step to end
        row, col = start[0] + row_step, start[1] + col_step
        while (row, col) != end:
            potential_piece = self.get_piece((row, col))
            if potential_piece:
                return False  # Obstacle detected

            # Move one step further
            row += row_step
            col += col_step

        return True  # Path is clear

    @validate_positions(1)
    def is_under_attack(
        self,
        pos: tuple[int, int],
        color: PieceColor,
    ) -> bool:
        """Returns True if the specified position on the chessboard is under attack by specified color pieces.

        Args:
            pos (tuple[int, int]): The position to check.
            color (PieceColor): The attacking team's color.

        Returns:
            bool: True if position is under attack by specified color pieces.
        """
        for piece in self.piece_list[color]:
            if piece.can_move_to(pos, self):
                return True  # Position is under attack

        return False  # Position not under attack

    @validate_positions(1, 2)
    def _is_king_safe_after_move(
        self,
        start: tuple[int, int],
        end: tuple[int, int],
    ) -> bool:
        """Returns whether the King is in check after a move has been made.
        Used to verify if a move leaves the player's King in check or not.

        Args:
            board_state (tuple[list[list[Optional[Piece]]], dict[PieceColor, set[Piece]]]): The tuple of the current board state
            start (tuple[int, int]): The position of the piece being moved.
            end (tuple[int, int]): The position the piece is being moved to.

        Returns:
            bool: True if the king is safe from check after a move is made.
        """
        # Copy self to simulate next move
        board_copy = copy.deepcopy(self)

        start_row, start_col = start
        end_row, end_col = end

        start_piece = board_copy.board_arr[start_row][start_col]
        end_piece = board_copy.board_arr[end_row][end_col]

        if not start_piece:  # Ensure piece exists at start
            return False

        if end_piece:  # If `end_piece` exists delete it from `piece_list`
            board_copy.piece_list[end_piece.color].remove(end_piece)

        board_copy.board_arr[start_row][start_col] = None
        board_copy.board_arr[end_row][end_col] = start_piece
        start_piece.pos = end

        # Ensure King is not in check after move is made
        for piece in board_copy.piece_list[start_piece.color]:
            if isinstance(piece, King):
                enemy_color = (
                    PieceColor.BLACK
                    if piece.color == PieceColor.WHITE
                    else PieceColor.WHITE
                )

                # Check if King is under attack
                if board_copy.is_under_attack(piece.pos, enemy_color):
                    return False

                break

        return True
