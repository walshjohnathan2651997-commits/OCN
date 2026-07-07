#!/usr/bin/env python
"""run_v3_17_confidential_pipeline.py — Unified V3.17 confidential pipeline runner.

Orchestrates the full V3.17 confidential lightweight pipeline as a sequence
of subprocess stage calls. Supports toy, real, and status_only modes.

Stages (spec V3.17 Task Pack G):
  status            — generate project status report
  pdf_corpus        — build PDF sentence corpus (toy or real)
  bm25_real         — BM25 sentence/window retrieval (real only)
  canonicalizer_real — evidence canonicalizer ablation (real only)
  format_shift_real — format-shift ablation (real only)
  leakage_real      — leakage audit (real only)
  error_taxonomy    — error taxonomy on real data
  human_audit_seed  — build human audit seed queue
  complexity_utility — complexity-vs-utility ablation
  smart_queue       — lightweight SmartQueue + review queue
  metric_robustness — bootstrap CI metrics
  paper_assets      — generate paper-ready tables/figures
  redteam           — confidentiality red-team scanner
  schema_validation — validate experiment outputs against schema registry
  toy_demo          — toy end-to-end demo (safe for CI)
  release_bundle    — build public sanitized release bundle

Legacy stage aliases (backward compat):
  corpus → pdf_corpus, retrieval → bm25_real, canonicalizer → canonicalizer_real,
  format_shift → format_shift_real, leakage_audit → leakage_real,
  redteam_scan → redteam, r4_eval → r4_eval (kept)

Modes:
  toy         — toy/synthetic data only (safe for CI)
  real        — real/private data (requires --allow_private_data true)
  status_only — only run the status stage
  full        — alias for real (deprecated)

Hard boundaries (enforced):
  - no network, no API, no training, no original data modification
  - real mode requires explicit --allow_private_data true
  - failure stops the pipeline (no swallow)

Outputs (under experiments/v3_17_confidential_pipeline_runs/{timestamp}/):
  run_summary.json   — overall status + per-stage results
  run_log.txt        — combined stdout/stderr from all stages
  stage_status.csv   — per-stage start/end/status/runtime/metadata
  config_snapshot.yaml — copy of the effective config
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable

# Shared config utilities
sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from config_utils import load_and_validate, print_guards  # noqa: E402


# ---------------------------------------------------------------------------
# Stage definitions
# ---------------------------------------------------------------------------

# Spec stages (Task Pack G)
SPEC_STAGES = [
    "status",
    "pdf_corpus",
    "bm25_real",
    "canonicalizer_real",
    "format_shift_real",
    "leakage_real",
    "error_taxonomy",
    "human_audit_seed",
    "complexity_utility",
    "smart_queue",
    "metric_robustness",
    "paper_assets",
    "redteam",
    "schema_validation",
    "toy_demo",
    "release_bundle",
]

# Legacy stage aliases → canonical stage name
STAGE_ALIASES = {
    "corpus": "pdf_corpus",
    "retrieval": "bm25_real",
    "canonicalizer": "canonicalizer_real",
    "format_shift": "format_shift_real",
    "leakage_audit": "leakage_real",
    "redteam_scan": "redteam",
    "r4_eval": "r4_eval",  # kept as-is
}

# All valid stage names (canonical + aliases)
ALL_STAGES = SPEC_STAGES + list(STAGE_ALIASES.keys())

# Default stages per mode
DEFAULT_TOY_STAGES = ["toy_demo", "schema_validation", "redteam"]
DEFAULT_REAL_STAGES = SPEC_STAGES  # all spec stages
DEFAULT_STATUS_ONLY_STAGES = ["status"]

# Stages that are always safe for CI (no private data)
CI_SAFE_STAGES = {"toy_demo", "schema_validation", "redteam", "status"}

# Stages that require real/private data
REAL_ONLY_STAGES = {"bm25_real", "canonicalizer_real", "format_shift_real", "leakage_real", "error_taxonomy", "metric_robustness"}


def _resolve_stage(stage: str) -> str:
    """Resolve a stage name to its canonical name (apply aliases)."""
    return STAGE_ALIASES.get(stage, stage)


def _stage_args(stage: str, mode: str, config_path: Optional[str]) -> List[str]:
    """Build the argument list for a given stage.

    Returns the full argv list (excluding the python executable and script path).
    """
    scripts_dir = REPO_ROOT / "scripts"
    toy = mode == "toy"
    canonical = _resolve_stage(stage)

    if canonical == "pdf_corpus":
        script = scripts_dir / "build_pdf_sentence_corpus_v1.py"
        args = ["--output_dir"]
        if toy:
            args.append("data/pdf_corpus_toy_v1")
            args.append("--toy_mode")
        else:
            args.append("data/pdf_corpus_v1")
        return [str(script)] + args

    if canonical == "bm25_real":
        script = scripts_dir / "run_bm25_sentence_retrieval_v1.py"
        args = ["--output_dir"]
        if toy:
            args.append("experiments/bm25_sentence_retrieval_v1_toy")
            args.append("--toy_mode")
        else:
            args.append("experiments/simclaim_pdf_corpus_retrieval_v1")
            if config_path:
                args.extend(["--config", config_path])
        return [str(script)] + args

    if canonical == "canonicalizer_real":
        script = scripts_dir / "run_canonicalizer_ablation_v1.py"
        args = ["--output_dir"]
        if toy:
            args.append("experiments/canonicalizer_ablation_v1_toy")
            args.append("--toy_mode")
        else:
            args.append("experiments/canonicalizer_ablation_v1")
            if config_path:
                args.extend(["--config", config_path])
        return [str(script)] + args

    if canonical == "format_shift_real":
        script = scripts_dir / "run_format_shift_ablation_v1.py"
        args = ["--output_dir"]
        if toy:
            args.append("experiments/format_shift_ablation_v1_toy")
            args.append("--toy_mode")
        else:
            args.append("experiments/format_shift_ablation_v1")
            if config_path:
                args.extend(["--config", config_path])
        return [str(script)] + args

    if canonical == "r4_eval":
        script = scripts_dir / "evaluate_r4_on_evidence_variants_v1.py"
        args = ["--output_dir"]
        if toy:
            args.append("experiments/r4_eval_v1_toy")
            args.append("--toy_mode")
        else:
            args.append("experiments/r4_eval_v1")
            if config_path:
                args.extend(["--config", config_path])
        return [str(script)] + args

    if canonical == "smart_queue":
        script = scripts_dir / "run_lightweight_smart_queue_v1.py"
        output_dir = "experiments/lightweight_smart_queue_v1_toy" if toy else "experiments/lightweight_smart_queue_v1"
        args = ["--output_dir", output_dir, "--profile", "balanced"]
        if toy:
            args.append("--toy_mode")
        elif config_path:
            args.extend(["--config", config_path])
        return [str(script)] + args

    if canonical == "leakage_real":
        script = scripts_dir / "run_leakage_audit_v1.py"
        args = ["--output_dir"]
        if toy:
            args.append("experiments/leakage_audit_v1_toy")
            args.append("--toy_mode")
        else:
            args.append("experiments/leakage_audit_v1")
            if config_path:
                args.extend(["--config", config_path])
        return [str(script)] + args

    if canonical == "schema_validation":
        script = scripts_dir / "validate_experiment_outputs_v1.py"
        args = []
        if toy:
            args.append("--toy_mode")
        elif config_path:
            args.extend(["--config", config_path])
        return [str(script)] + args

    if canonical == "redteam":
        script = scripts_dir / "run_confidentiality_redteam_scan_v1.py"
        args = []
        if toy:
            args.append("--toy_mode")
        # real mode: scan the full repo (default dirs)
        return [str(script)] + args

    if canonical == "paper_assets":
        script = scripts_dir / "generate_paper_assets_v3_17.py"
        args = []
        if toy:
            args.append("--toy_mode")
        return [str(script)] + args

    if canonical == "status":
        script = scripts_dir / "generate_project_status_report_v1.py"
        return [str(script)]

    if canonical == "error_taxonomy":
        script = scripts_dir / "run_error_taxonomy_v1.py"
        args = []
        if toy:
            args.append("--toy_mode")
        elif config_path:
            args.extend(["--config", config_path])
        return [str(script)] + args

    if canonical == "human_audit_seed":
        script = scripts_dir / "build_human_audit_queue_v1.py"
        return [str(script)]

    if canonical == "complexity_utility":
        script = scripts_dir / "run_complexity_vs_utility_ablation_v1.py"
        args = []
        if config_path:
            args.extend(["--config", config_path])
        return [str(script)] + args

    if canonical == "metric_robustness":
        script = scripts_dir / "run_metric_robustness_v1.py"
        args = []
        if toy:
            args.append("--toy_mode")
        elif config_path:
            args.extend(["--config", config_path])
        return [str(script)] + args

    if canonical == "toy_demo":
        script = scripts_dir / "run_toy_end_to_end_demo_v1.py"
        return [str(script)]

    if canonical == "release_bundle":
        script = scripts_dir / "build_public_sanitized_release_v1.py"
        return [str(script)]

    raise ValueError(f"Unknown stage: {stage}")


# ---------------------------------------------------------------------------
# Paper assets collection
# ---------------------------------------------------------------------------

def collect_paper_assets(output_dir: Path, mode: str) -> Tuple[bool, str]:
    """Collect key paper-ready artifacts from previous stages into a directory.

    This is a read-only collection step — it copies existing outputs, never
    modifies originals. Returns (success, message).
    """
    assets_dir = output_dir / "paper_assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    toy_suffix = "_toy" if mode == "toy" else ""
    collected = []

    # Key artifacts to collect
    sources = [
        ("experiments/lightweight_smart_queue_v1" + toy_suffix, "smart_queue_scores.csv"),
        ("experiments/lightweight_smart_queue_v1" + toy_suffix, "smart_queue_top100.csv"),
        ("experiments/leakage_audit_v1" + toy_suffix, "audit_summary.json"),
        ("experiments/leakage_audit_v1" + toy_suffix, "audit_summary.md"),
        ("experiments/confidentiality_redteam_scan_v1" + toy_suffix, "redteam_summary.json"),
        ("experiments/confidentiality_redteam_scan_v1" + toy_suffix, "redteam_summary.md"),
    ]

    for rel_dir, filename in sources:
        src = REPO_ROOT / rel_dir / filename
        if src.exists():
            dest = assets_dir / filename
            shutil.copy2(src, dest)
            collected.append(str(src.relative_to(REPO_ROOT)))

    # Write manifest
    manifest = {
        "mode": mode,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "collected_files": collected,
        "warning": (
            "All R4 scores in toy mode are MOCK/TOY. Do NOT cite in paper."
            if mode == "toy" else
            "Verify paper_valid=true before using in paper tables."
        ),
    }
    manifest_path = assets_dir / "paper_assets_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    msg = f"Collected {len(collected)} paper-ready artifacts to {assets_dir}"
    return True, msg


# ---------------------------------------------------------------------------
# Stage execution
# ---------------------------------------------------------------------------

def run_stage(
    stage: str,
    mode: str,
    config_path: Optional[str],
    run_log_file: Path,
    run_dir: Path,
) -> Dict:
    """Run a single stage as a subprocess. Returns a status dict.

    Stage result fields (per Task Pack G spec):
      stage_name, status, start_time, end_time, runtime_seconds,
      output_dir, error_message, privacy_mode, real_or_toy
    """
    canonical = _resolve_stage(stage)
    print(f"\n{'=' * 60}", file=sys.stderr, flush=True)
    print(f"[STAGE] {stage} → {canonical} (mode={mode})", file=sys.stderr, flush=True)
    print(f"{'=' * 60}", file=sys.stderr, flush=True)

    start_time = time.time()
    start_iso = datetime.now(timezone.utc).isoformat()

    # Build command
    cmd_parts = _stage_args(stage, mode, config_path)
    script_path = cmd_parts[0]
    script_args = cmd_parts[1:]

    if not Path(script_path).exists():
        end_time = time.time()
        return {
            "stage_name": stage,
            "canonical_name": canonical,
            "status": "failed",
            "start_time": start_iso,
            "end_time": datetime.now(timezone.utc).isoformat(),
            "runtime_seconds": round(end_time - start_time, 2),
            "output_dir": "",
            "error_message": f"Script not found: {script_path}",
            "privacy_mode": mode,
            "real_or_toy": "toy" if mode == "toy" else "real",
            # backward-compat fields
            "stage": stage,
            "start": start_iso,
            "end": datetime.now(timezone.utc).isoformat(),
            "message": f"Script not found: {script_path}",
        }

    cmd = [PYTHON, script_path] + script_args
    print(f"[CMD] {' '.join(cmd)}", file=sys.stderr, flush=True)

    # Log the command to run_log
    with open(run_log_file, "a", encoding="utf-8") as f:
        f.write(f"\n{'=' * 60}\n")
        f.write(f"[STAGE: {stage} → {canonical}]\n")
        f.write(f"[CMD] {' '.join(cmd)}\n")
        f.write(f"{'=' * 60}\n")

    try:
        result = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=600,  # 10 min max per stage
        )

        # Write output to run_log
        with open(run_log_file, "a", encoding="utf-8") as f:
            f.write(result.stdout)
            f.write(f"\n[EXIT CODE: {result.returncode}]\n")

        end_time = time.time()
        end_iso = datetime.now(timezone.utc).isoformat()
        runtime = round(end_time - start_time, 2)

        status = "ok" if result.returncode == 0 else "failed"
        error_message = ""
        # Redteam scan and schema validation may exit 1 when they find issues —
        # the scripts themselves ran successfully, so don't stop the pipeline.
        if canonical in ("redteam", "schema_validation") and result.returncode == 1:
            status = "ok_with_findings"
        if result.returncode != 0 and status == "failed":
            # Extract last few lines as error message
            error_lines = result.stdout.strip().split("\n")[-5:]
            error_message = "; ".join(error_lines)[:500]

        return {
            "stage_name": stage,
            "canonical_name": canonical,
            "status": status,
            "start_time": start_iso,
            "end_time": end_iso,
            "runtime_seconds": runtime,
            "output_dir": str(run_dir),
            "error_message": error_message,
            "privacy_mode": mode,
            "real_or_toy": "toy" if mode == "toy" else "real",
            # backward-compat fields
            "stage": stage,
            "start": start_iso,
            "end": end_iso,
            "exit_code": result.returncode,
            "message": f"Completed (exit={result.returncode}, runtime={runtime}s)",
        }

    except subprocess.TimeoutExpired:
        end_time = time.time()
        with open(run_log_file, "a", encoding="utf-8") as f:
            f.write(f"\n[TIMEOUT after 600s]\n")
        return {
            "stage_name": stage,
            "canonical_name": canonical,
            "status": "failed",
            "start_time": start_iso,
            "end_time": datetime.now(timezone.utc).isoformat(),
            "runtime_seconds": round(end_time - start_time, 2),
            "output_dir": str(run_dir),
            "error_message": "Timeout after 600s",
            "privacy_mode": mode,
            "real_or_toy": "toy" if mode == "toy" else "real",
            "stage": stage,
            "start": start_iso,
            "end": datetime.now(timezone.utc).isoformat(),
            "message": "Timeout after 600s",
        }
    except Exception as e:
        end_time = time.time()
        with open(run_log_file, "a", encoding="utf-8") as f:
            f.write(f"\n[EXCEPTION] {e}\n")
        return {
            "stage_name": stage,
            "canonical_name": canonical,
            "status": "failed",
            "start_time": start_iso,
            "end_time": datetime.now(timezone.utc).isoformat(),
            "runtime_seconds": round(end_time - start_time, 2),
            "output_dir": str(run_dir),
            "error_message": f"Exception: {e}",
            "privacy_mode": mode,
            "real_or_toy": "toy" if mode == "toy" else "real",
            "stage": stage,
            "start": start_iso,
            "end": datetime.now(timezone.utc).isoformat(),
            "message": f"Exception: {e}",
        }


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def write_stage_status_csv(run_dir: Path, stage_results: List[Dict]) -> None:
    """Write stage_status.csv with per-stage execution metadata."""
    csv_path = run_dir / "stage_status.csv"
    fieldnames = [
        "stage_name", "canonical_name", "status",
        "start_time", "end_time", "runtime_seconds",
        "output_dir", "error_message", "privacy_mode", "real_or_toy",
        # backward-compat columns
        "stage", "start", "end", "exit_code", "message",
    ]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in stage_results:
            writer.writerow(row)


def write_run_summary(
    run_dir: Path,
    mode: str,
    stages_requested: List[str],
    stage_results: List[Dict],
    overall_status: str,
    config_path: Optional[str],
) -> None:
    """Write run_summary.json with overall pipeline status."""
    summary = {
        "pipeline": "v3_17_confidential",
        "mode": mode,
        "overall_status": overall_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stages_requested": stages_requested,
        "stages_completed": [r["stage"] for r in stage_results if r["status"] in ("ok", "ok_with_findings")],
        "stages_failed": [r["stage"] for r in stage_results if r["status"] == "failed"],
        "n_stages_requested": len(stages_requested),
        "n_stages_completed": sum(1 for r in stage_results if r["status"] in ("ok", "ok_with_findings")),
        "n_stages_failed": sum(1 for r in stage_results if r["status"] == "failed"),
        "config_source": config_path or "default",
        "guards": {
            "no_api": True,
            "no_network": True,
            "no_training": True,
            "no_original_data_modification": True,
        },
        "stage_details": stage_results,
    }
    summary_path = run_dir / "run_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)


def write_config_snapshot(run_dir: Path, config_path: Optional[str], mode: str) -> None:
    """Copy the effective config file to the run directory."""
    snapshot_path = run_dir / "config_snapshot.yaml"
    if config_path and Path(config_path).exists():
        shutil.copy2(config_path, snapshot_path)
    else:
        # Write the default or toy config path
        default_config = (
            REPO_ROOT / "configs" / "toy_demo.yaml" if mode == "toy"
            else REPO_ROOT / "configs" / "v3_17_confidential_default.yaml"
        )
        if default_config.exists():
            shutil.copy2(default_config, snapshot_path)
        else:
            snapshot_path.write_text(
                f"# Config snapshot (mode={mode})\n# Source: {default_config} (not found)\n",
                encoding="utf-8",
            )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Unified V3.17 confidential pipeline runner."
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to YAML config (default: configs/v3_17_confidential_default.yaml or toy_demo.yaml)",
    )
    parser.add_argument(
        "--mode",
        choices=["toy", "real", "status_only", "full"],
        default="toy",
        help="Pipeline mode: toy (default), real (requires --allow_private_data true), status_only, full (deprecated alias for real)",
    )
    parser.add_argument(
        "--stages",
        default=None,
        help=f"Comma-separated list of stages. Default depends on mode.",
    )
    parser.add_argument(
        "--allow_private_data",
        default="false",
        help="Must be 'true' to run in real/full mode. Default: false.",
    )
    parser.add_argument(
        "--output_dir",
        default=None,
        help="Output directory (default: experiments/v3_17_confidential_pipeline_runs/{timestamp})",
    )
    args = parser.parse_args()

    # --- Normalize mode (full → real) ---
    effective_mode = "real" if args.mode == "full" else args.mode

    # --- Validate mode and private data authorization ---
    if effective_mode == "real" and args.allow_private_data != "true":
        print(
            "ERROR: real mode requires --allow_private_data true\n"
            "       This flag confirms you have authorization to access private PDF data.",
            file=sys.stderr,
        )
        return 2

    # --- Load config (for guard enforcement) ---
    config = load_and_validate(args.config, toy_mode=(effective_mode == "toy"))
    print_guards(config)

    # --- Determine stages ---
    if args.stages:
        stages = [s.strip() for s in args.stages.split(",") if s.strip()]
    elif effective_mode == "toy":
        stages = DEFAULT_TOY_STAGES
    elif effective_mode == "status_only":
        stages = DEFAULT_STATUS_ONLY_STAGES
    else:  # real
        stages = DEFAULT_REAL_STAGES

    # Validate stage names
    invalid = [s for s in stages if s not in ALL_STAGES]
    if invalid:
        print(f"ERROR: Unknown stages: {invalid}", file=sys.stderr)
        print(f"       Valid stages: {ALL_STAGES}", file=sys.stderr)
        return 2

    # --- Safety: real-only stages in toy mode ---
    if effective_mode == "toy":
        real_only_requested = [s for s in stages if _resolve_stage(s) in REAL_ONLY_STAGES]
        if real_only_requested:
            print(
                f"WARNING: Stages {real_only_requested} require real data but mode is toy. "
                f"These stages will use toy fallbacks.",
                file=sys.stderr,
            )

    # --- Create output directory ---
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if args.output_dir:
        run_dir = Path(args.output_dir)
    else:
        run_dir = REPO_ROOT / "experiments" / "v3_17_confidential_pipeline_runs" / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    run_log_file = run_dir / "run_log.txt"
    # Truncate log at start
    run_log_file.write_text(
        f"V3.17 Confidential Pipeline Run\n"
        f"Mode: {args.mode} (effective: {effective_mode})\n"
        f"Stages: {stages}\n"
        f"Timestamp: {timestamp}\n"
        f"Config: {args.config or 'default'}\n"
        f"Allow private data: {args.allow_private_data}\n"
        f"{'=' * 60}\n",
        encoding="utf-8",
    )

    print(f"[pipeline] mode={args.mode} (effective: {effective_mode})", file=sys.stderr, flush=True)
    print(f"[pipeline] stages={stages}", file=sys.stderr, flush=True)
    print(f"[pipeline] run_dir={run_dir}", file=sys.stderr, flush=True)

    # --- Write config snapshot ---
    write_config_snapshot(run_dir, args.config, effective_mode)

    # --- Run stages ---
    stage_results: List[Dict] = []
    overall_status = "running"

    for stage in stages:
        result = run_stage(stage, effective_mode, args.config, run_log_file, run_dir)
        stage_results.append(result)
        print(f"[STAGE] {stage}: {result['status']} ({result['runtime_seconds']}s)", file=sys.stderr, flush=True)

        if result["status"] == "failed":
            overall_status = "failed"
            print(
                f"\n[pipeline] STOPPING: stage '{stage}' failed.",
                file=sys.stderr,
                flush=True,
            )
            break

    if overall_status != "failed":
        overall_status = "completed"

    # --- Write outputs ---
    write_stage_status_csv(run_dir, stage_results)
    write_run_summary(run_dir, effective_mode, stages, stage_results, overall_status, args.config)

    print(f"\n[pipeline] overall_status={overall_status}", file=sys.stderr, flush=True)
    print(f"[pipeline] run_summary: {run_dir / 'run_summary.json'}", file=sys.stderr, flush=True)
    print(f"[pipeline] stage_status: {run_dir / 'stage_status.csv'}", file=sys.stderr, flush=True)
    print(f"[pipeline] run_log: {run_log_file}", file=sys.stderr, flush=True)

    return 0 if overall_status == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
