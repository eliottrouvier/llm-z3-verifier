"""Unit tests for Ramsey R(3,3) theorem verification."""

import pytest
from src.ramsey import check_ramsey


def test_ramsey_k5_sat():
    """K_5 can be 2-colored without a monochromatic triangle (R(3,3) > 5)."""
    status, coloring = check_ramsey(5, 3)
    assert status == "SAT"
    assert coloring is not None
    assert len(coloring) == 10  # 10 edges in K_5


def test_ramsey_k6_unsat():
    """K_6 CANNOT be 2-colored without a monochromatic triangle (R(3,3) <= 6)."""
    status, coloring = check_ramsey(6, 3)
    assert status == "UNSAT"
    assert coloring is None
