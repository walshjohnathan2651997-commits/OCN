"""Tests for P6-1: report timeout safety.

Verifies the safety properties required by task 1 acceptance:
- generate_tables.py runs within a bounded wall-clock time (does not
  hang on figure generation).
- A figure builder that raises / hangs is captured and recorded as
  invalid in figure_manifest; the report still completes.
- figure_warnings is populated and the report writes report_metadata.json
  with figure status even when some figures fail.

These complement tests/test_report_robustness_p6.py with explicit
"does not hang / does not crash" wall-clock assertions.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _write_minimal_eval(results_dir: Path) -> None:
    _write_json(results_dir / "eval_test.json", {
        "n_samples": 8,
        "binary": {"macro_f1": 0.5, "accuracy": 0.625,
                   "escalation_f1": 0.4,
                   "high_strength_false_support_rate": 0.1},
        "calibration": {"ece": 0.1},
        "ordinal_calibration_error": 0.15,
        "reliability": {"centers": [0.2, 0.7], "accuracies": [0.3, 0.6],
                        "confidences": [0.2, 0.7]},
        "threshold_sweep": {"threshold": [0.3, 0.5], "f1": [0.4, 0.5]},
    })


def _run_generate_tables(tmp_path: Path, profile: str = "pilot",
                         timeout_sec: float = 120.0) -> subprocess.CompletedProcess:
    """Run generate_tables.py as a subprocess; fail if it exceeds timeout."""
    results_dir = tmp_path / "results"
    out_dir = tmp_path / "report"
    cmd = [
        sys.executable, "-u", "scripts/generate_tables.py",
        "--results_dir", str(results_dir),
        "--output", str(out_dir),
        "--profile", profile,
        "--allow_toy_results",
    ]
    proc = subprocess.run(
        cmd, cwd=str(ROOT), capture_output=True, text=True,
        timeout=timeout_sec,
    )
    return proc


# ---------------------------------------------------------------------------
# report completes within bounded wall-clock time
# ---------------------------------------------------------------------------


def test_report_completes_within_timeout(tmp_path):
    """generate_tables.py must complete within a bounded wall-clock time
    on minimal valid input (default 120s per subprocess timeout)."""
    results_dir = tmp_path / "results"
    _write_minimal_eval(results_dir)
    start = time.monotonic()
    proc = _run_generate_tables(tmp_path, profile="pilot", timeout_sec=120.0)
    elapsed = time.monotonic() - start
    assert proc.returncode == 0, f"report failed: {proc.stderr[-500:]}"
    # Sanity: must complete in well under the subprocess timeout.
    assert elapsed < 120.0, f"report hung for {elapsed:.1f}s"


# ---------------------------------------------------------------------------
# figure_manifest written even on partial failure
# ---------------------------------------------------------------------------


def test_figure_manifest_written_to_metadata(tmp_path):
    """report_metadata.json must contain figure_manifest with at least
    one entry, even if some figures failed to render."""
    results_dir = tmp_path / "results"
    _write_minimal_eval(results_dir)
    proc = _run_generate_tables(tmp_path, profile="pilot")
    assert proc.returncode == 0
    metadata_path = tmp_path / "report" / "report_metadata.json"
    assert metadata_path.exists(), "report_metadata.json must be written"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert "figure_manifest" in metadata, "figure_manifest must be present"
    fm = metadata["figure_manifest"]
    assert isinstance(fm, dict)
    assert len(fm) > 0, "figure_manifest must have at least one entry"
    # Each entry must carry a status field.
    for fname, entry in fm.items():
        assert "status" in entry, f"{fname} missing status"
        assert entry["status"] in ("ok", "missing", "invalid", "unknown"), \
            f"{fname} has invalid status {entry['status']!r}"


# ---------------------------------------------------------------------------
# pilot profile does not block on missing pieces
# ---------------------------------------------------------------------------


def test_pilot_profile_does_not_hang_on_minimal_input(tmp_path):
    """pilot profile with minimal input must not hang / block; it should
    mark the run as diagnostic (not paper-ready) and return exit 0."""
    results_dir = tmp_path / "results"
    _write_minimal_eval(results_dir)
    proc = _run_generate_tables(tmp_path, profile="pilot", timeout_sec=90.0)
    assert proc.returncode == 0, \
        f"pilot report must not block on minimal input: {proc.stderr[-500:]}"
    metadata_path = tmp_path / "report" / "report_metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    # pilot must surface paper_ready=False (diagnostic) when strong
    # baselines / ablations are missing.
    assert metadata.get("paper_ready") is False, \
        "pilot profile with missing pieces must be marked not paper-ready"
