from __future__ import annotations
from typing import TYPE_CHECKING
from dataclasses import dataclass

from .utils import algebraic_to_bitpos
from .literals import QUEEN, ROOK, BISHOP, KNIGHT
from .consts import PIECE_SYMBOLS, REVERSE_SQUARE_MAP

if TYPE_CHECKING:
    from .literals import Piece


@dataclass(frozen=True)
class Move:
    """Represents a move on the chessboard, with optional promotion."""

    from_sq: int
    to_sq: int
    promotion: Piece | None = None

    @classmethod
    def from_uci(cls, uci_str: str) -> Move:
        """Creates a Move instance from a UCI string like "e2e4" or "e7e8q".

        :param str uci_str: he UCI move string.
        :raises ValueError: Invalid UCI move given.
        :raises ValueError: Invalid promotion character given.
        :return Move: The Move instance representing the input.
        """
        if len(uci_str) not in {4, 5}:
            raise ValueError(f"Invalid UCI move: '{uci_str}'")

        from_sq = algebraic_to_bitpos(uci_str[0:2])
        to_sq = algebraic_to_bitpos(uci_str[2:4])

        promotion = None
        if len(uci_str) == 5:
            promo_char = uci_str[4].lower()
            promotion = {
                "q": QUEEN,
                "r": ROOK,
                "b": BISHOP,
                "n": KNIGHT,
            }.get(promo_char)

            if promotion is None:
                raise ValueError(f"Invalid promotion character: '{promo_char}'")

        return cls(from_sq, to_sq, promotion)

    def to_uci(self) -> str:
        return f"{REVERSE_SQUARE_MAP[self.from_sq]}{REVERSE_SQUARE_MAP[self.to_sq]}{PIECE_SYMBOLS[self.promotion] if self.promotion is not None else ''}"
