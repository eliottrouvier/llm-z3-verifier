"""
Step-Level Proof Verifier.
Deconstructs mathematical arguments into individual logical deduction steps
and checks soundness against the Z3 SMT solver.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from .smt_engine import SMTEngine, SMTResult


@dataclass
class ProofStep:
    step_id: int
    text: str
    variables: Dict[str, str] = field(default_factory=dict)
    hypotheses: List[str] = field(default_factory=list)
    conclusion: str = ""
    status: str = "PENDING"  # PENDING, SOUND, UNSOUND, UNKNOWN
    counterexample: Optional[Dict[str, Any]] = None
    verification_time_ms: float = 0.0

    @property
    def is_sound(self) -> bool:
        return self.status == "SOUND"


@dataclass
class VerificationReport:
    total_steps: int
    sound_steps: int
    unsound_steps: int
    overall_valid: bool
    step_reports: List[ProofStep] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the verification report into a structured dictionary."""
        return {
            "total_steps": self.total_steps,
            "sound_steps": self.sound_steps,
            "unsound_steps": self.unsound_steps,
            "overall_valid": self.overall_valid,
            "steps": [
                {
                    "step_id": s.step_id,
                    "text": s.text,
                    "status": s.status,
                    "is_sound": s.is_sound,
                    "counterexample": s.counterexample,
                    "time_ms": s.verification_time_ms
                }
                for s in self.step_reports
            ]
        }


class ProofVerifier:
    """Verifies each deduction step in a multi-step proof sequence."""

    def __init__(self, smt_engine: Optional[SMTEngine] = None):
        self.smt_engine = smt_engine or SMTEngine()

    def verify_step(self, step: ProofStep) -> ProofStep:
        """Audits a single deduction step (hypotheses => conclusion)."""
        res: SMTResult = self.smt_engine.verify_implication_step(
            var_specs=step.variables,
            hypotheses=step.hypotheses,
            conclusion=step.conclusion
        )
        if res.is_valid:
            step.status = "SOUND"
            step.counterexample = None
        elif res.status == "sat":
            step.status = "UNSOUND"
            step.counterexample = res.counterexample
        else:
            step.status = "UNKNOWN"
            step.counterexample = None

        return step

    def verify_proof_chain(self, steps: List[ProofStep]) -> VerificationReport:
        """
        Verifies a sequential chain of proof steps.
        Stops immediately upon the first unsound step (fail-fast principle).
        """
        sound_count = 0
        unsound_count = 0
        all_sound = True

        verified_steps = []
        for step in steps:
            audited = self.verify_step(step)
            verified_steps.append(audited)
            if audited.status == "SOUND":
                sound_count += 1
            else:
                unsound_count += 1
                all_sound = False
                break  # The proof is severed at this step

        return VerificationReport(
            total_steps=len(steps),
            sound_steps=sound_count,
            unsound_steps=unsound_count,
            overall_valid=all_sound,
            step_reports=verified_steps
        )
