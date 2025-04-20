from __future__ import annotations
from typing import TYPE_CHECKING

from .literals import WHITE

if TYPE_CHECKING:
    from .literals import Color


def gen_knight_mask(square: int) -> int:
    """Generates a bit mask of all valid knight moves from a given square.

    The knight moves in L-shapes: two steps in one direction and one step in the perpendicular
    direction. This function calculates all such possible destinations from the given square,
    excluding any that would move off the board.

    :param int square: The square to generate the knight moves from.
    :return int: The knight move mask.
    """
    # Decode square index into (file, rank)
    file = square % 8
    rank = square // 8
    mask = 0

    # Try all 8 potential knight jumps
    for df, dr in [
        (-2, -1),
        (-2, 1),
        (-1, -2),
        (-1, 2),
        (1, -2),
        (1, 2),
        (2, -1),
        (2, 1),
    ]:
        new_file = file + df
        new_rank = rank + dr

        # Skip move if it would leave the board
        if 0 <= new_file < 8 and 0 <= new_rank < 8:
            target_sq = new_rank * 8 + new_file
            mask |= 1 << target_sq

    return mask


def gen_ray_mask(square: int, df: int, dr: int) -> int:
    """Generates ray bit masks from a position on the chessboard,
    from a direction, `df` and `dr`, a ray from and excluding the position to
    the edge of the board in the direction.

    :param int square: The square to generate the ray from.
    :param int df: Delta file (0, 1, -1). Indicates which direction to go column-wise.
    :param int dr: Delta row (0, 1, -1). Indicates which direction to go row-wise.
    :return int: The ray mask.
    """
    # Decode square index into (file, rank)
    file = square % 8
    rank = square // 8
    mask = 0
    step = 1

    # Traverse in the given (df, dr) direction until off-board
    while (
        0 <= (new_file := file + df * step) < 8
        and 0 <= (new_rank := rank + dr * step) < 8
    ):
        # Convert (file, rank) back to square index and set the bit
        target_sq = new_rank * 8 + new_file
        mask |= 1 << target_sq
        step += 1

    return mask


def gen_king_mask(square: int) -> int:
    """Generates a bit mask of all valid king moves from a given square.

    The king moves one square in any direction (horizontal, vertical, or diagonal).
    This function calculates all such legal destinations from the given square,
    excluding any that would go off the board.

    :param int square: The square to generate the king moves from.
    :return int: The king move mask.
    """
    # Decode square index into (file, rank)
    file = square % 8
    rank = square // 8
    mask = 0

    # Check all 8 adjacent directions
    for df, dr in [
        (-1, -1),
        (0, -1),
        (1, -1),
        (-1, 0),
        (1, 0),
        (-1, 1),
        (0, 1),
        (1, 1),
    ]:
        new_file = file + df
        new_rank = rank + dr

        # Skip move if it would leave the board
        if 0 <= new_file < 8 and 0 <= new_rank < 8:
            target_sq = new_rank * 8 + new_file
            mask |= 1 << target_sq

    return mask


def gen_pawn_atk_mask(square: int, color: Color) -> int:
    """Generates a bit mask of pawn attack targets from a given square.

    Pawns attack diagonally forward depending on their color. This function
    computes the two squares a pawn can attack from the given square, excluding
    any that would move off the board.

    :param int square: The square the pawn is on.
    :param Color color: The color of the pawn (WHITE or BLACK).
    :return int: The pawn attack mask.
    """
    # Decode square index into (file, rank)
    file = square % 8
    rank = square // 8
    direction = 1 if color == WHITE else -1  # Forward direction depends on color
    mask = 0

    # Try diagonal-left and diagonal-right attacks
    for df in [-1, 1]:
        new_file = file + df
        new_rank = rank + direction

        # Skip move if it would leave the board
        if 0 <= new_file < 8 and 0 <= new_rank < 8:
            target_sq = new_rank * 8 + new_file
            mask |= 1 << target_sq

    return mask


def gen_pawn_push_mask(square: int, color: Color) -> int:
    """Generates a bit mask for a single forward pawn push from a given square.

    Pawns move one square forward (not diagonally), with the direction depending
    on color. This function returns a mask for the square the pawn would move to
    if it's within bounds.

    :param int square: The square the pawn is on.
    :param Color color: The color of the pawn (WHITE or BLACK).
    :return int: The pawn push mask.
    """
    direction = 8 if color == WHITE else -8  # One rank forward based on color
    target = square + direction

    # Return bitmask if target is on the board; otherwise, return 0
    return (1 << target) if 0 <= target < 64 else 0


def gen_pawn_double_push_mask(square: int, color: Color) -> int:
    """Generates a bit mask for a pawn's initial two-square push, if legal.

    Pawns can move two squares forward from their starting rank.
    This function checks if the pawn is on its initial rank and computes the
    mask for the double push destination if it's within bounds.

    :param int square: The square the pawn is on.
    :param Color color: The color of the pawn (WHITE or BLACK).
    :return int: The double push mask, or 0 if not applicable.
    """
    start_rank = 1 if color == WHITE else 6
    if square // 8 != start_rank:
        return 0  # Not on starting rank, so double push is illegal

    direction = 16 if color == WHITE else -16  # Two ranks forward
    target_sq = square + direction

    # Return bitmask if target is on the board; otherwise, return 0
    return (1 << target_sq) if 0 <= target_sq < 64 else 0
