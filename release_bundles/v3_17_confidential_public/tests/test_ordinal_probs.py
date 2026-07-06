"""Tests for ordinal probability outputs."""

from __future__ import annotations

import torch

from cese.constants import NUM_TIERS
from cese.models.ordinal import SharedThresholdOrdinalLayer


def test_probs_sum_to_one():
    layer = SharedThresholdOrdinalLayer(num_tiers=NUM_TIERS, num_dims=4)
    theta = torch.randn(8, 4)
    probs = layer(theta)
    assert probs.shape == (8, 4, NUM_TIERS)
    sums = probs.sum(dim=-1)
    assert torch.allclose(sums, torch.ones_like(sums), atol=1e-5)


def test_probs_non_negative():
    layer = SharedThresholdOrdinalLayer(num_tiers=NUM_TIERS, num_dims=4)
    theta = torch.randn(8, 4)
    probs = layer(theta)
    assert (probs >= 0).all()


def test_higher_theta_shifts_mass_right():
    """Higher latent strength should shift probability mass to higher tiers."""
    layer = SharedThresholdOrdinalLayer(num_tiers=NUM_TIERS, num_dims=1)
    theta_low = torch.tensor([[-2.0]])
    theta_high = torch.tensor([[2.0]])
    probs_low = layer(theta_low)
    probs_high = layer(theta_high)
    # Expected tier should be higher for theta_high.
    tiers = torch.arange(NUM_TIERS).float()
    exp_low = (probs_low[0, 0] * tiers).sum()
    exp_high = (probs_high[0, 0] * tiers).sum()
    assert exp_high > exp_low


def test_shared_thresholds_same_across_dims():
    """When shared=True, thresholds are identical across claim dimensions."""
    layer = SharedThresholdOrdinalLayer(num_tiers=NUM_TIERS, num_dims=4, shared=True)
    thresholds = layer.get_thresholds()
    assert thresholds.shape == (NUM_TIERS - 1,)
    # Strictly increasing.
    assert (thresholds[1:] > thresholds[:-1]).all()


def test_per_dim_thresholds_different():
    """When shared=False, thresholds can differ across dimensions."""
    layer = SharedThresholdOrdinalLayer(num_tiers=NUM_TIERS, num_dims=4, shared=False)
    thresholds = layer.get_thresholds()
    assert thresholds.shape == (4, NUM_TIERS - 1)


def test_monotonic_enforced():
    """With enforce_monotonic=True, thresholds are strictly increasing."""
    layer = SharedThresholdOrdinalLayer(
        num_tiers=NUM_TIERS, num_dims=4, enforce_monotonic=True
    )
    thresholds = layer.get_thresholds()
    if thresholds.dim() == 1:
        assert (thresholds[1:] > thresholds[:-1]).all()
    else:
        for d in range(thresholds.shape[0]):
            assert (thresholds[d, 1:] > thresholds[d, :-1]).all()
