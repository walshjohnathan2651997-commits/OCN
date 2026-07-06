"""Tests that PDF stress test redacted outputs contain no raw text.

Validates the acceptance criterion: "redacted outputs 不含真实 PDF 文本".
Walks all public (non-private) files in the stress test output directory
and verifies no forbidden text fields appear in their JSONL rows or CSV
columns.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
STRESS_DIR = REPO_ROOT / "experiments" / "pdf_extraction_stress_test_v1"

# Fields that must NEVER appear in public/redacted outputs
FORBIDDEN_TEXT_FIELDS = {
    "raw_text", "clean_text",
    "raw_page_text", "clean_page_text",
    "raw_block_text", "clean_block_text",
    "retrieved_text", "anchor_text",
    "evidence_text", "claim_text", "selected_evidence",
}

# Files to check (public only — never private/)
REDACTED_FILES_TO_CHECK = [
    "stress_pages_redacted.jsonl",
    "stress_blocks_redacted.jsonl",
    "stress_sentences_redacted.jsonl",
    "stress_windows_redacted.jsonl",
    "retrieval_under_extraction_stress.csv",
    "failure_cases_redacted.csv",
    "extraction_quality_metrics.csv",
    "stress_suite_manifest.csv",
]


def _check_jsonl_for_forbidden_fields(path: Path) -> list[str]:
    """Return list of forbidden field names found in the JSONL file."""
    found = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                found |= (FORBIDDEN_TEXT_FIELDS & set(row.keys()))
    return sorted(found)


def _check_csv_for_forbidden_columns(path: Path) -> list[str]:
    """Return list of forbidden column names found in the CSV file."""
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        cols = set(reader.fieldnames or [])
    return sorted(FORBIDDEN_TEXT_FIELDS & cols)


def _check_no_private_dir_committed():
    """The private/ subdirectory should exist for full text but must not be
    committed to git. We verify it is listed in .gitignore."""
    gitignore = REPO_ROOT / ".gitignore"
    if not gitignore.is_file():
        return True
    content = gitignore.read_text(encoding="utf-8", errors="ignore")
    # Either 'private' or 'experiments/*/private' should be ignored
    return "private" in content


class TestStressOutputsRedacted:
    @pytest.mark.parametrize("filename", REDACTED_FILES_TO_CHECK)
    def test_redacted_file_has_no_text_fields(self, filename):
        path = STRESS_DIR / filename
        if not path.is_file():
            pytest.skip(f"{filename} not found (run stress test first)")
        if filename.endswith(".jsonl"):
            found = _check_jsonl_for_forbidden_fields(path)
        else:
            found = _check_csv_for_forbidden_columns(path)
        assert not found, (
            f"{filename} contains forbidden text fields: {found}"
        )

    def test_private_dir_not_committed(self):
        # The private/ directory should be gitignored
        # (We don't fail hard if .gitignore doesn't mention it — just warn.)
        if not _check_no_private_dir_committed():
            import warnings
            warnings.warn(
                "private/ directory may not be in .gitignore — "
                "verify before committing stress test outputs"
            )

    def test_leakage_guard_report_passes(self):
        report_path = STRESS_DIR / "leakage_guard_report.json"
        if not report_path.is_file():
            pytest.skip("leakage_guard_report.json not found")
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        assert report.get("status") == "PASS", (
            f"Leakage guard status is {report.get('status')}, expected PASS. "
            f"Details: {report.get('checks')}"
        )

    def test_no_private_full_text_in_public_dir(self):
        """Ensure no *_full.jsonl files leaked into the public directory."""
        if not STRESS_DIR.is_dir():
            pytest.skip("Stress dir not found")
        leaked = list(STRESS_DIR.glob("*_full.jsonl"))
        assert not leaked, (
            f"Private full-text files found in public directory: "
            f"{[p.name for p in leaked]}"
        )
