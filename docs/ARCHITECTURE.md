# System Architecture: `llm-z3-verifier`

This document details the multi-layered neurosymbolic software architecture of `llm-z3-verifier`.

---

## High-Level Architecture

```
+---------------------------------------------------------------+
|                      User & CLI Layer                         |
|      (python -m src.cli --demo | --mcts | --ramsey | --bench) |
+-------------------------------+-------------------------------+
                                |
                                v
+---------------------------------------------------------------+
|                 Generative & Translation Layer                |
|  - MockOfflineBackend (Deterministic Reference)               |
|  - OllamaBackend (Local Open-Weight LLMs)                     |
|  - OpenAIBackend (Cloud Frontier APIs)                        |
|  - SMTLibParser (S-expression Sanitizer & AST Validator)      |
+-------------------------------+-------------------------------+
                                |
                                v
+---------------------------------------------------------------+
|              Test-Time Search & PRM Supervision               |
|  - MCTSProofSearch (PUCT Action Selection)                    |
|  - SymbolicPRM (Step-by-Step Implication Scoring H => C)      |
|  - NeurosymbolicTreeSearch (Backtracking & Hard Pruning)      |
+-------------------------------+-------------------------------+
                                |
                                v
+---------------------------------------------------------------+
|                    Symbolic Engine Core                       |
|  - SMTEngine (Isolated z3.Context per query, Timeout Guard)   |
|  - Ramsey SAT Prover (K_5 vs K_6 Monochromatic Triangles)     |
|  - Theory Solvers: QF_LIA, QF_NRA, QF_BV                      |
+-------------------------------+-------------------------------+
                                |
                                v
+---------------------------------------------------------------+
|                 Stochastic Exploration Layer                  |
|  - MCMCStochasticExplorer (Metropolis-Hastings Pre-Filter)    |
|  - Simulated Annealing Cooling Schedule                       |
+---------------------------------------------------------------+
```

---

## Layer Breakdown

### 1. Generative & Translation Layer (`src/backends.py`, `src/smtlib_parser.py`)
- **`LLMBackend`:** Abstract base class specifying `generate()`, `formalize_conjecture()`, and `propose_proof_step()`.
- **`MockOfflineBackend`:** Contains the pre-compiled ground-truth SMT-LIB representations for the 20 benchmark conjectures and proof trajectories, allowing 100% offline, zero-token evaluation.
- **`SMTLibParser`:** Robust regex and S-expression parser that strips markdown fences, verifies parenthesis balance, identifies declared logics (`QF_LIA`, `QF_NRA`, `QF_NIA`), and compiles them into Z3 AST vectors.

### 2. Test-Time Search Layer (`src/mcts_search.py`, `src/tree_search.py`, `src/prm_verifier.py`)
- **`SymbolicPRM`:** Replaces noisy learned neural reward models with exact mathematical verification. For step $i$, it queries Z3 to evaluate $\text{UNSAT}(\mathcal{H}_i \land \neg C_i)$.
  - Sound: Returns $+1.0$.
  - Unsound: Returns $-1.0$ with counterexample dictionary.
- **`MCTSProofSearch`:** Employs the PUCT formula to balance prior generative confidence with symbolic reward. Automatically hard-prunes invalid branches ($R = -\infty$).
- **`ProofTreeVisualizer`:** Translates search trees directly into Mermaid flowcharts and JSON traces.

### 3. Symbolic Core (`src/smt_engine.py`, `src/ramsey.py`)
- **Hermetic Isolation:** Every query instantiates a dedicated `z3.Context()` to prevent cross-query symbol pollution and heuristic contamination.
- **Strict Timeouts:** Every solver instance enforces `solver.set("timeout", timeout_ms)` to avoid hanging on non-linear undecidable fragments.
- **Countermodel Extraction:** Automatically converts internal Z3 values (`RatNumRef`, `IntNumRef`, `BoolRef`) into native Python primitives (`float`, `int`, `bool`).

### 4. Stochastic Exploration Layer (`src/stochastic_sampler.py`)
- High-dimensional Metropolis-Hastings explorer designed to test constraint manifolds $f(x) \ge 0$ before invoking exact Cylindrical Algebraic Decomposition in Z3.
- If an empirical counterexample ($f(x) < 0$) is found, the solver bypasses heavy quantifier elimination.

---

## Directory Organization

```
llm-z3-verifier/
├── .github/workflows/ci.yml           # Automated CI workflow
├── docs/
│   ├── THEORY.md                      # Mathematical and decision procedure foundations
│   └── ARCHITECTURE.md                # System architecture documentation
├── pyproject.toml                     # Modern build metadata
├── Makefile                           # Developer CLI shortcuts
├── requirements.txt                   # Minimal pinned dependencies
├── LICENSE                            # MIT License
├── README.md                          # Main documentation & benchmark overview
│
├── src/                               # Core Source Code
│   ├── __init__.py
│   ├── backends.py                    # Mock, Ollama, and OpenAI backends
│   ├── smt_engine.py                  # Z3 SMT solver engine & context manager
│   ├── smtlib_parser.py               # SMT-LIB v2 parser and sanitizer
│   ├── verifier.py                    # Step-level proof auditor
│   ├── prm_verifier.py                # Symbolic Process Reward Model
│   ├── tree_search.py                 # Proof tree search with branch pruning
│   ├── mcts_search.py                 # MCTS proof search with PUCT
│   ├── ramsey.py                      # Ramsey R(3,3) theorem SAT prover
│   ├── stochastic_sampler.py          # MCMC Metropolis-Hastings explorer
│   ├── visualizer.py                  # Mermaid & JSON tree exporter
│   └── cli.py                         # Unified CLI entrypoint
│
├── examples/                          # 7 Executable Research Showcases
│   ├── 01_counterexample_search.py    # Discrete counterexample synthesis
│   ├── 02_proof_step_pruning.py       # Proof-step audit & branch pruning
│   ├── 03_stochastic_smt_hybrid.py    # MCMC stochastic falsification + SMT
│   ├── 04_ramsey_r33_theorem.py       # Formal proof of Ramsey R(3,3) = 6
│   ├── 05_mcts_proof_search.py        # MCTS proof search with Mermaid export
│   ├── 06_cauchy_schwarz_proof.py     # 3D Cauchy-Schwarz proof & equality test
│   └── 07_smtlib_raw_execution.py     # Raw SMT-LIB v2 string execution
│
├── benchmarks/                        # Benchmark & Evaluation Suite
│   ├── dataset.json                   # 20 benchmark conjectures across 5 domains
│   └── eval_suite.py                  # Evaluation metrics runner
│
└── tests/                             # 20 Automated Unit Tests (pytest)
    ├── test_mcts.py
    ├── test_ramsey.py
    ├── test_smt_engine.py
    ├── test_smtlib_parser.py
    ├── test_stochastic.py
    ├── test_tree_search.py
    ├── test_verifier.py
    └── test_visualizer.py
```
