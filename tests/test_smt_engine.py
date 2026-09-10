"""Unit tests for SMTEngine."""

import pytest
from src.smt_engine import SMTEngine


def test_variable_creation():
    engine = SMTEngine()
    vars_map = engine.create_variables({"x": "Int", "y": "Real", "b": "Bool"})
    assert "x" in vars_map
    assert "y" in vars_map
    assert "b" in vars_map


def test_find_counterexample_sat():
    engine = SMTEngine()
    # Claim: for all integer x in [0, 10], x < 5
    # Negation: x >= 5
    res = engine.find_counterexample(
        var_specs={"x": "Int"},
        domain_constraints=["x >= 0", "x <= 10"],
        negated_claims=["x >= 5"]
    )
    assert res.status == "sat"
    assert not res.is_valid
    assert res.counterexample is not None
    assert res.counterexample["x"] >= 5


def test_find_counterexample_unsat():
    engine = SMTEngine()
    # Claim: for all integer x in [0, 4], x < 5
    # Negation: x >= 5
    res = engine.find_counterexample(
        var_specs={"x": "Int"},
        domain_constraints=["x >= 0", "x <= 4"],
        negated_claims=["x >= 5"]
    )
    assert res.status == "unsat"
    assert res.is_valid
    assert res.counterexample is None


def test_verify_implication_step_sound():
    engine = SMTEngine()
    # Hypotheses: x > 2, y > 3
    # Conclusion: x + y > 5
    res = engine.verify_implication_step(
        var_specs={"x": "Int", "y": "Int"},
        hypotheses=["x > 2", "y > 3"],
        conclusion="x + y > 5"
    )
    assert res.is_valid
    assert res.status == "unsat"


def test_verify_implication_step_unsound():
    engine = SMTEngine()
    # Hypotheses: x * y == 0
    # Conclusion: x == 0 (UNSOUND because y could be 0 while x != 0)
    res = engine.verify_implication_step(
        var_specs={"x": "Int", "y": "Int"},
        hypotheses=["x * y == 0"],
        conclusion="x == 0"
    )
    assert not res.is_valid
    assert res.status == "sat"
    assert res.counterexample is not None
    ce = res.counterexample
    assert ce["x"] * ce["y"] == 0
    assert ce["x"] != 0
