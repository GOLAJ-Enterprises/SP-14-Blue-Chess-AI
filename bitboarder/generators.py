from __future__ import annotations
from typing import TYPE_CHECKING

from .move import Move
from .utils import opp_color, is_along_ray
from .bit_utils import not64, pop_lsb, mask, lsb, msb
from .consts import (
    PAWN_SINGLE_PUSH_MASKS,
    PAWN_DOUBLE_PUSH_MASKS,
    PAWN_ATK_MASKS,
    PAWN_PROMOTION_RANK,
    PAWN_START_RANK,
    DIRECTIONS_MAP,
    RAYS,
    POSITIVE_DIRECTIONS,
    KNIGHT_MASKS,
    KING_MASKS,
)
from .literals import (
    PAWN,
    ROOK,
    BISHOP,
    KNIGHT,
    QUEEN,
    KING,
    BLACK,
    WHITE,
    W_KINGSIDE,
    W_QUEENSIDE,
    B_KINGSIDE,
    B_QUEENSIDE,
)

if TYPE_CHECKING:
    from .bitboard import Board
    from .literals import Piece, Color


class AttackMapGenerator:
    """Generates bitboard-based attack maps for pieces on a given board."""

    def __init__(self, board: Board) -> None:
        self.board = board

    def get_map(self, bitpos: int) -> int:
        """Generates an attack bitmask for the piece at the given position.

        Looks up the piece at the given square and dispatches to the appropriate
        attack map generation method based on piece type.

        :param int bitpos: The square index (0–63) to generate attacks from.
        :return int: Bitmask of attacked squares, or 0 if no piece is present.
        """
        piece = self.board.piece_map.get(bitpos)
        if piece is None:
            return 0  # No piece on this square

        piece_type = piece[0]

        # Dispatch to the correct attack generation method based on piece type
        return {
            PAWN: self._gen_pawn_map,
            ROOK: self._gen_sliding_map,
            BISHOP: self._gen_sliding_map,
            KNIGHT: self._gen_knight_map,
            QUEEN: self._gen_sliding_map,
            KING: self._gen_king_map,
        }.get(piece_type, lambda *_: 0)(bitpos, piece)

    def get_all_maps(self) -> list[int]:
        """Generates combined attack bitmasks for both colors on the board.

        Iterates through all pieces and accumulates the attack maps for white and black
        separately.

        :return list[int]: A list of two bitmasks: [white_attacks, black_attacks].
        """
        attack_maps = [0, 0]  # Index 0 = white, Index 1 = black

        # Accumulate attack maps for each piece by color
        for bitpos, (_, color) in self.board.piece_map.items():
            attack_maps[color] |= self.get_map(bitpos)

        return attack_maps

    def _gen_pawn_map(self, bitpos: int, piece: tuple[Piece, Color]) -> int:
        _, color = piece
        return PAWN_ATK_MASKS[color][bitpos]

    def _gen_sliding_map(self, bitpos: int, piece: tuple[Piece, Color]) -> int:
        """Generates an attack bitmask for a sliding piece (rook, bishop, queen).

        Traverses each valid direction for the given piece from the current position.
        The ray in each direction is truncated if a blocking piece is encountered.

        :param int bitpos: The square the piece is on.
        :param tuple piece: A (PieceType, Color) tuple.
        :return int: Bitmask of attacked squares.
        """
        piece_type, _ = piece
        directions = DIRECTIONS_MAP[piece_type]
        all_occupied = self.board.occupied[BLACK] | self.board.occupied[WHITE]
        attack_map = 0

        # Traverse each allowed sliding direction
        for direction in directions:
            ray = RAYS[direction][bitpos]
            blockers = ray & all_occupied

            if not blockers:
                # No pieces in the ray; full ray is attackable
                attack_map |= ray
                continue

            # Truncate the ray at the closest blocker square
            blocker_sq = (
                lsb(blockers) if direction in POSITIVE_DIRECTIONS else msb(blockers)
            )
            attack_map |= (
                ray ^ RAYS[direction][blocker_sq]
            )  # Exclude squares beyond blocker

        return attack_map

    def _gen_knight_map(self, bitpos: int, *_) -> int:
        """Returns the precomputed attack mask for a knight at the given position.

        :param int bitpos: The square the knight is on.
        :return int: Bitmask of attacked squares.
        """
        return KNIGHT_MASKS[bitpos]

    def _gen_king_map(self, bitpos: int, *_) -> int:
        """Returns the precomputed attack mask for a king at the given position.

        :param int bitpos: The square the king is on.
        :return int: Bitmask of attacked squares.
        """
        return KING_MASKS[bitpos]


