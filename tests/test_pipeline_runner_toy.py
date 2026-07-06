"""Tests that the V3.17 confidential pipeline runner can complete in toy mode.

Task Pack G Step 4 — verifies that `--mode toy` with the toy-safe default
stages runs end-to-end and produces a clean run_summary.json.

Hard boundary: this test never invokes real mode and never passes
--allow_private_data true. It only exercises CI-safe stages.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_v3_17_confidential_pipeline.py"

PYTHON = sys.executable
PYTHON_310 = r"C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe"
if Path(PYTHON_310).exists():
    PYTHON = PYTHON_310


def _run(extra_args, timeout=300):
    cmd = [PYTHON, str(SCRIPT_PATH)] + list(extra_args)
    result = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
    )
    return result.returncode, result.stdout


class TestToyRunnerCompletes:
    def test_toy_mode_completes_with_default_stages(self, tmp_path):
        out_dir = tmp_path / "run_out"
        rc, stdout = _run([
            "--mode", "toy",
            "--output_dir", str(out_dir),
        ])
        assert rc == 0, (
            f"toy mode failed (rc={rc}):\n{stdout[-2000:]}"
        )
        assert (out_dir / "run_summary.json").exists()
        assert (out_dir / "stage_status.csv").exists()
        assert (out_dir / "run_log.txt").exists()
        assert (out_dir / "config_snapshot.yaml").exists()

    def test_toy_mode_summary_reports_completed(self, tmp_path):
        out_dir = tmp_path / "run_out"
        _run(["--mode", "toy", "--output_dir", str(out_dir)])
        with open(out_dir / "run_summary.json", "r", encoding="utf-8") as f:
            summary = json.load(f)
        assert summary["mode"] == "toy"
        assert summary["overall_status"] == "completed"
        assert summary["n_stages_failed"] == 0
        assert summary["stages_failed"] == []

    def test_toy_mode_uses_toy_privacy_label(self, tmp_path):
        out_dir = tmp_path / "run_out"
        _run(["--mode", "toy", "--output_dir", str(out_dir)])
        with open(out_dir / "run_summary.json", "r", encoding="utf-8") as f:
            summary = json.load(f)
        for stage in summary["stage_details"]:
            assert stage.get("real_or_toy") == "toy", (
                f"Stage {stage.get('stage_name')} real_or_toy != toy"
            )
            assert stage.get("privacy_mode") == "toy"

    def test_toy_mode_stage_status_csv_has_new_metadata_columns(
        self, tmp_path
    ):
        out_dir = tmp_path / "run_out"
        _run(["--mode", "toy", "--output_dir", str(out_dir)])
        with open(
            out_dir / "stage_status.csv", "r", encoding="utf-8", newline=""
        ) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        required = {
            "stage_name", "status", "start_time", "end_time",
            "runtime_seconds", "output_dir", "error_message",
            "privacy_mode", "real_or_toy",
        }
        assert rows, "stage_status.csv is empty"
        cols = set(reader.fieldnames or [])
        assert required.issubset(cols), (
            f"stage_status.csv missing columns: {required - cols}"
        )
        for row in rows:
            assert row["privacy_mode"] == "toy"
            assert row["real_or_toy"] == "toy"
            assert row["status"] in {"ok", "ok_with_findings", "failed"}

    def test_toy_mode_single_toy_demo_stage(self, tmp_path):
        out_dir = tmp_path / "run_out"
        rc, stdout = _run([
            "--mode", "toy",
            "--stages", "toy_demo",
            "--output_dir", str(out_dir),
        ])
        assert rc == 0, f"toy_demo stage failed: {stdout[-2000:]}"
        with open(out_dir / "run_summary.json", "r", encoding="utf-8") as f:
            summary = json.load(f)
        assert summary["n_stages_requested"] == 1
        assert summary["n_stages_completed"] == 1
        assert summary["stages_completed"] == ["toy_demo"]


class TestRealModeGating:
    """Ensure real mode is never auto-triggered from toy calls."""

    def test_real_mode_rejected_without_allow_private_data(self):
        rc, stdout = _run(["--mode", "real"])
        assert rc == 2
        assert "requires --allow_private_data true" in stdout

    def test_real_mode_rejected_with_false(self):
        rc, stdout = _run([
            "--mode", "real", "--allow_private_data", "false"
        ])
        assert rc == 2
        assert "requires --allow_private_data true" in stdout

    def test_toy_mode_never_passes_allow_private_data(self, tmp_path):
        """If toy mode silently enabled --allow_private_data, that would be
        a critical regression. Verify the runner does not do this."""
        out_dir = tmp_path / "run_out"
        rc, stdout = _run([
            "--mode", "toy",
            "--output_dir", str(out_dir),
        ])
        # toy mode should succeed WITHOUT --allow_private_data
        assert rc == 0
        # And the run_summary should reflect toy privacy mode
        with open(out_dir / "run_summary.json", "r", encoding="utf-8") as f:
            summary = json.load(f)
        assert summary["mode"] == "toy"
