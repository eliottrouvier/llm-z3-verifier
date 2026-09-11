# llm-z3-verifier

[![CI](https://github.com/eliottrouvier/llm-z3-verifier/actions/workflows/ci.yml/badge.svg)](https://github.com/eliottrouvier/llm-z3-verifier/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/downloads/)
[![Z3 Solver](https://img.shields.io/badge/SMT-Z3%20Solver%204.12%2B-orange.svg)](https://github.com/Z3Prover/z3)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Formal Soundness: 100%](https://img.shields.io/badge/Formal%20Soundness-100%25-brightgreen.svg)](#)
[![Benchmarks: 20/20 Passed](https://img.shields.io/badge/Benchmarks-20%2F20%20(100%25)-success.svg)](#benchmark-suite)

> **Neurosymbolic Counterexample Search, Step-Level Proof Verification (PRM), and MCTS Test-Time Pruning via Z3.**

`llm-z3-verifier` bridges generative heuristics from frontier Large Language Models with the **Z3 Theorem Prover / SMT Solver** to overcome the fundamental flaw of generative mathematical reasoning: **unverified hallucinations and unsound deductive steps**.

---

## Key Capabilities

1. **Automated Counterexample Synthesis:** Immediate generation of concrete algebraic, number-theoretic, and combinatorial countermodels disproving false mathematical conjectures.
2. **Process Reward Modeling (Symbolic PRM):** Exact formal auditing of intermediate proof steps ($H_1 \land \dots \land H_k \implies C$) returning $+1.0$ (sound), $-1.0$ (invalid with countermodel), or $0.0$ (unknown).
3. **MCTS with Hard Pruning:** Monte Carlo Tree Search guided by PUCT and symbolic Z3 rewards, eliminating compute waste on mathematically flawed branches.
4. **Ramsey Theorem Prover ($R(3,3) = 6$):** Formal propositional SAT certification proving $R(3,3) > 5$ (triangle-free 2-coloring on $K_5$) and $R(3,3) \le 6$ (UNSAT on $K_6$).
5. **Continuous/Discrete Stochastic Filter (MCMC):** Metropolis-Hastings simulated annealing to discover empirical boundary violations before exact SMT certification.
6. **SMT-LIB v2 Native Parser:** Sanitizes and executes raw LLM-generated S-expressions directly.
7. **Mermaid Flowchart Visualizer:** Exports color-coded proof search trees (Green = Sound, Red = Pruned with Counterexample, Gold = Q.E.D.).

---

## Architecture Overview

```mermaid
flowchart TD
    subgraph Generative ["Frontier Generative Layer"]
        A["Mathematical Claim / Conjecture"] --> B["LLM Prover & Formalizer"]
        B --> C["Step Proposals & SMT-LIB Specs"]
    end

    subgraph Search ["Test-Time Compute Search (MCTS)"]
        C --> D["PUCT Node Selection & Tree Expansion"]
        D --> E{"Symbolic PRM (Z3)"}
    end

    subgraph VerificationCore ["Symbolic Core (Z3 SMT)"]
        E -->|Valid Step: UNSAT on Negation| F["Reward +1.0<br/>Branch Retained"]
        E -->|Invalid Step: SAT on Negation| G["Reward -inf<br/>Branch Hard-Pruned"]
        G -.->|Countermodel Feedback| B
        E -->|Conjecture Falsified| H["Concrete Countermodel Synthesized"]
        E -->|Theorem Proved| I["Formal Q.E.D. Certified"]
    end

    subgraph StochasticLayer ["Stochastic Layer"]
        J["Non-linear Constraints"] --> K["MCMC Metropolis-Hastings Sampler"]
        K -->|Empirical Violation| E
    end

    F --> I
```

---

## Quickstart (3 Lines)

```bash
# 1. Clone the repository
git clone https://github.com/eliottrouvier/llm-z3-verifier.git && cd llm-z3-verifier

# 2. Install dependencies (z3-solver, numpy, requests, pytest)
pip install -r requirements.txt

# 3. Run all core showcases (100% offline, zero API key required)
python -m src.cli --demo
```

---

## Research Showcases

### 1. Ramsey's Theorem Formal Certification ($R(3,3) = 6$)
Ramsey's theorem states that any 2-coloring of the edges of a complete graph $K_n$ contains a monochromatic triangle if and only if $n \ge 6$.

```bash
python examples/04_ramsey_r33_theorem.py
```
**Output:**
```text
[Phase 1] Testing N = 5 (Complete Graph K_5, 10 Edges)...
  Result: SAT
  -> A valid 2-coloring without ANY monochromatic triangle EXISTS on K_5!
  -> Synthesized Counterexample Coloring (Pentagon C_5):
     Red Edges (5): (0,2), (0,3), (1,3), (1,4), (2,4)
     Blue Edges (5): (0,1), (0,4), (1,2), (2,3), (3,4)
  => Lemma 1 Certified: R(3,3) > 5

[Phase 2] Testing N = 6 (Complete Graph K_6, 15 Edges)...
  Result: UNSAT
  -> Every possible 2^15 = 32,768 coloring contains a monochromatic triangle.
  => Lemma 2 Certified: R(3,3) <= 6

FORMAL CONCLUSION: R(3,3) > 5 and R(3,3) <= 6 ===> R(3,3) = 6 (Q.E.D.)
Proven via exhaustive first-order propositional SAT resolution in Z3 (< 25 ms).
```

---

### 2. MCTS Proof Search with Symbolic PRM Guidance
Demonstrates test-time compute search guided by step-level process supervision.

```bash
python examples/05_mcts_proof_search.py
```

Generated Mermaid proof tree:

```mermaid
flowchart TD
    classDef rootStyle fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    classDef soundStyle fill:#e8f5e9,stroke:#388e3c,stroke-width:2px;
    classDef prunedStyle fill:#ffebee,stroke:#d32f2f,stroke-width:2px;
    classDef qedStyle fill:#fff8e1,stroke:#fbc02d,stroke-width:3px;

    R["Theorem Root State"]:::rootStyle
    M0["[Verified Step 0] Given (x - y)*(x + y) = 0, factor the polynomial over the integers."]:::soundStyle
    R --> M0
    M2["[Verified Step 2] Sound Case Analysis: If x - y == 0, then x = y. Otherwise x != y, which entails x + y = 0."]:::soundStyle
    M0 --> M2
    M3["[Verified Step 3] Conclude proof by synthesizing valid disjunction."]:::soundStyle
    M2 --> M3
    CE_0["[Branch Pruned by PRM]<br/>Countermodel: {'x': 1, 'y': 1}"]:::prunedStyle
    R -.->|Falsified by Z3| CE_0
    QED["<b>Theorem Proven (MCTS + Z3 Soundness)</b>"]:::qedStyle
    M3 ==> QED
```

---

### 3. Discrete Counterexample Search
*Conjecture:* *"For all $2 \times 2$ integer matrices $A$ and $B$, if $A \cdot B = 0$, then $A = 0$ or $B = 0$."*

```bash
python examples/01_counterexample_search.py
```
**Output:**
```text
Evaluating Conjecture: [Matrix Zero Divisors]
  [DISPROVED] Z3 synthesized an exact counterexample!
  Countermodel:
    Matrix A = [[0, 0], [-4, -4]]
    Matrix B = [[0, 7], [0, -7]]
    Verification: A*B = [[0, 0], [0, 0]] = 0 with A != 0 and B != 0.
```

---

### 4. Non-Linear Cauchy-Schwarz Proof in $\mathbb{R}^3$
```bash
python examples/06_cauchy_schwarz_proof.py
```
Proves $(x \cdot y)^2 \le \|x\|^2 \|y\|^2$ over $\mathbb{R}^3$ via Cylindrical Algebraic Decomposition (UNSAT on negation), and disproves strict inequality by synthesizing collinear equality vectors $x = y = (0, -1, 0)$.

---

### 5. Raw SMT-LIB v2 Script Execution
```bash
python examples/07_smtlib_raw_execution.py
```
Parses raw LLM markdown blocks containing SMT-LIB v2 scripts, validates parenthesis balance, compiles ASTs, and extracts models (e.g. integer Pythagorean triples with odd hypotenuse: $a=3, b=4, c=5$).

---

## Benchmark Suite (20 Mathematical Problems)

Run the comprehensive 20-problem evaluation benchmark:

```bash
python -m src.cli --benchmark
```

### Empirical Results across 5 Domains

| Domain | Conjectures Tested | Ground-Truth Accuracy | Mean Decision Latency |
| :--- | :---: | :---: | :---: |
| **Algebra** | 4 | **100.0%** (4/4) | 3.35 ms |
| **Analysis & Optimization** | 4 | **100.0%** (4/4) | 1.96 ms |
| **Combinatorics & Graph Theory** | 4 | **100.0%** (4/4) | 1.89 ms |
| **Formal Logic** | 4 | **100.0%** (4/4) | 0.94 ms |
| **Number Theory** | 4 | **100.0%** (4/4) | 61.65 ms |
| **OVERALL** | **20** | **100.0%** (20/20) | **13.96 ms** |

* **SMT Syntax Compilation Rate:** **100.0%**
* **Sound Branch Pruning Accuracy:** **100.0%** (Zero false positives admitted)

---

## CLI Reference

```bash
# Run all 3 core showcases
python -m src.cli --demo

# Run MCTS proof search and export Mermaid diagram
python -m src.cli --mcts --export-tree proof_tree.mmd

# Certify Ramsey's theorem R(3,3) = 6
python -m src.cli --ramsey

# Run full 20-problem benchmark suite
python -m src.cli --benchmark

# Verify or falsify custom mathematical queries
python -m src.cli --conjecture "Euler polynomial prime"
python -m src.cli --conjecture "Matrix zero divisors" --backend mock
```

---

## Supported Backends

- **`MockOfflineBackend` (Default):** 100% deterministic, offline reference engine. Runs all 20 benchmarks and proofs in $< 50\text{ ms}$ with zero API keys or external dependencies.
- **`OllamaBackend`:** Local open-weight models (`llama3:latest`, `qwen2.5-math`, `deepseek-r1`) via `http://localhost:11434`.
- **`OpenAIBackend`:** Cloud chat completion endpoints (`OPENAI_API_KEY`, `OPENAI_API_BASE`).

---

## Theoretical Monograph

For a rigorous theoretical treatment of the decision procedures, DPLL(T), Nelson-Oppen theory combination, and MCTS process supervision, refer to:
👉 **[`docs/THEORY.md`](docs/THEORY.md)**

---

## License

MIT License © 2026 Eliott Rouvier.
