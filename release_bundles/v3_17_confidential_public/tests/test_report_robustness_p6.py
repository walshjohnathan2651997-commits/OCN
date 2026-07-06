"""Tests for P6-1: report generation robustness.

Verifies:
- report (generate_tables.py) does not crash when input has many NA
  values in tables.
- monotonic_violation figure does not crash on NA rows.
- figure generation failure writes a warning and records the figure as
  missing/invalid in the manifest — does not block the whole report.
- pilot profile missing strong baselines does not crash and is marked
  diagnostic (not paper-ready).
- paper_full profile missing strong baselines returns a blocking error
  (non-zero exit).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import generate_tables as gt_mod


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _write_minimal_eval(results_dir: Path, with_na: bool = False) -> None:
    """Write a minimal eval_test.json. If with_na, metrics are NA/None."""
    if with_na:
        eval_data = {
            "n_samples": 8,
            "binary": {
                "macro_f1": None,
                "accuracy": "NA",
                "escalation_f1": float("nan"),
                "high_strength_false_support_rate": None,
            },
            "calibration": {"ece": float("nan")},
            "ordinal_calibration_error": None,
            "reliability": {"centers": [], "accuracies": []},
            "threshold_sweep": {"threshold": [], "f1": []},
        }
    else:
        eval_data = {
            "n_samples": 8,
            "binary": {
                "macro_f1": 0.5,
                "accuracy": 0.625,
                "escalation_f1": 0.4,
                "high_strength_false_support_rate": 0.1,
            },
            "calibration": {"ece": 0.1},
            "ordinal_calibration_error": 0.15,
            "reliability": {"centers": [0.2, 0.7], "accuracies": [0.3, 0.6],
                            "confidences": [0.2, 0.7]},
            "threshold_sweep": {"threshold": [0.3, 0.5], "f1": [0.4, 0.5]},
        }
    _write_json(results_dir / "eval_test.json", eval_data)


def _run_generate_tables(tmp_path: Path, profile: str,
                         data_path: Path | None = None,
                         extra_args: list[str] | None = None) -> int:
    """Run generate_tables.py as a subprocess and return exit code."""
    results_dir = tmp_path / "results"
    out_dir = tmp_path / "report"
    cmd = [
        sys.executable, "-u", "scripts/generate_tables.py",
        "--results_dir", str(results_dir),
        "--output", str(out_dir),
        "--profile", profile,
    ]
    if data_path is not None:
        cmd += ["--data_path", str(data_path)]
    if profile != "paper_full":
        cmd += ["--allow_toy_results"]
    if extra_args:
        cmd += extra_args
    proc = subprocess.run(
        cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=120,
    )
    return proc.returncode


# ---------------------------------------------------------------------------
# NA / NaN robustness
# ---------------------------------------------------------------------------


def test_report_handles_many_na_without_crashing(tmp_path):
    """generate_tables must not crash when input has many NA / None / nan
    values in tables."""
    results_dir = tmp_path / "results"
    _write_minimal_eval(results_dir, with_na=True)
    # Write minimal ablations with NA values.
    _write_json(results_dir / "ablations" / "ablations_results.json", {
        "no_calibration": {
            "macro_f1": None, "auroc": "NA",
            "claim_ordinal_ece": float("nan"),
            "support_ordinal_ece": None,
            "joint_ordinal_ece": float("nan"),
            "brier_escalation": None, "reliability_slope": "NA",
            "threshold_sensitivity": None, "n_samples": 0,
            "metric_valid": False,
        },
    })
    _write_json(results_dir / "adversarial" / "adversarial_results.json", {
        "adv1": {"escalation_f1": None, "n_samples": 0,
                  "metric_valid": False},
    })
    data_path = tmp_path / "data.jsonl"
    data_path.write_text(
        json.dumps({"split": "train", "escalation_label": 1}) + "\n"
        + json.dumps({"split": "test", "escalation_label": 0}) + "\n",
        encoding="utf-8",
    )
    rc = _run_generate_tables(tmp_path, profile="pilot", data_path=data_path)
    # Must exit 0 (NA handled gracefully). paper_full would fail due to
    # missing strong baselines; pilot should succeed.
    assert rc == 0, "generate_tables crashed on NA inputs"


def test_monotonic_violation_figure_handles_na_rows(tmp_path):
    """plot_monotonic_violation must not crash when rows have NA rates."""
    results_dir = tmp_path / "results"
    # Write ablations with one valid + one NA row.
    _write_json(results_dir / "ablations" / "ablations_results.json", {
        "full": {
            "escalation_f1": 0.5,
            "high_strength_false_support_rate": 0.1,
            "monotonic_violation_rate": 0.2,
            "truncation_violation_rate": 0.1,
            "n_samples": 8,
            "metric_valid": True,
        },
        "no_constraint": {
            "escalation_f1": None,
            "high_strength_false_support_rate": None,
            "monotonic_violation_rate": None,
            "truncation_violation_rate": "NA",
            "n_samples": 0,
            "metric_valid": False,
        },
    })
    out_path = tmp_path / "monotonic_violation.png"
    # Should not raise.
    gt_mod.plot_monotonic_violation(results_dir, out_path)
    # File should be written (with "no valid data" message or valid bars).
    assert out_path.exists(), "monotonic_violation.png was not written"


# ---------------------------------------------------------------------------
# Figure manifest: failure -> warning + invalid in manifest
# ---------------------------------------------------------------------------


def test_figure_failure_writes_warning_and_invalid_in_manifest(tmp_path,
                                                                 monkeypatch):
    """When a figure builder raises, generate_tables.py must:
      - record the figure as 'invalid' in figure_manifest,
      - add a warning to figure_warnings,
      - still exit 0 (not crash).
    """
    results_dir = tmp_path / "results"
    _write_minimal_eval(results_dir, with_na=False)
    data_path = tmp_path / "data.jsonl"
    data_path.write_text(
        json.dumps({"split": "train", "escalation_label": 1}) + "\n"
        + json.dumps({"split": "test", "escalation_label": 0}) + "\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "report"

    # Monkeypatch one figure builder to raise.
    def _boom(results_dir, out_path):
        raise RuntimeError("simulated figure failure")
    monkeypatch.setattr(gt_mod, "plot_calibration_curve", _boom)

    cmd = [
        sys.executable, "-u", "-c",
        "import sys; sys.path.insert(0, 'scripts'); "
        "import generate_tables as g; "
        "g.plot_calibration_curve = lambda rd, op: (_ for _ in ()).throw("
        "RuntimeError('simulated')); "
        "import runpy; runpy.run(g.__file__, run_name='__main__')",
        "--results_dir", str(results_dir),
        "--output", str(out_dir),
        "--profile", "pilot",
        "--data_path", str(data_path),
        "--allow_toy_results",
    ]
    # The inline patching is fragile in subprocess; instead patch in-process.
    # Run generate_tables.main() in-process with monkeypatched builder.
    import argparse
    monkeypatch.setattr(sys, "argv", [
        "generate_tables.py",
        "--results_dir", str(results_dir),
        "--output", str(out_dir),
        "--profile", "pilot",
        "--data_path", str(data_path),
        "--allow_toy_results",
    ])
    # Patch the figure builder AFTER main() captures it via the figure_specs
    # list. Since figure_specs is built inside main(), patch the module-level
    # function so the reference inside main() picks up the patched version.
    monkeypatch.setattr(gt_mod, "plot_calibration_curve", _boom)
    try:
        gt_mod.main()
    except SystemExit:
        pass

    metadata_path = out_dir / "report_metadata.json"
    assert metadata_path.exists(), "report_metadata.json not written"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert "figure_manifest" in metadata
    manifest = metadata["figure_manifest"]
    assert "calibration_curve.png" in manifest
    assert manifest["calibration_curve.png"]["status"] == "invalid"
    assert "calibration_curve.png" in str(metadata["figure_warnings"])
    # Other figures should still be ok.
    assert manifest["threshold_sensitivity.png"]["status"] == "ok"


# ---------------------------------------------------------------------------
# pilot profile: missing strong baselines -> diagnostic, not crash
# ---------------------------------------------------------------------------


def test_pilot_missing_strong_baselines_does_not_crash(tmp_path):
    """pilot profile missing strong baselines must not crash; must be
    marked diagnostic (paper_ready=False)."""
    results_dir = tmp_path / "results"
    _write_minimal_eval(results_dir, with_na=False)
    # baselines_results.json missing strong baselines entirely.
    _write_json(results_dir / "baselines" / "baselines_results.json", {
        "rule_baseline": {"macro_f1": 0.3, "n_samples": 8,
                          "paper_valid": False},
    })
    data_path = tmp_path / "data.jsonl"
    data_path.write_text(
        json.dumps({"split": "train", "escalation_label": 1}) + "\n"
        + json.dumps({"split": "test", "escalation_label": 0}) + "\n",
        encoding="utf-8",
    )
    rc = _run_generate_tables(tmp_path, profile="pilot", data_path=data_path)
    assert rc == 0, "pilot profile should not crash on missing strong baselines"
    metadata_path = tmp_path / "report" / "report_metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    # paper_ready must be False (diagnostic).
    assert metadata["paper_ready"] is False
    # strong_baselines_missing should list all 4 strong baselines.
    assert len(metadata["strong_baselines_missing"]) == 4
    # No blocking errors in pilot.
    assert metadata["blocking_errors"] == []


# ---------------------------------------------------------------------------
# paper_full: missing strong baselines -> blocking error (non-zero exit)
# ---------------------------------------------------------------------------


def test_paper_full_missing_strong_baselines_returns_blocking_error(tmp_path):
    """paper_full profile missing strong baselines must return a blocking
    error (non-zero exit code) and record blocking_errors."""
    results_dir = tmp_path / "results"
    _write_minimal_eval(results_dir, with_na=False)
    # baselines_results.json missing all strong baselines.
    _write_json(results_dir / "baselines" / "baselines_results.json", {
        "rule_baseline": {"macro_f1": 0.3, "n_samples": 8,
                          "paper_valid": False},
    })
    # paper_full requires all ablation variants too; write minimal valid.
    _write_json(results_dir / "ablations" / "ablations_results.json", {
        k: {"macro_f1": 0.5, "auroc": 0.6, "claim_ordinal_ece": 0.1,
            "support_ordinal_ece": 0.1, "joint_ordinal_ece": 0.1,
            "brier_escalation": 0.2, "reliability_slope": 1.0,
            "threshold_sensitivity": 0.1, "n_samples": 8,
            "metric_valid": True}
        for k in ("no_calibration", "temperature_global",
                  "temperature_ordinal", "isotonic_ordinal",
                  "separate_thresholds", "shared_threshold_full",
                  "no_constraint", "soft_gate",
                  "hard_truncation_renormalize",
                  "hard_truncation_route_review", "full")
    })
    data_path = tmp_path / "data.jsonl"
    data_path.write_text(
        json.dumps({"split": "train", "escalation_label": 1}) + "\n"
        + json.dumps({"split": "dev", "escalation_label": 0}) + "\n"
        + json.dumps({"split": "test", "escalation_label": 1}) + "\n",
        encoding="utf-8",
    )
    # paper_full does NOT allow toy results, but our data is not toy.
    out_dir = tmp_path / "report"
    cmd = [
        sys.executable, "-u", "scripts/generate_tables.py",
        "--results_dir", str(results_dir),
        "--output", str(out_dir),
        "--profile", "paper_full",
        "--data_path", str(data_path),
    ]
    proc = subprocess.run(
        cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=120,
    )
    # Must exit non-zero (blocking error).
    assert proc.returncode != 0, "paper_full should fail on missing strong baselines"
    metadata_path = out_dir / "report_metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert len(metadata["blocking_errors"]) >= 1
    assert "strong baselines" in metadata["blocking_errors"][0]
