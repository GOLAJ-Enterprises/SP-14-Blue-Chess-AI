from enum import Enum


class GameState(Enum):
    ACTIVE = "Active"  # Normal play
    CHECK = "Check"
    CHECKMATE = "Checkmate"
    STALEMATE = "Stalemate"
