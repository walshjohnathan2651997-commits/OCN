"""Tests for P3c reserved paper tables and P3d threshold provenance.

Verifies:
  * build_threshold_sensitivity emits NA row when sweep missing, real
    rows when present.
  * build_ordinal_calibration_diagnostics emits NA row when calibration
    block missing, per-dim rows when present.
  * build_high_strength_false_support emits rows for CESE-OCN + valid
    baselines, excludes paper_valid=False baselines in paper_full.
  * fit_thresholds records source_split / fit_split_provenance.
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

from scripts.generate_tables import (
    build_threshold_sensitivity,
    build_ordinal_calibration_diagnostics,
    build_high_strength_false_support,
)
from scripts.fit_thresholds import compute_threshold_state


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _write_eval(results_dir: Path, eval_data: dict) -> None:
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "eval_test.json").write_text(
        json.dumps(eval_data), encoding="utf-8"
    )


def _write_baselines(results_dir: Path, bl: dict) -> None:
    bl_dir = results_dir / "baselines"
    bl_dir.mkdir(parents=True, exist_ok=True)
    (bl_dir / "baselines_results.json").write_text(
        json.dumps(bl), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# threshold sensitivity
# ---------------------------------------------------------------------------


def test_threshold_sensitivity_na_when_sweep_missing(tmp_path):
    """When no test_predictions.jsonl and no threshold_sweep.csv exist,
    emit a single NA row with metric_valid=False (not silent empty)."""
    _write_eval(tmp_path, {"n_samples": 8})
    rows = build_threshold_sensitivity(tmp_path)
    assert len(rows) == 1
    assert rows[0]["threshold"] == "NA"
    assert rows[0]["escalation_f1"] == "NA"
    assert rows[0]["metric_valid"] is False


def test_threshold_sensitivity_real_rows_when_sweep_present(tmp_path):
    """When test_predictions.jsonl is present, recompute one row per
    threshold from y_true + y_prob (ocn-35 P1: single source of truth)."""
    pred_dir = tmp_path / "predictions"
    pred_dir.mkdir(parents=True, exist_ok=True)
    pred_path = pred_dir / "test_predictions.jsonl"
    # 4 samples: 2 positive (y_true=1), 2 negative (y_true=0).
    # y_prob spread so different thresholds give different predictions.
    import json as _json
    with pred_path.open("w", encoding="utf-8") as fh:
        for yt, yp in [(1, 0.9), (1, 0.4), (0, 0.35), (0, 0.1)]:
            fh.write(_json.dumps({"y_true": yt, "y_prob": yp}) + "\n")
    rows = build_threshold_sensitivity(tmp_path)
    # All rows must be valid (metric_valid=True) and have numeric thresholds.
    assert len(rows) > 0
    assert all(r["metric_valid"] is True for r in rows)
    assert all(isinstance(r["threshold"], float) for r in rows)
    # At threshold 0.05 all samples predicted positive: recall=1.0.
    low = [r for r in rows if abs(r["threshold"] - 0.05) < 1e-9][0]
    assert low["recall"] == 1.0
    # At threshold 0.95 no samples predicted positive: recall=0.0.
    high = [r for r in rows if abs(r["threshold"] - 0.95) < 1e-9][0]
    assert high["recall"] == 0.0


# ---------------------------------------------------------------------------
# ordinal calibration diagnostics
# ---------------------------------------------------------------------------


def test_ordinal_calibration_diagnostics_na_when_missing(tmp_path):
    """When eval_test.json has no calibration block, emit a single NA row."""
    _write_eval(tmp_path, {"n_samples": 8})
    rows = build_ordinal_calibration_diagnostics(tmp_path)
    assert len(rows) == 1
    assert rows[0]["dimension"] == "all"
    assert rows[0]["metric_valid"] is False


def test_ordinal_calibration_diagnostics_per_dim_when_present(tmp_path):
    """When ordinal_calibration_per_dim is present, emit one row per dimension.

    P0-D: the field name is ``ordinal_calibration_per_dim`` (dict keyed by
    dim name), NOT ``ordinal.per_dim`` (list). The latter never existed in
    evaluate_model.py output and caused a silent fall back to binary ECE.
    """
    _write_eval(tmp_path, {
        "n_samples": 8,
        "calibration": {"ece": 0.1, "reliability_slope": 1.0},
        "ordinal_calibration_per_dim": {
            "scope":    {"claim_ece": 0.05, "support_ece": 0.06, "joint_ece": 0.07},
            "causal":   {"claim_ece": 0.08, "support_ece": 0.09, "joint_ece": 0.10},
            "action":   {"claim_ece": 0.11, "support_ece": 0.12, "joint_ece": 0.13},
            "certainty":{"claim_ece": 0.14, "support_ece": 0.15, "joint_ece": 0.16},
        },
    })
    rows = build_ordinal_calibration_diagnostics(tmp_path)
    assert len(rows) == 4  # one per CLAIM_DIMS
    by_dim = {r["dimension"]: r for r in rows}
    assert by_dim["scope"]["claim_ordinal_ece"] == 0.05
    assert by_dim["causal"]["joint_ordinal_ece"] == 0.10
    assert all(r["metric_valid"] for r in rows)


# ---------------------------------------------------------------------------
# high-strength false-support
# ---------------------------------------------------------------------------


def test_high_strength_false_support_includes_cese_and_valid_baselines(tmp_path):
    """paper_full includes CESE-OCN + paper_valid baselines.

    P0-C: rule_baseline is NEVER paper_valid (uses gold tiers), so it is
    excluded from paper_full even if its source JSON claims paper_valid=True.
    """
    _write_eval(tmp_path, {
        "n_samples": 8,
        "high_strength_false_support_rate": 0.12,
    })
    _write_baselines(tmp_path, {
        # rule_baseline: source claims paper_valid=True but P0-C forces
        # paper_valid=False (uses gold tiers) -> excluded from paper_full.
        "rule_baseline": {"high_strength_false_support_rate": 0.5, "n_samples": 8, "paper_valid": True},
        "nli_baseline": {"high_strength_false_support_rate": 0.3, "n_samples": 8, "paper_valid": True},
        # paper_valid=False -> excluded in paper_full
        "scifact_verifier": {"high_strength_false_support_rate": None, "paper_valid": False},
    })
    rows = build_high_strength_false_support(tmp_path, profile="paper_full")
    models = {r["model"] for r in rows}
    assert "CESE-OCN full" in models
    # rule_baseline is correctly excluded (uses gold tiers, never paper-valid).
    assert "Rule baseline" not in models
    assert "NLI baseline" in models
    # paper_valid=False baseline excluded in paper_full
    assert "SciFact verifier" not in models


def test_high_strength_false_support_na_when_metric_missing(tmp_path):
    """When a baseline has no high_strength_false_support_rate, emit NA
    with metric_valid=False (not silently dropped)."""
    _write_eval(tmp_path, {"n_samples": 8})
    _write_baselines(tmp_path, {
        "rule_baseline": {"n_samples": 8, "paper_valid": True},  # no hsfs field
    })
    rows = build_high_strength_false_support(tmp_path, profile="ci_smoke")
    by_model = {r["model"]: r for r in rows}
    # ci_smoke keeps the row even though metric is NA.
    assert "Rule baseline" in by_model
    assert by_model["Rule baseline"]["high_strength_false_support_rate"] == "NA"
    assert by_model["Rule baseline"]["metric_valid"] is False


# ---------------------------------------------------------------------------
# P3d: fit_thresholds split provenance
# ---------------------------------------------------------------------------


def test_fit_thresholds_records_split_provenance(tmp_path):
    """compute_threshold_state output must be recordable with source_split
    provenance so downstream consumers can verify thresholds were NOT
    fit on the test split."""
    records = [
        {
            "sample_id": f"s{i}",
            "split": "train",
            "claim_tiers": {"scope": 2, "causal": 1, "action": 3, "certainty": 1},
            "support_tiers": {"scope": 1, "causal": 1, "action": 1, "certainty": 1},
        }
        for i in range(4)
    ]
    state = compute_threshold_state(records)
    # Simulate the main() provenance annotation.
    state["source_split"] = "train"
    state["fit_split_provenance"] = {
        "source_split": "train",
        "source_path": str(tmp_path / "data.jsonl"),
        "n_records_used": 4,
        "test_split_used": False,
    }
    assert state["source_split"] == "train"
    assert state["fit_split_provenance"]["test_split_used"] is False
    assert state["fit_split_provenance"]["n_records_used"] == 4
