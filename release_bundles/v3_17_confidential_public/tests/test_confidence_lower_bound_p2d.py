"""Tests for P2d: confidence-aware lower bound with per-feature rho_j."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cese.losses.confidence_lower_bound import (
    compute_evidence_lower_bound,
    confidence_lower_bound_loss,
    compute_lower_bound_diagnostics,
    exceedance_from_probs,
)


def test_compute_evidence_lower_bound_with_scalar_rho():
    """Scalar rho should behave like lambda_conf."""
    ev = torch.tensor([[0.8, 0.6, 0.4]])
    ec = torch.tensor([[1.0, 0.5, 0.0]])
    # rho=0.5, q=1.0 -> no reduction; q=0.5 -> reduce by 0.25; q=0 -> reduce by 0.5
    e_lower = compute_evidence_lower_bound(ev, ec, rho=0.5)
    expected = torch.tensor([[0.8, 0.35, 0.0]])  # 0.6-0.25, 0.4-0.5 clamped to 0
    assert torch.allclose(e_lower, expected, atol=1e-6)


def test_compute_evidence_lower_bound_with_per_feature_rho():
    """Per-feature rho should apply different sensitivity per dim."""
    ev = torch.tensor([[0.8, 0.6]])
    ec = torch.tensor([[0.5, 0.5]])  # q=0.5 -> (1-q)=0.5
    rho = torch.tensor([0.2, 0.8])
    e_lower = compute_evidence_lower_bound(ev, ec, rho=rho)
    # dim 0: 0.8 - 0.2*0.5 = 0.7
    # dim 1: 0.6 - 0.8*0.5 = 0.2
    expected = torch.tensor([[0.7, 0.2]])
    assert torch.allclose(e_lower, expected, atol=1e-6)


def test_compute_evidence_lower_bound_backward_compatible():
    """lambda_conf should still work (backward compatible)."""
    ev = torch.tensor([[0.8]])
    ec = torch.tensor([[0.5]])
    e_lower = compute_evidence_lower_bound(ev, ec, lambda_conf=0.5)
    expected = torch.tensor([[0.55]])  # 0.8 - 0.5*0.5
    assert torch.allclose(e_lower, expected, atol=1e-6)


def test_confidence_lower_bound_loss_with_rho():
    """confidence_lower_bound_loss should accept rho and evidence_confidence."""
    B, D = 4, 4
    p_exceed = torch.rand(B, D)
    p_exceed_lower = torch.rand(B, D) + 0.1  # higher (more conservative)
    ev = torch.rand(B, 8)
    e_lower = ev - 0.1
    ec = torch.rand(B, 8)
    rho = torch.tensor([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8])
    result = confidence_lower_bound_loss(
        p_exceed, p_exceed_lower, ev, e_lower, ec, rho=rho, L_f=1.0,
    )
    assert "loss" in result
    assert "bound" in result
    assert "violation" in result
    assert result["loss"].dim() == 0  # scalar
    assert result["bound"].shape == (B,)


def test_confidence_lower_bound_loss_bound_uses_rho():
    """The theoretical bound should be L_f * sum_j rho_j * (1 - q_j)."""
    B = 1
    p_exceed = torch.zeros(B, 4)
    p_exceed_lower = torch.zeros(B, 4)
    ev = torch.ones(B, 8)
    e_lower = torch.zeros(B, 8)
    ec = torch.tensor([[0.5] * 8])  # (1-q)=0.5 for all
    rho = torch.tensor([1.0] * 8)  # rho=1 for all
    result = confidence_lower_bound_loss(
        p_exceed, p_exceed_lower, ev, e_lower, ec, rho=rho, L_f=2.0,
    )
    # bound = L_f * sum_j rho_j * (1 - q_j) = 2.0 * 8 * 1.0 * 0.5 = 8.0
    assert torch.allclose(result["bound"], torch.tensor([8.0]), atol=1e-6)


def test_compute_lower_bound_diagnostics_outputs():
    """compute_lower_bound_diagnostics should return all required metrics."""
    B, D = 10, 4
    p_exceed = torch.rand(B, D)
    p_exceed_lower = p_exceed + 0.05  # lower bound is higher
    ec = torch.rand(B, 8)
    rho = torch.tensor([0.5] * 8)
    diag = compute_lower_bound_diagnostics(
        p_exceed, p_exceed_lower, ec, rho=rho, L_f=1.0, review_threshold=0.1,
    )
    expected_keys = {
        "observed_exceedance", "lower_bound_exceedance",
        "interval_width_mean", "interval_width_p90",
        "extraction_sensitive_rate", "lower_bound_coverage",
        "human_review_rate", "lipschitz_diagnostic_bound",
    }
    assert set(diag.keys()) == expected_keys
    for v in diag.values():
        assert isinstance(v, float)
    # lower_bound_exceedance should be >= observed (we added 0.05)
    assert diag["lower_bound_exceedance"] >= diag["observed_exceedance"] - 1e-6
    # coverage should be 1.0 (all samples have lower >= observed)
    assert diag["lower_bound_coverage"] == 1.0


def test_compute_lower_bound_diagnostics_review_rate():
    """human_review_rate should reflect samples with interval > threshold."""
    B, D = 10, 4
    p_exceed = torch.zeros(B, D)
    # 5 samples have interval 0.2 (> 0.1 threshold), 5 have 0.0
    p_exceed_lower = torch.zeros(B, D)
    p_exceed_lower[:5] = 0.2
    ec = torch.ones(B, 8)  # q=1 -> (1-q)=0 -> no bound
    diag = compute_lower_bound_diagnostics(
        p_exceed, p_exceed_lower, ec, rho=0.5, L_f=1.0, review_threshold=0.1,
    )
    # 5 out of 10 samples should be flagged -> review_rate = 0.5
    assert diag["human_review_rate"] == pytest.approx(0.5, abs=1e-6)
    assert diag["extraction_sensitive_rate"] == pytest.approx(0.5, abs=1e-6)
