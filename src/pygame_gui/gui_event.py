from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto


class GUIEvent(Enum):
    MOVE_PIECE = auto()


@dataclass
class GUIEventData:
    type: GUIEvent
    data: any
