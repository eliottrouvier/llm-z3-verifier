import pytest
from src.unsat_core import UnsatCoreEngine


def test_unsat_core_extraction():
    engine = UnsatCoreEngine()
    hypotheses = {
        "H1": "x > 10",
        "H2": "y == 5",
        "H3": "x < 5",
        "H4": "z > 0"
    }
    res = engine.extract_unsat_core(
        var_specs={"x": "Int", "y": "Int", "z": "Int"},
        hypotheses=hypotheses
    )
    assert res.is_unsat is True
    assert set(res.minimal_unsat_core) == {"H1", "H3"}
    assert set(res.redundant_hypotheses) == {"H2", "H4"}
    assert res.reduction_ratio == 0.5


def test_satisfiable_premises_no_core():
    engine = UnsatCoreEngine()
    hypotheses = {
        "H1": "x > 0",
        "H2": "x < 10"
    }
    res = engine.extract_unsat_core(
        var_specs={"x": "Int"},
        hypotheses=hypotheses
    )
    assert res.is_unsat is False
    assert res.status == "sat"
    assert res.satisfying_model is not None
    assert 0 < res.satisfying_model["x"] < 10
