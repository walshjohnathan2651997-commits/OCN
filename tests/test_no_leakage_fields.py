"""Tests: no forbidden fields used for retrieval/selection/sorting.

Smoke tests that verify leakage guards are in place across the pipeline.
These tests do NOT require real data — they check source code and
leakage_guard_report.json files from toy_mode runs.
"""

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

FORBIDDEN_SELECTOR_FIELDS = {
    "true_label", "candidate_label_guess", "gold_label", "human_audited",
    "oracle_hit", "final_label",
}

FORBIDDEN_QUEUE_SORT_FIELDS = {
    "true_label", "is_strong_action", "oracle_hit",
    "candidate_label_guess", "final_label", "gold_label",
    "human_audited", "evidence_text", "evidence_text_sha256",
}


def _run_toy_smart_queue():
    """Ensure toy SmartQueue output exists."""
    guard_path = REPO_ROOT / "experiments" / "lightweight_smart_queue_v1_toy" / "leakage_guard_report.json"
    if not guard_path.exists():
        import subprocess, sys
        # Per project constraint: tests must not use capture_output=True (deadlock risk).
        subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "run_lightweight_smart_queue_v1.py"),
             "--toy_mode", "--output_dir", "experiments/lightweight_smart_queue_v1_toy"],
            cwd=str(REPO_ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=120, check=True
        )
    return guard_path


def _run_toy_canonicalizer():
    """Ensure toy canonicalizer output exists."""
    guard_path = REPO_ROOT / "experiments" / "canonicalizer_ablation_v1_toy" / "leakage_guard_report.json"
    if not guard_path.exists():
        import subprocess, sys
        subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "run_canonicalizer_ablation_v1.py"),
             "--toy_mode", "--output_dir", "experiments/canonicalizer_ablation_v1_toy"],
            cwd=str(REPO_ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=120, check=True
        )
    return guard_path


class TestNoLeakageInSelector:
    """Selector must not use forbidden fields for evidence selection."""

    def test_canonicalizer_leakage_guard_exists(self):
        guard_path = _run_toy_canonicalizer()
        assert guard_path.exists(), f"leakage_guard_report.json not found at {guard_path}"

    def test_canonicalizer_no_oracle_for_selection(self):
        guard_path = _run_toy_canonicalizer()
        with open(guard_path, "r", encoding="utf-8") as f:
            guard = json.load(f)
        assert guard.get("oracle_used_for_selection") is False, \
            "oracle_hit must not be used for selection"
        assert guard.get("labels_used_for_selection") is False, \
            "labels must not be used for selection"

    def test_canonicalizer_forbidden_fields_listed(self):
        guard_path = _run_toy_canonicalizer()
        with open(guard_path, "r", encoding="utf-8") as f:
            guard = json.load(f)
        forbidden = set(guard.get("forbidden_fields_for_selection", []))
        for field in FORBIDDEN_SELECTOR_FIELDS:
            assert field in forbidden, f"{field} should be in forbidden_fields_for_selection"


class TestNoLeakageInQueue:
    """SmartQueue must not use forbidden fields for sorting."""

    def test_queue_leakage_guard_exists(self):
        guard_path = _run_toy_smart_queue()
        assert guard_path.exists(), f"leakage_guard_report.json not found at {guard_path}"

    def test_queue_no_true_label_for_sorting(self):
        guard_path = _run_toy_smart_queue()
        with open(guard_path, "r", encoding="utf-8") as f:
            guard = json.load(f)
        assert guard.get("true_label_used_for_sorting") is False, \
            "true_label must not be used for sorting"
        assert guard.get("oracle_hit_used_for_sorting") is False, \
            "oracle_hit must not be used for sorting"
        assert guard.get("evidence_text_used_for_sorting") is False, \
            "evidence_text must not be used for sorting"

    def test_queue_forbidden_fields_listed(self):
        guard_path = _run_toy_smart_queue()
        with open(guard_path, "r", encoding="utf-8") as f:
            guard = json.load(f)
        forbidden = set(guard.get("forbidden_sort_fields", []))
        for field in FORBIDDEN_QUEUE_SORT_FIELDS:
            assert field in forbidden, f"{field} should be in forbidden_sort_fields"

    def test_queue_allowed_fields_no_forbidden(self):
        guard_path = _run_toy_smart_queue()
        with open(guard_path, "r", encoding="utf-8") as f:
            guard = json.load(f)
        allowed = set(guard.get("allowed_sort_fields", []))
        forbidden = FORBIDDEN_QUEUE_SORT_FIELDS
        overlap = allowed & forbidden
        assert not overlap, f"Forbidden fields in allowed_sort_fields: {overlap}"

    def test_queue_true_label_for_metrics_only(self):
        guard_path = _run_toy_smart_queue()
        with open(guard_path, "r", encoding="utf-8") as f:
            guard = json.load(f)
        assert guard.get("true_label_used_for_metrics_only") is True, \
            "true_label should be used for metrics only"


class TestSourceCodeLeakage:
    """Check source code doesn't reference forbidden fields in scoring context."""

    def test_smart_queue_source_no_forbidden_in_scoring(self):
        """SmartQueue source should not use forbidden fields for sorting."""
        script_path = REPO_ROOT / "scripts" / "run_lightweight_smart_queue_v1.py"
        source = script_path.read_text(encoding="utf-8")
        # Check that forbidden fields are not used as sort keys
        for field in ["true_label", "oracle_hit", "evidence_text", "gold_label", "human_audited"]:
            # Allow references in FORBIDDEN_SORT_FIELDS set definition and comments
            # But not in actual sorting logic
            assert f'sort(key=lambda x: x["{field}"]' not in source, \
                f"{field} must not be used as sort key"
            assert f'["{field}"]' not in source.replace('FORBIDDEN_SORT_FIELDS', '').replace('FORBIDDEN_SELECTOR_FIELDS', ''), \
                f"{field} should not be accessed (except in forbidden field definitions)"

    def test_canonicalizer_source_no_forbidden_in_selection(self):
        """Canonicalizer source should not use forbidden fields for selection."""
        script_path = REPO_ROOT / "scripts" / "run_canonicalizer_ablation_v1.py"
        source = script_path.read_text(encoding="utf-8")
        for field in ["true_label", "oracle_hit", "gold_label", "human_audited", "final_label"]:
            assert f'selector_score *=.*{field}' not in source, \
                f"{field} must not influence selector_score"
