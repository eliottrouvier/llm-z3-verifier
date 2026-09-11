"""
Quantifier Reasoning Engine (First-Order Logic with E-Matching & MBQI).

Formally models and checks quantified mathematical claims:
1. Universal (ForAll) and Existential (Exists) quantifiers over Int and Real sorts.
2. Automated detection of Quantifier Alternation Fallacies (e.g. ForAll-Exists vs Exists-ForAll).
3. Model-Based Quantifier Instantiation (MBQI) configuration for decidable fragments.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import z3


@dataclass
class QuantifierResult:
    claim_name: str
    is_valid: bool
    status: str  # "sat", "unsat", "unknown"
    counterexample: Optional[Dict[str, Any]] = None
    explanation: str = ""


class QuantifierEngine:
    """Solves quantified first-order constraints using Z3 MBQI."""

    def __init__(self, timeout_ms: int = 5000):
        self.timeout_ms = timeout_ms

    def verify_additive_inverse_valid(self) -> QuantifierResult:
        """
        Formally verifies: ForAll x in Real, Exists y in Real, x + y == 0.
        To prove valid: check if negation is UNSAT.
        Negation: Exists x in Real, ForAll y in Real, x + y != 0.
        """
        ctx = z3.Context()
        solver = z3.Solver(ctx=ctx)
        solver.set("timeout", self.timeout_ms)
        solver.set("smt.mbqi", True)

        x = z3.Real("x", ctx=ctx)
        y = z3.Real("y", ctx=ctx)

        # Inner: ForAll y, x + y != 0
        inner = z3.ForAll([y], x + y != 0)
        solver.add(inner)

        res = solver.check()
        if res == z3.unsat:
            return QuantifierResult(
                claim_name="Additive Inverse (ForAll x, Exists y: x + y == 0)",
                is_valid=True,
                status="unsat",
                explanation="Formally certified: For every real x, an additive inverse y = -x exists."
            )
        else:
            return QuantifierResult(
                claim_name="Additive Inverse",
                is_valid=False,
                status=str(res),
                explanation="Unexpected countermodel."
            )

    def disprove_quantifier_swap_fallacy(self) -> QuantifierResult:
        """
        Tests the quantifier swap fallacy:
        Claim: Exists y in Real, ForAll x in Real, x + y == 0.
        (A universal constant y that inverts ALL x simultaneously).
        This claim is mathematically FALSE.
        Checking if the claim is satisfiable in Z3:
        """
        ctx = z3.Context()
        solver = z3.Solver(ctx=ctx)
        solver.set("timeout", self.timeout_ms)
        solver.set("smt.mbqi", True)

        x = z3.Real("x", ctx=ctx)
        y = z3.Real("y", ctx=ctx)

        # Claim: Exists y, ForAll x, x + y == 0
        claim = z3.ForAll([x], x + y == 0)
        solver.add(claim)

        res = solver.check()
        if res == z3.unsat:
            return QuantifierResult(
                claim_name="Quantifier Swap Fallacy (Exists y, ForAll x: x + y == 0)",
                is_valid=False,
                status="unsat",
                explanation=(
                    "Quantifier swap disproved: No single constant y can invert all real numbers x simultaneously. "
                    "Z3 proves the claim is UNSATISFIABLE."
                )
            )
        else:
            return QuantifierResult(
                claim_name="Quantifier Swap Fallacy",
                is_valid=True,
                status="sat",
                explanation="Counter-intuitive SAT model."
            )

    def verify_divisibility_transitivity(self) -> QuantifierResult:
        """
        Formally verifies divisibility transitivity over integers:
        If a | b and b | c, then a | c (with non-zero multipliers).
        """
        ctx = z3.Context()
        solver = z3.Solver(ctx=ctx)
        solver.set("timeout", self.timeout_ms)

        a = z3.Int("a", ctx=ctx)
        b = z3.Int("b", ctx=ctx)
        c = z3.Int("c", ctx=ctx)
        k1 = z3.Int("k1", ctx=ctx)
        k2 = z3.Int("k2", ctx=ctx)

        # b = k1 * a, c = k2 * b  ==> c = (k1 * k2) * a
        solver.add(b == k1 * a)
        solver.add(c == k2 * b)
        # Negation of conclusion: ForAll k3, c != k3 * a
        k3 = z3.Int("k3", ctx=ctx)
        solver.add(z3.ForAll([k3], c != k3 * a))

        res = solver.check()
        if res == z3.unsat:
            return QuantifierResult(
                claim_name="Integer Divisibility Transitivity (a|b and b|c => a|c)",
                is_valid=True,
                status="unsat",
                explanation="Formally proven via MBQI: Divisibility is transitive over integers with k3 = k1 * k2."
            )
        else:
            return QuantifierResult(
                claim_name="Integer Divisibility Transitivity",
                is_valid=False,
                status=str(res),
                explanation="Disproved."
            )
