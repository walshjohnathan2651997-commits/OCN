"""Tests: toy end-to-end demo completes successfully.

Runs the full toy pipeline (sentence corpus → BM25 → canonicalizer →
format-shift → mock R4 + SmartQueue → leakage audit) and verifies that
every step completes and produces the expected outputs.

This test does NOT require real PDFs, real data, network, or API keys.
All R4 scores in the demo are MOCK/TOY.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DEMO_OUTPUT = REPO_ROOT / "experiments" / "toy_end_to_end_demo_v1"

DEMO_REQUIRED_FILES = [
    "toy_review_queue.csv",
    "toy_run_summary.json",
]

# Each step's check_output (relative to repo root) — must exist after demo.
STEP_CHECK_OUTPUTS = [
    "data/pdf_corpus_toy_v1/sentences.jsonl",
    "experiments/bm25_sentence_retrieval_v1_toy/oracle_recall_summary.json",
    "experiments/canonicalizer_ablation_v1_toy/selector_metrics_summary.csv",
    "experiments/format_shift_ablation_v1_toy/format_shift_inputs.csv",
    "experiments/lightweight_smart_queue_v1_toy/smart_queue_top100.csv",
    "experiments/leakage_audit_v1_toy/audit_summary.md",
]


def _run_toy_demo():
    """Run the toy demo script. Idempotent — skips steps whose output exists."""
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "run_toy_end_to_end_demo_v1.py"),
    ]
    # Per project constraint: tests must not use capture_output=True (deadlock risk).
    # Redirect to DEVNULL to keep test output clean while avoiding pipe deadlocks.
    result = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=600,
    )
    return result.returncode


@pytest.fixture(scope="module", autouse=True)
def toy_demo_output():
    """Run the toy demo once for this module. Idempotent."""
    if not (DEMO_OUTPUT / "toy_run_summary.json").exists():
        rc = _run_toy_demo()
        assert rc == 0, f"Toy demo exited with code {rc}"
    return DEMO_OUTPUT


class TestToyDemoCompletes:
    """The toy demo must complete end-to-end without errors."""

    def test_demo_summary_exists(self, toy_demo_output):
        summary_path = toy_demo_output / "toy_run_summary.json"
        assert summary_path.exists(), "toy_run_summary.json not produced"

    def test_demo_all_steps_success(self, toy_demo_output):
        with open(toy_demo_output / "toy_run_summary.json", "r", encoding="utf-8") as f:
            summary = json.load(f)
        assert summary["all_steps_success"] is True, \
            f"Not all steps succeeded: {summary.get('steps')}"
        assert summary["n_steps_completed"] == summary["n_steps"], \
            f"Only {summary['n_steps_completed']}/{summary['n_steps']} steps completed"

    def test_demo_required_files(self, toy_demo_output):
        for fname in DEMO_REQUIRED_FILES:
            assert (toy_demo_output / fname).exists(), f"Missing demo output: {fname}"

    def test_demo_step_outputs_exist(self, toy_demo_output):
        for rel_path in STEP_CHECK_OUTPUTS:
            full_path = REPO_ROOT / rel_path
            assert full_path.exists(), f"Step output missing: {rel_path}"

    def test_demo_mock_warning_present(self, toy_demo_output):
        with open(toy_demo_output / "toy_run_summary.json", "r", encoding="utf-8") as f:
            summary = json.load(f)
        assert "mock_r4_warning" in summary, "mock_r4_warning field missing"
        assert "MOCK" in summary["mock_r4_warning"] or "TOY" in summary["mock_r4_warning"], \
            "mock_r4_warning must clearly state scores are MOCK/TOY"

    def test_demo_hard_boundaries(self, toy_demo_output):
        with open(toy_demo_output / "toy_run_summary.json", "r", encoding="utf-8") as f:
            summary = json.load(f)
        assert summary.get("no_network") is True
        assert summary.get("no_api") is True
        assert summary.get("no_training") is True


class TestToyReviewQueue:
    """The final toy review queue must have a valid schema."""

    def test_review_queue_has_rows(self, toy_demo_output):
        import csv
        queue_path = toy_demo_output / "toy_review_queue.csv"
        with open(queue_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) > 0, "Review queue is empty"
        assert len(rows) <= 100, "Review queue must not exceed 100 rows"

    def test_review_queue_has_rank(self, toy_demo_output):
        import csv
        queue_path = toy_demo_output / "toy_review_queue.csv"
        with open(queue_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert "rank" in reader.fieldnames, "rank column missing"
        assert "candidate_id" in reader.fieldnames, "candidate_id column missing"
        assert "bucket" in reader.fieldnames, "bucket column missing"
        # Ranks should be 1-based and increasing
        ranks = [int(r["rank"]) for r in rows]
        assert ranks == sorted(ranks), "Ranks not sorted"
        assert ranks[0] == 1, f"First rank should be 1, got {ranks[0]}"

    def test_review_queue_valid_buckets(self, toy_demo_output):
        import csv
        valid_buckets = {
            "contradiction_or_conflict_review",
            "high_priority_strong_review",
            "evidence_check_needed",
            "low_priority",
        }
        queue_path = toy_demo_output / "toy_review_queue.csv"
        with open(queue_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                assert row["bucket"] in valid_buckets, \
                    f"Invalid bucket '{row['bucket']}' for {row['candidate_id']}"
