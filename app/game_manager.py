import uuid
import threading

from bitboarder import Board
from app.ai import ChessCNN


class Game:
    def __init__(
        self, ai_game: bool, player1_id: str, player2_id: str, fen: str
    ) -> None:
        self.board = Board(fen)
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.ai = ChessCNN(self.board, temperature=0.0) if ai_game else None


class GameManager:
    def __init__(self) -> None:
        self.games: dict[str, Game] = {}  # game_id: Game
        self._lock = threading.Lock()

    def create_game(
        self,
        ai_game: bool = False,
        player1_id: str | None = None,
        player2_id: str | None = None,
        fen: str = "",
    ) -> str:
        game_id = str(uuid.uuid4())
        game = Game(ai_game, player1_id, player2_id if not ai_game else "AI", fen)

        with self._lock:
            self.games[game_id] = game

        return game_id

    def get_game(self, game_id: str) -> Game | None:
        with self._lock:
            return self.games.get(game_id)

    def remove_game(self, game_id: str) -> bool:
        with self._lock:
            if game_id in self.games:
                del self.games[game_id]
                return True

            return False
