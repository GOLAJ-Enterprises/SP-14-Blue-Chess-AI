import random

# -- Zobrist hashing setup --

random.seed(42)  # Ensure reproducibility for testing and debugging

NUM_SQUARES = 64
NUM_PIECES = 6
NUM_COLORS = 2

# Zobrist keys for piece positions: [piece_type][color][square]
ZOBRIST_PIECE = [
    [[random.getrandbits(64) for _ in range(NUM_SQUARES)] for _ in range(NUM_COLORS)]
    for _ in range(NUM_PIECES)
]

# Zobrist keys for 16 possible castling rights combinations (bitfield from 0–15)
ZOBRIST_CASTLING = [random.getrandbits(64) for _ in range(16)]

# Zobrist keys for en passant files (only a–h matter)
ZOBRIST_EN_PASSANT = [random.getrandbits(64) for _ in range(8)]

# Zobrist key for which side is to move (black or white)
ZOBRIST_SIDE_TO_MOVE = random.getrandbits(64)
