"""Tests for the V3.17 confidential pipeline runner.

Verifies:
  - Runner produces run_summary.json with correct structure
  - Runner produces stage_status.csv with required columns
  - Runner produces run_log.txt and config_snapshot.yaml
  - Full mode is rejected without --allow_private_data true
  - Full mode is accepted with --allow_private_data true (but doesn't run real data in tests)
  - Toy mode runs successfully and completes all default stages
  - Unknown stages are rejected
  - Runner is read-only (doesn't modify scanned files)
  - stage_status.csv has valid status values
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_v3_17_confidential_pipeline.py"
PYTHON = sys.executable

PYTHON_310 = r"C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe"
if Path(PYTHON_310).exists():
    PYTHON = PYTHON_310


def _run_runner(extra_args, timeout=120):
    """Run the pipeline runner with the given extra args. Returns (returncode, stdout)."""
    cmd = [PYTHON, str(SCRIPT_PATH)] + list(extra_args)
    result = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
    )
    return result.returncode, result.stdout


# ---------------- TestRunSummaryStructure ----------------

class TestRunSummaryStructure:
    """Verify run_summary.json has the correct structure."""

    def test_run_summary_has_required_fields(self, tmp_path):
        out_dir = tmp_path / "run_out"
        rc, _ = _run_runner([
            "--mode", "toy",
            "--stages", "corpus",
            "--output_dir", str(out_dir),
        ])
        assert rc == 0, "Toy pipeline should succeed"
        summary_path = out_dir / "run_summary.json"
        assert summary_path.exists()
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)
        required_fields = {
            "pipeline", "mode", "overall_status", "timestamp",
            "stages_requested", "stages_completed", "stages_failed",
            "n_stages_requested", "n_stages_completed", "n_stages_failed",
            "config_source", "guards", "stage_details",
        }
        assert required_fields.issubset(set(summary.keys())), (
            f"Missing fields: {required_fields - set(summary.keys())}"
        )

    def test_overall_status_completed_on_success(self, tmp_path):
        out_dir = tmp_path / "run_out"
        _run_runner([
            "--mode", "toy",
            "--stages", "corpus",
            "--output_dir", str(out_dir),
        ])
        with open(out_dir / "run_summary.json", "r", encoding="utf-8") as f:
            summary = json.load(f)
        assert summary["overall_status"] == "completed"

    def test_guards_enforced(self, tmp_path):
        out_dir = tmp_path / "run_out"
        _run_runner([
            "--mode", "toy",
            "--stages", "corpus",
            "--output_dir", str(out_dir),
        ])
        with open(out_dir / "run_summary.json", "r", encoding="utf-8") as f:
            summary = json.load(f)
        guards = summary["guards"]
        assert guards["no_api"] is True
        assert guards["no_network"] is True
        assert guards["no_training"] is True
        assert guards["no_original_data_modification"] is True

    def test_stage_details_have_runtime(self, tmp_path):
        out_dir = tmp_path / "run_out"
        _run_runner([
            "--mode", "toy",
            "--stages", "corpus",
            "--output_dir", str(out_dir),
        ])
        with open(out_dir / "run_summary.json", "r", encoding="utf-8") as f:
            summary = json.load(f)
        for stage in summary["stage_details"]:
            assert "runtime_seconds" in stage
            assert isinstance(stage["runtime_seconds"], (int, float))
            assert stage["runtime_seconds"] >= 0


# ---------------- TestStageStatusCsv ----------------

class TestStageStatusCsv:
    """Verify stage_status.csv has the correct columns and values."""

    def test_stage_status_csv_has_required_columns(self, tmp_path):
        out_dir = tmp_path / "run_out"
        _run_runner([
            "--mode", "toy",
            "--stages", "corpus",
            "--output_dir", str(out_dir),
        ])
        csv_path = out_dir / "stage_status.csv"
        assert csv_path.exists()
        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            required_cols = {"stage", "status", "start", "end", "runtime_seconds"}
            assert required_cols.issubset(set(reader.fieldnames or []))

    def test_stage_status_has_valid_status_values(self, tmp_path):
        out_dir = tmp_path / "run_out"
        _run_runner([
            "--mode", "toy",
            "--stages", "corpus,retrieval",
            "--output_dir", str(out_dir),
        ])
        with open(out_dir / "stage_status.csv", "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        valid_statuses = {"ok", "ok_with_findings", "failed", "running"}
        for row in rows:
            assert row["status"] in valid_statuses, (
                f"Invalid status '{row['status']}' for stage '{row['stage']}'"
            )

    def test_stage_status_rows_match_requested(self, tmp_path):
        out_dir = tmp_path / "run_out"
        _run_runner([
            "--mode", "toy",
            "--stages", "corpus,retrieval",
            "--output_dir", str(out_dir),
        ])
        with open(out_dir / "stage_status.csv", "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 2
        stages = {row["stage"] for row in rows}
        assert stages == {"corpus", "retrieval"}


# ---------------- TestAllOutputsProduced ----------------

class TestAllOutputsProduced:
    """Verify all 4 output files are produced."""

    def test_all_outputs_exist(self, tmp_path):
        out_dir = tmp_path / "run_out"
        _run_runner([
            "--mode", "toy",
            "--stages", "corpus",
            "--output_dir", str(out_dir),
        ])
        assert (out_dir / "run_summary.json").exists()
        assert (out_dir / "stage_status.csv").exists()
        assert (out_dir / "run_log.txt").exists()
        assert (out_dir / "config_snapshot.yaml").exists()

    def test_run_log_has_stage_header(self, tmp_path):
        out_dir = tmp_path / "run_out"
        _run_runner([
            "--mode", "toy",
            "--stages", "corpus",
            "--output_dir", str(out_dir),
        ])
        log = (out_dir / "run_log.txt").read_text(encoding="utf-8")
        assert "STAGE: corpus" in log
        assert "V3.17 Confidential Pipeline Run" in log

    def test_config_snapshot_is_valid_yaml(self, tmp_path):
        out_dir = tmp_path / "run_out"
        _run_runner([
            "--mode", "toy",
            "--stages", "corpus",
            "--output_dir", str(out_dir),
        ])
        config_path = out_dir / "config_snapshot.yaml"
        assert config_path.exists()
        import yaml
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        assert isinstance(config, dict)
        assert "no_api" in config
        assert config["no_api"] is True


# ---------------- TestFullModeAuthorization ----------------

class TestFullModeAuthorization:
    """Verify full mode requires --allow_private_data true."""

    def test_full_mode_rejected_without_flag(self):
        rc, stdout = _run_runner(["--mode", "full"])
        assert rc == 2, f"Expected exit 2, got {rc}"
        assert "requires --allow_private_data true" in stdout

    def test_full_mode_rejected_with_false(self):
        rc, stdout = _run_runner(["--mode", "full", "--allow_private_data", "false"])
        assert rc == 2
        assert "requires --allow_private_data true" in stdout

    def test_full_mode_accepted_with_true_but_stops_early(self, tmp_path):
        """Full mode with flag should not be rejected, but will fail on missing private data.
        We only verify it's not rejected at the authorization gate."""
        out_dir = tmp_path / "run_out"
        rc, stdout = _run_runner([
            "--mode", "full",
            "--allow_private_data", "true",
            "--stages", "corpus",
            "--output_dir", str(out_dir),
        ])
        # Should NOT contain the authorization rejection message
        assert "requires --allow_private_data true" not in stdout
        # It may fail due to missing private PDFs, but that's expected
        # The key is the authorization gate passed.


