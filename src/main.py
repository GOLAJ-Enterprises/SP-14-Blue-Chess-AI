from __future__ import annotations
from typing import TYPE_CHECKING
import pygame

from chess import ChessEngine
from pygame_gui import ChessGUI, GUIEvent

from consts import SCREEN_HEIGHT, SCREEN_WIDTH, FPS

if TYPE_CHECKING:
    pass


def main():
    # Initialize pygame
    pygame.init()
    surface = pygame.display.set_mode((SCREEN_HEIGHT, SCREEN_WIDTH))
    pygame.display.set_caption("Chess AI Engine")

    # Initialize engine and gui
    engine = ChessEngine()
    gui = ChessGUI(surface, engine)

    # Start running loop
    running = True
    clock = pygame.time.Clock()

    while running:
        pygame_events = pygame.event.get()
        gui.render_screen()
        gui_events = gui.handle_events(pygame_events)

        # Go through pygame events
        for event in pygame_events:
            if event.type == pygame.QUIT:
                running = False

        # Go through gui-to-engine events
        for event in gui_events:
            data = event.data

            if event.type is GUIEvent.MOVE_PIECE:
                from_pos = data[0]
                to_pos = data[1]
                success = engine.move_piece(from_pos, to_pos)
                print("Successful move" if success else "Failed to move")

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
