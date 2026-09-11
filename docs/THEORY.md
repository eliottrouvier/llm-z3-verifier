# Theoretical Foundations of Neurosymbolic SMT Verification

**Author:** Eliott Rouvier  
**Focus:** Frontier Mathematical Reasoning, SMT Solving & Process Supervision

---

## Abstract

Purely autoregressive Large Language Models (LLMs) generate mathematical text through token probability distribution modeling. While capable of synthesizing plausible heuristics, they fundamentally lack internal mechanisms for sound deductive verification, leading to exponential error accumulation over multi-step proofs:
$$P(\text{Proof Sound}) \approx (1 - \epsilon)^T \xrightarrow{T \to \infty} 0$$
where $\epsilon$ is the step failure probability and $T$ is proof depth.

`llm-z3-verifier` establishes a neurosymbolic framework that bridges generative heuristics with exact formal verification. This document provides the mathematical foundations of the architecture, detailing DPLL(T) decision procedures, the Nelson-Oppen combination framework, symbolic Process Reward Modeling (PRM), and test-time tree search pruning.

---

## 1. Satisfiability Modulo Theories (SMT) & DPLL(T)

### 1.1 Propositional Core: CDCL
At the core of modern SMT solvers is Conflict-Driven Clause Learning (CDCL). Given a propositional formula in Conjunctive Normal Form (CNF):
$$\Phi = \bigwedge_{i=1}^m \left( \bigvee_{j=1}^{k_i} l_{i,j} \right)$$
CDCL performs:
1. **Boolean Constraint Propagation (BCP):** Unit propagation via the two-watched-literals scheme.
2. **Conflict Analysis:** Constructing an implication graph to identify the First Unique Implication Point (1-UIP).
3. **Non-chronological Backtracking:** Jumping back multiple decision levels and appending the learned conflict clause to the formula.

### 1.2 The DPLL(T) Modular Architecture
DPLL(T) decouples propositional reasoning from domain-specific mathematical theories $T$. The formula $\Phi$ contains atoms over a first-order signature $\Sigma$.

A propositional abstraction maps first-order atoms to Boolean variables:
$$\alpha: \text{Atom}(\Sigma) \to \text{Bool}$$
The CDCL engine finds satisfying Boolean assignments $M_B$. The theory solver $T$-Solver verifies whether the conjunction of first-order literals corresponding to $M_B$ is $T$-satisfiable:
$$\bigwedge_{l \in M_B} \alpha^{-1}(l) \models_T \bot$$
If $T$-unsatisfiable, the $T$-Solver extracts an infeasible subset (minimal unsat core) and generates an explanation clause $\neg M_B'$, which is fed back to the CDCL engine as a learned lemma.

---

## 2. Theory Solvers & Decision Procedures

`llm-z3-verifier` interfaces with three primary theories supported by the Z3 theorem prover:

### 2.1 Quantifier-Free Linear Integer Arithmetic ($\text{QF\_LIA}$)
Formulas contain linear combinations of integer variables:
$$\sum_{i=1}^n a_i x_i \le b, \quad a_i, b, x_i \in \mathbb{Z}$$
Decided via the **Dual Simplex algorithm** combined with **Branch-and-Bound** and **Gomory's Cutting Planes**:
- The linear relaxation over $\mathbb{R}$ is solved using tableau pivots.
- If the optimal real solution contains fractional values $x_j = f \notin \mathbb{Z}$, a cutting plane or disjunction is generated:
  $$(x_j \le \lfloor f \rfloor) \lor (x_j \ge \lceil f \rceil)$$

### 2.2 Quantifier-Free Non-Linear Real Arithmetic ($\text{QF\_NRA}$)
Formulas contain polynomial equalities and inequalities over $\mathbb{R}$:
$$P(x_1, \dots, x_n) \ge 0, \quad P \in \mathbb{R}[x_1, \dots, x_n]$$
By Tarski's theorem (1948), the first-order theory of real closed fields admits quantifier elimination and is decidable. Z3 implements **NLSAT (Non-Linear Conflict-Driven Solving)** and **Cylindrical Algebraic Decomposition (CAD)**:
- Projects $n$-dimensional semi-algebraic sets into lower dimensions using sub-resultants.
- Isolates real algebraic roots using Sturm-Habicht sequences.
- Lifts sign-invariant cylindrical cells back to $\mathbb{R}^n$.

### 2.3 Theory Combination: Nelson-Oppen Method
When reasoning over formulas spanning multiple disjoint theories (e.g. arithmetic + uninterpreted functions $T_E \cup T_{\mathbb{Z}}$), `llm-z3-verifier` relies on the Nelson-Oppen combination theorem:
- **Condition:** Theories $T_1, T_2$ must be signature-disjoint ($\Sigma_1 \cap \Sigma_2 = \emptyset$) and stably infinite.
- **Purification:** Variables are introduced to separate mixed terms into pure literals.
- **Equality Sharing:** Solvers exchange deduced variable equalities:
  $$T_1 \models (x = y) \implies \text{Propagate } (x = y) \text{ to } T_2$$

---

