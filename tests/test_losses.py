"""Tests for loss functions."""

from __future__ import annotations

import torch

from cese.constants import NUM_TIERS, R_EXPERT
from cese.losses import (
    CesEOcnLoss,
    cese_ordinal_loss,
    cumulative_link_loss,
    cumulative_bce_loss,
    monotonicity_loss,
    perturb_evidence_pairs,
    ordinal_exceedance_loss,
    truncation_loss,
    compute_max_support_tiers,
    apply_strict_cap,
    confidence_lower_bound_loss,
    compute_evidence_lower_bound,
)
from cese.models.shared_threshold_calibrator import SharedThresholdCalibrator


def _make_probs(B=4, D=4, K=NUM_TIERS):
    logits = torch.randn(B, D, K)
    return torch.softmax(logits, dim=-1)


def test_cumulative_link_loss_positive():
    probs = _make_probs()
    targets = torch.randint(0, NUM_TIERS, (4, 4))
    loss = cumulative_link_loss(probs, targets, NUM_TIERS)
    assert loss.item() > 0


def test_cumulative_bce_loss_positive():
    p_ge = torch.sigmoid(torch.randn(4, 4, NUM_TIERS - 1))
    targets = torch.randint(0, NUM_TIERS, (4, 4))
    loss = cumulative_bce_loss(p_ge, targets, NUM_TIERS)
    assert loss.item() > 0


def test_cese_ordinal_loss():
    claim_probs = _make_probs()
    support_probs = _make_probs()
    claim_tiers = torch.randint(0, NUM_TIERS, (4, 4))
    support_tiers = torch.randint(0, NUM_TIERS, (4, 4))
    loss = cese_ordinal_loss(
        claim_probs, support_probs, claim_tiers, support_tiers, NUM_TIERS
    )
    assert loss.item() > 0


def test_ordinal_exceedance_loss():
    esc_probs = torch.rand(4, 4)
    labels = torch.randint(0, 2, (4, 4))
    loss = ordinal_exceedance_loss(esc_probs, labels)
    assert loss.item() >= 0


def test_monotonicity_loss_zero_when_high_geq_low():
    """When high evidence yields >= cumulative prob, loss ~0."""
    p_ge_low = torch.zeros(2, 4, NUM_TIERS - 1)
    p_ge_high = torch.ones(2, 4, NUM_TIERS - 1)
    loss = monotonicity_loss(p_ge_low, p_ge_high)
    assert loss.item() < 1e-5


def test_monotonicity_loss_positive_when_low_exceeds_high():
    p_ge_low = torch.ones(2, 4, NUM_TIERS - 1)
    p_ge_high = torch.zeros(2, 4, NUM_TIERS - 1)
    loss = monotonicity_loss(p_ge_low, p_ge_high)
    assert loss.item() > 0.5


def test_perturb_evidence_pairs():
    ev = torch.rand(3, 8)
    conf = torch.rand(3, 8)
    ev_low, ev_high, mask = perturb_evidence_pairs(ev, conf, R_EXPERT)
    assert ev_low.shape == (3, 4, 8)
    assert ev_high.shape == (3, 4, 8)
    assert mask.any()
    # High should be >= low on activated dims.
    assert (ev_high >= ev_low - 1e-6).all()


def test_truncation_loss_zero_when_within_cap():
    """When support mass is below the cap, truncation ~0."""
    support_probs = torch.zeros(2, 4, NUM_TIERS)
    support_probs[..., 0] = 1.0  # mass at tier 0
    max_tiers = torch.full((2, 4), 2, dtype=torch.long)
    loss = truncation_loss(support_probs, max_tiers, NUM_TIERS)
    assert loss.item() < 1e-5


def test_truncation_loss_positive_when_above_cap():
    support_probs = torch.zeros(2, 4, NUM_TIERS)
    support_probs[..., NUM_TIERS - 1] = 1.0  # mass at top tier
    max_tiers = torch.full((2, 4), 2, dtype=torch.long)
    loss = truncation_loss(support_probs, max_tiers, NUM_TIERS)
    assert loss.item() > 0.5


def test_compute_max_support_tiers_caps():
    ev = torch.zeros(2, 8)
    conf = torch.zeros(2, 8)
    claim_tiers = torch.zeros(2, 4)
    # causal dim (idx 1) tier 3, low causal_id evidence -> cap
    claim_tiers[:, 1] = 3
    max_tiers = compute_max_support_tiers(ev, conf, claim_tiers)
    assert max_tiers[0, 1].item() == 2
    # scope dim (idx 0) not capped
    assert max_tiers[0, 0].item() == NUM_TIERS - 1


def test_apply_strict_cap_renormalizes():
    support_probs = torch.ones(2, 4, NUM_TIERS) / NUM_TIERS
    max_tiers = torch.full((2, 4), 2, dtype=torch.long)
    capped = apply_strict_cap(support_probs, max_tiers, NUM_TIERS)
    # Mass above tier 2 should be zero.
    assert capped[..., 3:].sum().item() < 1e-6
    assert torch.allclose(capped.sum(dim=-1), torch.ones(2, 4), atol=1e-5)


