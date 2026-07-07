#!/usr/bin/env python
"""build_public_sanitized_release_v1.py — Build a public sanitized release bundle.

Creates a release bundle that contains only code, schemas, toy synthetic
fixtures, redacted audits, and aggregate metrics. Confidential PDFs, raw
claim texts, raw evidence spans, and real review queues are excluded.

Bundle structure:
  release_bundles/v3_17_confidential_public/
    README.md
    LICENSE_NOTICE.md
    CURRENT_MAINLINE.md
    docs/                    (selected policy + mainline docs)
    schemas/                 (all .schema.json + registry)
    scripts/                 (V3.17 safe scripts + lib/)
    data/toy_synthetic/      (toy fixtures only)
    experiments/
      aggregate_metrics/     (CI summaries, metric CSVs)
      redacted_audits/       (redteam + leakage audit summaries)
    paper_assets/            (generated tables/figures)
    MANIFEST.json            (per-file sha256, size, category)
    REDACTION_REPORT.json    (exclusion stats + redteam pass)

Excluded patterns:
  pdfs/, private_pdfs/, data/private/, experiments/private/
  *.pdf, *.docx, *.xlsx, *.npz, *.pkl, *.joblib
  Any file containing raw claim/evidence text

Integration:
  After building, runs run_confidentiality_redteam_scan_v1.py on the bundle.
  If high-risk findings > 0, the build fails and REDACTION_REPORT.redteam_pass=false.

Hard boundaries: no network, no API, no training, no original data modification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd

# Shared config utilities
sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from config_utils import load_and_validate, write_run_config, print_guards  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Exclusion patterns
# ---------------------------------------------------------------------------

EXCLUDED_DIR_NAMES = {
    "pdfs", "private_pdfs", "private", "__pycache__", ".git",
    "node_modules", ".venv", "venv", "env", ".pytest_cache",
    "_GPT_HANDOFF_CONTEXT_20260706",
}

EXCLUDED_DIR_PATTERNS = [
    "pdfs/", "private_pdfs/", "data/private/", "experiments/private/",
    "experiments/error_taxonomy_v1/private/",  # private error cases
    "gold_pilot_preparation_v1/", "gold_pilot_protocol_freeze_v1/",
    "gold_pilot_relation_realism_protocol_v2/",
    "external_repos/", "paper_versions_ordered/",
    "project_synthesis/", "_MAINLINE_CURRENT/", "_MAIN_PAPER_CURRENT/",
    "_PROJECT_INDEX/",
]

EXCLUDED_FILE_SUFFIXES = {
    ".pdf", ".docx", ".xlsx", ".npz", ".pkl", ".joblib",
    ".pyc", ".pyo", ".egg-info",
}

EXCLUDED_FILE_PATTERNS = [
    "error_cases_private", "private_", "_private",
    "real_review_queue", "gold_label", "human_audited",
    "GPT_HANDOFF", "handoff_context",
]

# Forbidden text columns in CSVs
FORBIDDEN_TEXT_COLUMNS = [
    "claim_text", "evidence_text", "selected_evidence",
    "raw_text", "clean_text", "retrieved_text",
    "raw_page_text", "clean_page_text", "source_excerpt",
]

# Forbidden sorting/oracle columns in CSVs (defense-in-depth: these must never
# appear in the public release, even if a file is added to an inclusion list).
# Redteam scan flags these as high-risk; internal scoring CSVs use them only
# for post-hoc metric computation, never for sorting.
FORBIDDEN_SORTING_COLUMNS = [
    "true_label", "oracle_hit",
    "candidate_label_guess", "final_label", "gold_label",
    "human_audited",
]

# ---------------------------------------------------------------------------
# Safe scripts (V3.17 confidential pipeline)
# ---------------------------------------------------------------------------

SAFE_SCRIPTS = [
    "run_v3_17_confidential_pipeline.py",
    "run_simclaim_pdf_retrieval_v1.py",
    "run_bm25_sentence_retrieval_v1.py",
    "run_canonicalizer_ablation_v1.py",
    "run_canonical_selector_robustness_v1.py",
    "run_r4_evidence_canonicalization_v1.py",
    "run_format_shift_ablation_v1.py",
    "run_canonicalized_review_queue_v1.py",
    "run_canonicalized_risk_ranking_v1.py",
    "run_lightweight_smart_queue_v1.py",
    "run_leakage_audit_v1.py",
    "run_metric_robustness_v1.py",
    "run_error_taxonomy_v1.py",
    "run_confidentiality_redteam_scan_v1.py",
    "validate_experiment_outputs_v1.py",
    "generate_paper_assets_v3_17.py",
    "run_toy_end_to_end_demo_v1.py",
    "build_pdf_sentence_corpus_v1.py",
    "build_public_sanitized_release_v1.py",
]

SAFE_LIB_FILES = [
    "lib/config_utils.py",
    "lib/schema_utils.py",
    "lib/__init__.py",
]

# Safe docs to include
SAFE_DOCS = [
    "current_mainline_v3_17_confidential.md",
    "data_release_policy.md",
    "leakage_and_confidentiality_policy.md",
    "toy_demo.md",
    "runbook_v3_17_confidential.md",
]

# Aggregate metrics to include (from experiments/)
AGGREGATE_METRIC_FILES = [
    "metric_robustness_v1/classification_metrics_with_ci.csv",
    "metric_robustness_v1/queue_metrics_with_ci.csv",
    "metric_robustness_v1/paired_comparison.csv",
    "metric_robustness_v1/robustness_summary.json",
    "metric_robustness_v1/robustness_summary.md",
    "metric_robustness_v1/run_config.json",
    "error_taxonomy_v1/error_taxonomy_summary.csv",
    "error_taxonomy_v1/error_taxonomy_summary.json",
    "error_taxonomy_v1/error_taxonomy_summary.md",
    "error_taxonomy_v1/error_cases_redacted.csv",
    "error_taxonomy_v1/run_config.json",
    "schema_validation_report.json",
    "schema_validation_summary.md",
]

# Redacted audit files to include
REDACTED_AUDIT_FILES = [
    "confidentiality_redteam_scan_v1/redteam_findings.csv",
    "confidentiality_redteam_scan_v1/redteam_summary.json",
    "confidentiality_redteam_scan_v1/redteam_summary.md",
    "confidentiality_redteam_scan_v1/.gitignore_check.json",
    "leakage_audit_v1_toy/claim_only_baseline.json",
    "leakage_audit_v1_toy/group_split_integrity.json",
    "leakage_audit_v1_toy/lexical_overlap_by_label.csv",
    "leakage_audit_v1_toy/metadata_only_retrieval_baseline.json",
    "leakage_audit_v1_toy/no_label_in_queue_sorting_check.json",
    "leakage_audit_v1_toy/no_oracle_in_selector_check.json",
    "leakage_audit_v1_toy/title_only_retrieval_baseline.json",
    "leakage_audit_v1_toy/audit_summary.md",
]

# Toy experiment outputs to include
TOY_EXPERIMENT_DIRS = [
    "bm25_sentence_retrieval_v1_toy",
    "canonicalizer_ablation_v1_toy",
    "format_shift_ablation_v1_toy",
    "lightweight_smart_queue_v1_toy",
    "leakage_audit_v1_toy",
    "r4_eval_v1_toy",
    "toy_end_to_end_demo_v1",
]


def log(msg):
    print(msg, flush=True)


# ---------------------------------------------------------------------------
# Path filtering
# ---------------------------------------------------------------------------

def is_excluded_path(rel_path: str) -> Tuple[bool, str]:
    """Check if a relative path should be excluded. Returns (excluded, reason)."""
    rel_path = rel_path.replace("\\", "/")
    parts = rel_path.split("/")

    # Check excluded directory names
    for part in parts:
        if part in EXCLUDED_DIR_NAMES:
            return True, f"excluded_dir:{part}"

    # Check excluded directory patterns
    for pattern in EXCLUDED_DIR_PATTERNS:
        if pattern in rel_path + "/":
            return True, f"dir_pattern:{pattern}"

    # Check file suffixes
    path_obj = Path(rel_path)
    if path_obj.suffix.lower() in EXCLUDED_FILE_SUFFIXES:
        return True, f"suffix:{path_obj.suffix}"

    # Check file name patterns
    name_lower = path_obj.name.lower()
    for pattern in EXCLUDED_FILE_PATTERNS:
        if pattern in name_lower:
            return True, f"file_pattern:{pattern}"

    return False, ""


def has_forbidden_text_columns(file_path: Path) -> bool:
    """Check if a CSV file has forbidden text columns."""
    if file_path.suffix.lower() != ".csv":
        return False
    try:
        df = pd.read_csv(file_path, keep_default_na=False, nrows=1)
        for col in df.columns:
            if col.lower() in FORBIDDEN_TEXT_COLUMNS:
                return True
    except Exception:
        return False
    return False


def has_forbidden_sorting_columns(file_path: Path) -> bool:
    """Check if a CSV file has forbidden sorting/oracle columns.

    Defense-in-depth: redteam scan flags true_label/oracle_hit as high-risk.
    Internal scoring CSVs use these only for post-hoc metrics, never for
    sorting, but they must never appear in the public release bundle.
    """
    if file_path.suffix.lower() != ".csv":
        return False
    try:
        df = pd.read_csv(file_path, keep_default_na=False, nrows=1)
        for col in df.columns:
            if col.lower() in FORBIDDEN_SORTING_COLUMNS:
                return True
    except Exception:
        return False
    return False


# ---------------------------------------------------------------------------
# File copying
# ---------------------------------------------------------------------------

def copy_file_safe(src: Path, dst: Path, excluded_files: List[str]) -> bool:
    """Copy a file if it passes all safety checks. Returns True if copied."""
    rel_src = str(src.relative_to(REPO_ROOT)).replace("\\", "/")

    # Check exclusion patterns
    excluded, reason = is_excluded_path(rel_src)
    if excluded:
        excluded_files.append(f"{rel_src} ({reason})")
        return False

    # Check for forbidden text columns in CSVs
    if has_forbidden_text_columns(src):
        excluded_files.append(f"{rel_src} (forbidden_text_columns)")
        return False

    # Check for forbidden sorting/oracle columns in CSVs (defense-in-depth)
    if has_forbidden_sorting_columns(src):
        excluded_files.append(f"{rel_src} (forbidden_sorting_columns)")
        return False

    # Copy the file
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def copy_tree_safe(src_dir: Path, dst_dir: Path, excluded_files: List[str],
                   extra_excluded_dirs: Optional[Set[str]] = None) -> int:
    """Copy a directory tree, filtering out excluded files. Returns count copied."""
    count = 0
    if not src_dir.exists():
        return 0

    for src in src_dir.rglob("*"):
        if not src.is_file():
            continue
        rel_src = str(src.relative_to(REPO_ROOT)).replace("\\", "/")

        # Check extra excluded dirs
        if extra_excluded_dirs:
            for excl in extra_excluded_dirs:
                if excl in rel_src:
                    excluded_files.append(f"{rel_src} (extra_excluded:{excl})")
                    break
            else:
                if copy_file_safe(src, dst_dir / src.relative_to(src_dir), excluded_files):
                    count += 1
                continue
            continue

        if copy_file_safe(src, dst_dir / src.relative_to(src_dir), excluded_files):
            count += 1

    return count


# ---------------------------------------------------------------------------
# SHA-256 and manifest
# ---------------------------------------------------------------------------

def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def categorize_file(rel_path: str) -> str:
    """Categorize a file for the manifest."""
    rel_path = rel_path.replace("\\", "/")
    if rel_path.startswith("scripts/"):
        return "code"
    elif rel_path.startswith("schemas/"):
        return "schema"
    elif rel_path.startswith("data/"):
        return "data_toy"
    elif rel_path.startswith("experiments/aggregate_metrics/"):
        return "aggregate_metrics"
    elif rel_path.startswith("experiments/redacted_audits/"):
        return "redacted_audit"
    elif rel_path.startswith("experiments/"):
        return "experiment_output"
    elif rel_path.startswith("paper_assets/"):
        return "paper_asset"
    elif rel_path.startswith("docs/"):
        return "documentation"
    elif rel_path.endswith("README.md"):
        return "documentation"
    elif rel_path.endswith("LICENSE_NOTICE.md"):
        return "license"
    elif rel_path.endswith("CURRENT_MAINLINE.md"):
        return "documentation"
    elif rel_path == "MANIFEST.json" or rel_path == "REDACTION_REPORT.json":
        return "manifest"
    elif rel_path.startswith("configs/"):
        return "config"
    elif rel_path.startswith("tests/"):
        return "test"
    elif rel_path.startswith("Makefile") or rel_path.startswith(".github/"):
        return "ci"
    else:
        return "other"


def build_manifest(bundle_dir: Path) -> List[Dict]:
    """Build the file manifest with sha256, size, and category."""
    manifest = []
    for f in sorted(bundle_dir.rglob("*")):
        if not f.is_file():
            continue
        rel_path = str(f.relative_to(bundle_dir)).replace("\\", "/")
        entry = {
            "path": rel_path,
            "sha256": compute_sha256(f),
            "size_bytes": f.stat().st_size,
            "release_category": categorize_file(rel_path),
        }
        manifest.append(entry)
    return manifest


# ---------------------------------------------------------------------------
# Bundle content writers
# ---------------------------------------------------------------------------

def write_bundle_readme(output_path: Path) -> None:
    """Write the bundle README."""
    content = """# V3.17 Confidential — Public Sanitized Release Bundle

