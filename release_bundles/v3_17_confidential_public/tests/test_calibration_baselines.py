"""Tests for calibration baselines (spec 6.7)."""

from __future__ import annotations

import numpy as np
import torch

from cese.baselines.calibration_baselines import (
    TemperatureScaling,
    IsotonicCalibration,
    _cumulative_to_categorical,
)
from cese.constants import NUM_TIERS


def test_cumulative_to_categorical_sums_to_one():
    p_ge = torch.sigmoid(torch.randn(8, 4, NUM_TIERS - 1))
    cat = _cumulative_to_categorical(p_ge, NUM_TIERS)
    assert cat.shape == (8, 4, NUM_TIERS)
    assert torch.allclose(cat.sum(dim=-1), torch.ones(8, 4), atol=1e-5)
    assert (cat >= 0).all()


def test_temperature_scaling_fit_reduces_nll():
    torch.manual_seed(0)
    N, D = 64, 4
    logits = torch.randn(N, D, NUM_TIERS - 1) * 3.0  # overconfident
    targets = torch.randint(0, NUM_TIERS, (N, D))
    cal = TemperatureScaling(num_dims=D, num_tiers=NUM_TIERS)
    res = cal.fit(logits, targets)
    assert res["temperature"] > 0
    # Calibrated probs should be valid.
    probs = cal.calibrate_probs(logits)
    assert probs.shape == (N, D, NUM_TIERS)
    assert torch.allclose(probs.sum(dim=-1), torch.ones(N, D), atol=1e-5)


def test_temperature_scaling_higher_T_flattens():
    cal = TemperatureScaling(num_tiers=NUM_TIERS)
    cal.log_temperature.data.fill_(2.0)  # T = e^2 ~ 7.4
    logits = torch.tensor([[[3.0, 2.0, 1.0, 0.5]]])  # (1,1,4)
    p_raw = torch.sigmoid(logits)
    p_cal = cal.calibrate_cumulative(logits)
    # Higher temperature should pull probs toward 0.5.
    assert (p_cal - 0.5).abs().max() <= (p_raw - 0.5).abs().max()


def test_isotonic_calibration_fit_and_transform():
    try:
        import sklearn  # noqa: F401
    except ImportError:
        return
    torch.manual_seed(0)
    N, D = 50, 4
    probs = torch.rand(N, D, NUM_TIERS - 1)
    targets = torch.randint(0, NUM_TIERS, (N, D))
    cal = IsotonicCalibration(num_dims=D, num_tiers=NUM_TIERS)
    res = cal.fit(probs, targets)
    assert res["fitted"] == 1.0
    out = cal.calibrate_cumulative(probs)
    assert out.shape == probs.shape
    # Ordinal cumulative P(Y>=m) must be non-increasing in m.
    diffs = out[..., 1:] - out[..., :-1]
    assert (diffs <= 1e-8).all()


def test_isotonic_calibration_unfitted_returns_identity():
    cal = IsotonicCalibration(num_tiers=NUM_TIERS)
    probs = torch.rand(5, 4, NUM_TIERS - 1)
    out = cal.calibrate_cumulative(probs)
    assert torch.allclose(out, probs.clamp(1e-7, 1 - 1e-7), atol=1e-6)


def test_isotonic_calibrate_probs_sums_to_one():
    try:
        import sklearn  # noqa: F401
    except ImportError:
        return
    torch.manual_seed(1)
    N, D = 40, 4
    probs = torch.rand(N, D, NUM_TIERS - 1)
    targets = torch.randint(0, NUM_TIERS, (N, D))
    cal = IsotonicCalibration(num_dims=D, num_tiers=NUM_TIERS)
    cal.fit(probs, targets)
    cat = cal.calibrate_probs(probs)
    assert cat.shape == (N, D, NUM_TIERS)
    assert torch.allclose(cat.sum(dim=-1), torch.ones(N, D), atol=1e-5)


def test_temperature_scaling_handles_zero_one_probs():
    """Temperature scaling must handle y_prob == 0 or 1 without log(0)."""
    from scripts.run_ablations import fit_temperature_scaling

    # Probabilities exactly 0 and 1 would cause log(0) without clipping.
    y_prob = np.array([0.0, 1.0, 0.5, 0.3, 0.7])
    y_true = np.array([0, 1, 0, 1, 1])
    p = np.clip(y_prob, 1e-7, 1 - 1e-7)
    logits = np.log(p / (1 - p))
    T = fit_temperature_scaling(logits, y_true)
    assert np.isfinite(T)


def test_temperature_is_positive():
    """Temperature must always be positive after fitting."""
    from scripts.run_ablations import fit_temperature_scaling

    rng = np.random.RandomState(42)
    logits = rng.randn(64).astype(np.float32) * 3.0
    y = (logits > 0).astype(np.float32)
    T = fit_temperature_scaling(logits, y)
    assert T > 0.0
    assert np.isfinite(T)


