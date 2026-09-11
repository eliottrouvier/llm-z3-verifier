"""Unit tests for SMTLibParser."""

import pytest
from src.smtlib_parser import SMTLibParser
from src.smt_engine import SMTEngine


def test_parser_valid_script():
    parser = SMTLibParser()
    script_str = """
    (set-logic QF_LIA)
    (declare-const x Int)
    (declare-const y Int)
    (assert (> x 0))
    (assert (< y 0))
    (assert (= (+ x y) 10))
    (check-sat)
    """
    res = parser.parse(script_str)
    assert res.is_valid_syntax is True
    assert res.logic == "QF_LIA"
    assert "x" in res.declared_constants
    assert "y" in res.declared_constants
    assert res.syntax_error is None


def test_parser_unbalanced_parentheses():
    parser = SMTLibParser()
    bad_script = """
    (set-logic QF_LIA
    (declare-const x Int)
    (assert (> x 0)
    """
    res = parser.parse(bad_script)
    assert res.is_valid_syntax is False
    assert "parentheses" in res.syntax_error.lower()


def test_solve_parsed_script_in_engine():
    parser = SMTLibParser()
    script_str = """
    (set-logic QF_LIA)
    (declare-const x Int)
    (declare-const y Int)
    (assert (= x 7))
    (assert (= y 3))
    (assert (= (+ x y) 10))
    (check-sat)
    """
    script = parser.parse(script_str)
    assert script.is_valid_syntax is True

    engine = SMTEngine()
    res = engine.solve_smtlib_script(script.raw_text)
    assert res.status == "sat"
    assert res.counterexample["x"] == 7
    assert res.counterexample["y"] == 3
