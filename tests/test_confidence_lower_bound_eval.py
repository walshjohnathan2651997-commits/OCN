"""Tests for confidence lower-bound loss and evaluation metrics.

Task 4 acceptance:
- confidence_lower_bound_loss returns p_exceed_observed, p_exceed_lower,
  interval_width, bound, violation.
- Lowering evidence should not lower exceedance (monotonicity of the
  lower bound).
- evaluate_model.py computes confidence_lower_bound_safety_rate and
  extraction_sensitive_rate.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from cese.losses.confidence_lower_bound import (
    compute_evidence_lower_bound,
    confidence_lower_bound_loss,
)
from cese.eval.cese_metrics import confidence_lower_bound_safety_rate


# ---------------------------------------------------------------------------
# Test 1: loss returns all required fields
# ---------------------------------------------------------------------------


def test_loss_returns_all_required_fields():
    """confidence_lower_bound_loss must return all 5 documented fields."""
    B, D = 4, 5
    p_exceed = torch.rand(B, D)
    p_exceed_lower = torch.rand(B, D)
    ev = torch.rand(B, 8)
    ec = torch.rand(B, 8)
    ev_lower = compute_evidence_lower_bound(ev, ec)

    result = confidence_lower_bound_loss(p_exceed, p_exceed_lower, ev, ev_lower, ec)

    required_keys = {
        "loss",
        "p_exceed_observed",
        "p_exceed_lower",
        "p_exceed_observed_mean",
        "p_exceed_lower_mean",
        "interval_width",
        "bound",
        "violation",
    }
    assert required_keys.issubset(result.keys()), (
        f"missing keys: {required_keys - result.keys()}"
    )
    # loss is a scalar tensor.
    assert result["loss"].dim() == 0
    # p_exceed_observed / p_exceed_lower have shape (B, D).
    assert result["p_exceed_observed"].shape == (B, D)
    assert result["p_exceed_lower"].shape == (B, D)
    # Means and per-sample fields are 1-D (B,).
    assert result["p_exceed_observed_mean"].shape == (B,)
    assert result["p_exceed_lower_mean"].shape == (B,)
    assert result["interval_width"].shape == (B,)
    assert result["bound"].shape == (B,)
    assert result["violation"].shape == (B,)


# ---------------------------------------------------------------------------
# Test 2: lowering evidence should not lower exceedance
# ---------------------------------------------------------------------------


def test_lowering_evidence_does_not_lower_exceedance():
    """When p_exceed_lower >= p_exceed (lower evidence -> higher exceedance),
    the violation should be zero.
    """
    B, D = 4, 5
    # Lower-bound exceedance is higher than observed (correct direction).
    p_exceed = torch.full((B, D), 0.3)
    p_exceed_lower = torch.full((B, D), 0.5)
    ev = torch.rand(B, 8)
    ec = torch.rand(B, 8)
    ev_lower = compute_evidence_lower_bound(ev, ec)

    result = confidence_lower_bound_loss(p_exceed, p_exceed_lower, ev, ev_lower, ec)

    # No violation because p_observed <= p_lower.
    assert result["violation"].sum().item() == 0.0
    assert result["loss"].item() == 0.0
    # interval_width = p_low - p_obs >= 0.
    assert (result["interval_width"] >= 0).all()


def test_violation_when_observed_exceeds_lower():
    """When p_exceed > p_exceed_lower (wrong direction), violation > 0."""
    B, D = 4, 5
    p_exceed = torch.full((B, D), 0.7)
    p_exceed_lower = torch.full((B, D), 0.3)
    # Use identical evidence vectors so the bound is zero, making the
    # violation purely from the exceedance difference.
    ev = torch.full((B, 8), 0.5)
    ev_lower = ev.clone()
    ec = torch.full((B, 8), 1.0)  # q=1 -> (1-q)=0 -> bound=0

    result = confidence_lower_bound_loss(p_exceed, p_exceed_lower, ev, ev_lower, ec)

    # Violation should be positive (bound=0, so violation = p_obs - p_low).
    assert result["violation"].sum().item() > 0.0
    assert result["loss"].item() > 0.0


# ---------------------------------------------------------------------------
# Test 3: margin parameter increases violation threshold
# ---------------------------------------------------------------------------


def test_margin_increases_violation():
    """A positive margin should increase the violation threshold."""
    B, D = 4, 5
    p_exceed = torch.full((B, D), 0.5)
    p_exceed_lower = torch.full((B, D), 0.4)
    ev = torch.rand(B, 8)
    ec = torch.rand(B, 8)
    ev_lower = compute_evidence_lower_bound(ev, ec)

    result_no_margin = confidence_lower_bound_loss(
        p_exceed, p_exceed_lower, ev, ev_lower, ec, margin=0.0
    )
    result_with_margin = confidence_lower_bound_loss(
        p_exceed, p_exceed_lower, ev, ev_lower, ec, margin=0.2
    )

    # With margin, violation should be >= without margin.
    assert result_with_margin["violation"].sum().item() >= result_no_margin["violation"].sum().item()


# ---------------------------------------------------------------------------
# Test 4: confidence_lower_bound_safety_rate metric
# ---------------------------------------------------------------------------


def test_safety_rate_all_safe():
    """When p_exceed >= p_exceed_lower - bound for all samples, rate = 1.0."""
    N, D = 10, 5
    p_exceed = np.full((N, D), 0.5)
    p_exceed_lower = np.full((N, D), 0.3)
    ev = np.random.rand(N, 8)
    ev_lower = ev - 0.1  # small perturbation

    rate = confidence_lower_bound_safety_rate(p_exceed, p_exceed_lower, ev, ev_lower)
    assert rate == 1.0


def test_safety_rate_some_unsafe():
    """When p_exceed < p_exceed_lower - bound for some samples, rate < 1.0."""
    N, D = 10, 5
    p_exceed = np.full((N, D), 0.3)
    p_exceed_lower = np.full((N, D), 0.7)
    ev = np.random.rand(N, 8)
    ev_lower = ev.copy()  # zero perturbation -> bound = 0

    rate = confidence_lower_bound_safety_rate(p_exceed, p_exceed_lower, ev, ev_lower)
    # All samples unsafe because p_exceed < p_exceed_lower with zero bound.
    assert rate == 0.0


# ---------------------------------------------------------------------------
# Test 5: compute_evidence_lower_bound reduces evidence
# ---------------------------------------------------------------------------


def test_evidence_lower_bound_reduces_evidence():
    """e_lower should be <= e_tilde for all dims."""
    ev = torch.rand(4, 8)
    ec = torch.rand(4, 8)
    e_lower = compute_evidence_lower_bound(ev, ec)

    assert (e_lower <= ev + 1e-7).all(), "e_lower should not exceed e_tilde"
    assert (e_lower >= 0).all(), "e_lower should be clamped to [0, 1]"


def test_evidence_lower_bound_zero_confidence_maximally_reduces():
    """When confidence q=0, e_lower = e_tilde - lambda_conf."""
    ev = torch.full((1, 8), 0.8)
    ec = torch.zeros(1, 8)
    e_lower = compute_evidence_lower_bound(ev, ec, lambda_conf=0.5)

    # e_lower = 0.8 - 0.5 * (1 - 0) = 0.3
    assert torch.allclose(e_lower, torch.full((1, 8), 0.3), atol=1e-6)
