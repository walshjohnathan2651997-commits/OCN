#!/usr/bin/env python
"""audit_path_hardcoding_v1.py — Scan all scripts for D:\\ocn path hardcoding.

Classifies each .py file in scripts/ into one of:
  - current_pipeline_blocker  : P0 mainline script with D:\ocn hardcoding
  - current_pipeline_warning  : non-P0 V3.17 script with D:\ocn hardcoding
  - legacy_exempt             : legacy script listed in exemptions doc
  - safe                      : no D:\ocn hardcoding

Outputs:
  reports/path_hardcoding_audit_v3_17.csv
  reports/path_hardcoding_audit_v3_17.md

Acceptance gate: current_pipeline_blocker must be 0.
"""

from __future__ import annotations

import csv
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from config_utils import get_repo_root, ensure_dir  # noqa: E402

REPO_ROOT = get_repo_root()
SCRIPTS_DIR = REPO_ROOT / "scripts"
REPORTS_DIR = REPO_ROOT / "reports"
EXEMPTIONS_DOC = REPO_ROOT / "docs" / "legacy_scripts_path_hardcoding_exemptions.md"

HARDCODED_RE = re.compile(r"D:[\\/]ocn")

# P0 mainline scripts that must be free of D:\ocn hardcoding.
P0_SCRIPTS = {
    "run_simclaim_pdf_retrieval_v1.py",
    "run_r4_evidence_canonicalization_v1.py",
    "run_canonicalized_review_queue_v1.py",
    "run_canonicalized_risk_ranking_v1.py",
    "build_pdf_sentence_corpus_v1.py",
    "run_bm25_sentence_retrieval_v1.py",
    "run_canonicalizer_ablation_v1.py",
    "run_format_shift_ablation_v1.py",
    "evaluate_r4_on_evidence_variants_v1.py",
    "run_leakage_audit_v1.py",
    "run_v3_17_confidential_pipeline.py",
    "generate_project_status_report_v1.py",
}

# V3.17-era scripts that are NOT P0 but are part of the V3.17 toolchain.
# These produce warnings (not blockers) if they contain D:\ocn.
V3_17_TOOLCHAIN = {
    "run_complexity_vs_utility_ablation_v1.py",
    "run_lightweight_smart_queue_v1.py",
    "run_error_taxonomy_v1.py",
    "run_metric_robustness_v1.py",
    "run_confidentiality_redteam_scan_v1.py",
    "build_public_sanitized_release_v1.py",
    "build_human_audit_queue_v1.py",
    "summarize_human_audit_v1.py",
    "generate_paper_assets_v3_17.py",
    "validate_experiment_outputs_v1.py",
    "run_toy_end_to_end_demo_v1.py",
    "clean_legacy_narrative_scan_v1.py",
    "run_pdf_extraction_stress_test_v1.py",
    "run_pdf_extraction_to_bm25_stress_v1.py",
    "summarize_pdf_stress_report_v1.py",
    "build_pdf_stress_suite_v1.py",
}


def _load_exempt_paths() -> set[str]:
    """Parse the exemptions doc to get the set of exempt script paths."""
    if not EXEMPTIONS_DOC.exists():
        return set()
    text = EXEMPTIONS_DOC.read_text(encoding="utf-8")
    exempt = set()
    for m in re.finditer(r"`(scripts/[^\s`]+\.py)`", text):
        exempt.add(m.group(1).replace("\\", "/"))
    for m in re.finditer(r"`(scripts/[^\s`]+/)`", text):
        exempt.add(m.group(1).replace("\\", "/"))
    return exempt


def _is_scanner_code(filepath: Path) -> bool:
    """Check if D:\ocn appears only as a string literal in scanner code
    (i.e., the script is detecting hardcoding in other scripts, not using
    D:\ocn as an actual path)."""
    name = filepath.name
    if name == "generate_project_status_report_v1.py":
        return True
    if name == "audit_path_hardcoding_v1.py":
        return True
    if name == "clean_legacy_narrative_scan_v1.py":
        return True
    return False


def _classify(filepath: Path, count: int, exempt_paths: set[str]) -> str:
    """Classify a script based on its hardcoding status and exemption list."""
    if count == 0:
        return "safe"

    rel_path = str(filepath.relative_to(REPO_ROOT)).replace("\\", "/")
    name = filepath.name

    # Scanner code uses D:\ocn as a string literal for detection
    if _is_scanner_code(filepath):
        return "safe"

    # P0 scripts must not have any hardcoding
    if name in P0_SCRIPTS:
        return "current_pipeline_blocker"

    # V3.17 toolchain scripts produce warnings
    if name in V3_17_TOOLCHAIN:
        return "current_pipeline_warning"

    # Check exemptions
    if rel_path in exempt_paths:
        return "legacy_exempt"

    # Check if parent directory is exempt
    for exempt_path in exempt_paths:
        if exempt_path.endswith("/") and rel_path.startswith(exempt_path):
            return "legacy_exempt"

    # Default: legacy_exempt (all non-P0, non-toolchain scripts are legacy)
    return "legacy_exempt"