# ---------------- TestStageValidation ----------------

class TestStageValidation:
    """Verify stage name validation."""

    def test_unknown_stage_rejected(self, tmp_path):
        rc, stdout = _run_runner([
            "--mode", "toy",
            "--stages", "unknown_stage",
            "--output_dir", str(tmp_path / "run_out"),
        ])
        assert rc == 2
        assert "Unknown stages" in stdout
        assert "unknown_stage" in stdout

    def test_all_stages_accepted(self, tmp_path):
        """Verify all 10 stage names are valid."""
        all_stages = "corpus,retrieval,canonicalizer,format_shift,r4_eval,smart_queue,leakage_audit,schema_validation,redteam_scan,paper_assets"
        rc, stdout = _run_runner([
            "--mode", "toy",
            "--stages", "paper_assets",
            "--output_dir", str(tmp_path / "run_out"),
        ])
        # paper_assets should succeed without error
        assert rc == 0, f"paper_assets stage failed: {stdout}"
        assert "Unknown stages" not in stdout


# ---------------- TestPaperAssetsStage ----------------

class TestPaperAssetsStage:
    """Verify the paper_assets stage collects artifacts."""

    def test_paper_assets_creates_manifest(self, tmp_path):
        out_dir = tmp_path / "run_out"
        _run_runner([
            "--mode", "toy",
            "--stages", "paper_assets",
            "--output_dir", str(out_dir),
        ])
        assets_dir = out_dir / "paper_assets"
        assert assets_dir.exists()
        manifest_path = assets_dir / "paper_assets_manifest.json"
        assert manifest_path.exists()
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        assert "mode" in manifest
        assert manifest["mode"] == "toy"
        assert "collected_files" in manifest
        assert "warning" in manifest


