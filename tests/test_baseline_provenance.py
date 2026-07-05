"""Tests for Task C: baseline / report provenance defensive defaults.

Verifies that:
- rule_baseline is never paper_valid (uses gold tiers).
- strong baselines without offline_jsonl / prediction_source default
  to paper_valid=False / metric_valid=False so an old
  baselines_results.json cannot leak them into the paper_full table.
- metric_valid=False rows are still emitted for diagnostics.
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

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import generate_tables as gt_mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_results_dir(tmp_path: Path, baselines: dict, eval_data: dict | None = None) -> Path:
    """Write baselines_results.json + eval_test.json under tmp_path."""
    (tmp_path / "baselines").mkdir(parents=True, exist_ok=True)
    (tmp_path / "baselines" / "baselines_results.json").write_text(
        json.dumps(baselines), encoding="utf-8"
    )
    if eval_data is not None:
        (tmp_path / "eval_test.json").write_text(
            json.dumps(eval_data), encoding="utf-8"
        )
    return tmp_path


# ---------------------------------------------------------------------------
# rule_baseline never paper_valid
# ---------------------------------------------------------------------------

def test_rule_baseline_never_paper_valid(tmp_path):
    """rule_baseline must have paper_valid=False / metric_valid=False /
    uses_gold_tiers=True even if source JSON sets paper_valid=True."""
    baselines = {
        "rule_baseline": {
            "accuracy": 0.8,
            "macro_f1": 0.7,
            "escalation_f1": 0.6,
            "high_strength_false_support_rate": 0.1,
            "evidence_gap_f1": 0.5,
            "ordinal_calibration_error": 0.2,
            "n_samples": 100,
            "paper_valid": True,  # source claims valid - must be overridden
            "metric_valid": True,
            "prediction_source": "model",
            "uses_gold_tiers": False,  # source claims no gold tiers - override
        }
    }
    _setup_results_dir(tmp_path, baselines)
    rows = gt_mod.build_main_results(tmp_path, profile="ci_smoke")
    rule_row = next(r for r in rows if r["model"] == "Rule baseline")
    assert rule_row["paper_valid"] is False
    assert rule_row["metric_valid"] is False
    assert rule_row["uses_gold_tiers"] is True
    assert rule_row["prediction_source"] == "gold_tier_rule"


def test_rule_baseline_excluded_from_paper_full(tmp_path):
    """rule_baseline must NOT appear in paper_full profile."""
    baselines = {
        "rule_baseline": {
            "accuracy": 0.8,
            "n_samples": 100,
            "paper_valid": True,
        }
    }
    _setup_results_dir(tmp_path, baselines)
    rows = gt_mod.build_main_results(tmp_path, profile="paper_full")
    assert not any(r["model"] == "Rule baseline" for r in rows)


# ---------------------------------------------------------------------------
# strong baseline without offline_jsonl
# ---------------------------------------------------------------------------

def test_strong_baseline_without_offline_jsonl_is_not_paper_valid(tmp_path):
    """scifact_verifier lacking offline_jsonl and prediction_source must
    default to paper_valid=False / metric_valid=False /
    prediction_source="missing_or_legacy" even if paper_valid is missing
    or set to True in an old baselines_results.json."""
    baselines = {
        "scifact_verifier": {
            "accuracy": 0.7,
            "n_samples": 50,
            # No offline_jsonl, no prediction_source, no paper_valid.
        }
    }
    _setup_results_dir(tmp_path, baselines)
    rows = gt_mod.build_main_results(tmp_path, profile="ci_smoke")
    sci = next(r for r in rows if r["model"] == "SciFact verifier")
    assert sci["paper_valid"] is False
    assert sci["metric_valid"] is False
    assert sci["prediction_source"] == "missing_or_legacy"


def test_strong_baseline_with_offline_jsonl_is_paper_valid(tmp_path):
    """scifact_verifier WITH offline_jsonl and paper_valid=True must be
    paper_valid=True / metric_valid=True."""
    baselines = {
        "scifact_verifier": {
            "accuracy": 0.7,
            "macro_f1": 0.65,
            "escalation_f1": 0.6,
            "high_strength_false_support_rate": 0.2,
            "evidence_gap_f1": 0.5,
            "ordinal_calibration_error": 0.25,
            "n_samples": 50,
            "paper_valid": True,
            "metric_valid": True,
            "prediction_source": "scifact_offline",
            "uses_gold_tiers": False,
            "offline_jsonl": "scifact_predictions.jsonl",
        }
    }
    _setup_results_dir(tmp_path, baselines)
    rows = gt_mod.build_main_results(tmp_path, profile="paper_full")
    sci = next(r for r in rows if r["model"] == "SciFact verifier")
    assert sci["paper_valid"] is True
    assert sci["metric_valid"] is True
    assert sci["prediction_source"] == "scifact_offline"


def test_strong_baseline_with_prediction_source_only(tmp_path):
    """Strong baseline with prediction_source but no offline_jsonl should
    still count as having offline predictions (the source field itself
    is the provenance)."""
    baselines = {
        "ragas_style_evaluator": {
            "accuracy": 0.6,
            "n_samples": 30,
            "paper_valid": True,
            "metric_valid": True,
            "prediction_source": "ragas_offline",
            "uses_gold_tiers": False,
        }
    }
    _setup_results_dir(tmp_path, baselines)
    rows = gt_mod.build_main_results(tmp_path, profile="paper_full")
    ragas = next(r for r in rows if r["model"] == "RAGAS-style evaluator")
    assert ragas["paper_valid"] is True
    assert ragas["metric_valid"] is True


def test_strong_baseline_missing_or_legacy_source_excluded(tmp_path):
    """Strong baseline with prediction_source="missing_or_legacy" must be
    treated as missing offline predictions -> paper_valid=False."""
    baselines = {
        "ares_style_evaluator": {
            "accuracy": 0.5,
            "n_samples": 10,
            "paper_valid": True,
            "prediction_source": "missing_or_legacy",
        }
    }
    _setup_results_dir(tmp_path, baselines)
    rows = gt_mod.build_main_results(tmp_path, profile="paper_full")
    assert not any(r["model"] == "ARES-style evaluator" for r in rows)


# ---------------------------------------------------------------------------
# high-strength false-support table also enforces defaults
# ---------------------------------------------------------------------------

def test_high_strength_false_support_rule_baseline_metric_invalid(tmp_path):
    """rule_baseline must have metric_valid=False in the high-strength
    false-support table, even with a numeric hsfs rate."""
    baselines = {
        "rule_baseline": {
            "high_strength_false_support_rate": 0.15,
            "n_samples": 100,
            "paper_valid": True,
        }
    }
    _setup_results_dir(tmp_path, baselines)
    rows = gt_mod.build_high_strength_false_support(tmp_path, profile="ci_smoke")
    rule = next(r for r in rows if r["model"] == "Rule baseline")
    assert rule["paper_valid"] is False
    assert rule["metric_valid"] is False


def test_high_strength_false_support_strong_baseline_no_offline(tmp_path):
    """Strong baseline without offline predictions must have
    metric_valid=False in the high-strength false-support table."""
    baselines = {
        "pairwise_llm_judge": {
            "high_strength_false_support_rate": 0.2,
            "n_samples": 30,
            # No offline_jsonl / prediction_source
        }
    }
    _setup_results_dir(tmp_path, baselines)
    rows = gt_mod.build_high_strength_false_support(tmp_path, profile="ci_smoke")
    pair = next(r for r in rows if r["model"] == "Pairwise LLM judge")
    assert pair["paper_valid"] is False
    assert pair["metric_valid"] is False