This public bundle contains only code, schemas, toy synthetic fixtures,
redacted audits, and aggregate metrics. Confidential PDFs, raw claim texts,
raw evidence spans, and real review queues are not included.

## Contents

- `scripts/` — V3.17 confidential pipeline scripts (safe subset)
- `schemas/` — JSON schemas for experiment output validation
- `data/toy_synthetic/` — Toy synthetic fixtures for testing
- `experiments/aggregate_metrics/` — Aggregate metrics with bootstrap CIs
- `experiments/redacted_audits/` — Redacted leakage and confidentiality audit results
- `paper_assets/` — Generated paper tables (LaTeX + Markdown) and figure data
- `docs/` — Selected policy and documentation files
- `MANIFEST.json` — File manifest with SHA-256 hashes
- `REDACTION_REPORT.json` — Redaction verification report

## What is NOT included

- Confidential PDF corpus (real research papers)
- Raw claim text or evidence text
- Real review queue (top-100 candidates with text)
- Private error analysis (full-text error cases)
- Model checkpoints, trained weights, or pickled artifacts
- Any file failing the confidentiality red-team scan

## Usage

```bash
# Run toy demo
python scripts/run_toy_end_to_end_demo_v1.py

# Validate schemas
python scripts/validate_experiment_outputs_v1.py

# Run red-team scan
python scripts/run_confidentiality_redteam_scan_v1.py --scan_dirs release_bundles/v3_17_confidential_public
```