def test_confidence_lower_bound_loss():
    p_exceed = torch.rand(4, 4)
    p_exceed_lower = p_exceed + 0.1  # lower evidence => higher escalation
    ev = torch.rand(4, 8)
    ec = torch.full((4, 8), 0.5)
    e_lower = compute_evidence_lower_bound(ev, ec)
    res = confidence_lower_bound_loss(p_exceed, p_exceed_lower, ev, e_lower, ec)
    assert res["loss"].item() >= 0
    # bound is (B,), not a scalar.
    assert (res["bound"] >= 0).all()
    # Shapes per the documented API.
    assert res["p_exceed_observed"].shape == (4, 4)
    assert res["p_exceed_lower"].shape == (4, 4)
    assert res["p_exceed_observed_mean"].shape == (4,)
    assert res["p_exceed_lower_mean"].shape == (4,)
    assert res["bound"].shape == (4,)
    assert res["violation"].shape == (4,)
    assert res["interval_width"].shape == (4,)


def test_total_loss_returns_components():
    calib = SharedThresholdCalibrator(num_tiers=NUM_TIERS, num_dims=4)
    theta_claim = torch.randn(4, 4)
    theta_support = torch.randn(4, 4)
    out = calib(theta_claim, theta_support)
    loss_fn = CesEOcnLoss(num_tiers=NUM_TIERS, ordinal_mode="bce")
    loss_dict = loss_fn(
        outputs=out,
        claim_tiers=torch.randint(0, NUM_TIERS, (4, 4)),
        support_tiers=torch.randint(0, NUM_TIERS, (4, 4)),
        escalation_labels=torch.randint(0, 2, (4,)),
        evidence_vector=torch.rand(4, 8),
        evidence_confidence=torch.rand(4, 8),
    )
    assert "total" in loss_dict
    assert "ordinal" in loss_dict
    assert "escalation" in loss_dict
    assert loss_dict["total"].item() > 0


def test_global_escalation_loss_uses_sample_labels():
    """P2a: sample-level BCE must use escalation_labels directly, not
    per-dim labels derived from claim_tiers > support_tiers.
    """
    from cese.losses.ordinal_losses import global_escalation_loss

    # escalation_score close to label -> low loss.
    score = torch.tensor([0.9, 0.1, 0.8, 0.2])
    labels = torch.tensor([1, 0, 1, 0])
    low_loss = global_escalation_loss(score, labels)

    # escalation_score far from label -> high loss.
    bad_score = torch.tensor([0.1, 0.9, 0.2, 0.8])
    high_loss = global_escalation_loss(bad_score, labels)

    assert low_loss.item() < high_loss.item()


def test_total_loss_has_global_and_dim_components():
    """P2a: loss dict must include global_escalation and dim_exceedance."""
    calib = SharedThresholdCalibrator(num_tiers=NUM_TIERS, num_dims=4)
    theta_claim = torch.randn(4, 4)
    theta_support = torch.randn(4, 4)
    out = calib(theta_claim, theta_support)
    loss_fn = CesEOcnLoss(
        num_tiers=NUM_TIERS,
        ordinal_mode="bce",
        global_escalation_weight=1.0,
        dim_exceedance_weight=0.5,
    )
    loss_dict = loss_fn(
        outputs=out,
        claim_tiers=torch.randint(0, NUM_TIERS, (4, 4)),
        support_tiers=torch.randint(0, NUM_TIERS, (4, 4)),
        escalation_labels=torch.tensor([1, 0, 1, 0]),
        evidence_vector=torch.rand(4, 8),
        evidence_confidence=torch.rand(4, 8),
    )
    assert "global_escalation" in loss_dict
    assert "dim_exceedance" in loss_dict
    assert "escalation" in loss_dict
    # escalation = global_escalation_weight * global + dim_exceedance_weight * dim
    g = loss_dict["global_escalation"]
    d = loss_dict["dim_exceedance"]
    expected = 1.0 * g + 0.5 * d
    actual = loss_dict["escalation"]
    assert torch.allclose(actual, expected, atol=1e-5)


def test_dim_exceedance_zero_weight_disables_per_dim():
    """When dim_exceedance_weight=0, only sample-level BCE is used."""
    calib = SharedThresholdCalibrator(num_tiers=NUM_TIERS, num_dims=4)
    out = calib(torch.randn(4, 4), torch.randn(4, 4))
    loss_fn = CesEOcnLoss(
        num_tiers=NUM_TIERS,
        ordinal_mode="bce",
        global_escalation_weight=1.0,
        dim_exceedance_weight=0.0,
    )
    loss_dict = loss_fn(
        outputs=out,
        claim_tiers=torch.randint(0, NUM_TIERS, (4, 4)),
        support_tiers=torch.randint(0, NUM_TIERS, (4, 4)),
        escalation_labels=torch.tensor([1, 0, 1, 0]),
        evidence_vector=torch.rand(4, 8),
        evidence_confidence=torch.rand(4, 8),
    )
    # dim_exceedance should be 0, escalation == global_escalation.
    assert loss_dict["dim_exceedance"] == 0.0
    assert torch.allclose(
        loss_dict["escalation"], loss_dict["global_escalation"], atol=1e-5
    )
