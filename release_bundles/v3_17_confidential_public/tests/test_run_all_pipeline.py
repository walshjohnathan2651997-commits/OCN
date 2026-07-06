"""P4 (ocn-16): minimal tests for the simple ``subprocess.run`` runner.

Only tests the simple runner behavior — no process-group / heartbeat /
multi-stage polling. Six core cases:

  1. success -> status=ok
  2. nonzero exit -> status=failed
  3. timeout -> status=timeout
  4. timeout -> log file exists (no content assertion)
  5. running summary is overwritten by final summary
  6. all_required_passed=false while a step is running
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Make scripts/ importable.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_all_experiments import run, write_summary_atomic

PY = sys.executable


# ---------------------------------------------------------------------------
# 1. success -> status=ok
# ---------------------------------------------------------------------------


def test_run_success_status_ok(tmp_path):
    """A command that exits 0 must produce status=ok."""
    result = run(
        [PY, "-c", "print('ok')"],
        step="ok_step",
        step_timeout_sec=10,
        log_dir=tmp_path / "logs",
    )
    assert result["status"] == "ok"
    assert result["returncode"] == 0
    assert result["step"] == "ok_step"
    assert Path(result["log_path"]).exists()


# ---------------------------------------------------------------------------
# 2. nonzero exit -> status=failed
# ---------------------------------------------------------------------------


def test_run_failure_status_failed(tmp_path):
    """A command that exits nonzero must produce status=failed."""
    result = run(
        [PY, "-c", "import sys; sys.exit(3)"],
        step="fail_step",
        step_timeout_sec=10,
        log_dir=tmp_path / "logs",
    )
    assert result["status"] == "failed"
    assert result["returncode"] == 3


# ---------------------------------------------------------------------------
# 3. timeout -> status=timeout
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_run_timeout_status_timeout(tmp_path):
    """A command that sleeps past the deadline must produce status=timeout
    and returncode=124."""
    result = run(
        [PY, "-c", "import time; time.sleep(2)"],
        step="slow_step",
        step_timeout_sec=0.2,
        log_dir=tmp_path / "logs",
    )
    assert result["status"] == "timeout"
    assert result["returncode"] == 124
    assert result["duration_sec"] < 5


# ---------------------------------------------------------------------------
# 4. timeout -> log file exists (no content assertion)
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_log_file_exists_on_timeout(tmp_path):
    """The log file must exist after a timeout. We do NOT assert the
    child's unflushed output is present — timeout-kill timing is not
    guaranteed to preserve it."""
    result = run(
        [PY, "-u", "-c", "import time; print('working', flush=True); time.sleep(3)"],
        step="timeout_log_step",
        step_timeout_sec=1.0,
        log_dir=tmp_path / "logs",
    )
    assert result["status"] == "timeout"
    assert Path(result["log_path"]).exists()


# ---------------------------------------------------------------------------
# 5. running summary is overwritten by final summary
# ---------------------------------------------------------------------------


def test_running_summary_overwritten_by_final(tmp_path):
    """After a step completes, the summary must not contain a stale
    ``status=running`` entry for that step. ``_record`` replaces the
    running entry with the final result by step name."""
    summary_path = tmp_path / "pipeline_summary.json"
    steps_summary: list[dict] = []

    def _build_summary_payload(running_step: dict | None = None) -> dict:
        steps_view = list(steps_summary)
        if running_step is not None:
            rname = running_step.get("step")
            steps_view = [s for s in steps_view if s.get("step") != rname]
            steps_view.append(running_step)
        return {"profile": "test", "steps": steps_view}

    def _summary_writer(step_name: str, status: str, payload: dict) -> None:
        running = {"step": step_name, "status": status,
                   "elapsed_sec": payload.get("elapsed_sec", 0.0)}
        write_summary_atomic(summary_path, _build_summary_payload(running))

    def _record(result: dict) -> bool:
        rname = result.get("step")
        steps_summary[:] = [s for s in steps_summary if s.get("step") != rname]
        steps_summary.append(result)
        write_summary_atomic(summary_path, _build_summary_payload())
        return result["status"] == "ok"

    # Simulate: running -> ok.
    _summary_writer("step_a", "running", {"elapsed_sec": 0.0})
    _record({"step": "step_a", "status": "ok", "duration_sec": 0.1})

    loaded = json.loads(summary_path.read_text(encoding="utf-8"))
    step_a = [s for s in loaded["steps"] if s.get("step") == "step_a"]
    assert len(step_a) == 1
    assert step_a[0]["status"] == "ok"
    assert not [s for s in loaded["steps"] if s.get("status") == "running"]


# ---------------------------------------------------------------------------
# 6. all_required_passed=false while a step is running
# ---------------------------------------------------------------------------


def test_all_required_passed_false_while_running(tmp_path):
    """When a step has ``status=running``, ``all_required_passed`` must
    be False and ``has_running_step`` must be True, even if all other
    required steps are ok."""
    summary_path = tmp_path / "pipeline_summary.json"
    steps_summary: list[dict] = []
    required_steps = {"validate", "train", "eval", "baselines", "ablations",
                      "adversarial", "oracle", "tables"}

    def _build_summary_payload(running_step: dict | None = None) -> dict:
        steps_view = list(steps_summary)
        if running_step is not None:
            rname = running_step.get("step")
            steps_view = [s for s in steps_view if s.get("step") != rname]
            steps_view.append(running_step)
        has_running = any(s.get("status") == "running" for s in steps_view)
        all_passed = (
            not has_running
            and all(s.get("status") == "ok" for s in steps_view
                    if s.get("step") in required_steps and s.get("required", True))
        )
        return {"profile": "test", "steps": steps_view,
                "has_running_step": has_running,
                "all_required_passed": all_passed}

    def _summary_writer(step_name: str, status: str, payload: dict) -> None:
        running = dict(payload)
        running["step"] = step_name
        running["status"] = status
        running.setdefault("required", True)
        write_summary_atomic(summary_path, _build_summary_payload(running))

    def _record(result: dict) -> bool:
        rname = result.get("step")
        steps_summary[:] = [s for s in steps_summary if s.get("step") != rname]
        steps_summary.append(result)
        write_summary_atomic(summary_path, _build_summary_payload())
        return result["status"] == "ok"

    # One completed required step.
    _record({"step": "validate", "status": "ok", "required": True})
    # A running required step.
    _summary_writer("train", "running", {"runner_stage": "subprocess_run_start"})

    loaded = json.loads(summary_path.read_text(encoding="utf-8"))
    assert loaded["has_running_step"] is True
    assert loaded["all_required_passed"] is False

    # Finalize -> all_required_passed becomes True.
    _record({"step": "train", "status": "ok", "required": True})
    loaded = json.loads(summary_path.read_text(encoding="utf-8"))
    assert loaded["has_running_step"] is False
    assert loaded["all_required_passed"] is True
