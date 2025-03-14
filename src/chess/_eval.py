from __future__ import annotations
from typing import TYPE_CHECKING
from itertools import chain
import copy

from ._utils import is_valid_coord, get_coords_between

if TYPE_CHECKING:
    from .pieces import Piece, King
    from ._color import Color
    from ._move import Move
    from .board import Board


class Evaluator:
    @staticmethod
    def is_under_attack(board: Board, pos: tuple[int, int], enemy_color: Color) -> bool:
        # TODO refine and add `after_move` bool
        from .pieces import King, Pawn  # Local import to avoid circular import

        enemy_pieces = Evaluator.get_pieces_by_color(board, enemy_color)
        r, c = pos

        for enemy in enemy_pieces:
            if enemy.pos == pos:
                continue

            er, ec = enemy.pos

            if isinstance(enemy, King):
                # To avoid infinite recursion, check if `pos` is adjacent to enemy king
                if max(abs(er - r), abs(ec - c)) == 1:
                    return True  # Enemy king able to capture
            elif isinstance(enemy, Pawn):
                if r == er + enemy.direction and abs(ec - c) == 1:
                    return True
            elif enemy.find_move(board, pos):
                return True  # Enemy can attack `pos`

        return False  # Space is not under attack by enemy

    @staticmethod
    def is_in_check(board: Board, color: Color) -> bool:
        king: King = board.kings[color]
        return Evaluator.is_under_attack(board, king.pos, king.color.opposite())

    @staticmethod
    def move_causes_own_check(board: Board, move: Move) -> bool:
        # Make a deep copy of the board to simulate the move
        board_copy = copy.deepcopy(board)

        # Grab the piece at `move.start`
        piece = board_copy.get_piece_at(move.start)

        if piece is None:
            raise ValueError("A piece must exist at the start of the move.")

        # if isinstance(piece, King):
        #    return False  # King manages itself

        sr, sc = move.start
        er, ec = move.end

        # Move piece
        board_copy.board_arr[sr][sc] = None
        board_copy.board_arr[er][ec] = piece
        piece.pos = move.end
        piece.has_moved = True

        # Return if the king is in check
        return Evaluator.is_in_check(board_copy, piece.color)

    @staticmethod
    def is_checkmate(board: Board, color: Color) -> bool:
        if not Evaluator.is_in_check(board, color):
            return False  # King must be in check

        if Evaluator._can_king_move_under_check(board, color):
            return False  # King can safely move to another position

        if Evaluator._can_king_block_attack(board, color):
            return False  # King can block attack using another piece

        return True  # Checkmate; game over

    @staticmethod
    def is_draw(board: Board, color: Color) -> bool:
        if _DrawEvaluator.is_50_move_rule(board):
            return True

        if _DrawEvaluator.is_75_move_rule(board):
            return True

        if _DrawEvaluator.is_threefold_repetition(board):
            return True

        if _DrawEvaluator.is_fivefold_repetition(board):
            return True

        if _DrawEvaluator.is_stalemate(board, color):
            return True

        if _DrawEvaluator.is_insufficient_material(board):
            return True

        return False

    @staticmethod
    def is_path_clear(
        board: Board,
        start: tuple[int, int],
        end: tuple[int, int],
        include_end: bool = False,
    ) -> bool:
        if not is_valid_coord(start) or not is_valid_coord(end):
            return False

        path = get_coords_between(start, end, include_end)
        return all(board.get_piece_at(coord) is None for coord in path)

    @staticmethod
    def get_pieces_by_color(board: Board, color: Color) -> list[Piece]:
        return [
            piece
            for piece in chain.from_iterable(board.board_arr)
            if piece is not None and piece.color is color
        ]

    @staticmethod
    def _can_king_move_under_check(board: Board, color: Color) -> bool:
        king = board.kings[color]

        king_moves = [
            (0, 1),  # up
            (0, -1),  # down
            (1, 0),  # right
            (-1, 0),  # left
            (1, 1),  # diagonal up-right
            (-1, -1),  # diagonal up-left
            (1, -1),  # diagonal down-right
            (-1, 1),  # Diagonal down-left
        ]

        sr, sc = king.pos
        for row_step, col_step in king_moves:
            end_pos = (sr + row_step, sc + col_step)

            if not is_valid_coord(end_pos):
                continue  # Position is off board; invalid move

            possible_piece = board.get_piece_at(end_pos)

            if possible_piece and possible_piece.color is king.color:
                continue  # Can't move to space with own color piece

            if Evaluator.is_under_attack(board, end_pos, king.color.opposite()):
                continue  # End position is under attack by enemy

            return True  # King can safely move

        return False  # King has no safe moves

    @staticmethod
    def _can_king_block_attack(board: Board, color: Color) -> bool:
        from .pieces import Rook, Bishop, Queen

        attacking_piece = None
        king: King = board.kings[color]
        friendly_pieces = Evaluator.get_pieces_by_color(board, king.color)
        enemy_pieces = Evaluator.get_pieces_by_color(board, king.color.opposite())

        for enemy in enemy_pieces:
            if enemy.find_move(board, king.pos) is None:
                continue  # Enemy must be able to capture king

            if attacking_piece is not None:
                return (
                    False  # If there are multiple attackers, attack cannot be blocked
                )

            attacking_piece = enemy

        # Attacking piece should always exist at this point in the code
        assert attacking_piece is not None

        attacker_path = get_coords_between(
            king.pos, attacking_piece.pos, include_end=True
        )

        for piece in friendly_pieces:
            if piece is king:
                continue

            legal_moves = piece.get_legal_moves(board)

            # Loop through enemy's path and see if friendly piece can block attack
            if isinstance(attacking_piece, (Rook, Bishop, Queen)):
                if any(
                    move.end == pos for move in legal_moves for pos in attacker_path
                ):
                    return True  # Piece can block attack
            elif any(move.end == attacking_piece.pos for move in legal_moves):
                return True  # Piece can block attack

        return False  # No pieces can block the attack


