from __future__ import annotations
from typing import TYPE_CHECKING
import pygame

from decorators import require_init
from consts import SCREEN_HEIGHT, SCREEN_WIDTH, FPS

from pygame_gui import GUIEvent

if TYPE_CHECKING:
    from chess import ChessEngine
    from pygame_gui import ChessGUI


class GameInterface:
    def __init__(self, engine: ChessEngine, gui: ChessGUI):
        self.engine = engine
        self.gui = gui
        self._initialized = False

    def init(self):
        pygame.init()
        screen = pygame.display.set_mode((SCREEN_HEIGHT, SCREEN_WIDTH))
        pygame.display.set_caption("Chess AI Engine")

        self.gui.init(screen)

        self._initialized = True

    @require_init
    def run_game_loop(self) -> None:
        running = True
        clock = pygame.time.Clock()

        while running:
            pygame_events = pygame.event.get()
            self.gui.render_screen(self.engine.board)
            gui_events = self.gui.handle_events(pygame_events, self.engine.board)

            for event in pygame_events:
                if event.type == pygame.QUIT:
                    running = False

            for event, details in gui_events.items():
                if event == GUIEvent.MOVE_PIECE:
                    from_pos = details[0]
                    to_pos = details[1]
                    success = self.engine.move_piece(from_pos, to_pos)
                    print("Success" if success else "Failure")

            pygame.display.flip()
            clock.tick(FPS)
