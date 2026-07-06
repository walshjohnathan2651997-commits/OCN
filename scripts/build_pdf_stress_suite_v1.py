#!/usr/bin/env python
"""build_pdf_stress_suite_v1.py — Build a synthetic PDF stress suite.

Reads synthetic stress page texts from data/toy_synthetic/pdf_stress_sources.jsonl
and prepares a stress suite manifest + per-doc page-text files for downstream
extraction stress testing. This script does NOT run extraction — it only prepares
inputs so that the stress test runner can exercise the cleaning pipeline against
known stress types.

Hard boundaries:
  - no network, no API, no cloud, no OCR, no training
  - synthetic inputs only (no private PDFs ingested)
  - outputs are redacted: only hashes, counts, and stress_type metadata

Usage:
  python scripts/build_pdf_stress_suite_v1.py \
      --sources data/toy_synthetic/pdf_stress_sources.jsonl \
      --output_dir experiments/pdf_extraction_stress_test_v1
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


STRESS_TYPES = [
    "normal_single_column",
    "two_column_like",
    "header_footer_noise",
    "page_number_noise",
    "hyphenation_noise",
    "long_paragraph",
    "table_like_text",
    "caption_like_text",
    "reference_heavy",
    "empty_page",
    "corrupted_text",
    "scanned_placeholder_detect_only",
]


def sha256_text(text: str) -> str:
    if text is None:
        text = ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_run_config(output_dir: Path, config: dict, script_name: str, extra: dict | None = None):
    """Write run_config.json capturing the script configuration."""
    rc = {
        "script": script_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config": config,
        "no_api": True,
        "no_network": True,
        "no_training": True,
        "no_ocr_by_default": True,
    }
    if extra:
        rc.update(extra)
    path = output_dir / "run_config.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rc, f, indent=2, ensure_ascii=False)
    return path


def load_sources(sources_path: Path) -> list[dict]:
    """Load synthetic stress sources from JSONL."""
    records = []
    with open(sources_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            records.append(rec)
    return records


def validate_records(records: list[dict]) -> list[str]:
    """Validate that records cover all required stress types and required fields.
    Returns list of warnings (empty if all good)."""
    warnings = []
    required_fields = {"stress_doc_id", "stress_type", "paper_id", "pdf_filename", "page_number", "page_text"}
    seen_types = set()
    for i, rec in enumerate(records):
        missing = required_fields - set(rec.keys())
        if missing:
            warnings.append(f"Record {i} missing fields: {sorted(missing)}")
        st = rec.get("stress_type", "")
        if st not in STRESS_TYPES:
            warnings.append(f"Record {i} has unknown stress_type: {st}")
        seen_types.add(st)
    missing_types = set(STRESS_TYPES) - seen_types
    if missing_types:
        warnings.append(f"Missing stress_type coverage: {sorted(missing_types)}")
    return warnings


def main():
    parser = argparse.ArgumentParser(
        description="Build a synthetic PDF stress suite manifest for extraction stress testing."
    )
    parser.add_argument(
        "--sources",
        default="data/toy_synthetic/pdf_stress_sources.jsonl",
        help="JSONL file with synthetic stress page texts (default: data/toy_synthetic/pdf_stress_sources.jsonl)",
    )
    parser.add_argument(
        "--output_dir",
        default="experiments/pdf_extraction_stress_test_v1",
        help="Output directory (default: experiments/pdf_extraction_stress_test_v1)",
    )
    args = parser.parse_args()

    sources_path = Path(args.sources)
    if not sources_path.is_file():
        print(f"ERROR: sources file not found at {sources_path}", file=sys.stderr)
        raise SystemExit(2)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading stress sources from {sources_path}")
    records = load_sources(sources_path)
    print(f"  Loaded {len(records)} records")

    warnings = validate_records(records)
    for w in warnings:
        print(f"  WARNING: {w}", file=sys.stderr)

    # Build manifest rows (redacted: no page_text in manifest, only hash)
    manifest_rows = []
    for rec in records:
        page_text = rec.get("page_text", "")
        manifest_rows.append({
            "stress_doc_id": rec["stress_doc_id"],
            "stress_type": rec["stress_type"],
            "paper_id": rec["paper_id"],
            "pdf_filename": rec["pdf_filename"],
            "page_number": rec["page_number"],
            "page_text_sha256": sha256_text(page_text),
            "n_chars": len(page_text),
            "n_words": len(page_text.split()) if page_text else 0,
            "scanned_detect_only": rec["stress_type"] == "scanned_placeholder_detect_only",
        })

    # Write stress_suite_manifest.csv
    manifest_path = output_dir / "stress_suite_manifest.csv"
    manifest_fields = [
        "stress_doc_id", "stress_type", "paper_id", "pdf_filename",
        "page_number", "page_text_sha256", "n_chars", "n_words",
        "scanned_detect_only",
    ]
    with open(manifest_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=manifest_fields)
        writer.writeheader()
        for row in manifest_rows:
            writer.writerow(row)
    print(f"Wrote {manifest_path} ({len(manifest_rows)} rows)")

    # Write sources to a private/ subdirectory (full page_text for downstream use)
    private_dir = output_dir / "private"
    private_dir.mkdir(parents=True, exist_ok=True)
    sources_private_path = private_dir / "stress_sources_full.jsonl"
    with open(sources_private_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"Wrote {sources_private_path} (private, full text for downstream extraction)")

    # Write run_config.json
    config = {
        "sources": str(sources_path),
        "output_dir": str(output_dir),
        "n_records": len(records),
        "stress_types_covered": sorted(set(r["stress_type"] for r in records)),
        "validation_warnings": warnings,
    }
    rc_path = write_run_config(
        output_dir, config, "build_pdf_stress_suite_v1.py",
        extra={"purpose": "Prepare synthetic stress inputs for PDF extraction robustness test"},
    )
    print(f"Wrote {rc_path}")

    # Coverage summary
    print(f"\nStress type coverage ({len(set(r['stress_type'] for r in records))}/{len(STRESS_TYPES)}):")
    for st in STRESS_TYPES:
        n = sum(1 for r in records if r["stress_type"] == st)
        marker = "OK" if n > 0 else "MISSING"
        print(f"  [{marker}] {st}: {n} record(s)")

    if warnings:
        print(f"\nCompleted with {len(warnings)} warning(s)", file=sys.stderr)
    else:
        print("\nCompleted with no warnings")


if __name__ == "__main__":
    main()
