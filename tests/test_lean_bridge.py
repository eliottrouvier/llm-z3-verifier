import pytest
from src.lean_bridge import Lean4Bridge, LeanBridge
from src.verifier import ProofStep


def test_lean4_theorem_export():
    bridge = Lean4Bridge()
    export = bridge.export_theorem(
        name="fermat_base_case",
        variables={"x": "Int", "y": "Int"},
        hypotheses=["x > 0", "y > 0", "x + y == 10"],
        conclusion="x < 10 and y < 10",
        tactic="omega"
    )
    assert export.theorem_name == "fermat_base_case"
    assert "import Mathlib" in export.lean_code
    assert "theorem fermat_base_case (x y : Int)" in export.lean_code
    assert "x + y = 10" in export.lean_code
    assert "x < 10 ∧ y < 10" in export.lean_code
    assert "omega" in export.lean_code


def test_lean4_proof_trajectory_export():
    bridge = LeanBridge()
    steps = [
        ProofStep(step_id=0, text="Given a > 0", status="SOUND"),
        ProofStep(step_id=1, text="Deduce a + 1 > 1", status="SOUND")
    ]
    code = bridge.export_proof_trajectory("simple_trajectory", steps)
    assert "theorem simple_trajectory_trajectory" in code
    assert "-- Step 0: Given a > 0" in code
    assert "trivial" in code
