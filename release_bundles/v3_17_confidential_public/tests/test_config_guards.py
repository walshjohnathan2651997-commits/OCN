"""Tests: config system guards and path resolution.

Verifies that:
  - configs are loadable
  - forbidden_scoring_fields are present in every config
  - no_api / no_network / no_training are True in every config
  - assert_confidential_guards raises ValueError when a guard is False
  - toy_demo.yaml can run the toy pipeline (end-to-end demo)
  - new scripts do not contain hardcoded D:\ocn paths
  - run_config.json is written to output dirs
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIGS_DIR = REPO_ROOT / "configs"

CONFIG_FILES = [
    CONFIGS_DIR / "v3_17_confidential_default.yaml",
    CONFIGS_DIR / "toy_demo.yaml",
    CONFIGS_DIR / "local_private_template.yaml",
]

REQUIRED_CONFIG_KEYS = [
    "project_root",
    "private_pdf_dir",
    "candidate_csv",
    "pdf_corpus_dir",
    "retrieval_dir",
    "canonicalizer_dir",
    "review_queue_dir",
    "risk_ranking_dir",
    "smart_queue_dir",
    "leakage_audit_dir",
    "toy_data_dir",
]

REQUIRED_GUARDS = ["no_api", "no_network", "no_training"]

EXPECTED_FORBIDDEN_FIELDS = [
    "true_label", "is_strong_action", "oracle_hit",
    "candidate_label_guess", "final_label", "gold_label",
    "human_audited", "evidence_text", "evidence_text_sha256",
]

# Scripts that should NOT have hardcoded D:\ocn paths (new scripts from task packs 3-6 + config_utils)
NEW_SCRIPTS = [
    "scripts/run_bm25_sentence_retrieval_v1.py",
    "scripts/run_canonicalizer_ablation_v1.py",
    "scripts/run_format_shift_ablation_v1.py",
    "scripts/evaluate_r4_on_evidence_variants_v1.py",
    "scripts/run_lightweight_smart_queue_v1.py",
    "scripts/run_leakage_audit_v1.py",
    "scripts/run_toy_end_to_end_demo_v1.py",
    "scripts/lib/config_utils.py",
]


def _lib_path():
    """Get the scripts/lib path for imports."""
    return str(REPO_ROOT / "scripts" / "lib")


class TestConfigLoading:
    """Configs must be loadable and contain all required keys."""

    @pytest.mark.parametrize("config_path", CONFIG_FILES)
    def test_config_exists(self, config_path):
        assert config_path.exists(), f"Config file missing: {config_path}"

    @pytest.mark.parametrize("config_path", CONFIG_FILES)
    def test_config_loadable(self, config_path):
        sys.path.insert(0, _lib_path())
        from config_utils import load_config
        config = load_config(str(config_path))
        assert config is not None
        assert isinstance(config, dict)

    @pytest.mark.parametrize("config_path", CONFIG_FILES)
    def test_config_has_required_keys(self, config_path):
        sys.path.insert(0, _lib_path())
        from config_utils import load_config
        config = load_config(str(config_path))
        for key in REQUIRED_CONFIG_KEYS:
            assert key in config, f"Config {config_path.name} missing key: {key}"
            assert config[key] is not None, f"Config {config_path.name} key '{key}' is None"


class TestForbiddenFields:
    """Every config must list all forbidden scoring fields."""

    @pytest.mark.parametrize("config_path", CONFIG_FILES)
    def test_forbidden_fields_present(self, config_path):
        sys.path.insert(0, _lib_path())
        from config_utils import load_config
        config = load_config(str(config_path))
        forbidden = config.get("forbidden_scoring_fields", [])
        for field in EXPECTED_FORBIDDEN_FIELDS:
            assert field in forbidden, \
                f"Config {config_path.name} missing forbidden field: {field}"


class TestConfidentialGuards:
    """no_api, no_network, no_training must all be True."""

    @pytest.mark.parametrize("config_path", CONFIG_FILES)
    def test_guards_are_true(self, config_path):
        sys.path.insert(0, _lib_path())
        from config_utils import load_config, assert_confidential_guards
        config = load_config(str(config_path))
        for guard in REQUIRED_GUARDS:
            assert config[guard] is True, \
                f"Config {config_path.name}: {guard} must be True, got {config[guard]}"
        # Should not raise
        assert_confidential_guards(config)

    def test_assert_raises_on_false_guard(self):
        sys.path.insert(0, _lib_path())
        from config_utils import assert_confidential_guards
        bad_config = {"no_api": False, "no_network": True, "no_training": True}
        with pytest.raises(ValueError, match="no_api"):
            assert_confidential_guards(bad_config)

    def test_assert_raises_on_missing_guard(self):
        sys.path.insert(0, _lib_path())
        from config_utils import assert_confidential_guards
        bad_config = {"no_network": True, "no_training": True}
        with pytest.raises(ValueError, match="no_api"):
            assert_confidential_guards(bad_config)


class TestPathResolution:
    """resolve_path should return absolute paths relative to project_root."""

    def test_resolve_path_relative(self):
        sys.path.insert(0, _lib_path())
        from config_utils import resolve_path
        config = {"project_root": ".", "smart_queue_dir": "experiments/smart_queue_v1"}
        result = resolve_path(config, "smart_queue_dir")
        assert result is not None
        assert result.is_absolute()

    def test_resolve_path_absolute(self):
        sys.path.insert(0, _lib_path())
        from config_utils import resolve_path
        # Use a guaranteed-absolute path on the current platform
        abs_path = str(Path.cwd() / "tmp_corpus")
        config = {"project_root": ".", "pdf_corpus_dir": abs_path}
        result = resolve_path(config, "pdf_corpus_dir")
        assert result is not None
        assert result.is_absolute()
        assert result == Path(abs_path)

    def test_resolve_path_missing_key(self):
        sys.path.insert(0, _lib_path())
        from config_utils import resolve_path
        config = {"project_root": "."}
        result = resolve_path(config, "nonexistent_key")
        assert result is None


class TestNoHardcodedPaths:
    """New scripts must not contain hardcoded D:\\ocn paths."""

    @pytest.mark.parametrize("script_rel", NEW_SCRIPTS)
    def test_no_hardcoded_docn(self, script_rel):
        script_path = REPO_ROOT / script_rel
        assert script_path.exists(), f"Script not found: {script_rel}"
        source = script_path.read_text(encoding="utf-8")
        # Check for D:\ocn or D:/ocn (case-insensitive on the drive letter)
        assert "D:\\ocn" not in source, \
            f"{script_rel} contains hardcoded D:\\ocn path"
        assert "D:/ocn" not in source, \
            f"{script_rel} contains hardcoded D:/ocn path"
        assert "d:\\ocn" not in source.lower(), \
            f"{script_rel} contains hardcoded d:\\ocn path"


class TestToyDemoConfig:
    """toy_demo.yaml must be able to run the toy pipeline."""

    def test_toy_config_loadable_and_valid(self):
        sys.path.insert(0, _lib_path())
        from config_utils import load_and_validate
        config = load_and_validate(str(CONFIGS_DIR / "toy_demo.yaml"), toy_mode=True)
        assert config["no_api"] is True
        assert config["no_network"] is True
        assert config["no_training"] is True

    def test_toy_demo_produces_run_config(self):
        """Toy demo output dir must contain run_config.json."""
        run_config_path = REPO_ROOT / "experiments" / "toy_end_to_end_demo_v1" / "run_config.json"
        if not run_config_path.exists():
            # Run the toy demo
            cmd = [sys.executable, str(REPO_ROOT / "scripts" / "run_toy_end_to_end_demo_v1.py")]
            subprocess.run(
                cmd, cwd=str(REPO_ROOT),
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=600,
            )
        assert run_config_path.exists(), "run_config.json not produced by toy demo"
        with open(run_config_path, "r", encoding="utf-8") as f:
            rc = json.load(f)
        assert rc["script_name"] == "run_toy_end_to_end_demo_v1.py"
        assert rc["guards"]["no_api"] is True
        assert rc["guards"]["no_network"] is True
        assert rc["guards"]["no_training"] is True

    def test_smart_queue_run_config_exists(self):
        """SmartQueue output dir must contain run_config.json."""
        run_config_path = REPO_ROOT / "experiments" / "lightweight_smart_queue_v1_toy" / "run_config.json"
        if not run_config_path.exists():
            cmd = [
                sys.executable,
                str(REPO_ROOT / "scripts" / "run_lightweight_smart_queue_v1.py"),
                "--toy_mode",
            ]
            subprocess.run(
                cmd, cwd=str(REPO_ROOT),
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=120,
            )
        assert run_config_path.exists(), "run_config.json not produced by SmartQueue"
        with open(run_config_path, "r", encoding="utf-8") as f:
            rc = json.load(f)
        assert "forbidden_scoring_fields" in rc
        forbidden = set(rc["forbidden_scoring_fields"])
        for field in EXPECTED_FORBIDDEN_FIELDS:
            assert field in forbidden, f"{field} missing from run_config forbidden_scoring_fields"
