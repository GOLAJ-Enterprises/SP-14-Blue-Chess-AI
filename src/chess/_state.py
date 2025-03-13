from enum import Enum


class State(Enum):
    ACTIVE = "Active"  # Normal play
    CHECKMATE = "Checkmate"
    DRAW = "Draw"
