"""Unit tests for MCMCStochasticExplorer."""

import numpy as np
from src.stochastic_sampler import MCMCStochasticExplorer


def test_mcmc_falsification_success():
    explorer = MCMCStochasticExplorer(seed=42)
    # Target function: f(x) = x^2 - 4. Falsifiable when x in [-1, 1] since f(x) <= -3 < 0
    fn = lambda p: p[0]**2 - 4.0
    bounds = [(-3.0, 3.0)]

    res = explorer.falsify_constraint(
        objective_fn=fn,
        bounds=bounds,
        param_names=["x"],
        num_iterations=200
    )

    assert res.falsified
    assert res.empirical_counterexample is not None
    assert res.min_energy_found < 0


def test_mcmc_strictly_positive():
    explorer = MCMCStochasticExplorer(seed=42)
    # Target function: f(x) = x^2 + 1. Strictly >= 1 > 0 everywhere
    fn = lambda p: p[0]**2 + 1.0
    bounds = [(-5.0, 5.0)]

    res = explorer.falsify_constraint(
        objective_fn=fn,
        bounds=bounds,
        param_names=["x"],
        num_iterations=100
    )

    assert not res.falsified
    assert res.empirical_counterexample is None
    assert res.min_energy_found >= 1.0
