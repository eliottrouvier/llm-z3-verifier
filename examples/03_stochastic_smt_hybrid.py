#!/usr/bin/env python3
"""
Example 03: Stochastic MCMC Exploration + Exact SMT Verification Hybrid.
Demonstrates the synergy between continuous stochastic search (Metropolis-Hastings)
and symbolic formal methods (Z3) on non-linear constraint domains.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.stochastic_sampler import MCMCStochasticExplorer
from src.smt_engine import SMTEngine


def main():
    print("----------------------------------------------------------------------")
    print("Example 3: MCMC Stochastic Falsification + Z3 Exact SMT Certification")
    print("----------------------------------------------------------------------")

    # Non-linear 2D objective function with a subtle local minimum that violates f(x, y) >= 0
    # Function: f(x, y) = (x - 2.5)^2 + (y + 1.2)^2 - 0.25
    # The claim: "For all (x, y) in [-5, 5]^2, f(x, y) >= 0"
    def objective(p):
        x, y = p[0], p[1]
        return (x - 2.5)**2 + (y + 1.2)**2 - 0.25

    bounds = [(-5.0, 5.0), (-5.0, 5.0)]
    param_names = ["x", "y"]

    print("Target Claim: For all (x, y) in [-5, 5]^2, (x - 2.5)^2 + (y + 1.2)^2 >= 0.25.")
    print("-> Phase 1: High-Speed Stochastic MCMC Exploration (Metropolis-Hastings)...")

    explorer = MCMCStochasticExplorer(seed=42)
    mcmc_res = explorer.falsify_constraint(
        objective_fn=objective,
        bounds=bounds,
        param_names=param_names,
        num_iterations=800,
        initial_temp=1.5,
        cooling_rate=0.99
    )

    if mcmc_res.falsified:
        print("  [MCMC Discovery] Empirical violation discovered!")
        print(f"  Samples Evaluated: {mcmc_res.samples_evaluated}")
        print(f"  Candidate Counterexample: x = {mcmc_res.empirical_counterexample['x']:.5f}, "
              f"y = {mcmc_res.empirical_counterexample['y']:.5f}")
        print(f"  Observed Value: {mcmc_res.min_energy_found:.6f} (< 0 => Violation)")
    else:
        print("  [MCMC Discovery] No empirical violation detected in sample budget.")

    print("\n-> Phase 2: Exact Formal SMT Certification (Z3 Non-Linear Real Arithmetic)...")
    smt = SMTEngine()
    cert_res = smt.find_counterexample(
        var_specs={"x": "Real", "y": "Real"},
        domain_constraints=["x >= -5", "x <= 5", "y >= -5", "y <= 5"],
        negated_claims=["(x - 2.5)*(x - 2.5) + (y + 1.2)*(y + 1.2) - 0.25 < 0"]
    )

    if cert_res.status == "sat":
        print("  [Z3 Formal Proof] SAT - Claim formally disproved with exact real model:")
        print(f"  Model: x = {cert_res.counterexample['x']}, y = {cert_res.counterexample['y']}")
    elif cert_res.status == "unsat":
        print("  [Z3 Formal Proof] UNSAT - Claim formally verified!")


if __name__ == "__main__":
    main()
