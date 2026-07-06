"""test_complexity_vs_utility_v1.py — Tests for complexity-vs-utility ablation.

Covers:
  - all 7 output files exist
  - method_comparison_metrics has all required columns and method families
  - pareto table has utility_score and pareto_overall
  - paired bootstrap: available=False rows do not fabricate data
  - summary has required disclaimers (does NOT prove rules beat learning)
  - claims checklist has safe/unsafe wording
  - leakage guard report has correct guard values
  - no raw text in any CSV output
  - SmartQueue described as usability layer, not new model
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "experiments" / "complexity_vs_utility_ablation_v1"

METHOD_COMPARISON_PATH = OUT_DIR / "method_comparison_metrics.csv"
PARETO_PATH = OUT_DIR / "method_pareto_table.csv"
COST_AUDIT_PATH = OUT_DIR / "complexity_cost_audit.csv"
PAIRED_BOOTSTRAP_PATH = OUT_DIR / "paired_bootstrap_comparison.csv"
SUMMARY_MD_PATH = OUT_DIR / "complexity_vs_utility_summary.md"
CLAIMS_CHECKLIST_PATH = OUT_DIR / "complexity_vs_utility_claims_checklist.md"
LEAKAGE_GUARD_PATH = OUT_DIR / "leakage_guard_report.json"

REQUIRED_METHOD_FAMILIES = {
    "raw_retrieval",
    "deterministic_canonicalization",
    "rule_queue",
    "smart_queue",
    "higher_complexity",
}

FORBIDDEN_RAWTEXT_FIELDS = {"claim_text", "evidence_text", "selected_evidence"}

METHOD_COMPARISON_COLUMNS = [
    "method_id", "method_family", "available", "uses_training", "uses_api",
    "uses_external_llm", "uses_oracle_for_selection", "uses_label_for_ranking",
    "requires_gpu", "deterministic", "auditable", "private_data_leaves_machine",
    "strong_F1", "precision_at_20", "recall_at_100", "fp_tp_at_5pct", "notes",
]

PARETO_COLUMNS = [
    "method_id", "method_family", "performance_score", "privacy_score",
    "auditability_score", "simplicity_score", "reproducibility_score",
    "utility_score", "pareto_overall",
]


def _read_csv(path: Path) -> tuple[list[str], list[dict]]:
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        return list(reader.fieldnames or []), rows


# ---------- File existence ----------

@pytest.mark.parametrize("path", [
    METHOD_COMPARISON_PATH,
    PARETO_PATH,
    COST_AUDIT_PATH,
    PAIRED_BOOTSTRAP_PATH,
    SUMMARY_MD_PATH,
    CLAIMS_CHECKLIST_PATH,
    LEAKAGE_GUARD_PATH,
])
def test_output_file_exists(path):
    assert path.exists(), f"missing {path}"


# ---------- method_comparison_metrics.csv ----------

def test_method_comparison_has_required_columns():
    header, _ = _read_csv(METHOD_COMPARISON_PATH)
    for col in METHOD_COMPARISON_COLUMNS:
        assert col in header, f"method_comparison missing column {col}"


def test_method_comparison_has_all_method_families():
    _, rows = _read_csv(METHOD_COMPARISON_PATH)
    families = {r["method_family"] for r in rows}
    missing = REQUIRED_METHOD_FAMILIES - families
    assert not missing, f"missing method families: {missing}"


def test_method_comparison_no_raw_text():
    header, _ = _read_csv(METHOD_COMPARISON_PATH)
    leak = set(header) & FORBIDDEN_RAWTEXT_FIELDS
    assert not leak, f"method_comparison has raw-text columns: {leak}"


def test_method_comparison_has_external_llm_unavailable():
    """External LLM baseline must be listed but available=False."""
    _, rows = _read_csv(METHOD_COMPARISON_PATH)
    llm = [r for r in rows if r["method_family"] == "external_llm"]
    assert len(llm) >= 1, "external_llm method family missing"
    assert llm[0]["available"] == "False", "external_llm should be unavailable"


def test_method_comparison_deterministic_methods_are_auditable():
    """All deterministic methods must be auditable."""
    _, rows = _read_csv(METHOD_COMPARISON_PATH)
    for r in rows:
        if r["deterministic"] == "True":
            assert r["auditable"] == "True", \
                f"{r['method_id']} is deterministic but not auditable"


def test_method_comparison_learned_uses_training():
    """Higher-complexity learned methods must have uses_training=True."""
    _, rows = _read_csv(METHOD_COMPARISON_PATH)
    for r in rows:
        if r["method_family"] == "higher_complexity":
            assert r["uses_training"] == "True", \
                f"{r['method_id']} is higher_complexity but uses_training != True"


# ---------- method_pareto_table.csv ----------

def test_pareto_has_required_columns():
    header, _ = _read_csv(PARETO_PATH)
    for col in PARETO_COLUMNS:
        assert col in header, f"pareto missing column {col}"


def test_pareto_has_pareto_overall_values():
    _, rows = _read_csv(PARETO_PATH)
    valid_values = {"pareto_optimal", "dominated", "unavailable"}
    for r in rows:
        assert r["pareto_overall"] in valid_values, \
            f"{r['method_id']} has invalid pareto_overall: {r['pareto_overall']}"


def test_pareto_has_at_least_one_optimal():
    _, rows = _read_csv(PARETO_PATH)
    optimal = [r for r in rows if r["pareto_overall"] == "pareto_optimal"]
    assert len(optimal) >= 1, "no pareto_optimal method found"


def test_pareto_scores_in_zero_one():
    _, rows = _read_csv(PARETO_PATH)
    score_cols = [
        "performance_score", "privacy_score", "auditability_score",
        "simplicity_score", "reproducibility_score", "utility_score",
    ]
    for r in rows:
        for col in score_cols:
            val = float(r[col])
            assert 0.0 <= val <= 1.0, \
                f"{r['method_id']} {col}={val} not in [0,1]"


def test_pareto_no_raw_text():
    header, _ = _read_csv(PARETO_PATH)
    leak = set(header) & FORBIDDEN_RAWTEXT_FIELDS
    assert not leak, f"pareto has raw-text columns: {leak}"


# ---------- complexity_cost_audit.csv ----------

def test_cost_audit_no_raw_text():
    header, _ = _read_csv(COST_AUDIT_PATH)
    leak = set(header) & FORBIDDEN_RAWTEXT_FIELDS
    assert not leak, f"cost_audit has raw-text columns: {leak}"


def test_cost_audit_has_all_methods():
    _, mc_rows = _read_csv(METHOD_COMPARISON_PATH)
    _, ca_rows = _read_csv(COST_AUDIT_PATH)
    mc_ids = {r["method_id"] for r in mc_rows}
    ca_ids = {r["method_id"] for r in ca_rows}
    missing = mc_ids - ca_ids
    assert not missing, f"cost_audit missing methods: {missing}"


def test_cost_audit_external_llm_data_leaves_machine():
    _, rows = _read_csv(COST_AUDIT_PATH)
    llm = [r for r in rows if r["method_family"] == "external_llm"]
    assert llm, "external_llm missing from cost_audit"
    assert llm[0]["data_leaves_machine"] == "True", \
        "external_llm should have data_leaves_machine=True"


# ---------- paired_bootstrap_comparison.csv ----------

def test_paired_bootstrap_no_raw_text():
    header, _ = _read_csv(PAIRED_BOOTSTRAP_PATH)
    leak = set(header) & FORBIDDEN_RAWTEXT_FIELDS
    assert not leak, f"paired_bootstrap has raw-text columns: {leak}"


def test_paired_bootstrap_has_at_least_one_available():
    _, rows = _read_csv(PAIRED_BOOTSTRAP_PATH)
    available = [r for r in rows if r.get("available") == "True"]
    assert len(available) >= 1, "no available paired bootstrap comparisons"


def test_paired_bootstrap_unavailable_rows_no_fabricated_data():
    """Rows with available=False must NOT have mean_a/mean_b/ci values."""
    _, rows = _read_csv(PAIRED_BOOTSTRAP_PATH)
    for r in rows:
        if r.get("available") == "False":
            for col in ["mean_a", "mean_b", "mean_delta", "ci_low", "ci_high"]:
                val = r.get(col, "").strip()
                assert val == "", \
                    f"{r['comparison_id']} available=False but {col}={val!r}"


def test_paired_bootstrap_available_rows_have_metrics():
    """Rows with available=True must have mean_a, mean_b, ci_low, ci_high."""
    _, rows = _read_csv(PAIRED_BOOTSTRAP_PATH)
    for r in rows:
        if r.get("available") == "True":
            for col in ["mean_a", "mean_b", "mean_delta", "ci_low", "ci_high",
                        "prob_delta_positive", "n_bootstrap"]:
                val = r.get(col, "").strip()
                assert val != "", \
                    f"{r['comparison_id']} available=True but {col} is empty"


def test_paired_bootstrap_has_required_comparisons():
    """Must include the 5 comparisons specified in the spec."""
    _, rows = _read_csv(PAIRED_BOOTSTRAP_PATH)
    comparison_ids = {r["comparison_id"] for r in rows}
    required = {
        "cmp_selector_overlap_vs_raw",
        "cmp_selector_overlap_vs_cleaned",
        "cmp_ranking_gconservative_vs_pstrong",
        "cmp_smartqueue_conservative_vs_gconservative",
        "cmp_learned_ranker_vs_gconservative",
    }
    missing = required - comparison_ids
    assert not missing, f"missing comparisons: {missing}"


# ---------- summary.md ----------

def test_summary_has_disclaimer():
    text = SUMMARY_MD_PATH.read_text(encoding="utf-8")
    assert "does not prove rules generally beat learned models" in text.lower()


def test_summary_has_deployment_specific_tradeoff():
    text = SUMMARY_MD_PATH.read_text(encoding="utf-8")
    assert "deployment-specific tradeoff" in text.lower()


def test_summary_has_unsafe_wording_section():
    text = SUMMARY_MD_PATH.read_text(encoding="utf-8")
    assert "simple methods generally beat intelligent methods" in text.lower()


def test_summary_mentions_smartqueue_usability_layer():
    text = SUMMARY_MD_PATH.read_text(encoding="utf-8")
    assert "routing/usability layer" in text.lower() or \
           "usability layer" in text.lower()


def test_summary_has_utility_score_disclaimer():
    text = SUMMARY_MD_PATH.read_text(encoding="utf-8")
    assert "diagnostic aggregation" in text.lower()
    assert "not a benchmark metric" in text.lower()


def test_summary_does_not_claim_sota():
    text = SUMMARY_MD_PATH.read_text(encoding="utf-8")
    # "SOTA" may appear in the forbidden list, but not as a claim.
    # Check that "SOTA" is not preceded by "achieves" or "is".
    lower = text.lower()
    assert "achieves sota" not in lower
    assert "is sota" not in lower


# ---------- claims_checklist.md ----------

def test_claims_checklist_has_safe_claims():
    text = CLAIMS_CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "deployment-specific tradeoff" in text.lower()


def test_claims_checklist_has_unsafe_claims():
    text = CLAIMS_CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "simple methods generally beat intelligent methods" in text.lower()
    assert "rules beat learning" in text.lower()
    assert "bm25 beats llms" in text.lower()


def test_claims_checklist_has_smartqueue_wording():
    text = CLAIMS_CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "routing/usability layer" in text.lower() or \
           "usability layer" in text.lower()


def test_claims_checklist_has_utility_score_disclaimer():
    text = CLAIMS_CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "diagnostic aggregation" in text.lower()
    assert "not a benchmark metric" in text.lower()


# ---------- leakage_guard_report.json ----------

def test_leakage_guard_has_guards():
    report = json.loads(LEAKAGE_GUARD_PATH.read_text(encoding="utf-8"))
    guards = report.get("guards", {})
    assert guards.get("no_api") is True
    assert guards.get("no_network") is True
    assert guards.get("no_training") is True


def test_leakage_guard_no_raw_text_flag():
    report = json.loads(LEAKAGE_GUARD_PATH.read_text(encoding="utf-8"))
    assert report.get("no_raw_text_in_outputs") is True


def test_leakage_guard_has_disclaimer():
    report = json.loads(LEAKAGE_GUARD_PATH.read_text(encoding="utf-8"))
    disclaimer = report.get("disclaimer", "")
    assert "does NOT prove rules beat learning" in disclaimer
