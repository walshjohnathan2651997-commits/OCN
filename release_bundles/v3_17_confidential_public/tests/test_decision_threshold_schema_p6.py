"""Tests for P6-2: decision_threshold / ordinal_calibration_thresholds schema.

Verifies:
- Loading operating_threshold.json produces a decision_threshold block
  with selected_threshold / source=dev_fit / source_split=dev /
  test_split_used=false / metric_optimized.
- When no operating_threshold_state is provided, decision_threshold has
  source=manual_or_default and paper_valid=False.
- A threshold state with test_split_used=true is refused (SystemExit).
- The old fields (operating_threshold / threshold_provenance) are no
  longer present in the eval report.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.evaluate_model import (
    load_operating_threshold_state,
    load_threshold_provenance,
)


class _StubLogger:
    def __init__(self):
        self.messages: list[str] = []

    def info(self, msg: str) -> None:
        self.messages.append(msg)

    def warning(self, msg: str) -> None:
        self.messages.append(msg)

    def error(self, msg: str) -> None:
        self.messages.append(msg)


def _write_operating_threshold_state(path: Path, **overrides) -> None:
    state = {
        "selected_threshold": 0.35,
        "metric_optimized": "macro_f1",
        "source_split": "dev",
        "n_records_used": 80,
        "test_split_used": False,
        "threshold_grid": {"min": 0.05, "max": 0.95, "num": 181},
        "best_metric_value": 0.62,
    }
    state.update(overrides)
    path.write_text(json.dumps(state), encoding="utf-8")


def _write_threshold_state(path: Path, source_split: str = "dev") -> None:
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


# ---------------------------------------------------------------------------
# decision_threshold field
# ---------------------------------------------------------------------------


def test_decision_threshold_loaded_from_operating_threshold_state(tmp_path):
    """When operating_threshold.json is loaded, decision_threshold block
    must contain selected_threshold / source=dev_fit / source_split /
    test_split_used=false / metric_optimized."""
    state_path = tmp_path / "operating_threshold.json"
    _write_operating_threshold_state(state_path, selected_threshold=0.35)
    block, thr = load_operating_threshold_state(
        state_path=str(state_path),
        cli_threshold=0.5,
        logger=_StubLogger(),
    )
    assert thr == pytest.approx(0.35)
    assert block["selected_threshold"] == pytest.approx(0.35)
    assert block["source"] == "dev_fit"
    assert block["source_split"] == "dev"
    assert block["test_split_used"] is False
    assert block["metric_optimized"] == "macro_f1"
    assert block["paper_valid"] is True


def test_decision_threshold_source_manual_or_default_when_no_state():
    """When no operating_threshold_state is provided, decision_threshold
    must have source=manual_or_default and paper_valid=False."""
    block, thr = load_operating_threshold_state(
        state_path=None,
        cli_threshold=0.5,
        logger=_StubLogger(),
    )
    assert block["source"] == "manual_or_default"
    assert block["selected_threshold"] == 0.5
    assert block["paper_valid"] is False


def test_decision_threshold_rejects_test_split_used(tmp_path):
    """operating_threshold_state with test_split_used=true must be refused
    (SystemExit)."""
    state_path = tmp_path / "operating_threshold.json"
    _write_operating_threshold_state(state_path, test_split_used=True)
    logger = _StubLogger()
    with pytest.raises(SystemExit):
        load_operating_threshold_state(
            state_path=str(state_path),
            cli_threshold=0.5,
            logger=logger,
        )
    assert any("test_split_used" in m or "forbidden" in m
               for m in logger.messages)


# ---------------------------------------------------------------------------
# ordinal_calibration_thresholds field
# ---------------------------------------------------------------------------


def test_ordinal_calibration_thresholds_loaded_from_threshold_state(tmp_path):
    """When threshold_state.json is loaded, ordinal_calibration_thresholds
    must record loaded=true / type=shared_threshold_calibration /
    source_split=dev / test_split_used=false."""
    state_path = tmp_path / "threshold_state.json"
    _write_threshold_state(state_path, source_split="dev")
    prov = load_threshold_provenance(
        state_path=str(state_path),
        operating_threshold=0.5,
        logger=_StubLogger(),
    )
    assert prov["loaded"] is True
    assert prov["type"] == "shared_threshold_calibration"
    assert prov["source_split"] == "dev"
    assert prov["test_split_used"] is False
    assert prov["paper_valid"] is True


def test_ordinal_calibration_thresholds_default_when_no_state():
    """When no threshold_state is provided, ordinal_calibration_thresholds
    must record loaded=false and paper_valid=false."""
    prov = load_threshold_provenance(
        state_path=None,
        operating_threshold=0.5,
        logger=_StubLogger(),
    )
    assert prov["loaded"] is False
    assert prov["source"] is None
    assert prov["paper_valid"] is False
    assert prov["type"] == "shared_threshold_calibration"


def test_ordinal_calibration_thresholds_rejects_test_fit(tmp_path):
    """threshold_state fit on the test split must be refused."""
    state_path = tmp_path / "threshold_state.json"
    _write_threshold_state(state_path, source_split="test")
    with pytest.raises(SystemExit):
        load_threshold_provenance(
            state_path=str(state_path),
            operating_threshold=0.5,
            logger=_StubLogger(),
        )


# ---------------------------------------------------------------------------
# Old fields no longer present in the decision_threshold block
# ---------------------------------------------------------------------------


def test_old_threshold_provenance_field_not_in_decision_threshold_block(tmp_path):
    """The decision_threshold block must NOT contain the legacy
    threshold_provenance field (replaced by source)."""
    state_path = tmp_path / "operating_threshold.json"
    _write_operating_threshold_state(state_path, selected_threshold=0.4)
    block, _ = load_operating_threshold_state(
        state_path=str(state_path),
        cli_threshold=0.5,
        logger=_StubLogger(),
    )
    assert "threshold_provenance" not in block
    assert "operating_threshold" not in block  # legacy top-level field


def test_old_threshold_provenance_field_not_in_ordinal_calib_block(tmp_path):
    """The ordinal_calibration_thresholds block must NOT contain legacy
    fields (threshold_state_loaded / threshold_state_source_split /
    operating_threshold_source)."""
    state_path = tmp_path / "threshold_state.json"
    _write_threshold_state(state_path, source_split="dev")
    prov = load_threshold_provenance(
        state_path=str(state_path),
        operating_threshold=0.5,
        logger=_StubLogger(),
    )
    assert "threshold_state_loaded" not in prov
    assert "threshold_state_source_split" not in prov
    assert "operating_threshold_source" not in prov
    assert "operating_threshold" not in prov
