#!/usr/bin/env python3
"""
Example 09: Inductive Invariant Verification & Counterexample to Induction (CTI).
Demonstrates:
1. Transition system: x_0 = 0, y_0 = 0; Step: x' = x + 1, y' = y + 2.
2. Target safety goal: 2*x == y.
3. Auditing weak invariant (x >= 0 and y >= 0): Z3 rejects with counterexample to safety.
4. Auditing exact invariant (2*x == y): Z3 formally proves initiation, consecution, and safety!
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.lemma_synthesis import InvariantVerifier


def main():
    print("=" * 75)
    print("Example 09: Automated Inductive Invariant Verification via Z3")
    print("=" * 75)
    print("Transition System:")
    print("  Init: x = 0, y = 0")
    print("  Trans: x' = x + 1, y' = y + 2")
    print("  Target Safety Property: 2*x == y\n")

    verifier = InvariantVerifier()

    variables = {"x": "Int", "y": "Int"}
    prime_variables = {"x_p": "Int", "y_p": "Int"}
    prime_mapping = {"x": "x_p", "y": "y_p"}
    init_constraints = ["x == 0", "y == 0"]
    trans_constraints = ["x_p == x + 1", "y_p == y + 2"]
    safety_property = "2 * x == y"

    # [1] Weak candidate invariant
    weak_inv = "x >= 0 and y >= 0"
    print(f"[Test 1] Auditing Weak Candidate Invariant: '{weak_inv}'")
    res_weak = verifier.verify_loop_invariant(
        variables=variables,
        prime_variables=prime_variables,
        prime_mapping=prime_mapping,
        init_constraints=init_constraints,
        transition_constraints=trans_constraints,
        candidate_invariant=weak_inv,
        safety_property=safety_property
    )
    print(f"  Initiation Valid?  : {res_weak.initiation_valid}")
    print(f"  Consecution Valid? : {res_weak.consecution_valid}")
    print(f"  Safety Valid?      : {res_weak.safety_valid}")
    print(f"  Is Inductive?      : {res_weak.is_inductive_invariant}")
    print(f"  Counterexample to Safety Synthesized by Z3: {res_weak.counterexample_to_safety}")
    print(f"  Diagnosis: {res_weak.explanation}\n")

    # [2] Sound inductive invariant
    sound_inv = "2 * x == y"
    print(f"[Test 2] Auditing Sound Candidate Invariant: '{sound_inv}'")
    res_sound = verifier.verify_loop_invariant(
        variables=variables,
        prime_variables=prime_variables,
        prime_mapping=prime_mapping,
        init_constraints=init_constraints,
        transition_constraints=trans_constraints,
        candidate_invariant=sound_inv,
        safety_property=safety_property
    )
    print(f"  Initiation Valid?  : {res_sound.initiation_valid} (UNSAT on Init and Not(Inv))")
    print(f"  Consecution Valid? : {res_sound.consecution_valid} (UNSAT on Inv and Trans and Not(Inv'))")
    print(f"  Safety Valid?      : {res_sound.safety_valid} (UNSAT on Inv and Not(Safe))")
    print(f"  Is Inductive?      : {res_sound.is_inductive_invariant}")
    print(f"  Conclusion         : {res_sound.explanation}")


if __name__ == "__main__":
    main()
