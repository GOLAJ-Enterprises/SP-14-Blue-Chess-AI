import pygame

from const import *


class Game:

    def __init__(self):
        pass

    def show_bg(self, surface):

        for row in range(8):
            for col in range(8):
                if (row + col) % 2 == 0:
                    color = DARKSQ  # Even squares are dark
                else:
                    color = LIGHTSQ # Odd squares are light

                #Create a square at x=col*sqsize, y=row*sqsize with size sqsize by sqsize
                square = (col * SQSIZE, row * SQSIZE, SQSIZE, SQSIZE)

                pygame.draw.rect(surface, color, square)