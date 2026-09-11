"""
SMT Unsat Core & Minimal Unsatisfiable Subformula (MUS) Extraction Engine.

When a set of mathematical hypotheses proves a theorem (or is logically inconsistent),
determining the exact minimal subset of axioms required is a fundamental problem in
formal verification and automated theorem proving.

This module implements:
1. Tracked Boolean Literal Resolution using Z3 assert_and_track.
2. Deletion-based Minimal Unsatisfiable Subformula (MUS) extraction.
3. Redundant Hypothesis Pruner: Discards spurious LLM premises to isolate
   the exact mathematical core needed to establish the conclusion.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
import z3


@dataclass
class UnsatCoreResult:
    is_unsat: bool
    status: str  # "unsat", "sat", "unknown"
    full_hypothesis_count: int
    raw_unsat_core: List[str] = field(default_factory=list)
    minimal_unsat_core: List[str] = field(default_factory=list)
    redundant_hypotheses: List[str] = field(default_factory=list)
    satisfying_model: Optional[Dict[str, Any]] = None
    reduction_ratio: float = 0.0
    explanation: str = ""


class UnsatCoreEngine:
    """Extracts minimal axiom sets and unsat cores using Z3 tracked literals."""

    def __init__(self, timeout_ms: int = 5000):
        self.timeout_ms = timeout_ms

    def extract_unsat_core(
        self,
        var_specs: Dict[str, str],
        hypotheses: Dict[str, str],
        negated_goal: Optional[str] = None
    ) -> UnsatCoreResult:
        """
        Audits hypotheses against an optional negated goal.
        hypotheses is a dict mapping label -> expression string (e.g. {"H1": "x > 0", "H2": "x < -5"}).
        """
        ctx = z3.Context()
        solver = z3.Solver(ctx=ctx)
        solver.set("timeout", self.timeout_ms)

        # 1. Create variables
        var_map = {}
        for name, vtype in var_specs.items():
            if vtype.lower() == "int":
                var_map[name] = z3.Int(name, ctx=ctx)
            elif vtype.lower() == "real":
                var_map[name] = z3.Real(name, ctx=ctx)
            elif vtype.lower() == "bool":
                var_map[name] = z3.Bool(name, ctx=ctx)

        # 2. Assert and track each hypothesis with a unique boolean literal
        trackers = {}
        parsed_clauses = {}
        for label, expr_str in hypotheses.items():
            trk = z3.Bool(f"trk_{label}", ctx=ctx)
            trackers[trk] = label
            ast = self._parse_expr(expr_str, var_map)
            parsed_clauses[label] = ast
            solver.assert_and_track(ast, trk)

        # 3. Add negated goal if present (untracked, must hold)
        if negated_goal:
            g_ast = self._parse_expr(negated_goal, var_map)
            solver.add(g_ast)

        # 4. Check satisfiability
        check_res = solver.check()
        total_hyps = len(hypotheses)

        if check_res == z3.sat:
            m = solver.model()
            model_dict = {}
            for k, v in var_map.items():
                val = m[v]
                if val is not None:
                    if z3.is_int_value(val):
                        model_dict[k] = val.as_long()
                    elif z3.is_rational_value(val):
                        model_dict[k] = float(val.as_fraction())
                    else:
                        model_dict[k] = str(val)
            return UnsatCoreResult(
                is_unsat=False,
                status="sat",
                full_hypothesis_count=total_hyps,
                satisfying_model=model_dict,
                explanation="Premises (and negated goal) are jointly SAT; no contradiction exists."
            )

        if check_res == z3.unknown:
            return UnsatCoreResult(
                is_unsat=False,
                status="unknown",
                full_hypothesis_count=total_hyps,
                explanation="Z3 returned unknown (timeout or undecidable fragment)."
            )

        # 5. Extract raw unsat core
        core_literals = solver.unsat_core()
        raw_core_labels = [trackers[lit] for lit in core_literals if lit in trackers]

        # 6. Deletion-based Minimal Unsatisfiable Subformula (MUS) extraction
        minimal_labels = self._compute_minimal_core(
            var_specs=var_specs,
            candidate_labels=raw_core_labels,
            all_hypotheses=hypotheses,
            negated_goal=negated_goal
        )

        all_label_set = set(hypotheses.keys())
        min_label_set = set(minimal_labels)
        redundant = sorted(list(all_label_set - min_label_set))

        red_ratio = (total_hyps - len(minimal_labels)) / total_hyps if total_hyps > 0 else 0.0

        expl = (
            f"Extracted minimal core of size {len(minimal_labels)} from {total_hyps} premises. "
            f"Pruned {len(redundant)} redundant hypotheses ({red_ratio*100:.1f}% reduction)."
        )

        return UnsatCoreResult(
            is_unsat=True,
            status="unsat",
            full_hypothesis_count=total_hyps,
            raw_unsat_core=sorted(raw_core_labels),
            minimal_unsat_core=sorted(minimal_labels),
            redundant_hypotheses=redundant,
            reduction_ratio=round(red_ratio, 4),
            explanation=expl
        )

    def _compute_minimal_core(
        self,
        var_specs: Dict[str, str],
        candidate_labels: List[str],
        all_hypotheses: Dict[str, str],
        negated_goal: Optional[str]
    ) -> List[str]:
        """Standard Deletion-Filter algorithm for guaranteed minimal unsat core."""
        current_core = list(candidate_labels)

        for candidate in list(candidate_labels):
            test_subset = [lbl for lbl in current_core if lbl != candidate]
            # Test if test_subset alone is still UNSAT
            if self._is_subset_unsat(var_specs, {lbl: all_hypotheses[lbl] for lbl in test_subset}, negated_goal):
                current_core.remove(candidate)

        return current_core

    def _is_subset_unsat(
        self,
        var_specs: Dict[str, str],
        subset_hypotheses: Dict[str, str],
        negated_goal: Optional[str]
    ) -> bool:
        ctx = z3.Context()
        solver = z3.Solver(ctx=ctx)
        solver.set("timeout", self.timeout_ms)

        var_map = {}
        for name, vtype in var_specs.items():
            if vtype.lower() == "int":
                var_map[name] = z3.Int(name, ctx=ctx)
            elif vtype.lower() == "real":
                var_map[name] = z3.Real(name, ctx=ctx)
            elif vtype.lower() == "bool":
                var_map[name] = z3.Bool(name, ctx=ctx)

        for expr_str in subset_hypotheses.values():
            solver.add(self._parse_expr(expr_str, var_map))

        if negated_goal:
            solver.add(self._parse_expr(negated_goal, var_map))

        return solver.check() == z3.unsat

    def _parse_expr(self, expr: str, var_map: Dict[str, Any]) -> Any:
        safe_env = {k: v for k, v in var_map.items()}
        safe_env["And"] = z3.And
        safe_env["Or"] = z3.Or
        safe_env["Not"] = z3.Not
        return eval(expr, {"__builtins__": {}}, safe_env)
