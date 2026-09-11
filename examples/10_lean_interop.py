#!/usr/bin/env python3
"""
Example 10: SMT to Lean 4 Formal Interoperability Bridge.
Demonstrates exporting SMT-verified theorems and step trajectories
into valid Lean 4 code compatible with Mathlib 4.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.lean_bridge import Lean4Bridge


def main():
    print("=" * 75)
    print("Example 10: SMT to Lean 4 Interactive Theorem Prover Bridge")
    print("=" * 75)

    # 1. Export algebraic factorization theorem
    print("\n[Case 1] Exporting Algebraic Factorization Theorem to Lean 4:")
    export_alg = Lean4Bridge.export_theorem(
        name="integer_difference_of_squares",
        variables={"x": "Int", "y": "Int"},
        hypotheses=["(x - y) * (x + y) == 0"],
        conclusion="x = y or x = -y",
        tactic="nlinarith"
    )
    print(export_alg.lean_code)

    # 2. Export Cauchy-Schwarz theorem
    print("\n" + "-" * 75)
    print("[Case 2] Exporting Cauchy-Schwarz in R^3 to Lean 4:")
    export_cs = Lean4Bridge.export_theorem(
        name="cauchy_schwarz_r3",
        variables={
            "x1": "Real", "x2": "Real", "x3": "Real",
            "y1": "Real", "y2": "Real", "y3": "Real"
        },
        hypotheses=[],
        conclusion="(x1*y1 + x2*y2 + x3*y3)^2 <= (x1^2 + x2^2 + x3^2) * (y1^2 + y2^2 + y3^2)",
        tactic="positivity"
    )
    print(export_cs.lean_code)


if __name__ == "__main__":
    main()
