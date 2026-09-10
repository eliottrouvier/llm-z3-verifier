#!/usr/bin/env python3
"""
Example 01: Counterexample Search on Discrete & Algebraic Conjectures.
Demonstrates how open-weight LLM formalization coupled with Z3 SMT solver
disproves false mathematical conjectures by automatically synthesizing models.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.backends import MockOfflineBackend
from src.smt_engine import SMTEngine


def main():
    print("----------------------------------------------------------------------")
    print("Example 1: Counterexample Synthesis on Discrete Structures")
    print("----------------------------------------------------------------------")

    backend = MockOfflineBackend()
    smt_engine = SMTEngine()

    conjectures = [
        (
            "Matrix Zero Divisors",
            "For all 2x2 integer matrices A and B, if A*B = 0, then A = 0 or B = 0.",
            "matrix_zero_divisors"
        ),
        (
            "Graph Chromatic Lower Bound",
            "Every finite graph with minimum degree delta >= 3 requires at least 4 colors.",
            "graph_bipartite_degree"
        )
    ]

    for title, text, query_key in conjectures:
        print(f"\nEvaluating Conjecture: [{title}]")
        print(f"  Statement: \"{text}\"")

        spec = backend.formalize_conjecture(query_key)
        print(f"  -> Formalized to Z3 variables: {list(spec['variables'].keys())}")
        print(f"  -> Asserting negation of theorem to search for counterexample model...")

        result = smt_engine.find_counterexample(
            var_specs=spec["variables"],
            domain_constraints=spec["domain_constraints"],
            negated_claims=spec["negated_formula"]
        )

        if result.status == "sat":
            print("  [DISPROVED] Z3 synthesized an exact counterexample!")
            print(f"  Countermodel: {result.counterexample}")
        elif result.status == "unsat":
            print("  [VERIFIED] Z3 proved UNSAT on negation -> Theorem holds in domain.")
        else:
            print(f"  [UNKNOWN] Reason: {result.reason_unknown}")


if __name__ == "__main__":
    main()
