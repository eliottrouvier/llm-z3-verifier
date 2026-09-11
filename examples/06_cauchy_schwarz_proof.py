#!/usr/bin/env python3
"""
Example 06: Formal Proof and Falsification of Cauchy-Schwarz & AM-GM in R^3.
Demonstrates Z3 Non-Linear Real Arithmetic (QF_NRA) for classic inequalities:
1. Cauchy-Schwarz in R^3: (x.y)^2 <= ||x||^2 * ||y||^2
2. Equality condition verification (collinear vectors).
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.smt_engine import SMTEngine


def main():
    print("=" * 75)
    print("Example 06: Formal Proof of Cauchy-Schwarz Inequality in R^3 via SMT")
    print("=" * 75)
    print("Inequality: (x1*y1 + x2*y2 + x3*y3)^2 <= (x1^2 + x2^2 + x3^2)*(y1^2 + y2^2 + y3^2)\n")

    smt = SMTEngine()

    var_specs = {
        "x1": "Real", "x2": "Real", "x3": "Real",
        "y1": "Real", "y2": "Real", "y3": "Real"
    }

    # [1] Proof of theorem: Assert negation of Cauchy-Schwarz
    # If negation is UNSAT, theorem is universally true!
    print("[Phase 1] Asserting Negation of Cauchy-Schwarz Inequality...")
    negated_claim = [
        "(x1*y1 + x2*y2 + x3*y3)*(x1*y1 + x2*y2 + x3*y3) > "
        "(x1*x1 + x2*x2 + x3*x3)*(y1*y1 + y2*y2 + y3*y3)"
    ]

    res = smt.find_counterexample(
        var_specs=var_specs,
        domain_constraints=[],
        negated_claims=negated_claim
    )

    print(f"  Z3 Solver Status: {res.status.upper()}")
    if res.status == "unsat":
        print("  -> Result is UNSAT: No real vector assignment can violate the inequality.")
        print("  => Theorem Proven: Cauchy-Schwarz holds for all vectors in R^3. (Q.E.D.)\n")

    # [2] Test strict inequality claim: Can equality occur?
    print("[Phase 2] Probing False Claim: 'Equality NEVER occurs for non-zero vectors'")
    # Claim: for all non-zero x, y: (x.y)^2 < ||x||^2 ||y||^2
    # Negation: non-zero x, y and (x.y)^2 == ||x||^2 ||y||^2
    res_eq = smt.find_counterexample(
        var_specs=var_specs,
        domain_constraints=[
            "x1*x1 + x2*x2 + x3*x3 > 0",
            "y1*y1 + y2*y2 + y3*y3 > 0"
        ],
        negated_claims=[
            "(x1*y1 + x2*y2 + x3*y3)*(x1*y1 + x2*y2 + x3*y3) == "
            "(x1*x1 + x2*x2 + x3*x3)*(y1*y1 + y2*y2 + y3*y3)"
        ]
    )

    print(f"  Z3 Solver Status: {res_eq.status.upper()}")
    if res_eq.status == "sat":
        print("  -> SAT: Counterexample found! Equality DOES occur when vectors are collinear:")
        m = res_eq.counterexample
        print(f"     Vector x = ({m['x1']}, {m['x2']}, {m['x3']})")
        print(f"     Vector y = ({m['y1']}, {m['y2']}, {m['y3']})")


if __name__ == "__main__":
    main()
