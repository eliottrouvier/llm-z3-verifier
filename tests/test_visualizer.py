"""Unit tests for ProofTreeVisualizer."""

import os
import pytest
from src.backends import MockOfflineBackend
from src.tree_search import NeurosymbolicTreeSearch
from src.visualizer import ProofTreeVisualizer


def test_render_mermaid_tree_search():
    backend = MockOfflineBackend()
    searcher = NeurosymbolicTreeSearch(backend=backend)
    res = searcher.search(
        initial_premises=["(x - y) * (x + y) == 0"],
        goal="(x == y) or (x == -y)"
    )

    mermaid_code = ProofTreeVisualizer.render_mermaid_tree_search(res)
    assert "```mermaid" in mermaid_code
    assert "flowchart TD" in mermaid_code
    assert "Q.E.D." in mermaid_code
    assert "PRUNED" in mermaid_code


def test_export_json_trace(tmp_path):
    backend = MockOfflineBackend()
    searcher = NeurosymbolicTreeSearch(backend=backend)
    res = searcher.search(
        initial_premises=["(x - y) * (x + y) == 0"],
        goal="(x == y) or (x == -y)"
    )

    json_file = os.path.join(tmp_path, "trace.json")
    ProofTreeVisualizer.export_json(res, json_file)

    assert os.path.exists(json_file)
    assert os.path.getsize(json_file) > 100
