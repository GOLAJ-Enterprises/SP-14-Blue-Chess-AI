class Board:

    # The term square as used in this class refers to the square of the chess board as represented in algebraic notation
    # The term index refers to a location in the nested list "_squares"
    # While every square has a corresponding index (and vice versa), to improve readability,
    # we will use algebraic notation squares whenever possible when passing board positions along.

    def __init__(self):
        # Create an 8 x 8 nested list to store chess pieces
        self._squares = [[0 for i in range(8)] for j in range(8)]

    # Returns index position of a given chess square
    def get_index(self, square: str) -> str:
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

    # Returns the contents of a given chess square
    def look(self, square):

        # Convert algebraic notation to list index
        index = self.get_index(square)

        # Return contents of list index
        return self._squares[square[0]][square[1]]

    def set(self, square, contents):