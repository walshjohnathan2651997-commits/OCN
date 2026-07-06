#!/usr/bin/env python
"""summarize_pdf_stress_report_v1.py — Generate final stress test summary report.

Reads the outputs from run_pdf_extraction_stress_test_v1.py and
run_pdf_extraction_to_bm25_stress_v1.py and produces:
  - stress_test_summary.md (human-readable summary)
  - leakage_guard_report.json (confidentiality verification)

Hard boundaries:
  - no network, no API, no cloud, no OCR, no training
  - verifies no raw_text/clean_text in public/redacted outputs
  - report explicitly states this is extraction robustness, NOT SOTA

Usage:
  python scripts/summarize_pdf_stress_report_v1.py \
      --stress_dir experiments/pdf_extraction_stress_test_v1
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


FORBIDDEN_TEXT_FIELDS = {
    "raw_text", "clean_text",
    "raw_page_text", "clean_page_text",
    "raw_block_text", "clean_block_text",
    "retrieved_text", "anchor_text",
    "evidence_text", "claim_text", "selected_evidence",
}


def sha256_text(text: str) -> str:
    if text is None:
        text = ""
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_csv(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_redaction(rows: list[dict], filename: str) -> dict:
    """Check that no row contains forbidden text fields."""
    forbidden_found = []
    for i, row in enumerate(rows):
        for field in FORBIDDEN_TEXT_FIELDS:
            if field in row:
                forbidden_found.append({"row": i, "field": field, "file": filename})
    return {
        "file": filename,
        "n_rows": len(rows),
        "forbidden_fields_found": forbidden_found,
        "passed": len(forbidden_found) == 0,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate PDF extraction stress test summary report."
    )
    parser.add_argument(
        "--stress_dir",
        default="experiments/pdf_extraction_stress_test_v1",
        help="Directory containing stress test outputs",
    )
    args = parser.parse_args()

    stress_dir = Path(args.stress_dir)
    if not stress_dir.is_dir():
        print(f"ERROR: stress_dir not found: {stress_dir}", file=sys.stderr)
        raise SystemExit(2)

    # --- Load all outputs ---
    manifest = load_csv(stress_dir / "stress_suite_manifest.csv")
    metrics = load_csv(stress_dir / "extraction_quality_metrics.csv")
    retrieval_rows = load_csv(stress_dir / "retrieval_under_extraction_stress.csv")
    retrieval_summary = load_json(stress_dir / "retrieval_stress_summary.json")
    failure_cases = load_csv(stress_dir / "failure_cases_redacted.csv")

    pages_redacted = load_jsonl(stress_dir / "stress_pages_redacted.jsonl")
    blocks_redacted = load_jsonl(stress_dir / "stress_blocks_redacted.jsonl")
    sentences_redacted = load_jsonl(stress_dir / "stress_sentences_redacted.jsonl")
    windows_redacted = load_jsonl(stress_dir / "stress_windows_redacted.jsonl")

    # --- Leakage guard: verify redacted outputs ---
    leakage_checks = [
        check_redaction(pages_redacted, "stress_pages_redacted.jsonl"),
        check_redaction(blocks_redacted, "stress_blocks_redacted.jsonl"),
        check_redaction(sentences_redacted, "stress_sentences_redacted.jsonl"),
        check_redaction(windows_redacted, "stress_windows_redacted.jsonl"),
        check_redaction(retrieval_rows, "retrieval_under_extraction_stress.csv"),
        check_redaction(failure_cases, "failure_cases_redacted.csv"),
    ]
    all_passed = all(c["passed"] for c in leakage_checks)
    leakage_report = {
        "status": "PASS" if all_passed else "FAIL",
        "checks": leakage_checks,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "policy": "Public/redacted outputs must not contain raw_text, clean_text, raw_page_text, clean_page_text, raw_block_text, clean_block_text, retrieved_text, anchor_text, evidence_text, claim_text, or selected_evidence fields.",
    }
    leakage_path = stress_dir / "leakage_guard_report.json"
    with open(leakage_path, "w", encoding="utf-8") as f:
        json.dump(leakage_report, f, indent=2, ensure_ascii=False)
    print(f"Wrote {leakage_path} (status={leakage_report['status']})")

    # --- Generate stress_test_summary.md ---
    n_docs = len(metrics)
    n_failures = len(failure_cases)
    n_empty_status = sum(1 for m in metrics if m.get("extraction_status") == "empty")
    n_scanned = sum(1 for m in metrics if m.get("extraction_status") == "scanned_detect_only")
    n_corrupted = sum(1 for m in metrics if m.get("extraction_status") == "corrupted_cleaned")
    n_ok = sum(1 for m in metrics if m.get("extraction_status") == "ok")

    # Per-stress-type summary
    by_type = {}
    for m in metrics:
        st = m.get("stress_type", "unknown")
        if st not in by_type:
            by_type[st] = {"n": 0, "n_sentences": 0, "n_blocks": 0, "empty_page_rate": 0.0}
        by_type[st]["n"] += 1
        by_type[st]["n_sentences"] += int(m.get("n_sentences", 0) or 0)
        by_type[st]["n_blocks"] += int(m.get("n_blocks", 0) or 0)
        try:
            by_type[st]["empty_page_rate"] += float(m.get("empty_page_rate", 0) or 0)
        except ValueError:
            pass

    # Retrieval summary by type
    retrieval_by_type = retrieval_summary.get("by_stress_type", {}) if retrieval_summary else {}

    summary_lines = []
    summary_lines.append("# PDF Extraction Stress Test Summary")
    summary_lines.append("")
    summary_lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    summary_lines.append("")
    summary_lines.append("> **This is an extraction robustness test, NOT a SOTA claim.**")
    summary_lines.append("> The purpose is to verify engineering reliability of the PDF")
    summary_lines.append("> extraction pipeline against common stress types. Results here")
    summary_lines.append("> must not be cited as benchmark performance.")
    summary_lines.append("")
    summary_lines.append("## 1. Scope and Boundaries")
    summary_lines.append("")
    summary_lines.append("- **No OCR by default**: scanned PDFs are detected and reported only.")
    summary_lines.append("- **No network, no API, no cloud, no training**.")
    summary_lines.append("- **Synthetic inputs only**: stress suite uses synthetic page texts,")
    summary_lines.append("  not private PDFs. No private PDF text enters public/redacted outputs.")
    summary_lines.append("- **Private mode**: public outputs are hash-only. Full text lives in")
    summary_lines.append("  `private/` subdirectory and must NOT be committed or released.")
    summary_lines.append("- **Anchor text usage**: anchor text is used for evaluation only,")
    summary_lines.append("  never for ranking. Public outputs keep only `anchor_text_sha256`.")
    summary_lines.append("")
    summary_lines.append("## 2. Stress Suite Coverage")
    summary_lines.append("")
    summary_lines.append(f"- Total stress docs: **{n_docs}**")
    summary_lines.append(f"- Stress types covered: **{len(by_type)}**")
    summary_lines.append("")
    summary_lines.append("| Stress Type | N | N Blocks | N Sentences |")
    summary_lines.append("|---|---|---|---|")
    for st in sorted(by_type.keys()):
        v = by_type[st]
        summary_lines.append(f"| {st} | {v['n']} | {v['n_blocks']} | {v['n_sentences']} |")
    summary_lines.append("")
    summary_lines.append("## 3. Extraction Quality")
    summary_lines.append("")
    summary_lines.append(f"- OK: **{n_ok}**")
    summary_lines.append(f"- Empty page: **{n_empty_status}**")
    summary_lines.append(f"- Scanned (detect only): **{n_scanned}**")
    summary_lines.append(f"- Corrupted (NUL cleaned): **{n_corrupted}**")
    summary_lines.append(f"- Failed: **{n_failures}**")
    summary_lines.append("")
    summary_lines.append("## 4. Retrieval Under Stress (Aggregate)")
    summary_lines.append("")
    if retrieval_summary:
        summary_lines.append(f"- N queries: **{retrieval_summary.get('n_queries', 0)}**")
        summary_lines.append(f"- Sentence Recall@1: **{retrieval_summary.get('sentence_recall1', 0)}**")
        summary_lines.append(f"- Sentence Recall@5: **{retrieval_summary.get('sentence_recall5', 0)}**")
        summary_lines.append(f"- Sentence Recall@10: **{retrieval_summary.get('sentence_recall10', 0)}**")
        summary_lines.append(f"- Sentence MRR: **{retrieval_summary.get('sentence_mrr', 0)}**")
        summary_lines.append(f"- Window Recall@1: **{retrieval_summary.get('window_recall1', 0)}**")
        summary_lines.append(f"- Window Recall@5: **{retrieval_summary.get('window_recall5', 0)}**")
        summary_lines.append(f"- Window Recall@10: **{retrieval_summary.get('window_recall10', 0)}**")
        summary_lines.append(f"- Window MRR: **{retrieval_summary.get('window_mrr', 0)}**")
    else:
        summary_lines.append("- (retrieval_stress_summary.json not found)")
    summary_lines.append("")
    summary_lines.append("### By Stress Type")
    summary_lines.append("")
    summary_lines.append("| Stress Type | N | Sent R@1 | Sent R@5 | Sent MRR | Win R@1 | Win R@5 | Win MRR |")
    summary_lines.append("|---|---|---|---|---|---|---|---|")
    for st in sorted(retrieval_by_type.keys()):
        v = retrieval_by_type[st]
        summary_lines.append(
            f"| {st} | {v.get('n', 0)} | {v.get('sentence_recall1', 0)} | "
            f"{v.get('sentence_recall5', 0)} | {v.get('sentence_mrr', 0)} | "
            f"{v.get('window_recall1', 0)} | {v.get('window_recall5', 0)} | "
            f"{v.get('window_mrr', 0)} |"
        )
    summary_lines.append("")
    summary_lines.append("## 5. Confidentiality / Leakage Guard")
    summary_lines.append("")
    summary_lines.append(f"- Status: **{leakage_report['status']}**")
    summary_lines.append(f"- Files checked: **{len(leakage_checks)}**")
    for c in leakage_checks:
        marker = "PASS" if c["passed"] else "FAIL"
        summary_lines.append(f"  - [{marker}] {c['file']} ({c['n_rows']} rows)")
    summary_lines.append("")
    summary_lines.append("## 6. How Not to Overclaim")
    summary_lines.append("")
    summary_lines.append("- These results are from **synthetic** stress texts, not real PDFs.")
    summary_lines.append("- The stress suite validates that the extraction pipeline handles")
    summary_lines.append("  common noise types; it does NOT validate retrieval accuracy on")
    summary_lines.append("  real scientific claims.")
    summary_lines.append("- Anchor texts are synthetic and derived from the same source page")
    summary_lines.append("  as the extraction target — recall is therefore optimistic and")
    summary_lines.append("  should not be compared to real-corpus BM25 baselines.")
    summary_lines.append("- No human audit, no gold labels, no SOTA claim.")
    summary_lines.append("- Scanned PDFs are NOT OCR'd. Detection-only results indicate the")
    summary_lines.append("  pipeline correctly identifies them as non-extractable, not that")
    summary_lines.append("  OCR was performed.")
    summary_lines.append("")

    summary_path = stress_dir / "stress_test_summary.md"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines))
    print(f"Wrote {summary_path}")

    print(f"\nDone. Leakage guard: {leakage_report['status']}. Summary at {summary_path}")


if __name__ == "__main__":
    main()