class PseudoLegalMoveGenerator:
    """Generates pseudo-legal moves for all pieces without checking king safety."""

    def __init__(self, board: Board) -> None:
        self.board = board

    def get_moves(self, bitpos: int) -> set[Move]:
        """Generates all pseudo-legal moves for the piece at the given position.

        Pseudo-legal moves are valid for the piece type and board position,
        but may leave the king in check. This method dispatches to the
        appropriate move generation function based on piece type.

        :param int bitpos: The position on the board (0–63).
        :return set[Move]: A set of pseudo-legal moves. Returns an empty set if no piece exists.
        """
        piece = self.board.piece_map.get(bitpos)
        if piece is None:
            return set()  # No piece at this square

        piece_type = piece[0]

        # Dispatch to piece-specific move generation method
        return {
            PAWN: self._gen_pawn_moves,
            ROOK: self._gen_sliding_moves,
            BISHOP: self._gen_sliding_moves,
            KNIGHT: self._gen_knight_moves,
            QUEEN: self._gen_sliding_moves,
            KING: self._gen_king_moves,
        }.get(piece_type, lambda *_: set())(bitpos, piece)

    def get_all_moves(self) -> list[set[Move]]:
        """Generates pseudo-legal moves for all pieces on the board.

        Iterates over all pieces and collects their pseudo-legal moves,
        separated by color.

        :return list[set[Move]]: A list of two sets: [white_moves, black_moves].
        """
        pseudo_moves = [set(), set()]  # Index 0 = white, Index 1 = black

        # Collect pseudo-legal moves for all pieces by color
        for bitpos, (_, color) in self.board.piece_map.items():
            pseudo_moves[color].update(self.get_moves(bitpos))

        return pseudo_moves

    # -- PAWN --
    def _gen_pawn_moves(self, bitpos: int, piece: tuple[Piece, Color]) -> set[Move]:
        """Generates pseudo-legal moves for a pawn at the given position.

        Includes forward pushes and diagonal captures, but does not check for
        king safety (i.e., legality).

        :param int bitpos: The square index of the pawn (0–63).
        :param tuple piece: A (PieceType, Color) tuple representing the pawn.
        :return set[Move]: A set of pseudo-legal moves for the pawn.
        """
        _, color = piece
        pseudo_legal_moves = set()

        # Add forward movement options
        self._add_pawn_push(pseudo_legal_moves, bitpos, color)

        # Add diagonal captures
        self._add_pawn_captures(pseudo_legal_moves, bitpos, color)

        return pseudo_legal_moves

    def _add_pawn_push(
        self, pseudo_moves: set[Move], bitpos: int, color: Color
    ) -> None:
        """Adds pseudo-legal forward pawn moves (single and double pushes).

        This helper is used during pawn move generation to handle non-capturing
        forward moves, including promotion and initial double pushes.

        :param set[Move] pseudo_moves: The set to add generated moves to.
        :param int bitpos: The position of the pawn (0–63).
        :param Color color: The color of the pawn.
        """
        all_occupied = self.board.occupied[BLACK] | self.board.occupied[WHITE]
        target_bb_single = PAWN_SINGLE_PUSH_MASKS[color][bitpos]

        # If the square in front is empty, the pawn can move
        if not target_bb_single & all_occupied:
            to_sq = lsb(target_bb_single)

            if mask(to_sq) & PAWN_PROMOTION_RANK[color]:
                # Add promotion moves
                self._add_pawn_promotion_moves(pseudo_moves, bitpos, to_sq)
            else:
                # Regular single push
                pseudo_moves.add(Move(bitpos, to_sq))

            # Check if double push is allowed (from starting rank)
            if mask(bitpos) & PAWN_START_RANK[color]:
                target_bb_double = PAWN_DOUBLE_PUSH_MASKS[color][bitpos]

                if not target_bb_double & all_occupied:
                    to_sq = lsb(target_bb_double)
                    pseudo_moves.add(Move(bitpos, to_sq))

    def _add_pawn_captures(
        self, pseudo_moves: set[Move], bitpos: int, color: Color
    ) -> None:
        """Adds pseudo-legal diagonal pawn captures, including en passant and promotions.

        This helper is used during pawn move generation to add all attacking moves,
        based on precomputed diagonal attack masks.

        :param set[Move] pseudo_moves: The set to add generated moves to.
        :param int bitpos: The position of the pawn (0–63).
        :param Color color: The color of the pawn.
        """
        enemy_occupied = self.board.occupied[opp_color(color)]
        target_bb_atk = PAWN_ATK_MASKS[color][bitpos]
        targets = target_bb_atk & enemy_occupied

        # Loop through each capturable square
        while targets:
            to_sq, targets = pop_lsb(targets)

            if mask(to_sq) & PAWN_PROMOTION_RANK[color]:
                # Capture that results in promotion
                self._add_pawn_promotion_moves(pseudo_moves, bitpos, to_sq)
            else:
                # Regular diagonal capture
                pseudo_moves.add(Move(bitpos, to_sq))

        # Explicitly check for en passant separately
        ep_sq = self.board.en_passant_square
        if ep_sq is not None and mask(ep_sq) & target_bb_atk:
            pseudo_moves.add(Move(bitpos, ep_sq))

    def _add_pawn_promotion_moves(
        self, pseudo_moves: set[Move], bitpos: int, to_sq: int
    ) -> None:
        """Adds all promotion options for a pawn reaching the final rank.

        This helper is used by both push and capture logic when a pawn reaches
        the promotion rank.

        :param set[Move] pseudo_moves: The set to add generated promotion moves to.
        :param int bitpos: The square the pawn is moving from.
        :param int to_sq: The square the pawn is moving to (on promotion rank).
        """
        for promo in (ROOK, BISHOP, KNIGHT, QUEEN):
            pseudo_moves.add(Move(bitpos, to_sq, promo))

    # -- QUEEN, BISHOP, ROOK --
    def _gen_sliding_moves(self, bitpos: int, piece: tuple[Piece, Color]) -> set[Move]:
        """Generates pseudo-legal sliding moves for rooks, bishops, and queens.

        This function generates all valid moves along the piece's allowed directions,
        stopping at the first occupied square. Moves that capture friendly pieces
        are excluded.

        :param int bitpos: The square the piece is on (0–63).
        :param tuple[Piece, Color] piece: A (PieceType, Color) tuple.
        :return set[Move]: The set of pseudo-legal moves for the piece.
        """
        piece_type, color = piece
        pseudo_legal_moves = set()
        all_occupied = self.board.occupied[BLACK] | self.board.occupied[WHITE]
        own_occupied = self.board.occupied[color]
        directions = DIRECTIONS_MAP[piece_type]

        # Check all sliding directions (horizontal, vertical, diagonal)
        for direction in directions:
            ray = RAYS[direction][bitpos]

            # Trim ray to exclude squares past the first blocker
            targets = self._trimmed_ray(ray, direction, all_occupied, own_occupied)

            # Convert each target square into a move
            while targets:
                to_sq, targets = pop_lsb(targets)
                pseudo_legal_moves.add(Move(bitpos, to_sq))

        return pseudo_legal_moves

    def _trimmed_ray(
        self, ray: int, direction: int, all_occupied: int, own_occupied: int
    ) -> int:
        """Trims a ray bitboard to exclude squares beyond the first blocker.

        Used for sliding move generation. Stops rays at the first occupied square
        and excludes any moves that would capture a friendly piece.

        :param int ray: The full directional ray bitboard.
        :param int direction: The direction of movement (used to determine blocker order).
        :param int all_occupied: Bitboard of all occupied squares.
        :param int own_occupied: Bitboard of squares occupied by friendly pieces.
        :return: The trimmed ray mask, excluding illegal moves.
        """
        blockers = ray & all_occupied
        if not blockers:
            return ray  # No blockers, full ray is valid

        # Find the first blocker depending on ray direction
        blocker_sq = (
            lsb(blockers) if direction in POSITIVE_DIRECTIONS else msb(blockers)
        )

        # Trim ray past the blocker and exclude friendly-occupied squares
        return (ray ^ RAYS[direction][blocker_sq]) & not64(own_occupied)

    # -- KNIGHT --
    def _gen_knight_moves(self, bitpos: int, piece: tuple[Piece, Color]) -> set[Move]:
        """Generates pseudo-legal knight moves from a given square.

        Knight moves are based on a precomputed mask and filtered to exclude
        friendly-occupied squares.

        :param int bitpos: The square the knight is on (0–63).
        :param tuple[Piece, Color] piece: A (PieceType, Color) tuple representing the knight.
        :return set[Move]: A set of pseudo-legal moves for the knight.
        """
        _, color = piece
        own_occupied = self.board.occupied[color]
        pseudo_legal_moves = set()

        # Exclude moves that would land on friendly pieces
        legal_mask = KNIGHT_MASKS[bitpos] & not64(own_occupied)

        # Convert each set bit into a move
        while legal_mask:
            to_sq, legal_mask = pop_lsb(legal_mask)
            pseudo_legal_moves.add(Move(bitpos, to_sq))

        return pseudo_legal_moves

    # -- KING --
    def _gen_king_moves(self, bitpos: int, piece: tuple[Piece, Color]) -> set[Move]:
        """Generates pseudo-legal king moves, including castling options.

        King moves are limited to one square in any direction, plus castling if available.
        This function excludes moves onto friendly-occupied squares.

        :param int bitpos: The square the king is on (0–63).
        :param tuple[Piece, Color] piece: A (PieceType, Color) tuple representing the king.
        :return set[Move]: A set of pseudo-legal moves for the king.
        """
        _, color = piece
        own_occupied = self.board.occupied[color]
        pseudo_legal_moves = set()

        # Add castling options if allowed
        self._add_castling_moves(pseudo_legal_moves, bitpos, color)

        # Filter out squares occupied by friendly pieces
        legal_mask = KING_MASKS[bitpos] & not64(own_occupied)

        # Convert each set bit into a move
        while legal_mask:
            to_sq, legal_mask = pop_lsb(legal_mask)
            pseudo_legal_moves.add(Move(bitpos, to_sq))

        return pseudo_legal_moves

    def _add_castling_moves(
        self, pseudo_moves: set[Move], bitpos: int, color: Color
    ) -> None:
        """Adds castling moves to the set of pseudo-legal king moves, if allowed.

        Validates that the king is not in check, and that the path between the
        king and rook is both unoccupied and not under attack.

        :param set[Move] pseudo_moves: The set to add castling moves to.
        :param int bitpos: The king's current square (should be e1/e8).
        :param Color color: The color of the king (WHITE or BLACK).
        """
        enemy_color = opp_color(color)
        enemy_attacks = self.board.attacked[enemy_color]
        all_occupied = self.board.occupied[BLACK] | self.board.occupied[WHITE]

        # King must not be in check to castle
        if not enemy_attacks & mask(bitpos):
            # Kingside castling (e1 → g1 or e8 → g8)
            if self._can_castle_kingside(color, all_occupied, enemy_attacks):
                pseudo_moves.add(Move(bitpos, 6 if color == WHITE else 62))

            # Queenside castling (e1 → c1 or e8 → c8)
            if self._can_castle_queenside(color, all_occupied, enemy_attacks):
                pseudo_moves.add(Move(bitpos, 2 if color == WHITE else 58))

    def _can_castle_kingside(
        self, color: Color, all_occupied: int, enemy_attacks: int
    ) -> bool:
        """Checks whether kingside castling is possible for the given color.

        Verifies that:
        - The castling right is still available.
        - The path between king and rook is unoccupied.
        - The path is not under enemy attack.

        :param Color color: The color attempting to castle.
        :param int all_occupied: Bitboard of all occupied squares.
        :param int enemy_attacks: Bitboard of all squares attacked by the opponent.
        :return bool: True if kingside castling is allowed, else False.
        """
        f1, g1, f8, g8 = 5, 6, 61, 62

        if color == WHITE:
            blockers_bb = mask(f1) | mask(g1)
            return (
                W_KINGSIDE & self.board.castling_rights
                and not all_occupied & blockers_bb
                and not enemy_attacks & blockers_bb
            )
        else:
            blockers_bb = mask(f8) | mask(g8)
            return (
                B_KINGSIDE & self.board.castling_rights
                and not all_occupied & blockers_bb
                and not enemy_attacks & blockers_bb
            )

    def _can_castle_queenside(
        self, color: Color, all_occupied: int, enemy_attacks: int
    ) -> bool:
        """Checks whether queenside castling is possible for the given color.

        Verifies that:
        - The castling right is still available.
        - The path between king and rook is unoccupied.
        - The squares the king must pass through are not under attack.

        :param Color color: The color attempting to castle.
        :param int all_occupied: Bitboard of all occupied squares.
        :param int enemy_attacks: Bitboard of all squares attacked by the opponent.
        :return bool: True if queenside castling is allowed, else False.
        """
        d1, c1, b1, d8, c8, b8 = 3, 2, 1, 59, 58, 57

        if color == WHITE:
            blockers_bb = mask(d1) | mask(c1) | mask(b1)
            king_path_bb = mask(d1) | mask(c1)
            return (
                W_QUEENSIDE & self.board.castling_rights
                and not all_occupied & blockers_bb
                and not enemy_attacks & king_path_bb
            )
        else:
            blockers_bb = mask(d8) | mask(c8) | mask(b8)
            king_path_bb = mask(d8) | mask(c8)
            return (
                B_QUEENSIDE & self.board.castling_rights
                and not all_occupied & blockers_bb
                and not enemy_attacks & king_path_bb
            )


