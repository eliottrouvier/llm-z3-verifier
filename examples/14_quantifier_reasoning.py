#!/usr/bin/env python3
"""
Example 14: Quantifier Reasoning & Model-Based Quantifier Instantiation (MBQI).
Demonstrates:
1. Universal additive inverse proof: ForAll x, Exists y: x + y == 0.
2. Disproving the Quantifier Swapping Fallacy: Exists y, ForAll x: x + y == 0.
3. Transitivity of integer divisibility with existential witness synthesis.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.quantifiers import QuantifierEngine


def main():
    print("=" * 75)
    print("Example 14: Quantifier Reasoning via Z3 MBQI")
    print("=" * 75)

    qe = QuantifierEngine()

    print("[Test 1] Universal Additive Inverse over Reals:")
    print("  Claim: ∀x ∈ ℝ, ∃y ∈ ℝ, x + y = 0")
    r1 = qe.verify_additive_inverse_valid()
    print(f"  Valid?  {r1.is_valid} (Status: {r1.status})")
    print(f"  Result: {r1.explanation}\n")

    print("[Test 2] Quantifier Swapping Fallacy Audit:")
    print("  Claim: ∃y ∈ ℝ, ∀x ∈ ℝ, x + y = 0 (Universal Constant Inverter)")
    r2 = qe.disprove_quantifier_swap_fallacy()
    print(f"  Valid?  {r2.is_valid} (Status: {r2.status})")
    print(f"  Result: {r2.explanation}\n")

    print("[Test 3] Transitivity of Integer Divisibility:")
    print("  Claim: If a | b and b | c, then a | c (with existential multiplier)")
    r3 = qe.verify_divisibility_transitivity()
    print(f"  Valid?  {r3.is_valid} (Status: {r3.status})")
    print(f"  Result: {r3.explanation}\n")

    print("=" * 75)
    print("First-order quantified statements formally audited with zero manual hints.")
    print("=" * 75)


if __name__ == "__main__":
    main()