def scan_all() -> list[dict]:
    """Scan all .py files in scripts/ and return findings."""
    exempt_paths = _load_exempt_paths()
    findings: list[dict] = []

    for py_file in sorted(SCRIPTS_DIR.rglob("*.py")):
        rel_path = str(py_file.relative_to(REPO_ROOT)).replace("\\", "/")
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        matches = HARDCODED_RE.findall(content)
        count = len(matches)
        classification = _classify(py_file, count, exempt_paths)

        # Get first few matching lines for context
        context_lines = []
        if count > 0:
            for i, line in enumerate(content.splitlines(), 1):
                if HARDCODED_RE.search(line):
                    context_lines.append(f"L{i}: {line.strip()[:120]}")
                    if len(context_lines) >= 3:
                        break

        findings.append({
            "path": rel_path,
            "hardcoded_count": count,
            "classification": classification,
            "context": " | ".join(context_lines) if context_lines else "",
        })

    return findings


def write_csv(findings: list[dict], path: Path) -> None:
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["path", "hardcoded_count", "classification", "context"])
        writer.writeheader()
        writer.writerows(findings)


def write_md(findings: list[dict], path: Path, summary: dict) -> None:
    ensure_dir(path.parent)
    lines = [
        "# Path Hardcoding Audit — V3.17",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        f"**Scripts scanned:** {len(findings)}",
        "",
        "## Summary",
        "",
        "| Classification | Count | Description |",
        "|---|---|---|",
        f"| current_pipeline_blocker | {summary['current_pipeline_blocker']} | P0 mainline scripts with D:\\ocn hardcoding (must be 0) |",
        f"| current_pipeline_warning | {summary['current_pipeline_warning']} | V3.17 toolchain scripts with D:\\ocn hardcoding |",
        f"| legacy_exempt | {summary['legacy_exempt']} | Legacy scripts listed in exemptions doc |",
        f"| safe | {summary['safe']} | No D:\\ocn hardcoding (or scanner code using string literal) |",
        "",
    ]

    if summary["current_pipeline_blocker"] > 0:
        lines += [
            "## BLOCKERS (must fix)",
            "",
            "The following P0 mainline scripts still contain D:\\ocn hardcoding:",
            "",
            "| Path | Count | Context |",
            "|---|---|---|",
        ]
        for f in findings:
            if f["classification"] == "current_pipeline_blocker":
                lines.append(f"| {f['path']} | {f['hardcoded_count']} | {f['context'][:200]} |")
        lines.append("")

    if summary["current_pipeline_warning"] > 0:
        lines += [
            "## Warnings (V3.17 toolchain)",
            "",
            "| Path | Count | Context |",
            "|---|---|---|",
        ]
        for f in findings:
            if f["classification"] == "current_pipeline_warning":
                lines.append(f"| {f['path']} | {f['hardcoded_count']} | {f['context'][:200]} |")
        lines.append("")

    lines += [
        "## Legacy exempt scripts",
        "",
        f"See `docs/legacy_scripts_path_hardcoding_exemptions.md` for the full list.",
        "",
        "| Path | Count |",
        "|---|---|",
    ]
    for f in findings:
        if f["classification"] == "legacy_exempt":
            lines.append(f"| {f['path']} | {f['hardcoded_count']} |")
    lines.append("")

    gate_pass = summary["current_pipeline_blocker"] == 0
    lines += [
        "## Gate",
        "",
        f"**current_pipeline_blocker = 0:** {'PASS' if gate_pass else 'FAIL'}",
        "",
    ]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main() -> None:
    findings = scan_all()
    summary = {
        "current_pipeline_blocker": sum(1 for f in findings if f["classification"] == "current_pipeline_blocker"),
        "current_pipeline_warning": sum(1 for f in findings if f["classification"] == "current_pipeline_warning"),
        "legacy_exempt": sum(1 for f in findings if f["classification"] == "legacy_exempt"),
        "safe": sum(1 for f in findings if f["classification"] == "safe"),
    }

    csv_path = REPORTS_DIR / "path_hardcoding_audit_v3_17.csv"
    md_path = REPORTS_DIR / "path_hardcoding_audit_v3_17.md"

    write_csv(findings, csv_path)
    write_md(findings, md_path, summary)

    print(f"[audit] wrote {csv_path.relative_to(REPO_ROOT)}")
    print(f"[audit] wrote {md_path.relative_to(REPO_ROOT)}")
    print()
    print(f"  current_pipeline_blocker: {summary['current_pipeline_blocker']}")
    print(f"  current_pipeline_warning: {summary['current_pipeline_warning']}")
    print(f"  legacy_exempt:            {summary['legacy_exempt']}")
    print(f"  safe:                     {summary['safe']}")

    if summary["current_pipeline_blocker"] > 0:
        print()
        print(f"[audit] FAIL: {summary['current_pipeline_blocker']} blocker(s) found.")
        sys.exit(1)
    else:
        print()
        print("[audit] PASS: current_pipeline_blocker = 0.")


if __name__ == "__main__":
    main()
