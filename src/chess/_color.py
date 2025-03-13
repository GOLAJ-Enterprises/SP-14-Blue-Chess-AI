from enum import Enum


class Color(Enum):
    WHITE = "w"
    BLACK = "b"

    def opposite(self) -> "Color":
        """Returns the opposite of the current color."""
        return Color.BLACK if self is Color.WHITE else Color.WHITE
