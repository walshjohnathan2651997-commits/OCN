"""tests/test_final_perfect_state_gate_v3_17.py — Final perfect-state gate tests.

Verifies that the V3.17 final perfect-state readiness gate:
  - Exists and produces both MD and JSON outputs.
  - Has the required executive summary section.
  - Contains all 10 gate categories.
  - Has no FAIL items.
  - All P0 items have a status (no ``unknown``).
  - All BLOCKED items have blocked_reason and next_action.
  - Final status is READY_WITH_LIMITATIONS (or at least not UNSAFE_OVERCLAIM).

Hard boundaries enforced:
  - No unsafe overclaim (final_status must not be UNSAFE_OVERCLAIM).
  - No undocumented P0 gaps.
  - No BLOCKED without a reason.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
GATE_MD = REPO_ROOT / "reports" / "final_perfect_state_gate_v3_17.md"
GATE_JSON = REPO_ROOT / "reports" / "final_perfect_state_gate_v3_17.json"
GATE_SCRIPT = REPO_ROOT / "scripts" / "run_final_perfect_state_gate_v1.py"

REQUIRED_CATEGORIES = [
    "1. Mainline",
    "2. Dataset",
    "3. Real Experiments",
    "4. PDF",
    "5. Leakage",
    "6. Human Audit",
    "7. Complexity",
    "8. Paper",
    "9. Release",
    "10. CI/Repro",
]

VALID_STATUSES = {"PASS", "WARNING", "BLOCKED", "FAIL"}
VALID_FINAL_STATUSES = {
    "READY_WITH_LIMITATIONS",
    "NOT_READY_P0_BLOCKERS",
    "BLOCKED_BY_PRIVATE_DATA",
    "UNSAFE_OVERCLAIM",
}


# ---------- Fixtures ----------

@pytest.fixture(scope="module")
def gate_json():
    if not GATE_JSON.exists():
        pytest.fail(
            f"Final gate JSON missing: {GATE_JSON}. "
            f"Run: python scripts/run_final_perfect_state_gate_v1.py"
        )
    with open(GATE_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def gate_md_text():
    if not GATE_MD.exists():
        pytest.fail(f"Final gate MD missing: {GATE_MD}")
    return GATE_MD.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def checks(gate_json):
    return gate_json.get("checks", [])


# ---------- File existence ----------

def test_gate_script_exists():
    assert GATE_SCRIPT.exists(), (
        f"Gate script missing: {GATE_SCRIPT}"
    )


def test_gate_md_exists():
    assert GATE_MD.exists(), (
        f"Gate MD missing: {GATE_MD}. "
        f"Run: python scripts/run_final_perfect_state_gate_v1.py"
    )


def test_gate_json_exists():
    assert GATE_JSON.exists(), (
        f"Gate JSON missing: {GATE_JSON}. "
        f"Run: python scripts/run_final_perfect_state_gate_v1.py"
    )


# ---------- Structure ----------

def test_gate_has_executive_summary(gate_md_text):
    assert "## Executive Summary" in gate_md_text, (
        "Gate MD missing Executive Summary section"
    )


def test_gate_has_final_status(gate_md_text, gate_json):
    final = gate_json.get("final_status", "")
    assert final in VALID_FINAL_STATUSES, (
        f"Invalid final_status: {final}. Must be one of {VALID_FINAL_STATUSES}"
    )
    assert final in gate_md_text or final.replace("_", " ") in gate_md_text, (
        f"Final status '{final}' not found in gate MD"
    )


def test_gate_has_summary_counts(gate_json):
    summary = gate_json.get("summary", {})
    assert "total_checks" in summary, "Summary missing total_checks"
    assert "pass" in summary, "Summary missing pass count"
    assert "warning" in summary, "Summary missing warning count"
    assert "blocked" in summary, "Summary missing blocked count"
    assert "fail" in summary, "Summary missing fail count"


def test_gate_has_all_10_categories(checks):
    categories = {c["category"] for c in checks}
    missing = set(REQUIRED_CATEGORIES) - categories
    assert missing == set(), (
        f"Gate missing categories: {missing}. "
        f"Present: {categories}"
    )


def test_gate_has_minimum_check_count(checks):
    assert len(checks) >= 30, (
        f"Gate has only {len(checks)} checks; expected >=30 "
        f"to cover all 10 categories with sub-checks"
    )


# ---------- Status validation ----------

def test_all_checks_have_valid_status(checks):
    for c in checks:
        assert c["status"] in VALID_STATUSES, (
            f"Check {c['check_id']} has invalid status: {c['status']}"
        )


def test_all_checks_have_priority(checks):
    for c in checks:
        assert "priority" in c, f"Check {c['check_id']} missing priority"
        assert c["priority"].startswith("P"), (
            f"Check {c['check_id']} has invalid priority: {c['priority']}"
        )


# ---------- No FAIL ----------

def test_no_fail_items(gate_json):
    fail_items = gate_json.get("fail_items", [])
    assert fail_items == [], (
        f"Gate has {len(fail_items)} FAIL items: "
        f"{[f['check_id'] for f in fail_items]}. "
        f"FAIL = unsafe or undocumented missing. Must be resolved before release."
    )


def test_fail_count_zero(gate_json):
    assert gate_json["summary"]["fail"] == 0, (
        f"fail count = {gate_json['summary']['fail']}, expected 0"
    )


# ---------- P0 items not unknown ----------

def test_p0_items_have_status(checks):
    p0_items = [c for c in checks if c["priority"] == "P0"]
    assert len(p0_items) > 0, "No P0 items found in gate"
    for c in p0_items:
        assert c["status"] in VALID_STATUSES, (
            f"P0 check {c['check_id']} has status '{c['status']}' — must be a valid status, not unknown"
        )


def test_p0_items_not_all_blocked(checks):
    """Not all P0 items should be blocked — at least some must pass."""
    p0_items = [c for c in checks if c["priority"] == "P0"]
    p0_pass = sum(1 for c in p0_items if c["status"] == "PASS")
    assert p0_pass > 0, (
        "No P0 items have PASS status — project has fundamental gaps"
    )


# ---------- BLOCKED has reasons ----------

def test_blocked_items_have_reason(checks):
    blocked = [c for c in checks if c["status"] == "BLOCKED"]
    for c in blocked:
        assert c["blocked_reason"], (
            f"BLOCKED check {c['check_id']} has empty blocked_reason. "
            f"Every BLOCKED item must document why it is blocked."
        )


def test_blocked_items_have_next_action(checks):
    blocked = [c for c in checks if c["status"] == "BLOCKED"]
    for c in blocked:
        assert c["next_action"], (
            f"BLOCKED check {c['check_id']} has empty next_action. "
            f"Every BLOCKED item must document the next action to resolve it."
        )


def test_blocked_json_items_have_reason(gate_json):
    blocked_items = gate_json.get("blocked_items", [])
    for item in blocked_items:
        assert item["blocked_reason"], (
            f"blocked_items entry {item['check_id']} has empty blocked_reason"
        )
        assert item["next_action"], (
            f"blocked_items entry {item['check_id']} has empty next_action"
        )


# ---------- WARNING has documentation ----------

def test_warning_items_have_evidence(checks):
    warnings = [c for c in checks if c["status"] == "WARNING"]
    for c in warnings:
        assert c["evidence"], (
            f"WARNING check {c['check_id']} has empty evidence"
        )


def test_warning_items_have_next_action(checks):
    warnings = [c for c in checks if c["status"] == "WARNING"]
    for c in warnings:
        assert c["next_action"], (
            f"WARNING check {c['check_id']} has empty next_action"
        )


# ---------- Final status ----------

def test_final_status_not_unsafe(gate_json):
    """The final status must NOT be UNSAFE_OVERCLAIM."""
    final = gate_json["final_status"]
    assert final != "UNSAFE_OVERCLAIM", (
        "Final status is UNSAFE_OVERCLAIM — unsafe claims detected. "
        "Must fix all overclaim before release."
    )


def test_final_status_is_ready_with_limitations(gate_json):
    """For a well-documented project, the final status should be
    READY_WITH_LIMITATIONS (no FAIL, all BLOCKED documented)."""
    final = gate_json["final_status"]
    assert final == "READY_WITH_LIMITATIONS", (
        f"Expected READY_WITH_LIMITATIONS, got {final}. "
        f"This means either FAIL items exist, BLOCKED items lack reasons, "
        f"or all issues are private-data-related."
    )


# ---------- Category-specific checks ----------

def test_mainline_gate_passes(checks):
    """All mainline checks (category 1) must PASS — V3.17 must be the
    current mainline with no unsafe claims."""
    mainline = [c for c in checks if c["category"] == "1. Mainline"]
    for c in mainline:
        assert c["status"] == "PASS", (
            f"Mainline check {c['check_id']} is {c['status']}, expected PASS. "
            f"Mainline gate is P0 — must be fully passing."
        )


def test_dataset_gate_passes(checks):
    """All dataset checks (category 2) must PASS — dataset must be locked
    with correct counts and silver status documented."""
    dataset = [c for c in checks if c["category"] == "2. Dataset"]
    for c in dataset:
        assert c["status"] == "PASS", (
            f"Dataset check {c['check_id']} is {c['status']}, expected PASS. "
            f"Dataset gate is P0 — must be fully passing."
        )


def test_leakage_no_fail(checks):
    """Leakage gate (category 5) must have no FAIL — safety-critical."""
    leakage = [c for c in checks if c["category"] == "5. Leakage"]
    for c in leakage:
        assert c["status"] != "FAIL", (
            f"Leakage check {c['check_id']} is FAIL — safety-critical leakage issue"
        )


def test_release_no_fail(checks):
    """Release gate (category 9) must have no FAIL — release safety."""
    release = [c for c in checks if c["category"] == "9. Release"]
    for c in release:
        assert c["status"] != "FAIL", (
            f"Release check {c['check_id']} is FAIL — release safety issue"
        )


def test_complexity_disclaimer_present(checks):
    """Complexity gate must verify the required disclaimer is present."""
    complexity = [c for c in checks if c["category"] == "7. Complexity"]
    disclaimer_check = [c for c in complexity if "disclaimer" in c["description"].lower()]
    assert disclaimer_check, "No disclaimer check in complexity gate"
    for c in disclaimer_check:
        assert c["status"] == "PASS", (
            f"Complexity disclaimer check {c['check_id']} is {c['status']}, expected PASS. "
            f"The summary must contain 'This does not prove rules generally beat learned models'."
        )


# ---------- MD format checks ----------

def test_md_has_scoring_legend(gate_md_text):
    assert "## Scoring legend" in gate_md_text, (
        "Gate MD missing Scoring legend section"
    )


def test_md_has_final_status_legend(gate_md_text):
    assert "## Final status legend" in gate_md_text, (
        "Gate MD missing Final status legend section"
    )


def test_md_has_blocked_items_section(gate_md_text, gate_json):
    blocked = gate_json.get("blocked_items", [])
    if blocked:
        assert "### Blocked items" in gate_md_text, (
            "Gate MD missing Blocked items section despite having blocked items"
        )


def test_md_has_warning_items_section(gate_md_text, gate_json):
    warnings = gate_json.get("warning_items", [])
    if warnings:
        assert "### Warning items" in gate_md_text, (
            "Gate MD missing Warning items section despite having warning items"
        )


def test_md_has_full_check_details(gate_md_text):
    assert "## Full Check Details" in gate_md_text, (
        "Gate MD missing Full Check Details section"
    )
