"""
Process Reward Model (PRM) with Symbolic Z3 Verification.
Implements step-level process supervision (Lightman et al. 2023 style)
where each deduction step receives an exact formal verification reward in [-1.0, 1.0].
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from .smt_engine import SMTEngine, SMTResult
from .verifier import ProofStep


@dataclass
class StepReward:
    step_id: int
    step_text: str
    reward: float  # +1.0 for sound, -1.0 for invalid, 0.0 for unknown/unverified
    is_sound: bool
    counterexample: Optional[Dict[str, Any]] = None
    rationale: str = ""


@dataclass
class TrajectoryScore:
    total_steps: int
    step_rewards: List[StepReward]
    cumulative_reward: float
    min_step_reward: float
    is_trajectory_sound: bool
    flawed_step_index: Optional[int] = None


class SymbolicPRM:
    """
    Step-level Process Reward Model backed by Z3.
    Replaces soft neural reward guesses with hard mathematical verification.
    """

    def __init__(self, smt_engine: Optional[SMTEngine] = None):
        self.smt_engine = smt_engine or SMTEngine()

    def score_step(self, step: ProofStep) -> StepReward:
        """Evaluates a single deduction step and computes its formal PRM reward."""
        res: SMTResult = self.smt_engine.verify_implication_step(
            var_specs=step.variables,
            hypotheses=step.hypotheses,
            conclusion=step.conclusion
        )

        if res.is_valid:
            return StepReward(
                step_id=step.step_id,
                step_text=step.text,
                reward=1.0,
                is_sound=True,
                counterexample=None,
                rationale="Formally proved valid by Z3 SMT solver."
            )
        elif res.status == "sat":
            return StepReward(
                step_id=step.step_id,
                step_text=step.text,
                reward=-1.0,
                is_sound=False,
                counterexample=res.counterexample,
                rationale=f"Falsified by Z3 with counterexample: {res.counterexample}"
            )
        else:
            return StepReward(
                step_id=step.step_id,
                step_text=step.text,
                reward=0.0,
                is_sound=False,
                counterexample=None,
                rationale=f"Solver returned unknown: {res.reason_unknown}"
            )

    def score_trajectory(self, steps: List[ProofStep]) -> TrajectoryScore:
        """
        Computes process rewards across an entire reasoning chain.
        Early-terminates upon first unsound step (fail-fast principle).
        """
        rewards: List[StepReward] = []
        is_sound = True
        flawed_idx = None

        for idx, step in enumerate(steps):
            s_reward = self.score_step(step)
            rewards.append(s_reward)
            if not s_reward.is_sound:
                is_sound = False
                flawed_idx = idx
                break

        if not rewards:
            return TrajectoryScore(0, [], 0.0, 0.0, True, None)

        cum_reward = sum(r.reward for r in rewards)
        min_reward = min(r.reward for r in rewards)

        return TrajectoryScore(
            total_steps=len(rewards),
            step_rewards=rewards,
            cumulative_reward=cum_reward,
            min_step_reward=min_reward,
            is_trajectory_sound=is_sound,
            flawed_step_index=flawed_idx
        )
