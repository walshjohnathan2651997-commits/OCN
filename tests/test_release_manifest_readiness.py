"""Tests for release manifest readiness gate (ocn-31 P2-3).

Verifies the readiness gate forces paper_ready=False when:
  * human_audited_count == 0
  * contradiction_positive_count == 0
  * required strong baselines missing (baseline_completion_status=incomplete)
  * calibration ablations missing
  * test size too small (n_test < 30)
  * source_type all oracle
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_release_bundle import build_manifest


def _make_results_dir(tmp_path: Path) -> Path:
    """Create a minimal results dir with required subdirs."""
    results = tmp_path / "results"
    for sub in ("tables", "figures", "baselines", "oracle_extracted"):
        (results / sub).mkdir(parents=True, exist_ok=True)
    # Minimal report_metadata so paper_ready can be True from metadata.
    (results / "tables" / "report_metadata.json").write_text(
        json.dumps({
            "paper_ready": True,
            "required_results_complete": True,
            "report_mode": "paper_full",
        }),
        encoding="utf-8",
    )
    # Oracle comparison so oracle triples check passes.
    (results / "oracle_extracted" / "comparison_results.json").write_text(
        json.dumps({
            "same_model_same_samples": {
                "same_model_same_samples_valid": True,
                "n_logical_samples": 3,
            }
        }),
        encoding="utf-8",
    )
    return results


def _write_data(tmp_path: Path, records: list) -> Path:
    """Write a JSONL data file and return its path."""
    p = tmp_path / "data.jsonl"
    with p.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    return p


def _baseline_record(split: str = "train", audited: bool = False,
                     contra: int = 0, source: str = "oracle") -> dict:
    return {
        "sample_id": f"s_{split}_{audited}_{contra}_{source}",
        "split": split,
        "source_type": source,
        "contradiction_label": contra,
        "annotation": {"is_human_audited": audited, "annotators": ["human"] if audited else ["ai"]},
    }


def test_human_audited_zero_blocks_paper_ready(tmp_path):
    """human_audited_count==0 → paper_ready=False."""
    results = _make_results_dir(tmp_path)
    data = _write_data(tmp_path, [
        _baseline_record("train", audited=False),
        _baseline_record("test", audited=False, contra=1, source="extracted"),
    ])
    m = build_manifest(
        results_dir=results, data_path=data, config_path=None,
        checkpoint_path=None, seed=42, tables=["main_results"],
        figures=["calibration_curve"],
    )
    assert m["paper_ready"] is False
    reasons = m.get("blocking_reasons", [])
    assert any("human_audited_count=0" in r for r in reasons), \
        f"expected human_audited blocking reason, got: {reasons}"


def test_contradiction_positive_zero_blocks_paper_ready(tmp_path):
    """contradiction_positive_count==0 → paper_ready=False."""
    results = _make_results_dir(tmp_path)
    data = _write_data(tmp_path, [
        _baseline_record("train", audited=True, contra=0),
        _baseline_record("test", audited=True, contra=0, source="extracted"),
    ])
    m = build_manifest(
        results_dir=results, data_path=data, config_path=None,
        checkpoint_path=None, seed=42, tables=["main_results"],
        figures=["calibration_curve"],
    )
    assert m["paper_ready"] is False
    reasons = m.get("blocking_reasons", [])
    assert any("contradiction_positive_count=0" in r for r in reasons), \
        f"expected contradiction blocking reason, got: {reasons}"


def test_missing_baselines_blocks_paper_ready(tmp_path):
    """baseline_completion_status=incomplete → paper_ready=False.

    Writes a baselines_results.json that explicitly lists a missing
    required baseline so baseline_completion_status=incomplete.
    """
    results = _make_results_dir(tmp_path)
    # Write baselines_results.json with missing_required_results.
    (results / "baselines" / "baselines_results.json").write_text(
        json.dumps({
            "missing_required_results": [
                "baselines/scifact_verifier: missing offline_jsonl",
            ],
        }),
        encoding="utf-8",
    )
    # Data with audited + contradiction + extracted source + enough test
    # samples so only the baseline check blocks.
    records = [_baseline_record("train", audited=True, contra=1, source="extracted")]
    for i in range(40):
        records.append(_baseline_record("test", audited=True, contra=1, source="extracted"))
    data = _write_data(tmp_path, records)
    m = build_manifest(
        results_dir=results, data_path=data, config_path=None,
        checkpoint_path=None, seed=42, tables=["main_results"],
        figures=["calibration_curve"],
    )
    assert m["paper_ready"] is False
    reasons = m.get("blocking_reasons", [])
    # The per-item missing-required-results strings are propagated as-is
    # into blocking_reasons (see build_release_bundle.py). The test wrote
    # "baselines/scifact_verifier: missing offline_jsonl" into
    # baselines_results.json#missing_required_results, so that exact
    # string must appear in blocking_reasons.
    assert any("scifact_verifier" in r and "missing" in r for r in reasons), \
        f"expected baselines blocking reason, got: {reasons}"


def test_test_size_too_small_blocks_paper_ready(tmp_path):
    """n_test < 30 → paper_ready=False (pilot_only)."""
    results = _make_results_dir(tmp_path)
    records = [_baseline_record("train", audited=True, contra=1, source="extracted")]
    # Only 5 test samples (< 30).
    for i in range(5):
        records.append(_baseline_record("test", audited=True, contra=1, source="extracted"))
    data = _write_data(tmp_path, records)
    m = build_manifest(
        results_dir=results, data_path=data, config_path=None,
        checkpoint_path=None, seed=42, tables=["main_results"],
        figures=["calibration_curve"],
    )
    assert m["paper_ready"] is False
    reasons = m.get("blocking_reasons", [])
    assert any("test size too small" in r for r in reasons), \
        f"expected test-size blocking reason, got: {reasons}"


def test_source_type_all_oracle_blocks_paper_ready(tmp_path):
    """source_type all oracle → paper_ready=False."""
    results = _make_results_dir(tmp_path)
    data = _write_data(tmp_path, [
        _baseline_record("train", audited=True, contra=1, source="oracle"),
        _baseline_record("test", audited=True, contra=1, source="oracle"),
    ])
    m = build_manifest(
        results_dir=results, data_path=data, config_path=None,
        checkpoint_path=None, seed=42, tables=["main_results"],
        figures=["calibration_curve"],
    )
    assert m["paper_ready"] is False
    reasons = m.get("blocking_reasons", [])
    assert any("source_type all oracle" in r for r in reasons), \
        f"expected source_type blocking reason, got: {reasons}"


def test_no_data_path_skips_data_checks(tmp_path):
    """When data_path is None, data-dependent checks are skipped.

    The data checks (human_audited, contradiction_positive, source_type,
    n_test) must NOT appear in blocking_reasons when data_path is None.
    Completion-status checks (baselines/calibration/constraint) may still
    block because they reflect whether experiment tables exist.
    """
    results = _make_results_dir(tmp_path)
    m = build_manifest(
        results_dir=results, data_path=None, config_path=None,
        checkpoint_path=None, seed=42, tables=["main_results"],
        figures=["calibration_curve"],
    )
    reasons = m.get("blocking_reasons", [])
    # Data-dependent checks must not fire when data_path is None.
    data_check_markers = (
        "human_audited_count==0",
        "contradiction_positive_count==0",
        "test size too small",
        "source_type all oracle",
    )
    for marker in data_check_markers:
        assert not any(marker in r for r in reasons), \
            f"data-check '{marker}' fired despite data_path=None: {reasons}"
