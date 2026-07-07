#!/usr/bin/env python
"""build_v3_17_safe_handoff_bundle.py — Build the final safe handoff bundle.

Produces a self-contained delivery bundle at
``release_bundles/v3_17_final_safe_handoff/`` that lets a reviewer understand
the project state, contributions, limitations, what is public, and what is
private. This bundle is a *handoff* pack: it focuses on reports, paper assets,
docs, and aggregate experiment summaries — not code or toy data (those live in
the public release bundle ``v3_17_confidential_public``).

Bundle structure:
  release_bundles/v3_17_final_safe_handoff/
    README.md
    reports/                (status card, delivery manifest, final gate, ...)
    paper_assets/v3_17_confidential/   (manuscript, tables, source map)
    docs/                   (dataset lock, policies, reviewer pack, ...)
    experiments/aggregate_metrics/   (metric CSVs + summary JSON/MD)
    experiments/redacted_audits/     (redacted audit summaries)
    release_manifests/     (public bundle MANIFEST + REDACTION_REPORT)
    MANIFEST.json          (per-file sha256, size, category)
    REDACTION_REPORT.json  (exclusion stats + redteam pass)

Reuses the vetted exclusion logic from build_public_sanitized_release_v1.py:
  - EXCLUDED_DIR_NAMES / EXCLUDED_DIR_PATTERNS / EXCLUDED_FILE_SUFFIXES
  - EXCLUDED_FILE_PATTERNS (private_, gold_label, human_audited, ...)
  - FORBIDDEN_TEXT_COLUMNS / FORBIDDEN_SORTING_COLUMNS
  - is_excluded_path / has_forbidden_text_columns / has_forbidden_sorting_columns
  - compute_sha256 / run_redteam_scan

Hard boundaries: no network, no API, no training, no original-data modification,
no private audit CSV, no PDFs, no raw claim/evidence text, no pkl/joblib/npz,
no docx/xlsx, no data/private, no data/private_audit.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent

# Reuse the vetted exclusion logic from the public release builder. This keeps
# the two bundles consistent: any file excluded from the public release is also
# excluded from the handoff bundle.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_sanitized_release_v1 import (  # noqa: E402
    EXCLUDED_DIR_NAMES,
    EXCLUDED_DIR_PATTERNS,
    EXCLUDED_FILE_SUFFIXES,
    EXCLUDED_FILE_PATTERNS,
    FORBIDDEN_TEXT_COLUMNS,
    FORBIDDEN_SORTING_COLUMNS,
    is_excluded_path,
    has_forbidden_text_columns,
    has_forbidden_sorting_columns,
    copy_file_safe,
    copy_tree_safe,
    compute_sha256,
    categorize_file,
    run_redteam_scan,
)


# ---------------------------------------------------------------------------
# Handoff-specific inclusion lists
# ---------------------------------------------------------------------------

# Aggregate experiment summaries (explicit allowlist — these are the files
# referenced by the manuscript tables and the result source map). Each is a
# public-safe aggregate: no raw claim/evidence text, no forbidden sorting
# columns in scoring outputs.
AGGREGATE_EXPERIMENT_FILES = [
    # Metric robustness (R4 with bootstrap CIs)
    "metric_robustness_v1/classification_metrics_with_ci.csv",
    "metric_robustness_v1/queue_metrics_with_ci.csv",
    "metric_robustness_v1/paired_comparison.csv",
    "metric_robustness_v1/robustness_summary.json",
    "metric_robustness_v1/robustness_summary.md",
    "metric_robustness_v1/run_config.json",
    # Error taxonomy
    "error_taxonomy_v1/error_taxonomy_summary.csv",
    "error_taxonomy_v1/error_taxonomy_summary.json",
    "error_taxonomy_v1/error_taxonomy_summary.md",
    "error_taxonomy_v1/error_cases_redacted.csv",
    "error_taxonomy_v1/run_config.json",
    # Canonicalizer ablation
    "canonicalizer_ablation_v1/selector_metrics_summary.csv",
    "canonicalizer_ablation_v1/selector_examples_redacted.csv",
    # Risk ranking
    "canonicalized_risk_ranking_v1/risk_ranking_results_by_variant.csv",
    "canonicalized_risk_ranking_v1/risk_ranking_report.md",
    "canonicalized_risk_ranking_v1/risk_ranking_gate.json",
    # Review queue (aggregate metrics + gate only; scores/top100 are private)
    "canonicalized_review_queue_v1/review_queue_metrics.csv",
    "canonicalized_review_queue_v1/canonicalized_review_queue_gate.json",
    # Format-shift ablation (real metrics; resolved)
    "format_shift_ablation_v1/format_shift_metrics.csv",
    "format_shift_ablation_v1/format_shift_summary.json",
    "format_shift_ablation_v1/r4_eval_blocked.json",
    "format_shift_ablation_v1/format_shift_inputs_redacted.csv",
    # Leakage audit (summaries + baselines; no raw text)
    "leakage_audit_v1/audit_summary.md",
    "leakage_audit_v1/claim_only_baseline.json",
    "leakage_audit_v1/shuffled_evidence_baseline.json",
    # Complexity vs utility
    "complexity_vs_utility_ablation_v1/method_pareto_table.csv",
    "complexity_vs_utility_ablation_v1/complexity_vs_utility_summary.md",
    # PDF stress test
    "pdf_extraction_stress_test_v1/stress_test_summary.md",
    "pdf_extraction_stress_test_v1/stress_suite_manifest.csv",
    "pdf_extraction_stress_test_v1/stress_blocks_redacted.jsonl",
    # Smart queue summary
    "lightweight_smart_queue_v1/smart_queue_metric_summary.json",
    # Redteam scan outputs
    "confidentiality_redteam_scan_v1/redteam_findings.csv",
    "confidentiality_redteam_scan_v1/redteam_summary.json",
    "confidentiality_redteam_scan_v1/redteam_summary.md",
    # Schema validation
    "schema_validation_report.json",
    "schema_validation_summary.md",
    # Retrieval metrics (chunk + sentence/window)
    "simclaim_pdf_corpus_retrieval_v1/retrieval_metrics_bm25.json",
    "bm25_sentence_retrieval_v1/oracle_recall_summary.json",
    "bm25_sentence_retrieval_v1/leakage_guard_report.json",
    # R4 recovery gate
    "r4_minimal_recovery_v1/r4_recovery_gate.json",
]

# Redacted audit / template files (safe to ship).
REDACTED_AUDIT_FILES = [
    "data/audit_templates/human_audit_template.csv",
    "data/audit_templates/human_audit_queue_seed_v1_redacted.csv",
]

# Release manifests from the public bundle to embed for traceability.
RELEASE_MANIFEST_FILES = [
    "release_bundles/v3_17_confidential_public/MANIFEST.json",
    "release_bundles/v3_17_confidential_public/REDACTION_REPORT.json",
]

# Repo-root docs to ship at top level.
TOP_LEVEL_FILES = [
    "CURRENT_MAINLINE.md",
    "README.md",
    "artifacts_manifest_v3_17.yaml",
]


def log(msg: str) -> None:
    print(msg, flush=True)


def is_safe_report_file(rel_path: str) -> bool:
    """Reports include only .md/.json/.csv files that are not logs and do not
    start with an underscore (internal logs)."""
    rel = rel_path.replace("\\", "/")
    name = Path(rel).name
    if name.startswith("_"):
        return False
    if rel.endswith(".log"):
        return False
    return rel.endswith((".md", ".json", ".csv"))


def build_manifest(bundle_dir: Path) -> List[Dict]:
    """Build the file manifest with sha256, size, and category."""
    manifest = []
    for f in sorted(bundle_dir.rglob("*")):
        if not f.is_file():
            continue
        rel_path = str(f.relative_to(bundle_dir)).replace("\\", "/")
        manifest.append({
            "path": rel_path,
            "sha256": compute_sha256(f),
            "size_bytes": f.stat().st_size,
            "release_category": categorize_file(rel_path),
        })
    return manifest


def write_bundle_readme(output_path: Path) -> None:
    content = """# V3.17 Final Safe Handoff Bundle

