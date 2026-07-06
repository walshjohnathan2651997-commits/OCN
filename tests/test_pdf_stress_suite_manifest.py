"""Tests for the PDF stress suite manifest.

Validates that the stress suite manifest exists, has the expected columns,
covers all 12 required stress types, and contains no raw text fields.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
STRESS_DIR = REPO_ROOT / "experiments" / "pdf_extraction_stress_test_v1"
MANIFEST_PATH = STRESS_DIR / "stress_suite_manifest.csv"

REQUIRED_STRESS_TYPES = {
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
}

REQUIRED_COLUMNS = {
    "stress_doc_id",
    "stress_type",
    "paper_id",
    "pdf_filename",
    "page_number",
    "page_text_sha256",
    "n_chars",
    "n_words",
    "scanned_detect_only",
}

FORBIDDEN_TEXT_FIELDS = {
    "raw_text", "clean_text", "page_text",
    "raw_page_text", "clean_page_text",
    "anchor_text", "evidence_text", "claim_text",
}


def _load_manifest():
    if not MANIFEST_PATH.is_file():
        return None, []
    with open(MANIFEST_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames or [], list(reader)


class TestStressSuiteManifest:
    def test_manifest_exists(self):
        assert MANIFEST_PATH.is_file(), f"Manifest not found at {MANIFEST_PATH}"

    def test_manifest_has_required_columns(self):
        cols, _ = _load_manifest()
        assert cols is not None, "Manifest could not be loaded"
        missing = REQUIRED_COLUMNS - set(cols)
        assert not missing, f"Manifest missing required columns: {sorted(missing)}"

    def test_manifest_has_no_forbidden_text_fields(self):
        cols, _ = _load_manifest()
        assert cols is not None
        forbidden_found = FORBIDDEN_TEXT_FIELDS & set(cols)
        assert not forbidden_found, (
            f"Manifest contains forbidden text fields: {sorted(forbidden_found)}"
        )

    def test_manifest_covers_all_stress_types(self):
        _, rows = _load_manifest()
        assert rows, "Manifest has no rows"
        seen_types = {r["stress_type"] for r in rows}
        missing = REQUIRED_STRESS_TYPES - seen_types
        assert not missing, f"Manifest missing stress types: {sorted(missing)}"

    def test_manifest_has_at_least_eight_records(self):
        _, rows = _load_manifest()
        assert len(rows) >= 8, f"Expected >= 8 records, got {len(rows)}"

    def test_each_row_has_hash_not_text(self):
        _, rows = _load_manifest()
        for r in rows:
            assert r.get("page_text_sha256"), (
                f"Row {r.get('stress_doc_id')} missing page_text_sha256"
            )
            # Ensure no column name suggests raw text leaked in
            for col in r:
                assert col not in FORBIDDEN_TEXT_FIELDS, (
                    f"Forbidden column {col} present in manifest"
                )

    def test_scanned_type_marked_detect_only(self):
        _, rows = _load_manifest()
        for r in rows:
            if r["stress_type"] == "scanned_placeholder_detect_only":
                assert r.get("scanned_detect_only") in ("True", "true", "1"), (
                    f"Scanned doc {r['stress_doc_id']} not marked scanned_detect_only"
                )
