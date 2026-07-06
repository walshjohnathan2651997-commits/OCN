"""
Validate Experiment Outputs v1
==============================
Walks experiments/ (and optionally data/) and validates every known output
file against its registered schema in schemas/.

For each file, checks:
  1. File exists.
  2. All schema.required_columns are present.
  3. No schema.forbidden_columns_for_scoring fields are present.
  4. For redacted files: no schema.text_columns or
     schema.forbidden_columns_for_public_release fields are present.

Outputs:
  experiments/schema_validation_report.json   (machine-readable)
  experiments/schema_validation_summary.md    (human-readable)

Per-directory schema_validation_report.json files written by individual
scripts (see scripts/lib/schema_utils.py) are NOT overwritten by this pass;
this script only writes the two top-level summary files in experiments/.

Usage:
  python scripts/validate_experiment_outputs_v1.py
  python scripts/validate_experiment_outputs_v1.py --experiments-dir experiments --data-dir data
  python scripts/validate_experiment_outputs_v1.py --strict

Prohibitions: no training, no API, no network, no original-data modification.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# Shared config + schema utilities
sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from config_utils import load_and_validate, print_guards  # noqa: E402
from schema_utils import (  # noqa: E402
    SCHEMAS_DIR,
    validate_csv_file,
    validate_jsonl_file,
    validate_json_file,
    validate_redacted_file,
    load_schema,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EXPERIMENTS_DIR = REPO_ROOT / "experiments"
DEFAULT_DATA_DIR = REPO_ROOT / "data"


# ---------------- Experiment -> schema mapping ----------------
# Each entry: relative_path_under_root -> (schema_name, is_redacted)
# is_redacted=True triggers validate_redacted_file (no text columns allowed).

EXPERIMENT_SCHEMA_MAP: Dict[str, List[Tuple[str, str, bool]]] = {
    "experiments/bm25_sentence_retrieval_v1": [
        ("retrieval_results_sentence_bm25.csv", "bm25_retrieval_results", False),
        ("retrieval_results_window_bm25.csv", "bm25_retrieval_results", False),
        ("retrieval_examples_redacted.csv", "bm25_retrieval_results", True),
    ],
    "experiments/bm25_sentence_retrieval_v1_toy": [
        ("retrieval_results_sentence_bm25.csv", "bm25_retrieval_results", False),
        ("retrieval_results_window_bm25.csv", "bm25_retrieval_results", False),
        ("retrieval_examples_redacted.csv", "bm25_retrieval_results", True),
    ],
    "experiments/canonicalizer_ablation_v1": [
        ("selector_variant_evidence.csv", "selector_variant_evidence", False),
        ("selector_examples_redacted.csv", "selector_variant_evidence", True),
    ],
    "experiments/canonicalizer_ablation_v1_toy": [
        ("selector_variant_evidence.csv", "selector_variant_evidence", False),
        ("selector_examples_redacted.csv", "selector_variant_evidence", True),
    ],
    "experiments/format_shift_ablation_v1": [
        ("format_shift_metrics.csv", "format_shift_metrics", False),
        ("format_shift_inputs.csv", "format_shift_inputs", False),
        ("format_shift_inputs_redacted.csv", "format_shift_inputs", True),
    ],
    "experiments/format_shift_ablation_v1_toy": [
        ("format_shift_metrics.csv", "format_shift_metrics", False),
        ("format_shift_inputs.csv", "format_shift_inputs", False),
        ("format_shift_inputs_redacted.csv", "format_shift_inputs", True),
    ],
    "experiments/canonicalized_review_queue_v1": [
        ("canonicalized_r4_review_scores.csv", "r4_review_scores", False),
        ("review_queue_top100.csv", "r4_review_scores", False),
    ],
    "experiments/canonicalized_risk_ranking_v1": [
        ("risk_ranking_features.csv", "r4_review_scores", False),
        ("review_queue_top100_best.csv", "r4_review_scores", False),
    ],
    "experiments/lightweight_smart_queue_v1": [
        ("smart_queue_scores.csv", "smart_queue_scores", False),
    ],
    "experiments/lightweight_smart_queue_v1_toy": [
        ("smart_queue_scores.csv", "smart_queue_scores", False),
    ],
    "experiments/leakage_audit_v1": [
        ("claim_only_baseline.json", "leakage_audit", False),
        ("title_only_retrieval_baseline.json", "leakage_audit", False),
        ("metadata_only_retrieval_baseline.json", "leakage_audit", False),
        ("group_split_integrity.json", "leakage_audit", False),
        ("no_oracle_in_selector_check.json", "leakage_audit", False),
        ("no_label_in_queue_sorting_check.json", "leakage_audit", False),
    ],
    "experiments/leakage_audit_v1_toy": [
        ("claim_only_baseline.json", "leakage_audit", False),
        ("title_only_retrieval_baseline.json", "leakage_audit", False),
        ("metadata_only_retrieval_baseline.json", "leakage_audit", False),
        ("group_split_integrity.json", "leakage_audit", False),
        ("no_oracle_in_selector_check.json", "leakage_audit", False),
        ("no_label_in_queue_sorting_check.json", "leakage_audit", False),
    ],
    "experiments/simclaim_pdf_corpus_retrieval_v1": [],  # legacy; outputs not schema-tracked
    "experiments/toy_end_to_end_demo_v1": [],  # demo dir; no schema-tracked outputs
}

DATA_SCHEMA_MAP: Dict[str, List[Tuple[str, str, bool]]] = {
    "data/pdf_corpus_v1": [
        ("pdf_manifest.csv", "pdf_manifest", False),
        ("sentences.jsonl", "pdf_sentence_corpus", False),
    ],
    "data/pdf_corpus_toy_v1": [
        ("pdf_manifest.csv", "pdf_manifest", False),
        ("sentences.jsonl", "pdf_sentence_corpus", False),
    ],
}


def _validate_one(
    root: Path,
    rel_dir: str,
    filename: str,
    schema_name: str,
    is_redacted: bool,
    strict: bool,
) -> Dict[str, Any]:
    """Validate a single file. Returns a report dict."""
    file_path = root / rel_dir / filename
    if not file_path.exists():
        return {
            "schema": schema_name,
            "file_path": str(file_path),
            "file_exists": False,
            "is_redacted": is_redacted,
            "ok": False,
            "error": "file not found",
        }

    # Route by extension
    if filename.endswith(".csv"):
        try:
            df = pd.read_csv(file_path, keep_default_na=False)
        except Exception as e:
            return {
                "schema": schema_name,
                "file_path": str(file_path),
                "file_exists": True,
                "ok": False,
                "error": f"failed to read CSV: {e}",
            }
        if is_redacted:
            report = validate_redacted_file(df, schema_name)
        else:
            from schema_utils import validate_dataframe_columns
            report = validate_dataframe_columns(df, schema_name, strict=strict)
        report["file_path"] = str(file_path)
        report["file_exists"] = True
        report["is_redacted"] = True
        return report

    if filename.endswith(".jsonl"):
        report = validate_jsonl_file(file_path, schema_name, strict=strict, max_records=1)
        report["is_redacted"] = is_redacted
        return report

    if filename.endswith(".json"):
        report = validate_json_file(file_path, schema_name, strict=strict)
        report["is_redacted"] = is_redacted
        return report

    return {
        "schema": schema_name,
        "file_path": str(file_path),
        "file_exists": True,
        "ok": False,
        "error": f"unsupported file extension: {filename}",
    }


def run_validation(
    experiments_dir: Path,
    data_dir: Optional[Path] = None,
    strict: bool = False,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Run all validations. Returns (reports, warnings)."""
    reports: List[Dict[str, Any]] = []
    warnings: List[str] = []

    # experiments/
    for rel_dir, files in EXPERIMENT_SCHEMA_MAP.items():
        target_dir = REPO_ROOT / rel_dir
        if not target_dir.exists():
            # Skip silently — many experiment dirs only exist after their
            # producing script runs.
            continue
        for filename, schema_name, is_redacted in files:
            report = _validate_one(
                REPO_ROOT, rel_dir, filename, schema_name, is_redacted, strict
            )
            report["experiment_dir"] = rel_dir
            reports.append(report)

    # data/ (optional)
    if data_dir is not None and data_dir.exists():
        for rel_dir, files in DATA_SCHEMA_MAP.items():
            target_dir = REPO_ROOT / rel_dir
            if not target_dir.exists():
                continue
            for filename, schema_name, is_redacted in files:
                report = _validate_one(
                    REPO_ROOT, rel_dir, filename, schema_name, is_redacted, strict
                )
                report["experiment_dir"] = rel_dir
                reports.append(report)

    # Sanity: every schema file in schemas/ must be loadable
    for schema_path in sorted(SCHEMAS_DIR.glob("*.schema.json")):
        name = schema_path.stem[: -len(".schema")]
        try:
            load_schema(name)
        except Exception as e:
            warnings.append(f"schema '{name}' failed to load: {e}")

    return reports, warnings


