from __future__ import annotations
from typing import TYPE_CHECKING, Dict
import torch
import json

from .rp import resource_path
from .mcts import MonteCarloTreeSearch

if TYPE_CHECKING:
    from bitboarder import Board


class ChessCNN:
    """Neural network wrapper with optional MCTS for move prediction."""

    _model: torch.jit.ScriptModule = None
    _move_index_dict: Dict[str, int] = None
    _index_to_move: Dict[str, str] = None

    def __init__(self, board: Board, device: str = "cpu") -> None:
        """Initializes the ChessCNN model and loads model/data files if not already loaded."""
        self.board = board
        self.device = torch.device(device)

        if ChessCNN._model is None:
            model_path = resource_path(
                "neural_net/model/best_model_acc0.4378_param1.89m.pt"
            )
            move_dict_path = resource_path("app/data/move_index_dict.json")
            index_to_move_path = resource_path("app/data/index_to_move.json")

            ChessCNN._model = torch.jit.load(model_path).to(self.device)
            ChessCNN._model.eval()

            with move_dict_path.open("r") as f:
                ChessCNN._move_index_dict = json.load(f)

            with index_to_move_path.open("r") as f:
                ChessCNN._index_to_move = json.load(f)

        self.model = ChessCNN._model
        self.move_index_dict = ChessCNN._move_index_dict
        self.index_to_move = ChessCNN._index_to_move

    def predict(self, use_mcts: bool = True, visits: int = 50) -> str:
        """Predicts the best move using either MCTS or direct inference."""
        if use_mcts:
            mcts = MonteCarloTreeSearch(self.model, self.device)
            move_uci = mcts.search(self.board, num_visits=visits)
            if move_uci is None:
                raise RuntimeError("MCTS returned no move: board appears terminal.")
            return move_uci

        board_tensor = self.board.to_tensor().unsqueeze(0).to(self.device)

        with torch.no_grad():
            policy_logits, _ = self.model(board_tensor)
            policy_logits = policy_logits[0]  # shape: [N]

        legal_uci = [move.to_uci() for move in self.board.legal_moves]
        legal_indices = [
            self.move_index_dict[uci]
            for uci in legal_uci
            if uci in self.move_index_dict
        ]

        if not legal_indices:
            raise RuntimeError("No legal moves found in move index dictionary.")

        masked = torch.full_like(policy_logits, float("-inf"))
        masked[legal_indices] = policy_logits[legal_indices]

        best_index = torch.argmax(masked).item()
        uci = self.index_to_move[best_index]
        return uci