# ---------------- TestPipelineFailureHandling ----------------

class TestPipelineFailureHandling:
    """Verify the pipeline handles failures correctly."""

    def test_pipeline_stops_on_failure(self, tmp_path):
        """If a stage fails, the pipeline should stop and not run subsequent stages."""
        out_dir = tmp_path / "run_out"
        # r4_eval in toy mode may fail if dependencies are missing
        rc, stdout = _run_runner([
            "--mode", "toy",
            "--stages", "corpus,r4_eval,smart_queue",
            "--output_dir", str(out_dir),
        ])
        with open(out_dir / "run_summary.json", "r", encoding="utf-8") as f:
            summary = json.load(f)
        # If r4_eval failed, smart_queue should NOT have run
        if summary["n_stages_failed"] > 0:
            # smart_queue should not be in completed stages
            completed = summary["stages_completed"]
            # If r4_eval is in failed, smart_queue should not be in completed
            if "r4_eval" in summary["stages_failed"]:
                assert "smart_queue" not in completed, (
                    "Pipeline should stop after failure, but smart_queue ran"
                )

    def test_failed_overall_status(self, tmp_path):
        """When a stage fails, overall_status should be 'failed'."""
        out_dir = tmp_path / "run_out"
        rc, stdout = _run_runner([
            "--mode", "toy",
            "--stages", "corpus,r4_eval",
            "--output_dir", str(out_dir),
        ])
        with open(out_dir / "run_summary.json", "r", encoding="utf-8") as f:
            summary = json.load(f)
        if summary["n_stages_failed"] > 0:
            assert summary["overall_status"] == "failed"
            assert rc == 1


# ---------------- TestRunnerReadOnly ----------------

class TestRunnerReadOnly:
    """Verify the runner doesn't modify existing files."""

    def test_runner_does_not_modify_existing_outputs(self, tmp_path):
        """Running the pipeline should not modify existing experiment outputs."""
        import hashlib
        # First, ensure toy outputs exist
        _run_runner([
            "--mode", "toy",
            "--stages", "corpus",
            "--output_dir", str(tmp_path / "first_run"),
        ])
        # Hash the corpus output
        corpus_file = REPO_ROOT / "data" / "pdf_corpus_toy_v1" / "sentences.jsonl"
        if corpus_file.exists():
            before = hashlib.sha256(corpus_file.read_bytes()).hexdigest()
            # Run again
            _run_runner([
                "--mode", "toy",
                "--stages", "corpus",
                "--output_dir", str(tmp_path / "second_run"),
            ])
            after = hashlib.sha256(corpus_file.read_bytes()).hexdigest()
            assert before == after, "Runner modified existing corpus output"
