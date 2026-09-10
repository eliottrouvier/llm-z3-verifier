"""Unit tests for NeurosymbolicTreeSearch."""

from src.backends import MockOfflineBackend
from src.tree_search import NeurosymbolicTreeSearch
from src.verifier import ProofVerifier


def test_tree_search_backtracking_and_pruning():
    backend = MockOfflineBackend()
    verifier = ProofVerifier()
    searcher = NeurosymbolicTreeSearch(backend=backend, verifier=verifier)

    result = searcher.search(
        initial_premises=["(x - y) * (x + y) == 0"],
        goal="(x == y) or (x == -y)"
    )

    assert result.success
    assert result.total_nodes_explored > 1
    assert result.nodes_pruned >= 1
    assert len(result.pruned_steps) >= 1

    # Verify that the pruned step was indeed unsound
    bad_step = result.pruned_steps[0]
    assert bad_step.status == "UNSOUND"
    assert bad_step.counterexample is not None

    # Verify that the final sound path consists only of sound steps
    for step in result.sound_path:
        assert step.status == "SOUND"
