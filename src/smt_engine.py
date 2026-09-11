"""
Z3 SMT Solver Execution Engine.
Handles:
- Z3 context and solver lifecycle with strict timeouts.
- AST compilation from variables and constraints.
- Counterexample synthesis (SAT) and bounded domain verification (UNSAT).
- Step-level logical implication verification (H => C) with countermodel extraction upon invalidity.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import z3


@dataclass
class SMTResult:
    status: str  # "sat", "unsat", "unknown"
    is_valid: bool  # True if negated check is UNSAT (meaning theorem holds)
    counterexample: Optional[Dict[str, Any]] = None
    solver_time_ms: float = 0.0
    reason_unknown: Optional[str] = None

    @property
    def is_sound(self) -> bool:
        return self.is_valid


class SMTEngine:
    """Manages compilation, solving, and model extraction using Z3."""

    def __init__(self, default_timeout_ms: int = 5000):
        self.default_timeout_ms = default_timeout_ms

    def solve_smtlib_script(self, script_text: str, timeout_ms: Optional[int] = None) -> SMTResult:
        """Parses and solves a complete SMT-LIB v2 script directly."""
        timeout = timeout_ms or self.default_timeout_ms
        solver = z3.Solver()
        solver.set("timeout", timeout)

        try:
            assertions = z3.parse_smt2_string(script_text)
            solver.add(assertions)
        except Exception as e:
            return SMTResult(
                status="unknown",
                is_valid=False,
                reason_unknown=f"SMT-LIB v2 parsing error: {e}"
            )

        check_res = solver.check()
        if check_res == z3.sat:
            model = solver.model()
            countermodel = {}
            for d in model.decls():
                val = model[d]
                if z3.is_int_value(val):
                    countermodel[str(d.name())] = val.as_long()
                elif z3.is_rational_value(val):
                    countermodel[str(d.name())] = float(val.as_decimal(5))
                elif z3.is_bool(val):
                    countermodel[str(d.name())] = bool(val)
                else:
                    countermodel[str(d.name())] = str(val)
            return SMTResult(status="sat", is_valid=False, counterexample=countermodel)
        elif check_res == z3.unsat:
            return SMTResult(status="unsat", is_valid=True, counterexample=None)
        else:
            return SMTResult(status="unknown", is_valid=False, reason_unknown=str(solver.reason_unknown()))

    def create_variables(self, var_specs: Dict[str, str], ctx: Optional[z3.Context] = None) -> Dict[str, Any]:
        """
        Creates Z3 AST symbols based on type mapping.
        Supported types: 'Int', 'Real', 'Bool'.
        """
        z3_vars = {}
        for name, vtype in var_specs.items():
            if vtype.lower() == "int":
                z3_vars[name] = z3.Int(name, ctx=ctx) if ctx else z3.Int(name)
            elif vtype.lower() == "real":
                z3_vars[name] = z3.Real(name, ctx=ctx) if ctx else z3.Real(name)
            elif vtype.lower() == "bool":
                z3_vars[name] = z3.Bool(name, ctx=ctx) if ctx else z3.Bool(name)
            else:
                raise ValueError(f"Unsupported Z3 variable type: {vtype} for {name}")
        return z3_vars

    def eval_constraint(self, constraint_str: str, z3_vars: Dict[str, Any]) -> Any:
        """
        Safely evaluates an expression string into a Z3 BoolRef AST.
        Supports standard Python comparison, logic, and arithmetic operators on Z3 symbols.
        """
        # Safe evaluation environment exposing Z3 constructs and the declared variables
        safe_env = {
            "And": z3.And,
            "Or": z3.Or,
            "Not": z3.Not,
            "Implies": z3.Implies,
            "If": z3.If,
            "Sum": z3.Sum,
            "Distinct": z3.Distinct,
            **z3_vars
        }
        # Replace python logical words if present outside parentheses
        transformed = (
            constraint_str
            .replace(" or ", " | ")
            .replace(" and ", " & ")
        )
        try:
            return eval(transformed, {"__builtins__": {}}, safe_env)
        except Exception as e:
            raise ValueError(f"Failed to evaluate constraint '{constraint_str}': {e}") from e

    def find_counterexample(
        self,
        var_specs: Dict[str, str],
        domain_constraints: List[str],
        negated_claims: List[str],
        timeout_ms: Optional[int] = None
    ) -> SMTResult:
        """
        Attempts to satisfy the negated claims under domain constraints.
        If SAT: a counterexample to the conjecture is found!
        If UNSAT: no counterexample exists within the bounded domain (claim holds).
        """
        timeout = timeout_ms or self.default_timeout_ms
        ctx = z3.Context()
        solver = z3.Solver(ctx=ctx)
        solver.set("timeout", timeout)

        z3_vars = self.create_variables(var_specs, ctx=ctx)

        # Assert domain bounds
        for dc in domain_constraints:
            solver.add(self.eval_constraint(dc, z3_vars))

        # Assert negated claims (counterexample search conditions)
        for nc in negated_claims:
            solver.add(self.eval_constraint(nc, z3_vars))

        check_res = solver.check()

        if check_res == z3.sat:
            model = solver.model()
            countermodel = self._extract_model(model, z3_vars)
            return SMTResult(status="sat", is_valid=False, counterexample=countermodel)
        elif check_res == z3.unsat:
            return SMTResult(status="unsat", is_valid=True, counterexample=None)
        else:
            return SMTResult(
                status="unknown",
                is_valid=False,
                reason_unknown=str(solver.reason_unknown())
            )

    def _extract_model(self, model: z3.ModelRef, z3_vars: Dict[str, Any]) -> Dict[str, Any]:
        countermodel = {}
        for name, z_var in z3_vars.items():
            val = model.eval(z_var, model_completion=True)
            if z3.is_int_value(val):
                countermodel[name] = val.as_long()
            elif z3.is_rational_value(val):
                countermodel[name] = float(val.as_decimal(5))
            elif z3.is_bool(val):
                countermodel[name] = bool(val)
            else:
                try:
                    countermodel[name] = float(val.as_decimal(5))
                except Exception:
                    countermodel[name] = str(val)
        return countermodel

    def verify_implication_step(
        self,
        var_specs: Dict[str, str],
        hypotheses: List[str],
        conclusion: str,
        timeout_ms: Optional[int] = None
    ) -> SMTResult:
        """
        Formally checks whether Hypotheses => Conclusion is logically valid.
        Proof technique: Check if (Hypotheses AND NOT Conclusion) is UNSAT.
        - If UNSAT: the implication holds strictly (sound step!).
        - If SAT: the step is UNSOUND. The returned model is a concrete counterexample.
        """
        timeout = timeout_ms or self.default_timeout_ms
        ctx = z3.Context()
        solver = z3.Solver(ctx=ctx)
        solver.set("timeout", timeout)

        z3_vars = self.create_variables(var_specs, ctx=ctx)

        # Add all premises / hypotheses
        for hyp in hypotheses:
            solver.add(self.eval_constraint(hyp, z3_vars))

        # Add negation of conclusion
        conc_ast = self.eval_constraint(conclusion, z3_vars)
        solver.add(z3.Not(conc_ast))

        check_res = solver.check()

        if check_res == z3.unsat:
            # Hypotheses AND NOT Conclusion is unsatisfiable => Hypotheses => Conclusion is valid
            return SMTResult(status="unsat", is_valid=True, counterexample=None)
        elif check_res == z3.sat:
            # Counterexample exists where Hypotheses hold but Conclusion fails!
            model = solver.model()
            countermodel = self._extract_model(model, z3_vars)
            return SMTResult(status="sat", is_valid=False, counterexample=countermodel)
        else:
            return SMTResult(
                status="unknown",
                is_valid=False,
                reason_unknown=str(solver.reason_unknown())
            )
