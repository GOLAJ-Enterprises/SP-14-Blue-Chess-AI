from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from _move import Move
from _eval import Evaluator
from _utils import coord_to_algebraic, is_valid_coord

if TYPE_CHECKING:
    from _color import Color
    from board import Board


class Piece(ABC):
    def __init__(self, color: Color, pos: tuple[int, int]):
        self.color = color
        self.pos = pos
        self.has_moved = False

    def find_move(
        self,
        board: Board,
        target_pos: tuple[int, int],
    ) -> Move | None:
        # Get all legal moves
        legal_moves: list[Move] = self.get_legal_moves(board)

        # Iterate through legal moves and find one that matches target
        for move in legal_moves:
            if move.end == target_pos:
                return move

        return None

    @abstractmethod
    def get_legal_moves(self, board: Board) -> list[Move]:
        pass


class SlidingPiece(Piece, ABC):
    def get_legal_moves(self, board):
        moves = []
        sr, sc = self.pos

        # Loop through each direction until an obstacle is found
        for dr, dc in self._get_directions():
            r, c = sr, sc
            while is_valid_coord(new_pos := (r + dr, c + dc)):
                obstacle = board.get_piece_at(new_pos)

                # Stop if there's a friendly piece
                if obstacle is not None and obstacle.color is self.color:
                    break

                # Add the move (enemy capture or empty square)
                moves.append(Move(self.pos, new_pos))
                r += dr
                c += dc

                # If an enemy piece was encountered, break after adding the move
                if obstacle is not None:
                    break

        return moves

    @abstractmethod
    def _get_directions(self) -> set[tuple[int, int]]:
        pass


class Bishop(SlidingPiece):
    def _get_directions(self) -> set[tuple[int, int]]:
        return {(1, 1), (-1, -1), (1, -1), (-1, 1)}

    def __str__(self) -> str:
        return "b" if self.color is Color.BLACK else "B"


class Rook(SlidingPiece):
    def _get_directions(self) -> set[tuple[int, int]]:
        return {(1, 0), (-1, 0), (0, 1), (0, -1)}

    def __str__(self) -> str:
        return "r" if self.color is Color.BLACK else "R"


class Queen(SlidingPiece):
    def _get_directions_set(self):
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

    def __str__(self) -> str:
        return "q" if self.color is Color.BLACK else "Q"


class Pawn(Piece):
    def __init__(self, color, pos):
        super().__init(color, pos)
        self.direction = 1 if self.color is Color.BLACK else -1
        self.blocked = False

    def get_legal_moves(self, board):
        pawn_moves = [
            (2 * self.direction, 0),
            (1 * self.direction, 0),
            (1 * self.direction, 1),
            (1 * self.direction, -1),
        ]
        moves = []
        sr, sc = self.pos

        for dr, dc in pawn_moves:
            er, _ = new_pos = (sr + dr, sc + dc)
            promotion = False

            # New position must be a valid coordinate
            if not is_valid_coord(new_pos):
                continue

            # Move forward two spaces if hasn't moved
            if abs(dr) == 2 and dc == 0 and not self.has_moved:
                if Evaluator.is_path_clear(board, self.pos, new_pos, include_end=True):
                    moves.append(Move(self.pos, new_pos, moved_two=True))

            # From this point on, move is only one square forward
            if abs(dr) != 1:
                continue

            # Check pawn promotion
            if (self.color is Color.WHITE and er == 0) or (
                self.color is Color.BLACK and er == 7
            ):
                promotion = True

            possible_piece = board.get_piece_at(new_pos)

            # Moves diagonally to capture
            if abs(dc) == 1:
                if (
                    possible_piece is not None
                    and possible_piece.color is not self.color
                ):
                    moves.append(Move(self.pos, new_pos, promote_pawn=promotion))
                elif self._en_passant_check(board, new_pos):
                    moves.append(
                        Move(self.pos, new_pos, promote_pawn=promotion, en_passant=True)
                    )

            # Move forward one space
            if dc == 0 and possible_piece is None:
                moves.append(Move(self.pos, new_pos, promote_pawn=promotion))

        return moves

    def _en_passant_check(self, board: Board, target_pos: tuple[int, int]) -> bool:
        en_passant_target_pos = (self.pos[0], target_pos[1])
        en_passant_target = board.get_piece_at(en_passant_target_pos)
        pos_to_algebraic = coord_to_algebraic(en_passant_target_pos)

        return (
            en_passant_target is not None
            and pos_to_algebraic == board.en_passant_target
            and en_passant_target.color is not self.color
        )

    def __str__(self) -> str:
        return "p" if self.color is Color.BLACK else "P"


class Knight(Piece):
    def get_legal_moves(self, board):
        knight_moves = [
            (1, 2),
            (-1, 2),
            (1, -2),
            (-1, -2),
            (2, 1),
            (-2, 1),
            (2, -1),
            (-2, -1),
        ]
        moves = []
        sr, sc = self.pos

        for dr, dc in knight_moves:
            new_pos = (sr + dr, sc + dc)

            if not is_valid_coord(new_pos):
                continue

            possible_piece = board.get_piece_at(new_pos)

            if possible_piece is not None and possible_piece.color is self.color:
                continue

            moves.append(Move(self.pos, new_pos))

        return moves

    def __str__(self) -> str:
        return "n" if self.color is Color.BLACK else "N"


class King(Piece):
    def get_legal_moves(self, board):
        king_moves = [
            (0, 1),
            (0, -1),
            (1, 0),
            (-1, 0),
            (1, 1),
            (1, -1),
            (-1, 1),
            (-1, -1),
            (0, 2),
            (0, -2),
        ]
        moves = []
        sr, sc = self.pos

        for dr, dc in king_moves:
            _, ec = new_pos = (sr + dr, sc + dc)

            possible_piece = board.get_piece_at(new_pos)

            if possible_piece is not None and possible_piece.color is self.color:
                continue  # Cannot capture same color piece

            # Castling
            if dr == 0 and abs(dc) == 2 and not self.has_moved:
                if Evaluator.is_in_check(board, self.color):
                    continue  # King is currently in check; can't castle

                # Grab corner rook
                rook_col = 0 if ec < sc else 7
                corner_rook = board.get_piece_at((sr, rook_col))

                if corner_rook is None or corner_rook.has_moved:
                    continue  # Corner rook doesn't exist or piece exists that move there

                if not Evaluator.is_path_clear(board, self.pos, corner_rook.pos):
                    continue  # Path between king and corner rook is obstructed

                # Ensure the 2 spaces the king travels are not under attack
                col_dir = 1 if ec > sc else -1
                if Evaluator.is_under_attack(
                    board, new_pos, self.color.opposite()
                ) or Evaluator.is_under_attack(
                    board, (sr, sc + col_dir), self.color.opposite()
                ):
                    continue

                moves.append(Move(self.pos, new_pos, castling=True))

            # Single space move
            if abs(dr) == 1 or abs(dc) == 1:
                if not Evaluator.is_under_attack(board, new_pos, self.color.opposite()):
                    moves.append(Move(self.pos, new_pos))

        return moves

    def __str__(self) -> str:
        return "k" if self.color is Color.BLACK else "K"
