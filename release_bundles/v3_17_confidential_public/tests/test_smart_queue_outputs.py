"""Tests: SmartQueue output schema and constraints.

Verifies that SmartQueue produces all required output files with
correct schemas, valid bucket assignments, and group diversity.
"""

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "experiments" / "lightweight_smart_queue_v1_toy"

REQUIRED_OUTPUTS = [
    "smart_queue_scores.csv",
    "smart_queue_top20.csv",
    "smart_queue_top50.csv",
    "smart_queue_top100.csv",
    "smart_queue_config.json",
    "smart_queue_metric_summary.json",
    "leakage_guard_report.json",
]

SCORES_FIELDS = [
    "candidate_id", "target_candidate_group_id", "bucket",
    "p_strong", "p_contra", "p_svm", "strong_action_flag", "entropy",
    "selector_score", "selected_rank", "selected_n_words", "bm25_score",
    "evidence_score", "length_penalty",
    "score_conservative", "score_balanced", "score_high_recall",
    "selected_profile", "final_score",
]

QUEUE_FIELDS = [
    "rank", "candidate_id", "target_candidate_group_id", "bucket",
    "final_score", "p_strong", "p_contra", "evidence_score",
    "selected_n_words", "selected_page_number",
]

VALID_BUCKETS = {
    "contradiction_or_conflict_review",
    "high_priority_strong_review",
    "evidence_check_needed",
    "low_priority",
}


def _ensure_smart_queue_output():
    """Run SmartQueue in toy_mode if output doesn't exist."""
    if not (OUTPUT_DIR / "smart_queue_scores.csv").exists():
        # Per project constraint: tests must not use capture_output=True (deadlock risk).
        subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "run_lightweight_smart_queue_v1.py"),
             "--toy_mode", "--output_dir", "experiments/lightweight_smart_queue_v1_toy",
             "--profile", "balanced"],
            cwd=str(REPO_ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=120, check=True
        )


@pytest.fixture(scope="module", autouse=True)
def smart_queue_output():
    _ensure_smart_queue_output()
    return OUTPUT_DIR


class TestSmartQueueFiles:
    def test_all_required_files_exist(self, smart_queue_output):
        for fname in REQUIRED_OUTPUTS:
            assert (smart_queue_output / fname).exists(), f"Missing: {fname}"

    def test_scores_csv_schema(self, smart_queue_output):
        with open(smart_queue_output / "smart_queue_scores.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            for field in SCORES_FIELDS:
                assert field in headers, f"Missing field in scores CSV: {field}"

    def test_queue_csv_schema(self, smart_queue_output):
        for queue_file in ["smart_queue_top20.csv", "smart_queue_top50.csv", "smart_queue_top100.csv"]:
            with open(smart_queue_output / queue_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                for field in QUEUE_FIELDS:
                    assert field in headers, f"Missing field in {queue_file}: {field}"


class TestSmartQueueBuckets:
    def test_buckets_are_valid(self, smart_queue_output):
        with open(smart_queue_output / "smart_queue_scores.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                assert row["bucket"] in VALID_BUCKETS, \
                    f"Invalid bucket: {row['bucket']}"

    def test_config_has_all_profiles(self, smart_queue_output):
        with open(smart_queue_output / "smart_queue_config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        profiles = config.get("profiles", {})
        assert "conservative" in profiles
        assert "balanced" in profiles
        assert "high_recall" in profiles

    def test_config_has_group_diversity(self, smart_queue_output):
        with open(smart_queue_output / "smart_queue_config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        gd = config.get("group_diversity", {})
        assert gd.get("top20_max_per_group") == 1
        assert gd.get("top50_max_per_group") == 2
        assert gd.get("top100_max_per_group") == 3


class TestSmartQueueMetrics:
    def test_metric_summary_exists(self, smart_queue_output):
        with open(smart_queue_output / "smart_queue_metric_summary.json", "r", encoding="utf-8") as f:
            summary = json.load(f)
        assert "n_candidates" in summary
        assert "precision_at_20" in summary
        assert "true_label_used_for_metrics_only" in summary
        assert summary["true_label_used_for_metrics_only"] is True

    def test_no_forbidden_in_sorting(self, smart_queue_output):
        with open(smart_queue_output / "leakage_guard_report.json", "r", encoding="utf-8") as f:
            guard = json.load(f)
        assert guard["true_label_used_for_sorting"] is False
        assert guard["oracle_hit_used_for_sorting"] is False
        assert guard["evidence_text_used_for_sorting"] is False
