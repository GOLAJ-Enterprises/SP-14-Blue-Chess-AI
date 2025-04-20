import re

from .literals import (
    ROOK,
    BISHOP,
    QUEEN,
    BLACK,
    WHITE,
    W_KINGSIDE,
    W_QUEENSIDE,
    B_KINGSIDE,
    B_QUEENSIDE,
)
from .mask_gens import (
    gen_king_mask,
    gen_knight_mask,
    gen_pawn_atk_mask,
    gen_pawn_double_push_mask,
    gen_pawn_push_mask,
    gen_ray_mask,
)

# -- Literal constants --

# Piece symbols (index corresponds to piece type enum: PAWN = 0, ROOK = 1, etc.)
PIECE_SYMBOLS = ["p", "r", "b", "n", "q", "k"]

# Color symbols (index corresponds to color enum: BLACK = 0, WHITE = 1)
COLOR_SYMBOLS = ["b", "w"]

# Maps FEN castling characters to their corresponding bit flag
CHAR_TO_CASTLING_BIT = {
    "K": W_KINGSIDE,
    "Q": W_QUEENSIDE,
    "k": B_KINGSIDE,
    "q": B_QUEENSIDE,
}

# Game state labels used internally
GAME_STATE_NAMES = ["active", "draw", "checkmate"]

# -- FEN constants --

# Standard starting position in FEN notation
STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

# Regex for parsing FEN strings into board, turn, castling rights, en passant, etc.
FEN_REGEX = re.compile(
    r"""^
    (?P<board>([rnbqkpRNBQKP1-8]+/){7}[rnbqkpRNBQKP1-8]+)\s
    (?P<turn>[wb])\s
    (?P<castling>K?Q?k?q?|-)\s
    (?P<ep>-|[a-h][36])\s
    (?P<halfmove>\d+)\s
    (?P<fullmove>[1-9]\d*)
    $""",
    re.VERBOSE,
)

# -- Board position constants --

# Maps algebraic notation (e.g. "e4") to square index (0–63)
SQUARE_MAP = {
    f"{file}{rank}": (rank - 1) * 8 + file_idx
    for rank in range(1, 9)
    for file_idx, file in enumerate("abcdefgh")
}

# Reverse of SQUARE_MAP: maps square index to algebraic notation
REVERSE_SQUARE_MAP = {v: k for k, v in SQUARE_MAP.items()}

# -- Logic masks --

# Precomputed attack masks for knights and kings on each square
KNIGHT_MASKS = [gen_knight_mask(sq) for sq in range(64)]
KING_MASKS = [gen_king_mask(sq) for sq in range(64)]

# Bitboards marking the promotion and starting ranks for pawns
PAWN_PROMOTION_RANK = [0x0000_0000_0000_00FF, 0xFF00_0000_0000_0000]  # [BLACK, WHITE]
PAWN_START_RANK = [0x00FF_0000_0000_0000, 0x0000_0000_0000_FF00]  # [BLACK, WHITE]

# Precomputed pawn attack masks per square, for both colors
PAWN_ATK_MASKS = [
    [gen_pawn_atk_mask(sq, BLACK) for sq in range(64)],
    [gen_pawn_atk_mask(sq, WHITE) for sq in range(64)],
]

# Precomputed single push masks for pawns
PAWN_SINGLE_PUSH_MASKS = [
    [gen_pawn_push_mask(sq, BLACK) for sq in range(64)],
    [gen_pawn_push_mask(sq, WHITE) for sq in range(64)],
]

# Precomputed double push masks for pawns
PAWN_DOUBLE_PUSH_MASKS = [
    [gen_pawn_double_push_mask(sq, BLACK) for sq in range(64)],
    [gen_pawn_double_push_mask(sq, WHITE) for sq in range(64)],
]

# -- RAYS --

# Direction vectors used for sliding piece movement and ray generation
DIRECTIONS = {
    "N": (0, 1),
    "S": (0, -1),
    "E": (1, 0),
    "W": (-1, 0),
    "NE": (1, 1),
    "NW": (-1, 1),
    "SE": (1, -1),
    "SW": (-1, -1),
}

# Precomputed ray bitboards for each direction and square
# RAYS["N"][square] gives the northward ray from that square, etc.
RAYS = {
    direction: [gen_ray_mask(sq, *delta) for sq in range(64)]
    for direction, delta in DIRECTIONS.items()
}

# -- Direction constants --

# Direction groupings by piece type
ROOK_DIRECTIONS = ["N", "S", "W", "E"]
BISHOP_DIRECTIONS = ["NW", "NE", "SW", "SE"]
QUEEN_DIRECTIONS = ROOK_DIRECTIONS + BISHOP_DIRECTIONS

# Used to determine whether to use lsb or msb when trimming rays
POSITIVE_DIRECTIONS = {"N", "NE", "E", "NW"}
NEGATIVE_DIRECTIONS = {"S", "SW", "W", "SE"}

# Maps piece type to allowed sliding directions
DIRECTIONS_MAP = {
    ROOK: ROOK_DIRECTIONS,
    BISHOP: BISHOP_DIRECTIONS,
    QUEEN: QUEEN_DIRECTIONS,
}

# Maps from a square to all other reachable squares and the direction to reach them
# Useful for detecting pins and rays between pieces
RAYS_DIRECTIONS_MAP = {
    from_sq: {
        to_sq: direction
        for direction, (df, dr) in DIRECTIONS.items()
        for step in range(1, 8)
        if (
            0 <= (to_file := (from_sq % 8) + df * step) < 8
            and 0 <= (to_rank := (from_sq // 8) + dr * step) < 8
            and (to_sq := to_rank * 8 + to_file) != from_sq
        )
    }
    for from_sq in range(64)
}
