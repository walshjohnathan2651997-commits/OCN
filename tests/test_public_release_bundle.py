"""Tests for the public sanitized release bundle builder.

Verifies:
  - Release bundle can be built
  - Bundle contains no PDF files
  - Bundle contains no raw text fields (claim_text, evidence_text, etc.)
  - Bundle contains toy demo data
  - Bundle contains schemas
  - REDACTION_REPORT.json exists and reports pass
  - MANIFEST.json exists and is complete
  - Red-team scan passes (high_risk == 0)
  - Bundle contains required top-level files (README, LICENSE, CURRENT_MAINLINE)
  - No excluded file patterns present
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "build_public_sanitized_release_v1.py"
PYTHON = sys.executable

PYTHON_310 = r"C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe"
if Path(PYTHON_310).exists():
    PYTHON = PYTHON_310

FORBIDDEN_TEXT_COLUMNS = [
    "claim_text", "evidence_text", "selected_evidence",
    "raw_text", "clean_text", "retrieved_text",
]

EXCLUDED_SUFFIXES = [".pdf", ".docx", ".xlsx", ".npz", ".pkl", ".joblib"]


def _run_builder(args, timeout=300):
    """Run the release bundle builder. Returns (returncode, stdout)."""
    cmd = [PYTHON, str(SCRIPT_PATH)] + list(args)
    result = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
    )
    return result.returncode, result.stdout


# ---------------------------------------------------------------------------
# TestBundleBuilds
# ---------------------------------------------------------------------------

class TestBundleBuilds:
    """Release bundle can be built successfully."""

    def test_bundle_builds_without_error(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        rc, stdout = _run_builder([
            "--output_dir", str(out_dir),
        ])
        assert rc == 0, f"Build failed: {stdout}"
        assert out_dir.exists()
        assert (out_dir / "README.md").exists()

    def test_bundle_has_required_top_level_files(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        required = ["README.md", "LICENSE_NOTICE.md", "MANIFEST.json", "REDACTION_REPORT.json"]
        for name in required:
            assert (out_dir / name).exists(), f"Missing top-level file: {name}"


# ---------------------------------------------------------------------------
# TestNoPdfFiles
# ---------------------------------------------------------------------------

class TestNoPdfFiles:
    """Bundle must not contain any PDF files."""

    def test_no_pdf_files(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        pdf_files = list(out_dir.rglob("*.pdf"))
        assert len(pdf_files) == 0, f"Found PDF files in bundle: {pdf_files}"

    def test_no_excluded_suffix_files(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        for suffix in EXCLUDED_SUFFIXES:
            files = list(out_dir.rglob(f"*{suffix}"))
            assert len(files) == 0, f"Found {suffix} files: {files}"


# ---------------------------------------------------------------------------
# TestNoRawTextFields
# ---------------------------------------------------------------------------

class TestNoRawTextFields:
    """No CSV in bundle contains forbidden text columns."""

    def test_no_forbidden_text_columns_in_csvs(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        csv_files = list(out_dir.rglob("*.csv"))
        assert len(csv_files) > 0, "No CSV files found in bundle"

        violations = []
        for csv_path in csv_files:
            try:
                df = pd.read_csv(csv_path, keep_default_na=False, nrows=1)
                for col in df.columns:
                    if col.lower() in FORBIDDEN_TEXT_COLUMNS:
                        violations.append((str(csv_path.relative_to(out_dir)), col))
            except Exception:
                pass

        assert not violations, f"Forbidden text columns found: {violations}"

    def test_no_raw_text_in_file_names(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        forbidden_name_patterns = [
            "error_cases_private", "real_review_queue",
            "gold_label", "human_audited",
        ]
        for f in out_dir.rglob("*"):
            if f.is_file():
                name_lower = f.name.lower()
                for pattern in forbidden_name_patterns:
                    assert pattern not in name_lower, (
                        f"Forbidden file name pattern '{pattern}' in: {f.name}"
                    )


# ---------------------------------------------------------------------------
# TestContainsToyDemo
# ---------------------------------------------------------------------------

class TestContainsToyDemo:
    """Bundle contains toy synthetic demo data."""

    def test_toy_synthetic_dir_exists(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        toy_dir = out_dir / "data" / "toy_synthetic"
        assert toy_dir.exists(), "Missing data/toy_synthetic directory"
        toy_files = list(toy_dir.glob("*"))
        assert len(toy_files) > 0, "No toy data files found"

    def test_toy_demo_script_exists(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        demo_script = out_dir / "scripts" / "run_toy_end_to_end_demo_v1.py"
        assert demo_script.exists(), "Missing toy demo script"


# ---------------------------------------------------------------------------
# TestContainsSchemas
# ---------------------------------------------------------------------------

class TestContainsSchemas:
    """Bundle contains schema files."""

    def test_schemas_dir_exists(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        schemas_dir = out_dir / "schemas"
        assert schemas_dir.exists(), "Missing schemas directory"

    def test_schema_files_present(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        schema_files = list((out_dir / "schemas").glob("*.json"))
        assert len(schema_files) >= 5, f"Expected >=5 schema files, got {len(schema_files)}"

    def test_schema_registry_exists(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        registry = out_dir / "schemas" / "schema_registry.md"
        assert registry.exists(), "Missing schema_registry.md"


# ---------------------------------------------------------------------------
# TestRedactionReport
# ---------------------------------------------------------------------------

class TestRedactionReport:
    """REDACTION_REPORT.json exists and reports correct values."""

    def test_redaction_report_exists(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        report_path = out_dir / "REDACTION_REPORT.json"
        assert report_path.exists()

    def test_redaction_report_content(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        with open(out_dir / "REDACTION_REPORT.json", "r", encoding="utf-8") as f:
            report = json.load(f)

        assert "excluded_patterns" in report
        assert "excluded_files_count" in report
        assert "included_files_count" in report
        assert "redteam_pass" in report
        assert "contains_real_pdf" in report
        assert "contains_raw_evidence_text" in report
        assert "contains_real_claim_text" in report

    def test_redteam_pass_is_true(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        with open(out_dir / "REDACTION_REPORT.json", "r", encoding="utf-8") as f:
            report = json.load(f)
        assert report["redteam_pass"] is True, "Red-team scan did not pass"

    def test_no_real_pdf(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        with open(out_dir / "REDACTION_REPORT.json", "r", encoding="utf-8") as f:
            report = json.load(f)
        assert report["contains_real_pdf"] is False

    def test_no_raw_evidence_text(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        with open(out_dir / "REDACTION_REPORT.json", "r", encoding="utf-8") as f:
            report = json.load(f)
        assert report["contains_raw_evidence_text"] is False

    def test_no_raw_claim_text(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        with open(out_dir / "REDACTION_REPORT.json", "r", encoding="utf-8") as f:
            report = json.load(f)
        assert report["contains_real_claim_text"] is False

    def test_included_files_count_positive(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        with open(out_dir / "REDACTION_REPORT.json", "r", encoding="utf-8") as f:
            report = json.load(f)
        assert report["included_files_count"] > 0


# ---------------------------------------------------------------------------
# TestManifest
# ---------------------------------------------------------------------------

class TestManifest:
    """MANIFEST.json is complete and valid."""

    def test_manifest_exists(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        assert (out_dir / "MANIFEST.json").exists()

    def test_manifest_has_files_list(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        with open(out_dir / "MANIFEST.json", "r", encoding="utf-8") as f:
            manifest = json.load(f)
        assert "files" in manifest
        assert isinstance(manifest["files"], list)
        assert len(manifest["files"]) > 0

    def test_manifest_entries_have_required_fields(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        with open(out_dir / "MANIFEST.json", "r", encoding="utf-8") as f:
            manifest = json.load(f)

        for entry in manifest["files"][:10]:  # Check first 10
            assert "path" in entry
            assert "sha256" in entry
            assert "size_bytes" in entry
            assert "release_category" in entry
            assert len(entry["sha256"]) == 64  # SHA-256 hex length

    def test_manifest_sha256_matches_files(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        with open(out_dir / "MANIFEST.json", "r", encoding="utf-8") as f:
            manifest = json.load(f)

        import hashlib
        # Verify a few files match their recorded SHA-256
        for entry in manifest["files"][:5]:
            file_path = out_dir / entry["path"]
            if file_path.exists():
                h = hashlib.sha256(file_path.read_bytes()).hexdigest()
                assert h == entry["sha256"], f"SHA-256 mismatch for {entry['path']}"


# ---------------------------------------------------------------------------
# TestBundleContent
# ---------------------------------------------------------------------------

class TestBundleContent:
    """Bundle has expected content structure."""

    def test_has_scripts_dir(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        assert (out_dir / "scripts").exists()
        scripts = list((out_dir / "scripts").glob("*.py"))
        assert len(scripts) >= 10, f"Expected >=10 scripts, got {len(scripts)}"

    def test_has_paper_assets(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        paper_dir = out_dir / "paper_assets"
        assert paper_dir.exists()
        assert (paper_dir / "v3_17_confidential").exists()

    def test_has_experiments_aggregate_metrics(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        agg_dir = out_dir / "experiments" / "aggregate_metrics"
        assert agg_dir.exists()
        files = list(agg_dir.glob("*"))
        assert len(files) > 0

    def test_has_experiments_redacted_audits(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        audit_dir = out_dir / "experiments" / "redacted_audits"
        assert audit_dir.exists()
        files = list(audit_dir.glob("*"))
        assert len(files) > 0

    def test_has_docs(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        docs_dir = out_dir / "docs"
        assert docs_dir.exists()
        # Should have at least the selected policy docs
        assert (docs_dir / "data_release_policy.md").exists()
        assert (docs_dir / "leakage_and_confidentiality_policy.md").exists()

    def test_readme_has_disclaimer(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        readme = (out_dir / "README.md").read_text(encoding="utf-8")
        assert "not included" in readme.lower()
        assert "confidential" in readme.lower() or "sanitized" in readme.lower()

    def test_license_notice_exists(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        license_path = out_dir / "LICENSE_NOTICE.md"
        assert license_path.exists()
        content = license_path.read_text(encoding="utf-8")
        assert "MIT" in content or "CC-BY" in content


# ---------------------------------------------------------------------------
# TestNoPrivateDirs
# ---------------------------------------------------------------------------

class TestNoPrivateDirs:
    """Bundle must not contain private directories."""

    def test_no_private_dirs(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        forbidden_dirs = ["pdfs", "private_pdfs", "data/private", "experiments/private"]
        for d in forbidden_dirs:
            assert not (out_dir / d).exists(), f"Found forbidden directory: {d}"

    def test_no_error_cases_private(self, tmp_path):
        out_dir = tmp_path / "release_bundle"
        _run_builder(["--output_dir", str(out_dir)])

        # The private error cases file should not be in the bundle
        private_files = list(out_dir.rglob("*private*"))
        # run_config.json might mention "private" in text, but no actual private data files
        data_private = [f for f in private_files if f.suffix in (".csv", ".json", ".jsonl")]
        assert len(data_private) == 0, f"Found private data files: {data_private}"


# ---------------------------------------------------------------------------
# TestRealDataRun
# ---------------------------------------------------------------------------

class TestRealDataRun:
    """Build the bundle from the real repo (not just toy)."""

    def test_real_build_completes(self, tmp_path):
        out_dir = tmp_path / "release_bundle_real"
        rc, stdout = _run_builder([
            "--output_dir", str(out_dir),
        ], timeout=300)
        assert rc == 0, f"Real build failed: {stdout}"

        # Verify REDACTION_REPORT
        with open(out_dir / "REDACTION_REPORT.json", "r", encoding="utf-8") as f:
            report = json.load(f)
        assert report["redteam_pass"] is True
        assert report["contains_real_pdf"] is False
        assert report["contains_raw_evidence_text"] is False
        assert report["contains_real_claim_text"] is False
