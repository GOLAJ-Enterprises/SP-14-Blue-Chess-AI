import pygame
from board import *
from const import *


class Game:

    def __init__(self):
        self.board = Board()

        #Setting up the board for player as white pieces
        self.board.set_board("white")

    def draw_bg(self, surface):
        """Displays the background tiles of the chess board."""

        for row in range(8):
            for col in range(8):
                color = DARKSQ if (row + col) % 2 == 0 else LIGHTSQ


                #Create a square at x=col*sqsize, y=row*sqsize with size sqsize by sqsize
                square = (col * SQSIZE, row * SQSIZE, SQSIZE, SQSIZE)

                pygame.draw.rect(surface, color, square)

    def draw_pieces(self, surface):
        """Draws the chess pieces onto the board"""

        for row in range(ROWS):
            for col in range(COLS):
                if self.board.look(col, row) is not None:

                    piece = self.board.look(col, row)

                    img = piece.texture
                    img_center = (col * SQSIZE + SQSIZE * 0.05, row * SQSIZE)

                    surface.blit(img, img_center)

