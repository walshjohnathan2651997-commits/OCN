"""Tests for the shared-threshold calibrator."""

from __future__ import annotations

import torch

from cese.constants import NUM_TIERS
from cese.models.shared_threshold_calibrator import SharedThresholdCalibrator


def test_calibrator_output_shapes():
    calib = SharedThresholdCalibrator(num_tiers=NUM_TIERS, num_dims=4)
    theta_claim = torch.randn(8, 4)
    theta_support = torch.randn(8, 4)
    out = calib(theta_claim, theta_support)
    assert out["claim_probs"].shape == (8, 4, NUM_TIERS)
    assert out["support_probs"].shape == (8, 4, NUM_TIERS)
    assert out["escalation_probs"].shape == (8, 4)


def test_escalation_probs_in_range():
    calib = SharedThresholdCalibrator(num_tiers=NUM_TIERS, num_dims=4)
    theta_claim = torch.randn(8, 4)
    theta_support = torch.randn(8, 4)
    out = calib(theta_claim, theta_support)
    ep = out["escalation_probs"]
    assert (ep >= 0).all() and (ep <= 1).all()


def test_higher_claim_than_support_increases_escalation():
    """When claim strength >> support strength, escalation prob should be high."""
    calib = SharedThresholdCalibrator(num_tiers=NUM_TIERS, num_dims=4)
    theta_claim = torch.full((4, 4), 5.0)
    theta_support = torch.full((4, 4), -5.0)
    out = calib(theta_claim, theta_support)
    assert out["escalation_probs"].mean() > 0.5


def test_lower_claim_than_support_decreases_escalation():
    """When claim strength << support strength, escalation prob should be low."""
    calib = SharedThresholdCalibrator(num_tiers=NUM_TIERS, num_dims=4)
    theta_claim = torch.full((4, 4), -5.0)
    theta_support = torch.full((4, 4), 5.0)
    out = calib(theta_claim, theta_support)
    assert out["escalation_probs"].mean() < 0.5


def test_get_thresholds_returns_two_sets():
    calib = SharedThresholdCalibrator(num_tiers=NUM_TIERS, num_dims=4)
    thresholds = calib.get_thresholds()
    # Shared thresholds: single (D, K-1) tensor shared by claim & support.
    assert thresholds.shape == (4, NUM_TIERS - 1)
    # Thresholds must be strictly increasing over m for each dim.
    diffs = thresholds[:, 1:] - thresholds[:, :-1]
    assert (diffs > 0).all()


def test_discrimination_positive():
    calib = SharedThresholdCalibrator(num_tiers=NUM_TIERS, num_dims=4)
    a = calib.get_discrimination()
    assert a.shape == (4,)
    assert (a > 0).all()


def test_higher_theta_shifts_mass_up():
    """Higher theta should shift probability mass to higher tiers."""
    calib = SharedThresholdCalibrator(num_tiers=NUM_TIERS, num_dims=4)
    theta_low = torch.full((2, 4), -3.0)
    theta_high = torch.full((2, 4), 3.0)
    out = calib(theta_high, theta_low)
    tiers = torch.arange(NUM_TIERS).float()
    exp_claim_high = (out["claim_probs"] * tiers).sum(dim=-1)
    exp_claim_low = calib(theta_low, theta_low)["claim_probs"]
    exp_claim_low = (exp_claim_low * tiers).sum(dim=-1)
    assert (exp_claim_high > exp_claim_low).all()


def test_severity_score_increases_with_gap():
    calib = SharedThresholdCalibrator(num_tiers=NUM_TIERS, num_dims=4, score_mode="severity")
    theta_claim = torch.full((2, 4), 5.0)
    theta_support_low = torch.full((2, 4), -5.0)
    theta_support_high = torch.full((2, 4), 5.0)
    score_low = calib(theta_claim, theta_support_low)["escalation_score"]
    score_high = calib(theta_claim, theta_support_high)["escalation_score"]
    assert (score_low > score_high).all()


def test_noisy_or_default_score_in_unit_interval():
    """Default escalation_aggregation='noisy_or' produces scores in [0,1]."""
    calib = SharedThresholdCalibrator(num_tiers=NUM_TIERS, num_dims=4)
    assert calib.escalation_aggregation == "noisy_or"
    torch.manual_seed(0)
    theta_claim = torch.randn(16, 4) * 3
    theta_support = torch.randn(16, 4) * 3
    out = calib(theta_claim, theta_support)
    score = out["escalation_score"]
    assert score.shape == (16,)
    assert (score >= 0).all() and (score <= 1).all()


