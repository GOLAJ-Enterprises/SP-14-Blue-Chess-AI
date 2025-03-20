from dataclasses import dataclass


@dataclass(frozen=True)
class Move:
    start: tuple[int, int]
    end: tuple[int, int]
    promote_pawn: bool = False
    castling: bool = False
    en_passant: bool = False
    moved_two: bool = False