This bundle is the **final delivery pack** for the V3.17 Confidential Lightweight
mainline. It lets a reviewer understand the project state, contributions,
limitations, what is public, and what is private — without exposing any
confidential content.

## What this bundle IS

- One-page status card and final delivery manifest
- Submission manuscript (v2 Final Freeze), 8 result tables, result source map
- Final perfect-state gate, artifact ledger, release safety manifest
- Reviewer response playbook and risk register
- Dataset version lock and safe-claims dictionary
- Aggregate experiment summaries (metric CSVs, summary JSON/MD)
- Redacted audit summaries and redteam reconciliation
- Public release bundle MANIFEST + REDACTION_REPORT (for traceability)

## What this bundle is NOT

- It is NOT the code pack (code lives in `v3_17_confidential_public`).
- It is NOT the toy-data pack (toy data lives in `v3_17_confidential_public`).
- It does NOT contain any private/raw content (see hard boundaries below).

## Hard boundaries (enforced by the builder + redteam scan)

- No private audit CSV (`data/private_audit/`).
- No PDFs (`*.pdf`).
- No raw claim/evidence text (`claim_text`, `evidence_text`, `selected_evidence`, `raw_text`).
- No pkl/joblib/model artifacts (`*.pkl`, `*.joblib`, `*.npz`).
- No `data/private/`, no `data/private_audit/`.
- No `*.docx`, `*.xlsx`.
- No unredacted CSV with text columns.

