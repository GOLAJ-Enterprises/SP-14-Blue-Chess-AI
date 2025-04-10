from __future__ import annotations
from typing import TYPE_CHECKING
from dataclasses import dataclass
from collections import defaultdict

from .generators import PseudoLegalMoveGenerator, AttackMapGenerator, LegalMoveGenerator
from .literals import (
    WHITE,
    BLACK,
    PAWN,
    KING,
    ROOK,
    BISHOP,
    QUEEN,
    KNIGHT,
    W_KINGSIDE,
    W_QUEENSIDE,
    B_KINGSIDE,
    B_QUEENSIDE,
    ACTIVE,
    DRAW,
    CHECKMATE,
)
from .consts import STARTING_FEN, DIRECTIONS_MAP, RAYS
from .utils import (
    is_valid_fen,
    algebraic_to_bitpos,
    bitpos_to_algebraic,
    get_color_from_symbol,
    get_color_symbol,
    get_piece_symbol,
    str_to_castling_rights,
    castling_rights_to_str,
    get_bitboard_from_fen,
    opp_color,
    ray_between,
)
from .bit_utils import pop_lsb, mask, not64, lsb
from .zobrist import (
    ZOBRIST_CASTLING,
    ZOBRIST_EN_PASSANT,
    ZOBRIST_PIECE,
    ZOBRIST_SIDE_TO_MOVE,
)

if TYPE_CHECKING:
    from .literals import Piece, Color, GameState
    from .move import Move


@dataclass(frozen=True)
class _UndoInfo:
    """Stores all state needed to undo a move and restore the previous board state."""

    from_sq: int
    to_sq: int
    moved_piece: tuple[Piece, Color]
    captured_piece: tuple[Piece, Color] | None
    capture_sq: int
    promotion_piece: Piece | None
    active_color: Color
    castling_rights: int
    en_passant_square: int | None
    halfmove_clock: int
    fullmove_count: int
    zobrist_hash: int
    game_state: int


