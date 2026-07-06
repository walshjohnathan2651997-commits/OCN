"""Tests for the metric robustness bootstrap analysis (run_metric_robustness_v1.py).

Verifies:
  - Script produces all 5 output files (classification_metrics_with_ci.csv,
    queue_metrics_with_ci.csv, paired_comparison.csv, robustness_summary.json,
    robustness_summary.md)
  - CI columns exist and are valid (ci_low <= point_estimate <= ci_high)
  - Group bootstrap is used when target_candidate_group_id is available
  - Candidate-level fallback warns when groups < 2
  - true_label is not used for ranking (verified via config check)
  - Summary marks data as silver diagnostic
  - Paired comparison produces delta/CI/prob_delta_positive
  - Script runs without network/API/training
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_metric_robustness_v1.py"
PYTHON = sys.executable

PYTHON_310 = r"C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe"
if Path(PYTHON_310).exists():
    PYTHON = PYTHON_310


def _create_toy_fixture(tmp_path):
    """Create a toy fixture with all required columns for testing.

    Creates 3 CSVs:
      - review_scores.csv: candidate_id, true_label, pred_label, priority_score
      - ranking_scores.csv: candidate_id, score_conservative, score_balanced
      - candidates.csv: candidate_id, target_candidate_group_id
    """
    fixture_dir = tmp_path / "fixture"
    fixture_dir.mkdir()

    # 20 candidates, 5 groups (4 per group), 4 labels
    np.random.seed(42)
    n = 20
    n_groups = 5
    labels = ["supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate"]

    candidate_ids = [f"c{i:03d}" for i in range(n)]
    groups = [f"g{i % n_groups}" for i in range(n)]
    true_labels = [labels[i % 4] for i in range(n)]
    # Pred labels: 70% correct, 30% wrong
    pred_labels = []
    for i, tl in enumerate(true_labels):
        if np.random.random() < 0.7:
            pred_labels.append(tl)
        else:
            pred_labels.append(labels[(i + 1) % 4])

    # Scores: priority_score (G_conservative_precision), score_conservative, score_balanced
    priority_score = np.random.uniform(0, 1, n)
    score_conservative = priority_score + np.random.normal(0, 0.1, n)
    score_balanced = priority_score + np.random.normal(0, 0.15, n)

    review_df = pd.DataFrame({
        "candidate_id": candidate_ids,
        "true_label": true_labels,
        "pred_label": pred_labels,
        "priority_score": priority_score,
    })
    review_df.to_csv(fixture_dir / "review_scores.csv", index=False)

    ranking_df = pd.DataFrame({
        "candidate_id": candidate_ids,
        "score_conservative": score_conservative,
        "score_balanced": score_balanced,
    })
    ranking_df.to_csv(fixture_dir / "ranking_scores.csv", index=False)

    candidate_df = pd.DataFrame({
        "candidate_id": candidate_ids,
        "target_candidate_group_id": groups,
    })
    candidate_df.to_csv(fixture_dir / "candidates.csv", index=False)

    return fixture_dir


def _run_script(args, timeout=120):
    """Run the metric robustness script. Returns (returncode, stdout)."""
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


# ---------------- TestOutputsExist ----------------

class TestOutputsExist:
    """Verify all 5 output files are produced."""

    def test_all_outputs_exist(self, tmp_path):
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        rc, stdout = _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--ranking_scores_csv", str(fixture / "ranking_scores.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
            "--n_bootstrap", "50",
        ])
        assert rc == 0, f"Script failed: {stdout}"
        assert (out_dir / "classification_metrics_with_ci.csv").exists()
        assert (out_dir / "queue_metrics_with_ci.csv").exists()
        assert (out_dir / "paired_comparison.csv").exists()
        assert (out_dir / "robustness_summary.json").exists()
        assert (out_dir / "robustness_summary.md").exists()

    def test_run_config_exists(self, tmp_path):
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--ranking_scores_csv", str(fixture / "ranking_scores.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
            "--n_bootstrap", "50",
        ])
        assert (out_dir / "run_config.json").exists()


# ---------------- TestCIValidity ----------------

class TestCIValidity:
    """Verify CI columns are valid."""

    def test_ci_low_le_point_le_ci_high(self, tmp_path):
        """For each metric, ci_low <= point_estimate <= ci_high."""
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--ranking_scores_csv", str(fixture / "ranking_scores.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
            "--n_bootstrap", "100",
        ])
        df = pd.read_csv(out_dir / "classification_metrics_with_ci.csv", keep_default_na=False)
        for _, row in df.iterrows():
            pe = float(row["point_estimate"])
            cl = float(row["ci_low_2_5"])
            ch = float(row["ci_high_97_5"])
            assert cl <= pe + 0.001, f"ci_low > point_estimate for {row['metric']}: {cl} > {pe}"
            assert pe <= ch + 0.001, f"point_estimate > ci_high for {row['metric']}: {pe} > {ch}"

    def test_ci_is_not_zero_width(self, tmp_path):
        """CI should not be zero-width (bootstrap should produce variation)."""
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--ranking_scores_csv", str(fixture / "ranking_scores.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
            "--n_bootstrap", "100",
        ])
        df = pd.read_csv(out_dir / "classification_metrics_with_ci.csv", keep_default_na=False)
        for _, row in df.iterrows():
            width = float(row["ci_high_97_5"]) - float(row["ci_low_2_5"])
            assert width > 0, f"Zero-width CI for {row['metric']}"


# ---------------- TestGroupBootstrap ----------------

class TestGroupBootstrap:
    """Verify group-aware bootstrap is used."""

    def test_group_bootstrap_used(self, tmp_path):
        """When target_candidate_group_id is available, bootstrap_unit should be 'group'."""
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--ranking_scores_csv", str(fixture / "ranking_scores.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
            "--n_bootstrap", "50",
            "--bootstrap_unit", "group",
        ])
        df = pd.read_csv(out_dir / "classification_metrics_with_ci.csv", keep_default_na=False)
        assert (df["bootstrap_unit"] == "group").all()

    def test_candidate_fallback_warns(self, tmp_path):
        """When only 1 group exists, should fall back to candidate-level with warning."""
        fixture = _create_toy_fixture(tmp_path)
        # Override candidates with only 1 group
        candidate_df = pd.DataFrame({
            "candidate_id": [f"c{i:03d}" for i in range(20)],
            "target_candidate_group_id": ["g0"] * 20,  # all same group
        })
        candidate_df.to_csv(fixture / "candidates.csv", index=False)

        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--ranking_scores_csv", str(fixture / "ranking_scores.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
            "--n_bootstrap", "50",
            "--bootstrap_unit", "group",
        ])
        with open(out_dir / "robustness_summary.json", "r", encoding="utf-8") as f:
            summary = json.load(f)
        assert summary["bootstrap_unit"] == "candidate"
        assert summary["warning"] is not None
        assert "fallback" in summary["warning"].lower() or "falling back" in summary["warning"].lower()

    def test_candidate_mode_works(self, tmp_path):
        """Explicit candidate-level bootstrap should work."""
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--ranking_scores_csv", str(fixture / "ranking_scores.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
            "--n_bootstrap", "50",
            "--bootstrap_unit", "candidate",
        ])
        df = pd.read_csv(out_dir / "classification_metrics_with_ci.csv", keep_default_na=False)
        assert (df["bootstrap_unit"] == "candidate").all()


# ---------------- TestSilverDiagnosticDisclaimer ----------------

class TestSilverDiagnosticDisclaimer:
    """Verify the summary marks data as silver diagnostic."""

    def test_json_has_disclaimer(self, tmp_path):
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--ranking_scores_csv", str(fixture / "ranking_scores.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
            "--n_bootstrap", "50",
        ])
        with open(out_dir / "robustness_summary.json", "r", encoding="utf-8") as f:
            summary = json.load(f)
        assert "data_disclaimer" in summary
        disclaimer = summary["data_disclaimer"].lower()
        assert "silver" in disclaimer or "diagnostic" in disclaimer
        assert "not natural prevalence" in disclaimer

    def test_md_has_disclaimer(self, tmp_path):
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--ranking_scores_csv", str(fixture / "ranking_scores.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
            "--n_bootstrap", "50",
        ])
        md = (out_dir / "robustness_summary.md").read_text(encoding="utf-8")
        assert "silver" in md.lower() or "diagnostic" in md.lower()
        assert "not natural prevalence" in md.lower()


# ---------------- TestPairedComparison ----------------

class TestPairedComparison:
    """Verify paired bootstrap comparison works."""

    def test_paired_comparison_has_rows(self, tmp_path):
        """When both priority_score and score_conservative/balanced exist,
        paired comparison should produce rows."""
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--ranking_scores_csv", str(fixture / "ranking_scores.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
            "--n_bootstrap", "50",
        ])
        df = pd.read_csv(out_dir / "paired_comparison.csv", keep_default_na=False)
        assert len(df) > 0, "Expected paired comparison rows"

    def test_paired_comparison_has_required_columns(self, tmp_path):
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--ranking_scores_csv", str(fixture / "ranking_scores.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
            "--n_bootstrap", "50",
        ])
        df = pd.read_csv(out_dir / "paired_comparison.csv", keep_default_na=False)
        required = {"metric", "variant_a", "variant_b", "delta", "ci_low", "ci_high", "prob_delta_positive"}
        assert required.issubset(set(df.columns)), f"Missing: {required - set(df.columns)}"

    def test_paired_comparison_variants(self, tmp_path):
        """Should compare priority_score vs score_conservative and score_balanced."""
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--ranking_scores_csv", str(fixture / "ranking_scores.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
            "--n_bootstrap", "50",
        ])
        df = pd.read_csv(out_dir / "paired_comparison.csv", keep_default_na=False)
        variant_bs = set(df["variant_b"].unique())
        assert "score_conservative" in variant_bs or "score_balanced" in variant_bs

    def test_prob_delta_positive_in_range(self, tmp_path):
        """prob_delta_positive should be between 0 and 1."""
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--ranking_scores_csv", str(fixture / "ranking_scores.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
            "--n_bootstrap", "50",
        ])
        df = pd.read_csv(out_dir / "paired_comparison.csv", keep_default_na=False)
        for _, row in df.iterrows():
            p = float(row["prob_delta_positive"])
            assert 0.0 <= p <= 1.0, f"prob_delta_positive out of range: {p}"


# ---------------- TestGuardsEnforced ----------------

class TestGuardsEnforced:
    """Verify hard boundaries are enforced."""

    def test_guards_in_summary(self, tmp_path):
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--ranking_scores_csv", str(fixture / "ranking_scores.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
            "--n_bootstrap", "50",
        ])
        with open(out_dir / "robustness_summary.json", "r", encoding="utf-8") as f:
            summary = json.load(f)
        guards = summary["guards"]
        assert guards["no_api"] is True
        assert guards["no_network"] is True
        assert guards["no_training"] is True
        assert guards["true_label_used_only_for_metrics"] is True

    def test_guards_printed_to_stdout(self, tmp_path):
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _, stdout = _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--ranking_scores_csv", str(fixture / "ranking_scores.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
            "--n_bootstrap", "50",
        ])
        assert "no_api: True" in stdout
        assert "no_network: True" in stdout
        assert "no_training: True" in stdout


# ---------------- TestQueueMetrics ----------------

class TestQueueMetrics:
    """Verify queue metrics are computed correctly."""

    def test_all_queue_metrics_present(self, tmp_path):
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--ranking_scores_csv", str(fixture / "ranking_scores.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
            "--n_bootstrap", "50",
        ])
        df = pd.read_csv(out_dir / "queue_metrics_with_ci.csv", keep_default_na=False)
        metrics = set(df["metric"].unique())
        expected = {
            "precision_at_10", "precision_at_20", "precision_at_50",
            "recall_at_100", "tp_at_20", "fp_at_20",
        }
        assert expected.issubset(metrics), f"Missing metrics: {expected - metrics}"

    def test_fp_tp_ratio_at_prevalences(self, tmp_path):
        """Should have FP/TP ratio at all 6 prevalences."""
        fixture = _create_toy_fixture(tmp_path)
        out_dir = tmp_path / "output"
        _run_script([
            "--review_scores_csv", str(fixture / "review_scores.csv"),
            "--ranking_scores_csv", str(fixture / "ranking_scores.csv"),
            "--candidate_csv", str(fixture / "candidates.csv"),
            "--output_dir", str(out_dir),
            "--n_bootstrap", "50",
        ])
        df = pd.read_csv(out_dir / "queue_metrics_with_ci.csv", keep_default_na=False)
        prev_metrics = [m for m in df["metric"].unique() if m.startswith("fp_tp_ratio_at_")]
        assert len(prev_metrics) == 6, f"Expected 6 prevalence metrics, got {len(prev_metrics)}"


# ---------------- TestRealDataRun ----------------

class TestRealDataRun:
    """Run the script on real V3.17 data (if available)."""

    def test_real_data_run_completes(self, tmp_path):
        """Script should complete on real canonicalized_r4_review_scores."""
        review_csv = REPO_ROOT / "experiments" / "canonicalized_review_queue_v1" / "canonicalized_r4_review_scores.csv"
        ranking_csv = REPO_ROOT / "experiments" / "canonicalized_risk_ranking_v1" / "risk_ranking_features.csv"
        candidate_csv = REPO_ROOT / "data" / "simclaim_all92_candidate_pool_v1" / "strict_silver_max_v1" / "strict_silver_max_candidates_v1.csv"

        if not all(p.exists() for p in [review_csv, ranking_csv, candidate_csv]):
            pytest.skip("Real data files not available")

        out_dir = tmp_path / "real_output"
        rc, stdout = _run_script([
            "--review_scores_csv", str(review_csv),
            "--ranking_scores_csv", str(ranking_csv),
            "--candidate_csv", str(candidate_csv),
            "--output_dir", str(out_dir),
            "--n_bootstrap", "50",
        ], timeout=180)
        assert rc == 0, f"Script failed on real data: {stdout}"

        # Verify strong_F1 is in expected range (~0.45)
        df = pd.read_csv(out_dir / "classification_metrics_with_ci.csv", keep_default_na=False)
        strong_f1_row = df[df["metric"] == "strong_F1"]
        assert len(strong_f1_row) == 1
        strong_f1 = float(strong_f1_row.iloc[0]["point_estimate"])
        assert 0.3 < strong_f1 < 0.6, f"strong_F1 out of expected range: {strong_f1}"