def test_noisy_or_monotonic_in_per_dim_exceedance():
    """Raising per-dim exceedance (claim up / support down) must not
    decrease the global noisy-OR escalation score."""
    calib = SharedThresholdCalibrator(num_tiers=NUM_TIERS, num_dims=4)
    theta_support = torch.full((4, 4), -2.0)
    theta_claim_low = torch.full((4, 4), -1.0)
    theta_claim_high = torch.full((4, 4), 3.0)
    score_low = calib(theta_claim_low, theta_support)["escalation_score"]
    score_high = calib(theta_claim_high, theta_support)["escalation_score"]
    assert (score_high >= score_low - 1e-6).all()


def test_weighted_sum_ablation_mode():
    """escalation_aggregation='weighted_sum' is retained as an ablation."""
    calib = SharedThresholdCalibrator(
        num_tiers=NUM_TIERS, num_dims=4, escalation_aggregation="weighted_sum"
    )
    assert calib.escalation_aggregation == "weighted_sum"
    theta_claim = torch.full((2, 4), 5.0)
    theta_support = torch.full((2, 4), -5.0)
    out = calib(theta_claim, theta_support)
    # weighted_sum of per-dim exceedance probs (each <=1) with uniform 1/4
    # weights -> score in [0,1].
    assert (out["escalation_score"] >= 0).all()
    assert (out["escalation_score"] <= 1).all()


def test_calibration_modes_construct_different_params():
    """shared / separate / no_calibration expose different parameter sets."""
    shared = SharedThresholdCalibrator(num_tiers=NUM_TIERS, num_dims=4,
                                       calibration_mode="shared_threshold")
    sep = SharedThresholdCalibrator(num_tiers=NUM_TIERS, num_dims=4,
                                    calibration_mode="separate_thresholds")
    noc = SharedThresholdCalibrator(num_tiers=NUM_TIERS, num_dims=4,
                                    calibration_mode="no_calibration")
    # separate_thresholds has claim/support-specific params
    assert hasattr(sep, "raw_a_claim") and hasattr(sep, "raw_a_support")
    assert hasattr(sep, "raw_beta0_claim") and hasattr(sep, "raw_beta0_support")
    # shared does not
    assert not hasattr(shared, "raw_a_claim")
    # no_calibration has the linear logit head instead
    assert hasattr(noc, "tier_weight") and hasattr(noc, "tier_bias")
    assert not hasattr(shared, "tier_weight")


def test_separate_thresholds_forward_shapes():
    calib = SharedThresholdCalibrator(num_tiers=NUM_TIERS, num_dims=4,
                                      calibration_mode="separate_thresholds")
    theta_claim = torch.randn(4, 4)
    theta_support = torch.randn(4, 4)
    out = calib(theta_claim, theta_support)
    assert out["claim_probs"].shape == (4, 4, NUM_TIERS)
    assert out["support_probs"].shape == (4, 4, NUM_TIERS)
    assert out["escalation_score"].shape == (4,)


def test_no_calibration_forward_shapes():
    calib = SharedThresholdCalibrator(num_tiers=NUM_TIERS, num_dims=4,
                                      calibration_mode="no_calibration")
    theta_claim = torch.randn(4, 4)
    theta_support = torch.randn(4, 4)
    out = calib(theta_claim, theta_support)
    assert out["claim_probs"].shape == (4, 4, NUM_TIERS)
    assert out["support_probs"].shape == (4, 4, NUM_TIERS)
    # no_calibration has no cumulative-threshold layer -> p_ge_* are None
    assert out["p_ge_claim"] is None and out["p_ge_support"] is None
    # tier probs sum to 1 (softmax)
    s = out["claim_probs"].sum(dim=-1)
    assert torch.allclose(s, torch.ones_like(s), atol=1e-5)


def test_calibration_mode_changes_parameters():
    """Different calibration_mode values must produce different parameter sets.

    This verifies that the calibration_mode parameter is actually wired
    through to the calibrator's structure, not silently ignored.
    """
    shared = SharedThresholdCalibrator(
        num_tiers=NUM_TIERS, num_dims=4,
        calibration_mode="shared_threshold",
    )
    sep = SharedThresholdCalibrator(
        num_tiers=NUM_TIERS, num_dims=4,
        calibration_mode="separate_thresholds",
    )
    noc = SharedThresholdCalibrator(
        num_tiers=NUM_TIERS, num_dims=4,
        calibration_mode="no_calibration",
    )
    # shared: only raw_a, raw_beta0, delta
    assert hasattr(shared, "raw_a") and hasattr(shared, "raw_beta0")
    assert not hasattr(shared, "raw_a_claim") and not hasattr(shared, "tier_weight")
    # separate: has claim/support-specific params
    assert hasattr(sep, "raw_a_claim") and hasattr(sep, "raw_a_support")
    assert hasattr(sep, "raw_beta0_claim") and hasattr(sep, "raw_beta0_support")
    # no_calibration: has linear head (tier_weight, tier_bias) for direct
    # tier logits, bypassing the cumulative-threshold layer.
    assert hasattr(noc, "tier_weight") and hasattr(noc, "tier_bias")
    # The stored calibration_mode attribute matches what was passed.
    assert shared.calibration_mode == "shared_threshold"
    assert sep.calibration_mode == "separate_thresholds"
    assert noc.calibration_mode == "no_calibration"


