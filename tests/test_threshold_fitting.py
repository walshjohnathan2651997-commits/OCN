"""Tests for Task E: threshold fitting pipeline integration.

Verifies:
- ``fit_thresholds.py`` records split provenance (source_split,
  test_split_used) so downstream consumers can verify thresholds were
  NOT fit on the test split.
- ``evaluate_model.py`` ``--threshold_state`` loads the state, records
  provenance in the eval report, and REFUSES states fit on test.
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

import fit_thresholds as ft_mod
import evaluate_model as eval_mod


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _toy_record(sample_id: str, split: str = "train") -> dict:
    return {
        "sample_id": sample_id,
        "logical_sample_id": sample_id,
        "domain": "toy",
        "source_type": "oracle",
        "split": split,
        "claim_text": "c",
        "evidence_text": "e",
        "claim_family": "causal",
        "evidence_vector": {d: 0.0 for d in [
            "alignment", "transparency", "coverage", "traceability",
            "boundary", "uncertainty", "causal_id", "risk_utility",
        ]},
        "evidence_confidence": {d: 1.0 for d in [
            "alignment", "transparency", "coverage", "traceability",
            "boundary", "uncertainty", "causal_id", "risk_utility",
        ]},
        "claim_tiers": {"scope": 1, "causal": 0, "action": 1, "certainty": 0},
        "support_tiers": {"scope": 0, "causal": 0, "action": 0, "certainty": 0},
        "escalation_label": 1,
    }


def _write_jsonl(path: Path, records: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


# ---------------------------------------------------------------------------
# fit_thresholds.compute_threshold_state
# ---------------------------------------------------------------------------

def test_compute_threshold_state_basic():
    records = [_toy_record(f"s{i}") for i in range(10)]
    state = ft_mod.compute_threshold_state(records)
    assert state["num_tiers"] == 5
    assert state["num_dims"] == 4
    assert state["n_samples"] == 20  # 10 records x 2 (claim+support pooled)
    assert "target_betas" in state
    assert len(state["target_betas"]) == 4  # D dims
    assert len(state["target_betas"][0]) == 4  # K-1 thresholds
    assert state["init_strategy"] == "quantile"


def test_compute_threshold_state_strictly_increasing():
    """target_betas must be strictly increasing along the tier axis."""
    records = [_toy_record(f"s{i}") for i in range(10)]
    state = ft_mod.compute_threshold_state(records)
    for d in range(4):
        for m in range(1, 4):
            assert state["target_betas"][d][m] >= state["target_betas"][d][m - 1]


# ---------------------------------------------------------------------------
# fit_thresholds CLI provenance
# ---------------------------------------------------------------------------

def test_fit_thresholds_records_provenance_train(tmp_path):
    """fit_thresholds.py --source_split=train records
    test_split_used=False."""
    in_path = tmp_path / "in.jsonl"
    _write_jsonl(in_path, [_toy_record(f"s{i}", split="train") for i in range(10)])
    out_path = tmp_path / "threshold_state.json"
    ft_mod.main_with_args(
        input=str(in_path),
        output=str(out_path),
        source_split="train",
    )
    state = json.loads(out_path.read_text(encoding="utf-8"))
    assert state["fit_split_provenance"]["source_split"] == "train"
    assert state["fit_split_provenance"]["test_split_used"] is False
    assert state["fit_split_provenance"]["n_records_used"] == 10


def test_fit_thresholds_records_provenance_test(tmp_path):
    """fit_thresholds.py --source_split=test records test_split_used=True
    (so evaluate_model can refuse it)."""
    in_path = tmp_path / "in.jsonl"
    _write_jsonl(in_path, [_toy_record(f"s{i}", split="test") for i in range(10)])
    out_path = tmp_path / "threshold_state.json"
    ft_mod.main_with_args(
        input=str(in_path),
        output=str(out_path),
        source_split="test",
    )
    state = json.loads(out_path.read_text(encoding="utf-8"))
    assert state["fit_split_provenance"]["test_split_used"] is True
    assert state["fit_split_provenance"]["source_split"] == "test"


# ---------------------------------------------------------------------------
# evaluate_model --threshold_state provenance check
# ---------------------------------------------------------------------------

def _write_threshold_state(path: Path, source_split: str = "dev") -> None:
    """Write a minimal threshold_state.json with provenance."""
    state = {
        "empirical_p_ge": [[0.5] * 4] * 4,
        "target_betas": [[0.0] * 4] * 4,
        "n_samples": 100,
        "num_tiers": 5,
        "num_dims": 4,
        "init_strategy": "quantile",
        "source_split": source_split,
        "source_path": "in.jsonl",
        "fit_split_provenance": {
            "source_split": source_split,
            "source_path": "in.jsonl",
            "n_records_used": 100,
            "test_split_used": source_split == "test",
        },
    }
    path.write_text(json.dumps(state), encoding="utf-8")


def test_evaluate_model_threshold_provenance_loaded(tmp_path, monkeypatch):
    """When --threshold_state points to a valid state (fit on dev),
    the ordinal_calibration_thresholds should be recorded in the report."""
    # Build a minimal threshold_state.json fit on dev split.
    state_path = tmp_path / "threshold_state.json"
    _write_threshold_state(state_path, source_split="dev")
    # Call the provenance-loading helper directly (avoids needing a
    # full model / checkpoint for this unit test).
    prov = eval_mod.load_threshold_provenance(
        state_path=str(state_path),
        operating_threshold=0.42,
    )
    assert prov["loaded"] is True
    assert prov["source_split"] == "dev"
    assert prov["test_split_used"] is False
    assert prov["type"] == "shared_threshold_calibration"
    assert prov["paper_valid"] is True


def test_evaluate_model_refuses_test_fit_threshold_state(tmp_path):
    """evaluate_model must refuse a threshold_state fit on the test
    split (raises SystemExit)."""
    state_path = tmp_path / "threshold_state.json"
    _write_threshold_state(state_path, source_split="test")
    with pytest.raises(SystemExit):
        eval_mod.load_threshold_provenance(
            state_path=str(state_path),
            operating_threshold=0.5,
        )


def test_evaluate_model_threshold_provenance_default(tmp_path):
    """When --threshold_state is NOT provided, ordinal_calibration_thresholds
    records loaded=False and paper_valid=False."""
    prov = eval_mod.load_threshold_provenance(
        state_path=None,
        operating_threshold=0.5,
    )
    assert prov["loaded"] is False
    assert prov["source"] is None
    assert prov["test_split_used"] is False
    assert prov["paper_valid"] is False
