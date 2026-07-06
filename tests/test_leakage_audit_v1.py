"""Tests for the enhanced leakage audit (Task Pack C).

Validates:
1. All 12 required output files exist in experiments/leakage_audit_v1/
2. audit_summary.md has overall PASS/WARNING/FAIL status
3. No raw claim_text/evidence_text in any output file
4. claim_only_baseline.json has TF-IDF+LR metrics (strong_F1, macro_F1, P@20)
5. shuffled_evidence_baseline.json has correct > shuffled ordering
6. cue_words_by_label.csv has action/certainty/deployment/safety columns
7. generation_policy_distribution.json has policy×label crosstab
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
AUDIT_DIR = REPO_ROOT / "experiments" / "leakage_audit_v1"

REQUIRED_FILES = [
    "claim_only_baseline.json",
    "empty_evidence_baseline.json",
    "shuffled_evidence_baseline.json",
    "title_only_retrieval_baseline.json",
    "metadata_only_retrieval_baseline.json",
    "lexical_overlap_by_label.csv",
    "cue_words_by_label.csv",
    "group_split_integrity.json",
    "generation_policy_distribution.json",
    "no_oracle_in_selector_check.json",
    "no_label_in_queue_sorting_check.json",
    "audit_summary.md",
]

FORBIDDEN_TEXT_FIELDS = {
    "claim_text", "evidence_text", "selected_evidence",
    "raw_text", "clean_text", "retrieved_text",
}


class TestLeakageAuditFilesExist:
    @pytest.mark.parametrize("filename", REQUIRED_FILES)
    def test_file_exists(self, filename):
        path = AUDIT_DIR / filename
        assert path.is_file(), f"Required file missing: {filename}"


class TestLeakageAuditSummary:
    def test_summary_has_overall_status(self):
        path = AUDIT_DIR / "audit_summary.md"
        if not path.is_file():
            pytest.skip("audit_summary.md not found")
        content = path.read_text(encoding="utf-8")
        assert "Overall Status:" in content, "Summary must have overall status"
        # Must be one of PASS/WARNING/FAIL
        assert any(s in content for s in ["PASS", "WARNING", "FAIL"]), \
            "Overall status must be PASS, WARNING, or FAIL"

    def test_summary_has_safe_unsafe_wording(self):
        path = AUDIT_DIR / "audit_summary.md"
        if not path.is_file():
            pytest.skip("audit_summary.md not found")
        content = path.read_text(encoding="utf-8")
        assert "Safe wording" in content or "safe wording" in content.lower(), \
            "Summary must include safe wording guidance"
        assert "Unsafe wording" in content or "unsafe wording" in content.lower(), \
            "Summary must include unsafe wording guidance"
        assert "controlled silver diagnostic" in content, \
            "Summary must mention 'controlled silver diagnostic' as safe wording"

    def test_summary_has_strongest_concern(self):
        path = AUDIT_DIR / "audit_summary.md"
        if not path.is_file():
            pytest.skip("audit_summary.md not found")
        content = path.read_text(encoding="utf-8")
        assert "Strongest leakage concern" in content or "strongest" in content.lower(), \
            "Summary must identify the strongest leakage concern"


class TestLeakageAuditNoRawText:
    @pytest.mark.parametrize("filename", [f for f in REQUIRED_FILES if f.endswith(".json")])
    def test_json_no_forbidden_text_fields(self, filename):
        path = AUDIT_DIR / filename
        if not path.is_file():
            pytest.skip(f"{filename} not found")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Recursively check for forbidden field names
        found = _find_forbidden_fields(data, FORBIDDEN_TEXT_FIELDS)
        assert not found, f"{filename} contains forbidden text fields: {found}"

    @pytest.mark.parametrize("filename", [f for f in REQUIRED_FILES if f.endswith(".csv")])
    def test_csv_no_forbidden_text_columns(self, filename):
        path = AUDIT_DIR / filename
        if not path.is_file():
            pytest.skip(f"{filename} not found")
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            cols = set(reader.fieldnames or [])
        forbidden = FORBIDDEN_TEXT_FIELDS & cols
        assert not forbidden, f"{filename} has forbidden columns: {sorted(forbidden)}"


class TestClaimOnlyBaseline:
    def test_has_tfidf_lr_metrics(self):
        path = AUDIT_DIR / "claim_only_baseline.json"
        if not path.is_file():
            pytest.skip("claim_only_baseline.json not found")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Must have strong_f1_mean, macro_f1_mean, p_at_20_mean
        assert "strong_f1_mean" in data, "Missing strong_f1_mean"
        assert "macro_f1_mean" in data, "Missing macro_f1_mean"
        assert "p_at_20_mean" in data, "Missing p_at_20_mean"
        assert "ratio_claim_only_to_r4" in data, "Missing ratio_claim_only_to_r4"
        assert "n_folds" in data, "Missing n_folds (group-aware CV)"
        assert data["n_folds"] >= 2, f"Expected >= 2 folds, got {data['n_folds']}"

    def test_has_ci(self):
        path = AUDIT_DIR / "claim_only_baseline.json"
        if not path.is_file():
            pytest.skip("claim_only_baseline.json not found")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "strong_f1_ci95_low" in data, "Missing CI low"
        assert "strong_f1_ci95_high" in data, "Missing CI high"


class TestShuffledEvidenceBaseline:
    def test_correct_greater_than_shuffled(self):
        path = AUDIT_DIR / "shuffled_evidence_baseline.json"
        if not path.is_file():
            pytest.skip("shuffled_evidence_baseline.json not found")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        correct = data.get("mean_correct_evidence_overlap", 0)
        shuffled = data.get("mean_cross_group_shuffled_overlap", 0)
        assert correct > shuffled, \
            f"Correct evidence overlap ({correct}) should be > shuffled ({shuffled})"

    def test_has_ordering_check(self):
        path = AUDIT_DIR / "shuffled_evidence_baseline.json"
        if not path.is_file():
            pytest.skip("shuffled_evidence_baseline.json not found")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "ordering_holds" in data, "Missing ordering_holds field"
        assert "expected_ordering" in data, "Missing expected_ordering field"


class TestCueWordsCSV:
    def test_has_required_columns(self):
        path = AUDIT_DIR / "cue_words_by_label.csv"
        if not path.is_file():
            pytest.skip("cue_words_by_label.csv not found")
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            cols = set(reader.fieldnames or [])
        required = {
            "label", "n",
            "mean_action_cue_rate", "mean_certainty_cue_rate",
            "mean_deployment_cue_rate", "mean_safety_cue_rate",
        }
        missing = required - cols
        assert not missing, f"cue_words_by_label.csv missing columns: {sorted(missing)}"


class TestGenerationPolicyDistribution:
    def test_has_crosstab(self):
        path = AUDIT_DIR / "generation_policy_distribution.json"
        if not path.is_file():
            pytest.skip("generation_policy_distribution.json not found")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "policy_label_crosstab" in data, "Missing policy_label_crosstab"
        assert "domain_label_crosstab" in data, "Missing domain_label_crosstab"
        assert "max_policy_label_concentration" in data, "Missing max_policy_label_concentration"
        assert "silver_label_source_counts" in data, "Missing silver_label_source_counts"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_forbidden_fields(obj, forbidden, path=""):
    """Recursively search for forbidden field names in a JSON object."""
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in forbidden:
                found.append(f"{path}.{k}")
            found.extend(_find_forbidden_fields(v, forbidden, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(_find_forbidden_fields(v, forbidden, f"{path}[{i}]"))
    return found
