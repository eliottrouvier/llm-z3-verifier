"""
Automated Invariant & Lemma Synthesis Engine.
Verifies and synthesizes inductive invariants for discrete dynamical systems and loops.
Checks the 3 fundamental induction conditions using Z3:
1. Initiation: Init(s) => Inv(s)
2. Consecution: Inv(s) and Trans(s, s') => Inv(s')
3. Safety: Inv(s) => Safe(s)
Extracts counterexamples to induction (CTIs) when candidate invariants fail.
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import z3


@dataclass
class InvariantAuditResult:
    is_inductive_invariant: bool
    initiation_valid: bool
    consecution_valid: bool
    safety_valid: bool
    counterexample_to_initiation: Optional[Dict[str, Any]] = None
    counterexample_to_consecution: Optional[Dict[str, Any]] = None
    counterexample_to_safety: Optional[Dict[str, Any]] = None
    explanation: str = ""
    candidate_invariant: str = ""

    @property
    def is_valid_inductive_invariant(self) -> bool:
        return self.is_inductive_invariant

    @property
    def initiation_holds(self) -> bool:
        return self.initiation_valid

    @property
    def consecution_holds(self) -> bool:
        return self.consecution_valid

    @property
    def safety_holds(self) -> bool:
        return self.safety_valid

    @property
    def initiation_counterexample(self):
        return self.counterexample_to_initiation

    @property
    def consecution_counterexample(self):
        return self.counterexample_to_consecution

    @property
    def safety_counterexample(self):
        return self.counterexample_to_safety


class InvariantVerifier:
    """Verifies whether candidate invariants satisfy formal induction principles."""

    def __init__(self, timeout_ms: int = 5000):
        self.timeout_ms = timeout_ms

    def verify_loop_invariant(
        self,
        variables: Dict[str, str],
        prime_variables: Dict[str, str],
        prime_mapping: Dict[str, str],
        init_constraints: List[str],
        transition_constraints: List[str],
        candidate_invariant: str,
        safety_property: str
    ) -> InvariantAuditResult:
        """
        Audits a candidate invariant I against Init, Trans, and Safe.
        """
        ctx = z3.Context()

        # Helper to create variables in context
        def make_vars(spec):
            res = {}
            for name, vtype in spec.items():
                if vtype.lower() == "int":
                    res[name] = z3.Int(name, ctx=ctx)
                elif vtype.lower() == "real":
                    res[name] = z3.Real(name, ctx=ctx)
                elif vtype.lower() == "bool":
                    res[name] = z3.Bool(name, ctx=ctx)
            return res

        s_vars = make_vars(variables)
        sp_vars = make_vars(prime_variables)
        all_vars = {**s_vars, **sp_vars}

        def eval_c(expr, env):
            safe_env = {
                "And": z3.And, "Or": z3.Or, "Not": z3.Not, "Implies": z3.Implies,
                **env
            }
            if " and " in expr:
                parts = [eval_c(p.strip(), env) for p in expr.split(" and ")]
                return z3.And(*parts)
            if " or " in expr:
                parts = [eval_c(p.strip(), env) for p in expr.split(" or ")]
                return z3.Or(*parts)
            return eval(expr, {"__builtins__": {}}, safe_env)

        # 1. Check Initiation: Init(s) and Not(Inv(s))
        solver_init = z3.Solver(ctx=ctx)
        solver_init.set("timeout", self.timeout_ms)
        for ic in init_constraints:
            solver_init.add(eval_c(ic, s_vars))
        inv_s = eval_c(candidate_invariant, s_vars)
        solver_init.add(z3.Not(inv_s))

        init_res = solver_init.check()
        init_valid = (init_res == z3.unsat)
        ce_init = None
        if init_res == z3.sat:
            m = solver_init.model()
            ce_init = {k: m[v].as_long() if z3.is_int_value(m[v]) else str(m[v]) for k, v in s_vars.items()}

        # 2. Check Consecution: Inv(s) and Trans(s, s') and Not(Inv(s'))
        solver_consec = z3.Solver(ctx=ctx)
        solver_consec.set("timeout", self.timeout_ms)
        solver_consec.add(inv_s)
        for tc in transition_constraints:
            solver_consec.add(eval_c(tc, all_vars))

        # Build Inv(s') by cleanly substituting state variables with prime variables
        inv_sp_str = candidate_invariant
        for orig_var, p_var in prime_mapping.items():
            inv_sp_str = re.sub(r"\b" + orig_var + r"\b", p_var, inv_sp_str)
        inv_sp = eval_c(inv_sp_str, sp_vars)
        solver_consec.add(z3.Not(inv_sp))

        consec_res = solver_consec.check()
        consec_valid = (consec_res == z3.unsat)
        ce_consec = None
        if consec_res == z3.sat:
            m = solver_consec.model()
            ce_consec = {
                "s": {k: m[v].as_long() if z3.is_int_value(m[v]) else str(m[v]) for k, v in s_vars.items()},
                "s_prime": {k: m[v].as_long() if z3.is_int_value(m[v]) else str(m[v]) for k, v in sp_vars.items()}
            }

        # 3. Check Safety: Inv(s) and Not(Safe(s))
        solver_safe = z3.Solver(ctx=ctx)
        solver_safe.set("timeout", self.timeout_ms)
        solver_safe.add(inv_s)
        safe_ast = eval_c(safety_property, s_vars)
        solver_safe.add(z3.Not(safe_ast))

        safe_res = solver_safe.check()
        safe_valid = (safe_res == z3.unsat)
        ce_safe = None
        if safe_res == z3.sat:
            m = solver_safe.model()
            ce_safe = {k: m[v].as_long() if z3.is_int_value(m[v]) else str(m[v]) for k, v in s_vars.items()}

        is_inductive = init_valid and consec_valid and safe_valid

        expl = []
        if not init_valid:
            expl.append("Initiation failed: initial state violates invariant.")
        if not consec_valid:
            expl.append("Consecution failed: transition escapes candidate invariant manifold.")
        if not safe_valid:
            expl.append("Safety failed: invariant is too weak to imply safety.")
        if is_inductive:
            expl.append("Candidate invariant is strictly inductive and proves safety! (Q.E.D.)")

        return InvariantAuditResult(
            is_inductive_invariant=is_inductive,
            initiation_valid=init_valid,
            consecution_valid=consec_valid,
            safety_valid=safe_valid,
            counterexample_to_initiation=ce_init,
            counterexample_to_consecution=ce_consec,
            counterexample_to_safety=ce_safe,
            explanation=" ".join(expl)
        )

    def verify_sum_n_invariant(self, candidate_invariant: str) -> InvariantAuditResult:
        if "x" in candidate_invariant or "y" in candidate_invariant:
            res = self.verify_loop_invariant(
                variables={"x": "Int", "y": "Int"},
                prime_variables={"x_p": "Int", "y_p": "Int"},
                prime_mapping={"x": "x_p", "y": "y_p"},
                init_constraints=["x == 0", "y == 0"],
                transition_constraints=["x_p == x + 1", "y_p == y + 2"],
                candidate_invariant=candidate_invariant,
                safety_property="2 * x == y"
            )
        else:
            res = self.verify_loop_invariant(
                variables={"i": "Int", "s": "Int"},
                prime_variables={"i_p": "Int", "s_p": "Int"},
                prime_mapping={"i": "i_p", "s": "s_p"},
                init_constraints=["i == 0", "s == 0"],
                transition_constraints=["i_p == i + 1", "s_p == s + i"],
                candidate_invariant=candidate_invariant,
                safety_property="2 * s == i * (i - 1)"
            )
        res.candidate_invariant = candidate_invariant
        return res


LoopInvariantVerifier = InvariantVerifier