def write_summary_markdown(
    reports: List[Dict[str, Any]],
    warnings: List[str],
    out_path: Path,
) -> None:
    """Write experiments/schema_validation_summary.md."""
    n_total = len(reports)
    n_ok = sum(1 for r in reports if r.get("ok"))
    n_fail = n_total - n_ok
    by_dir: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in reports:
        by_dir[r.get("experiment_dir", "?")].append(r)

    lines: List[str] = []
    lines.append("# Schema Validation Summary")
    lines.append("")
    lines.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}")
    lines.append("")
    lines.append(f"- Total files checked: **{n_total}**")
    lines.append(f"- Passed: **{n_ok}**")
    lines.append(f"- Failed: **{n_fail}**")
    lines.append("")
    if warnings:
        lines.append("## Schema registry warnings")
        lines.append("")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    lines.append("## Per-directory results")
    lines.append("")
    for rel_dir in sorted(by_dir.keys()):
        dir_reports = by_dir[rel_dir]
        dir_ok = sum(1 for r in dir_reports if r.get("ok"))
        dir_fail = len(dir_reports) - dir_ok
        status = "OK" if dir_fail == 0 else "FAIL"
        lines.append(f"### `{rel_dir}` — {status} ({dir_ok}/{len(dir_reports)} ok)")
        lines.append("")
        for r in dir_reports:
            fname = Path(r.get("file_path", "?")).name
            ok = r.get("ok", False)
            mark = "PASS" if ok else "FAIL"
            lines.append(f"- [{mark}] `{fname}` (schema: `{r.get('schema')}`)")
            if not ok:
                if not r.get("file_exists", True):
                    lines.append(f"  - file does not exist")
                if r.get("required_missing"):
                    lines.append(
                        f"  - missing required columns: {r['required_missing']}"
                    )
                if r.get("forbidden_scoring_present"):
                    lines.append(
                        f"  - FORBIDDEN scoring fields present: "
                        f"{r['forbidden_scoring_present']}"
                    )
                if r.get("leaked_text_columns"):
                    lines.append(
                        f"  - leaked text columns in redacted output: "
                        f"{r['leaked_text_columns']}"
                    )
                if r.get("leaked_public_columns"):
                    lines.append(
                        f"  - leaked public columns in redacted output: "
                        f"{r['leaked_public_columns']}"
                    )
                if r.get("error"):
                    lines.append(f"  - error: {r['error']}")
        lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate experiment outputs against schemas/*.schema.json"
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to YAML config file. If omitted, loads configs/v3_17_confidential_default.yaml.",
    )
    parser.add_argument(
        "--experiments-dir",
        default=str(DEFAULT_EXPERIMENTS_DIR),
        help="Root experiments/ directory (default: REPO_ROOT/experiments)",
    )
    parser.add_argument(
        "--data-dir",
        default=str(DEFAULT_DATA_DIR),
        help="Root data/ directory. Set to empty string to skip data/ validation.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat unexpected columns as failures.",
    )
    parser.add_argument(
        "--toy_mode",
        action="store_true",
        help="Use toy config (configs/toy_demo.yaml) instead of default.",
    )
    args = parser.parse_args()

    config = load_and_validate(args.config, toy_mode=args.toy_mode)
    print_guards(config)

    experiments_dir = Path(args.experiments_dir)
    data_dir = Path(args.data_dir) if args.data_dir else None

    print(f"[validate_experiment_outputs_v1] experiments_dir={experiments_dir}")
    print(f"[validate_experiment_outputs_v1] data_dir={data_dir}")
    print(f"[validate_experiment_outputs_v1] strict={args.strict}")

    reports, warnings = run_validation(experiments_dir, data_dir, strict=args.strict)

    # Write JSON report
    n_total = len(reports)
    n_ok = sum(1 for r in reports if r.get("ok"))
    n_fail = n_total - n_ok
    json_payload = {
        "script_name": "validate_experiment_outputs_v1.py",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "experiments_dir": str(experiments_dir),
        "data_dir": str(data_dir) if data_dir else None,
        "strict": bool(args.strict),
        "n_files_checked": n_total,
        "n_ok": n_ok,
        "n_fail": n_fail,
        "all_ok": n_fail == 0 and len(warnings) == 0,
        "schema_registry_warnings": warnings,
        "reports": reports,
    }
    json_out = experiments_dir / "schema_validation_report.json"
    experiments_dir.mkdir(parents=True, exist_ok=True)
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(json_payload, f, indent=2, ensure_ascii=False, default=str)
    print(f"[validate_experiment_outputs_v1] wrote {json_out}")

    # Write markdown summary
    md_out = experiments_dir / "schema_validation_summary.md"
    write_summary_markdown(reports, warnings, md_out)
    print(f"[validate_experiment_outputs_v1] wrote {md_out}")

    print(f"[validate_experiment_outputs_v1] {n_ok}/{n_total} files OK, {n_fail} fail")
    if warnings:
        print(f"[validate_experiment_outputs_v1] {len(warnings)} schema registry warnings")

    # Exit 0 if all OK and no registry warnings; 1 otherwise
    return 0 if (n_fail == 0 and not warnings) else 1


if __name__ == "__main__":
    sys.exit(main())
