"""Tests for scripts/check_paper_readiness.py (P4a).

Verifies the gate fails (non-zero exit) when:
  * data audit is not paper_ready
  * toy/smoke/pilot_template data is used
  * required strong baselines are missing / paper_valid=False
  * required tables are missing
  * key tables have no metric_valid=True row
  * rule/gold-tier baseline is in the main table as paper_valid=True
  * release manifest has paper_ready=False
  * tables are mostly NA

And passes (exit 0) when everything is paper-ready.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.check_paper_readiness import check_paper_readiness


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _write_csv(path: Path, rows: list, fieldnames: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def _make_paper_ready_results(tmp_path: Path) -> Path:
    """Build a minimal results dir that passes the gate."""
    results = tmp_path / "results"
    # data audit paper_ready=True
    # P7 (ocn-30): include multi-annotator agreement counts so the
    # paper-readiness gate's new agreement check passes.
    _write_json(results / "data_audit.json", {
        "paper_ready": {
            "paper_ready": True,
            "blocking_errors": [],
            "counts": {
                "n_multi_annotator": 8,
                "n_with_agreement_score": 8,
            },
        }
    })
    # P4-12: operating threshold state fit on dev (test_split_used=false).
    thr_state_path = results / "operating_threshold.json"
    _write_json(thr_state_path, {
        "selected_threshold": 0.35,
        "metric_optimized": "macro_f1",
        "source_split": "dev",
        "n_records_used": 80,
        "test_split_used": False,
        "best_metric_value": 0.62,
    })
    _write_json(results / "train_eval" / "train_eval_summary.json", {
        "operating_threshold_state": str(thr_state_path),
        "operating_threshold_valid": True,
    })
    # baselines: all required strong baselines paper_valid=True
    bl = {
        name: {"paper_valid": True, "n_samples": 8, "escalation_f1": 0.5}
        for name in (
            "scifact_verifier", "ragas_style_evaluator",
            "ares_style_evaluator", "pairwise_llm_judge",
        )
    }
    _write_json(results / "baselines" / "baselines_results.json", bl)
    # tables: each required table with at least one metric_valid=True row
    # and not mostly NA.
    tables_dir = results / "tables"
    _write_csv(tables_dir / "main_results.csv", [
        {"model": "CESE-OCN full", "accuracy": "0.8", "macro_f1": "0.7",
         "escalation_f1": "0.6", "paper_valid": "true",
         "uses_gold_tiers": "false", "metric_valid": "true"},
    ], ["model", "accuracy", "macro_f1", "escalation_f1",
        "paper_valid", "uses_gold_tiers", "metric_valid"])
    _write_csv(tables_dir / "calibration_ablation.csv", [
        {"calibration": "No calibration", "macro_f1": "0.6", "auroc": "0.75",
         "metric_valid": "true"},
        {"calibration": "Temperature (global)", "macro_f1": "0.65", "auroc": "0.77",
         "metric_valid": "true"},
        {"calibration": "Temperature (ordinal)", "macro_f1": "0.66", "auroc": "0.78",
         "metric_valid": "true"},
        {"calibration": "Isotonic (ordinal)", "macro_f1": "0.67", "auroc": "0.79",
         "metric_valid": "true"},
        {"calibration": "Separate thresholds", "macro_f1": "0.65", "auroc": "0.77",
         "metric_valid": "true"},
        {"calibration": "Shared thresholds", "macro_f1": "0.7", "auroc": "0.8",
         "metric_valid": "true"},
    ], ["calibration", "macro_f1", "auroc", "metric_valid"])
    _write_csv(tables_dir / "constraint_ablation.csv", [
        {"constraint": "full", "escalation_f1": "0.6",
         "metric_valid": "true"},
    ], ["constraint", "escalation_f1", "metric_valid"])
    _write_csv(tables_dir / "adversarial_results.csv", [
        {"split": "Standard test", "escalation_f1": "0.6",
         "metric_valid": "true"},
    ], ["split", "escalation_f1", "metric_valid"])
    _write_csv(tables_dir / "oracle_extracted_confidence.csv", [
        {"source": "extracted", "escalation_f1": "0.6",
         "metric_valid": "true"},
    ], ["source", "escalation_f1", "metric_valid"])
    _write_csv(tables_dir / "mapping_ablation.csv", [
        {"mapping": "expert", "scope_escalation_f1": "0.6",
         "metric_valid": "true"},
    ], ["mapping", "scope_escalation_f1", "metric_valid"])
    _write_csv(tables_dir / "threshold_sensitivity.csv", [
        {"threshold": "0.5", "f1": "0.6", "metric_valid": "true"},
    ], ["threshold", "f1", "metric_valid"])
    _write_csv(tables_dir / "ordinal_calibration_diagnostics.csv", [
        {"dimension": "scope", "claim_ordinal_ece": "0.05",
         "metric_valid": "true"},
    ], ["dimension", "claim_ordinal_ece", "metric_valid"])
    _write_csv(tables_dir / "high_strength_false_support.csv", [
        {"model": "CESE-OCN full", "high_strength_false_support_rate": "0.1",
         "metric_valid": "true"},
    ], ["model", "high_strength_false_support_rate", "metric_valid"])
    # ocn-30 P1/P2/P3/P7: bootstrap CI, paired significance, error
    # analysis, and stage-wise agreement report are now required for
    # paper_full. Provide valid fixtures so the happy-path test passes.
    _write_json(results / "bootstrap_ci.json", {
        "CESE-OCN": {"metric_valid": True, "n_samples": 80,
                     "macro_f1": {"mean": 0.7, "ci95_low": 0.6, "ci95_high": 0.8}},
        "_meta": {"n_boot": 1000, "seed": 13,
                  "paper_full_confirmatory": True},
    })
    _write_json(results / "paired_significance.json", {
        "metric_valid": True,
        "CESE-OCN_vs_structured_llm_judge": {
            "mcnemar": {"p_value": 0.04},
        },
    })
    _write_json(results / "error_analysis.json", {"buckets": {}, "overall": {"n": 80}})
    (results / "error_examples.md").write_text("# examples\n", encoding="utf-8")
    _write_json(results / "agreement_report.json", {
        "n_double_annotated": 60,
        "stage_1_claim_tiers": {
            "weighted_kappa_by_dim": {"scope": 0.6, "causal": 0.55,
                                      "action": 0.6, "certainty": 0.6},
        },
        "stage_3_labels": {
            "cohen_kappa_escalation": 0.6,
            "adjudication_rate": 0.2,
        },
    })
    return results


def _make_paper_ready_release(tmp_path: Path) -> Path:
    release = tmp_path / "release"
    _write_json(release / "RESULTS_MANIFEST.json", {
        "paper_ready": True,
        "missing_required_results": [],
        "required_results_complete": True,
    })
    # ocn-30 P5/P7: user-spec manifest.json must carry code_version,
    # excluded_artifacts, and per-file hashes for the gate's manifest
    # hash check.
    _write_json(release / "manifest.json", {
        "paper_ready": True,
        "required_results_complete": True,
        "missing_required_results": [],
        "code_version": "deadbeef",
        "data_files": [{"path": "data/simclaim_eval/test.jsonl", "sha256": "abc"}],
        "configs": [{"path": "configs/model_cese_ocn.yaml", "sha256": "def"}],
        "results": [{"path": "results/eval_test.json", "sha256": "ghi"}],
        "excluded_artifacts": ["checkpoints/*.pt", "outputs/*/logs/*.log"],
        "exact_command_sequence": ["python scripts/validate_data.py"],
    })
    return release


def test_gate_passes_when_everything_paper_ready(tmp_path):
    results = _make_paper_ready_results(tmp_path)
    release = _make_paper_ready_release(tmp_path)
    code = check_paper_readiness(results, release, data_path=None)
    assert code == 0


def test_gate_fails_when_data_audit_not_paper_ready(tmp_path):
    results = _make_paper_ready_results(tmp_path)
    release = _make_paper_ready_release(tmp_path)
    _write_json(results / "data_audit.json", {
        "paper_ready": {"paper_ready": False, "blocking_errors": ["x"]}
    })
    code = check_paper_readiness(results, release, data_path=None)
    assert code != 0


def test_gate_fails_when_toy_data_used(tmp_path):
    results = _make_paper_ready_results(tmp_path)
    release = _make_paper_ready_release(tmp_path)
    code = check_paper_readiness(results, release, data_path=Path("data/toy/smoke.jsonl"))
    assert code != 0


def test_gate_fails_when_pilot_template_data_used(tmp_path):
    results = _make_paper_ready_results(tmp_path)
    release = _make_paper_ready_release(tmp_path)
    code = check_paper_readiness(results, release, data_path=Path("data/pilot_template.jsonl"))
    assert code != 0


def test_gate_fails_when_strong_baseline_missing(tmp_path):
    results = _make_paper_ready_results(tmp_path)
    release = _make_paper_ready_release(tmp_path)
    bl = _read_json(results / "baselines" / "baselines_results.json")
    del bl["scifact_verifier"]
    _write_json(results / "baselines" / "baselines_results.json", bl)
    code = check_paper_readiness(results, release, data_path=None)
    assert code != 0


def test_gate_fails_when_strong_baseline_not_paper_valid(tmp_path):
    results = _make_paper_ready_results(tmp_path)
    release = _make_paper_ready_release(tmp_path)
    bl = _read_json(results / "baselines" / "baselines_results.json")
    bl["scifact_verifier"]["paper_valid"] = False
    bl["scifact_verifier"]["error"] = "missing offline_jsonl"
    _write_json(results / "baselines" / "baselines_results.json", bl)
    code = check_paper_readiness(results, release, data_path=None)
    assert code != 0


def test_gate_fails_when_required_table_missing(tmp_path):
    results = _make_paper_ready_results(tmp_path)
    release = _make_paper_ready_release(tmp_path)
    (results / "tables" / "main_results.csv").unlink()
    code = check_paper_readiness(results, release, data_path=None)
    assert code != 0


def test_gate_fails_when_table_mostly_na(tmp_path):
    results = _make_paper_ready_results(tmp_path)
    release = _make_paper_ready_release(tmp_path)
    # Overwrite main_results with mostly NA rows.
    _write_csv(results / "tables" / "main_results.csv", [
        {"model": "CESE-OCN full", "accuracy": "NA", "macro_f1": "NA",
         "escalation_f1": "NA", "paper_valid": "true",
         "uses_gold_tiers": "false", "metric_valid": "true"},
    ], ["model", "accuracy", "macro_f1", "escalation_f1",
        "paper_valid", "uses_gold_tiers", "metric_valid"])
    code = check_paper_readiness(results, release, data_path=None)
    assert code != 0


def test_gate_fails_when_rule_baseline_in_main_as_paper_valid(tmp_path):
    results = _make_paper_ready_results(tmp_path)
    release = _make_paper_ready_release(tmp_path)
    # Add a rule baseline row with paper_valid=True + uses_gold_tiers=True.
    main_csv = results / "tables" / "main_results.csv"
    _write_csv(main_csv, [
        {"model": "CESE-OCN full", "accuracy": "0.8", "macro_f1": "0.7",
         "escalation_f1": "0.6", "paper_valid": "true",
         "uses_gold_tiers": "false", "metric_valid": "true"},
        {"model": "Rule baseline", "accuracy": "0.9", "macro_f1": "0.9",
         "escalation_f1": "0.9", "paper_valid": "true",
         "uses_gold_tiers": "true", "metric_valid": "true"},
    ], ["model", "accuracy", "macro_f1", "escalation_f1",
        "paper_valid", "uses_gold_tiers", "metric_valid"])
    code = check_paper_readiness(results, release, data_path=None)
    assert code != 0


def test_gate_fails_when_manifest_paper_ready_false(tmp_path):
    results = _make_paper_ready_results(tmp_path)
    release = _make_paper_ready_release(tmp_path)
    _write_json(release / "RESULTS_MANIFEST.json", {
        "paper_ready": False,
        "missing_required_results": [],
    })
    code = check_paper_readiness(results, release, data_path=None)
    assert code != 0


def test_gate_fails_when_key_table_no_metric_valid_true(tmp_path):
    results = _make_paper_ready_results(tmp_path)
    release = _make_paper_ready_release(tmp_path)
    # Overwrite main_results with all metric_valid=False.
    _write_csv(results / "tables" / "main_results.csv", [
        {"model": "CESE-OCN full", "accuracy": "0.8", "macro_f1": "0.7",
         "escalation_f1": "0.6", "paper_valid": "true",
         "uses_gold_tiers": "false", "metric_valid": "false"},
    ], ["model", "accuracy", "macro_f1", "escalation_f1",
        "paper_valid", "uses_gold_tiers", "metric_valid"])
    code = check_paper_readiness(results, release, data_path=None)
    assert code != 0


# ---------------------------------------------------------------------------
# P5b: Graph CESE optional claim rule
# ---------------------------------------------------------------------------


def test_gate_fails_when_graph_cese_claimed_without_ablation(tmp_path):
    """P5b: Graph CESE in main_results as paper_valid=True without a
    graph ablation table is a blocking error."""
    results = _make_paper_ready_results(tmp_path)
    release = _make_paper_ready_release(tmp_path)
    # Add a Graph CESE row to main_results as paper_valid=True.
    _write_csv(results / "tables" / "main_results.csv", [
        {"model": "CESE-OCN full", "accuracy": "0.8", "macro_f1": "0.7",
         "escalation_f1": "0.6", "paper_valid": "true",
         "uses_gold_tiers": "false", "metric_valid": "true"},
        {"model": "Graph CESE", "accuracy": "0.85", "macro_f1": "0.75",
         "escalation_f1": "0.65", "paper_valid": "true",
         "uses_gold_tiers": "false", "metric_valid": "true"},
    ], ["model", "accuracy", "macro_f1", "escalation_f1",
        "paper_valid", "uses_gold_tiers", "metric_valid"])
    code = check_paper_readiness(results, release, data_path=None)
    assert code != 0


def test_gate_passes_when_graph_cese_absent(tmp_path):
    """P5b: Graph CESE absent from main_results is NOT a blocking error
    (it is optional)."""
    results = _make_paper_ready_results(tmp_path)
    release = _make_paper_ready_release(tmp_path)
    code = check_paper_readiness(results, release, data_path=None)
    assert code == 0


def test_gate_passes_when_graph_cese_claimed_with_ablation(tmp_path):
    """P5b: Graph CESE in main_results is OK when a graph_ablation.csv
    table exists."""
    results = _make_paper_ready_results(tmp_path)
    release = _make_paper_ready_release(tmp_path)
    _write_csv(results / "tables" / "main_results.csv", [
        {"model": "CESE-OCN full", "accuracy": "0.8", "macro_f1": "0.7",
         "escalation_f1": "0.6", "paper_valid": "true",
         "uses_gold_tiers": "false", "metric_valid": "true"},
        {"model": "Graph CESE", "accuracy": "0.85", "macro_f1": "0.75",
         "escalation_f1": "0.65", "paper_valid": "true",
         "uses_gold_tiers": "false", "metric_valid": "true"},
    ], ["model", "accuracy", "macro_f1", "escalation_f1",
        "paper_valid", "uses_gold_tiers", "metric_valid"])
    _write_csv(results / "tables" / "graph_ablation.csv", [
        {"relation": "supports", "escalation_f1": "0.65",
         "metric_valid": "true"},
    ], ["relation", "escalation_f1", "metric_valid"])
    code = check_paper_readiness(results, release, data_path=None)
    assert code == 0


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# P4-12: operating threshold state checks
# ---------------------------------------------------------------------------


def test_gate_fails_when_operating_threshold_missing(tmp_path):
    """P4-12: missing train_eval_summary.json blocks paper_ready."""
    results = _make_paper_ready_results(tmp_path)
    release = _make_paper_ready_release(tmp_path)
    (results / "train_eval" / "train_eval_summary.json").unlink()
    code = check_paper_readiness(results, release, data_path=None)
    assert code != 0


def test_gate_fails_when_operating_threshold_invalid(tmp_path):
    """P4-12: operating_threshold_valid=False blocks paper_ready."""
    results = _make_paper_ready_results(tmp_path)
    release = _make_paper_ready_release(tmp_path)
    _write_json(results / "train_eval" / "train_eval_summary.json", {
        "operating_threshold_state": str(results / "operating_threshold.json"),
        "operating_threshold_valid": False,
    })
    code = check_paper_readiness(results, release, data_path=None)
    assert code != 0


def test_gate_fails_when_operating_threshold_uses_test_split(tmp_path):
    """P4-12: test_split_used=true blocks paper_ready."""
    results = _make_paper_ready_results(tmp_path)
    release = _make_paper_ready_release(tmp_path)
    thr_state_path = results / "operating_threshold.json"
    _write_json(thr_state_path, {
        "selected_threshold": 0.35,
        "source_split": "test",
        "test_split_used": True,
    })
    code = check_paper_readiness(results, release, data_path=None)
    assert code != 0


def test_pilot_ok_does_not_change_paper_ready_on_failure(tmp_path):
    """P4-12: --pilot_ok is advisory only; it cannot make a failing
    gate pass."""
    results = _make_paper_ready_results(tmp_path)
    release = _make_paper_ready_release(tmp_path)
    # Break the data audit so the gate should fail.
    _write_json(results / "data_audit.json", {
        "paper_ready": {"paper_ready": False, "blocking_errors": ["x"]}
    })
    code = check_paper_readiness(
        results, release, data_path=None, pilot_ok=True
    )
    assert code != 0


def test_rule_baseline_paper_valid_blocks(tmp_path):
    """P4-12: a rule baseline appearing paper_valid=True in the main
    table blocks the gate."""
    results = _make_paper_ready_results(tmp_path)
    release = _make_paper_ready_release(tmp_path)
    _write_csv(results / "tables" / "main_results.csv", [
        {"model": "CESE-OCN full", "accuracy": "0.8", "macro_f1": "0.7",
         "escalation_f1": "0.6", "paper_valid": "true",
         "uses_gold_tiers": "false", "metric_valid": "true"},
        {"model": "Rule baseline", "accuracy": "0.9", "macro_f1": "0.9",
         "escalation_f1": "0.9", "paper_valid": "true",
         "uses_gold_tiers": "true", "metric_valid": "true"},
    ], ["model", "accuracy", "macro_f1", "escalation_f1",
        "paper_valid", "uses_gold_tiers", "metric_valid"])
    code = check_paper_readiness(results, release, data_path=None)
    assert code != 0
