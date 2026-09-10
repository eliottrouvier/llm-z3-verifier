#!/usr/bin/env python3
"""
Root entry point for llm-z3-verifier.
Forwards CLI arguments to src.cli.main().
"""

import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cli import main

if __name__ == "__main__":
    main()