def test_structural_params_stored_on_calibrator():
    """threshold_init, enforce_monotonic, margin must be stored on the
    calibrator so they can be recovered from a checkpoint.
    """
    calib = SharedThresholdCalibrator(
        num_tiers=NUM_TIERS, num_dims=4,
        threshold_init="uniform",
        enforce_monotonic=False,
        margin=0.7,
    )
    assert calib.threshold_init == "uniform"
    assert calib.enforce_monotonic is False
    assert calib.margin == 0.7


# ---------------------------------------------------------------------------
# Task 4: strict validation of score_mode / escalation_aggregation
# ---------------------------------------------------------------------------


def test_invalid_score_mode_raises():
    """Unknown score_mode must raise ValueError, not silently fall back."""
    import pytest
    with pytest.raises(ValueError, match="score_mode"):
        SharedThresholdCalibrator(num_tiers=NUM_TIERS, num_dims=4,
                                   score_mode="difference")


def test_invalid_escalation_aggregation_raises():
    """Unknown escalation_aggregation must raise ValueError."""
    import pytest
    with pytest.raises(ValueError, match="escalation_aggregation"):
        SharedThresholdCalibrator(num_tiers=NUM_TIERS, num_dims=4,
                                   escalation_aggregation="median")


def test_invalid_calibration_mode_raises():
    """Unknown calibration_mode must raise ValueError."""
    import pytest
    with pytest.raises(ValueError, match="calibration_mode"):
        SharedThresholdCalibrator(num_tiers=NUM_TIERS, num_dims=4,
                                   calibration_mode="weird_mode")


def test_max_aggregation_in_unit_interval():
    """max aggregation should produce a score in [0, 1] equal to max over D."""
    calib = SharedThresholdCalibrator(
        num_tiers=NUM_TIERS, num_dims=4,
        escalation_aggregation="max",
    )
    theta_claim = torch.randn(8, 4)
    theta_support = torch.randn(8, 4)
    out = calib(theta_claim, theta_support)
    score = out["escalation_score"]
    assert score.shape == (8,)
    assert (score >= 0).all() and (score <= 1).all()
    # max should be >= each per-dim value.
    assert (score >= out["p_exceed"].max(dim=-1).values - 1e-6).all()


def test_mean_aggregation_in_unit_interval():
    """mean aggregation should produce a score in [0, 1] equal to mean over D."""
    calib = SharedThresholdCalibrator(
        num_tiers=NUM_TIERS, num_dims=4,
        escalation_aggregation="mean",
    )
    theta_claim = torch.randn(8, 4)
    theta_support = torch.randn(8, 4)
    out = calib(theta_claim, theta_support)
    score = out["escalation_score"]
    assert score.shape == (8,)
    assert (score >= 0).all() and (score <= 1).all()
    assert torch.allclose(score, out["p_exceed"].mean(dim=-1), atol=1e-6)


def test_aggregation_modes_produce_different_scores():
    """noisy_or / weighted_sum / max / mean should generally differ."""
    theta_claim = torch.randn(8, 4)
    theta_support = torch.randn(8, 4)
    scores = {}
    for mode in ("noisy_or", "weighted_sum", "max", "mean"):
        calib = SharedThresholdCalibrator(
            num_tiers=NUM_TIERS, num_dims=4,
            escalation_aggregation=mode,
        )
        out = calib(theta_claim, theta_support)
        scores[mode] = out["escalation_score"]
    # At least two modes should differ on this batch.
    diffs = []
    keys = list(scores.keys())
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            diffs.append((scores[keys[i]] - scores[keys[j]]).abs().sum().item())
    assert max(diffs) > 1e-6, "all aggregation modes produced identical scores"
    # All scores in [0, 1].
    for s in scores.values():
        assert (s >= 0).all() and (s <= 1).all()