class LegalMoveGenerator:
    """Filters pseudo-legal moves to produce fully legal moves that don't leave the king in check."""

    def __init__(self, board: Board) -> None:
        self.board = board

    def get_moves(self, bitpos: int) -> set[Move]:
        """Generates all legal moves for a piece, filtering pseudo-legal moves.

        Legal moves are pseudo-legal moves that do not leave the king in check
        and respect constraints such as pins and required responses to checks.

        :param int bitpos: The square of the piece to generate moves for (0–63).
        :return set[Move]: A set of fully legal moves from that square.
        """
        color = self.board.piece_map.get(bitpos, (None, None))[1]
        if color != self.board.active_color:
            return set()  # Not this player's turn

        king_bb = self.board.bitboards[color][KING]
        king_sq = lsb(king_bb)
        check_mask = self.board.check_mask
        pinned = self.board.pinned[color]

        pseudo_moves = self.board.pseudo_legal_moves[color]
        legal_moves = set()

        for move in pseudo_moves:
            if move.from_sq != bitpos:
                continue

            if bitpos == king_sq:
                # King move: destination must not be under attack
                # Temporarily apply king move

                if self._is_king_safe_after_move(move.from_sq, move.to_sq, color):
                    legal_moves.add(move)
            else:
                # Non-king move: must resolve check and respect pin constraints

                # If in check, move must hit check mask
                if not mask(move.to_sq) & check_mask:
                    continue

                # If piece is pinned, move must stay along ray between king and piece
                if mask(bitpos) & pinned:
                    if not is_along_ray(king_sq, bitpos, move.to_sq):
                        continue

                legal_moves.add(move)

        return legal_moves

    def get_all_moves(self) -> set[Move]:
        """Generates all legal moves for the current active player.

        Iterates over all of the player's pieces and aggregates their legal moves.

        :return set[Move]: A set of all fully legal moves available on the board.
        """
        legal_moves = set()

        # Collect legal moves from all pieces
        for bitpos in list(self.board.piece_map.keys()):
            legal_moves |= self.get_moves(bitpos)

        return legal_moves

    def _is_king_safe_after_move(self, from_sq: int, to_sq: int, color: Color) -> bool:
        """Simulates moving the king to a square and checks if it would be in check.

        Does NOT trigger legal move gen, history, or check recursion.
        Returns True if the move is safe (king not attacked after move).

        Args:
            from_sq (int): Location of king.
            to_sq (int): Where king is moving to.
            color (Color): Color of king.

        Returns:
            bool: True if king is not under attack after moving.
        """
        enemy_color = opp_color(color)

        # Temporarily make the move
        captured = self.board.piece_map.pop(to_sq, None)
        del self.board.piece_map[from_sq]
        self.board.piece_map[to_sq] = (KING, color)

        self.board.bitboards[color][KING] ^= mask(from_sq) | mask(to_sq)
        self.board.occupied[color] ^= mask(from_sq) | mask(to_sq)

        self.board.attacked = self.board.attack_map_gen.get_all_maps()
        is_safe = not (mask(to_sq) & self.board.attacked[enemy_color])

        # Undo the move
        self.board.bitboards[color][KING] ^= mask(from_sq) | mask(to_sq)
        self.board.occupied[color] ^= mask(from_sq) | mask(to_sq)
        del self.board.piece_map[to_sq]
        self.board.piece_map[from_sq] = (KING, color)
        if captured:
            self.board.piece_map[to_sq] = captured

        self.board.attacked = self.board.attack_map_gen.get_all_maps()

        return is_safe