class _DrawEvaluator:
    @staticmethod
    def is_threefold_repetition(board: Board) -> bool:
        return any(board.state_counts[state] >= 3 for state in board.state_counts)

    @staticmethod
    def is_fivefold_repetition(board: Board) -> bool:
        return any(board.state_counts[state] >= 5 for state in board.state_counts)

    @staticmethod
    def is_50_move_rule(board: Board) -> bool:
        return board.halfmove_clock >= 100

    @staticmethod
    def is_75_move_rule(board: Board) -> bool:
        return board.halfmove_clock >= 150

    @staticmethod
    def is_stalemate(board: Board, color: Color) -> bool:
        if Evaluator.is_in_check(board, color):
            return False  # Not stalemate if in check

        pieces = Evaluator.get_pieces_by_color(board, color)

        # Check if any pieces can move anywhere on the board
        for piece in pieces:
            legal_moves = piece.get_legal_moves(board)
            if legal_moves:
                return False  # A piece can move; no stalemate

        return True

    @staticmethod
    def is_insufficient_material(board: Board) -> bool:
        from .pieces import Bishop

        pieces_count = {
            "k": 0,
            "q": 0,
            "n": 0,
            "b": 0,
            "r": 0,
            "p": 0,
            "K": 0,
            "Q": 0,
            "N": 0,
            "B": 0,
            "R": 0,
            "P": 0,
        }

        bishops: list[Bishop] = []

        # Count pieces
        for piece in chain.from_iterable(board.board_arr):
            pieces_count[str(piece)] += 1

            if isinstance(piece, Bishop):
                bishops.append(piece)

        total_pieces = sum(pieces_count.values())

        if not (pieces_count["k"] == 1 and pieces_count["K"] == 1):
            raise ValueError(
                "Something went wrong. Greater or less than 2 total kings detected."
            )

        # Kings only
        if total_pieces == 2:
            return True

        # Kings with single knight
        if (pieces_count["n"] == 1 or pieces_count["N"] == 1) and total_pieces == 3:
            return True

        # Kings with single bishop
        if (pieces_count["b"] == 1 or pieces_count["B"] == 1) and total_pieces == 3:
            return True

        # Kings with bishops
        if (
            pieces_count["b"] == 1
            and pieces_count["B"] == 1
            and total_pieces == 4
            and len(bishops) == 2
        ):
            # Ensure bishops are on same color squares
            r1, c1 = bishops[0].pos
            r2, c2 = bishops[1].pos
            return (r1 + c1) % 2 == (r2 + c2) % 2

        return False
