import pytest
from src.quantifiers import QuantifierEngine


def test_additive_inverse():
    qe = QuantifierEngine()
    res = qe.verify_additive_inverse_valid()
    assert res.is_valid is True
    assert res.status == "unsat"


def test_quantifier_swap_fallacy():
    qe = QuantifierEngine()
    res = qe.disprove_quantifier_swap_fallacy()
    assert res.is_valid is False
    assert res.status == "unsat"


def test_divisibility_transitivity():
    qe = QuantifierEngine()
    res = qe.verify_divisibility_transitivity()
    assert res.is_valid is True
    assert res.status == "unsat"
