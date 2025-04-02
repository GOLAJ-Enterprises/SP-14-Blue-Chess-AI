from typing import TypeAlias, Literal

Piece: TypeAlias = Literal[0, 1, 2, 3, 4, 5]
Color: TypeAlias = Literal[0, 1]
GameState: TypeAlias = Literal[0, 1, 2]
CastlingRight: TypeAlias = Literal[0b0001, 0b0010, 0b0100, 0b1000]

PAWN: Piece = 0
ROOK: Piece = 1
BISHOP: Piece = 2
KNIGHT: Piece = 3
QUEEN: Piece = 4
KING: Piece = 5

BLACK: Color = 0
WHITE: Color = 1

ACTIVE: GameState = 0
DRAW: GameState = 1
CHECKMATE: GameState = 2

W_KINGSIDE: CastlingRight = 0b1000
W_QUEENSIDE: CastlingRight = 0b0100
B_KINGSIDE: CastlingRight = 0b0010
B_QUEENSIDE: CastlingRight = 0b0001
