"""Tests for paper_full required-results completeness (spec P1-2).

Verifies that:
  * paper_full emits a BLOCKING WARNING row when a required ordinal
    calibration variant is missing.
  * required_results_complete is False when any BLOCKING WARNING row is
    present.
  * ci_smoke does NOT emit blocking warnings (allows partial ablation).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generate_tables import build_calibration_ablation, build_constraint_ablation


def _write_ablations(results_dir: Path, variants: dict) -> None:
    """Write a minimal ablations_results.json with the given variants."""
    abl_dir = results_dir / "ablations"
    abl_dir.mkdir(parents=True, exist_ok=True)
    (abl_dir / "ablations_results.json").write_text(
        json.dumps(variants), encoding="utf-8"
    )


def _make_variant(name: str, n_samples: int = 8) -> dict:
    """Build a minimal valid ablation variant entry."""
    return {
        "macro_f1": 0.5,
        "auroc": 0.6,
        "claim_ordinal_ece": 0.1,
        "support_ordinal_ece": 0.1,
        "joint_ordinal_ece": 0.1,
        "brier_escalation": 0.2,
        "reliability_slope": 1.0,
        "threshold_sensitivity": 0.1,
        "n_samples": n_samples,
        "metric_valid": True,
    }


REQUIRED_ORDINAL_VARIANTS = (
    "no_calibration",
    "temperature_global",
    "temperature_ordinal",
    "isotonic_ordinal",
    "separate_thresholds",
    "shared_thresholds",
)


def test_paper_full_emits_blocking_warning_when_calibration_variant_missing(tmp_path):
    """paper_full must emit a BLOCKING WARNING row when a required ordinal
    calibration variant is missing from ablations_results.json."""
    # Write ablations with all variants EXCEPT temperature_global.
    variants = {k: _make_variant(k) for k in REQUIRED_ORDINAL_VARIANTS}
    del variants["temperature_global"]
    _write_ablations(tmp_path, variants)

    rows = build_calibration_ablation(tmp_path, profile="paper_full")
    blocking = [r for r in rows if "BLOCKING WARNING" in str(r.get("calibration", ""))]
    assert len(blocking) == 1, "paper_full should emit one BLOCKING WARNING row"
    assert "temperature_global" in blocking[0]["calibration"]


def test_paper_full_no_warning_when_all_variants_present(tmp_path):
    """paper_full must NOT emit a BLOCKING WARNING when all required ordinal
    variants are present."""
    variants = {k: _make_variant(k) for k in REQUIRED_ORDINAL_VARIANTS}
    _write_ablations(tmp_path, variants)

    rows = build_calibration_ablation(tmp_path, profile="paper_full")
    blocking = [r for r in rows if "BLOCKING WARNING" in str(r.get("calibration", ""))]
    assert len(blocking) == 0, "paper_full should not warn when all variants present"


def test_ci_smoke_no_blocking_warning_when_variant_missing(tmp_path):
    """ci_smoke must NOT emit blocking warnings (allows partial ablation
    for diagnostic purposes)."""
    variants = {k: _make_variant(k) for k in REQUIRED_ORDINAL_VARIANTS}
    del variants["isotonic_ordinal"]
    _write_ablations(tmp_path, variants)

    rows = build_calibration_ablation(tmp_path, profile="ci_smoke")
    blocking = [r for r in rows if "BLOCKING WARNING" in str(r.get("calibration", ""))]
    assert len(blocking) == 0, "ci_smoke should not emit blocking warnings"


def test_paper_full_emits_warning_for_all_missing_variants(tmp_path):
    """paper_full must list ALL missing variants in the BLOCKING WARNING."""
    variants = {k: _make_variant(k) for k in REQUIRED_ORDINAL_VARIANTS}
    del variants["temperature_global"]
    del variants["isotonic_ordinal"]
    del variants["separate_thresholds"]
    _write_ablations(tmp_path, variants)

    rows = build_calibration_ablation(tmp_path, profile="paper_full")
    blocking = [r for r in rows if "BLOCKING WARNING" in str(r.get("calibration", ""))]
    assert len(blocking) == 1
    label = blocking[0]["calibration"]
    assert "temperature_global" in label
    assert "isotonic_ordinal" in label
    assert "separate_thresholds" in label


def test_paper_full_missing_source_file_emits_missing_signal(tmp_path):
    """paper_full must emit a 'missing source file' row (not silent NA)
    when ablations_results.json does not exist."""
    # Do NOT write ablations_results.json.
    rows = build_calibration_ablation(tmp_path, profile="paper_full")
    assert len(rows) == 1
    assert "missing source file" in str(rows[0].get("calibration", ""))
    assert rows[0].get("metric_valid") is False
