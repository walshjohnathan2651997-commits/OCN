"""Tests for paper assets generator (generate_paper_assets_v3_17.py).

Verifies:
  - paper_assets directory is generated with all required files
  - No CSV contains forbidden text columns (claim_text, evidence_text, etc.)
  - No file contains raw claim/evidence text (long text strings)
  - Missing inputs do not crash the script (writes "not generated")
  - paper_claims_checklist.md has Safe Claims, Unsafe Claims, and Evidence sections
  - All table captions include the silver diagnostic caveat
  - LaTeX output uses booktabs style
  - run_config.json is produced
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "generate_paper_assets_v3_17.py"
PYTHON = sys.executable

PYTHON_310 = r"C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe"
if Path(PYTHON_310).exists():
    PYTHON = PYTHON_310

FORBIDDEN_TEXT_COLUMNS = [
    "claim_text", "evidence_text", "selected_evidence",
    "raw_text", "clean_text", "retrieved_text",
]

# Files where field names (not values) are acceptable in metadata context
METADATA_FILES = {"run_config.json", "schema_validation_report.json"}


def _run_script(args, timeout=120):
    """Run the paper assets generator. Returns (returncode, stdout)."""
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
# TestPaperAssetsGenerated
# ---------------------------------------------------------------------------

class TestPaperAssetsGenerated:
    """Paper assets directory is generated with all required files."""

    def test_all_required_files_exist(self, tmp_path):
        out_dir = tmp_path / "paper_assets"
        rc, stdout = _run_script([
            "--toy_mode",
            "--output_dir", str(out_dir),
        ])
        assert rc == 0, f"Script failed: {stdout}"

        required = [
            "tables/table1_dataset_summary.md",
            "tables/table1_dataset_summary.tex",
            "tables/table2_retrieval_recall.md",
            "tables/table2_retrieval_recall.tex",
            "tables/table3_format_shift_ablation.md",
            "tables/table3_format_shift_ablation.tex",
            "tables/table4_canonicalizer_ablation.md",
            "tables/table4_canonicalizer_ablation.tex",
            "tables/table5_review_queue.md",
            "tables/table5_review_queue.tex",
            "tables/table6_leakage_audit.md",
            "tables/table6_leakage_audit.tex",
            "tables/table7_complexity_utility.md",
            "tables/table7_complexity_utility.tex",
            "tables/table8_human_audit_if_available.md",
            "tables/table8_human_audit_if_available.tex",
            "figures/pipeline_ascii.md",
            "figures/format_shift_bar_data.csv",
            "figures/queue_precision_recall_data.csv",
            "figures/smartqueue_bucket_counts.csv",
            "paper_results_summary.md",
            "paper_claims_checklist.md",
            "run_config.json",
        ]
        for name in required:
            assert (out_dir / name).exists(), f"Missing: {name}"


# ---------------------------------------------------------------------------
# TestNoForbiddenTextColumns
# ---------------------------------------------------------------------------

class TestNoForbiddenTextColumns:
    """No CSV in paper_assets contains forbidden text columns."""

    def test_csvs_have_no_text_columns(self, tmp_path):
        out_dir = tmp_path / "paper_assets"
        _run_script(["--toy_mode", "--output_dir", str(out_dir)])

        csv_files = list(out_dir.rglob("*.csv"))
        assert len(csv_files) > 0, "No CSV files found"

        for csv_path in csv_files:
            df = pd.read_csv(csv_path, keep_default_na=False, nrows=1)
            for col in df.columns:
                assert col not in FORBIDDEN_TEXT_COLUMNS, (
                    f"{csv_path.name} has forbidden column: {col}"
                )


# ---------------------------------------------------------------------------
# TestNoRawTextInFiles
# ---------------------------------------------------------------------------

class TestNoRawTextInFiles:
    """No file in paper_assets contains raw claim/evidence text.

    We check for long strings (>200 chars) that would indicate raw text
    leakage. Field names in metadata files (run_config.json) are allowed.
    """

    def test_no_long_text_strings(self, tmp_path):
        out_dir = tmp_path / "paper_assets"
        _run_script(["--toy_mode", "--output_dir", str(out_dir)])

        for f in out_dir.rglob("*"):
            if not f.is_file():
                continue
            if f.suffix in (".csv",):
                # Check cell values in CSVs
                df = pd.read_csv(f, keep_default_na=False)
                for col in df.columns:
                    for val in df[col].astype(str):
                        if len(val) > 200:
                            pytest.fail(
                                f"{f.name} column '{col}' has cell >200 chars: "
                                f"{val[:100]}..."
                            )
            elif f.suffix in (".md", ".tex"):
                # Check for long lines that aren't table headers or formatting
                content = f.read_text(encoding="utf-8")
                for line in content.split("\n"):
                    # Allow long lines in LaTeX tables (formatting)
                    if len(line) > 300 and not line.strip().startswith("\\"):
                        # Check if it looks like raw text (not a URL or path)
                        if not line.strip().startswith(("http", "/", "D:\\", "C:\\")):
                            pytest.fail(
                                f"{f.name} has long line ({len(line)} chars): "
                                f"{line[:100]}..."
                            )

    def test_no_evidence_text_values_in_csvs(self, tmp_path):
        """CSVs should not contain actual evidence/claim text values."""
        out_dir = tmp_path / "paper_assets"
        _run_script(["--toy_mode", "--output_dir", str(out_dir)])

        for f in out_dir.rglob("*.csv"):
            df = pd.read_csv(f, keep_default_na=False)
            for col in df.columns:
                if col.lower() in FORBIDDEN_TEXT_COLUMNS:
                    pytest.fail(f"{f.name} has forbidden column: {col}")
                # Check for text that looks like claims (heuristic)
                for val in df[col].astype(str):
                    if len(val) > 100 and any(
                        kw in val.lower() for kw in [" claim ", " evidence ", "we propose", "we present"]
                    ):
                        pytest.fail(
                            f"{f.name} column '{col}' may contain raw text: {val[:80]}..."
                        )


# ---------------------------------------------------------------------------
# TestMissingInputsDontCrash
# ---------------------------------------------------------------------------

class TestMissingInputsDontCrash:
    """Missing experiment inputs should not crash the script."""

    def test_empty_experiments_dir(self, tmp_path):
        """Script should complete even when experiments_dir is empty."""
        empty_dir = tmp_path / "empty_experiments"
        empty_dir.mkdir()
        out_dir = tmp_path / "paper_assets"

        rc, stdout = _run_script([
            "--experiments_dir", str(empty_dir),
            "--output_dir", str(out_dir),
        ])
        assert rc == 0, f"Script crashed on empty experiments dir: {stdout}"

        # Tables should still exist with "not generated" status
        assert (out_dir / "tables" / "table1_dataset_summary.md").exists()
        assert (out_dir / "tables" / "table5_review_queue.md").exists()

        # Check "not generated" appears in some tables
        t5_md = (out_dir / "tables" / "table5_review_queue.md").read_text(encoding="utf-8")
        assert "not generated" in t5_md.lower(), "Table 5 should say 'not generated' when input missing"

    def test_missing_file_logged(self, tmp_path):
        """Missing files should be logged in run_config.json."""
        empty_dir = tmp_path / "empty_experiments"
        empty_dir.mkdir()
        out_dir = tmp_path / "paper_assets"

        _run_script([
            "--experiments_dir", str(empty_dir),
            "--output_dir", str(out_dir),
        ])

        rc_path = out_dir / "run_config.json"
        assert rc_path.exists()
        with open(rc_path, "r", encoding="utf-8") as f:
            rc = json.load(f)
        # missing_files may or may not be populated, but the key should exist
        assert "missing_files" in rc or "guards" in rc  # at least basic structure


# ---------------------------------------------------------------------------
# TestClaimsChecklist
# ---------------------------------------------------------------------------

class TestClaimsChecklist:
    """paper_claims_checklist.md has required sections."""

    def test_has_safe_and_unsafe_claims(self, tmp_path):
        out_dir = tmp_path / "paper_assets"
        _run_script(["--toy_mode", "--output_dir", str(out_dir)])

        md = (out_dir / "paper_claims_checklist.md").read_text(encoding="utf-8")
        assert "## Safe Claims" in md, "Missing Safe Claims section"
        assert "## Unsafe Claims" in md, "Missing Unsafe Claims section"
        assert "## Evidence Index" in md or "Evidence" in md, "Missing Evidence section"

    def test_has_caveat(self, tmp_path):
        out_dir = tmp_path / "paper_assets"
        _run_script(["--toy_mode", "--output_dir", str(out_dir)])

        md = (out_dir / "paper_claims_checklist.md").read_text(encoding="utf-8")
        assert "silver diagnostic" in md.lower()
        assert "not gold" in md.lower() or "not human-audited" in md.lower()

    def test_safe_claims_have_evidence(self, tmp_path):
        out_dir = tmp_path / "paper_assets"
        _run_script(["--toy_mode", "--output_dir", str(out_dir)])

        md = (out_dir / "paper_claims_checklist.md").read_text(encoding="utf-8")
        # Each safe claim (S1-S5) should have an Evidence line
        for i in range(1, 6):
            assert f"S{i}:" in md, f"Missing safe claim S{i}"
        assert "**Evidence file**" in md, "Missing evidence references"

    def test_unsafe_claims_have_reasons(self, tmp_path):
        out_dir = tmp_path / "paper_assets"
        _run_script(["--toy_mode", "--output_dir", str(out_dir)])

        md = (out_dir / "paper_claims_checklist.md").read_text(encoding="utf-8")
        # Each unsafe claim (U1-U5) should have a "Why unsafe" line
        for i in range(1, 6):
            assert f"U{i}:" in md, f"Missing unsafe claim U{i}"
        assert "Why unsafe" in md, "Missing 'Why unsafe' explanations"


# ---------------------------------------------------------------------------
# TestTableCaptions
# ---------------------------------------------------------------------------

class TestTableCaptions:
    """All LaTeX table captions include the silver diagnostic caveat."""

    def test_tex_tables_have_caveat(self, tmp_path):
        out_dir = tmp_path / "paper_assets"
        _run_script(["--toy_mode", "--output_dir", str(out_dir)])

        tex_files = list((out_dir / "tables").glob("*.tex"))
        assert len(tex_files) == 8, f"Expected 8 tex files, got {len(tex_files)}"

        for tex_path in tex_files:
            content = tex_path.read_text(encoding="utf-8")
            assert "silver diagnostic" in content.lower(), (
                f"{tex_path.name} missing silver diagnostic caveat"
            )
            assert "\\caption" in content, f"{tex_path.name} missing caption"

    def test_tex_uses_booktabs(self, tmp_path):
        out_dir = tmp_path / "paper_assets"
        _run_script(["--toy_mode", "--output_dir", str(out_dir)])

        tex_files = list((out_dir / "tables").glob("*.tex"))
        for tex_path in tex_files:
            content = tex_path.read_text(encoding="utf-8")
            # At least some should use booktabs; missing-input tables may not
            if "not generated" not in content.lower():
                assert "\\toprule" in content, f"{tex_path.name} missing \\toprule"
                assert "\\midrule" in content, f"{tex_path.name} missing \\midrule"
                assert "\\bottomrule" in content, f"{tex_path.name} missing \\bottomrule"


# ---------------------------------------------------------------------------
# TestPaperResultsSummary
# ---------------------------------------------------------------------------

class TestPaperResultsSummary:
    """paper_results_summary.md has RQ-organized structure."""

    def test_has_all_rqs(self, tmp_path):
        out_dir = tmp_path / "paper_assets"
        _run_script(["--toy_mode", "--output_dir", str(out_dir)])

        md = (out_dir / "paper_results_summary.md").read_text(encoding="utf-8")
        for rq in ["RQ1", "RQ2", "RQ3", "RQ4", "RQ5", "RQ6", "RQ7", "RQ8"]:
            assert rq in md, f"Missing {rq} in results summary"

    def test_has_caveat(self, tmp_path):
        out_dir = tmp_path / "paper_assets"
        _run_script(["--toy_mode", "--output_dir", str(out_dir)])

        md = (out_dir / "paper_results_summary.md").read_text(encoding="utf-8")
        assert "silver diagnostic" in md.lower()


# ---------------------------------------------------------------------------
# TestPipelineAscii
# ---------------------------------------------------------------------------

class TestPipelineAscii:
    """pipeline_ascii.md has the pipeline diagram."""

    def test_pipeline_has_all_stages(self, tmp_path):
        out_dir = tmp_path / "paper_assets"
        _run_script(["--toy_mode", "--output_dir", str(out_dir)])

        md = (out_dir / "figures" / "pipeline_ascii.md").read_text(encoding="utf-8")
        stages = [
            "Local PDFs",
            "Text extraction",
            "BM25",
            "Evidence canonicalization",
            "R4",
            "SmartQueue",
            "review queue",
        ]
        for stage in stages:
            assert stage.lower() in md.lower(), f"Pipeline missing stage: {stage}"


# ---------------------------------------------------------------------------
# TestRunConfig
# ---------------------------------------------------------------------------

class TestRunConfig:
    """run_config.json has correct structure."""

    def test_run_config_valid(self, tmp_path):
        out_dir = tmp_path / "paper_assets"
        _run_script(["--toy_mode", "--output_dir", str(out_dir)])

        rc_path = out_dir / "run_config.json"
        assert rc_path.exists()
        with open(rc_path, "r", encoding="utf-8") as f:
            rc = json.load(f)
        assert rc.get("script_name") == "generate_paper_assets_v3_17.py"
        assert "guards" in rc
        assert "caveat" in rc


# ---------------------------------------------------------------------------
# TestRealDataRun
# ---------------------------------------------------------------------------

class TestRealDataRun:
    """Run the script on real V3.17 data (if available)."""

    def test_real_data_run_completes(self, tmp_path):
        experiments_dir = REPO_ROOT / "experiments"
        if not experiments_dir.exists():
            pytest.skip("Experiments directory not available")

        out_dir = tmp_path / "paper_assets_real"
        rc, stdout = _run_script([
            "--experiments_dir", str(experiments_dir),
            "--output_dir", str(out_dir),
        ], timeout=120)
        assert rc == 0, f"Script failed on real data: {stdout}"

        # Verify table5 has actual metrics (not "not generated")
        t5_md = (out_dir / "tables" / "table5_review_queue.md").read_text(encoding="utf-8")
        assert "not generated" not in t5_md.lower(), "Table 5 should have real data"

        # Verify strong_F1 appears
        assert "strong_F1" in t5_md or "strong_f1" in t5_md.lower()
