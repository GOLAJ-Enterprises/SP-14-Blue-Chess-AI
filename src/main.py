import pygame
import sys

from const import *
from game import Game

class Main:


    def __init__(self):
        """Initialization on game startup"""

        pygame.init()
        self.screen = pygame.display.set_mode( (WIDTH, HEIGHT) )
        pygame.display.set_caption("Chess")
        self.game = Game()

    def mainloop(self):
        """This continuously loops as the program is running"""

        while True:

            self.game.draw_bg(self.screen)

            self.game.draw_pieces(self.screen)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            pygame.display.update()


main = Main()
main.mainloop()