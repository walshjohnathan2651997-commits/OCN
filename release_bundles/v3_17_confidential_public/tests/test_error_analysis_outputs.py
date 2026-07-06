"""Tests for error_analysis.py release outputs (ocn-31 P2-3).

Verifies error_analysis.py --release_dir produces:
  * release/error_analysis.md (non-empty, with threshold sweep)
  * release/error_analysis.csv (non-empty, per-sample rows)
  * threshold sweep table is populated
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _write_mock_predictions(path: Path, n: int = 16) -> None:
    """Write n mock prediction records for testing."""
    import random
    random.seed(42)
    recs = []
    for i in range(n):
        gold = i % 2
        prob = max(0.01, min(0.99, random.uniform(0.1, 0.9) + (0.3 if gold else -0.2)))
        pred = 1 if prob >= 0.5 else 0
        recs.append({
            "sample_id": f"mock-{i:03d}",
            "gold_escalation_label": gold,
            "escalation_score": prob,
            "escalation_pred": pred,
            "claim_tiers": {"scope": 3 + gold, "causal": 2, "action": 2, "certainty": 3},
            "support_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
            "claim_tiers_pred": {"scope": 3 + gold, "causal": 2, "action": 2, "certainty": 3},
            "support_tiers_pred": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
            "evidence_gap_labels": [f"scope_missing"] if gold else [],
            "claim_text": f"claim {i}",
            "evidence_text": f"evidence {i}",
            "source_type": "oracle",
            "domain": "test",
            "claim_family": "test",
        })
    with path.open("w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")


def test_error_analysis_generates_csv_and_md(tmp_path):
    """--release_dir produces both error_analysis.md and error_analysis.csv."""
    preds_path = tmp_path / "preds.jsonl"
    _write_mock_predictions(preds_path)
    release_dir = tmp_path / "release"
    release_dir.mkdir()
    from scripts.error_analysis import main as ea_main
    import argparse
    # Call main with sys.argv override.
    orig_argv = sys.argv
    sys.argv = [
        "error_analysis.py",
        "--predictions", str(preds_path),
        "--release_dir", str(release_dir),
        "--data_version", "test",
    ]
    try:
        ea_main()
    finally:
        sys.argv = orig_argv
    md_path = release_dir / "error_analysis.md"
    csv_path = release_dir / "error_analysis.csv"
    assert md_path.exists(), f"md not found: {md_path}"
    assert csv_path.exists(), f"csv not found: {csv_path}"
    md_text = md_path.read_text(encoding="utf-8")
    assert len(md_text) > 0, "md is empty"


def test_threshold_sweep_is_populated(tmp_path):
    """The threshold sweep table in error_analysis.md is non-empty."""
    preds_path = tmp_path / "preds.jsonl"
    _write_mock_predictions(preds_path)
    release_dir = tmp_path / "release"
    release_dir.mkdir()
    from scripts.error_analysis import main as ea_main
    orig_argv = sys.argv
    sys.argv = [
        "error_analysis.py",
        "--predictions", str(preds_path),
        "--release_dir", str(release_dir),
        "--data_version", "test",
    ]
    try:
        ea_main()
    finally:
        sys.argv = orig_argv
    md_text = (release_dir / "error_analysis.md").read_text(encoding="utf-8")
    # Must contain threshold sweep section with rows.
    assert "Threshold sweep" in md_text or "threshold sweep" in md_text.lower(), \
        "md missing threshold sweep section"
    # Must contain at least one threshold row (0.05 or 0.10 etc).
    assert "| 0." in md_text, "md missing threshold table rows"


def test_csv_has_required_columns(tmp_path):
    """error_analysis.csv has the required per-sample columns."""
    preds_path = tmp_path / "preds.jsonl"
    _write_mock_predictions(preds_path)
    release_dir = tmp_path / "release"
    release_dir.mkdir()
    from scripts.error_analysis import main as ea_main
    orig_argv = sys.argv
    sys.argv = [
        "error_analysis.py",
        "--predictions", str(preds_path),
        "--release_dir", str(release_dir),
        "--data_version", "test",
    ]
    try:
        ea_main()
    finally:
        sys.argv = orig_argv
    csv_path = release_dir / "error_analysis.csv"
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    required = {
        "sample_id", "true_label", "predicted_probability",
        "predicted_label", "claim_tiers", "support_tiers",
        "exceeded_dimensions", "top_evidence_gaps", "correct",
    }
    assert required.issubset(set(header)), \
        f"csv missing columns: {required - set(header)}"
    assert len(rows) > 0, "csv has no data rows"


def test_json_report_contains_sweep_and_diagnosis(tmp_path):
    """The JSON report embeds threshold_sweep and escalation_f1_diagnosis."""
    preds_path = tmp_path / "preds.jsonl"
    _write_mock_predictions(preds_path)
    release_dir = tmp_path / "release"
    release_dir.mkdir()
    out_json = tmp_path / "ea.json"
    from scripts.error_analysis import main as ea_main
    orig_argv = sys.argv
    sys.argv = [
        "error_analysis.py",
        "--predictions", str(preds_path),
        "--release_dir", str(release_dir),
        "--output_json", str(out_json),
        "--data_version", "test",
    ]
    try:
        ea_main()
    finally:
        sys.argv = orig_argv
    report = json.loads(out_json.read_text(encoding="utf-8"))
    assert "threshold_sweep" in report, "JSON missing threshold_sweep"
    assert "escalation_f1_diagnosis" in report, "JSON missing escalation_f1_diagnosis"
    assert isinstance(report["threshold_sweep"], list)
    assert len(report["threshold_sweep"]) > 0, "threshold_sweep is empty"
