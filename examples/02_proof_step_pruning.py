#!/usr/bin/env python3
"""
Example 02: Step-Level Proof Verification and Neurosymbolic Tree Search Pruning.
Demonstrates the process-supervision loop:
1. LLM proposes a candidate deduction step.
2. Z3 checks if premises => conclusion is sound.
3. When an invalid step is detected, Z3 synthesizes a counterexample disproving the step.
4. The search engine prunes the invalid branch and backtracks to explore a sound derivation.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.backends import MockOfflineBackend
from src.verifier import ProofStep, ProofVerifier
from src.tree_search import NeurosymbolicTreeSearch


def main():
    print("----------------------------------------------------------------------")
    print("Example 2: Proof-Step Verification & Branch Pruning via Z3")
    print("----------------------------------------------------------------------")

    backend = MockOfflineBackend()
    verifier = ProofVerifier()

    print("Goal: Prove that if (x - y)*(x + y) = 0 over integers, then x = y or x = -y.\n")

    # 1. Direct step audit demonstration
    print("[1] Auditing a Deliberately Flawed Deduction Step:")
    unsound_step = ProofStep(
        step_id=1,
        text="Divide both sides by (x - y) to obtain x + y = 0.",
        variables={"x": "Int", "y": "Int"},
        hypotheses=["(x - y) * (x + y) == 0"],
        conclusion="x + y == 0"  # Invalid! What if x == y != 0?
    )
    verified = verifier.verify_step(unsound_step)
    print(f"  Step Text: \"{verified.text}\"")
    print(f"  Audit Status: {verified.status}")
    print(f"  Counterexample Model Synthesized by Z3: {verified.counterexample}")
    print("  -> Explanation: When x=y (e.g. x=1, y=1), (x-y)(x+y)=0 holds, but x+y=2 != 0.")
    print("  -> Conclusion: Division by zero fallacy detected. Deduction pruned!\n")

    # 2. Complete Tree Search Trajectory
    print("[2] Executing Full Neurosymbolic Tree Search with Backtracking:")
    searcher = NeurosymbolicTreeSearch(backend=backend, verifier=verifier)
    result = searcher.search(
        initial_premises=["(x - y) * (x + y) == 0"],
        goal="(x == y) or (x == -y)"
    )

    print(f"\nSearch Summary: Explored {result.total_nodes_explored} nodes, pruned {result.nodes_pruned} branch(es).")
    print("\nVerified Sound Proof Trajectory:")
    for step in result.sound_path:
        print(f"  [Step {step.step_id}] {step.text}")


if __name__ == "__main__":
    main()