## 3. The Neurosymbolic Verification Loop

### 3.1 Step-Level Implication Audit (Process Supervision)
A mathematical proof consists of a sequence of deduction steps. Let $\mathcal{H} = \{H_1, \dots, H_k\}$ denote active hypotheses and axioms, and let $C$ denote the proposed deduction step.

The deduction is formally sound if and only if:
$$\mathcal{H} \models_{\Sigma} C \iff \left( \bigwedge_{i=1}^k H_i \right) \implies C \quad \text{is universally valid}$$

By the refutation completeness of SMT:
$$\text{Valid}(\mathcal{H} \implies C) \iff \text{UNSAT}\left( \bigwedge_{i=1}^k H_i \land \neg C \right)$$

Two outcomes are decidable by Z3:
1. **Outcome 1 (UNSAT):** No assignment satisfies $\mathcal{H} \land \neg C$. The deduction is **sound**.
2. **Outcome 2 (SAT):** Z3 synthesizes a concrete model $\mathcal{M}$:
   $$\mathcal{M} \models \left( \bigwedge_{i=1}^k H_i \land \neg C \right)$$
   $\mathcal{M}$ assigns exact values to all variables where all premises hold, but the conclusion $C$ is **false**. This model constitutes an irrefutable counterexample disproving the step.

---

## 4. Monte Carlo Tree Search with Hard Pruning

To search over mathematical deduction trajectories, we employ MCTS with PUCT action selection (AlphaZero/o1 style) combined with formal Process Reward Modeling (PRM):

### 4.1 Node Selection via PUCT
At state node $s$, action $a$ (candidate deduction step) is selected to maximize:
$$a^* = \arg\max_a \left[ Q(s, a) + c_{\text{puct}} \cdot P(s, a) \cdot \frac{\sqrt{\sum_b N(s, b)}}{1 + N(s, a)} \right]$$
where:
- $Q(s, a)$ is the expected verification value of the branch.
- $P(s, a)$ is the generative prior proposed by the LLM.
- $N(s, a)$ is the visit count.

### 4.2 Symbolic PRM Reward Function
Rather than employing a learned neural scalar reward subject to reward hacking, the reward $R(s, a)$ is computed strictly by Z3:
$$R(s, a) = \begin{cases} +1.0 & \text{if } \text{UNSAT}(\mathcal{H}_s \land \neg C_a) \quad [\text{Sound Step}] \\ -\infty & \text{if } \text{SAT}(\mathcal{H}_s \land \neg C_a) \quad [\text{Unsound / Prune}] \\ 0.0 & \text{if } \text{UNKNOWN / Timeout} \end{cases}$$

### 4.3 Hard Pruning & Backpropagation
When $R(s, a) = -\infty$:
1. The node is marked `pruned = True`.
2. The countermodel $\mathcal{M}$ is attached to the node.
3. The value is backpropagated up the ancestral path:
   $$W(s) \leftarrow W(s) - 1.0, \quad N(s) \leftarrow N(s) + 1$$
4. Subsequent simulations are mathematically prevented from exploring subtrees rooted at $a$, eliminating compute waste on invalid derivations.

---

## 5. Stochastic MCMC Pre-Filtering

For high-degree non-linear systems where CAD latency can scale doubly exponentially with the number of variables ($\mathcal{O}(d^{2^n})$), `llm-z3-verifier` deploys a Metropolis-Hastings MCMC explorer as a fast-path filter:

Given constraint $f(x) \ge 0$, we define an energy surface:
$$E(x) = f(x)$$
A violation occurs whenever $E(x) < 0$.

1. **Proposal:** $x' \sim \mathcal{N}(x, \sigma^2 I)$.
2. **Metropolis Acceptance:**
   $$\alpha(x, x') = \min\left(1, \exp\left(-\frac{E(x') - E(x)}{T}\right)\right)$$
3. **Cooling Schedule:** $T_{k+1} = \gamma T_k$ with $\gamma = 0.99$.

If MCMC discovers a point $x^*$ with $E(x^*) < 0$ in $< 50$ iterations, the conjecture is empirically falsified in $< 5\text{ ms}$, bypassing full CAD decomposition. If no violation is found, the exact Z3 solver is invoked for sound certification.

---

## References

1. **Nelson, G., & Oppen, D. C.** (1979). *Simplification by cooperating decision procedures.* ACM TOPLAS, 1(2), 245-257.
2. **Nieuwenhuis, R., Oliveras, A., & Tinelli, C.** (2006). *Solving SAT and SAT modulo theories: From an abstract Davis--Putnam--Logemann--Loveland procedure to DPLL(T).* JACM, 53(6), 937-977.
3. **De Moura, L., & Bjørner, N.** (2008). *Z3: An efficient SMT solver.* TACAS 2008, LNCS 4963, 337-340.
4. **Lightman, H., et al.** (2023). *Let's Verify Step by Step.* OpenAI Technical Report, arXiv:2305.20050.
5. **Jovanović, D., & de Moura, L.** (2012). *Solving non-linear arithmetic using partial cylindrical algebraic decomposition.* TACAS 2012, 102-116.
