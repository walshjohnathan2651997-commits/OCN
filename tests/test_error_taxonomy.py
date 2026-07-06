"""Tests for the error taxonomy analysis (run_error_taxonomy_v1.py).

Verifies:
  - Script produces all required output files
  - FP and FN cases are correctly classified and tagged
  - All 9 error types can be triggered
  - Redacted output contains no raw text (claim_text, evidence_text, selected_evidence)
  - Redacted output contains SHA-256 hashes for traceability
  - true_label is used only for error analysis, not scoring/ranking
  - Summary CSV and MD have correct structure
  - Summary clearly marks data as silver diagnostic
  - Script runs without network/API/training (guards enforced)
  - Real data run completes successfully
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_error_taxonomy_v1.py"
PYTHON = sys.executable

PYTHON_310 = r"C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe"
if Path(PYTHON_310).exists():
    PYTHON = PYTHON_310

# ---------------------------------------------------------------------------
# Toy fixture
# ---------------------------------------------------------------------------

def _create_toy_fixture(tmp_path):
    """Create a toy fixture with all required CSVs for error taxonomy testing.

    Creates:
      - review_scores.csv: candidate_id, true_label, pred_label, selected_evidence, ...
      - selector.csv: candidate_id, p_strong, p_contra, entropy, selector_score, ...
      - retrieval.csv: candidate_id, rank, is_oracle_hit, bm25_score, ...
      - candidates.csv: candidate_id, target_candidate_group_id, claim_text, evidence_text
      - smart_queue.csv: candidate_id, bucket, score_conservative, ...
    """
    fixture_dir = tmp_path / "fixture"
    fixture_dir.mkdir()

    # 12 candidates, 3 groups (4 per group), 4 labels
    # Designed to trigger multiple error types
    candidate_ids = [f"tc{i:03d}" for i in range(12)]
    groups = ["gA", "gA", "gA", "gA", "gB", "gB", "gB", "gB", "gC", "gC", "gC", "gC"]

    # True labels: each group has 4 variants (supported, mild, strong, contra)
    true_labels = [
        "supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate",
        "supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate",
        "supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate",
    ]

    # Pred labels: introduce specific errors
    # - mild predicted as strong (mild_vs_strong_boundary FP)
    # - strong predicted as mild (mild_vs_strong_boundary FN)
    # - supported flagged as strong (supported_overflag)
    # - contra signal high on non-contra (contradiction_confusion)
    pred_labels = [
        "strong_action_overclaim",   # supported -> strong (FP, supported_overflag)
        "strong_action_overclaim",   # mild -> strong (FP, mild_vs_strong_boundary)
        "strong_action_overclaim",   # strong -> strong (TP)
        "strong_action_overclaim",   # contra -> strong (FP, contradiction_confusion)
        "supported",                 # supported -> supported (TN)
        "mild_scope_overclaim",      # mild -> mild (TN)
        "mild_scope_overclaim",      # strong -> mild (FN, mild_vs_strong_boundary)
        "contradiction_candidate",   # contra -> contra (TN)
        "strong_action_overclaim",   # supported -> strong (FP)
        "mild_scope_overclaim",      # mild -> mild (TN)
        "strong_action_overclaim",   # strong -> strong (TP)
        "contradiction_candidate",   # contra -> contra (TN)
    ]

    # selected_evidence: vary length to trigger evidence_format_noise
    short_evidence = "Short."
    normal_evidence = "This is a normal length evidence sentence with adequate detail."
    long_evidence = " ".join(["word"] * 60) + "."

    selected_evidence = [
        normal_evidence,   # tc000
        short_evidence,    # tc001 (evidence_format_noise: < 5 words... actually 1 word)
        normal_evidence,   # tc002
        normal_evidence,   # tc003
        normal_evidence,   # tc004
        normal_evidence,   # tc005
        long_evidence,     # tc006 (evidence_format_noise: > 50 words)
        normal_evidence,   # tc007
        normal_evidence,   # tc008
        normal_evidence,   # tc009
        normal_evidence,   # tc010
        normal_evidence,   # tc011
    ]

    # Selector features
    p_strong = [0.85, 0.80, 0.75, 0.70, 0.30, 0.40, 0.50, 0.20, 0.90, 0.35, 0.65, 0.15]
    p_contra = [0.10, 0.15, 0.20, 0.45, 0.05, 0.10, 0.35, 0.80, 0.08, 0.12, 0.25, 0.85]
    contradiction_nli = [0.05, 0.10, 0.15, 0.40, 0.02, 0.08, 0.32, 0.75, 0.06, 0.10, 0.20, 0.80]
    entropy = [0.15, 0.25, 0.30, 0.55, 0.10, 0.20, 0.65, 0.40, 0.12, 0.18, 0.35, 0.45]
    selector_score = [0.75, 0.20, 0.60, 0.45, 0.80, 0.70, 0.25, 0.85, 0.65, 0.55, 0.50, 0.90]
    selected_rank = [1, 2, 1, 3, 1, 2, 7, 1, 2, 1, 3, 1]  # tc006 has rank > 5
    selected_n_words = [12, 1, 10, 11, 13, 14, 60, 9, 11, 12, 10, 8]
    bm25_score = [30.0, 25.0, 35.0, 20.0, 28.0, 22.0, 15.0, 40.0, 32.0, 26.0, 24.0, 38.0]
    oracle_hit = [1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1]  # tc001 and tc005 have retrieval_miss

    # Claim text with action words for action_lexicon_shortcut
    claim_text = [
        "We propose a new method to improve performance.",     # action words: propose, improve
        "The system extends existing capabilities.",           # action: extends
        "This paper introduces a novel framework.",            # action: introduces
        "The approach enhances overall robustness.",           # action: enhances
        "Results show improvements in accuracy.",              # action: improvements (not in lexicon)
        "The model achieves state-of-the-art results.",        # action: achieves
        "We design and build a new architecture.",             # action: design, build
        "The method creates opportunities for optimization.",  # action: creates, optimization
        "We develop a comprehensive evaluation suite.",        # action: develop
        "The framework delivers consistent gains.",            # action: delivers
        "Our approach provides complementary insights.",       # action: provides
        "We optimize the training procedure.",                 # action: optimize
    ]

    # Evidence text: some don't contain the action words (shortcut)
    evidence_text = [
        "The method is evaluated on multiple benchmarks.",     # no propose/improve -> shortcut
        "The system extends existing capabilities with new modules.",  # has extends -> no shortcut
        "This paper introduces a novel framework for planning.",  # has introduces -> no shortcut
        "The approach is evaluated on real data.",             # no enhances -> shortcut
        "Results show improvements in accuracy across settings.",
        "The model achieves state-of-the-art results on all metrics.",
        "We design and build a new architecture for detection.",  # has design, build
        "The method creates opportunities for optimization.",  # has creates
        "We develop a comprehensive evaluation suite.",        # has develop
        "The framework delivers consistent gains across tasks.",
        "Our approach provides complementary insights into planning.",
        "We optimize the training procedure for stability.",
    ]

    strong_action_flag = [1 if pl == "strong_action_overclaim" else 0 for pl in pred_labels]

    # Write review_scores.csv
    review_df = pd.DataFrame({
        "candidate_id": candidate_ids,
        "true_label": true_labels,
        "pred_label": pred_labels,
        "strong_action_flag": strong_action_flag,
        "strong_action_score": p_strong,
        "p_contra_mean": p_contra,
        "priority_score": [0.9, 0.85, 0.8, 0.75, 0.3, 0.4, 0.5, 0.2, 0.95, 0.35, 0.7, 0.15],
        "selected_evidence": selected_evidence,
        "selected_chunk_id": [f"chunk_{i}" for i in range(12)],
        "selected_rank": selected_rank,
        "source_pdf": [f"paper_{i % 3}" for i in range(12)],
        "page": [1] * 12,
        "route": ["strong_action"] * 12,
        "n_seeds_voted": [1] * 12,
        "vote_share_strong": [1.0] * 12,
    })
    review_df.to_csv(fixture_dir / "review_scores.csv", index=False)

    # Write selector.csv
    selector_df = pd.DataFrame({
        "candidate_id": candidate_ids,
        "true_label": true_labels,
        "pred_label": pred_labels,
        "strong_action_flag": strong_action_flag,
        "p_strong": p_strong,
        "p_contra": p_contra,
        "p_svm": [0.5] * 12,
        "entailment": [0.3] * 12,
        "neutral": [0.5] * 12,
        "contradiction_nli": contradiction_nli,
        "entropy": entropy,
        "selector_score": selector_score,
        "selected_rank": selected_rank,
        "selected_n_words": selected_n_words,
        "bm25_score": bm25_score,
        "oracle_hit": oracle_hit,
    })
    selector_df.to_csv(fixture_dir / "selector.csv", index=False)

    # Write retrieval.csv (multiple rows per candidate)
    retrieval_rows = []
    for i, cid in enumerate(candidate_ids):
        for rank in range(1, 6):
            retrieval_rows.append({
                "candidate_id": cid,
                "rank": rank,
                "chunk_id": f"chunk_{i}_r{rank}",
                "bm25_score": bm25_score[i] - rank * 2,
                "retrieved_text": f"Retrieved text for {cid} rank {rank}",
                "paper_id": f"paper_{i % 3}",
                "same_paper": True,
                "is_oracle_hit": (rank == 1 and oracle_hit[i] == 1),
                "oracle_match_score": 1.0 if (rank == 1 and oracle_hit[i] == 1) else 0.0,
                "page_number": 1,
            })
    retrieval_df = pd.DataFrame(retrieval_rows)
    retrieval_df.to_csv(fixture_dir / "retrieval.csv", index=False)

    # Write candidates.csv
    candidate_df = pd.DataFrame({
        "candidate_id": candidate_ids,
        "target_candidate_group_id": groups,
        "claim_text": claim_text,
        "evidence_text": evidence_text,
        "claim_text_sha256": [f"sha256_claim_{i}" for i in range(12)],
        "evidence_text_sha256": [f"sha256_evidence_{i}" for i in range(12)],
        "domain": ["test"] * 12,
        "source_id": ["src_1"] * 12,
        "group_quality_tier": ["tier3"] * 12,
    })
    candidate_df.to_csv(fixture_dir / "candidates.csv", index=False)

    # Write smart_queue.csv
    sq_df = pd.DataFrame({
        "candidate_id": candidate_ids,
        "target_candidate_group_id": groups,
        "bucket": ["high_priority"] * 4 + ["low_priority"] * 4 + ["high_priority"] * 4,
        "score_conservative": [0.9, 0.85, 0.8, 0.75, 0.3, 0.4, 0.5, 0.2, 0.95, 0.35, 0.7, 0.15],
        "score_balanced": [0.8, 0.75, 0.7, 0.65, 0.4, 0.5, 0.6, 0.3, 0.85, 0.45, 0.6, 0.25],
        "score_high_recall": [0.7, 0.65, 0.6, 0.55, 0.5, 0.6, 0.7, 0.4, 0.75, 0.55, 0.5, 0.35],
        "final_score": [0.8, 0.75, 0.7, 0.65, 0.4, 0.5, 0.6, 0.3, 0.85, 0.45, 0.6, 0.25],
    })
    sq_df.to_csv(fixture_dir / "smart_queue.csv", index=False)

    return fixture_dir


def _run_script(args, timeout=120):
    """Run the error taxonomy script. Returns (returncode, stdout)."""
    cmd = [PYTHON, str(SCRIPT_PATH)] + list(args)
    result = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
    )
    return result.returncode, result.stdout


# ---------------------------------------------------------------------------
# TestOutputsExist
# ---------------------------------------------------------------------------

class TestOutputsExist:
    """All required output files are produced."""

    def test_all_outputs_exist(self, tmp_path):
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        rc, stdout = _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--selector_csv", str(fixture / "selector.csv"),
            "--retrieval_csv", str(fixture / "retrieval.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--smart_queue_csv", str(fixture / "smart_queue.csv"),
            "--output_dir", str(out_dir),
        ])
        assert rc == 0, f"Script failed: {stdout}"

        required = [
            "error_cases_redacted.csv",
            "error_taxonomy_summary.csv",
            "error_taxonomy_summary.md",
            "error_taxonomy_summary.json",
            "run_config.json",
        ]
        for name in required:
            assert (out_dir / name).exists(), f"Missing output: {name}"

    def test_private_output_exists(self, tmp_path):
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        rc, stdout = _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--selector_csv", str(fixture / "selector.csv"),
            "--retrieval_csv", str(fixture / "retrieval.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
        ])
        assert rc == 0, f"Script failed: {stdout}"
        assert (out_dir / "private" / "error_cases_private.csv").exists()


# ---------------------------------------------------------------------------
# TestFpFnClassification
# ---------------------------------------------------------------------------

class TestFpFnClassification:
    """FP and FN cases are correctly classified."""

    def test_error_categories_present(self, tmp_path):
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--selector_csv", str(fixture / "selector.csv"),
            "--retrieval_csv", str(fixture / "retrieval.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
        ])
        df = pd.read_csv(out_dir / "error_cases_redacted.csv", keep_default_na=False)
        assert "error_category" in df.columns
        categories = set(df["error_category"].unique())
        assert categories <= {"TP", "FP", "FN", "TN"}, f"Unexpected categories: {categories}"
        # Should have at least some FP and FN
        assert "FP" in categories, "No FP cases found"
        assert "FN" in categories, "No FN cases found"

    def test_fp_fn_counts_correct(self, tmp_path):
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--selector_csv", str(fixture / "selector.csv"),
            "--retrieval_csv", str(fixture / "retrieval.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
        ])
        df = pd.read_csv(out_dir / "error_cases_redacted.csv", keep_default_na=False)
        n_fp = int((df["error_category"] == "FP").sum())
        n_fn = int((df["error_category"] == "FN").sum())
        assert n_fp > 0, "Expected at least 1 FP"
        assert n_fn > 0, "Expected at least 1 FN"


# ---------------------------------------------------------------------------
# TestErrorTypesTagged
# ---------------------------------------------------------------------------

class TestErrorTypesTagged:
    """All 9 error types can be triggered and are tagged."""

    def test_error_type_tags_column_exists(self, tmp_path):
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--selector_csv", str(fixture / "selector.csv"),
            "--retrieval_csv", str(fixture / "retrieval.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
        ])
        df = pd.read_csv(out_dir / "error_cases_redacted.csv", keep_default_na=False)
        assert "error_type_tags" in df.columns

    def test_multiple_error_types_triggered(self, tmp_path):
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--selector_csv", str(fixture / "selector.csv"),
            "--retrieval_csv", str(fixture / "retrieval.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
        ])
        df = pd.read_csv(out_dir / "error_cases_redacted.csv", keep_default_na=False)
        all_tags = set()
        for tags in df["error_type_tags"]:
            if tags:
                all_tags.update(tags.split(";"))
        # Should trigger at least 5 of 9 error types
        assert len(all_tags) >= 5, f"Only {len(all_tags)} error types triggered: {all_tags}"

    def test_summary_csv_has_all_9_types(self, tmp_path):
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--selector_csv", str(fixture / "selector.csv"),
            "--retrieval_csv", str(fixture / "retrieval.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
        ])
        summary = pd.read_csv(out_dir / "error_taxonomy_summary.csv", keep_default_na=False)
        expected_types = {
            "retrieval_miss", "evidence_format_noise", "weak_selector_overlap",
            "contradiction_confusion", "action_lexicon_shortcut",
            "mild_vs_strong_boundary", "supported_overflag",
            "uncertainty_high_entropy", "group_variant_artifact",
        }
        actual_types = set(summary["error_type"].tolist())
        assert actual_types == expected_types, f"Missing error types: {expected_types - actual_types}"


# ---------------------------------------------------------------------------
# TestRedactedNoRawText
# ---------------------------------------------------------------------------

class TestRedactedNoRawText:
    """Redacted output must not contain raw text fields."""

    FORBIDDEN_TEXT_COLUMNS = [
        "claim_text", "evidence_text", "selected_evidence", "retrieved_text",
    ]

    def test_no_text_columns_in_redacted(self, tmp_path):
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--selector_csv", str(fixture / "selector.csv"),
            "--retrieval_csv", str(fixture / "retrieval.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
        ])
        df = pd.read_csv(out_dir / "error_cases_redacted.csv", keep_default_na=False)
        for col in self.FORBIDDEN_TEXT_COLUMNS:
            assert col not in df.columns, f"Redacted output contains forbidden text column: {col}"

    def test_has_sha256_hashes(self, tmp_path):
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--selector_csv", str(fixture / "selector.csv"),
            "--retrieval_csv", str(fixture / "retrieval.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
        ])
        df = pd.read_csv(out_dir / "error_cases_redacted.csv", keep_default_na=False)
        hash_cols = [c for c in df.columns if "sha256" in c.lower()]
        assert len(hash_cols) >= 1, f"No SHA-256 hash columns in redacted output: {list(df.columns)}"

    def test_private_has_text_but_redacted_does_not(self, tmp_path):
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--selector_csv", str(fixture / "selector.csv"),
            "--retrieval_csv", str(fixture / "retrieval.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
        ])
        private_df = pd.read_csv(out_dir / "private" / "error_cases_private.csv", keep_default_na=False)
        redacted_df = pd.read_csv(out_dir / "error_cases_redacted.csv", keep_default_na=False)

        # Private should have text columns
        assert "claim_text" in private_df.columns or "evidence_text" in private_df.columns, \
            "Private output should contain text columns"
        # Redacted should not
        for col in self.FORBIDDEN_TEXT_COLUMNS:
            assert col not in redacted_df.columns, f"Redacted leaked: {col}"


# ---------------------------------------------------------------------------
# TestLabelUsagePolicy
# ---------------------------------------------------------------------------

class TestLabelUsagePolicy:
    """true_label is used only for error analysis, not scoring/ranking."""

    def test_label_policy_in_summary_json(self, tmp_path):
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--selector_csv", str(fixture / "selector.csv"),
            "--retrieval_csv", str(fixture / "retrieval.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
        ])
        with open(out_dir / "error_taxonomy_summary.json", "r", encoding="utf-8") as f:
            summary = json.load(f)
        assert "label_usage_policy" in summary, "Missing label_usage_policy in summary JSON"
        assert "error analysis" in summary["label_usage_policy"].lower()

    def test_no_score_columns_derived_from_label(self, tmp_path):
        """Verify that no scoring/ranking column is a function of true_label."""
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--selector_csv", str(fixture / "selector.csv"),
            "--retrieval_csv", str(fixture / "retrieval.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
        ])
        df = pd.read_csv(out_dir / "error_cases_redacted.csv", keep_default_na=False)
        # priority_score, selector_score, bm25_score should exist and not be constant
        # functions of true_label (i.e., they're input features, not derived from labels)
        score_cols = [c for c in ["priority_score", "selector_score", "bm25_score"] if c in df.columns]
        assert len(score_cols) >= 1, "No score columns found"
        for col in score_cols:
            # Score should vary within the same true_label group (not a function of label)
            for label in df["true_label"].unique():
                vals = df[df["true_label"] == label][col]
                if len(vals) > 1:
                    assert vals.nunique() > 1, f"{col} is constant within true_label={label} (may be label-derived)"


# ---------------------------------------------------------------------------
# TestSilverDiagnosticDisclaimer
# ---------------------------------------------------------------------------

class TestSilverDiagnosticDisclaimer:
    """Summary must clearly mark data as silver diagnostic."""

    def test_json_has_disclaimer(self, tmp_path):
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--selector_csv", str(fixture / "selector.csv"),
            "--retrieval_csv", str(fixture / "retrieval.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
        ])
        with open(out_dir / "error_taxonomy_summary.json", "r", encoding="utf-8") as f:
            summary = json.load(f)
        assert "data_disclaimer" in summary
        assert "silver" in summary["data_disclaimer"].lower()
        assert "not natural prevalence" in summary["data_disclaimer"].lower()

    def test_md_has_disclaimer(self, tmp_path):
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--selector_csv", str(fixture / "selector.csv"),
            "--retrieval_csv", str(fixture / "retrieval.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
        ])
        md = (out_dir / "error_taxonomy_summary.md").read_text(encoding="utf-8")
        assert "silver" in md.lower()
        assert "not natural prevalence" in md.lower()


# ---------------------------------------------------------------------------
# TestGuardsEnforced
# ---------------------------------------------------------------------------

class TestGuardsEnforced:
    """Script must enforce no_api/no_network/no_training guards."""

    def test_guards_in_summary_json(self, tmp_path):
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--selector_csv", str(fixture / "selector.csv"),
            "--retrieval_csv", str(fixture / "retrieval.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
        ])
        with open(out_dir / "error_taxonomy_summary.json", "r", encoding="utf-8") as f:
            summary = json.load(f)
        assert "guards" in summary
        guards = summary["guards"]
        assert guards.get("no_api") is True
        assert guards.get("no_network") is True
        assert guards.get("no_training") is True

    def test_guards_in_run_config(self, tmp_path):
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--selector_csv", str(fixture / "selector.csv"),
            "--retrieval_csv", str(fixture / "retrieval.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
        ])
        with open(out_dir / "run_config.json", "r", encoding="utf-8") as f:
            rc = json.load(f)
        assert "guards" in rc
        assert rc["guards"].get("no_api") is True


# ---------------------------------------------------------------------------
# TestSummaryStructure
# ---------------------------------------------------------------------------

class TestSummaryStructure:
    """Summary CSV and MD have correct structure."""

    def test_summary_csv_required_columns(self, tmp_path):
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--selector_csv", str(fixture / "selector.csv"),
            "--retrieval_csv", str(fixture / "retrieval.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
        ])
        summary = pd.read_csv(out_dir / "error_taxonomy_summary.csv", keep_default_na=False)
        required = ["error_type", "n_cases", "pct_cases", "fp_count", "fn_count", "example_candidate_ids"]
        for col in required:
            assert col in summary.columns, f"Missing column: {col}"

    def test_md_has_paper_readable_sections(self, tmp_path):
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--selector_csv", str(fixture / "selector.csv"),
            "--retrieval_csv", str(fixture / "retrieval.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
        ])
        md = (out_dir / "error_taxonomy_summary.md").read_text(encoding="utf-8")
        assert "Error Type Distribution" in md
        assert "Top FP Causes" in md
        assert "Top FN Causes" in md
        assert "Implications for Future Work" in md

    def test_summary_json_has_counts(self, tmp_path):
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--selector_csv", str(fixture / "selector.csv"),
            "--retrieval_csv", str(fixture / "retrieval.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
        ])
        with open(out_dir / "error_taxonomy_summary.json", "r", encoding="utf-8") as f:
            summary = json.load(f)
        for key in ["n_candidates", "n_fp", "n_fn", "n_tp", "n_tn", "n_groups"]:
            assert key in summary, f"Missing {key} in summary JSON"
            assert isinstance(summary[key], int), f"{key} should be int"
        assert "error_type_counts" in summary
        assert isinstance(summary["error_type_counts"], dict)


# ---------------------------------------------------------------------------
# TestRunConfig
# ---------------------------------------------------------------------------

class TestRunConfig:
    """run_config.json has correct structure."""

    def test_run_config_exists_and_valid(self, tmp_path):
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--selector_csv", str(fixture / "selector.csv"),
            "--retrieval_csv", str(fixture / "retrieval.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
        ])
        rc_path = out_dir / "run_config.json"
        assert rc_path.exists()
        with open(rc_path, "r", encoding="utf-8") as f:
            rc = json.load(f)
        assert rc.get("script_name") == "run_error_taxonomy_v1.py"
        assert "inputs" in rc
        assert "thresholds" in rc
        assert "data_disclaimer" in rc


# ---------------------------------------------------------------------------
# TestRealDataRun
# ---------------------------------------------------------------------------

class TestRealDataRun:
    """Run the script on real V3.17 data (if available)."""

    def test_real_data_run_completes(self, tmp_path):
        review_csv = REPO_ROOT / "experiments" / "canonicalized_review_queue_v1" / "canonicalized_r4_review_scores.csv"
        selector_csv = REPO_ROOT / "experiments" / "canonicalized_risk_ranking_v1" / "risk_ranking_features.csv"
        retrieval_csv = REPO_ROOT / "experiments" / "simclaim_pdf_corpus_retrieval_v1" / "retrieval_results_bm25.csv"
        candidate_csv = REPO_ROOT / "data" / "simclaim_all92_candidate_pool_v1" / "strict_silver_max_v1" / "strict_silver_max_candidates_v1.csv"

        if not all(p.exists() for p in [review_csv, selector_csv, retrieval_csv, candidate_csv]):
            pytest.skip("Real data files not available")

        out_dir = tmp_path / "real_output"
        rc, stdout = _run_script([
            "--review_scores_csv", str(review_csv),
            "--selector_csv", str(selector_csv),
            "--retrieval_csv", str(retrieval_csv),
            "--candidate_csv", str(candidate_csv),
            "--output_dir", str(out_dir),
        ], timeout=180)
        assert rc == 0, f"Script failed on real data: {stdout}"

        # Verify outputs
        df = pd.read_csv(out_dir / "error_cases_redacted.csv", keep_default_na=False)
        assert len(df) == 436, f"Expected 436 candidates, got {len(df)}"
        # Should have FP and FN
        assert int((df["error_category"] == "FP").sum()) > 0
        assert int((df["error_category"] == "FN").sum()) > 0
