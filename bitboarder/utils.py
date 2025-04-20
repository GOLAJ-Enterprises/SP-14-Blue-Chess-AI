from __future__ import annotations
from typing import TYPE_CHECKING

from .consts import (
    SQUARE_MAP,
    REVERSE_SQUARE_MAP,
    FEN_REGEX,
    PIECE_SYMBOLS,
    COLOR_SYMBOLS,
    CHAR_TO_CASTLING_BIT,
    GAME_STATE_NAMES,
    RAYS,
    DIRECTIONS,
)
from .literals import W_KINGSIDE, W_QUEENSIDE, B_KINGSIDE, B_QUEENSIDE, BLACK, WHITE
from .bit_utils import mask, not64

if TYPE_CHECKING:
    from .literals import Color, Piece, GameState


def algebraic_to_bitpos(uci_sq: str) -> int:
    """Converts an algebraic square (e.g., 'e4') to a bitboard index (0–63).

    :param str uci_sq: The square in algebraic notation.
    :return int: The corresponding bitboard index.
    """
    return SQUARE_MAP[uci_sq]


def bitpos_to_algebraic(bitpos: int) -> str:
    """Converts a bitboard index (0–63) to its algebraic square notation (e.g., 'e4').

    :param int bitpos: The bitboard index.
    :return str: The corresponding algebraic square.
    """
    return REVERSE_SQUARE_MAP[bitpos]


def opp_color(color: Color) -> Color:
    """Returns the opposite color.

    :param Color color: The input color (WHITE or BLACK).
    :return Color: The opposite color.
    """
    return color ^ 1


def ray_between(sq1: int, sq2: int) -> int:
    """Returns a bitboard representing the squares between sq1 and sq2 along a shared ray.

    If sq2 is on a ray originating from sq1, this returns all squares between them (exclusive).
    Otherwise, returns 0.

    :param int sq1: Starting square.
    :param int sq2: Target square.
    :return int: Bitboard of intermediate squares, or 0 if not aligned on a ray.
    """
    for direction in DIRECTIONS.keys():
        ray = RAYS[direction][sq1]
        if mask(sq2) & ray:
            # Remove squares beyond sq2 and exclude sq2 itself
            ray_mask = (ray ^ RAYS[direction][sq2]) & not64(mask(sq2))
            return ray_mask

    return 0


def is_along_ray(a: int, b: int, c: int) -> bool:
    """Checks if squares b and c lie along the same ray originating from a.

    Useful for verifying pin alignment or directionality along sliding piece paths.

    :param int a: The origin square.
    :param int b: The first square to test.
    :param int c: The second square to test.
    :return bool: True if both b and c are on the same ray from a, else False.
    """
    for direction in DIRECTIONS.keys():
        ray = RAYS[direction][a]

        if mask(b) & ray and mask(c) & ray:
            return True

    return False


def get_piece_symbol(piece: Piece) -> str:
    """Returns the lowercase symbol corresponding to a piece type.

    :param Piece piece: The piece type (e.g., PAWN, ROOK).
    :return str: The corresponding symbol (e.g., 'p', 'r').
    """
    return PIECE_SYMBOLS[piece]


def get_piece_from_symbol(symbol: str) -> Piece:
    """Returns the piece type index corresponding to a symbol.

    :param str symbol: A lowercase piece symbol (e.g., 'n', 'q').
    :return Piece: The corresponding piece type.
    """
    return PIECE_SYMBOLS.index(symbol)


def get_color_symbol(color: Color) -> str:
    """Returns the color symbol for a given color index.

    :param Color color: The color (BLACK or WHITE).
    :return str: 'b' for black, 'w' for white.
    """
    return COLOR_SYMBOLS[color]


def get_color_from_symbol(symbol: str) -> Color:
    """Returns the color index corresponding to a symbol.

    :param str symbol: 'b' or 'w'.
    :return Color: The corresponding color index.
    """
    return COLOR_SYMBOLS.index(symbol)


def get_game_state_name(state: GameState) -> str:
    """Returns the name of a game state from its enum value.

    :param GameState state: The game state enum value.
    :return str: 'active', 'draw', or 'checkmate'.
    """
    return GAME_STATE_NAMES[state]


def castling_rights_to_str(rights: int) -> str:
    """Converts a castling rights bitfield into the FEN string representation.

    Outputs characters 'KQkq' based on which castling rights are set,
    or '-' if no rights are available.

    :param int rights: Bitfield representing available castling rights.
    :return str: FEN-compatible string for castling rights.
    """
    s = (
        ("K" if rights & W_KINGSIDE else "")
        + ("Q" if rights & W_QUEENSIDE else "")
        + ("k" if rights & B_KINGSIDE else "")
        + ("q" if rights & B_QUEENSIDE else "")
    )
    return s or "-"  # FEN requires '-' if no castling rights exist


def str_to_castling_rights(fen_castling: str) -> int:
    """Parses the castling portion of a FEN string into a bitfield.

    Each character corresponds to a specific castling right (e.g., 'K', 'q').

    :param str fen_castling: The castling availability string from FEN (e.g., 'KQkq' or '-').
    :return int: Bitfield representing available castling rights.
    """
    if fen_castling == "-":
        return 0

    rights = 0
    for c in fen_castling:
        rights |= CHAR_TO_CASTLING_BIT[c]  # Accumulate castling bits

    return rights


def is_valid_fen(fen: str) -> bool:
    """Checks if a FEN string is syntactically valid and structurally correct.

    Validates FEN format using regex and ensures each rank contains exactly 8 squares.

    :param str fen: The full FEN string to validate.
    :return bool: True if the FEN is valid, False otherwise.
    """
    fen = fen.strip()

    match = FEN_REGEX.match(fen)
    if not match:
        return False  # FEN format doesn't match the regex

    # Validate that each rank adds up to exactly 8 squares
    ranks = match.group("board").split("/")
    for rank in ranks:
        count = 0
        for c in rank:
            if c.isdigit():
                count += int(c)
            elif c.lower() in "prnbqk":
                count += 1
            else:
                return False  # Invalid character found

        if count != 8:
            return False  # Rank doesn't have exactly 8 squares

    return True


def get_bitboard_from_fen(fen_board: str) -> list[list[int]]:
    """Parses the board portion of a FEN string into bitboards by color and piece type.

    The output is a 2D list where bitboards[color][piece_type] contains
    the bitboard for that piece type and color.

    :param str fen_board: The board segment of a FEN string (e.g. 'rnbqkbnr/pppppppp/...').
    :return list[list[int]]: A 2x6 matrix of bitboards [color][piece_type].
    """
    bitboards = [[0] * 6, [0] * 6]  # [BLACK][piece_type], [WHITE][piece_type]

    rank_offset = 56  # Start from rank 8 (top row in FEN)
    for row in fen_board.split("/"):
        file_offset = 0

        for char in row:
            if char.isdigit():
                file_offset += int(char)  # Empty squares
            else:
                # Get piece type and color from symbol
                piece_type = get_piece_from_symbol(char.lower())
                color = BLACK if char.islower() else WHITE

                # Compute square index and set corresponding bit
                square = rank_offset + file_offset
                piece_mask = mask(square)
                bitboards[color][piece_type] |= piece_mask

                file_offset += 1

        rank_offset -= 8  # Move to next rank

    return bitboards
