"""Unit tests for ProofVerifier."""

from src.smt_engine import SMTEngine
from src.verifier import ProofStep, ProofVerifier


def test_proof_step_verification_sound():
    verifier = ProofVerifier()
    step = ProofStep(
        step_id=0,
        text="Assume a + b > 10 and a > 5. Then b can be anything consistent.",
        variables={"a": "Int", "b": "Int"},
        hypotheses=["a + b > 10", "a > 5"],
        conclusion="a + b >= 11"
    )
    audited = verifier.verify_step(step)
    assert audited.status == "SOUND"
    assert audited.counterexample is None


def test_proof_step_verification_unsound():
    verifier = ProofVerifier()
    step = ProofStep(
        step_id=1,
        text="Assume x * y == 0. Then deduce x == 0.",
        variables={"x": "Int", "y": "Int"},
        hypotheses=["x * y == 0"],
        conclusion="x == 0"
    )
    audited = verifier.verify_step(step)
    assert audited.status == "UNSOUND"
    assert audited.counterexample is not None
    # Verify that the synthesized counterexample actually violates the conclusion
    assert audited.counterexample["x"] != 0


def test_proof_chain_early_stopping():
    verifier = ProofVerifier()
    steps = [
        ProofStep(
            step_id=0,
            text="Valid step",
            variables={"x": "Int"},
            hypotheses=["x > 5"],
            conclusion="x >= 6"
        ),
        ProofStep(
            step_id=1,
            text="Invalid step",
            variables={"x": "Int"},
            hypotheses=["x >= 6"],
            conclusion="x == 10"
        ),
        ProofStep(
            step_id=2,
            text="Subsequent step that should not be reached",
            variables={"x": "Int"},
            hypotheses=["x == 10"],
            conclusion="x > 0"
        )
    ]
    report = verifier.verify_proof_chain(steps)
    assert not report.overall_valid
    assert report.sound_steps == 1
    assert report.unsound_steps == 1
    assert len(report.step_reports) == 2  # Fail-fast stopped at step 1
