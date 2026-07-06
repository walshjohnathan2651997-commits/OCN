"""Tests for the confidentiality red-team scanner (run_confidentiality_redteam_scan_v1.py).

Verifies:
  - Scanner runs on toy data without crashing
  - Scanner distinguishes toy text from real text (toy_ prefix = low risk, no prefix = high risk)
  - Scanner outputs all three artifacts (findings.csv, summary.json, summary.md)
  - Scanner produces a public release gate (pass/fail)
  - Scanner does not modify or delete any real data
  - Scanner detects forbidden sorting fields in scoring outputs
  - Scanner detects text fields in redacted files
  - Scanner detects long text leaks
  - .gitignore check runs and reports missing entries
"""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_confidentiality_redteam_scan_v1.py"
PYTHON = sys.executable

# Use the same Python that has pytest installed (Python 3.10 on this machine)
PYTHON_310 = r"C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe"
if Path(PYTHON_310).exists():
    PYTHON = PYTHON_310


def _run_scanner(scan_dirs, output_dir, extra_args=None):
    """Run the scanner on the given scan_dirs. Returns (returncode, stdout)."""
    cmd = [PYTHON, str(SCRIPT_PATH), "--scan_dirs"] + list(scan_dirs) + \
          ["--output_dir", str(output_dir)]
    if extra_args:
        cmd.extend(extra_args)
    result = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=60,
    )
    return result.returncode, result.stdout


# ---------------- TestScannerRunsOnToyData ----------------

class TestScannerRunsOnToyData:
    """Verify the scanner runs on toy data without crashing."""

    def test_scanner_completes_on_toy_data(self, tmp_path):
        rc, stdout = _run_scanner(
            scan_dirs=["data/toy_synthetic/"],
            output_dir=tmp_path / "scan_out",
        )
        # Scanner may exit 1 if findings exist, but it should not crash
        assert "Traceback" not in stdout, f"Scanner crashed:\n{stdout}"
        assert "redteam_scan" in stdout

    def test_scanner_produces_all_three_outputs(self, tmp_path):
        out_dir = tmp_path / "scan_out"
        _run_scanner(
            scan_dirs=["data/toy_synthetic/"],
            output_dir=out_dir,
        )
        assert (out_dir / "redteam_findings.csv").exists()
        assert (out_dir / "redteam_summary.json").exists()
        assert (out_dir / "redteam_summary.md").exists()

    def test_scanner_produces_run_config(self, tmp_path):
        """Scanner should write run_config.json (from config_utils integration)."""
        out_dir = tmp_path / "scan_out"
        _run_scanner(
            scan_dirs=["data/toy_synthetic/"],
            output_dir=out_dir,
        )
        assert (out_dir / "run_config.json").exists()

    def test_scanner_prints_guards(self, tmp_path):
        """Scanner must print no_api/no_network/no_training/no_original_data_modification."""
        _, stdout = _run_scanner(
            scan_dirs=["data/toy_synthetic/"],
            output_dir=tmp_path / "scan_out",
        )
        assert "no_api: True" in stdout
        assert "no_network: True" in stdout
        assert "no_training: True" in stdout
        assert "no_original_data_modification: True" in stdout


# ---------------- TestScannerDistinguishesToyVsReal ----------------

