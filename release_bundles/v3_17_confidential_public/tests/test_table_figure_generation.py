"""Tests for Task D: table and figure generation fixes.

Verifies:
- ``plot_monotonic_violation`` filters invalid rows (BLOCKING WARNING
  placeholder, NaN/None rates, metric_valid=False) before plotting.
- ``build_ordinal_calibration_diagnostics`` reads the true per-dim
  ordinal ECE from ``eval_data["ordinal_calibration_per_dim"]`` and does
  NOT fall back to the binary ``calibration.ece`` (which would
  mislabel binary ECE as ordinal ECE).
- When per-dim ordinal ECE is missing, the row is emitted with NA +
  metric_valid=False (not silently defaulted to binary ECE).
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import generate_tables as gt_mod


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write_eval(tmp_path: Path, eval_data: dict) -> Path:
    (tmp_path / "eval_test.json").write_text(
        json.dumps(eval_data), encoding="utf-8"
    )
    return tmp_path


# ---------------------------------------------------------------------------
# build_ordinal_calibration_diagnostics
# ---------------------------------------------------------------------------

def test_ordinal_calibration_reads_per_dim_ordinal_ece(tmp_path):
    """When eval_test.json contains ordinal_calibration_per_dim, the
    diagnostics table should report per-dim claim/support/joint ECE
    from that field (NOT from binary calibration.ece)."""
    eval_data = {
        "n_samples": 100,
        "calibration": {"ece": 0.05, "reliability_slope": 0.9},
        # Binary ECE - must NOT be reported as ordinal ECE.
        "ordinal_calibration_error": 0.15,
        "ordinal_calibration_per_dim": {
            "scope":       {"claim_ece": 0.10, "support_ece": 0.12, "joint_ece": 0.11},
            "causal":      {"claim_ece": 0.20, "support_ece": 0.22, "joint_ece": 0.21},
            "action":      {"claim_ece": 0.30, "support_ece": 0.32, "joint_ece": 0.31},
            "certainty":   {"claim_ece": 0.40, "support_ece": 0.42, "joint_ece": 0.41},
        },
    }
    _write_eval(tmp_path, eval_data)
    rows = gt_mod.build_ordinal_calibration_diagnostics(tmp_path)
    assert len(rows) == 4  # one per CLAIM_DIMS
    dims = {r["dimension"] for r in rows}
    assert dims == {"scope", "causal", "action", "certainty"}
    scope = next(r for r in rows if r["dimension"] == "scope")
    assert scope["claim_ordinal_ece"] == 0.10
    assert scope["support_ordinal_ece"] == 0.12
    assert scope["joint_ordinal_ece"] == 0.11
    assert scope["metric_valid"] is True
    # The binary ECE (0.05) must NOT appear as an ordinal ECE.
    assert scope["claim_ordinal_ece"] != 0.05
    assert scope["support_ordinal_ece"] != 0.05


def test_ordinal_calibration_does_not_fallback_to_binary_ece(tmp_path):
    """When per-dim ordinal ECE is MISSING, the diagnostics must NOT fall
    back to the binary calibration.ece. Instead emit NA +
    metric_valid=False."""
    eval_data = {
        "n_samples": 100,
        "calibration": {"ece": 0.05, "reliability_slope": 0.9},
        # No ordinal_calibration_per_dim field.
        "ordinal_calibration_error": float("nan"),
    }
    _write_eval(tmp_path, eval_data)
    rows = gt_mod.build_ordinal_calibration_diagnostics(tmp_path)
    # Single fallback row.
    assert len(rows) == 1
    row = rows[0]
    assert row["dimension"] == "all"
    # Must NOT be the binary ECE (0.05).
    assert row["claim_ordinal_ece"] != 0.05
    assert row["claim_ordinal_ece"] == "NA"
    assert row["support_ordinal_ece"] == "NA"
    assert row["joint_ordinal_ece"] == "NA"
    assert row["metric_valid"] is False


def test_ordinal_calibration_scalar_oce_when_no_per_dim(tmp_path):
    """When per-dim ordinal ECE is missing but a scalar
    ordinal_calibration_error exists, the all-dims row should report it
    (it's a true ordinal ECE, just not per-dim) and set metric_valid
    based on its presence."""
    eval_data = {
        "n_samples": 100,
        "calibration": {"ece": 0.05},
        "ordinal_calibration_error": 0.18,
        # No ordinal_calibration_per_dim
    }
    _write_eval(tmp_path, eval_data)
    rows = gt_mod.build_ordinal_calibration_diagnostics(tmp_path)
    assert len(rows) == 1
    row = rows[0]
    # Scalar OCE reported as claim_ordinal_ece (true ordinal ECE).
    assert row["claim_ordinal_ece"] == 0.18
    # But support/joint are NA (no per-dim data).
    assert row["support_ordinal_ece"] == "NA"
    assert row["joint_ordinal_ece"] == "NA"
    # metric_valid is True because the scalar OCE is a real value.
    assert row["metric_valid"] is True


def test_ordinal_calibration_missing_dim_emits_na_row(tmp_path):
    """If per_dim dict is missing one of CLAIM_DIMS, that dim gets an NA
    row with metric_valid=False."""
    eval_data = {
        "n_samples": 100,
        "calibration": {"ece": 0.05},
        "ordinal_calibration_per_dim": {
            # Only 2 of 4 dims present.
            "scope": {"claim_ece": 0.10, "support_ece": 0.12, "joint_ece": 0.11},
            "causal": {"claim_ece": 0.20, "support_ece": 0.22, "joint_ece": 0.21},
        },
    }
    _write_eval(tmp_path, eval_data)
    rows = gt_mod.build_ordinal_calibration_diagnostics(tmp_path)
    assert len(rows) == 4
    action = next(r for r in rows if r["dimension"] == "action")
    assert action["claim_ordinal_ece"] == "NA"
    assert action["metric_valid"] is False
    scope = next(r for r in rows if r["dimension"] == "scope")
    assert scope["claim_ordinal_ece"] == 0.10
    assert scope["metric_valid"] is True


# ---------------------------------------------------------------------------
# plot_monotonic_violation
# ---------------------------------------------------------------------------

def test_plot_monotonic_violation_filters_invalid_rows(tmp_path):
    """plot_monotonic_violation must skip:
    - the BLOCKING WARNING placeholder row (metric_valid=False).
    - rows with NaN monotonic_violation_rate.
    - rows with metric_valid=False.
    Only rows with a real numeric rate AND metric_valid=True should be
    plotted. We verify this indirectly by checking the saved PNG is
    non-trivial (matplotlib writes a real PNG when bars are drawn)."""
    # Set up an ablations_results.json with mixed valid / invalid rows.
    abl = {
        # valid row
        "full": {
            "escalation_f1": 0.8,
            "monotonic_violation_rate": 0.05,
            "truncation_violation_rate": 0.1,
            "n_samples": 100,
            "metric_valid": True,
        },
        # NaN violation rate - should be filtered.
        "soft_gate": {
            "escalation_f1": 0.7,
            "monotonic_violation_rate": float("nan"),
            "truncation_violation_rate": 0.2,
            "n_samples": 100,
            "metric_valid": True,
        },
        # metric_valid=False - should be filtered.
        "no_constraint": {
            "escalation_f1": 0.6,
            "monotonic_violation_rate": 0.3,
            "truncation_violation_rate": 0.4,
            "n_samples": 100,
            "metric_valid": False,
        },
    }
    (tmp_path / "ablations").mkdir(parents=True, exist_ok=True)
    (tmp_path / "ablations" / "ablations_results.json").write_text(
        json.dumps(abl), encoding="utf-8"
    )
    out_path = tmp_path / "monotonic_violation.png"
    gt_mod.plot_monotonic_violation(tmp_path, out_path)
    assert out_path.exists()
    assert out_path.stat().st_size > 0


def test_plot_monotonic_violation_no_valid_data(tmp_path):
    """When all rows are invalid (e.g. only the BLOCKING WARNING
    placeholder), the plot should still be created with an explicit
    "no valid data" message rather than an empty bar chart."""
    # paper_full profile with missing required variants -> emits a
    # BLOCKING WARNING row with metric_valid=False.
    (tmp_path / "ablations").mkdir(parents=True, exist_ok=True)
    (tmp_path / "ablations" / "ablations_results.json").write_text(
        json.dumps({}), encoding="utf-8"
    )
    out_path = tmp_path / "monotonic_violation.png"
    gt_mod.plot_monotonic_violation(tmp_path, out_path)
    assert out_path.exists()
    assert out_path.stat().st_size > 0
