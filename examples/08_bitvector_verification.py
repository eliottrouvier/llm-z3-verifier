#!/usr/bin/env python3
"""
Example 08: Bit-Vector (QF_BV) Formal Verification & Machine Overflow Discovery.
Demonstrates:
1. Exact machine overflow detection (disproving x + 1 > x on 32-bit/64-bit integers).
2. Universal verification of the classic XOR swap algorithm: x^=y, y^=x, x^=y.
3. Proof of the power-of-two bitwise hack: (x & (x - 1)) == 0 for all 2^32 words.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.bitvectors import BitVectorEngine


def main():
    print("=" * 75)
    print("Example 08: Bit-Vector (QF_BV) Formal Verification & Machine Overflows")
    print("=" * 75)

    engine = BitVectorEngine()

    # [1] Machine Overflow Detection
    print("\n[Case 1] Auditing Naive Claim: 'For all machine integers x, x + 1 > x'")
    for width in [16, 32, 64]:
        res_overflow = engine.check_addition_overflow(width=width, signed=True)
        print(f"\n  Checking {width}-bit Signed Integer Arithmetic:")
        print(f"  Result: {res_overflow.status.upper()} (Counterexample Synthesized)")
        ce = res_overflow.counterexample
        print(f"    Counterexample x : {ce['x']} (0x{ce['x']:0{width//4}X})")
        print(f"    Evaluated x + 1  : {ce['x_next']}")
        print(f"    Explanation      : {res_overflow.explanation}")

    # [2] XOR Swap Identity Proof
    print("\n" + "-" * 75)
    print("[Case 2] Proving XOR Swap Algorithm for In-Place Register Exchange")
    res_xor = engine.verify_xor_swap(width=32)
    print(f"  Z3 Solver Status: {res_xor.status.upper()}")
    print(f"  Theorem Proved  : {res_xor.is_valid}")
    print(f"  Explanation     : {res_xor.explanation}")

    # [3] Power-of-Two Bitwise Hack Proof
    print("\n" + "-" * 75)
    print("[Case 3] Formally Proving the Power-of-Two Bithack: x & (x - 1) == 0")
    res_bithack = engine.verify_power_of_two_hack(width=32)
    print(f"  Z3 Solver Status: {res_bithack.status.upper()}")
    print(f"  Theorem Proved  : {res_bithack.is_valid}")
    print(f"  Explanation     : {res_bithack.explanation}")


if __name__ == "__main__":
    main()