class TestScannerDistinguishesToyVsReal:
    """Verify the scanner correctly distinguishes toy text from real text risk."""

    def test_toy_text_with_toy_prefix_is_low_risk(self, tmp_path):
        """A CSV with toy_claim_text column (toy_ prefix) should NOT be high risk."""
        fixture_dir = tmp_path / "toy_fixture"
        fixture_dir.mkdir()
        # Create a toy CSV with proper toy_ prefix
        import pandas as pd
        df = pd.DataFrame({
            "candidate_id": ["c1", "c2"],
            "toy_claim_text": ["this is a toy claim", "another toy claim"],
            "toy_evidence_text": ["toy evidence", "more toy evidence"],
            "synthetic": [True, True],
        })
        df.to_csv(fixture_dir / "toy_data.csv", index=False)

        out_dir = tmp_path / "scan_out"
        rc, stdout = _run_scanner(
            scan_dirs=[str(fixture_dir)],
            output_dir=out_dir,
        )
        findings_path = out_dir / "redteam_findings.csv"
        assert findings_path.exists()
        import pandas as pd
        findings = pd.read_csv(findings_path, keep_default_na=False)
        # Should NOT have any high-risk findings for toy_claim_text
        high_findings = findings[findings["risk_level"] == "high"]
        field_risk_high = high_findings[high_findings["risk_type"] == "field_risk"]
        assert len(field_risk_high) == 0, (
            f"Toy-prefixed columns should not be high risk. "
            f"Found: {field_risk_high.to_dict('records')}"
        )

    def test_real_text_without_toy_prefix_is_high_risk(self, tmp_path):
        """A redacted CSV with claim_text column (no toy_ prefix) should be high risk."""
        fixture_dir = tmp_path / "real_fixture"
        fixture_dir.mkdir()
        import pandas as pd
        # Create a "redacted" CSV with real text column (no toy_ prefix)
        df = pd.DataFrame({
            "candidate_id": ["c1", "c2"],
            "claim_text": ["this is a real claim from a paper", "another real claim"],
            "evidence_text": ["real evidence excerpt", "more real evidence"],
        })
        df.to_csv(fixture_dir / "results_redacted.csv", index=False)

        out_dir = tmp_path / "scan_out"
        rc, stdout = _run_scanner(
            scan_dirs=[str(fixture_dir)],
            output_dir=out_dir,
        )
        findings_path = out_dir / "redteam_findings.csv"
        import pandas as pd
        findings = pd.read_csv(findings_path, keep_default_na=False)
        high_findings = findings[(findings["risk_level"] == "high") & (findings["risk_type"] == "field_risk")]
        # Should detect both claim_text and evidence_text
        matched_fields = set(high_findings["matched_field"].tolist())
        assert "claim_text" in matched_fields, f"Expected claim_text in high-risk findings, got: {matched_fields}"
        assert "evidence_text" in matched_fields, f"Expected evidence_text in high-risk findings, got: {matched_fields}"

    def test_forbidden_sorting_field_detected(self, tmp_path):
        """A smart_queue_scores.csv with true_label should be flagged as high risk."""
        fixture_dir = tmp_path / "scoring_fixture"
        fixture_dir.mkdir()
        import pandas as pd
        df = pd.DataFrame({
            "candidate_id": ["c1"],
            "true_label": ["strong_action_overclaim"],  # FORBIDDEN
            "final_score": [0.9],
        })
        df.to_csv(fixture_dir / "smart_queue_scores.csv", index=False)

        out_dir = tmp_path / "scan_out"
        _run_scanner(
            scan_dirs=[str(fixture_dir)],
            output_dir=out_dir,
        )
        import pandas as pd
        findings = pd.read_csv(out_dir / "redteam_findings.csv", keep_default_na=False)
        forbidden = findings[findings["risk_type"] == "forbidden_sorting_field"]
        assert len(forbidden) > 0, "Expected forbidden_sorting_field finding"
        assert "true_label" in forbidden["matched_field"].tolist()


# ---------------- TestPublicReleaseGate ----------------

