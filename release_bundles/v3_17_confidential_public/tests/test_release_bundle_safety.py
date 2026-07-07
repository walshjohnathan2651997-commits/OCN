"""Tests that the public release bundle is safe to publish.

Task Pack G Step 4 — verifies the release bundle:
  - has no PDF files
  - has no private text columns (claim_text, evidence_text, etc.)
  - carries a REDACTION_REPORT certifying safety
  - has MANIFEST.json
  - includes the current mainline lock (CURRENT_MAINLINE.md)
  - redteam scan reports high_risk_count == 0
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
BUNDLE_DIR = REPO_ROOT / "release_bundles" / "v3_17_confidential_public"

FORBIDDEN_TEXT_FIELDS = {
    "claim_text",
    "evidence_text",
    "selected_evidence",
    "raw_text",
    "clean_text",
}

FORBIDDEN_BINARY_SUFFIXES = {".pdf", ".docx", ".xlsx", ".npz", ".pkl", ".joblib"}


def _is_private_dir(path: Path) -> bool:
    for part in path.parts:
        plower = part.lower()
        if plower in ("private", ".git", "__pycache__"):
            return True
        if plower.startswith("private_") or plower.endswith("_private"):
            return True
    return False


def _is_toy_path(path: Path) -> bool:
    """Match the redteam scanner's toy-path detection.

    Toy/synthetic data is allowed in the public bundle and legitimately
    uses synthetic claim_text/evidence_text fields.
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


def _bundle_files(suffixes=None) -> list[Path]:
    if not BUNDLE_DIR.exists():
        return []
    out: list[Path] = []
    for p in BUNDLE_DIR.rglob("*"):
        if not p.is_file():
            continue
        if _is_private_dir(p):
            continue
        if suffixes is not None and p.suffix.lower() not in suffixes:
            continue
        out.append(p)
    return sorted(set(out))


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(BUNDLE_DIR)).replace("\\", "/")
    except ValueError:
        return str(path)


@pytest.fixture(scope="module")
def bundle_exists():
    if not BUNDLE_DIR.exists():
        pytest.skip(
            "Release bundle has not been built yet — run "
            "'python scripts/build_public_sanitized_release_v1.py' first"
        )


class TestReleaseBundleStructure:
    def test_bundle_has_manifest(self, bundle_exists):
        assert (BUNDLE_DIR / "MANIFEST.json").exists(), (
            "MANIFEST.json missing from release bundle"
        )

    def test_bundle_has_redaction_report(self, bundle_exists):
        assert (BUNDLE_DIR / "REDACTION_REPORT.json").exists(), (
            "REDACTION_REPORT.json missing from release bundle"
        )

    def test_bundle_has_current_mainline(self, bundle_exists):
        assert (BUNDLE_DIR / "CURRENT_MAINLINE.md").exists(), (
            "CURRENT_MAINLINE.md missing from release bundle"
        )

    def test_bundle_has_readme(self, bundle_exists):
        assert (BUNDLE_DIR / "README.md").exists(), (
            "README.md missing from release bundle"
        )


class TestReleaseBundleNoPdf:
    def test_no_pdf_files(self, bundle_exists):
        pdfs = [p for p in _bundle_files() if p.suffix.lower() == ".pdf"]
        assert not pdfs, (
            "Release bundle contains PDF files: "
            + ", ".join(_rel(p) for p in pdfs)
        )

    def test_no_forbidden_binary_files(self, bundle_exists):
        offenders = [
            p for p in _bundle_files()
            if p.suffix.lower() in FORBIDDEN_BINARY_SUFFIXES
        ]
        assert not offenders, (
            "Release bundle contains forbidden binary types: "
            + ", ".join(f"{_rel(p)} ({p.suffix})" for p in offenders)
        )


class TestReleaseBundleNoPrivateText:
    def test_no_forbidden_text_columns_in_csv(self, bundle_exists):
        csv_files = _bundle_files({".csv", ".tsv"})
        violations = []
        for path in csv_files:
            if _is_toy_path(path):
                continue
            try:
                df = pd.read_csv(path, keep_default_na=False, nrows=1)
            except Exception:
                continue
            cols = {str(c) for c in df.columns}
            hits = FORBIDDEN_TEXT_FIELDS & cols
            if hits:
                violations.append(f"{_rel(path)}: {sorted(hits)}")
        assert not violations, (
            "Release bundle CSVs contain forbidden text columns:\n  " +
            "\n  ".join(violations)
        )

    def test_no_forbidden_text_keys_in_json(self, bundle_exists):
        json_files = _bundle_files({".json", ".jsonl"})
        violations = []
        for path in json_files:
            if _is_toy_path(path):
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    if path.suffix.lower() == ".jsonl":
                        first = f.readline()
                        obj = json.loads(first) if first.strip() else {}
                    else:
                        obj = json.load(f)
            except Exception:
                continue
            if isinstance(obj, dict):
                hits = FORBIDDEN_TEXT_FIELDS & set(obj.keys())
                if hits:
                    violations.append(
                        f"{_rel(path)}: top-level keys {sorted(hits)}"
                    )
                records = obj.get("records") or obj.get("data") or obj.get("rows")
                if isinstance(records, list) and records and isinstance(records[0], dict):
                    nested_hits = FORBIDDEN_TEXT_FIELDS & set(records[0].keys())
                    if nested_hits:
                        violations.append(
                            f"{_rel(path)}: records keys {sorted(nested_hits)}"
                        )
            elif isinstance(obj, list) and obj and isinstance(obj[0], dict):
                hits = FORBIDDEN_TEXT_FIELDS & set(obj[0].keys())
                if hits:
                    violations.append(
                        f"{_rel(path)}: list-of-records keys {sorted(hits)}"
                    )
        assert not violations, (
            "Release bundle JSON files contain forbidden text fields:\n  " +
            "\n  ".join(violations)
        )


class TestReleaseBundleRedactionReport:
    def test_redaction_report_certifies_no_raw_text(self, bundle_exists):
        with open(
            BUNDLE_DIR / "REDACTION_REPORT.json", "r", encoding="utf-8"
        ) as f:
            report = json.load(f)
        assert report.get("contains_raw_evidence_text") is False
        assert report.get("contains_real_claim_text") is False
        assert report.get("contains_real_pdf") is False

    def test_redaction_report_redteam_pass(self, bundle_exists):
        with open(
            BUNDLE_DIR / "REDACTION_REPORT.json", "r", encoding="utf-8"
        ) as f:
            report = json.load(f)
        assert report.get("redteam_pass") is True
        summary = report.get("redteam_summary", {})
        assert summary.get("high_risk_count", 1) == 0, (
            f"Release bundle redteam scan found high-risk findings: "
            f"{summary.get('high_risk_count')}"
        )

    def test_redaction_report_guards_enforced(self, bundle_exists):
        with open(
            BUNDLE_DIR / "REDACTION_REPORT.json", "r", encoding="utf-8"
        ) as f:
            report = json.load(f)
        guards = report.get("guards", {})
        assert guards.get("no_api") is True
        assert guards.get("no_network") is True
        assert guards.get("no_training") is True
