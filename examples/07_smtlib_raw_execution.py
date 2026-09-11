#!/usr/bin/env python3
"""
Example 07: Raw SMT-LIB v2 Script Parsing, Sanitization, and Direct Execution.
Demonstrates:
- Accepting raw LLM-generated SMT-LIB v2 strings with markdown wrappers.
- Syntax validation and parenthesis balance checking.
- Direct execution through Z3 AST parser and model extraction.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.smtlib_parser import SMTLibParser
from src.smt_engine import SMTEngine


def main():
    print("=" * 75)
    print("Example 07: Raw SMT-LIB v2 Parsing & Direct Solver Execution")
    print("=" * 75)

    # Typical raw LLM output with comments and markdown fences
    raw_llm_output = """
```smt2
; Mathematical Conjecture: Integer Pythagorean Triples with Odd Hypotenuse
; Searching for a^2 + b^2 = c^2 such that c is odd and a, b > 0
(set-logic QF_NIA)

(declare-const a Int)
(declare-const b Int)
(declare-const c Int)

(assert (> a 0))
(assert (> b 0))
(assert (> c 0))
(assert (= (+ (* a a) (* b b)) (* c c)))
(assert (= (mod c 2) 1))
(assert (<= c 25))

(check-sat)
(get-model)
```
"""
    print("Input Raw Script from LLM:")
    print(raw_llm_output.strip())
    print("\n-> Parsing and sanitizing SMT-LIB v2 syntax...")

    parser = SMTLibParser()
    script = parser.parse(raw_llm_output)

    print(f"  Valid Syntax? {script.is_valid_syntax}")
    print(f"  Detected Logic: {script.logic}")
    print(f"  Constants Declared: {script.declared_constants}")

    if not script.is_valid_syntax:
        print(f"  Syntax Error: {script.syntax_error}")
        return

    print("\n-> Executing script directly in Z3...")
    engine = SMTEngine()
    result = engine.solve_smtlib_script(script.raw_text)

    print(f"  Solver Status: {result.status.upper()}")
    if result.status == "sat":
        print("  -> SAT: Solution Synthesized!")
        print(f"     Model: {result.counterexample}")
        m = result.counterexample
        a, b, c = m.get("a", 0), m.get("b", 0), m.get("c", 0)
        print(f"     Check: {a}^2 + {b}^2 = {a*a + b*b} == {c}^2 = {c*c} (c={c} is odd)")


if __name__ == "__main__":
    main()
