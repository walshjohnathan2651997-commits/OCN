"""Tests for V3.17 path configurability (Task Pack I).

Verifies:
  - config_utils.get_repo_root() resolves correctly.
  - config_utils.resolve_path() handles relative/absolute paths.
  - config_utils.detect_private_mode() and fail_if_network_requested() work.
  - configs/v3_17_paths.yaml exists and has required keys.
  - P0 scripts do not contain D:\ocn hardcoded paths.
  - The path hardcoding audit report shows current_pipeline_blocker = 0.
  - The toy pipeline can run in a temporary directory.
"""

from __future__ import annotations

import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
LIB_DIR = SCRIPTS_DIR / "lib"

# Ensure scripts/lib is importable
sys.path.insert(0, str(LIB_DIR))

from config_utils import (  # noqa: E402
    get_repo_root,
    resolve_path,
    ensure_dir,
    load_yaml_config,
    detect_private_mode,
    fail_if_network_requested,
    load_paths_config,
)

# P0 scripts that must be free of D:\ocn hardcoding
P0_SCRIPTS = [
    "run_simclaim_pdf_retrieval_v1.py",
    "run_r4_evidence_canonicalization_v1.py",
    "run_canonicalized_review_queue_v1.py",
    "run_canonicalized_risk_ranking_v1.py",
    "build_pdf_sentence_corpus_v1.py",
    "run_bm25_sentence_retrieval_v1.py",
    "run_canonicalizer_ablation_v1.py",
    "run_format_shift_ablation_v1.py",
    "evaluate_r4_on_evidence_variants_v1.py",
    "run_leakage_audit_v1.py",
    "run_v3_17_confidential_pipeline.py",
    "generate_project_status_report_v1.py",
]

HARDCODED_RE = re.compile(r"D:[\\/]ocn")

# generate_project_status_report_v1.py legitimately contains "D:\ocn" as a
# string literal in its scanner code (it detects hardcoding in other scripts).
# We exclude it from the "no D:\ocn" check.
SCANNER_SCRIPTS = {"generate_project_status_report_v1.py"}

PATHS_CONFIG = REPO_ROOT / "configs" / "v3_17_paths.yaml"
AUDIT_MD = REPO_ROOT / "reports" / "path_hardcoding_audit_v3_17.md"
AUDIT_CSV = REPO_ROOT / "reports" / "path_hardcoding_audit_v3_17.csv"
EXEMPTIONS_DOC = REPO_ROOT / "docs" / "legacy_scripts_path_hardcoding_exemptions.md"

PYTHON = sys.executable


