from piece import *
from const import *

class Board:
    """The Board object tracks piece positions."""


    # The term square as used in this class refers to the square of the chess board as represented in algebraic notation
    # The term index refers to a location in the nested list "_squares"
    # While every square has a corresponding index (and vice versa), to improve readability,
    # we will use algebraic notation squares whenever possible when passing board positions along.
    # Maybe.

    def __init__(self):
        """Creates a board object for tracking piece positions."""

        # Create an 8 x 8 nested list to store chess pieces
        self._squares = [[None for i in range(COLS)] for j in range(ROWS)]


    def get_index(self, square: str) -> str:
        """Returns index position of a given chess square"""

        index = ""

        # Convert first letter of square to index position
        # e.g. the "e" in "e2" becomes "4"
        match square[0]:
            case "a":
                index += "0"
            case "b":
                index += "1"
            case "c":
                index += "2"
            case "d":
                index += "3"
            case "e":
                index += "4"
            case "f":
                index += "5"
            case "g":
                index += "6"
            case "h":
                index += "7"
            case _:
                return "-1" # TODO get this to crash the program l8r

        # Convert the number of the square to index position
        # e.g. the "2" in "e2" becomes "1"
        index += int(square[1]) - 1

        return index


    def look(self, square):
        """Returns the contents of a given chess square"""

        # Convert algebraic notation to list index
        index = self.get_index(square)

        # Return contents of list index
        return self._squares[ int(index[0]) ][ int(index[1]) ]

    def look(self, col, row):
        """Returns the contents of a given chess square"""

        # Return contents of list index
        return self._squares[col][row]


    def set(self, square, contents):
        """Set the contents of a square."""

        # Convert algebraic notation to list index
        index = self.get_index(square)

        # Set list[index] = contents
        self._squares[ int(index[0]) ][ int(index[1]) ] = contents


    def set_board(self, color):
        """Set up the pieces on the board"""

        #Set up the white pieces first
        front_row, rear_row = (6, 7) if color == "white" else (1, 0)

        # Pawns
        for col in range(8):
            self._squares[col][front_row] = Pawn("white")

        #Knights
        self._squares[1][rear_row] = Knight("white")
        self._squares[6][rear_row] = Knight("white")

        #Bishops
        self._squares[2][rear_row] = Bishop("white")
        self._squares[5][rear_row] = Bishop("white")

        #Rooks
        #self._squares[0][rear_row] = Rook("white")
        #self._squares[7][rear_row] = Rook("white")

        #Queen
        #self._squares[3][rear_row] = Queen("white")

        #King
        #self._squares[4][rear_row] = King("white")