from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
import pygame

from .gui_event import GUIEvent, GUIEventData

from consts import SQUARE_SIZE, PIECE_IMAGES

if TYPE_CHECKING:
    from chess import Board


class Screen(ABC):
    @abstractmethod
    def handle_events(
        self, events: list[pygame.event.Event], **kwargs
    ) -> list[GUIEventData]:
        pass

    @abstractmethod
    def render(self, surface: pygame.surface.Surface, **kwargs) -> None:
        pass


class GameScreen(Screen):
    def __init__(self):
        self.selected_pos = None

    def handle_events(self, events, **kwargs):
        gui_events = []
        board: Board = kwargs.get("board")

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos_x, pos_y = pygame.mouse.get_pos()
                arr_pos = (pos_y // SQUARE_SIZE, pos_x // SQUARE_SIZE)
                piece = board.get_piece_at(arr_pos)

                if piece is not None and piece.color.value == board.active_color:
                    self.selected_pos = arr_pos
                elif self.selected_pos is not None:
                    gui_events.append(
                        GUIEventData(GUIEvent.MOVE_PIECE, (self.selected_pos, arr_pos))
                    )
                    self.selected_pos = None

        return gui_events

    def render(self, surface, **kwargs):
        board: Board = kwargs.get("board")
        self._draw_board(surface)
        self._draw_pieces(surface, board)

    def _draw_board(self, surface: pygame.surface.Surface):
        colors = [(240, 217, 181), (181, 136, 99)]  # Light and dark
        for row in range(8):
            for col in range(8):
                color = colors[(row + col) % 2]
                pygame.draw.rect(
                    surface,
                    color,
                    pygame.Rect(
                        col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE
                    ),
                )

    def _draw_pieces(self, surface: pygame.surface.Surface, board: Board):
        for row in range(8):
            for col in range(8):
                piece = board.get_piece_at((row, col))
                if piece is not None:
                    img = PIECE_IMAGES[str(piece)]
                    surface.blit(img, (col * SQUARE_SIZE, row * SQUARE_SIZE))
