"""Unit tests for MCTSProofSearch."""

import pytest
from src.backends import MockOfflineBackend
from src.prm_verifier import SymbolicPRM
from src.mcts_search import MCTSProofSearch


def test_mcts_proof_search_execution():
    backend = MockOfflineBackend()
    prm = SymbolicPRM()
    searcher = MCTSProofSearch(backend=backend, prm=prm, c_puct=1.414, max_depth=4)

    res = searcher.search(
        initial_premises=["(x - y) * (x + y) == 0"],
        goal="(x == y) or (x == -y)",
        num_simulations=15
    )

    assert res.total_nodes >= 3
    assert res.nodes_pruned >= 1  # Successfully pruned flawed division-by-zero branch
    assert len(res.best_sound_trajectory) >= 2
    assert res.goal_proven is True


def test_mcts_node_pruning_value():
    backend = MockOfflineBackend()
    prm = SymbolicPRM()
    searcher = MCTSProofSearch(backend=backend, prm=prm)

    res = searcher.search(
        initial_premises=["(x - y) * (x + y) == 0"],
        goal="(x == y) or (x == -y)",
        num_simulations=5
    )

    # Ensure counterexample was captured
    assert len(res.counterexamples_found) >= 1
    assert "x" in res.counterexamples_found[0]
