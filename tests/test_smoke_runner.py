"""Tests for scripts/run_smoke_minimal.py summary behavior.

P0 (ocn-25): verify that the smoke runner writes a correct
smoke_summary.json in all three states: ok, failed, timeout.

The summary must never stay "running" after the runner exits.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import the module to access _run_step and _write_summary.
sys.path.insert(0, str(ROOT / "scripts"))
import importlib.util

spec = importlib.util.spec_from_file_location(
    "run_smoke_minimal", ROOT / "scripts" / "run_smoke_minimal.py"
)
smoke_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke_mod)


def test_write_summary_creates_json(tmp_path):
    """_write_summary must atomically write a JSON file."""
    summary_path = tmp_path / "smoke_summary.json"
    payload = {"status": "ok", "steps": [{"step": "validate", "status": "ok"}]}
    smoke_mod._write_summary(summary_path, payload)
    assert summary_path.exists()
    loaded = json.loads(summary_path.read_text(encoding="utf-8"))
    assert loaded["status"] == "ok"
    assert loaded["steps"][0]["step"] == "validate"


def test_run_step_success(tmp_path):
    """_run_step must return status=ok when subprocess succeeds."""
    log_dir = tmp_path / "logs"
    summary_path = tmp_path / "smoke_summary.json"
    summary_steps: list[dict] = []

    # Mock subprocess.run to return rc=0.
    fake_completed = MagicMock()
    fake_completed.returncode = 0
    with patch("subprocess.run", return_value=fake_completed):
        result = smoke_mod._run_step(
            [sys.executable, "-c", "print('ok')"],
            "validate",
            log_dir,
            step_timeout_sec=10,
            summary_path=summary_path,
            summary_steps=summary_steps,
        )
    assert result["status"] == "ok"
    assert result["returncode"] == 0
    # Summary must have been written with the step recorded.
    loaded = json.loads(summary_path.read_text(encoding="utf-8"))
    assert loaded["status"] == "running"  # last write before step completes
    assert loaded["current_step"] == "validate"


def test_run_step_failure(tmp_path):
    """_run_step must return status=failed when subprocess returns non-zero."""
    log_dir = tmp_path / "logs"
    summary_path = tmp_path / "smoke_summary.json"
    summary_steps: list[dict] = []

    fake_completed = MagicMock()
    fake_completed.returncode = 1
    with patch("subprocess.run", return_value=fake_completed):
        result = smoke_mod._run_step(
            [sys.executable, "-c", "sys.exit(1)"],
            "train",
            log_dir,
            step_timeout_sec=10,
            summary_path=summary_path,
            summary_steps=summary_steps,
        )
    assert result["status"] == "failed"
    assert result["returncode"] == 1
    # The step must be appended to summary_steps.
    assert len(summary_steps) == 1
    assert summary_steps[0]["status"] == "failed"


def test_run_step_timeout(tmp_path):
    """_run_step must return status=timeout when subprocess exceeds timeout."""
    import subprocess as sp

    log_dir = tmp_path / "logs"
    summary_path = tmp_path / "smoke_summary.json"
    summary_steps: list[dict] = []

    with patch("subprocess.run", side_effect=sp.TimeoutExpired(cmd=[], timeout=1)):
        result = smoke_mod._run_step(
            [sys.executable, "-c", "import time; time.sleep(100)"],
            "eval",
            log_dir,
            step_timeout_sec=1,
            summary_path=summary_path,
            summary_steps=summary_steps,
        )
    assert result["status"] == "timeout"
    assert result["returncode"] == 124
    assert len(summary_steps) == 1
    assert summary_steps[0]["status"] == "timeout"


def test_run_step_exception(tmp_path):
    """_run_step must return status=failed on unexpected exception."""
    log_dir = tmp_path / "logs"
    summary_path = tmp_path / "smoke_summary.json"
    summary_steps: list[dict] = []

    with patch("subprocess.run", side_effect=RuntimeError("boom")):
        result = smoke_mod._run_step(
            [sys.executable, "-c", "pass"],
            "validate",
            log_dir,
            step_timeout_sec=10,
            summary_path=summary_path,
            summary_steps=summary_steps,
        )
    assert result["status"] == "failed"
    assert result["returncode"] == 1
