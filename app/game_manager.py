import uuid

from chess import Board


class Game:
    def __init__(self, player1_id: str, player2_id: str, fen: str = None) -> None:
        self.board = Board(fen)
        self.player1_id = player1_id
        self.player2_id = player2_id


class GameManager:
    def __init__(self) -> None:
        self.games: dict[str, Game] = {}  # game_id: Game

    def create_game(
        self, player1_id: str = None, player2_id: str = None, fen: str = None
    ) -> str:
        game_id = str(uuid.uuid4())
        self.games[game_id] = Game(player1_id, player2_id)
        return game_id

    def get_game(self, game_id: str) -> Game | None:
        return self.games.get(game_id)

    def remove_game(self, game_id: str) -> bool:
        if game_id in self.games:
            del self.games[game_id]
            return True

        return False
