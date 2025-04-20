def pop_lsb(bb: int) -> tuple[int, int]:
    """Returns the index of the least significant set bit and clears it from the bitboard.

    :param int bb: Bitboard to pop from.
    :return tuple[int, int]: A tuple (index, new_bitboard) after popping the LSB.
    """
    lsb_idx = (bb & -bb).bit_length() - 1
    bb &= bb - 1
    return lsb_idx, bb


def lsb(bb: int) -> int:
    """Returns the index of the least significant set bit.

    :param int bb: Bitboard to check.
    :return int: Index of the LSB.
    """
    return (bb & -bb).bit_length() - 1


def msb(bb: int) -> int:
    """Returns the index of the most significant set bit.

    :param int bb: Bitboard to check.
    :return int: Index of the MSB.
    """
    return bb.bit_length() - 1


def not64(x: int) -> int:
    """Returns the bitwise NOT of a 64-bit integer (masked to 64 bits).

    :param int x: Input bitboard.
    :return int: Inverted bitboard, limited to 64 bits.
    """
    return ~x & 0xFFFF_FFFF_FFFF_FFFF


def mask(sq: int) -> int:
    """Returns a bitboard with a single bit set at the given square index.

    :param int sq: Square index (0–63).
    :return int: Bitboard with bit `sq` set.
    """
    return 1 << sq