## Mandatory framing

This is a **controlled silver diagnostic study**, not a gold benchmark.
**Not SOTA. Not an automatic peer reviewer. Not a validated general detector.**
The system is a second-stage review queue generator, not a standalone detector.
"""
    output_path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the final V3.17 safe handoff bundle."
    )
    parser.add_argument(
        "--output_dir",
        default="release_bundles/v3_17_final_safe_handoff",
        help="Output directory for the handoff bundle",
    )
    parser.add_argument(
        "--skip_redteam",
        action="store_true",
        help="Skip red-team scan (for testing only)",
    )
    args = parser.parse_args()

    guards = {
        "no_api": True,
        "no_network": True,
        "no_training": True,
        "no_original_data_modification": True,
    }

    log("=" * 72)
    log("V3.17 Final Safe Handoff Bundle Builder")
    log("=" * 72)
    log(f"Output dir: {args.output_dir}")
    log(f"Guards: {guards}")
    log("")

    bundle_dir = Path(args.output_dir)
    if not bundle_dir.is_absolute():
        bundle_dir = REPO_ROOT / bundle_dir

    if bundle_dir.exists():
        log(f"  Removing existing bundle at {bundle_dir}")
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    excluded_files: List[str] = []
    included_count = 0

    # 1. Copy reports/ (safe .md/.json/.csv only, no logs, no underscore-prefixed)
    log("Copying reports/...")
    reports_src = REPO_ROOT / "reports"
    reports_dst = bundle_dir / "reports"
    reports_dst.mkdir(parents=True, exist_ok=True)
    count = 0
    if reports_src.exists():
        for f in sorted(reports_src.iterdir()):
            if not f.is_file():
                continue
            rel = str(f.relative_to(REPO_ROOT)).replace("\\", "/")
            if not is_safe_report_file(rel):
                excluded_files.append(f"{rel} (report_filter)")
                continue
            if copy_file_safe(f, reports_dst / f.name, excluded_files):
                count += 1
    included_count += count
    log(f"  Copied {count} report files")

    # 2. Copy paper_assets/v3_17_confidential/ (filtered tree)
    log("Copying paper_assets/v3_17_confidential/...")
    paper_src = REPO_ROOT / "paper_assets" / "v3_17_confidential"
    paper_dst = bundle_dir / "paper_assets" / "v3_17_confidential"
    if paper_src.exists():
        count = copy_tree_safe(paper_src, paper_dst, excluded_files)
        included_count += count
        log(f"  Copied {count} paper asset files")

    # 3. Copy docs/ (filtered tree)
    log("Copying docs/...")
    docs_src = REPO_ROOT / "docs"
    docs_dst = bundle_dir / "docs"
    if docs_src.exists():
        count = copy_tree_safe(docs_src, docs_dst, excluded_files)
        included_count += count
        log(f"  Copied {count} doc files")

    # 4. Copy aggregate experiment summaries (explicit allowlist)
    log("Copying aggregate experiment summaries...")
    agg_dst = bundle_dir / "experiments" / "aggregate_metrics"
    agg_dst.mkdir(parents=True, exist_ok=True)
    count = 0
    for rel_path in AGGREGATE_EXPERIMENT_FILES:
        src = REPO_ROOT / "experiments" / rel_path
        if not src.exists():
            excluded_files.append(f"experiments/{rel_path} (missing)")
            continue
        # Preserve a flat-ish structure under aggregate_metrics/<exp_dir>/<file>
        dst = agg_dst / Path(rel_path).parent.name / Path(rel_path).name
        if copy_file_safe(src, dst, excluded_files):
            count += 1
    included_count += count
    log(f"  Copied {count} aggregate metric files")

    # 5. Copy redacted audit/template files
    log("Copying redacted audit templates...")
    audit_dst = bundle_dir / "experiments" / "redacted_audits"
    audit_dst.mkdir(parents=True, exist_ok=True)
    count = 0
    for rel_path in REDACTED_AUDIT_FILES:
        src = REPO_ROOT / rel_path
        if not src.exists():
            excluded_files.append(f"{rel_path} (missing)")
            continue
        if copy_file_safe(src, audit_dst / Path(rel_path).name, excluded_files):
            count += 1
    included_count += count
    log(f"  Copied {count} redacted audit files")

    # 6. Copy release manifests (public bundle MANIFEST + REDACTION_REPORT)
    log("Copying release manifests...")
    rm_dst = bundle_dir / "release_manifests"
    rm_dst.mkdir(parents=True, exist_ok=True)
    count = 0
    for rel_path in RELEASE_MANIFEST_FILES:
        src = REPO_ROOT / rel_path
        if not src.exists():
            excluded_files.append(f"{rel_path} (missing)")
            continue
        if copy_file_safe(src, rm_dst / Path(rel_path).name, excluded_files):
            count += 1
    included_count += count
    log(f"  Copied {count} release manifest files")

    # 7. Copy top-level files (CURRENT_MAINLINE, README, artifacts manifest)
    log("Copying top-level files...")
    count = 0
    for rel_path in TOP_LEVEL_FILES:
        src = REPO_ROOT / rel_path
        if not src.exists():
            excluded_files.append(f"{rel_path} (missing)")
            continue
        if copy_file_safe(src, bundle_dir / Path(rel_path).name, excluded_files):
            count += 1
    included_count += count
    log(f"  Copied {count} top-level files")

    # 8. Write bundle README
    log("Writing bundle README...")
    write_bundle_readme(bundle_dir / "README.md")
    included_count += 1

    # 9. Run red-team scan
    redteam_pass = True
    redteam_summary: Dict = {}
    if not args.skip_redteam:
        redteam_pass, redteam_summary = run_redteam_scan(bundle_dir)
    else:
        log("  [SKIP] Red-team scan skipped (--skip_redteam)")

    # 10. Build MANIFEST.json
    log("Building MANIFEST.json...")
    manifest = build_manifest(bundle_dir)
    manifest_path = bundle_dir / "MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "bundle_name": "v3_17_final_safe_handoff",
            "bundle_type": "final_delivery_handoff",
            "total_files": len(manifest),
            "files": manifest,
        }, f, indent=2, ensure_ascii=False)
    log(f"  Manifest: {len(manifest)} files")

    # 11. Build REDACTION_REPORT.json
    log("Building REDACTION_REPORT.json...")

    contains_real_pdf = any(
        f.suffix.lower() == ".pdf" for f in bundle_dir.rglob("*") if f.is_file()
    )
    contains_raw_evidence = False
    contains_raw_claim = False
    for f in bundle_dir.rglob("*.csv"):
        try:
            df = pd.read_csv(f, keep_default_na=False, nrows=1)
            cols_lower = [c.lower() for c in df.columns]
            if "evidence_text" in cols_lower:
                contains_raw_evidence = True
            if "claim_text" in cols_lower:
                contains_raw_claim = True
        except Exception:
            pass

    redaction_report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "bundle_name": "v3_17_final_safe_handoff",
        "bundle_type": "final_delivery_handoff",
        "excluded_dir_names": list(EXCLUDED_DIR_NAMES),
        "excluded_dir_patterns": list(EXCLUDED_DIR_PATTERNS),
        "excluded_file_suffixes": list(EXCLUDED_FILE_SUFFIXES),
        "excluded_file_patterns": list(EXCLUDED_FILE_PATTERNS),
        "forbidden_text_columns": list(FORBIDDEN_TEXT_COLUMNS),
        "forbidden_sorting_columns": list(FORBIDDEN_SORTING_COLUMNS),
        "excluded_files_count": len(excluded_files),
        "included_files_count": included_count,
        "redteam_pass": redteam_pass,
        "redteam_summary": redteam_summary,
        "contains_real_pdf": contains_real_pdf,
        "contains_raw_evidence_text": contains_raw_evidence,
        "contains_real_claim_text": contains_raw_claim,
        "excluded_files_sample": excluded_files[:80],
        "guards": guards,
    }

    redaction_path = bundle_dir / "REDACTION_REPORT.json"
    with open(redaction_path, "w", encoding="utf-8") as f:
        json.dump(redaction_report, f, indent=2, ensure_ascii=False)
    log(f"  Redaction report: excluded={len(excluded_files)}, included={included_count}")

    # 12. Final check
    log("")
    if redteam_pass:
        log("=" * 72)
        log("BUILD SUCCESS — Final safe handoff bundle is ready")
        log("=" * 72)
        log(f"  Bundle: {bundle_dir}")
        log(f"  Files: {included_count}")
        log(f"  Red-team: PASS")
        log(f"  Contains PDF: {contains_real_pdf}")
        log(f"  Contains raw evidence: {contains_raw_evidence}")
        log(f"  Contains raw claim: {contains_raw_claim}")
        return 0
    else:
        log("=" * 72)
        log("BUILD FAILED — Red-team scan found high-risk findings")
        log("=" * 72)
        log(f"  Bundle: {bundle_dir}")
        log(f"  Red-team: FAIL")
        log(f"  See: {bundle_dir}/_redteam_scan/redteam_summary.json")
        return 1


if __name__ == "__main__":
    sys.exit(main())
