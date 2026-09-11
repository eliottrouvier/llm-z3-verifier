"""
Ramsey Number R(3,3) Formal Prover.
Encodes the complete graph edge 2-coloring problem into propositional SAT in Z3.
Demonstrates:
1. R(3,3) > 5 by finding a monochromatic-triangle-free 2-coloring on K_5 (SAT).
2. R(3,3) <= 6 by proving that no such 2-coloring exists on K_6 (UNSAT).
"""

from __future__ import annotations
import itertools
from typing import Any, Dict, Optional, Tuple
import z3


def check_ramsey(n: int, k: int = 3, timeout_ms: int = 10000) -> Tuple[str, Optional[Dict[str, str]]]:
    """
    Checks if complete graph K_n can be 2-colored without a monochromatic K_k (triangle).
    Returns ("SAT", coloring_dict) or ("UNSAT", None) or ("UNKNOWN", None).
    """
    ctx = z3.Context()
    solver = z3.Solver(ctx=ctx)
    solver.set("timeout", timeout_ms)

    # Variables: edge_color(i, j) in {True (Red), False (Blue)} for 0 <= i < j < n
    edge_vars = {}
    for i in range(n):
        for j in range(i + 1, n):
            edge_vars[(i, j)] = z3.Bool(f"e_{i}_{j}", ctx=ctx)

    # For every triple {i, j, k}, forbid monochromatic triangle:
    # Not(all Red) and Not(all Blue)
    for triple in itertools.combinations(range(n), k):
        i, j, m = sorted(triple)
        e1, e2, e3 = edge_vars[(i, j)], edge_vars[(j, m)], edge_vars[(i, m)]

        # Cannot all be True (Red triangle forbidden)
        solver.add(z3.Not(z3.And(e1, e2, e3)))
        # Cannot all be False (Blue triangle forbidden)
        solver.add(z3.Not(z3.And(z3.Not(e1), z3.Not(e2), z3.Not(e3))))

    res = solver.check()
    if res == z3.sat:
        model = solver.model()
        coloring = {
            f"({i},{j})": "Red" if bool(model[edge_vars[(i, j)]]) else "Blue"
            for (i, j) in edge_vars
        }
        return "SAT", coloring
    elif res == z3.unsat:
        return "UNSAT", None
    else:
        return "UNKNOWN", None
