"""Tests for top-level package exports."""

import src


def test_package_exports():
    expected_exports = {
        "__version__",
        "__author__",
        "ProofVerifier",
        "ProofStep",
        "VerificationReport",
        "SMTEngine",
        "SMTResult",
        "MCTSProofSearch",
        "MCTSNode",
        "MCTSResult",
    }
    assert set(src.__all__) == expected_exports
    for name in expected_exports:
        assert hasattr(src, name)
