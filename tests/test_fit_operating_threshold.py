"""Tests for P3-7: scripts/fit_operating_threshold.py.

Verifies:
- dev predictions can fit a threshold.
- test predictions error out.
- single-class labels error out.
- output JSON contains test_split_used=false.
- threshold_state records provenance fields.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.fit_operating_threshold import fit_operating_threshold


def _write_predictions(path: Path, records: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def _balanced_dev_records(n_pos: int = 5, n_neg: int = 5) -> list[dict]:
    recs: list[dict] = []
    for i in range(n_pos):
        recs.append({
            "sample_id": f"p{i}",
            "split": "dev",
            "gold_escalation_label": 1,
            "escalation_score": 0.7 + 0.01 * i,
        })
    for i in range(n_neg):
        recs.append({
            "sample_id": f"n{i}",
            "split": "dev",
            "gold_escalation_label": 0,
            "escalation_score": 0.2 + 0.01 * i,
        })
    return recs


# ---------------------------------------------------------------------------

def test_dev_predictions_can_fit_threshold(tmp_path):
    pred_path = tmp_path / "dev_predictions.jsonl"
    out_path = tmp_path / "operating_threshold.json"
    _write_predictions(pred_path, _balanced_dev_records())
    state = fit_operating_threshold(
        predictions_path=pred_path,
        output_path=out_path,
        metric="macro_f1",
        min_threshold=0.05,
        max_threshold=0.95,
        num_grid=181,
    )
    assert 0.05 <= state["selected_threshold"] <= 0.95
    assert state["metric_optimized"] == "macro_f1"
    assert state["source_split"] == "dev"
    assert state["n_records_used"] == 10
    assert state["test_split_used"] is False
    assert state["threshold_grid"] == {"min": 0.05, "max": 0.95, "num": 181}
    assert "best_metric_value" in state
    # File written.
    assert out_path.exists()
    saved = json.loads(out_path.read_text(encoding="utf-8"))
    assert saved["selected_threshold"] == state["selected_threshold"]
    # Provenance recorded.
    assert "provenance" in saved
    assert saved["provenance"]["fitter"].endswith("fit_operating_threshold.py")


def test_test_predictions_raise_error(tmp_path):
    pred_path = tmp_path / "test_predictions.jsonl"
    out_path = tmp_path / "operating_threshold.json"
    recs = [
        {"sample_id": "t1", "split": "test",
         "gold_escalation_label": 1, "escalation_score": 0.7},
        {"sample_id": "t2", "split": "test",
         "gold_escalation_label": 0, "escalation_score": 0.3},
    ]
    _write_predictions(pred_path, recs)
    with pytest.raises(ValueError, match="test split"):
        fit_operating_threshold(
            predictions_path=pred_path,
            output_path=out_path,
            metric="macro_f1",
        )


def test_single_class_labels_raise_error(tmp_path):
    pred_path = tmp_path / "dev_predictions.jsonl"
    out_path = tmp_path / "operating_threshold.json"
    recs = [
        {"sample_id": "p1", "split": "dev",
         "gold_escalation_label": 1, "escalation_score": 0.7},
        {"sample_id": "p2", "split": "dev",
         "gold_escalation_label": 1, "escalation_score": 0.9},
    ]
    _write_predictions(pred_path, recs)
    with pytest.raises(ValueError, match="only one class"):
        fit_operating_threshold(
            predictions_path=pred_path,
            output_path=out_path,
            metric="macro_f1",
        )


def test_output_contains_test_split_used_false(tmp_path):
    pred_path = tmp_path / "dev_predictions.jsonl"
    out_path = tmp_path / "operating_threshold.json"
    _write_predictions(pred_path, _balanced_dev_records())
    state = fit_operating_threshold(
        predictions_path=pred_path,
        output_path=out_path,
    )
    assert state["test_split_used"] is False


def test_missing_required_field_errors(tmp_path):
    pred_path = tmp_path / "dev_predictions.jsonl"
    out_path = tmp_path / "operating_threshold.json"
    recs = [
        {"sample_id": "p1", "split": "dev",
         "gold_escalation_label": 1},  # missing escalation_score
    ]
    _write_predictions(pred_path, recs)
    with pytest.raises(ValueError, match="escalation_score"):
        fit_operating_threshold(pred_path, out_path)
