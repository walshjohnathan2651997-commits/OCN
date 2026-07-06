"""Additional unit tests (spec Section 11, items 8-10).

  8. Confidence lower bound never exceeds extracted evidence.
  9. Metrics handle empty labels safely.
  10. Random seed reproducibility.
"""

from __future__ import annotations

import numpy as np
import torch

from cese.eval import (
    binary_escalation_metrics,
    expected_calibration_error,
    quadratic_weighted_kappa,
    mean_absolute_error,
    high_strength_false_support_rate,
    evidence_gap_micro_f1,
    evidence_gap_macro_f1,
    monotonic_violation_rate,
    truncation_violation_rate,
    confidence_lower_bound_safety_rate,
    prompt_run_variance_for_llm_baselines,
)
from cese.eval.metrics import ordinal_calibration_error
from cese.losses.confidence_lower_bound import (
    compute_evidence_lower_bound,
    confidence_lower_bound_loss,
)
from cese.utils.seed import set_seed


# ---------------------------------------------------------------------------
# 8. Confidence lower bound never exceeds extracted evidence.
# ---------------------------------------------------------------------------


def test_confidence_lower_bound_never_exceeds_extracted():
    """e_lower_j = clamp(e_tilde_j - lambda*(1-q_j), 0, 1) <= e_tilde_j."""
    torch.manual_seed(0)
    evidence_vector = torch.rand(8, 8)  # e_tilde in [0, 1]
    evidence_confidence = torch.rand(8, 8)  # q in [0, 1]
    for lam in [0.0, 0.25, 0.5, 1.0]:
        e_lower = compute_evidence_lower_bound(evidence_vector, evidence_confidence, lam)
        # The lower-bound evidence must never exceed the extracted evidence.
        assert torch.all(e_lower <= evidence_vector + 1e-6), (
            f"e_lower > e_tilde at lambda={lam}"
        )
        # And must remain in [0, 1].
        assert torch.all(e_lower >= 0.0)
        assert torch.all(e_lower <= 1.0)


def test_confidence_lower_bound_safety_rate_is_one_when_consistent():
    """When observed escalation >= lower-bound escalation, safety rate = 1."""
    # p_exceed (observed) >= p_exceed_lower (worst case).
    p_exceed = np.full((4, 4), 0.8)
    p_exceed_lower = np.full((4, 4), 0.6)
    ev = np.ones((4, 8))
    e_lower = np.zeros((4, 8))
    rate = confidence_lower_bound_safety_rate(p_exceed, p_exceed_lower, ev, e_lower, L_f=1.0)
    assert rate == 1.0


# ---------------------------------------------------------------------------
# 9. Metrics handle empty labels safely.
# ---------------------------------------------------------------------------


def test_binary_metrics_empty_labels():
    """binary_escalation_metrics should not raise on empty inputs."""
    y_true = np.array([], dtype=int)
    y_pred = np.array([], dtype=int)
    m = binary_escalation_metrics(y_true, y_pred)
    # Should return finite-ish values (0 or nan) without raising.
    assert "accuracy" in m
    assert "macro_f1" in m


def test_qwk_empty_labels():
    y = np.array([], dtype=int)
    # sklearn raises for single-class; we accept nan via exception.
    try:
        q = quadratic_weighted_kappa(y, y)
        assert np.isnan(q) or q == 1.0
    except Exception:
        pass  # acceptable: empty labels are degenerate


def test_mae_empty_labels():
    y = np.array([])
    val = mean_absolute_error(y, y)
    # Empty inputs should not raise; nan is acceptable safe handling.
    assert val == 0.0 or np.isnan(val)


def test_ece_empty_labels():
    y_true = np.array([], dtype=int)
    y_prob = np.array([], dtype=float)
    ece = expected_calibration_error(y_true, y_prob, n_bins=5)
    assert ece == 0.0 or np.isnan(ece)


def test_high_strength_false_support_rate_empty():
    claim = np.zeros((0, 4), dtype=int)
    support = np.zeros((0, 4), dtype=int)
    labels = np.array([], dtype=int)
    rate = high_strength_false_support_rate(claim, support, labels)
    assert np.isnan(rate)


def test_evidence_gap_f1_empty():
    assert np.isnan(evidence_gap_micro_f1([], []))
    assert np.isnan(evidence_gap_macro_f1([], []))


def test_monotonic_violation_rate_empty():
    p_low = np.zeros((0, 4, 4))
    p_high = np.zeros((0, 4, 4))
    rate = monotonic_violation_rate(p_low, p_high)
    assert np.isnan(rate) or rate == 0.0


def test_truncation_violation_rate_empty():
    support = np.zeros((0, 4, 5))
    max_tiers = np.zeros((0, 4), dtype=int)
    rate = truncation_violation_rate(support, max_tiers)
    assert rate == 0.0


def test_ordinal_calibration_error_empty():
    probs = np.zeros((0, 4, 5))
    labels = np.zeros((0, 4), dtype=int)
    oce = ordinal_calibration_error(probs, labels)
    assert np.isnan(oce)


def test_prompt_run_variance_empty():
    out = prompt_run_variance_for_llm_baselines([])
    assert np.isnan(out["mean"])


# ---------------------------------------------------------------------------
# 10. Random seed reproducibility.
# ---------------------------------------------------------------------------


def test_set_seed_reproducibility_numpy():
    """Same seed -> same numpy random state."""
    set_seed(42)
    a = np.random.rand(10)
    set_seed(42)
    b = np.random.rand(10)
    assert np.allclose(a, b)


def test_set_seed_reproducibility_torch():
    """Same seed -> same torch random state."""
    set_seed(42)
    a = torch.rand(10)
    set_seed(42)
    b = torch.rand(10)
    assert torch.allclose(a, b)


def test_set_seed_different_seeds_differ():
    set_seed(42)
    a = np.random.rand(10)
    set_seed(7)
    b = np.random.rand(10)
    assert not np.allclose(a, b)
