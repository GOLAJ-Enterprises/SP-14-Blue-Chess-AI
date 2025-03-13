from __future__ import annotations
import pygame
import cairosvg
from typing import TYPE_CHECKING

from _consts import SQUARE_SIZE, ASSETS_DIR, CACHE_DIR

if TYPE_CHECKING:
    from ..chess.pieces import Piece


class Renderer:
    @staticmethod
    def draw_board(screen: pygame.Surface) -> None:
        colors = [(240, 217, 181), (181, 136, 99)]  # Light and dark
        for row in range(8):
            for col in range(8):
                color = colors[(row + col) % 2]
                pygame.draw.rect(
                    screen,
                    color,
                    pygame.Rect(
                        col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE
                    ),
                )

    @staticmethod
    def draw_pieces(screen: pygame.Surface, board: list[list[Piece | None]]) -> None:
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece is not None:
                    img = PIECE_IMAGES[str(piece)]
                    screen.blit(img, (col * SQUARE_SIZE, row * SQUARE_SIZE))

    @staticmethod
    def load_piece_images(size: int = 100) -> None:
        global PIECE_IMAGES

        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        svg_map = {
            "P": "w_pawn.svg",
            "p": "b_pawn.svg",
            "R": "w_rook.svg",
            "r": "b_rook.svg",
            "B": "w_bishop.svg",
            "b": "b_bishop.svg",
            "N": "w_knight.svg",
            "n": "b_knight.svg",
            "Q": "w_queen.svg",
            "q": "b_queen.svg",
            "K": "w_king.svg",
            "k": "b_king.svg",
        }

        for symbol, filename in svg_map.items():
            svg_path = ASSETS_DIR / filename
            png_path = CACHE_DIR / f"{symbol}_{size}.png"

            if not png_path.exists():
                cairosvg.svg2png(
                    url=str(svg_path),
                    write_to=str(png_path),
                    output_width=size,
                    output_height=size,
                )

            PIECE_IMAGES[symbol] = pygame.image.load(str(png_path)).convert_alpha()
