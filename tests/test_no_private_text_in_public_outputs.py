"""Tests that public output directories contain no private text fields.

Task Pack G Step 4 — verifies that paper_assets/, release_bundles/, and docs/
do not contain CSV/JSON/JSONL files with the forbidden text columns:
  claim_text, evidence_text, selected_evidence, raw_text, clean_text.

These directories are the public-facing artifacts; if they contain raw
claim/evidence text, that is a confidentiality violation.

Note: paper_assets/ may legitimately contain table markdown that *quotes*
short phrases for analysis (e.g., in a leakage-failure example table).
Those are checked by the redteam scanner with long-text thresholds. This
test targets only structured CSV/JSON/JSONL fields, not prose markdown.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

FORBIDDEN_TEXT_FIELDS = {
    "claim_text",
    "evidence_text",
    "selected_evidence",
    "raw_text",
    "clean_text",
}

# Public-facing directories that must never carry raw text columns.
PUBLIC_DIRS = [
    REPO_ROOT / "paper_assets",
    REPO_ROOT / "release_bundles",
    REPO_ROOT / "docs",
]

# Files in docs/ that are policy/spec prose and may legitimately mention
# the forbidden field *names* (e.g., "do not include claim_text"). We skip
# markdown for the structured-field check; only data files are scanned.
SCANNED_SUFFIXES = {".csv", ".json", ".jsonl", ".tsv"}


def _is_private_dir(path: Path) -> bool:
    parts = path.parts
    for part in parts:
        plower = part.lower()
        if plower in ("private", ".git", "__pycache__", "node_modules"):
            return True
        if plower.startswith("private_") or plower.endswith("_private"):
            return True
    return False


def _is_toy_path(path: Path) -> bool:
    """Match the redteam scanner's toy-path detection.

    Toy/synthetic data legitimately uses synthetic claim_text/evidence_text
    fields — these are not real confidential content and are explicitly
    allowed in public outputs.
    """
    for part in path.parts:
        plower = part.lower()
        if plower == "toy_synthetic":
            return True
        if plower.startswith("toy_") or plower.endswith("_toy"):
            return True
        if plower in ("synthetic", "mock", "fake", "dummy"):
            return True
    return False


def _collect_data_files() -> list[Path]:
    files: list[Path] = []
    for public_dir in PUBLIC_DIRS:
        if not public_dir.exists():
            continue
        for p in public_dir.rglob("*"):
            if not p.is_file():
                continue
            if _is_private_dir(p):
                continue
            if _is_toy_path(p):
                continue
            if p.suffix.lower() not in SCANNED_SUFFIXES:
                continue
            files.append(p)
    return sorted(set(files))


def _check_csv(path: Path) -> list[str]:
    try:
        df = pd.read_csv(path, keep_default_na=False, nrows=1)
    except Exception:
        return []
    cols = {str(c) for c in df.columns}
    return sorted(FORBIDDEN_TEXT_FIELDS & cols)


def _check_json(path: Path) -> list[str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
    except Exception:
        return []
    hits: list[str] = []
    if isinstance(obj, dict):
        for key in obj:
            if key in FORBIDDEN_TEXT_FIELDS:
                hits.append(key)
        # Check common nested structures (records list)
        records = obj.get("records") or obj.get("data") or obj.get("rows")
        if isinstance(records, list) and records and isinstance(records[0], dict):
            for key in records[0]:
                if key in FORBIDDEN_TEXT_FIELDS:
                    hits.append(key)
    elif isinstance(obj, list) and obj and isinstance(obj[0], dict):
        for key in obj[0]:
            if key in FORBIDDEN_TEXT_FIELDS:
                hits.append(key)
    return sorted(set(hits))


def _check_jsonl(path: Path) -> list[str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            first_line = f.readline()
    except Exception:
        return []
    if not first_line.strip():
        return []
    try:
        obj = json.loads(first_line)
    except Exception:
        return []
    if not isinstance(obj, dict):
        return []
    return sorted(FORBIDDEN_TEXT_FIELDS & set(obj.keys()))


def _check_file(path: Path) -> list[str]:
    suffix = path.suffix.lower()
    if suffix == ".csv" or suffix == ".tsv":
        return _check_csv(path)
    if suffix == ".json":
        return _check_json(path)
    if suffix == ".jsonl":
        return _check_jsonl(path)
    return []


def _file_id(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


class TestNoPrivateTextInPublicOutputs:
    def test_public_dirs_have_no_forbidden_text_fields(self):
        files = _collect_data_files()
        assert files, (
            "Expected to scan at least one data file under paper_assets/, "
            "release_bundles/, or docs/"
        )
        violations: list[str] = []
        for path in files:
            hits = _check_file(path)
            if hits:
                violations.append(
                    f"{_file_id(path)}: forbidden columns {hits}"
                )
        assert not violations, (
            "Public outputs contain forbidden text columns:\n  " +
            "\n  ".join(violations)
        )

    def test_release_bundle_redaction_report_passes(self):
        """The release bundle REDACTION_REPORT must certify no raw text."""
        report_path = (
            REPO_ROOT
            / "release_bundles"
            / "v3_17_confidential_public"
            / "REDACTION_REPORT.json"
        )
        if not report_path.exists():
            pytest.skip("Release bundle has not been built yet")
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        assert report.get("contains_raw_evidence_text") is False, (
            "REDACTION_REPORT.json says raw evidence text is present"
        )
        assert report.get("contains_real_claim_text") is False, (
            "REDACTION_REPORT.json says real claim text is present"
        )

    def test_release_bundle_has_no_pdf_files(self):
        bundle_dir = (
            REPO_ROOT / "release_bundles" / "v3_17_confidential_public"
        )
        if not bundle_dir.exists():
            pytest.skip("Release bundle has not been built yet")
        pdfs = list(bundle_dir.rglob("*.pdf"))
        assert not pdfs, (
            "Release bundle must not contain PDF files. Found: "
            + ", ".join(_file_id(p) for p in pdfs)
        )
