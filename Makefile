.PHONY: help install test demo benchmark mcts ramsey serve bitvectors invariants lean profile clean

PYTHON ?= python3

help:
	@echo "llm-z3-verifier development commands:"
	@echo "  make install     Install dependencies in current environment"
	@echo "  make test        Run all unit tests via pytest"
	@echo "  make demo        Run all core showcases"
	@echo "  make benchmark   Run 20-problem neurosymbolic benchmark suite"
	@echo "  make mcts        Run MCTS proof search with PRM"
	@echo "  make ramsey      Run Ramsey R(3,3)=6 formal proof"
	@echo "  make serve       Start local interactive Web dashboard on :8080"
	@echo "  make bitvectors  Run QF_BV bit-vector verification"
	@echo "  make invariants  Run loop invariant induction"
	@echo "  make lean        Synthesize Lean 4 theorem code"
	@echo "  make profile     Run Z3 tactic and memory profiler"
	@echo "  make clean       Clean pycache and build artifacts"

install:
	pip install -r requirements.txt

test:
	$(PYTHON) -m pytest tests/ -v

demo:
	$(PYTHON) -m src.cli --demo

benchmark:
	$(PYTHON) -m src.cli --benchmark

mcts:
	$(PYTHON) -m src.cli --mcts

ramsey:
	$(PYTHON) -m src.cli --ramsey

serve:
	$(PYTHON) -m src.cli --serve 8080

bitvectors:
	$(PYTHON) -m src.cli --bitvectors

invariants:
	$(PYTHON) -m src.cli --invariants

lean:
	$(PYTHON) -m src.cli --lean

profile:
	$(PYTHON) benchmarks/profiler.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
