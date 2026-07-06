"""Tests that the release was regenerated from clean_v2 data (ocn-33 P2-7).

Verifies ``release/RESULTS_MANIFEST.json`` reflects the clean_v2 release:
  * ``data_path`` / ``data_version`` point to clean_v2.
  * ``n_train`` / ``n_validation`` / ``n_test`` are 48 / 16 / 16.
  * ``paper_ready`` is False (pilot pipeline validation only).
  * ``blocking_reasons`` is non-empty.
  * ``test_threshold_tuning_used`` is False.
  * ``predictions_path`` is set and points to test_predictions.jsonl.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MANIFEST_PATH = ROOT / "release" / "RESULTS_MANIFEST.json"


@pytest.fixture(scope="module")
def manifest() -> dict:
    """Load the release manifest once for all tests in this module."""
    if not MANIFEST_PATH.exists():
        pytest.skip(
            f"release manifest not found at {MANIFEST_PATH}; "
            "run scripts/run_release_pipeline.py first"
        )
    with MANIFEST_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def test_data_path_points_to_clean_v2(manifest: dict):
    """data_path / dataset.path must reference clean_v2."""
    data_path = manifest.get("data_path", "")
    assert "clean_v2" in str(data_path), (
        f"data_path should reference clean_v2, got: {data_path!r}"
    )
    dataset = manifest.get("dataset", {}) or {}
    assert "clean_v2" in str(dataset.get("path", "")), (
        f"dataset.path should reference clean_v2, got: {dataset.get('path')!r}"
    )


def test_data_version_is_clean_v2(manifest: dict):
    """data_version field must be 'clean_v2'."""
    assert manifest.get("data_version") == "clean_v2", (
        f"data_version should be 'clean_v2', got: {manifest.get('data_version')!r}"
    )


def test_config_path_points_to_clean_v2(manifest: dict):
    """config path must reference model_clean_v2.yaml, not the legacy config."""
    config = manifest.get("config", {}) or {}
    cfg_path = str(config.get("path", ""))
    assert "model_clean_v2" in cfg_path, (
        f"config.path should reference model_clean_v2.yaml, got: {cfg_path!r}"
    )
    # Explicitly forbid the legacy config name.
    assert "model_cese_ocn.yaml" not in cfg_path.lower(), (
        f"config.path must not be the legacy model_cese_ocn.yaml: {cfg_path!r}"
    )


def test_split_counts_are_48_16_16(manifest: dict):
    """n_train / n_validation / n_test must be 48 / 16 / 16."""
    assert manifest.get("n_train") == 48, (
        f"n_train should be 48, got: {manifest.get('n_train')}"
    )
    assert manifest.get("n_validation") == 16, (
        f"n_validation should be 16, got: {manifest.get('n_validation')}"
    )
    assert manifest.get("n_test") == 16, (
        f"n_test should be 16, got: {manifest.get('n_test')}"
    )


def test_paper_ready_is_false(manifest: dict):
    """paper_ready must be False (pilot pipeline validation only)."""
    assert manifest.get("paper_ready") is False, (
        "paper_ready must be False; clean_v2 is a pilot dataset "
        "(n=80, human_audited=0, contradiction_positive=0)"
    )


def test_blocking_reasons_is_non_empty(manifest: dict):
    """blocking_reasons must be non-empty (pilot has known gaps)."""
    reasons = manifest.get("blocking_reasons", [])
    assert isinstance(reasons, list) and len(reasons) > 0, (
        "blocking_reasons must be non-empty for the pilot release"
    )


def test_blocking_reasons_include_required_items(manifest: dict):
    """blocking_reasons must include the known pilot limitations."""
    reasons = manifest.get("blocking_reasons", [])
    joined = " ".join(reasons).lower()
    # Must mention human_audited_count=0.
    assert "human_audited_count=0" in joined, (
        f"blocking_reasons must mention human_audited_count=0: {reasons}"
    )
    # Must mention contradiction_positive_count=0.
    assert "contradiction_positive_count=0" in joined, (
        f"blocking_reasons must mention contradiction_positive_count=0: {reasons}"
    )
    # Must mention test size too small.
    assert "test size too small" in joined, (
        f"blocking_reasons must mention test size too small: {reasons}"
    )
    # Must mention source_type all oracle.
    assert "source_type all oracle" in joined, (
        f"blocking_reasons must mention source_type all oracle: {reasons}"
    )


def test_test_threshold_tuning_used_is_false(manifest: dict):
    """test_threshold_tuning_used must be False (no test-set threshold tuning)."""
    assert manifest.get("test_threshold_tuning_used") is False, (
        "test_threshold_tuning_used must be False; the operating threshold "
        "is fit on dev only, never tuned on test"
    )


def test_predictions_path_is_set(manifest: dict):
    """predictions_path must be set and point to test_predictions.jsonl."""
    pp = manifest.get("predictions_path")
    assert pp, "predictions_path must be set in the manifest"
    assert "test_predictions.jsonl" in str(pp), (
        f"predictions_path should point to test_predictions.jsonl, got: {pp!r}"
    )


def test_operating_threshold_matches_best_threshold_on_dev(manifest: dict):
    """operating_threshold must equal best_threshold_on_dev (same dev-fit value)."""
    op = manifest.get("operating_threshold")
    best_dev = manifest.get("best_threshold_on_dev")
    assert op is not None and best_dev is not None, (
        "operating_threshold and best_threshold_on_dev must both be set"
    )
    assert op == best_dev, (
        f"operating_threshold ({op}) must equal best_threshold_on_dev ({best_dev}); "
        "the operating threshold is the dev-fit threshold applied to test"
    )


def test_confidence_level_is_pilot_only(manifest: dict):
    """confidence_level must be 'pilot_only' (n_test=16 < 30)."""
    cl = manifest.get("confidence_level")
    assert cl == "pilot_only", (
        f"confidence_level should be 'pilot_only' for n_test=16, got: {cl!r}"
    )


def test_source_type_counts_all_oracle(manifest: dict):
    """source_type_counts must show all 80 samples are oracle (pilot limit)."""
    stc = manifest.get("source_type_counts", {})
    assert stc.get("oracle") == 80, (
        f"source_type_counts.oracle should be 80, got: {stc}"
    )
    # No extracted / confidence_aware samples.
    assert "extracted" not in stc, (
        f"pilot data should not have extracted samples: {stc}"
    )
    assert "confidence_aware" not in stc, (
        f"pilot data should not have confidence_aware samples: {stc}"
    )


def test_manifest_registers_release_tables_and_figures(manifest: dict):
    """Manifest must not claim shipped tables/figures are missing.

    run_release_pipeline.py must write generated tables/figures into the
    canonical results dir first, then build_release_bundle.py copies them
    into release/ and hashes them in RESULTS_MANIFEST.json. Otherwise the
    release can become internally contradictory: release/tables/*.md
    exists, but manifest.tables is empty and RELEASE_STATUS.md reports
    those same tables as missing.
    """
    required_tables = {
        "main_results",
        "oracle_extracted_confidence",
        "calibration_ablation",
        "constraint_ablation",
        "mapping_ablation",
        "adversarial_results",
        "llm_stability",
    }
    required_figures = {
        "calibration_curve",
        "threshold_sensitivity",
        "oracle_extracted_gap",
        "adversarial_drop",
        "monotonic_violation",
    }
    tables = manifest.get("tables", {}) or {}
    figures = manifest.get("figures", {}) or {}
    assert required_tables.issubset(tables.keys()), (
        f"manifest.tables missing shipped tables: "
        f"{sorted(required_tables - set(tables.keys()))}"
    )
    assert required_figures.issubset(figures.keys()), (
        f"manifest.figures missing shipped figures: "
        f"{sorted(required_figures - set(figures.keys()))}"
    )
    missing = manifest.get("missing_required_results", []) or []
    forbidden_missing = [
        x for x in missing
        if x.startswith("tables/") or x.startswith("figures/")
    ]
    assert forbidden_missing == [], (
        "manifest must not report tables/figures as missing when they are "
        f"shipped and hashed: {forbidden_missing}"
    )


def test_copied_files_records_release_tables(manifest: dict):
    """copied_files.tables must include generated table artifacts."""
    copied = manifest.get("copied_files", {}) or {}
    copied_tables = copied.get("tables", []) or []
    assert any(str(x).endswith("main_results.md") for x in copied_tables), (
        f"copied_files.tables should include main_results.md, got {copied_tables}"
    )
    assert any(str(x).endswith("calibration_ablation.md") for x in copied_tables), (
        "copied_files.tables should include calibration_ablation.md"
    )
    assert any(str(x).endswith("constraint_ablation.md") for x in copied_tables), (
        "copied_files.tables should include constraint_ablation.md"
    )
