"""Tests for cese.eval.constraint_eval.compute_monotonic_violation_from_model.

Task 3 acceptance:
- A deliberately non-monotonic fake evidence branch must yield
  violation_rate > 0.
- A monotonic fake evidence branch must yield violation_rate == 0.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
import torch
import torch.nn as nn

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from cese.constants import CLAIM_DIMS, EVIDENCE_DIMS
from cese.eval.constraint_eval import compute_monotonic_violation_from_model


# ---------------------------------------------------------------------------
# Fake evidence branch: maps (evidence_vector, evidence_confidence) -> theta_support
# ---------------------------------------------------------------------------


class MonotonicEvidenceBranch(nn.Module):
    """Evidence branch that is monotonic by construction.

    theta_support = sum of evidence dims (more evidence -> higher theta).
    """

    def forward(self, evidence_vector: torch.Tensor, evidence_confidence: torch.Tensor) -> torch.Tensor:
        # theta_support shape (B, D) where D = len(CLAIM_DIMS).
        # Use the sum of evidence_vector as the latent strength for all dims.
        strength = evidence_vector.sum(dim=-1, keepdim=True)  # (B, 1)
        return strength.expand(-1, len(CLAIM_DIMS))  # (B, D)


class NonMonotonicEvidenceBranch(nn.Module):
    """Evidence branch that is deliberately non-monotonic.

    theta_support decreases when evidence increases (inverted), so
    higher evidence yields lower p_ge_support -> violations.
    """

    def forward(self, evidence_vector: torch.Tensor, evidence_confidence: torch.Tensor) -> torch.Tensor:
        # Inverted: more evidence -> lower theta.
        strength = -evidence_vector.sum(dim=-1, keepdim=True)
        return strength.expand(-1, len(CLAIM_DIMS))


# ---------------------------------------------------------------------------
# Fake calibrator: simple sigmoid on theta
# ---------------------------------------------------------------------------


class FakeCalibrator(nn.Module):
    """Minimal calibrator producing p_ge_support = sigmoid(theta - beta).

    This mimics SharedThresholdCalibrator._cumulative_probs with a=1, beta=0.
    Higher theta -> higher p_ge_support (monotonic in theta).
    """

    def __init__(self, num_tiers: int = 5):
        super().__init__()
        self.num_tiers = num_tiers
        # beta thresholds for K-1 tiers.
        self.register_buffer("beta", torch.linspace(0.2, 0.8, num_tiers - 1))

    def forward(self, theta_claim: torch.Tensor, theta_support: torch.Tensor) -> dict:
        # p_ge_support: (B, D, K-1) = sigmoid(theta_support - beta)
        # theta_support: (B, D), beta: (K-1,)
        z = theta_support.unsqueeze(-1) - self.beta.unsqueeze(0).unsqueeze(0)
        p_ge_support = torch.sigmoid(z)
        return {"p_ge_support": p_ge_support}


# ---------------------------------------------------------------------------
# Fake model wrapper
# ---------------------------------------------------------------------------


class FakeModel(nn.Module):
    def __init__(self, evidence_branch, calibrator):
        super().__init__()
        self.evidence_branch = evidence_branch
        self.calibrator = calibrator


# ---------------------------------------------------------------------------
# Fake loader
# ---------------------------------------------------------------------------


class FakeLoader:
    """Yields batches with evidence_vector and evidence_confidence."""

    def __init__(self, n_samples: int = 16, ev_dim: int = 8, batch_size: int = 4):
        rng = torch.Generator().manual_seed(42)
        self.batches = []
        for i in range(0, n_samples, batch_size):
            n = min(batch_size, n_samples - i)
            ev = torch.rand(n, ev_dim, generator=rng)
            ec = torch.rand(n, ev_dim, generator=rng)
            self.batches.append({"evidence_vector": ev, "evidence_confidence": ec})

    def __iter__(self):
        return iter(self.batches)


# ---------------------------------------------------------------------------
# Mapping: each claim dim maps to all evidence dims
# ---------------------------------------------------------------------------

EXPERT_MAPPING = {k: list(EVIDENCE_DIMS) for k in CLAIM_DIMS}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_non_monotonic_branch_has_violations():
    """A non-monotonic (inverted) evidence branch must yield violation_rate > 0."""
    model = FakeModel(NonMonotonicEvidenceBranch(), FakeCalibrator())
    loader = FakeLoader(n_samples=16, batch_size=4)
    result = compute_monotonic_violation_from_model(
        model, loader, mapping=EXPERT_MAPPING, device="cpu"
    )
    assert result["monotonic_violation_rate"] > 0, (
        f"expected violation_rate > 0 for non-monotonic branch, "
        f"got {result['monotonic_violation_rate']}"
    )
    # Per-dim should also show violations.
    for dim_name, rate in result["monotonic_violation_by_dim"].items():
        assert rate > 0, f"dim {dim_name} expected > 0, got {rate}"
    assert result["n_pairs"] > 0


def test_monotonic_branch_has_no_violations():
    """A monotonic evidence branch must yield violation_rate == 0."""
    model = FakeModel(MonotonicEvidenceBranch(), FakeCalibrator())
    loader = FakeLoader(n_samples=16, batch_size=4)
    result = compute_monotonic_violation_from_model(
        model, loader, mapping=EXPERT_MAPPING, device="cpu"
    )
    assert result["monotonic_violation_rate"] == 0, (
        f"expected violation_rate == 0 for monotonic branch, "
        f"got {result['monotonic_violation_rate']}"
    )
    for dim_name, rate in result["monotonic_violation_by_dim"].items():
        assert rate == 0, f"dim {dim_name} expected 0, got {rate}"


def test_empty_loader_returns_nan():
    """An empty loader must return NaN violation rate."""
    model = FakeModel(MonotonicEvidenceBranch(), FakeCalibrator())
    loader = FakeLoader(n_samples=0, batch_size=4)
    result = compute_monotonic_violation_from_model(
        model, loader, mapping=EXPERT_MAPPING, device="cpu"
    )
    assert np.isnan(result["monotonic_violation_rate"])
    assert result["n_pairs"] == 0
