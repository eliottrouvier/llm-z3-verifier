import pytest
from src.bitvectors import BitVectorEngine, BitVectorVerifier


def test_xor_swap_verification():
    bv = BitVectorEngine()
    for width in [8, 16, 32, 64]:
        res = bv.verify_xor_swap(width=width)
        assert res.is_valid is True
        assert res.is_sound is True
        assert res.status == "unsat"
        assert res.counterexample is None


def test_addition_signed_overflow():
    bv = BitVectorVerifier()
    # Signed 16-bit
    res16 = bv.check_addition_overflow(width=16, signed=True)
    assert res16.status == "sat"
    assert res16.counterexample["x"] == 32767  # 2^15 - 1

    # Signed 32-bit
    res32 = bv.check_addition_overflow(width=32, signed=True)
    assert res32.status == "sat"
    assert res32.counterexample["x"] == 2147483647  # 2^31 - 1


def test_addition_unsigned_overflow():
    bv = BitVectorEngine()
    res = bv.check_addition_overflow(width=8, signed=False)
    assert res.status == "sat"
    assert res.counterexample["x"] == 255  # 2^8 - 1


def test_power_of_two_hack():
    bv = BitVectorEngine()
    res = bv.verify_power_of_two_hack(width=16)
    assert res.is_valid is True
    assert res.status == "unsat"
    assert res.counterexample is None
