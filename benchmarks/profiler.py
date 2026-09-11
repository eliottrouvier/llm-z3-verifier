"""
Performance Profiler & Z3 Solver Tactic Analyzer.
Measures memory usage (peak allocation in KB) and latency across distinct solver tactics:
- QF_LIA (Simplex + Gomory cuts)
- QF_NRA (Cylindrical Algebraic Decomposition / NLSAT)
- QF_BV (Bit-Blasting & SAT)
- Propositional SAT (CDCL on Ramsey K_5 / K_6)
"""

from __future__ import annotations
import json
import os
import sys
import time
import tracemalloc
from typing import Dict, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.smt_engine import SMTEngine
from src.bitvectors import BitVectorEngine
from src.ramsey import check_ramsey


def profile_all_theories() -> Dict[str, Any]:
    print("\n" + "=" * 75)
    print("      Z3 SOLVER TACTIC & MEMORY PROFILER")
    print("=" * 75)

    profile_results = []
    smt = SMTEngine()
    bv_engine = BitVectorEngine()

    benchmarks = [
        (
            "Propositional SAT (Ramsey K_5)",
            "CDCL boolean constraint propagation",
            lambda: check_ramsey(5, 3)
        ),
        (
            "Propositional SAT (Ramsey K_6 UNSAT)",
            "CDCL exhaustive refutation",
            lambda: check_ramsey(6, 3)
        ),
        (
            "QF_LIA (Matrix Zero Divisors)",
            "Dual Simplex with integer branch-and-bound",
            lambda: smt.find_counterexample(
                var_specs={"a": "Int", "b": "Int", "c": "Int", "d": "Int",
                           "x": "Int", "y": "Int", "z": "Int", "w": "Int"},
                domain_constraints=[],
                negated_claims=[
                    "a*a + b*b + c*c + d*d > 0", "x*x + y*y + z*z + w*w > 0",
                    "a*x + b*z == 0", "a*y + b*w == 0",
                    "c*x + d*z == 0", "c*y + d*w == 0"
                ]
            )
        ),
        (
            "QF_NRA (Cauchy-Schwarz in R^3)",
            "NLSAT & Cylindrical Algebraic Decomposition (CAD)",
            lambda: smt.find_counterexample(
                var_specs={"x1": "Real", "x2": "Real", "x3": "Real",
                           "y1": "Real", "y2": "Real", "y3": "Real"},
                domain_constraints=[],
                negated_claims=[
                    "(x1*y1 + x2*y2 + x3*y3)**2 > (x1**2 + x2**2 + x3**2)*(y1**2 + y2**2 + y3**2)"
                ]
            )
        ),
        (
            "QF_BV (32-bit Integer Overflow)",
            "Bit-blasting to propositional SAT",
            lambda: bv_engine.check_addition_overflow(32, signed=True)
        ),
        (
            "QF_BV (Power-of-Two Bitwise Hack)",
            "Bit-vector equivalence reasoning",
            lambda: bv_engine.verify_power_of_two_hack(32)
        )
    ]

    for name, description, runner in benchmarks:
        tracemalloc.start()
        t0 = time.perf_counter()

        _ = runner()

        elapsed_ms = (time.perf_counter() - t0) * 1000
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_kb = peak / 1024
        res_dict = {
            "benchmark": name,
            "tactic": description,
            "latency_ms": round(elapsed_ms, 2),
            "peak_memory_kb": round(peak_kb, 1)
        }
        profile_results.append(res_dict)
        print(f" {name:<38} | Latency: {elapsed_ms:6.2f} ms | Peak Mem: {peak_kb:6.1f} KB")

    avg_lat = sum(r["latency_ms"] for r in profile_results) / len(profile_results)
    avg_mem = sum(r["peak_memory_kb"] for r in profile_results) / len(profile_results)

    print("-" * 75)
    print(f"Summary: Average Latency = {avg_lat:.2f} ms | Average Peak Memory = {avg_mem:.1f} KB")
    print("=" * 75 + "\n")

    return {
        "benchmarks": profile_results,
        "avg_latency_ms": round(avg_lat, 2),
        "avg_peak_memory_kb": round(avg_mem, 1)
    }


if __name__ == "__main__":
    profile_all_theories()
