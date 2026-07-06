"""Tests for the release bundle manifest (spec P2).

Verifies that:
  * RESULTS_MANIFEST.json contains the required top-level fields:
    dataset_hash, config_hash, checkpoint_hash, paper_ready,
    required_results_complete, missing_required_results, tables, figures.
  * The manifest never contains bare NaN/Inf tokens (invalid JSON).
  * Checkpoints (.pt), logs (.log) and cache dirs are NOT copied into
    the release bundle.
  * required_results_complete is False when required tables are missing
    or when paper_ready is False.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_release_bundle import (
    EXCLUDED_SUFFIXES,
    _is_excluded,
    build_manifest,
)


def _make_results_dir(tmp_path: Path) -> Path:
    """Create a minimal results dir with tables/ and figures/."""
    results = tmp_path / "results"
    tables = results / "tables"
    figures = results / "figures"
    tables.mkdir(parents=True)
    figures.mkdir(parents=True)
    # Write a minimal CSV table.
    (tables / "main_results.csv").write_text("name,score\nfoo,0.9\n", encoding="utf-8")
    (tables / "main_results.md").write_text("# Main Results\n\n| name | score |\n", encoding="utf-8")
    # Write a minimal figure.
    (figures / "calibration_curve.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    return results


def _make_data_file(tmp_path: Path) -> Path:
    data = tmp_path / "data.jsonl"
    data.write_text('{"sample_id": "s1"}\n', encoding="utf-8")
    return data


def _make_config_file(tmp_path: Path) -> Path:
    cfg = tmp_path / "config.yaml"
    cfg.write_text("seed: 42\n", encoding="utf-8")
    return cfg


def _write_completion_fixtures(results: Path) -> None:
    """Write minimal baseline + ablation fixtures so the readiness gate
    (baseline / calibration / constraint completion) does not force
    paper_ready=False. Lets a test focus on the required_results_complete
    or oracle-triples logic rather than the ablation gate. Matches the
    variant labels checked by CALIBRATION_REQUIRED_VARIANTS and
    CONSTRAINT_REQUIRED_VARIANTS in build_release_bundle.py."""
    import json as _json
    baselines_dir = results / "baselines"
    baselines_dir.mkdir(parents=True, exist_ok=True)
    (baselines_dir / "baselines_results.json").write_text(
        _json.dumps({"missing_required_results": []}), encoding="utf-8"
    )
    tables = results / "tables"
    # ocn-35 P1: variant names must match CALIBRATION_REQUIRED_VARIANTS /
    # CONSTRAINT_REQUIRED_VARIANTS in build_release_bundle.py (case-
    # insensitive substring match on the table text).
    (tables / "calibration_ablation.csv").write_text(
        "calibration\n"
        "no calibration\n"
        "separate thresholds\n"
        "shared-threshold ordinal calibration\n"
        "temperature scaling\n"
        "isotonic calibration\n",
        encoding="utf-8",
    )
    (tables / "constraint_ablation.csv").write_text(
        "constraint\n"
        "no constraint\n"
        "monotonicity only\n"
        "soft gate\n"
        "hard truncation (renormalize)\n"
        "hard truncation (route review)\n"
        "full cese-ocn\n",
        encoding="utf-8",
    )


def test_manifest_has_required_top_level_fields(tmp_path):
    """RESULTS_MANIFEST.json must contain all P2 required fields."""
    results = _make_results_dir(tmp_path)
    data = _make_data_file(tmp_path)
    config = _make_config_file(tmp_path)

    manifest = build_manifest(
        results_dir=results,
        data_path=data,
        config_path=config,
        checkpoint_path=None,
        seed=42,
        tables=["main_results"],
        figures=["calibration_curve"],
    )
    required_keys = {
        "dataset_hash",
        "config_hash",
        "checkpoint_hash",
        "paper_ready",
        "required_results_complete",
        "missing_required_results",
        "tables",
        "figures",
    }
    assert required_keys.issubset(set(manifest.keys())), (
        f"Missing manifest keys: {required_keys - set(manifest.keys())}"
    )
    # dataset_hash and config_hash must be non-None when paths are provided.
    assert manifest["dataset_hash"] is not None
    assert manifest["config_hash"] is not None
    # checkpoint_hash must be None when no checkpoint is provided.
    assert manifest["checkpoint_hash"] is None


def test_manifest_no_bare_nan(tmp_path):
    """The manifest JSON must not contain bare NaN/Inf tokens."""
    from cese.utils.io import write_json

    results = _make_results_dir(tmp_path)
    manifest = build_manifest(
        results_dir=results,
        data_path=None,
        config_path=None,
        checkpoint_path=None,
        seed=42,
        tables=["main_results"],
        figures=["calibration_curve"],
    )
    # Inject a NaN to verify sanitization.
    manifest["test_nan"] = float("nan")
    manifest["test_inf"] = float("inf")
    manifest["nested"] = {"val": float("nan"), "list": [float("nan"), 1.0]}
    out_path = tmp_path / "RESULTS_MANIFEST.json"
    write_json(manifest, out_path)
    raw = out_path.read_text(encoding="utf-8")
    # Must not contain bare NaN or Infinity tokens.
    assert "NaN" not in raw, "Manifest contains bare NaN token"
    assert "Infinity" not in raw, "Manifest contains bare Infinity token"
    # Must be valid JSON (parseable by strict json.load).
    parsed = json.loads(raw)
    assert parsed["test_nan"] is None
    assert parsed["test_inf"] is None
    assert parsed["nested"]["val"] is None
    assert parsed["nested"]["list"][0] is None


def test_required_results_complete_false_when_table_missing(tmp_path):
    """required_results_complete must be False when a required table is
    missing (recorded in missing_required_results)."""
    results = _make_results_dir(tmp_path)
    manifest = build_manifest(
        results_dir=results,
        data_path=None,
        config_path=None,
        checkpoint_path=None,
        seed=42,
        tables=["main_results", "calibration_ablation"],  # calibration_ablation missing
        figures=["calibration_curve"],
    )
    assert "tables/calibration_ablation" in manifest["missing_required_results"]
    assert manifest["required_results_complete"] is False


def test_required_results_complete_false_when_paper_ready_false(tmp_path):
    """required_results_complete must be False when paper_ready is False
    even if all tables exist (no report_metadata.json -> paper_ready=False)."""
    results = _make_results_dir(tmp_path)
    manifest = build_manifest(
        results_dir=results,
        data_path=None,
        config_path=None,
        checkpoint_path=None,
        seed=42,
        tables=["main_results"],
        figures=["calibration_curve"],
    )
    # paper_ready defaults to False (no audit report, no report_metadata).
    assert manifest["paper_ready"] is False
    assert manifest["required_results_complete"] is False


def test_required_results_complete_true_when_paper_ready_and_no_missing(tmp_path):
    """required_results_complete must be True only when paper_ready is True
    AND no required results are missing AND report_metadata says complete
    AND oracle triples are complete."""
    results = _make_results_dir(tmp_path)
    # Write a report_metadata.json with paper_ready=True and
    # required_results_complete=True.
    import json as _json
    meta = {
        "paper_ready": True,
        "required_results_complete": True,
        "report_mode": "paper_full",
    }
    (results / "tables" / "report_metadata.json").write_text(
        _json.dumps(meta), encoding="utf-8"
    )
    # P2: write a valid oracle/extracted comparison_results.json so the
    # oracle triples completeness check passes.
    oracle_dir = results / "oracle_extracted"
    oracle_dir.mkdir(parents=True, exist_ok=True)
    (oracle_dir / "comparison_results.json").write_text(
        _json.dumps({
            "same_model_same_samples": {
                "same_model_same_samples_valid": True,
                "n_logical_samples": 3,
            }
        }),
        encoding="utf-8",
    )
    _write_completion_fixtures(results)
    manifest = build_manifest(
        results_dir=results,
        data_path=None,
        config_path=None,
        checkpoint_path=None,
        seed=42,
        tables=["main_results"],
        figures=["calibration_curve"],
    )
    assert manifest["paper_ready"] is True
    assert manifest["required_results_complete"] is True


def test_required_results_complete_false_when_meta_says_incomplete(tmp_path):
    """required_results_complete must be False when report_metadata says
    incomplete (e.g. BLOCKING WARNING in ablation table), even if
    paper_ready is True."""
    results = _make_results_dir(tmp_path)
    import json as _json
    meta = {
        "paper_ready": True,
        "required_results_complete": False,
        "report_mode": "paper_full",
    }
    (results / "tables" / "report_metadata.json").write_text(
        _json.dumps(meta), encoding="utf-8"
    )
    _write_completion_fixtures(results)
    manifest = build_manifest(
        results_dir=results,
        data_path=None,
        config_path=None,
        checkpoint_path=None,
        seed=42,
        tables=["main_results"],
        figures=["calibration_curve"],
    )
    assert manifest["paper_ready"] is True
    assert manifest["required_results_complete"] is False


def test_required_results_complete_false_when_oracle_triples_missing(tmp_path):
    """required_results_complete must be False when the oracle/extracted
    comparison_results.json is missing (incomplete triples)."""
    results = _make_results_dir(tmp_path)
    import json as _json
    meta = {
        "paper_ready": True,
        "required_results_complete": True,
        "report_mode": "paper_full",
    }
    (results / "tables" / "report_metadata.json").write_text(
        _json.dumps(meta), encoding="utf-8"
    )
    # Do NOT write oracle_extracted/comparison_results.json.
    _write_completion_fixtures(results)
    manifest = build_manifest(
        results_dir=results,
        data_path=None,
        config_path=None,
        checkpoint_path=None,
        seed=42,
        tables=["main_results"],
        figures=["calibration_curve"],
    )
    assert manifest["paper_ready"] is True
    assert manifest["required_results_complete"] is False
    assert any(
        "oracle_extracted" in r for r in manifest["missing_required_results"]
    ), "missing oracle triples should be recorded"


def test_required_results_complete_false_when_oracle_triples_incomplete(tmp_path):
    """required_results_complete must be False when the oracle comparison
    exists but same_model_same_samples_valid is False or n_logical_samples
    is 0."""
    results = _make_results_dir(tmp_path)
    import json as _json
    meta = {
        "paper_ready": True,
        "required_results_complete": True,
        "report_mode": "paper_full",
    }
    (results / "tables" / "report_metadata.json").write_text(
        _json.dumps(meta), encoding="utf-8"
    )
    oracle_dir = results / "oracle_extracted"
    oracle_dir.mkdir(parents=True, exist_ok=True)
    # n_logical_samples=0 -> incomplete.
    (oracle_dir / "comparison_results.json").write_text(
        _json.dumps({
            "same_model_same_samples": {
                "same_model_same_samples_valid": True,
                "n_logical_samples": 0,
            }
        }),
        encoding="utf-8",
    )
    manifest = build_manifest(
        results_dir=results,
        data_path=None,
        config_path=None,
        checkpoint_path=None,
        seed=42,
        tables=["main_results"],
        figures=["calibration_curve"],
    )
    assert manifest["required_results_complete"] is False


def test_report_metadata_path_recorded(tmp_path):
    """manifest must record the path to report_metadata.json."""
    results = _make_results_dir(tmp_path)
    import json as _json
    # Write to the canonical outputs/report/report_metadata.json location.
    report_dir = results / "report"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "report_metadata.json").write_text(
        _json.dumps({"paper_ready": True, "required_results_complete": True}),
        encoding="utf-8",
    )
    # Also write a valid oracle comparison.
    oracle_dir = results / "oracle_extracted"
    oracle_dir.mkdir(parents=True, exist_ok=True)
    (oracle_dir / "comparison_results.json").write_text(
        _json.dumps({
            "same_model_same_samples": {
                "same_model_same_samples_valid": True,
                "n_logical_samples": 3,
            }
        }),
        encoding="utf-8",
    )
    manifest = build_manifest(
        results_dir=results,
        data_path=None,
        config_path=None,
        checkpoint_path=None,
        seed=42,
        tables=["main_results"],
        figures=["calibration_curve"],
    )
    assert manifest["report_metadata_path"] is not None
    assert "report_metadata.json" in manifest["report_metadata_path"]


def test_excluded_suffixes_not_copied():
    """Files with excluded suffixes (.pt, .log, etc.) must not be copied."""
    for suffix in [".pt", ".ckpt", ".bin", ".log", ".pyc"]:
        p = Path(f"foo{suffix}")
        assert _is_excluded(p), f"{suffix} should be excluded"


def test_excluded_dirs_not_copied():
    """Files in __pycache__ etc. must not be copied."""
    p = Path("__pycache__") / "module.pyc"
    assert _is_excluded(p)


def test_non_excluded_files_pass():
    """CSV, MD, PNG, JSON files must NOT be excluded."""
    for suffix in [".csv", ".md", ".png", ".json", ".txt"]:
        p = Path(f"results{suffix}")
        assert not _is_excluded(p), f"{suffix} should not be excluded"


# ---------------------------------------------------------------------------
# P4b: data_audit summary + toy/template markers
# ---------------------------------------------------------------------------


def test_manifest_includes_data_audit_summary(tmp_path):
    """Manifest must include a data_audit_summary block when
    data_audit.json exists."""
    results = _make_results_dir(tmp_path)
    import json as _json
    _write_json(results / "data_audit.json", {
        "paper_ready": {
            "paper_ready": True,
            "blocking_errors": [],
            "warnings": ["minor"],
            "counts": {"n_total": 100, "n_complete_triples": 50},
        }
    })
    manifest = build_manifest(
        results_dir=results,
        data_path=None,
        config_path=None,
        checkpoint_path=None,
        seed=42,
        tables=["main_results"],
        figures=["calibration_curve"],
    )
    assert "data_audit_summary" in manifest
    audit = manifest["data_audit_summary"]
    assert audit["paper_ready"] is True
    assert audit["counts"]["n_total"] == 100
    assert audit["warnings"] == ["minor"]


def test_manifest_forces_paper_ready_false_for_toy_data(tmp_path):
    """Manifest must force paper_ready=False when data_path contains
    toy/smoke/pilot_template markers."""
    results = _make_results_dir(tmp_path)
    data = tmp_path / "toy" / "smoke.jsonl"
    data.parent.mkdir(parents=True)
    data.write_text('{"sample_id": "s1"}\n', encoding="utf-8")
    manifest = build_manifest(
        results_dir=results,
        data_path=data,
        config_path=None,
        checkpoint_path=None,
        seed=42,
        tables=["main_results"],
        figures=["calibration_curve"],
    )
    assert manifest["uses_toy_or_template_data"] is True
    assert manifest["paper_ready"] is False
    assert "toy_or_template_markers" in manifest
    assert any("toy" in m or "smoke" in m for m in manifest["toy_or_template_markers"])
    assert any(
        "toy/smoke/pilot_template" in m
        for m in manifest["missing_required_results"]
    )


def test_manifest_forces_paper_ready_false_for_pilot_template(tmp_path):
    """Manifest must force paper_ready=False for pilot_template data."""
    results = _make_results_dir(tmp_path)
    data = tmp_path / "pilot_template.jsonl"
    data.write_text('{"sample_id": "s1"}\n', encoding="utf-8")
    manifest = build_manifest(
        results_dir=results,
        data_path=data,
        config_path=None,
        checkpoint_path=None,
        seed=42,
        tables=["main_results"],
        figures=["calibration_curve"],
    )
    assert manifest["uses_toy_or_template_data"] is True
    assert manifest["paper_ready"] is False
    assert "pilot_template" in manifest["toy_or_template_markers"]


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