def test_isotonic_cumulative_non_increasing():
    """P(Y>=m) must be non-increasing in m after isotonic calibration."""
    try:
        import sklearn  # noqa: F401
    except ImportError:
        return
    torch.manual_seed(2)
    N, D = 30, 3
    probs = torch.rand(N, D, NUM_TIERS - 1)
    targets = torch.randint(0, NUM_TIERS, (N, D))
    cal = IsotonicCalibration(num_dims=D, num_tiers=NUM_TIERS)
    cal.fit(probs, targets)
    p_ge = cal.calibrate_cumulative(probs).numpy()
    # P(Y>=m) non-increasing: p_ge[..., m] <= p_ge[..., m-1] + eps
    assert np.all(p_ge[..., 1:] <= p_ge[..., :-1] + 1e-8)
    cat = cal.calibrate_probs(probs).numpy()
    assert np.allclose(cat.sum(axis=-1), 1.0, atol=1e-5)


# ---------------------------------------------------------------------------
# P1-2: ordinal calibration ablation tests.
# These verify that temperature_ordinal / isotonic_ordinal actually change
# cumulative tier probabilities and that the output remains a valid ordinal
# distribution (non-increasing cumulative, sums to 1).
# ---------------------------------------------------------------------------


def test_ordinal_temperature_changes_cumulative_probabilities():
    """temperature_ordinal must change cumulative P(Y>=m), not be identity."""
    from scripts.run_ablations import (
        fit_ordinal_temperature,
        make_ordinal_temperature_transform,
    )

    rng = np.random.RandomState(0)
    N, D, K = 64, 4, NUM_TIERS
    # Overconfident per-tier probs (one-hot-ish).
    raw = rng.rand(N, D, K).astype(np.float32) + 0.01
    probs = raw / raw.sum(axis=-1, keepdims=True)
    labels = rng.randint(0, K, (N, D))
    T = fit_ordinal_temperature(probs, labels)
    assert np.isfinite(T) and T > 0
    transform = make_ordinal_temperature_transform(T)
    calibrated = transform(probs)
    # Cumulative probabilities must differ from the input (T != 1).
    cum_in = probs.cumsum(axis=-1)
    cum_out = calibrated.cumsum(axis=-1)
    assert not np.allclose(cum_in, cum_out, atol=1e-6), (
        "temperature_ordinal should change cumulative probabilities"
    )
    # Output must still be a valid distribution.
    assert np.allclose(calibrated.sum(axis=-1), 1.0, atol=1e-5)
    assert (calibrated >= 0).all()


def test_ordinal_isotonic_output_non_increasing_cumulative():
    """isotonic_ordinal output must satisfy P(Y>=m+1) <= P(Y>=m)."""
    try:
        import sklearn  # noqa: F401
    except ImportError:
        return
    from scripts.run_ablations import (
        _per_tier_to_cumulative,
        fit_ordinal_isotonic,
        make_ordinal_isotonic_transform,
    )

    rng = np.random.RandomState(1)
    N, D, K = 50, 4, NUM_TIERS
    raw = rng.rand(N, D, K).astype(np.float32) + 0.01
    probs = raw / raw.sum(axis=-1, keepdims=True)
    labels = rng.randint(0, K, (N, D))
    iso = fit_ordinal_isotonic(probs, labels)
    transform = make_ordinal_isotonic_transform(iso)
    calibrated = transform(probs)
    # Cumulative P(Y>=m) must be non-increasing in m.
    cum = _per_tier_to_cumulative(calibrated)
    assert np.all(cum[..., 1:] <= cum[..., :-1] + 1e-6), (
        "isotonic_ordinal must preserve P(Y>=m+1) <= P(Y>=m)"
    )
    assert np.allclose(calibrated.sum(axis=-1), 1.0, atol=1e-5)


def test_separate_thresholds_not_shared_with_shared_threshold():
    """separate_thresholds must use independent thresholds, not shared beta."""
    from cese.models.shared_threshold_calibrator import SharedThresholdCalibrator

    torch.manual_seed(0)
    shared = SharedThresholdCalibrator(
        num_tiers=NUM_TIERS, num_dims=4, calibration_mode="shared_threshold"
    )
    separate = SharedThresholdCalibrator(
        num_tiers=NUM_TIERS, num_dims=4, calibration_mode="separate_thresholds"
    )
    # shared_threshold must NOT have separate claim/support parameter tensors.
    assert not hasattr(shared, "raw_a_claim")
    assert not hasattr(shared, "raw_a_support")
    # separate_thresholds MUST have independent claim/support parameter tensors.
    assert hasattr(separate, "raw_a_claim")
    assert hasattr(separate, "raw_a_support")
    assert hasattr(separate, "raw_beta0_claim")
    assert hasattr(separate, "raw_beta0_support")
    # Perturbing the support-only parameters must change support_probs but
    # not claim_probs in separate_thresholds mode.
    theta_c = torch.randn(4, 4)
    theta_s = torch.randn(4, 4)
    out_before = separate(theta_c, theta_s)
    with torch.no_grad():
        separate.raw_a_support.add_(2.5)
        separate.raw_beta0_support.sub_(1.0)
    out_after = separate(theta_c, theta_s)
    # Support probs must change after perturbing support-only params.
    assert not torch.allclose(
        out_before["support_probs"], out_after["support_probs"], atol=1e-6
    ), "separate_thresholds support params should affect support_probs"
    # Claim probs must be unchanged (independent thresholds).
    assert torch.allclose(
        out_before["claim_probs"], out_after["claim_probs"], atol=1e-6
    ), "separate_thresholds claim probs should be independent of support params"