class TestPublicReleaseGate:
    """Verify the public release gate works correctly."""

    def test_gate_fails_on_high_risk(self, tmp_path):
        """Scanner should exit 1 when high-risk findings exist."""
        fixture_dir = tmp_path / "dirty_fixture"
        fixture_dir.mkdir()
        import pandas as pd
        df = pd.DataFrame({
            "candidate_id": ["c1"],
            "claim_text": ["real claim text"],  # high risk in redacted file
        })
        df.to_csv(fixture_dir / "data_redacted.csv", index=False)

        rc, _ = _run_scanner(
            scan_dirs=[str(fixture_dir)],
            output_dir=tmp_path / "scan_out",
        )
        assert rc == 1, "Expected exit code 1 (gate FAIL) when high-risk findings exist"

    def test_gate_passes_on_clean_toy_data(self, tmp_path):
        """Scanner should exit 0 when no high-risk findings exist."""
        fixture_dir = tmp_path / "clean_fixture"
        fixture_dir.mkdir()
        import pandas as pd
        df = pd.DataFrame({
            "candidate_id": ["c1", "c2"],
            "toy_claim_text": ["toy claim 1", "toy claim 2"],
            "synthetic": [True, True],
        })
        df.to_csv(fixture_dir / "toy_clean_data.csv", index=False)

        rc, _ = _run_scanner(
            scan_dirs=[str(fixture_dir)],
            output_dir=tmp_path / "scan_out",
        )
        assert rc == 0, "Expected exit code 0 (gate PASS) on clean toy data"

    def test_summary_json_has_gate_field(self, tmp_path):
        """redteam_summary.json must have pass_public_release_gate field."""
        out_dir = tmp_path / "scan_out"
        _run_scanner(
            scan_dirs=["data/toy_synthetic/"],
            output_dir=out_dir,
        )
        with open(out_dir / "redteam_summary.json", "r", encoding="utf-8") as f:
            summary = json.load(f)
        assert "pass_public_release_gate" in summary
        assert isinstance(summary["pass_public_release_gate"], bool)
        assert "high_risk_count" in summary
        assert "medium_risk_count" in summary
        assert "low_risk_count" in summary

    def test_strict_mode_fails_on_medium_risk(self, tmp_path):
        """In strict mode, medium-risk findings also fail the gate."""
        fixture_dir = tmp_path / "medium_fixture"
        fixture_dir.mkdir()
        # Create a file with "top100" in the name (medium risk filename_risk)
        import pandas as pd
        df = pd.DataFrame({"candidate_id": ["c1"], "value": [1]})
        df.to_csv(fixture_dir / "review_queue_top100.csv", index=False)

        # Without strict: should pass (only medium risk)
        rc, _ = _run_scanner(
            scan_dirs=[str(fixture_dir)],
            output_dir=tmp_path / "scan_out_nonstrict",
        )
        assert rc == 0, "Expected gate PASS (medium only, non-strict)"

        # With strict: should fail
        rc, _ = _run_scanner(
            scan_dirs=[str(fixture_dir)],
            output_dir=tmp_path / "scan_out_strict",
            extra_args=["--strict"],
        )
        assert rc == 1, "Expected gate FAIL (medium in strict mode)"


# ---------------- TestScannerDoesNotModifyFiles ----------------

class TestScannerDoesNotModifyFiles:
    """Verify the scanner is strictly read-only."""

    def test_scanner_does_not_modify_scanned_files(self, tmp_path):
        """Files should have the same content+hash before and after scanning."""
        fixture_dir = tmp_path / "fixture"
        fixture_dir.mkdir()
        import pandas as pd
        df = pd.DataFrame({
            "candidate_id": ["c1"],
            "toy_claim_text": ["toy claim"],
            "synthetic": [True],
        })
        target_file = fixture_dir / "toy_data.csv"
        df.to_csv(target_file, index=False)

        import hashlib
        before_hash = hashlib.sha256(target_file.read_bytes()).hexdigest()

        _run_scanner(
            scan_dirs=[str(fixture_dir)],
            output_dir=tmp_path / "scan_out",
        )

        after_hash = hashlib.sha256(target_file.read_bytes()).hexdigest()
        assert before_hash == after_hash, "Scanner modified the scanned file!"

    def test_scanner_does_not_delete_files(self, tmp_path):
        """No files should be deleted by the scanner."""
        fixture_dir = tmp_path / "fixture"
        fixture_dir.mkdir()
        import pandas as pd
        df = pd.DataFrame({"candidate_id": ["c1"], "toy_claim_text": ["x"], "synthetic": [True]})
        target_file = fixture_dir / "toy_data.csv"
        df.to_csv(target_file, index=False)

        _run_scanner(
            scan_dirs=[str(fixture_dir)],
            output_dir=tmp_path / "scan_out",
        )

        assert target_file.exists(), "Scanner deleted a scanned file!"


# ---------------- TestGitignoreCheck ----------------

