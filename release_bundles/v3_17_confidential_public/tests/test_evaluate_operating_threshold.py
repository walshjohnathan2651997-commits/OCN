"""Tests for P3-8: evaluate_model.py operating threshold state support.

Verifies:
- load_operating_threshold_state loads a valid state and returns the
  selected_threshold.
- threshold_state with test_split_used=true is rejected.
- when no state is provided, threshold_provenance="manual_or_default".
- paper_full profile requires a valid state (metric_valid=false otherwise).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.evaluate_model import load_operating_threshold_state


class _StubLogger:
    def __init__(self):
        self.messages: list[str] = []

    def info(self, msg: str) -> None:
        self.messages.append(msg)

    def warning(self, msg: str) -> None:
        self.messages.append(msg)

    def error(self, msg: str) -> None:
        self.messages.append(msg)


def _write_state(path: Path, **overrides) -> None:
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


def test_load_valid_operating_threshold_state(tmp_path):
    state_path = tmp_path / "operating_threshold.json"
    _write_state(state_path, selected_threshold=0.42)
    logger = _StubLogger()
    block, thr = load_operating_threshold_state(
        state_path=str(state_path),
        cli_threshold=0.5,
        logger=logger,
    )
    assert thr == pytest.approx(0.42)
    assert block["selected_threshold"] == pytest.approx(0.42)
    assert block["source_split"] == "dev"
    assert block["test_split_used"] is False
    assert block["metric_optimized"] == "macro_f1"
    assert block["source"] == "dev_fit"
    assert block["paper_valid"] is True


def test_state_with_test_split_used_is_rejected(tmp_path):
    state_path = tmp_path / "operating_threshold.json"
    _write_state(state_path, test_split_used=True)
    logger = _StubLogger()
    with pytest.raises(SystemExit):
        load_operating_threshold_state(
            state_path=str(state_path),
            cli_threshold=0.5,
            logger=logger,
        )
    # Error message must mention test_split_used=true / forbidden.
    assert any("test_split_used" in m or "forbidden" in m for m in logger.messages)


def test_missing_state_file_errors(tmp_path):
    state_path = tmp_path / "does_not_exist.json"
    logger = _StubLogger()
    with pytest.raises(SystemExit):
        load_operating_threshold_state(
            state_path=str(state_path),
            cli_threshold=0.5,
            logger=logger,
        )


def test_no_state_returns_manual_or_default_block():
    logger = _StubLogger()
    block, thr = load_operating_threshold_state(
        state_path=None,
        cli_threshold=0.5,
        logger=logger,
    )
    assert thr == 0.5
    assert block["source"] == "manual_or_default"
    assert block["selected_threshold"] == 0.5
    assert block["source_split"] is None
    assert block["metric_optimized"] is None
    assert block["paper_valid"] is False


def test_state_overrides_cli_threshold(tmp_path):
    state_path = tmp_path / "operating_threshold.json"
    _write_state(state_path, selected_threshold=0.27)
    block, thr = load_operating_threshold_state(
        state_path=str(state_path),
        cli_threshold=0.5,
        logger=_StubLogger(),
    )
    # The fitted threshold (0.27) must override the CLI default (0.5).
    assert thr == pytest.approx(0.27)
    assert block["selected_threshold"] == pytest.approx(0.27)
