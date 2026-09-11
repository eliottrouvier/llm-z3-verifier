.PHONY: help install test demo benchmark mcts ramsey clean

PYTHON ?= python3

help:
	@echo "llm-z3-verifier development commands:"
	@echo "  make install    Install dependencies in current environment"
	@echo "  make test       Run all unit tests via pytest"
	@echo "  make demo       Run all core showcases"
	@echo "  make benchmark  Run 20-problem neurosymbolic benchmark suite"
	@echo "  make mcts       Run MCTS proof search with PRM"
	@echo "  make ramsey     Run Ramsey R(3,3)=6 formal proof"
	@echo "  make clean      Clean pycache and build artifacts"

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

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
