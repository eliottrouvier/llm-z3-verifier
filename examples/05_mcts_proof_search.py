#!/usr/bin/env python3
"""
Example 05: Monte Carlo Tree Search (MCTS) with Symbolic PRM Guidance.
Demonstrates test-time compute search:
- MCTS explores reasoning paths.
- Symbolic PRM uses Z3 to assign exact formal rewards (+1.0 for valid, -1.0 for invalid).
- Unsound branches are hard-pruned, preventing compute waste.
- Renders and exports Mermaid flowchart visualization.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.backends import MockOfflineBackend
from src.prm_verifier import SymbolicPRM
from src.mcts_search import MCTSProofSearch
from src.visualizer import ProofTreeVisualizer


def main():
    print("=" * 75)
    print("Example 05: MCTS Proof Search with Symbolic PRM Guidance")
    print("=" * 75)
    print("Goal: Synthesize a sound deduction trajectory proving that:")
    print("      (x - y)*(x + y) == 0  ===>  (x == y) or (x == -y)\n")

    backend = MockOfflineBackend()
    prm = SymbolicPRM()
    searcher = MCTSProofSearch(backend=backend, prm=prm, c_puct=1.414)

    print("Running MCTS with 25 simulations...")
    result = searcher.search(
        initial_premises=["(x - y) * (x + y) == 0"],
        goal="(x == y) or (x == -y)",
        num_simulations=25
    )

    print(f"\n[MCTS Summary]")
    print(f"  * Total Nodes Generated : {result.total_nodes}")
    print(f"  * Nodes Hard-Pruned     : {result.nodes_pruned}")
    print(f"  * Goal Proven Formally  : {result.goal_proven}")
    print(f"  * Counterexamples Found : {len(result.counterexamples_found)}")

    print("\n[Optimal Sound Trajectory Discovered]")
    for i, step in enumerate(result.best_sound_trajectory):
        print(f"  Step {i+1} [ID {step.step_id}]: {step.text}")

    print("\n[Exporting Mermaid Visualization Diagram]")
    mermaid_diagram = ProofTreeVisualizer.render_mermaid_mcts(result)
    out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "proof_tree_mcts.mmd"))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(mermaid_diagram)
    print(f"  -> Diagram written to: {out_path}")
    print("\n" + mermaid_diagram + "\n")


if __name__ == "__main__":
    main()
