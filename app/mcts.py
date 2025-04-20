from __future__ import annotations
import math
import json
import random
import torch
import torch.nn.functional as F
from pathlib import Path
from typing import Optional, Tuple, List, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from bitboarder import Board

# Load move index mapping
BASE_DIR = Path(__file__).resolve().parent.parent
MOVE_INDEX_PATH = BASE_DIR / "app" / "data" / "move_index_dict.json"

with MOVE_INDEX_PATH.open("r") as f:
    move_index_dict: Dict[str, int] = json.load(f)


class Node:
    """A node in the Monte Carlo Tree.

    Attributes:
        board: Board position at this node.
        parent: Parent Node or None if root.
        children: Dict mapping UCI string to child Node.
        prior: Prior probability for selecting this node.
        visit_count, total_value, mean_value tracked by backprop.
    """

    def __init__(
        self, board: Board, parent: Optional[Node] = None, prior: float = 0.0
    ) -> None:
        """Initializes a search node.

        :param board: Current board state
        :param parent: Parent node in the tree
        :param prior: Prior probability from the policy network
        """
        self.board = board
        self.parent = parent
        self.children: Dict[str, Node] = {}
        self.prior = prior
        self.visit_count = 0
        self.total_value = 0.0
        self.mean_value = 0.0

    def is_leaf(self) -> bool:
        """Checks if node is a leaf (has no children)."""
        return len(self.children) == 0

    def is_terminal(self) -> bool:
        """Checks if node is terminal (game is over)."""
        return self.board.is_game_over()


class MonteCarloTreeSearch:
    """Performs MCTS guided by a policy-value neural network."""

    def __init__(
        self, model: torch.nn.Module, device: torch.device, cpuct: float = 1.25
    ) -> None:
        """Initializes MCTS with model and configuration.

        :param model: TorchScript model that outputs policy logits and value
        :param device: Device to run the model on
        :param cpuct: C_PUCT exploration constant
        """
        self.model = model
        self.device = device
        self.cpuct = cpuct

    def search(self, root_board: Board, num_visits: int = 50) -> Optional[str]:
        """Performs MCTS search starting from root board.

        :param root_board: The board to search from
        :param num_visits: Number of simulations to run
        :return: The UCI string of the move with the highest visit count, or None if the root position is terminal.
        """
        root_node = Node(root_board)
        if root_node.is_terminal():
            # No move to select from a terminal position
            return None

        self.expand(root_node)

        for _ in range(num_visits):
            node, path = self.select(root_node)
            if node.is_terminal():
                value = self.evaluate_terminal(node)
            else:
                value = self.expand(node)
            self.backprop(path, value)

        # pick move(s) with highest visit count, break ties randomly
        max_visits = max(child.visit_count for child in root_node.children.values())
        best_moves = [
            uci
            for uci, child in root_node.children.items()
            if child.visit_count == max_visits
        ]
        return random.choice(best_moves)

    def select(self, node: Node) -> Tuple[Node, List[Node]]:
        """Traverses tree to find leaf node with highest UCB.

        :param node: Starting node
        :return: Leaf node and path from root to that node
        """
        path = [node]

        while not node.is_leaf() and not node.is_terminal():
            total_visits = sum(c.visit_count for c in node.children.values()) or 1
            best_score = float("-inf")
            best_child = None

            for child in node.children.values():
                ucb = child.mean_value + self.cpuct * child.prior * math.sqrt(
                    total_visits
                ) / (1 + child.visit_count)
                if ucb > best_score:
                    best_score = ucb
                    best_child = child

            node = best_child
            path.append(node)

        return node, path

    def expand(self, node: Node) -> float:
        """Expands a leaf node using the model to initialize children.

        :param node: The node to expand
        :raises RuntimeError: If no moves in the policy mapping for a non-terminal node
        :return: The value prediction from the model
        """
        board_tensor = node.board.to_tensor().unsqueeze(0).to(self.device)

        with torch.no_grad():
            policy_logits, value = self.model(board_tensor)
            # keep probabilities on-device to avoid costly CPU/GPU sync
            policy_probs = F.softmax(policy_logits[0], dim=0)
            value = value.item()

        legal_moves = list(node.board.legal_moves)
        num_moves = len(legal_moves)
        if num_moves == 0:
            return value

        # Gather mapping indices
        indices = [move_index_dict.get(m.to_uci()) for m in legal_moves]

        # If the mapping misses *all* legal moves, that's an error
        if all(idx is None for idx in indices) and not node.is_terminal():
            raise RuntimeError(
                f"No moves in policy mapping for non-terminal position: {node.board}"
            )

        # For any unmapped moves, fall back to uniform weight
        uniform = 1.0 / num_moves
        raw_priors: List[float] = []
        for idx in indices:
            if idx is not None:
                raw_priors.append(policy_probs[idx].item())
            else:
                raw_priors.append(uniform)

        # Normalize so priors sum to 1
        total_raw = sum(raw_priors)
        normalized = [raw / total_raw for raw in raw_priors]

        # Create children keyed by UCI string
        for move, prior in zip(legal_moves, normalized):
            child = node.board.copy()
            child.push(move)
            node.children[move.to_uci()] = Node(child, parent=node, prior=prior)

        return value

    def backprop(self, path: List[Node], value: float) -> None:
        """Propagates the evaluation value up the tree.

        :param path: List of nodes from leaf to root
        :param value: Evaluation value to backpropagate
        """
        for n in reversed(path):
            n.visit_count += 1
            n.total_value += value
            n.mean_value = n.total_value / n.visit_count
            value = -value  # switch perspective

    def evaluate_terminal(self, node: Node) -> float:
        """Returns a value for terminal states.

        :param node: Node to evaluate
        :raises ValueError: If node is not terminal
        :return: -1 if loss, 0 if draw
        """
        board = node.board
        if board.is_checkmate():
            return -1.0
        if board.is_draw():
            return 0.0
        raise ValueError("evaluate_terminal called on non-terminal node.")
