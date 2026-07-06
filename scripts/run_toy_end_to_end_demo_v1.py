#!/usr/bin/env python
"""run_toy_end_to_end_demo_v1.py — Toy end-to-end pipeline demo.

Orchestrates the full V3.17 pipeline on toy synthetic data:
  toy texts → sentence corpus → BM25 → canonicalizer → mock R4 → SmartQueue → review queue

All R4 scores are MOCK/TOY. Do NOT mix with real experiment results.
Hard boundaries: no network, no API, no training, no real data.
"""

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable

# Shared config utilities
sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from config_utils import load_and_validate, write_run_config, print_guards  # noqa: E402
from schema_utils import validate_csv_file, write_schema_validation_report  # noqa: E402

STEPS = [
    {
        "name": "1. Build sentence corpus",
        "script": "scripts/build_pdf_sentence_corpus_v1.py",
        "args": ["--toy_mode", "--output_dir", "data/pdf_corpus_toy_v1"],
        "check_output": "data/pdf_corpus_toy_v1/sentences.jsonl",
    },
    {
        "name": "2. BM25 sentence/window retrieval",
        "script": "scripts/run_bm25_sentence_retrieval_v1.py",
        "args": ["--toy_mode", "--output_dir", "experiments/bm25_sentence_retrieval_v1_toy"],
        "check_output": "experiments/bm25_sentence_retrieval_v1_toy/oracle_recall_summary.json",
    },
    {
        "name": "3. Canonicalizer ablation",
        "script": "scripts/run_canonicalizer_ablation_v1.py",
        "args": ["--toy_mode", "--output_dir", "experiments/canonicalizer_ablation_v1_toy"],
        "check_output": "experiments/canonicalizer_ablation_v1_toy/selector_metrics_summary.csv",
    },
    {
        "name": "4. Format-shift ablation",
        "script": "scripts/run_format_shift_ablation_v1.py",
        "args": ["--toy_mode", "--output_dir", "experiments/format_shift_ablation_v1_toy"],
        "check_output": "experiments/format_shift_ablation_v1_toy/format_shift_inputs.csv",
    },
    {
        "name": "5. Mock R4 + SmartQueue",
        "script": "scripts/run_lightweight_smart_queue_v1.py",
        "args": ["--toy_mode", "--output_dir", "experiments/lightweight_smart_queue_v1_toy", "--profile", "balanced"],
        "check_output": "experiments/lightweight_smart_queue_v1_toy/smart_queue_top100.csv",
    },
    {
        "name": "6. Leakage audit",
        "script": "scripts/run_leakage_audit_v1.py",
        "args": ["--toy_mode", "--output_dir", "experiments/leakage_audit_v1_toy"],
        "check_output": "experiments/leakage_audit_v1_toy/audit_summary.md",
    },
]


def log(msg):
    print(msg, flush=True)


def run_step(step):
    """Run a pipeline step. Returns (success, output_lines)."""
    check_path = REPO_ROOT / step["check_output"]
    if check_path.exists():
        log(f"  [SKIP] {step['name']} (output already exists: {step['check_output']})")
        return True, ["[skipped]"]

    script_path = REPO_ROOT / step["script"]
    if not script_path.exists():
        log(f"  [ERROR] Script not found: {step['script']}")
        return False, [f"script not found: {step['script']}"]

    cmd = [PYTHON, str(script_path)] + step["args"]
    log(f"  [RUN] {step['name']}")
    log(f"        cmd: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, cwd=str(REPO_ROOT), capture_output=False, text=True, timeout=120
        )
        if result.returncode != 0:
            log(f"  [FAIL] {step['name']} (exit code {result.returncode})")
            return False, [f"exit code {result.returncode}"]
        log(f"  [OK] {step['name']}")
        return True, ["[ok]"]
    except subprocess.TimeoutExpired:
        log(f"  [FAIL] {step['name']} (timeout)")
        return False, ["timeout"]
    except Exception as e:
        log(f"  [FAIL] {step['name']} (exception: {e})")
        return False, [str(e)]


def main():
    parser = argparse.ArgumentParser(description="Toy end-to-end pipeline demo.")
    parser.add_argument("--config", default=None, help="Path to YAML config (default: toy_demo.yaml)")
    args = parser.parse_args()

    # --- Load config (toy demo always uses toy config by default) ---
    config = load_and_validate(args.config, toy_mode=True)
    print_guards(config)

    output_dir = REPO_ROOT / "experiments" / "toy_end_to_end_demo_v1"
    output_dir.mkdir(parents=True, exist_ok=True)

    log("=" * 60)
    log("Toy End-to-End Demo V1")
    log("All R4 scores are MOCK/TOY. Do NOT mix with real results.")
    log("=" * 60)

    step_results = []
    all_success = True

    for step in STEPS:
        success, output = run_step(step)
        step_results.append({
            "name": step["name"],
            "script": step["script"],
            "success": success,
            "check_output": step["check_output"],
        })
        if not success:
            all_success = False
            log(f"\nStopping: step '{step['name']}' failed.")
            break

    # Copy final review queue to demo output
    queue_path = REPO_ROOT / "experiments" / "lightweight_smart_queue_v1_toy" / "smart_queue_top100.csv"
    if queue_path.exists():
        dest = output_dir / "toy_review_queue.csv"
        shutil.copy2(queue_path, dest)
        log(f"\nCopied review queue to {dest}")

    # Write summary
    summary = {
        "demo_name": "toy_end_to_end_demo_v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "all_steps_success": all_success,
        "n_steps": len(STEPS),
        "n_steps_completed": sum(1 for r in step_results if r["success"]),
        "steps": step_results,
        "mock_r4_warning": "All R4 scores in this demo are MOCK/TOY. Do NOT mix with real experiment results.",
        "pipeline": [
            "toy texts → sentence corpus → BM25 → canonicalizer → mock R4 → SmartQueue → review queue"
        ],
        "no_network": True,
        "no_api": True,
        "no_training": True,
    }
    summary_path = output_dir / "toy_run_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    log(f"\nWrote {summary_path}")

    # --- Schema validation (sub-scripts already wrote per-dir reports;
    # here we validate the canonical SmartQueue scores output as a demo-level check) ---
    smart_queue_scores_path = REPO_ROOT / "experiments" / "lightweight_smart_queue_v1_toy" / "smart_queue_scores.csv"
    schema_reports = [
        validate_csv_file(smart_queue_scores_path, "smart_queue_scores"),
    ]
    write_schema_validation_report(
        output_dir, schema_reports, script_name="run_toy_end_to_end_demo_v1.py"
    )
    log("Wrote schema_validation_report.json")

    write_run_config(output_dir, config, "run_toy_end_to_end_demo_v1.py",
                     extra={"toy_mode": True, "all_steps_success": all_success})
    log("Wrote run_config.json")

    if all_success:
        log("\nAll steps completed successfully!")
    else:
        log("\nSome steps failed. Check output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