class Board:
    """Represents the full game state, including piece positions, castling rights, and move generation."""

    def __init__(self, fen: str = STARTING_FEN):
        fen = fen.strip()

        # Initialize generators and rule evaluator
        self.attack_map_gen = AttackMapGenerator(self)
        self.pseudo_move_gen = PseudoLegalMoveGenerator(self)
        self.legal_move_gen = LegalMoveGenerator(self)

        # Initialize starting board state
        self.active_color: Color = WHITE
        self.game_state: GameState = ACTIVE
        self.castling_rights = 0b1111
        self.en_passant_square = None
        self.halfmove_clock = 0
        self.fullmove_count = 1
        self.piece_map: dict[int, tuple[Piece, Color]] = {}
        self.zobrist_hash = 0
        self.unique_history: dict[int, int] = defaultdict(int)
        self.history_stack: list[_UndoInfo] = []
        self.bitboards = [
            [  # BLACK
                0x00FF_0000_0000_0000,  # Pawns (rank 7)
                0x8100_0000_0000_0000,  # Rooks (a8, h8)
                0x2400_0000_0000_0000,  # Bishops (c8, f8)
                0x4200_0000_0000_0000,  # Knights (b8, g8)
                0x0800_0000_0000_0000,  # Queen (d8)
                0x1000_0000_0000_0000,  # King (e8)
            ],
            [  # WHITE
                0x0000_0000_0000_FF00,  # Pawns (rank 2)
                0x0000_0000_0000_0081,  # Rooks (a1, h1)
                0x0000_0000_0000_0024,  # Bishops (c1, f1)
                0x0000_0000_0000_0042,  # Knights (b1, g1)
                0x0000_0000_0000_0008,  # Queen (d1)
                0x0000_0000_0000_0010,  # King (e1)
            ],
        ]

        # Cache
        self.pinned: list[int]
        self.check_mask: int
        self.attacked: list[int]
        self.pseudo_legal_moves: list[set[Move]]
        self.legal_moves: set[Move]
        self.occupied = [
            0xFFFF_0000_0000_0000,  # BLACK
            0x0000_0000_0000_FFFF,  # WHITE
        ]

        if fen != STARTING_FEN and is_valid_fen(fen):
            self.set_from_fen(fen)
        else:
            self._post_init()

    def reset(self) -> None:
        """Resets the board to the standard starting position using STARTING_FEN."""
        self.__init__()

    def set_from_fen(self, fen: str) -> bool:
        """Parses a FEN string and sets the internal board state accordingly.

        :param str fen: The FEN string to parse.
        :return bool: True if FEN is valid and successfully applied, otherwise False.
        """
        fen = fen.strip()

        if not is_valid_fen(fen):
            return False

        (
            fen_board,
            fen_color,
            fen_castling,
            fen_en_passant,
            fen_halfmove,
            fen_fullmove,
        ) = fen.split()

        # Set basic game state from FEN components
        self.active_color = get_color_from_symbol(fen_color)
        self.castling_rights = str_to_castling_rights(fen_castling)
        self.en_passant_square = (
            None if fen_en_passant == "-" else algebraic_to_bitpos(fen_en_passant)
        )
        self.halfmove_clock = int(fen_halfmove)
        self.fullmove_count = int(fen_fullmove)
        self.bitboards = get_bitboard_from_fen(fen_board)

        # Recompute derived state
        self._build_occupied()
        self._post_init()

        return True

    def is_in_check(self) -> bool:
        """Checks if the active player's king is currently in check.

        :return bool: True if the king is in check, else False.
        """
        return self.check_mask != 0xFFFF_FFFF_FFFF_FFFF

    def is_checkmate(self) -> bool:
        """Checks if the active player is checkmated.

        :return bool: True if in check and has no legal moves.
        """
        return self.is_in_check() and len(self.legal_moves) == 0

    def is_draw(self) -> bool:
        """Checks if the game is a draw due to any standard draw condition.

        Includes stalemate, 75-move rule, fivefold repetition, or insufficient material.

        :return bool: True if the position is a draw.
        """
        return (
            self.is_stalemate()
            or self.is_75_move_rule()
            or self.is_fivefold_repetition()
            or self.is_insufficient_material()
        )

    def push(self, move: Move) -> bool:
        """Attempts to play a legal move, updating the board and history if successful.

        The move is only executed if the game is not over and the move is legal.
        Undo information is stored on a history stack.

        :param Move move: The move to be made.
        :return bool: True if the move was made, otherwise False.
        """
        if self.game_state != ACTIVE or not self.is_legal(move):
            return False

        # Apply the move and store undo information
        undo_info = self._make_move(move)
        self.history_stack.append(undo_info)

        return True

    def is_legal(self, move: Move) -> bool:
        """Checks if a move is legal for the current active player.

        :param Move move: The move to validate.
        :return bool: True if the move is legal, otherwise False.
        """
        return move in self.legal_moves

    def get_piece_at(self, uci_sq: str) -> tuple[Piece, Color] | None:
        """Returns the piece located at the given square, if any.

        :param str uci_sq: A square in UCI notation (e.g., "e2").
        :return tuple[Piece, Color] | None: The piece and color at the square, or None if empty.
        """
        bitpos = algebraic_to_bitpos(uci_sq)
        return self.piece_map.get(bitpos)

    def undo(self) -> None:
        """Reverts the last move played and restores the previous board state.

        If no moves have been made, the function does nothing.
        """
        if not self.history_stack:
            return  # Nothing to undo

        undo = self.history_stack.pop()

        # Restore game state fields
        self.active_color = undo.active_color
        self.castling_rights = undo.castling_rights
        self.en_passant_square = undo.en_passant_square
        self.halfmove_clock = undo.halfmove_clock
        self.fullmove_count = undo.fullmove_count
        self.zobrist_hash = undo.zobrist_hash
        self.game_state = undo.game_state

        from_sq, to_sq = undo.from_sq, undo.to_sq
        moved_type, color = undo.moved_piece
        new_type = undo.promotion_piece or moved_type

        # Revert castling rook movement if needed
        self._undo_castling(undo.moved_piece, to_sq)

        # Remove the promoted piece (if any) or regular piece from destination
        self.bitboards[color][new_type] &= not64(mask(to_sq))
        self.occupied[color] &= not64(mask(to_sq))
        self.piece_map.pop(to_sq)

        # Restore the moved piece to its original square
        self.bitboards[color][moved_type] |= mask(from_sq)
        self.occupied[color] |= mask(from_sq)
        self.piece_map[from_sq] = undo.moved_piece

        # Restore any captured piece
        if undo.captured_piece:
            cap_type, cap_color = undo.captured_piece
            self.bitboards[cap_color][cap_type] |= mask(undo.capture_sq)
            self.occupied[cap_color] |= mask(undo.capture_sq)
            self.piece_map[undo.capture_sq] = undo.captured_piece

        # Update repetition tracking
        self.unique_history[self.zobrist_hash] -= 1
        if self.unique_history[self.zobrist_hash] == 0:
            del self.unique_history[self.zobrist_hash]

        # Recalculate attack maps, pins, check mask, legal moves, etc.
        self._update_cache()

    def is_stalemate(self) -> bool:
        """Checks if the game is in stalemate (no legal moves and not in check).

        :return bool: True if stalemate, otherwise False.
        """
        return not self.is_in_check() and len(self.legal_moves) == 0

    def is_50_move_rule(self) -> bool:
        """Checks if the 50-move rule condition is met (draw claimable by player).

        :return bool: True if 50-move rule can be claimed.
        """
        return self.halfmove_clock >= 100

    def is_75_move_rule(self) -> bool:
        """Checks if the 75-move rule condition is met (auto draw enforced).

        :return bool: True if the 75-move rule auto-draw applies.
        """
        return self.halfmove_clock >= 150

    def is_threefold_repetition(self) -> bool:
        """Checks if the same board state has occurred three times (draw claimable).

        :return bool: True if threefold repetition can be claimed.
        """
        return self.unique_history.get(self.zobrist_hash, 0) >= 3

    def is_fivefold_repetition(self) -> bool:
        """Checks if the same board state has occurred five times (auto draw).

        :return bool: True if fivefold repetition auto-draw applies.
        """
        return self.unique_history.get(self.zobrist_hash, 0) >= 5

    def is_insufficient_material(self) -> bool:
        """Checks if neither player has sufficient material to checkmate.

        Returns True in cases like:
        - King vs King
        - King and bishop/knight vs King
        - King and bishop vs King and bishop (same-color bishops)

        :return bool: True if no checkmate is possible for either side.
        """
        pieces = [
            (ptype, color)
            for _, (ptype, color) in self.piece_map.items()
            if ptype != KING
        ]

        if not pieces:
            return True  # King vs King

        if len(pieces) == 1:
            return pieces[0][0] in {BISHOP, KNIGHT}

        if len(pieces) == 2:
            (p1, c1), (p2, c2) = pieces
            if p1 == p2 == BISHOP and c1 != c2:
                return self._same_color_square_bishops()

        return False

    def serialize(self) -> list[list[str]]:
        """Converts the board into a 2D list of string symbols representing each square.

        Uppercase letters are white pieces, lowercase are black.
        Empty squares are represented by empty strings.

        :return list[list[str]]: The 8x8 visual representation of the board.
        """
        board = [["" for _ in range(8)] for _ in range(8)]

        for square, (ptype, color) in self.piece_map.items():
            row = 7 - (square // 8)
            col = square % 8
            symbol = get_piece_symbol(ptype)
            board[row][col] = symbol.upper() if color == WHITE else symbol.lower()

        return board

    def get_fen_stats(self) -> tuple[str]:
        ac = get_color_symbol(self.active_color)
        cr = castling_rights_to_str(self.castling_rights)
        eps = (
            bitpos_to_algebraic(self.en_passant_square)
            if self.en_passant_square is not None
            else "-"
        )
        hc = str(self.halfmove_clock)
        fc = str(self.fullmove_count)

        return (
            ac,
            cr,
            eps,
            hc,
            fc,
        )

    def get_board_state(self) -> str:
        return {ACTIVE: "Active", CHECKMATE: "Checkmate", DRAW: "Draw"}[self.game_state]

    def _same_color_square_bishops(self) -> bool:
        """Checks if both bishops (one per side) are on the same color square.

            Used in insufficient material detection, where opposite-colored bishops
        can still lead to checkmate, but same-colored bishops cannot.

            :return bool: True if both bishops are on same-colored squares, else False.
        """
        bishops = [sq for sq, (ptype, _) in self.piece_map.items() if ptype == BISHOP]
        if len(bishops) != 2:
            return False

        # Square color is determined by (file + rank) % 2
        return (bishops[0] % 8 + bishops[0] // 8) % 2 == (
            bishops[1] % 8 + bishops[1] // 8
        ) % 2

    def _undo_castling(self, moved_piece: tuple[Piece, Color], to_sq: int) -> None:
        """Reverts a rook move if the previous move was a castling move.

        Called from `Board.undo()` to restore rook position during castling reversal.

        :param tuple[Piece, Color] moved_piece: The piece that moved last.
        :param int to_sq: The square the piece moved to.
        """
        moved_type, color = moved_piece

        if moved_type == KING:
            # Determine if castling occurred and identify rook movement
            if to_sq in {2, 6}:  # White castling (c1 or g1)
                rook_from, rook_to = (0, 3) if to_sq == 2 else (7, 5)
            elif to_sq in {58, 62}:  # Black castling (c8 or g8)
                rook_from, rook_to = (56, 59) if to_sq == 58 else (63, 61)
            else:
                rook_from, rook_to = None, None

            # If valid castling move and rook still present, move rook back
            if rook_from is not None and rook_to in self.piece_map:
                rook_piece = self.piece_map[rook_to]
                self.bitboards[color][ROOK] &= not64(mask(rook_to))
                self.bitboards[color][ROOK] |= mask(rook_from)
                self.piece_map.pop(rook_to)
                self.piece_map[rook_from] = rook_piece
                self.occupied[color] &= not64(mask(rook_to))
                self.occupied[color] |= mask(rook_from)

    def _make_move(self, move: Move) -> _UndoInfo:
        """Executes a move and updates all related board state, returning undo info.

        Handles capturing, promotions, castling, en passant, halfmove clock, and updates
        internal piece maps and bitboards. Used internally by `Board.push()`.

        :param Move move: The move being made.
        :return _UndoInfo: Data needed to reverse the move (pushed to history stack).
        """
        moved_piece = self.piece_map.get(move.from_sq)

        # Save pre-move state
        old_castling = self.castling_rights
        old_en_passant = self.en_passant_square
        capture_sq, captured_piece = self._get_captured_piece(move, moved_piece)
        undo_info = self._get_undo_info(move, moved_piece, captured_piece, capture_sq)

        # Handle captures, promotions, castling, en passant, etc.
        self._handle_capture(move, moved_piece)
        self._handle_pawn_double_push(move, moved_piece)
        rook_move = self._handle_castling(move, moved_piece)
        self._handle_halfmove_fullmove(moved_piece, captured_piece)

        # Update bitboards with the move (handling promotion if applicable)
        piece_type, color = moved_piece
        new_type = move.promotion or piece_type
        self.bitboards[color][piece_type] &= not64(mask(move.from_sq))
        self.bitboards[color][new_type] |= mask(move.to_sq)

        # Update piece map
        self.piece_map.pop(move.from_sq)
        self.piece_map[move.to_sq] = new_type, color

        # Update occupancy
        self.occupied[color] &= not64(mask(move.from_sq))
        self.occupied[color] |= mask(move.to_sq)

        # Finalize move state updates
        self._post_move_updates(
            move,
            moved_piece,
            captured_piece,
            capture_sq,
            old_castling,
            old_en_passant,
            rook_move,
        )

        return undo_info

    def _post_move_updates(
        self,
        move: Move,
        moved_piece: tuple[Piece, Color],
        captured_piece: tuple[Piece, Color] | None,
        capture_sq: int,
        old_castling: int,
        old_en_passant: int | None,
        rook_move: tuple[int, int] | None,
    ) -> None:
        """Performs all post-move bookkeeping and cache updates.

        Called at the end of `_make_move` to handle turn switching, Zobrist hashing,
        repetition tracking, game state updates, and move regeneration.

        :param Move move: The move that was just made.
        :param tuple[Piece, Color] moved_piece: The piece that moved.
        :param tuple[Piece, Color] | None captured_piece: The piece captured, if any.
        :param int capture_sq: The square the piece was captured on.
        :param int old_castling: The castling rights before the move.
        :param int | None old_en_passant: The en passant square before the move.
        :param tuple[int, int] | None rook_move: Rook move info if castling occurred.
        """
        # Switch active player
        self.active_color ^= 1

        # Update Zobrist hash with the move and previous state
        self._increment_zobrist(
            move,
            moved_piece,
            captured_piece,
            capture_sq,
            old_castling,
            old_en_passant,
            rook_move,
        )

        # Track position for repetition detection
        self.unique_history[self.zobrist_hash] += 1

        # Update game state (checkmate, draw, active, etc.)
        self._update_game_state()

        # Recalculate all move-related caches (attack maps, legal moves, pins, etc.)
        self._update_cache()

    def _handle_capture(self, move: Move, moved_piece: tuple[Piece, Color]) -> None:
        """Handles removal of a captured piece and updates board state accordingly.

        Also revokes castling rights if a rook is captured.

        :param Move move: The move being made.
        :param tuple[Piece, Color] moved_piece: The piece that is moving.
        """
        capture_sq, captured_piece = self._get_captured_piece(move, moved_piece)

        if captured_piece:
            cap_type, cap_color = captured_piece

            # Remove the captured piece from bitboards and map
            self.bitboards[cap_color][cap_type] &= not64(mask(capture_sq))
            self.piece_map.pop(capture_sq)
            self.occupied[cap_color] &= not64(mask(capture_sq))

            # Revoke castling rights if a rook was captured from its starting square
            if cap_type == ROOK:
                self._revoke_castling_rights(capture_sq, captured_piece)

    def _handle_pawn_double_push(
        self, move: Move, moved_piece: tuple[Piece, Color]
    ) -> None:
        """Handles setting en passant square for a two-square pawn push.

        :param Move move: The pawn move being made.
        :param tuple[Piece, Color] moved_piece: The piece that is moving.
        """
        piece_type, color = moved_piece
        direction = 16 if color == WHITE else -16

        # Check if the move is a double push from starting rank
        if piece_type != PAWN or move.to_sq != move.from_sq + direction:
            self.en_passant_square = None
            return

        # Set en passant square behind the pawn
        self.en_passant_square = move.from_sq + direction // 2

    def _handle_castling(
        self, move: Move, moved_piece: tuple[Piece, Color]
    ) -> tuple[int, int] | None:
        """Handles castling logic if the king performs a castle, and revokes castling rights if needed.

        Also updates bitboards, piece map, and occupied map to reflect rook movement.

        :param Move move: The move being made.
        :param tuple[Piece, Color] moved_piece: The piece that was moved.
        :return tuple[int, int] | None: The rook's (from_sq, to_sq) if castling occurred, else None.
        """
        piece_type, color = moved_piece
        rook_move = None

        if piece_type == KING:
            # Define corner and destination squares
            a1, h1, c1, d1, f1, g1 = 0, 7, 2, 3, 5, 6
            a8, h8, c8, d8, f8, g8 = 56, 63, 58, 59, 61, 62
            old_pos, new_pos, corner_rook = None, None, None

            # Detect and handle castling movement
            if color == WHITE:
                if move.to_sq == c1 and self.castling_rights & W_QUEENSIDE:
                    old_pos, new_pos, corner_rook = a1, d1, self.piece_map.get(a1)
                elif move.to_sq == g1 and self.castling_rights & W_KINGSIDE:
                    old_pos, new_pos, corner_rook = h1, f1, self.piece_map.get(h1)
            else:
                if move.to_sq == c8 and self.castling_rights & B_QUEENSIDE:
                    old_pos, new_pos, corner_rook = a8, d8, self.piece_map.get(a8)
                elif move.to_sq == g8 and self.castling_rights & B_KINGSIDE:
                    old_pos, new_pos, corner_rook = h8, f8, self.piece_map.get(h8)

            # Move the rook if castling occurred
            if corner_rook:
                rook_type, rook_color = corner_rook
                rook_move = old_pos, new_pos

                # Update rook's bitboard and occupancy
                self.bitboards[rook_color][rook_type] &= not64(mask(old_pos))
                self.bitboards[rook_color][rook_type] |= mask(new_pos)

                self.piece_map.pop(old_pos)
                self.piece_map[new_pos] = corner_rook

                self.occupied[rook_color] &= not64(mask(old_pos))
                self.occupied[rook_color] |= mask(new_pos)

        # Revoke castling rights if king or rook moves
        if piece_type in {KING, ROOK}:
            self._revoke_castling_rights(move.from_sq, moved_piece)

        return rook_move

    def _revoke_castling_rights(
        self, from_sq: int, moved_piece: tuple[Piece, Color]
    ) -> None:
        """Revokes castling rights if the king or rook moves from its starting square.

        Called when a king or rook moves or is captured, to update castling rights accordingly.

        :param int from_sq: The square index the piece moved from.
        :param tuple[Piece, Color] moved_piece: The piece being moved.
        """
        piece_type, color = moved_piece

        if color == WHITE:
            if piece_type == KING:
                self.castling_rights &= ~(W_KINGSIDE | W_QUEENSIDE)
            elif piece_type == ROOK:
                if from_sq == 0:  # a1 rook
                    self.castling_rights &= ~W_QUEENSIDE
                elif from_sq == 7:  # h1 rook
                    self.castling_rights &= ~W_KINGSIDE
        else:
            if piece_type == KING:
                self.castling_rights &= ~(B_KINGSIDE | B_QUEENSIDE)
            elif piece_type == ROOK:
                if from_sq == 56:  # a8 rook
                    self.castling_rights &= ~B_QUEENSIDE
                elif from_sq == 63:  # h8 rook
                    self.castling_rights &= ~B_KINGSIDE

    def _handle_halfmove_fullmove(
        self,
        moved_piece: tuple[Piece, Color],
        captured_piece: tuple[Piece, Color] | None,
    ) -> None:
        """Updates the halfmove clock and fullmove count after a move.

        The halfmove clock resets on pawn moves or captures.
        The fullmove count increases after Black's move.

        :param tuple[Piece, Color] moved_piece: The piece that was moved.
        :param tuple[Piece, Color] | None captured_piece: The piece that was captured, if any.
        """
        piece_type, color = moved_piece

        # Reset halfmove clock on pawn moves or captures
        if piece_type == PAWN or captured_piece:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        # Increment fullmove count only after Black's move
        if color == BLACK:
            self.fullmove_count += 1

    def _get_undo_info(
        self,
        move: Move,
        moved_piece: tuple[Piece, Color],
        captured_piece: tuple[Piece, Color] | None,
        capture_sq: int,
    ) -> _UndoInfo:
        """Constructs and returns all data required to undo a move.

        This is used to store the full game state before making a move,
        allowing accurate reversal via the undo stack.

        :param Move move: The move being made.
        :param tuple[Piece, Color] moved_piece: The piece that is moving.
        :param tuple[Piece, Color] | None captured_piece: The captured piece, if any.
        :param int capture_sq: The square where the capture occurred.
        :return _UndoInfo: A data container for reversing this move.
        """
        return _UndoInfo(
            from_sq=move.from_sq,
            to_sq=move.to_sq,
            moved_piece=moved_piece,
            captured_piece=captured_piece,
            capture_sq=capture_sq,
            promotion_piece=move.promotion,
            active_color=self.active_color,
            castling_rights=self.castling_rights,
            en_passant_square=self.en_passant_square,
            halfmove_clock=self.halfmove_clock,
            fullmove_count=self.fullmove_count,
            zobrist_hash=self.zobrist_hash,
            game_state=self.game_state,
        )

    def _get_captured_piece(
        self, move: Move, moved_piece: tuple[Piece, Color]
    ) -> tuple[int, tuple[Piece, Color] | None]:
        """Determines if a piece is captured by the given move, including en passant.

        :param Move move: The move being made.
        :param tuple[Piece, Color] moved_piece: The piece performing the move.
        :return tuple[int, tuple[Piece, Color] | None]: The square of the captured piece,
                and the piece itself if one was captured.
        """
        piece_type, color = moved_piece

        # Handle en passant capture
        if piece_type == PAWN and move.to_sq == self.en_passant_square:
            direction = -8 if color == WHITE else 8
            target_sq = move.to_sq + direction
            return target_sq, self.piece_map.get(target_sq)

        # Standard capture
        return move.to_sq, self.piece_map.get(move.to_sq)

    def _update_cache(self) -> None:
        """Regenerates all cached state related to move generation and checks.

        This includes:
        - Pinned pieces
        - Squares attacked by both players
        - Check mask for the current player
        - Pseudo-legal and legal move lists
        """
        self._build_pinned()
        self.attacked = self.attack_map_gen.get_all_maps()
        self._build_check_mask(self.active_color)
        self.pseudo_legal_moves = self.pseudo_move_gen.get_all_moves()
        self.legal_moves = self.legal_move_gen.get_all_moves()

    def _post_init(self) -> None:
        """Performs full post-initialization setup after setting bitboards or loading FEN.

        Reconstructs the piece map, zobrist hash, move history, and cached game state.
        """
        # Build piece map and initial hash
        self._build_piece_map()
        self._build_zobrist()

        # Reset history tracking
        self.history_stack.clear()
        self.unique_history.clear()
        self.unique_history[self.zobrist_hash] += 1

        # Update all caches and determine initial game state
        self._update_cache()
        self._update_game_state()

    def _build_occupied(self) -> None:
        """Builds `Board.occupied` bitboards for each color.

        Combines all individual piece-type bitboards into a single bitboard
        for each color to represent total occupancy.
        """
        self.occupied = [0, 0]
        for color in (BLACK, WHITE):
            for piece_type in range(6):
                self.occupied[color] |= self.bitboards[color][piece_type]

    def _build_piece_map(self) -> None:
        """Builds `Board.piece_map` from the current bitboards.

        Maps each occupied square to its (piece_type, color) pair.
        """
        self.piece_map.clear()
        for color in (BLACK, WHITE):
            for piece_type in range(6):
                targets = self.bitboards[color][piece_type]

                while targets:
                    sq, targets = pop_lsb(targets)
                    self.piece_map[sq] = piece_type, color

    def _build_zobrist(self) -> None:
        """Builds the initial `Board.zobrist_hash` from the current board state.

        Combines piece positions, side to move, castling rights, and en passant square
        into a unique 64-bit hash.
        """
        self.zobrist_hash = 0

        # Hash piece positions
        for square, (piece_type, color) in self.piece_map.items():
            self.zobrist_hash ^= ZOBRIST_PIECE[piece_type][color][square]

        # Hash side to move (only if Black)
        if self.active_color == BLACK:
            self.zobrist_hash ^= ZOBRIST_SIDE_TO_MOVE

        # Hash castling rights
        self.zobrist_hash ^= ZOBRIST_CASTLING[self.castling_rights]

        # Hash en passant file (only the file matters)
        if self.en_passant_square is not None:
            file = self.en_passant_square % 8
            self.zobrist_hash ^= ZOBRIST_EN_PASSANT[file]

    def _build_check_mask(self, color: Color) -> None:
        """Builds the `Board.check_mask` used to restrict legal moves during check.

        The check mask determines which squares non-king pieces are allowed to move to:
        - All squares if not in check
        - Only the king's square if double-checked
        - Squares that block or capture the checker if single-checked

        :param Color color: The color of the side currently being evaluated.
        """
        self.check_mask = 0
        enemy_color = opp_color(color)
        king_bb = self.bitboards[color][KING]
        checkers = []

        # Find all enemy pieces currently giving check
        for sq, (piece_type, piece_color) in self.piece_map.items():
            if piece_color != enemy_color:
                continue

            attacks = self.attack_map_gen.get_map(sq)
            if king_bb & attacks:
                checkers.append((piece_type, sq))

        # No check — allow all moves
        if len(checkers) == 0:
            self.check_mask = 0xFFFF_FFFF_FFFF_FFFF
            return

        # Double check — only king moves allowed
        if len(checkers) > 1:
            self.check_mask = king_bb
            return

        # Single check — allow capturing the checker or blocking the ray
        piece_type, checker_sq = checkers[0]
        self.check_mask = mask(checker_sq)

        # For sliding checkers, also allow blocking the check
        if piece_type in {ROOK, BISHOP, QUEEN}:
            self.check_mask |= ray_between(lsb(king_bb), checker_sq)

    def _build_pinned(self) -> None:
        """Builds `Board.pinned`, a bitboard for each color indicating pinned pieces.

        A piece is considered pinned if it lies between its own king and an enemy sliding piece
        (rook, bishop, or queen) and blocking that piece from checking the king.
        """
        self.pinned = [0, 0]
        all_occupied = self.occupied[WHITE] | self.occupied[BLACK]

        for color in (BLACK, WHITE):
            enemy_color = opp_color(color)
            king_bb = self.bitboards[color][KING]
            pinned_bb = 0

            for sq, (piece_type, piece_color) in self.piece_map.items():
                if piece_color != enemy_color:
                    continue
                if piece_type not in {ROOK, BISHOP, QUEEN}:
                    continue

                directions = DIRECTIONS_MAP[piece_type]
                for direction in directions:
                    ray = RAYS[direction][sq]

                    # Skip if the king is not along the ray
                    if not king_bb & ray:
                        continue

                    # Get all pieces between the sliding attacker and the king
                    between = ray_between(sq, lsb(king_bb))
                    blockers = between & all_occupied

                    # Exactly one piece between attacker and king
                    if blockers.bit_count() == 1:
                        blocker_sq = lsb(blockers)
                        blocker_color = self.piece_map.get(blocker_sq, (None, None))[1]

                        # If it's one of our pieces, it's pinned
                        if blocker_color == color:
                            pinned_bb |= blockers

            self.pinned[color] = pinned_bb

    def _increment_zobrist(
        self,
        move: Move,
        moved_piece: tuple[Piece, Color],
        captured_piece: tuple[Piece, Color] | None,
        capture_sq: int,
        old_castling: int,
        old_en_passant: int | None,
        rook_move: tuple[int, int] | None,
    ) -> None:
        """Updates the Zobrist hash to reflect the current board state after a move.

        This handles piece movement, captures, promotions, castling rights,
        en passant, and side-to-move flipping.

        :param Move move: The move that was played.
        :param tuple[Piece, Color] moved_piece: The piece that moved.
        :param tuple[Piece, Color] | None captured_piece: The piece that was captured, if any.
        :param int capture_sq: The square the capture occurred on.
        :param int old_castling: The castling rights before the move.
        :param int | None old_en_passant: The en passant square before the move.
        :param tuple[int, int] | None rook_move: The rook's from/to squares, if castling occurred.
        """
        piece_type, color = moved_piece
        new_type = move.promotion or piece_type

        # Flip side to move
        self.zobrist_hash ^= ZOBRIST_SIDE_TO_MOVE

        # Remove old en passant square
        if old_en_passant is not None:
            self.zobrist_hash ^= ZOBRIST_EN_PASSANT[old_en_passant % 8]

        # Handle moved piece (removal from origin, addition to destination)
        self.zobrist_hash ^= ZOBRIST_PIECE[piece_type][color][move.from_sq]
        self.zobrist_hash ^= ZOBRIST_PIECE[new_type][color][move.to_sq]

        # Handle captured piece
        if captured_piece:
            cap_type, cap_color = captured_piece
            self.zobrist_hash ^= ZOBRIST_PIECE[cap_type][cap_color][capture_sq]

        # Update castling rights if changed
        if self.castling_rights != old_castling:
            self.zobrist_hash ^= ZOBRIST_CASTLING[old_castling]
            self.zobrist_hash ^= ZOBRIST_CASTLING[self.castling_rights]

        # Add new en passant square
        if self.en_passant_square is not None:
            self.zobrist_hash ^= ZOBRIST_EN_PASSANT[self.en_passant_square % 8]

        # Update rook movement if castling occurred
        if rook_move is not None:
            rook_from, rook_to = rook_move
            self.zobrist_hash ^= ZOBRIST_PIECE[ROOK][color][rook_from]
            self.zobrist_hash ^= ZOBRIST_PIECE[ROOK][color][rook_to]

    def _update_game_state(self) -> None:
        """Updates `Board.game_state` to reflect the current status of the game.

        The game state can be:
        - CHECKMATE if the active player is in checkmate,
        - DRAW if the position meets any draw conditions,
        - ACTIVE otherwise.
        """
        self.game_state = (
            CHECKMATE if self.is_checkmate() else DRAW if self.is_draw() else ACTIVE
        )
