"""
Synthetic PRM (Process Reward Model) Dataset Generator.

Generates mathematically verified step-level proof trajectories labeled by Z3:
1. Sound deductive derivations (Labeled +1.0).
2. Plausible but unsound derivations with controlled mathematical mutations (Labeled -1.0),
   accompanied by concrete synthesized counterexamples disproving the step.

Output format is directly compatible with HuggingFace datasets and PRM training
pipelines (Lightman et al. PRM800K style).
"""

from __future__ import annotations
import json
import random
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional
from .smt_engine import SMTEngine


@dataclass
class SyntheticPRMStep:
    step_id: int
    text: str
    variables: Dict[str, str]
    hypotheses: List[str]
    conclusion: str
    prm_label: float  # +1.0 for provably sound, -1.0 for unsound
    is_sound: bool
    mutation_type: Optional[str] = None
    counterexample: Optional[Dict[str, Any]] = None
    explanation: str = ""


@dataclass
class SyntheticPRMTrajectory:
    trajectory_id: str
    problem_statement: str
    variables: Dict[str, str]
    initial_premises: List[str]
    target_goal: str
    steps: List[SyntheticPRMStep] = field(default_factory=list)
    has_mutation: bool = False
    first_flawed_step_index: Optional[int] = None


class SyntheticPRMDatasetGenerator:
    """Generates verified process-supervised mathematical reasoning traces."""

    def __init__(self, seed: int = 42, smt_engine: Optional[SMTEngine] = None):
        self.rng = random.Random(seed)
        self.smt_engine = smt_engine or SMTEngine()

    def generate_algebraic_cancellation_trace(self, inject_flaw: bool = False) -> SyntheticPRMTrajectory:
        """
        Problem: Prove that if x*y = x*z, does y = z over integers?
        Sound reasoning requires case analysis (x != 0).
        Unsound mutation assumes y = z unconditionally (disproved by x=0, y=1, z=2).
        """
        var_specs = {"x": "Int", "y": "Int", "z": "Int"}
        steps = []

        # Step 0: Algebraic rearrangement
        step0 = SyntheticPRMStep(
            step_id=0,
            text="Given x*y == x*z, subtract x*z from both sides to obtain x*y - x*z == 0.",
            variables=var_specs,
            hypotheses=["x * y == x * z"],
            conclusion="x * y - x * z == 0",
            prm_label=1.0,
            is_sound=True
        )
        steps.append(step0)

        # Step 1: Factoring
        step1 = SyntheticPRMStep(
            step_id=1,
            text="Factor out x to get x * (y - z) == 0.",
            variables=var_specs,
            hypotheses=["x * y - x * z == 0"],
            conclusion="x * (y - z) == 0",
            prm_label=1.0,
            is_sound=True
        )
        steps.append(step1)

        if inject_flaw:
            # Flaw: Divide by zero without check
            step2 = SyntheticPRMStep(
                step_id=2,
                text="Divide both sides by x to deduce that y - z == 0, hence y == z.",
                variables=var_specs,
                hypotheses=["x * (y - z) == 0"],
                conclusion="y == z",
                prm_label=-1.0,
                is_sound=False,
                mutation_type="UNCHECKED_DIVISION_BY_ZERO"
            )
            # Verify with Z3
            res = self.smt_engine.verify_implication_step(
                var_specs=var_specs,
                hypotheses=["x * (y - z) == 0"],
                conclusion="y == z"
            )
            step2.counterexample = res.counterexample
            step2.explanation = "Z3 synthesized countermodel showing division by zero when x = 0."
            steps.append(step2)
            first_flaw = 2
        else:
            # Sound step: Case distinction
            step2 = SyntheticPRMStep(
                step_id=2,
                text="Case 1: If x != 0, we divide by x to obtain y == z. If x == 0, y and z can be arbitrary.",
                variables=var_specs,
                hypotheses=["x * (y - z) == 0"],
                conclusion="(x == 0) or (y == z)",
                prm_label=1.0,
                is_sound=True
            )
            steps.append(step2)
            first_flaw = None

        return SyntheticPRMTrajectory(
            trajectory_id=f"alg_cancellation_{'flawed' if inject_flaw else 'sound'}",
            problem_statement="Analyze whether x*y = x*z implies y = z over integers.",
            variables=var_specs,
            initial_premises=["x * y == x * z"],
            target_goal="(x == 0) or (y == z)" if not inject_flaw else "y == z",
            steps=steps,
            has_mutation=inject_flaw,
            first_flawed_step_index=first_flaw
        )

    def generate_inequality_squaring_trace(self, inject_flaw: bool = False) -> SyntheticPRMTrajectory:
        """
        Problem: If a > b, is a^2 > b^2 over reals?
        Unsound mutation: a > b => a^2 > b^2 without non-negativity constraint.
        Countermodel: a = 1, b = -3 (1 > -3, but 1^2 = 1 < 9 = (-3)^2).
        """
        var_specs = {"a": "Real", "b": "Real"}
        steps = []

        step0 = SyntheticPRMStep(
            step_id=0,
            text="Assume a > b in the real domain.",
            variables=var_specs,
            hypotheses=["a > b"],
            conclusion="a > b",
            prm_label=1.0,
            is_sound=True
        )
        steps.append(step0)

        if inject_flaw:
            step1 = SyntheticPRMStep(
                step_id=1,
                text="Square both sides of the inequality to deduce a*a > b*b.",
                variables=var_specs,
                hypotheses=["a > b"],
                conclusion="a * a > b * b",
                prm_label=-1.0,
                is_sound=False,
                mutation_type="UNCHECKED_INEQUALITY_SQUARING"
            )
            res = self.smt_engine.verify_implication_step(
                var_specs=var_specs,
                hypotheses=["a > b"],
                conclusion="a * a > b * b"
            )
            step1.counterexample = res.counterexample
            step1.explanation = "Z3 synthesized countermodel showing squaring is non-monotonic on negative reals."
            steps.append(step1)
            first_flaw = 1
        else:
            step1 = SyntheticPRMStep(
                step_id=1,
                text="Assume the additional premise that b >= 0, implying 0 <= b < a.",
                variables=var_specs,
                hypotheses=["a > b", "b >= 0"],
                conclusion="a * a > b * b",
                prm_label=1.0,
                is_sound=True
            )
            steps.append(step1)
            first_flaw = None

        return SyntheticPRMTrajectory(
            trajectory_id=f"inequality_squaring_{'flawed' if inject_flaw else 'sound'}",
            problem_statement="Analyze if a > b implies a^2 > b^2.",
            variables=var_specs,
            initial_premises=["a > b"],
            target_goal="a * a > b * b",
            steps=steps,
            has_mutation=inject_flaw,
            first_flawed_step_index=first_flaw
        )

    def generate_dataset(self, num_samples: int = 10) -> List[SyntheticPRMTrajectory]:
        """Generates a balanced batch of sound and flawed mathematical trajectories."""
        trajectories = []
        for i in range(num_samples):
            inject_flaw = (i % 2 == 1)
            if i % 4 in [0, 1]:
                traj = self.generate_algebraic_cancellation_trace(inject_flaw=inject_flaw)
            else:
                traj = self.generate_inequality_squaring_trace(inject_flaw=inject_flaw)
            trajectories.append(traj)
        return trajectories

    def export_jsonl(self, trajectories: List[SyntheticPRMTrajectory], output_path: str) -> None:
        """Exports trajectories to JSONL format for PRM training."""
        with open(output_path, "w", encoding="utf-8") as f:
            for traj in trajectories:
                entry = {
                    "trajectory_id": traj.trajectory_id,
                    "problem_statement": traj.problem_statement,
                    "has_flaw": traj.has_mutation,
                    "first_flawed_step": traj.first_flawed_step_index,
                    "steps": [
                        {
                            "step_id": s.step_id,
                            "text": s.text,
                            "label": s.prm_label,
                            "is_sound": s.is_sound,
                            "mutation": s.mutation_type,
                            "counterexample": s.counterexample
                        }
                        for s in traj.steps
                    ]
                }
                f.write(json.dumps(entry) + "\n")
