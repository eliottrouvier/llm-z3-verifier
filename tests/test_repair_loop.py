import pytest
from src.repair_loop import AutoRepairEngine


def test_auto_repair_division_by_zero():
    engine = AutoRepairEngine(max_iterations=5)
    report = engine.audit_and_repair(
        var_specs={"x": "Int", "y": "Int", "z": "Int"},
        initial_hypotheses=["x * y == x * z"],
        goal="y == z"
    )
    assert report.converged is True
    assert report.iterations_run == 2
    assert "x != 0" in report.final_hypotheses
    assert report.final_status == "SOUND_AND_VERIFIED"


def test_already_sound_implication():
    engine = AutoRepairEngine(max_iterations=3)
    report = engine.audit_and_repair(
        var_specs={"x": "Int"},
        initial_hypotheses=["x > 5"],
        goal="x > 0"
    )
    assert report.converged is True
    assert report.iterations_run == 1
    assert report.final_hypotheses == ["x > 5"]