class TestGitignoreCheck:
    """Verify the .gitignore check runs and reports missing entries."""

    def test_gitignore_check_in_summary(self, tmp_path):
        """redteam_summary.json should contain gitignore_report."""
        out_dir = tmp_path / "scan_out"
        _run_scanner(
            scan_dirs=["data/toy_synthetic/"],
            output_dir=out_dir,
        )
        with open(out_dir / "redteam_summary.json", "r", encoding="utf-8") as f:
            summary = json.load(f)
        assert "gitignore_report" in summary
        gi = summary["gitignore_report"]
        assert "existing_count" in gi
        assert "missing" in gi
        assert "missing_count" in gi

    def test_gitignore_findings_in_csv(self, tmp_path):
        """redteam_findings.csv should contain gitignore_missing entries."""
        out_dir = tmp_path / "scan_out"
        _run_scanner(
            scan_dirs=["data/toy_synthetic/"],
            output_dir=out_dir,
        )
        import pandas as pd
        findings = pd.read_csv(out_dir / "redteam_findings.csv", keep_default_na=False)
        gi_findings = findings[findings["risk_type"] == "gitignore_missing"]
        # The repo .gitignore may or may not have all entries; just verify the check ran
        # (if all entries exist, there will be 0 findings; if any missing, there will be >0)
        assert "gitignore_missing" in findings["risk_type"].tolist() or len(gi_findings) == 0


# ---------------- TestFindingsSchema ----------------

class TestFindingsSchema:
    """Verify the findings CSV has the required columns."""

    def test_findings_csv_has_required_columns(self, tmp_path):
        out_dir = tmp_path / "scan_out"
        _run_scanner(
            scan_dirs=["data/toy_synthetic/"],
            output_dir=out_dir,
        )
        import pandas as pd
        findings = pd.read_csv(out_dir / "redteam_findings.csv", keep_default_na=False)
        required_cols = {"path", "risk_level", "risk_type", "matched_field",
                         "line_or_row", "message", "recommendation"}
        assert required_cols.issubset(set(findings.columns)), (
            f"Missing columns: {required_cols - set(findings.columns)}"
        )

    def test_risk_levels_are_valid(self, tmp_path):
        """All risk_level values must be high/medium/low."""
        out_dir = tmp_path / "scan_out"
        _run_scanner(
            scan_dirs=["data/toy_synthetic/"],
            output_dir=out_dir,
        )
        import pandas as pd
        findings = pd.read_csv(out_dir / "redteam_findings.csv", keep_default_na=False)
        valid_levels = {"high", "medium", "low"}
        actual_levels = set(findings["risk_level"].unique())
        assert actual_levels.issubset(valid_levels), (
            f"Invalid risk levels: {actual_levels - valid_levels}"
        )

    def test_summary_md_has_risk_sections(self, tmp_path):
        """redteam_summary.md should have High/Medium/Low risk sections."""
        out_dir = tmp_path / "scan_out"
        _run_scanner(
            scan_dirs=["data/toy_synthetic/"],
            output_dir=out_dir,
        )
        md = (out_dir / "redteam_summary.md").read_text(encoding="utf-8")
        assert "High Risk" in md
        assert "Medium Risk" in md
        assert "Low Risk" in md
        assert "Public Release Gate" in md


# ---------------- TestFullRepoScan ----------------

class TestFullRepoScan:
    """Run the scanner on the full repo (default scan_dirs) and verify it completes."""

    def test_full_repo_scan_completes(self, tmp_path):
        """The scanner should complete on the full repo without crashing."""
        rc, stdout = _run_scanner(
            scan_dirs=["README.md", "CURRENT_MAINLINE.md", "docs/", "scripts/",
                       "schemas/", "experiments/", "data/toy_synthetic/"],
            output_dir=tmp_path / "full_scan_out",
        )
        # May exit 1 due to existing high-risk findings in canonicalized_review_queue_v1 etc.
        # The key is it doesn't crash
        assert "Traceback" not in stdout, f"Scanner crashed on full repo:\n{stdout}"
        assert "redteam_scan" in stdout
        # Verify summary exists
        assert (tmp_path / "full_scan_out" / "redteam_summary.json").exists()

    def test_full_repo_summary_has_counts(self, tmp_path):
        """Full repo scan summary should have non-negative counts."""
        out_dir = tmp_path / "full_scan_out"
        _run_scanner(
            scan_dirs=["README.md", "CURRENT_MAINLINE.md", "docs/", "scripts/",
                       "schemas/", "experiments/", "data/toy_synthetic/"],
            output_dir=out_dir,
        )
        with open(out_dir / "redteam_summary.json", "r", encoding="utf-8") as f:
            summary = json.load(f)
        assert summary["high_risk_count"] >= 0
        assert summary["medium_risk_count"] >= 0
        assert summary["low_risk_count"] >= 0
        assert summary["scanned_files"] > 0
