"""
Neurosymbolic Auto-Repair & Self-Correction Loop.

Bridges generative LLM formalization errors with automated SMT repair:
1. Vacuity Detection: Audits whether premises are self-contradictory (unsat antecedent).
2. Counterexample-Guided Guard Synthesis (CEGIS-style repair):
   When a candidate implication H => G fails with counterexample x*,
   synthesizes inductive guard constraints (e.g. non-zero, positivity, non-degeneracy)
   to prune the counterexample space.
3. Multi-turn convergence tracking.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from .smt_engine import SMTEngine, SMTResult
from .unsat_core import UnsatCoreEngine


@dataclass
class RepairIteration:
    iteration: int
    hypotheses: List[str]
    goal: str
    is_vacuous: bool
    is_verified: bool
    counterexample: Optional[Dict[str, Any]] = None
    repair_action_applied: Optional[str] = None


@dataclass
class RepairReport:
    initial_goal: str
    converged: bool
    iterations_run: int
    final_hypotheses: List[str]
    final_status: str
    repair_trajectory: List[RepairIteration] = field(default_factory=list)
    explanation: str = ""


class AutoRepairEngine:
    """Automates multi-turn verification, vacuity checking, and counterexample-guided repair."""

    def __init__(self, smt_engine: Optional[SMTEngine] = None, max_iterations: int = 5):
        self.smt_engine = smt_engine or SMTEngine()
        self.unsat_engine = UnsatCoreEngine()
        self.max_iterations = max_iterations

    def audit_and_repair(
        self,
        var_specs: Dict[str, str],
        initial_hypotheses: List[str],
        goal: str
    ) -> RepairReport:
        """
        Executes an iterative CEGIS-like repair loop to turn flawed conjectures/proofs
        into formally certified mathematical statements.
        """
        current_hyps = list(initial_hypotheses)
        trajectory = []

        for i in range(self.max_iterations):
            # 1. Vacuity check: are current hypotheses jointly satisfiable?
            hyp_dict = {f"H_{idx}": h for idx, h in enumerate(current_hyps)}
            vac_res = self.unsat_engine.extract_unsat_core(var_specs, hyp_dict)
            if vac_res.is_unsat:
                # Premises are contradictory!
                iter_info = RepairIteration(
                    iteration=i,
                    hypotheses=list(current_hyps),
                    goal=goal,
                    is_vacuous=True,
                    is_verified=False,
                    repair_action_applied=f"Pruned contradictory premise core: {vac_res.minimal_unsat_core}"
                )
                trajectory.append(iter_info)
                # Remove one contradictory clause to restore satisfiability
                if vac_res.minimal_unsat_core:
                    bad_label = vac_res.minimal_unsat_core[-1]
                    bad_idx = int(bad_label.split("_")[1])
                    current_hyps.pop(bad_idx)
                continue

            # 2. Implication check: current_hyps => goal
            res: SMTResult = self.smt_engine.verify_implication_step(
                var_specs=var_specs,
                hypotheses=current_hyps,
                conclusion=goal
            )

            if res.is_sound:
                # Formally proven sound!
                trajectory.append(RepairIteration(
                    iteration=i,
                    hypotheses=list(current_hyps),
                    goal=goal,
                    is_vacuous=False,
                    is_verified=True,
                    repair_action_applied="Converged: Formal proof certified by Z3."
                ))
                return RepairReport(
                    initial_goal=goal,
                    converged=True,
                    iterations_run=i + 1,
                    final_hypotheses=current_hyps,
                    final_status="SOUND_AND_VERIFIED",
                    repair_trajectory=trajectory,
                    explanation=f"Successfully repaired and certified in {i + 1} iteration(s)."
                )

            # 3. Step was unsound, counterexample found
            ce = res.counterexample
            repair_guard = self._synthesize_guard(ce)
            current_hyps.append(repair_guard)

            trajectory.append(RepairIteration(
                iteration=i,
                hypotheses=list(current_hyps[:-1]),
                goal=goal,
                is_vacuous=False,
                is_verified=False,
                counterexample=ce,
                repair_action_applied=f"Synthesized countermodel-excluding guard: '{repair_guard}'"
            ))

        return RepairReport(
            initial_goal=goal,
            converged=False,
            iterations_run=self.max_iterations,
            final_hypotheses=current_hyps,
            final_status="MAX_ITERATIONS_EXCEEDED",
            repair_trajectory=trajectory,
            explanation="Failed to converge to a sound proof within iteration limit."
        )

    def _synthesize_guard(self, counterexample: Dict[str, Any]) -> str:
        """
        Synthesizes a minimal guard to exclude the observed counterexample.
        For common mathematical pathologies:
        - Variable equals zero: synthesize (var != 0)
        - Negative variable: synthesize (var >= 0)
        """
        for var, val in counterexample.items():
            if val == 0:
                return f"{var} != 0"
            if isinstance(val, (int, float)) and val < 0:
                return f"{var} >= 0"

        # General disjunction exclusion: Not(all vars equal counterexample point)
        point_clauses = [f"{k} == {v}" for k, v in counterexample.items()]
        return f"Not({' and '.join(point_clauses)})"
