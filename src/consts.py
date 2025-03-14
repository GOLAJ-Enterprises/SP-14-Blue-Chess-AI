from __future__ import annotations
from typing import TYPE_CHECKING

from pathlib import Path

if TYPE_CHECKING:
    import pygame

SCREEN_WIDTH = 800
SCREEN_HEIGHT = SCREEN_WIDTH
SQUARE_SIZE = SCREEN_WIDTH // 8

FPS = 10

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSETS_PIECES_DIR = PROJECT_ROOT / "assets" / "pieces_png"

PIECE_IMAGES: dict[str, pygame.surface.Surface] = {}
