"""Tests for P4-10 / P4-11 / P4-12: pilot diagnostic, rule baseline
diagnostic-only, and stricter paper readiness gate.

Covers:
- profile=pilot -> CESE-OCN row paper_valid=false / metric_valid=false.
- rule baseline -> paper_valid=false / result_scope=diagnostic_upper_bound.
- generate_tables refuses --allow_toy_results with paper_full.
- check_paper_readiness blocks on:
  * toy/smoke/template data path
  * missing operating_threshold_state
  * rule baseline paper_valid=true
- --pilot_ok does not change paper_ready=false.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generate_tables import build_main_results
from scripts.check_paper_readiness import check_paper_readiness


def _eval_report(binary=True):
    return {
        "binary": {
            "accuracy": 0.8,
            "macro_f1": 0.75,
            "escalation_f1": 0.7,
        },
        "calibration": {"ece": 0.05},
        "high_strength_false_support_rate": 0.1,
        "evidence_gap_f1": 0.6,
        "ordinal_calibration_error": 0.04,
    }


# ---------------------------------------------------------------------------
# P4-10: pilot profile marks CESE-OCN paper_valid=false
# ---------------------------------------------------------------------------

def test_pilot_profile_marks_cese_paper_valid_false(tmp_path):
    results_dir = tmp_path / "results"
    (results_dir).mkdir(parents=True)
    (results_dir / "eval_test.json").write_text(
        json.dumps(_eval_report()), encoding="utf-8"
    )
    # No baselines file -> only CESE-OCN full row.
    rows = build_main_results(results_dir, profile="pilot")
    cese_rows = [r for r in rows if r["model"] == "cese_ocn_full"]
    assert len(cese_rows) == 1
    assert cese_rows[0]["paper_valid"] is False
    # ocn-41 task 7: metric_valid reflects real metrics, not paper_valid.
    # Pilot CESE with real metrics has metric_valid=True but paper_valid=False.
    assert cese_rows[0]["metric_valid"] is True
    assert cese_rows[0]["result_scope"] == "pilot_diagnostic"


def test_paper_full_profile_cese_can_be_paper_valid(tmp_path):
    results_dir = tmp_path / "results"
    (results_dir).mkdir(parents=True)
    (results_dir / "eval_test.json").write_text(
        json.dumps(_eval_report()), encoding="utf-8"
    )
    rows = build_main_results(results_dir, profile="paper_full")
    cese_rows = [r for r in rows if r["model"] == "cese_ocn_full"]
    assert len(cese_rows) == 1
    assert cese_rows[0]["paper_valid"] is True
    assert cese_rows[0]["metric_valid"] is True
    assert cese_rows[0]["result_scope"] == "paper_full_main"


# ---------------------------------------------------------------------------
# P4-11: rule baseline is always diagnostic
# ---------------------------------------------------------------------------

def test_rule_baseline_is_always_diagnostic(tmp_path):
    """Rule baseline must be paper_valid=False / metric_valid=False /
    result_scope=diagnostic_upper_bound regardless of legacy JSON."""
    results_dir = tmp_path / "results"
    (results_dir / "baselines").mkdir(parents=True)
    # Legacy baselines_results.json that falsely claims paper_valid=True
    # for rule_baseline. P4-11 must override this.
    baselines = {
        "rule_baseline": {
            "accuracy": 0.9,
            "macro_f1": 0.88,
            "escalation_f1": 0.85,
            "paper_valid": True,  # legacy wrong value
            "metric_valid": True,  # legacy wrong value
            "uses_gold_tiers": False,  # legacy missing
        },
    }
    (results_dir / "baselines" / "baselines_results.json").write_text(
        json.dumps(baselines), encoding="utf-8"
    )
    rows = build_main_results(results_dir, profile="paper_full")
    rule_rows = [r for r in rows if r["model"] == "Rule baseline"]
    # paper_full excludes paper_valid=False rows, so rule_baseline
    # should NOT appear in the main table.
    assert len(rule_rows) == 0


def test_rule_baseline_diagnostic_in_pilot(tmp_path):
    """In pilot profile, rule_baseline appears with diagnostic_upper_bound."""
    results_dir = tmp_path / "results"
    (results_dir / "baselines").mkdir(parents=True)
    baselines = {
        "rule_baseline": {
            "accuracy": 0.9,
            "macro_f1": 0.88,
            "escalation_f1": 0.85,
            "paper_valid": True,  # legacy wrong value
        },
    }
    (results_dir / "baselines" / "baselines_results.json").write_text(
        json.dumps(baselines), encoding="utf-8"
    )
    rows = build_main_results(results_dir, profile="pilot")
    rule_rows = [r for r in rows if r["model"] == "Rule baseline"]
    assert len(rule_rows) == 1
    assert rule_rows[0]["paper_valid"] is False
    assert rule_rows[0]["metric_valid"] is False
    assert rule_rows[0]["result_scope"] == "diagnostic_upper_bound"
    assert rule_rows[0]["uses_gold_tiers"] is True
    assert rule_rows[0]["prediction_source"] == "gold_tier_rule"


# ---------------------------------------------------------------------------
# P4-12: paper readiness blocks on missing operating threshold
# ---------------------------------------------------------------------------

def test_paper_readiness_blocks_on_missing_operating_threshold(tmp_path):
    """Without train_eval/train_eval_summary.json, paper readiness fails."""
    results_dir = tmp_path / "results"
    release_dir = tmp_path / "release"
    # Minimal data_audit.json claiming paper_ready
    (results_dir).mkdir(parents=True)
    (results_dir / "data_audit.json").write_text(
        json.dumps({"paper_ready": {"paper_ready": True}}), encoding="utf-8"
    )
    (release_dir).mkdir(parents=True)
    (release_dir / "RESULTS_MANIFEST.json").write_text(
        json.dumps({"paper_ready": True, "missing_required_results": []}),
        encoding="utf-8",
    )
    data_path = tmp_path / "cese_ocn.jsonl"
    data_path.write_text("dummy\n", encoding="utf-8")
    code = check_paper_readiness(results_dir, release_dir, data_path)
    assert code != 0  # blocked


def test_paper_readiness_blocks_on_toy_data(tmp_path):
    results_dir = tmp_path / "results"
    release_dir = tmp_path / "release"
    (results_dir).mkdir(parents=True)
    (results_dir / "data_audit.json").write_text(
        json.dumps({"paper_ready": {"paper_ready": True}}), encoding="utf-8"
    )
    (release_dir).mkdir(parents=True)
    (release_dir / "RESULTS_MANIFEST.json").write_text(
        json.dumps({"paper_ready": True, "missing_required_results": []}),
        encoding="utf-8",
    )
    # data_path contains "toy" marker.
    toy_path = tmp_path / "data" / "toy_data.jsonl"
    toy_path.parent.mkdir(parents=True)
    toy_path.write_text("dummy\n", encoding="utf-8")
    code = check_paper_readiness(results_dir, release_dir, toy_path)
    assert code != 0


def test_paper_readiness_blocks_on_smoke_template_data(tmp_path):
    """data_path with 'smoke' or 'template' in filename blocks."""
    results_dir = tmp_path / "results"
    release_dir = tmp_path / "release"
    (results_dir).mkdir(parents=True)
    (results_dir / "data_audit.json").write_text(
        json.dumps({"paper_ready": {"paper_ready": True}}), encoding="utf-8"
    )
    (release_dir).mkdir(parents=True)
    (release_dir / "RESULTS_MANIFEST.json").write_text(
        json.dumps({"paper_ready": True, "missing_required_results": []}),
        encoding="utf-8",
    )
    for marker in ("smoke_data.jsonl", "pilot_template.jsonl"):
        bad_path = tmp_path / marker
        bad_path.write_text("dummy\n", encoding="utf-8")
        code = check_paper_readiness(results_dir, release_dir, bad_path)
        assert code != 0, f"Expected block for {marker}"


# ---------------------------------------------------------------------------
# P4-12: --pilot_ok does NOT change paper_ready
# ---------------------------------------------------------------------------

def test_pilot_ok_does_not_change_paper_ready(tmp_path):
    """Even with pilot_ok=True, paper_ready must stay false when data
    is toy or threshold missing."""
    results_dir = tmp_path / "results"
    release_dir = tmp_path / "release"
    (results_dir).mkdir(parents=True)
    (results_dir / "data_audit.json").write_text(
        json.dumps({"paper_ready": {"paper_ready": True}}), encoding="utf-8"
    )
    (release_dir).mkdir(parents=True)
    (release_dir / "RESULTS_MANIFEST.json").write_text(
        json.dumps({"paper_ready": True, "missing_required_results": []}),
        encoding="utf-8",
    )
    toy_path = tmp_path / "data" / "toy.jsonl"
    toy_path.parent.mkdir(parents=True)
    toy_path.write_text("dummy\n", encoding="utf-8")
    code = check_paper_readiness(
        results_dir, release_dir, toy_path, pilot_ok=True
    )
    # Still blocked; pilot_ok is advisory only.
    assert code != 0


# ---------------------------------------------------------------------------
# P4-12: rule baseline paper_valid=true triggers blocking error
# ---------------------------------------------------------------------------

def test_rule_baseline_paper_valid_triggers_blocking(tmp_path):
    """A main_results.csv with a rule baseline paper_valid=true triggers
    a blocking error."""
    results_dir = tmp_path / "results"
    release_dir = tmp_path / "release"
    (results_dir / "tables").mkdir(parents=True)
    (results_dir / "train_eval").mkdir(parents=True)
    # Provide train_eval_summary.json with valid operating_threshold_state
    # so the gate doesn't block on the threshold check.
    thr_state_path = results_dir / "operating_threshold.json"
    thr_state_path.write_text(
        json.dumps({
            "selected_threshold": 0.35,
            "source_split": "dev",
            "test_split_used": False,
        }),
        encoding="utf-8",
    )
    (results_dir / "train_eval" / "train_eval_summary.json").write_text(
        json.dumps({
            "operating_threshold_state": str(thr_state_path),
            "operating_threshold_valid": True,
        }),
        encoding="utf-8",
    )
    # main_results.csv with a rule row paper_valid=true.
    csv = "model,uses_gold_tiers,paper_valid\nRule baseline,true,true\n"
    (results_dir / "tables" / "main_results.csv").write_text(csv, encoding="utf-8")
    (results_dir / "data_audit.json").write_text(
        json.dumps({"paper_ready": {"paper_ready": True}}), encoding="utf-8"
    )
    (release_dir).mkdir(parents=True)
    (release_dir / "RESULTS_MANIFEST.json").write_text(
        json.dumps({"paper_ready": True, "missing_required_results": []}),
        encoding="utf-8",
    )
    data_path = tmp_path / "real.jsonl"
    data_path.write_text("dummy\n", encoding="utf-8")
    code = check_paper_readiness(results_dir, release_dir, data_path)
    assert code != 0
