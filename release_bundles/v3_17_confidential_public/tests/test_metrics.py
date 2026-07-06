"""Tests for evaluation metrics."""

from __future__ import annotations

import numpy as np

from cese.constants import CLAIM_DIMS
from cese.eval import (
    binary_escalation_metrics,
    brier_score,
    calibration_report,
    error_decomposition,
    exceedance_accuracy,
    expected_calibration_error,
    mean_absolute_error,
    ordinal_metrics,
    quadratic_weighted_kappa,
    threshold_sweep,
)


def test_binary_metrics_perfect():
    y_true = np.array([0, 1, 0, 1])
    y_pred = np.array([0, 1, 0, 1])
    y_prob = np.array([0.1, 0.9, 0.2, 0.8])
    m = binary_escalation_metrics(y_true, y_pred, y_prob)
    assert m["accuracy"] == 1.0
    assert m["f1"] == 1.0
    assert m["roc_auc"] == 1.0


def test_qwk_perfect_agreement():
    y_true = np.array([0, 1, 2, 3, 4])
    y_pred = np.array([0, 1, 2, 3, 4])
    qwk = quadratic_weighted_kappa(y_true, y_pred)
    assert abs(qwk - 1.0) < 1e-6


def test_mae_zero():
    y = np.array([1, 2, 3])
    assert mean_absolute_error(y, y) == 0.0


def test_exceedance_accuracy():
    claim = np.array([[2, 1]])
    support = np.array([[1, 1]])
    labels = np.array([[1, 0]])
    acc = exceedance_accuracy(claim, support, labels)
    assert acc == 1.0


def test_ordinal_metrics_shapes():
    n, d = 10, 4
    claim_true = np.random.randint(0, 5, (n, d))
    claim_pred = np.random.randint(0, 5, (n, d))
    support_true = np.random.randint(0, 5, (n, d))
    support_pred = np.random.randint(0, 5, (n, d))
    esc = (claim_true > support_true).astype(int)
    m = ordinal_metrics(
        claim_true, claim_pred, support_true, support_pred, esc, dim_names=CLAIM_DIMS
    )
    assert set(m.keys()) == set(CLAIM_DIMS)
    for dim_metrics in m.values():
        assert "claim_qwk" in dim_metrics
        assert "claim_mae" in dim_metrics


def test_ece_zero_for_perfect():
    y_true = np.array([0, 1, 0, 1])
    y_prob = np.array([0.0, 1.0, 0.0, 1.0])
    ece = expected_calibration_error(y_true, y_prob, n_bins=10)
    assert ece < 1e-6


def test_brier_zero_for_perfect():
    y_true = np.array([0, 1])
    y_prob = np.array([0.0, 1.0])
    assert brier_score(y_true, y_prob) == 0.0


def test_calibration_report_keys():
    y_true = np.array([0, 1, 0, 1])
    y_prob = np.array([0.2, 0.8, 0.3, 0.7])
    rep = calibration_report(y_true, y_prob)
    assert "ece" in rep and "brier" in rep and "nll" in rep


def test_threshold_sweep():
    y_true = np.array([0, 1, 0, 1])
    y_prob = np.array([0.2, 0.8, 0.3, 0.7])
    sweep = threshold_sweep(y_true, y_prob, points=11)
    assert len(sweep["threshold"]) == 11
    assert len(sweep["f1"]) == 11


def test_error_decomposition():
    claim_true = np.array([[2, 1]])
    claim_pred = np.array([[3, 0]])  # one over, one under
    support = np.array([[1, 1]])
    out = error_decomposition(claim_true, claim_pred, support, dim_names=["a", "b"])
    assert out["over_escalation"] == 1
    assert out["under_escalation"] == 1
    assert out["exact"] == 0
    assert "per_dimension" in out
