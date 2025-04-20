import sys
from pathlib import Path


def resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and for PyInstaller .exe"""
    base_path = getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent)
    return Path(base_path) / relative_path
