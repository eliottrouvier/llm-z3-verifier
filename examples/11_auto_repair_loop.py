#!/usr/bin/env python3
"""
Example 11: Counterexample-Guided Auto-Repair & Self-Correction Loop.
Demonstrates:
1. Auditing a mathematically flawed LLM deduction: x*y == x*z => y == z.
2. Z3 discovers counterexample {x: 0, y: 1, z: 2}.
3. The AutoRepairEngine synthesizes guard (x != 0).
4. Re-audits the repaired statement and formally certifies Q.E.D.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.repair_loop import AutoRepairEngine


def main():
    print("=" * 75)
    print("Example 11: SMT Counterexample-Guided Auto-Repair Loop")
    print("=" * 75)
    print("Initial LLM Proposal:")
    print("  Hypotheses: ['x * y == x * z']")
    print("  Goal:       'y == z'")
    print("  Domain:     x, y, z in Int\n")

    engine = AutoRepairEngine(max_iterations=5)
    report = engine.audit_and_repair(
        var_specs={"x": "Int", "y": "Int", "z": "Int"},
        initial_hypotheses=["x * y == x * z"],
        goal="y == z"
    )

    print(f"Convergence Status: {report.final_status}")
    print(f"Total Iterations:   {report.iterations_run}")
    print(f"Final Hypotheses:   {report.final_hypotheses}")
    print(f"Explanation:        {report.explanation}\n")

    print("--- Repair Trajectory ---")
    for it in report.repair_trajectory:
        status_sym = "[PASS]" if it.is_verified else "[RETRY]"
        print(f"{status_sym} Iteration {it.iteration}:")
        print(f"       Hypotheses: {it.hypotheses}")
        if it.counterexample:
            print(f"       Counterexample Disproved Step: {it.counterexample}")
        print(f"       Action: {it.repair_action_applied}\n")

    print("=" * 75)
    print("Conclusion: Flawed generative deduction automatically repaired into formal truth.")
    print("=" * 75)


if __name__ == "__main__":
    main()
