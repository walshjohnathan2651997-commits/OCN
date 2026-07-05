"""Tests for stage_runner.run_step timeout handling (ocn-20 P2).

Verifies that when a subprocess exceeds its timeout:
  1. result["status"] == "timeout"
  2. result["returncode"] == 124
  3. stage_summary.json immediately reflects status == "timeout"
  4. log file exists and contains the timeout marker
  5. the stage script returns non-zero
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.stage_runner import (
    run_step, finalize_running_steps_as_failed, write_summary,
)


def test_run_step_timeout_updates_summary(tmp_path: Path):
    """run_step must mark status=timeout and write summary immediately."""
    log_dir = tmp_path / "logs"
    summary_path = tmp_path / "stage_summary.json"
    summary_steps: list[dict] = []

    # Command that sleeps for 60 seconds; we will time out after 1 second.
    cmd = [sys.executable, "-u", "-c", "import time; time.sleep(60)"]

    t0 = time.monotonic()
    result = run_step(
        cmd,
        step="sleep_step",
        log_dir=log_dir,
        step_timeout_sec=1,
        summary_path=summary_path,
        summary_steps=summary_steps,
        stage="test_stage",
    )
    elapsed = time.monotonic() - t0

    # Should return well before the 60s sleep completes.
    assert elapsed < 30, f"run_step did not return promptly: {elapsed:.1f}s"

    # 1. result status
    assert result["status"] == "timeout", result
    # 2. returncode
    assert result["returncode"] == 124, result

    # 3. stage_summary.json reflects timeout immediately
    assert summary_path.exists(), "stage_summary.json not written"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["status"] == "timeout", summary
    assert summary["current_step"] == "sleep_step", summary
    steps = summary["steps"]
    assert len(steps) == 1
    assert steps[0]["status"] == "timeout", steps[0]
    assert steps[0]["returncode"] == 124, steps[0]

    # 4. log file exists and contains timeout marker
    log_path = log_dir / "sleep_step.log"
    assert log_path.exists(), f"log file not created: {log_path}"
    log_text = log_path.read_text(encoding="utf-8", errors="replace")
    assert "timeout after" in log_text, f"no timeout marker in log: {log_text!r}"

    # 5. summary_steps list was updated in-place
    assert len(summary_steps) == 1
    assert summary_steps[0]["status"] == "timeout"


def test_run_step_timeout_marker_format(tmp_path: Path):
    """The timeout marker must include the stage name and timeout value."""
    log_dir = tmp_path / "logs"
    summary_path = tmp_path / "stage_summary.json"
    summary_steps: list[dict] = []

    cmd = [sys.executable, "-u", "-c", "import time; time.sleep(60)"]

    run_step(
        cmd,
        step="marker_step",
        log_dir=log_dir,
        step_timeout_sec=2,
        summary_path=summary_path,
        summary_steps=summary_steps,
        stage="marker_stage",
    )

    log_path = log_dir / "marker_step.log"
    log_text = log_path.read_text(encoding="utf-8", errors="replace")
    # Expected format: "[marker_stage] timeout after 2s"
    assert "[marker_stage] timeout after 2s" in log_text, \
        f"unexpected marker format: {log_text!r}"


# ---------------------------------------------------------------------------
# ocn-30 P0: finalize_running_steps_as_failed防腐保护
# ---------------------------------------------------------------------------

def test_finalize_running_step_marked_failed(tmp_path: Path):
    """A step left in 'running' must be flipped to 'failed'."""
    summary_path = tmp_path / "stage_summary.json"
    payload = {
        "stage": "train_eval",
        "status": "running",
        "current_step": "eval_test",
        "steps": [
            {"step": "train", "status": "ok"},
            {"step": "eval_test", "status": "running"},
        ],
    }
    write_summary(summary_path, payload)

    finalize_running_steps_as_failed(summary_path)

    out = json.loads(summary_path.read_text(encoding="utf-8"))
    assert out["status"] == "failed"
    running_steps = [s for s in out["steps"] if s["status"] == "running"]
    assert running_steps == [], f"still running steps: {running_steps}"
    failed_step = out["steps"][1]
    assert failed_step["status"] == "failed"
    assert failed_step["error"] == "interrupted before final status"
    # Already-finalized steps must be untouched.
    assert out["steps"][0]["status"] == "ok"


def test_finalize_already_failed_unchanged(tmp_path: Path):
    """A summary already in a final state must not be mutated."""
    summary_path = tmp_path / "stage_summary.json"
    payload = {
        "stage": "train_eval",
        "status": "ok",
        "steps": [
            {"step": "train", "status": "ok"},
            {"step": "eval_test", "status": "ok"},
        ],
    }
    write_summary(summary_path, payload)

    finalize_running_steps_as_failed(summary_path)

    out = json.loads(summary_path.read_text(encoding="utf-8"))
    assert out["status"] == "ok"
    assert all(s["status"] == "ok" for s in out["steps"])


def test_finalize_missing_file_no_error(tmp_path: Path):
    """A missing summary file must not raise."""
    summary_path = tmp_path / "does_not_exist.json"
    # Should be a no-op, not raise.
    finalize_running_steps_as_failed(summary_path)
    assert not summary_path.exists()


def test_finalize_corrupt_json_no_error(tmp_path: Path):
    """Corrupt JSON must not raise —防腐保护 must be defensive."""
    summary_path = tmp_path / "stage_summary.json"
    summary_path.write_text("{not valid json", encoding="utf-8")
    finalize_running_steps_as_failed(summary_path)
    # File is left as-is (we do not rewrite corrupt input).
    assert "{" in summary_path.read_text(encoding="utf-8")
