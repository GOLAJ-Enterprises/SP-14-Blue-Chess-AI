from abc import ABC, abstractmethod

from board import Board


class Piece:
    @abstractmethod
    def __init__(self, board: Board, square):
        self.board = board
        self.square = square

    @abstractmethod
    def can_move(self, square: str) -> bool:
        pass

    @abstractmethod
    def move(self, square: str):
        pass