class TestConfigUtils:
    def test_get_repo_root(self):
        root = get_repo_root()
        assert root.is_dir(), f"repo root is not a directory: {root}"
        # The repo root should contain README.md and scripts/
        assert (root / "README.md").exists(), "repo root missing README.md"
        assert (root / "scripts").is_dir(), "repo root missing scripts/"

    def test_resolve_path_absolute(self):
        result = resolve_path("/tmp" if os.name != "nt" else "C:\\Windows")
        assert result is not None
        assert result.is_absolute()

    def test_resolve_path_relative(self):
        result = resolve_path("data/test_file.csv")
        assert result is not None
        assert result.is_absolute()
        assert result.name == "test_file.csv"
        assert "data" in result.parts

    def test_resolve_path_none(self):
        assert resolve_path(None) is None

    def test_resolve_path_with_repo_root(self):
        custom_root = Path(tempfile.mkdtemp())
        try:
            result = resolve_path("foo/bar.csv", repo_root=custom_root)
            assert result == (custom_root / "foo" / "bar.csv").resolve()
        finally:
            shutil.rmtree(custom_root, ignore_errors=True)

    def test_resolve_path_legacy_dict_signature(self):
        config = {
            "project_root": ".",
            "candidate_csv": "data/test.csv",
        }
        result = resolve_path(config, "candidate_csv")
        assert result is not None
        assert result.name == "test.csv"

    def test_resolve_path_legacy_dict_missing_key(self):
        config = {"project_root": "."}
        assert resolve_path(config, "nonexistent_key") is None

    def test_ensure_dir(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            new_dir = tmp / "a" / "b" / "c"
            result = ensure_dir(new_dir)
            assert result is not None
            assert result.exists()
            assert result.is_dir()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_ensure_dir_none(self):
        assert ensure_dir(None) is None

    def test_detect_private_mode_default_off(self):
        assert detect_private_mode() is False

    def test_detect_private_mode_env_var(self, monkeypatch):
        monkeypatch.setenv("OCN_ALLOW_PRIVATE_DATA", "true")
        assert detect_private_mode() is True

    def test_detect_private_mode_env_var_false(self, monkeypatch):
        monkeypatch.setenv("OCN_ALLOW_PRIVATE_DATA", "false")
        assert detect_private_mode() is False

    def test_detect_private_mode_args_true(self):
        class Args:
            allow_private_data = True
        assert detect_private_mode(args=Args()) is True

    def test_detect_private_mode_args_string_true(self):
        class Args:
            allow_private_data = "true"
        assert detect_private_mode(args=Args()) is True

    def test_detect_private_mode_config_true(self):
        assert detect_private_mode(config={"allow_private_data": True}) is True

    def test_fail_if_network_requested_blocks(self):
        class Args:
            allow_private_data = False
            allow_network = True
        with pytest.raises(PermissionError, match="Network/API access requested"):
            fail_if_network_requested(args=Args())

    def test_fail_if_network_requested_allows_when_private(self):
        class Args:
            allow_private_data = True
            allow_network = True
        # Should not raise
        fail_if_network_requested(args=Args())

    def test_fail_if_network_requested_no_network(self):
        class Args:
            allow_private_data = False
        # Should not raise (no network requested)
        fail_if_network_requested(args=Args())


class TestPathsConfig:
    def test_paths_config_exists(self):
        assert PATHS_CONFIG.exists(), f"paths config missing: {PATHS_CONFIG}"

    def test_paths_config_has_required_keys(self):
        config = load_paths_config()
        required = [
            "candidate_csv",
            "pdf_dir",
            "pdf_corpus_dir",
            "experiments_dir",
            "paper_assets_dir",
            "reports_dir",
            "release_dir",
        ]
        for key in required:
            assert key in config, f"paths config missing key: {key}"

    def test_paths_config_guards_true(self):
        config = load_paths_config()
        assert config.get("no_api") is True
        assert config.get("no_network") is True
        assert config.get("no_training") is True

    def test_load_paths_config_fallback(self):
        """When the config file doesn't exist, load_paths_config should
        return fallback defaults with all required keys."""
        config = load_paths_config("/nonexistent/path.yaml")
        required = [
            "candidate_csv",
            "pdf_dir",
            "pdf_corpus_dir",
            "experiments_dir",
            "paper_assets_dir",
            "reports_dir",
            "release_dir",
        ]
        for key in required:
            assert key in config, f"fallback config missing key: {key}"


class TestP0ScriptsNoHardcoding:
    """All P0 scripts must be free of D:\\ocn hardcoded paths."""

    @pytest.mark.parametrize("script_name", P0_SCRIPTS)
    def test_p0_script_no_hardcoded_docn(self, script_name):
        script_path = SCRIPTS_DIR / script_name
        if not script_path.exists():
            pytest.skip(f"script not found: {script_name}")
        content = script_path.read_text(encoding="utf-8", errors="ignore")

        if script_name in SCANNER_SCRIPTS:
            # Scanner scripts legitimately contain "D:\ocn" as a string
            # literal for detection. Verify that ALL occurrences are in
            # string-literal/scanner/comment context, not as actual
            # Path() arguments.
            bad_lines = []
            for i, line in enumerate(content.splitlines(), 1):
                if HARDCODED_RE.search(line):
                    stripped = line.strip()
                    # Allow comments
                    if stripped.startswith("#"):
                        continue
                    # Allow string-literal detection code
                    if ('"D:\\ocn"' in stripped or "'D:\\ocn'" in stripped
                            or '"D:/ocn"' in stripped or "'D:/ocn'" in stripped
                            or 'in content' in stripped or 'count(' in stripped
                            or 'in content or' in stripped):
                        continue
                    bad_lines.append(f"L{i}: {stripped}")
            assert not bad_lines, (
                f"{script_name} has non-scanner D:\\ocn hardcoding:\n"
                + "\n".join(bad_lines)
            )
        else:
            matches = HARDCODED_RE.findall(content)
            assert not matches, (
                f"{script_name} contains {len(matches)} D:\\ocn hardcoded path(s)"
            )

    def test_p0_scripts_support_config_arg(self):
        """P0 scripts that have argparse should accept --config."""
        scripts_with_main = [
            "run_simclaim_pdf_retrieval_v1.py",
            "run_r4_evidence_canonicalization_v1.py",
            "run_canonicalized_review_queue_v1.py",
            "run_canonicalized_risk_ranking_v1.py",
        ]
        for name in scripts_with_main:
            script_path = SCRIPTS_DIR / name
            if not script_path.exists():
                continue
            content = script_path.read_text(encoding="utf-8", errors="ignore")
            assert "--config" in content, (
                f"{name} does not support --config argument"
            )
            assert "--repo_root" in content, (
                f"{name} does not support --repo_root argument"
            )
            assert "--output_dir" in content, (
                f"{name} does not support --output_dir argument"
            )


class TestAuditReport:
    def test_audit_md_exists(self):
        assert AUDIT_MD.exists(), f"audit report missing: {AUDIT_MD}"

    def test_audit_csv_exists(self):
        assert AUDIT_CSV.exists(), f"audit CSV missing: {AUDIT_CSV}"

    def test_audit_md_shows_zero_blockers(self):
        text = AUDIT_MD.read_text(encoding="utf-8")
        match = re.search(
            r"current_pipeline_blocker\s*\|\s*(\d+)\s*\|", text
        )
        assert match, "audit MD missing current_pipeline_blocker row"
        assert int(match.group(1)) == 0, (
            f"audit shows current_pipeline_blocker = {match.group(1)}, expected 0"
        )

    def test_audit_csv_no_blockers(self):
        with AUDIT_CSV.open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        blockers = [r for r in rows if r["classification"] == "current_pipeline_blocker"]
        assert not blockers, (
            f"audit CSV has {len(blockers)} current_pipeline_blocker rows"
        )

    def test_audit_csv_classifications_valid(self):
        valid = {"safe", "legacy_exempt", "current_pipeline_warning", "current_pipeline_blocker"}
        with AUDIT_CSV.open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        assert rows, "audit CSV is empty"
        for row in rows:
            assert row["classification"] in valid, (
                f"invalid classification '{row['classification']}' in {row['path']}"
            )

    def test_exemptions_doc_exists(self):
        assert EXEMPTIONS_DOC.exists(), (
            f"exemptions doc missing: {EXEMPTIONS_DOC}"
        )

    def test_exemptions_doc_lists_legacy_scripts(self):
        text = EXEMPTIONS_DOC.read_text(encoding="utf-8")
        assert "legacy_exempt" in text or "legacy" in text.lower()
        assert "V3.1" in text or "V3.16" in text
        assert "simclaim_hardpair" in text or "simclaim_v4" in text.lower()


class TestToyPipelineInTempDir:
    """Verify that the toy pipeline can run from a non-repo working
    directory, proving that repo-root detection works and the pipeline
    does not depend on D:\\ocn being the CWD."""

    def test_toy_demo_runs_from_temp_cwd(self, tmp_path):
        """Run the toy end-to-end demo from a temp working directory.
        The demo uses config_utils.get_repo_root() to locate scripts, so
        it should work regardless of CWD."""
        demo_script = SCRIPTS_DIR / "run_toy_end_to_end_demo_v1.py"
        if not demo_script.exists():
            pytest.skip("toy demo script not found")

        result = subprocess.run(
            [PYTHON, str(demo_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=180,
            cwd=str(tmp_path),
        )
        assert result.returncode == 0, (
            f"toy demo failed from temp CWD (exit {result.returncode}):\n"
            f"stdout: {result.stdout[-800:]}\n"
            f"stderr: {result.stderr[-800:]}"
        )
