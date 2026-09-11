import pytest
from src.lemma_synthesis import InvariantVerifier, LoopInvariantVerifier


def test_inductive_invariant_sound():
    verifier = InvariantVerifier()
    res = verifier.verify_loop_invariant(
        variables={"x": "Int", "y": "Int"},
        prime_variables={"x_p": "Int", "y_p": "Int"},
        prime_mapping={"x": "x_p", "y": "y_p"},
        init_constraints=["x == 0", "y == 0"],
        transition_constraints=["x_p == x + 1", "y_p == y + 2"],
        candidate_invariant="2 * x == y",
        safety_property="2 * x == y"
    )
    assert res.is_inductive_invariant is True
    assert res.initiation_valid is True
    assert res.consecution_valid is True
    assert res.safety_valid is True
    assert res.is_valid_inductive_invariant is True


def test_weak_invariant_cti():
    verifier = LoopInvariantVerifier()
    # x >= 0 and y >= 0 is an invariant of the system, but too weak to prove 2*x == y
    res = verifier.verify_loop_invariant(
        variables={"x": "Int", "y": "Int"},
        prime_variables={"x_p": "Int", "y_p": "Int"},
        prime_mapping={"x": "x_p", "y": "y_p"},
        init_constraints=["x == 0", "y == 0"],
        transition_constraints=["x_p == x + 1", "y_p == y + 2"],
        candidate_invariant="x >= 0 and y >= 0",
        safety_property="2 * x == y"
    )
    assert res.initiation_valid is True
    assert res.consecution_valid is True
    assert res.safety_valid is False
    assert res.is_inductive_invariant is False
    assert res.counterexample_to_safety is not None


def test_verify_sum_n_helper():
    verifier = InvariantVerifier()
    res = verifier.verify_sum_n_invariant("2 * s == i * (i - 1)")
    assert res.is_valid_inductive_invariant is True
    assert res.initiation_holds is True
    assert res.consecution_holds is True
    assert res.safety_holds is True