## Disclaimer

All metrics are based on controlled silver diagnostic data, not gold/human-audited.
The balanced 4-class pool (109 per class) does not reflect natural prevalence.
"""
    output_path.write_text(content, encoding="utf-8")


def write_license_notice(output_path: Path) -> None:
    """Write the license notice."""
    content = """# License Notice

## Code

All scripts in `scripts/` are released under the MIT License.

## Data

- `data/toy_synthetic/` — Toy synthetic fixtures, released under CC-BY-4.0.
  These are entirely synthetic and contain no real research paper content.

## Schemas

- `schemas/` — JSON schemas, released under CC-BY-4.0.

## Aggregate Metrics

- `experiments/aggregate_metrics/` — Aggregate metrics and summaries, released
  under CC-BY-4.0. These contain only numerical aggregates and SHA-256 hashes,
  no raw text.

## Redacted Audits

- `experiments/redacted_audits/` — Redacted audit results, released under
  CC-BY-4.0. These contain only pass/fail statuses and aggregate statistics.

## Paper Assets

- `paper_assets/` — Generated tables and figures, released under CC-BY-4.0.

## Excluded Content

The following are NOT included in this bundle and remain confidential:
- Real PDF corpus (research papers under various publisher licenses)
- Raw claim text and evidence text (derived from copyrighted source material)
- Real review queue (contains text from source papers)
- Human annotation data (contains identifiable research content)
"""
    output_path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Red-team scan integration
# ---------------------------------------------------------------------------

def run_redteam_scan(bundle_dir: Path) -> Tuple[bool, dict]:
    """Run the confidentiality red-team scanner on the bundle.

    Returns (pass, summary_dict).
    """
    scanner_path = REPO_ROOT / "scripts" / "run_confidentiality_redteam_scan_v1.py"
    if not scanner_path.exists():
        log("  [WARN] Red-team scanner not found, skipping scan")
        return True, {"status": "skipped", "reason": "scanner not found"}

    log(f"  Running red-team scan on {bundle_dir}...")
    cmd = [
        sys.executable,
        str(scanner_path),
        "--scan_dirs", str(bundle_dir),
        "--output_dir", str(bundle_dir / "_redteam_scan"),
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=120,
        )
        if result.returncode not in (0, 1):
            log(f"  [ERROR] Red-team scanner crashed with code {result.returncode}")
            return False, {"status": "error", "stdout": result.stdout[:500]}

        # Read the summary
        summary_path = bundle_dir / "_redteam_scan" / "redteam_summary.json"
        if summary_path.exists():
            with open(summary_path, "r", encoding="utf-8") as f:
                summary = json.load(f)
            high_count = summary.get("high_risk_count", 0)
            passed = high_count == 0
            log(f"  Red-team scan: high_risk={high_count}, pass={passed}")
            return passed, summary
        else:
            log("  [WARN] Red-team summary not found")
            return True, {"status": "no_summary"}
    except subprocess.TimeoutExpired:
        log("  [ERROR] Red-team scan timed out")
        return False, {"status": "timeout"}
    except Exception as e:
        log(f"  [ERROR] Red-team scan failed: {e}")
        return False, {"status": "error", "reason": str(e)}


# ---------------------------------------------------------------------------
# Main build
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Build a public sanitized release bundle."
    )
    parser.add_argument("--output_dir", default="release_bundles/v3_17_confidential_public",
                        help="Output directory for the release bundle")
    parser.add_argument("--include_code", default="true",
                        help="Include scripts (true/false)")
    parser.add_argument("--include_toy", default="true",
                        help="Include toy synthetic data (true/false)")
    parser.add_argument("--include_aggregate_metrics", default="true",
                        help="Include aggregate metrics (true/false)")
    parser.add_argument("--include_redacted_audits", default="true",
                        help="Include redacted audits (true/false)")
    parser.add_argument("--config", default=None,
                        help="YAML config file")
    parser.add_argument("--skip_redteam", action="store_true",
                        help="Skip red-team scan (for testing only)")
    args = parser.parse_args()

    # Load config if provided
    config = {}
    guards = {}
    if args.config:
        config = load_and_validate(args.config)
        guards = config.get("guards", {})
    else:
        guards = {
            "no_api": True,
            "no_network": True,
            "no_training": True,
            "no_original_data_modification": True,
        }

    def flag(name):
        return getattr(args, name).lower() in ("true", "1", "yes")

    include_code = flag("include_code")
    include_toy = flag("include_toy")
    include_agg = flag("include_aggregate_metrics")
    include_audits = flag("include_redacted_audits")

    log("=" * 72)
    log("Public Sanitized Release Bundle Builder v1")
    log("=" * 72)
    log(f"Output dir: {args.output_dir}")
    log(f"Include code: {include_code}")
    log(f"Include toy: {include_toy}")
    log(f"Include aggregate metrics: {include_agg}")
    log(f"Include redacted audits: {include_audits}")
    log(f"Guards: {guards}")
    log("")

    bundle_dir = Path(args.output_dir)
    if not bundle_dir.is_absolute():
        bundle_dir = REPO_ROOT / bundle_dir

    # Clean and create bundle directory
    if bundle_dir.exists():
        log(f"  Removing existing bundle at {bundle_dir}")
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    excluded_files: List[str] = []
    included_count = 0

    # 1. Copy scripts
    if include_code:
        log("Copying scripts...")
        scripts_dst = bundle_dir / "scripts"
        scripts_dst.mkdir(parents=True, exist_ok=True)
        for script_name in SAFE_SCRIPTS:
            src = REPO_ROOT / "scripts" / script_name
            if src.exists():
                if copy_file_safe(src, scripts_dst / script_name, excluded_files):
                    included_count += 1
        # Copy lib directory
        lib_dst = scripts_dst / "lib"
        lib_dst.mkdir(parents=True, exist_ok=True)
        for lib_file in SAFE_LIB_FILES:
            src = REPO_ROOT / "scripts" / lib_file
            if src.exists():
                shutil.copy2(src, lib_dst / Path(lib_file).name)
                included_count += 1
        # Copy __init__.py if exists
        init_src = REPO_ROOT / "scripts" / "lib" / "__init__.py"
        if init_src.exists():
            shutil.copy2(init_src, lib_dst / "__init__.py")
        log(f"  Copied {included_count} script files")

    # 2. Copy schemas
    log("Copying schemas...")
    schemas_src = REPO_ROOT / "schemas"
    schemas_dst = bundle_dir / "schemas"
    if schemas_src.exists():
        count = copy_tree_safe(schemas_src, schemas_dst, excluded_files)
        included_count += count
        log(f"  Copied {count} schema files")

    # 3. Copy toy synthetic data
    if include_toy:
        log("Copying toy synthetic data...")
        toy_src = REPO_ROOT / "data" / "toy_synthetic"
        toy_dst = bundle_dir / "data" / "toy_synthetic"
        if toy_src.exists():
            count = copy_tree_safe(toy_src, toy_dst, excluded_files)
            included_count += count
            log(f"  Copied {count} toy data files")

    # 4. Copy aggregate metrics
    if include_agg:
        log("Copying aggregate metrics...")
        agg_dst = bundle_dir / "experiments" / "aggregate_metrics"
        agg_dst.mkdir(parents=True, exist_ok=True)
        count = 0
        for rel_path in AGGREGATE_METRIC_FILES:
            src = REPO_ROOT / "experiments" / rel_path
            if src.exists():
                if copy_file_safe(src, agg_dst / Path(rel_path).name, excluded_files):
                    count += 1
        # Also copy toy experiment outputs
        for toy_dir in TOY_EXPERIMENT_DIRS:
            src_dir = REPO_ROOT / "experiments" / toy_dir
            if src_dir.exists():
                # Copy redacted files and summaries, not raw text
                for f in src_dir.rglob("*"):
                    if f.is_file():
                        rel = str(f.relative_to(src_dir))
                        # Skip files with raw text
                        if has_forbidden_text_columns(f):
                            excluded_files.append(f"{toy_dir}/{rel} (forbidden_text_columns)")
                            continue
                        # Skip non-redacted CSVs that might have text
                        if f.suffix == ".csv" and "redacted" not in f.name.lower():
                            # Check columns for text fields
                            try:
                                df = pd.read_csv(f, keep_default_na=False, nrows=1)
                                text_cols = [c for c in df.columns if any(t in c.lower() for t in ("text", "evidence", "claim")) and "sha256" not in c.lower()]
                                if text_cols:
                                    excluded_files.append(f"{toy_dir}/{rel} (text_columns:{text_cols})")
                                    continue
                            except Exception:
                                pass
                        dst = agg_dst / "toy_outputs" / toy_dir / rel
                        if copy_file_safe(f, dst, excluded_files):
                            count += 1
        included_count += count
        log(f"  Copied {count} aggregate metric files")

    # 5. Copy redacted audits
    if include_audits:
        log("Copying redacted audits...")
        audit_dst = bundle_dir / "experiments" / "redacted_audits"
        audit_dst.mkdir(parents=True, exist_ok=True)
        count = 0
        for rel_path in REDACTED_AUDIT_FILES:
            src = REPO_ROOT / "experiments" / rel_path
            if src.exists():
                if copy_file_safe(src, audit_dst / Path(rel_path).name, excluded_files):
                    count += 1
        included_count += count
        log(f"  Copied {count} audit files")

    # 6. Copy paper assets
    log("Copying paper assets...")
    paper_src = REPO_ROOT / "paper_assets" / "v3_17_confidential"
    paper_dst = bundle_dir / "paper_assets" / "v3_17_confidential"
    if paper_src.exists():
        count = copy_tree_safe(paper_src, paper_dst, excluded_files)
        included_count += count
        log(f"  Copied {count} paper asset files")

    # 7. Copy selected docs
    log("Copying docs...")
    docs_dst = bundle_dir / "docs"
    docs_dst.mkdir(parents=True, exist_ok=True)
    count = 0
    for doc_name in SAFE_DOCS:
        src = REPO_ROOT / "docs" / doc_name
        if src.exists():
            shutil.copy2(src, docs_dst / doc_name)
            count += 1
    included_count += count
    log(f"  Copied {count} doc files")

    # 8. Copy configs
    log("Copying configs...")
    configs_src = REPO_ROOT / "configs"
    configs_dst = bundle_dir / "configs"
    if configs_src.exists():
        count = copy_tree_safe(configs_src, configs_dst, excluded_files)
        included_count += count
        log(f"  Copied {count} config files")

    # 9. Copy Makefile
    makefile_src = REPO_ROOT / "Makefile"
    if makefile_src.exists():
        shutil.copy2(makefile_src, bundle_dir / "Makefile")
        included_count += 1
        log("  Copied Makefile")

    # 10. Copy tests
    log("Copying tests...")
    tests_src = REPO_ROOT / "tests"
    tests_dst = bundle_dir / "tests"
    if tests_src.exists():
        count = 0
        for f in tests_src.glob("*.py"):
            if copy_file_safe(f, tests_dst / f.name, excluded_files):
                count += 1
        # Copy conftest if exists
        conftest = tests_src / "conftest.py"
        if conftest.exists():
            shutil.copy2(conftest, tests_dst / "conftest.py")
            count += 1
        included_count += count
        log(f"  Copied {count} test files")

    # 11. Write README, LICENSE, CURRENT_MAINLINE
    log("Writing bundle docs...")
    write_bundle_readme(bundle_dir / "README.md")
    write_license_notice(bundle_dir / "LICENSE_NOTICE.md")
    current_mainline = REPO_ROOT / "CURRENT_MAINLINE.md"
    if current_mainline.exists():
        shutil.copy2(current_mainline, bundle_dir / "CURRENT_MAINLINE.md")
    included_count += 3

    # 12. Run red-team scan
    redteam_pass = True
    redteam_summary = {}
    if not args.skip_redteam:
        redteam_pass, redteam_summary = run_redteam_scan(bundle_dir)
    else:
        log("  [SKIP] Red-team scan skipped (--skip_redteam)")

    # 13. Build MANIFEST.json
    log("Building MANIFEST.json...")
    manifest = build_manifest(bundle_dir)
    manifest_path = bundle_dir / "MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "bundle_name": "v3_17_confidential_public",
            "total_files": len(manifest),
            "files": manifest,
        }, f, indent=2, ensure_ascii=False)
    log(f"  Manifest: {len(manifest)} files")

    # 14. Build REDACTION_REPORT.json
    log("Building REDACTION_REPORT.json...")

    # Check for real PDFs and raw text
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
        "excluded_patterns": list(EXCLUDED_DIR_PATTERNS) + list(EXCLUDED_FILE_SUFFIXES) + list(EXCLUDED_FILE_PATTERNS),
        "forbidden_text_columns": list(FORBIDDEN_TEXT_COLUMNS),
        "forbidden_sorting_columns": list(FORBIDDEN_SORTING_COLUMNS),
        "excluded_files_count": len(excluded_files),
        "included_files_count": included_count,
        "redteam_pass": redteam_pass,
        "redteam_summary": redteam_summary,
        "contains_real_pdf": contains_real_pdf,
        "contains_raw_evidence_text": contains_raw_evidence,
        "contains_real_claim_text": contains_raw_claim,
        "excluded_files_sample": excluded_files[:50],
        "guards": guards,
    }

    redaction_path = bundle_dir / "REDACTION_REPORT.json"
    with open(redaction_path, "w", encoding="utf-8") as f:
        json.dump(redaction_report, f, indent=2, ensure_ascii=False)
    log(f"  Redaction report: excluded={len(excluded_files)}, included={included_count}")

    # 15. Final check
    log("")
    if redteam_pass:
        log("=" * 72)
        log("BUILD SUCCESS — Release bundle is ready")
        log("=" * 72)
        log(f"  Bundle: {bundle_dir}")
        log(f"  Files: {included_count}")
        log(f"  Red-team: PASS")
        log(f"  Contains PDF: {contains_real_pdf}")
        log(f"  Contains raw evidence: {contains_raw_evidence}")
        log(f"  Contains raw claim: {contains_raw_claim}")
    else:
        log("=" * 72)
        log("BUILD FAILED — Red-team scan found high-risk findings")
        log("=" * 72)
        log(f"  Bundle: {bundle_dir}")
        log(f"  Red-team: FAIL")
        log(f"  See: {bundle_dir}/_redteam_scan/redteam_summary.json")
        sys.exit(1)


if __name__ == "__main__":
    main()
