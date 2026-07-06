"""P6 (ocn-22): slow integration test for the pilot stage chain.

P5 (ocn-23): updated to use the 7 independent stage scripts (the old
run_stage_diagnostics.py wrapper is deprecated; the test now calls
run_stage_ablations.py + run_stage_adversarial.py +
run_stage_oracle_extracted.py directly).

Runs the 7 independent stage scripts end-to-end on the pilot_template
data and asserts that:

  - each stage_summary.json has status == "ok"
  - report/results.md exists
  - report_metadata.json has the expected pilot_diagnostic fields:
      report_mode == "pilot_diagnostic"
      paper_ready == false
      is_pilot_template == true
      human_audited == false

This test does NOT exercise the deprecated run_stage_baselines.py,
run_stage_diagnostics.py wrappers or the experimental
run_all_experiments.py orchestrator.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def _run(cmd: list[str], cwd: Path, timeout: int = 300) -> subprocess.CompletedProcess:
    """Run a stage script and surface stdout/stderr on failure."""
    proc = subprocess.run(
        cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout,
    )
    if proc.returncode != 0:
        print("STDOUT:", proc.stdout)
        print("STDERR:", proc.stderr)
    assert proc.returncode == 0, f"command failed: {' '.join(cmd)}"
    return proc


@pytest.mark.slow
@pytest.mark.integration
def test_pilot_stage_chain_smoke(tmp_path):
    """End-to-end smoke of the 7 independent stage scripts."""
    out_root = tmp_path / "pilot_stage"
    out_root.mkdir(parents=True, exist_ok=True)

    data = str(ROOT / "data" / "pilot_template.jsonl")
    cfg = str(ROOT / "configs" / "pilot_test.yaml")
    abl_cfg = str(ROOT / "configs" / "pilot_ablations.yaml")
    bl_cfg = str(ROOT / "configs" / "pilot_baselines.yaml")

    # Stage 1: train + eval
    te_out = out_root / "train_eval"
    _run([
        PY, "-u", "scripts/run_stage_train_eval.py",
        "--config", cfg,
        "--train", data, "--dev", data, "--test", data,
        "--output", str(te_out),
        "--step_timeout_sec", "120",
    ], cwd=ROOT)
    _assert_stage_ok(te_out / "stage_summary.json")

    # Stage 2a: baseline train
    bl_train_out = out_root / "baseline_train"
    _run([
        PY, "-u", "scripts/run_stage_baseline_train.py",
        "--config", bl_cfg,
        "--train", data, "--dev", data,
        "--output", str(bl_train_out),
        "--step_timeout_sec", "120",
    ], cwd=ROOT)
    _assert_stage_ok(bl_train_out / "stage_summary.json")

    # Stage 2b: baseline eval
    bl_eval_out = out_root / "baseline_eval"
    _run([
        PY, "-u", "scripts/run_stage_baseline_eval.py",
        "--config", bl_cfg,
        "--test", data,
        "--checkpoint-dir", str(bl_train_out),
        "--output", str(bl_eval_out),
        "--profile", "pilot",
        "--step_timeout_sec", "120",
    ], cwd=ROOT)
    _assert_stage_ok(bl_eval_out / "stage_summary.json")

    # Stage 3a: ablations only
    abl_out = out_root / "ablations"
    _run([
        PY, "-u", "scripts/run_stage_ablations.py",
        "--config", cfg,
        "--ablations-config", abl_cfg,
        "--checkpoint", str(te_out / "train" / "best.pt"),
        "--data", data,
        "--output", str(abl_out),
        "--step_timeout_sec", "120",
    ], cwd=ROOT)
    _assert_stage_ok(abl_out / "stage_summary.json")

    # Stage 3b: adversarial eval only
    adv_out = out_root / "adversarial"
    _run([
        PY, "-u", "scripts/run_stage_adversarial.py",
        "--config", cfg,
        "--checkpoint", str(te_out / "train" / "best.pt"),
        "--data", data,
        "--output", str(adv_out),
        "--profile", "pilot",
        "--step_timeout_sec", "120",
    ], cwd=ROOT)
    _assert_stage_ok(adv_out / "stage_summary.json")

    # Stage 3c: oracle/extracted comparison only
    orc_out = out_root / "oracle_extracted"
    _run([
        PY, "-u", "scripts/run_stage_oracle_extracted.py",
        "--config", cfg,
        "--checkpoint", str(te_out / "train" / "best.pt"),
        "--data", data,
        "--output", str(orc_out),
        "--step_timeout_sec", "120",
    ], cwd=ROOT)
    _assert_stage_ok(orc_out / "stage_summary.json")

    # Stage 4: report
    report_out = out_root / "report"
    _run([
        PY, "-u", "scripts/run_stage_report.py",
        "--results_dir", str(out_root),
        "--data", data,
        "--output", str(report_out),
        "--profile", "pilot",
        "--allow_toy_results",
        "--step_timeout_sec", "120",
    ], cwd=ROOT)
    _assert_stage_ok(report_out / "stage_summary.json")

    # results.md must exist
    results_md = report_out / "results.md"
    assert results_md.exists(), f"missing {results_md}"

    # report_metadata.json must have the expected pilot fields
    meta_path = report_out / "report_metadata.json"
    assert meta_path.exists(), f"missing {meta_path}"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta.get("report_mode") == "pilot_diagnostic", \
        f"report_mode={meta.get('report_mode')!r}"
    assert meta.get("paper_ready") is False, \
        f"paper_ready={meta.get('paper_ready')!r}"
    assert meta.get("is_pilot_template") is True, \
        f"is_pilot_template={meta.get('is_pilot_template')!r}"
    assert meta.get("human_audited") is False, \
        f"human_audited={meta.get('human_audited')!r}"


def _assert_stage_ok(summary_path: Path) -> None:
    assert summary_path.exists(), f"missing {summary_path}"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary.get("status") == "ok", \
        f"stage {summary_path.parent.name} status={summary.get('status')!r}"

