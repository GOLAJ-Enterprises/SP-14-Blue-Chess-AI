from pathlib import Path

SCREEN_WIDTH = 800
SCREEN_HEIGHT = SCREEN_WIDTH
SQUARE_SIZE = SCREEN_WIDTH // 8

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = PROJECT_ROOT / "assets" / "pieces_svg"
CACHE_DIR = PROJECT_ROOT / ".cache" / "pngs"
