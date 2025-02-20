import os
import pygame
import io

from const import *
from board import *


class Piece:
    """Superclass for all piece objects."""

    def __init__(self, name, color, texture=None):
        self.name = name
        self.color = color
       # self.texture = os.path.join(f"../assets/images/{name}{color}.svg")
        self.texture = load_and_scale_svg(f"{name}{color}", PIECE_SCALE)

def load_and_scale_svg(filename, scale):
    """Loads an svg file and scales it to be scale pixels wide"""


    filepath = os.path.join(f"../assets/images/{filename}.svg")
    svg_string = open(filepath, "rt").read()
    start = svg_string.find('<svg')
    if start > 0:
        svg_string = svg_string[:start + 4] + f' transform="scale({scale})" width="{SQSIZE}" height="{SQSIZE}"' + svg_string[start + 4:]
    return pygame.image.load(io.BytesIO(svg_string.encode()))


class Pawn(Piece):

    def __init__(self, color):
        super().__init__("pawn", color)


class Knight(Piece):

    def __init__(self, color):
        super().__init__("knight", color)


class Bishop(Piece):

    def __init__(self, color):
        super().__init__("bishop", color)


class Rook:

    def __init__(self, color):
        super().__init__("rook", color)


class Queen:

    def __init__(self, color):
        super().__init__("queen", color)


class King:

    def __init__(self, color):
        super().__init__("king", color)
