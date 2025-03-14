from __future__ import annotations
from typing import TYPE_CHECKING
import pygame

from ._screens import GameScreen

from consts import ASSETS_PIECES_DIR, SQUARE_SIZE, PIECE_IMAGES

if TYPE_CHECKING:
    from .gui_event import GUIEventData
    import pygame
    from chess import ChessEngine


class ChessGUI:
    def __init__(self, surface: pygame.surface.Surface, engine: ChessEngine):
        self.surface = surface
        self.engine = engine
        ChessGUI._load_piece_images()
        self.screens = {"Game": GameScreen()}
        self.current_screen = self.screens["Game"]

    def render_screen(self) -> None:
        self.current_screen.render(self.surface, board=self.engine.board)

    def handle_events(self, events: list[pygame.event.Event]) -> list[GUIEventData]:
        return self.current_screen.handle_events(events, board=self.engine.board)

    @staticmethod
    def _load_piece_images() -> None:
        png_map = {
            "P": "w_pawn.png",
            "p": "b_pawn.png",
            "R": "w_rook.png",
            "r": "b_rook.png",
            "B": "w_bishop.png",
            "b": "b_bishop.png",
            "N": "w_knight.png",
            "n": "b_knight.png",
            "Q": "w_queen.png",
            "q": "b_queen.png",
            "K": "w_king.png",
            "k": "b_king.png",
        }

        for symbol, filename in png_map.items():
            png_path = ASSETS_PIECES_DIR / filename

            if not png_path.exists():
                raise FileNotFoundError(f"Missing image file: {png_path}")

            raw_image = pygame.image.load(str(png_path)).convert_alpha()
            scaled_image = pygame.transform.smoothscale(
                raw_image, (SQUARE_SIZE, SQUARE_SIZE)
            )
            PIECE_IMAGES[symbol] = scaled_image
