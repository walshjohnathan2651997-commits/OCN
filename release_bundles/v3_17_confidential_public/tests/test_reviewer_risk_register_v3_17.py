"""tests/test_reviewer_risk_register_v3_17.py — Reviewer risk register tests.

Verifies that the reviewer risk register, response playbook, and paper
risk table are correctly generated and contain safe, non-overclaiming
responses for all anticipated reviewer attacks.

Hard boundaries enforced:
  - No exaggeration (no "gold benchmark", "SOTA", "human-audited" as
    current claims in safe_response fields).
  - No fabricated experiments (missing/blocked results must be marked).
  - Silver data is never called gold.
  - Each high-severity risk must have a safe_response.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTER_PATH = REPO_ROOT / "docs" / "reviewer_risk_register_v3_17.md"
PLAYBOOK_PATH = REPO_ROOT / "docs" / "reviewer_response_playbook_v3_17.md"
TABLE_PATH = REPO_ROOT / "paper_assets" / "v3_17_confidential" / "reviewer_risk_table.md"

EXPECTED_RISK_IDS = [f"R{i:02d}" for i in range(1, 11)]
REQUIRED_FIELDS = [
    "risk_id",
    "reviewer_attack",
    "severity",
    "evidence_needed",
    "current_evidence_file",
    "status",
    "safe_response",
    "paper_section_to_address",
    "remaining_limitation",
]
VALID_SEVERITIES = {"high", "medium", "low"}
VALID_STATUSES = {"done", "partial", "blocked", "missing", "pending", "unknown"}

# Keywords that, if found in a safe_response as a current claim, indicate
# defensive overclaim. We check that these do NOT appear as positive
# assertions (they may appear in negated form like "not a gold benchmark").
OVERCLAIM_PATTERNS = [
    "is a gold benchmark",
    "is gold",
    "human-validated",
    "human-audited benchmark",
    "state-of-the-art",
    "SOTA detector",
    "automatic peer reviewer",
    "general scientific overstatement detector",
    "full CESE-OCN architecture validated",
    "outperforms LLM",
    "outperforms all",
]


# ---------- File existence ----------

def test_register_exists():
    assert REGISTER_PATH.exists(), (
        f"Reviewer risk register missing: {REGISTER_PATH}"
    )


def test_playbook_exists():
    assert PLAYBOOK_PATH.exists(), (
        f"Reviewer response playbook missing: {PLAYBOOK_PATH}"
    )


def test_paper_table_exists():
    assert TABLE_PATH.exists(), (
        f"Paper risk table missing: {TABLE_PATH}"
    )


# ---------- Risk count and IDs ----------

def test_register_has_10_risks():
    text = REGISTER_PATH.read_text(encoding="utf-8")
    # Count risk detail headers like "### R01 — ..."
    matches = re.findall(r"^### (R\d{2})\s", text, re.MULTILINE)
    assert len(matches) == 10, (
        f"Expected 10 risks in register, found {len(matches)}: {matches}"
    )


def test_register_has_all_expected_risk_ids():
    text = REGISTER_PATH.read_text(encoding="utf-8")
    for rid in EXPECTED_RISK_IDS:
        assert rid in text, f"Risk {rid} not found in register"


def test_table_has_all_risk_ids():
    text = TABLE_PATH.read_text(encoding="utf-8")
    for rid in EXPECTED_RISK_IDS:
        assert rid in text, f"Risk {rid} not found in paper table"


# ---------- Required fields ----------

def test_register_has_all_required_fields():
    text = REGISTER_PATH.read_text(encoding="utf-8")
    for field in REQUIRED_FIELDS:
        # Check that the field label appears in the register.
        assert field in text, (
            f"Required field '{field}' not found in register"
        )


def test_each_risk_has_safe_response():
    text = REGISTER_PATH.read_text(encoding="utf-8")
    # Split by risk detail headers.
    sections = re.split(r"^### (R\d{2})\s", text, flags=re.MULTILINE)
    # sections[0] is preamble; then pairs of (risk_id, body).
    for i in range(1, len(sections), 2):
        rid = sections[i]
        body = sections[i + 1] if i + 1 < len(sections) else ""
        assert "**safe_response:**" in body, (
            f"Risk {rid} missing safe_response field"
        )
        # Verify the safe_response is non-empty (more than just the label).
        match = re.search(r"\*\*safe_response:\*\*\s*(.+?)(?=\n- \*\*|\n###|\Z)", body, re.DOTALL)
        assert match, f"Risk {rid} safe_response is empty"
        response_text = match.group(1).strip()
        assert len(response_text) > 20, (
            f"Risk {rid} safe_response is too short ({len(response_text)} chars): "
            f"{response_text[:80]}"
        )


def test_each_risk_has_remaining_limitation():
    text = REGISTER_PATH.read_text(encoding="utf-8")
    sections = re.split(r"^### (R\d{2})\s", text, flags=re.MULTILINE)
    for i in range(1, len(sections), 2):
        rid = sections[i]
        body = sections[i + 1] if i + 1 < len(sections) else ""
        assert "**remaining_limitation:**" in body, (
            f"Risk {rid} missing remaining_limitation field"
        )


def test_each_risk_has_paper_section():
    text = REGISTER_PATH.read_text(encoding="utf-8")
    sections = re.split(r"^### (R\d{2})\s", text, flags=re.MULTILINE)
    for i in range(1, len(sections), 2):
        rid = sections[i]
        body = sections[i + 1] if i + 1 < len(sections) else ""
        assert "**paper_section_to_address:**" in body, (
            f"Risk {rid} missing paper_section_to_address field"
        )


# ---------- Severity ----------

def test_all_severities_valid():
    text = REGISTER_PATH.read_text(encoding="utf-8")
    # Find all "- **severity:** X" patterns.
    matches = re.findall(r"\*\*severity:\*\*\s*(\w+)", text)
    assert len(matches) == 10, f"Expected 10 severity entries, found {len(matches)}"
    for sev in matches:
        assert sev in VALID_SEVERITIES, (
            f"Invalid severity '{sev}'. Valid: {VALID_SEVERITIES}"
        )


def test_high_severity_risks_present():
    text = REGISTER_PATH.read_text(encoding="utf-8")
    matches = re.findall(r"\*\*severity:\*\*\s*(\w+)", text)
    n_high = sum(1 for s in matches if s == "high")
    assert n_high >= 4, (
        f"Expected at least 4 high-severity risks, found {n_high}. "
        f"R01, R02, R06, R10 should be high."
    )


# ---------- Status ----------

def test_all_statuses_valid():
    text = REGISTER_PATH.read_text(encoding="utf-8")
    matches = re.findall(r"\*\*status:\*\*\s*(\w+)", text)
    assert len(matches) == 10, f"Expected 10 status entries, found {len(matches)}"
    for status in matches:
        assert status in VALID_STATUSES, (
            f"Invalid status '{status}'. Valid: {VALID_STATUSES}"
        )


def test_human_audit_risk_is_partial_or_blocked():
    """R06 (no human audit) must be 'partial' or 'blocked', not 'done'."""
    text = REGISTER_PATH.read_text(encoding="utf-8")
    # Find R06 section.
    match = re.search(r"### R06\s.*?\*\*status:\*\*\s*(\w+)", text, re.DOTALL)
    assert match, "R06 section not found in register"
    status = match.group(1)
    assert status in ("partial", "blocked"), (
        f"R06 (human audit) status must be 'partial' or 'blocked', got '{status}'. "
        f"The human audit is not complete."
    )


# ---------- No defensive overclaim ----------

def test_no_overclaim_in_safe_responses():
    """safe_response fields must NOT contain overclaim patterns as positive assertions."""
    text = REGISTER_PATH.read_text(encoding="utf-8")
    # Extract all safe_response bodies.
    responses = re.findall(
        r"\*\*safe_response:\*\*\s*(.+?)(?=\n- \*\*|\n###|\Z)",
        text,
        re.DOTALL,
    )
    assert len(responses) == 10, (
        f"Expected 10 safe_response entries, found {len(responses)}"
    )
    for i, response in enumerate(responses):
        response_lower = response.lower()
        for pattern in OVERCLAIM_PATTERNS:
            # Allow the pattern if it's preceded by "not"/"no"/"never" within
            # 80 chars (i.e., it's a negation, not a positive claim). The wider
            # window handles constructions like "No silver label will be
            # re-described as gold or human-validated."
            idx = response_lower.find(pattern)
            if idx == -1:
                continue
            prefix = response_lower[max(0, idx - 80):idx]
            if "not " in prefix or "no " in prefix or "never " in prefix:
                continue
            pytest.fail(
                f"Overclaim pattern '{pattern}' found in safe_response "
                f"(response {i + 1}) as a positive assertion. "
                f"Context: ...{response[max(0, idx - 20):idx + len(pattern) + 20]}..."
            )


def test_no_overclaim_in_paper_table_caveat():
    """Paper risk table's safe caveat must NOT contain overclaim as positive assertions.

    Note: the reviewer_attack column naturally contains phrases like
    'general scientific overstatement detector' (that's the attack being
    described). We only check the safe_caveat section, not the attack column.
    """
    text = TABLE_PATH.read_text(encoding="utf-8")
    # Extract only the safe caveat section (after "Safe caveat:").
    match = re.search(r"\*\*Safe caveat:\*\*\s*(.+)", text, re.DOTALL)
    if not match:
        pytest.skip("No safe caveat section found in paper table.")
    caveat = match.group(1).lower()
    for pattern in OVERCLAIM_PATTERNS:
        idx = caveat.find(pattern)
        if idx == -1:
            continue
        prefix = caveat[max(0, idx - 80):idx]
        if "not " in prefix or "no " in prefix or "never " in prefix:
            continue
        pytest.fail(
            f"Overclaim pattern '{pattern}' found in paper table safe caveat. "
            f"Context: ...{caveat[max(0, idx - 20):idx + len(pattern) + 20]}..."
        )


# ---------- Safe caveat ----------

def test_paper_table_has_safe_caveat():
    text = TABLE_PATH.read_text(encoding="utf-8")
    # Normalize whitespace for matching.
    normalized = re.sub(r"\s+", " ", text)
    assert "source-traceable controlled silver diagnostic" in normalized, (
        "Paper risk table must include the safe caveat."
    )
    assert "not gold or human-audited" in normalized, (
        "Paper risk table must state labels are not gold or human-audited."
    )


def test_register_has_safe_caveat_or_positioning():
    """Register must include safe positioning language."""
    text = REGISTER_PATH.read_text(encoding="utf-8").lower()
    assert "silver" in text, "Register must mention 'silver' diagnostic"
    assert "not" in text, "Register must include negation of gold/human-audited"


def test_playbook_has_forbidden_patterns_section():
    """Playbook must document forbidden response patterns."""
    text = PLAYBOOK_PATH.read_text(encoding="utf-8")
    assert "Forbidden" in text or "forbidden" in text, (
        "Playbook must have a 'Forbidden response patterns' section."
    )


def test_playbook_has_allowed_patterns_section():
    """Playbook must document allowed response patterns."""
    text = PLAYBOOK_PATH.read_text(encoding="utf-8")
    assert "Allowed" in text or "allowed" in text, (
        "Playbook must have an 'Allowed response patterns' section."
    )


# ---------- Specific risk content ----------

def test_r01_addresses_silver_dataset():
    text = REGISTER_PATH.read_text(encoding="utf-8")
    match = re.search(r"### R01\s.*?(?=### R02|\Z)", text, re.DOTALL)
    assert match, "R01 section not found"
    body = match.group(0).lower()
    assert "silver" in body, "R01 must mention 'silver'"
    assert "leakage" in body, "R01 must mention leakage audit"


def test_r02_addresses_template_cues():
    text = REGISTER_PATH.read_text(encoding="utf-8")
    match = re.search(r"### R02\s.*?(?=### R03|\Z)", text, re.DOTALL)
    assert match, "R02 section not found"
    body = match.group(0).lower()
    assert "claim-only" in body or "claim_only" in body, (
        "R02 must mention claim-only baseline"
    )


def test_r04_addresses_contribution():
    text = REGISTER_PATH.read_text(encoding="utf-8")
    match = re.search(r"### R04\s.*?(?=### R05|\Z)", text, re.DOTALL)
    assert match, "R04 section not found"
    body = match.group(0).lower()
    assert "format-shift" in body or "format shift" in body, (
        "R04 must mention format-shift as the contribution"
    )


def test_r05_addresses_no_llm():
    text = REGISTER_PATH.read_text(encoding="utf-8")
    match = re.search(r"### R05\s.*?(?=### R06|\Z)", text, re.DOTALL)
    assert match, "R05 section not found"
    body = match.group(0).lower()
    assert "confidential" in body or "no-api" in body or "no api" in body, (
        "R05 must mention confidentiality/no-API constraint"
    )


def test_r06_addresses_human_audit_pending():
    text = REGISTER_PATH.read_text(encoding="utf-8")
    match = re.search(r"### R06\s.*?(?=### R07|\Z)", text, re.DOTALL)
    assert match, "R06 section not found"
    body = match.group(0).lower()
    assert "pending" in body or "not complete" in body or "not done" in body, (
        "R06 must acknowledge human audit is pending/incomplete"
    )


def test_r10_addresses_future_architecture():
    text = REGISTER_PATH.read_text(encoding="utf-8")
    match = re.search(r"### R10\s.*?(?=## |\Z)", text, re.DOTALL)
    assert match, "R10 section not found"
    body = match.group(0).lower()
    assert "future" in body, "R10 must mention full CESE-OCN is future work"
    assert "not current" in body or "not the current" in body, (
        "R10 must state full CESE-OCN is not the current claim"
    )


# ---------- No raw text leak ----------

def test_register_no_claim_evidence_raw_text():
    """Register must not contain raw claim_text or evidence_text from the CSV."""
    register_text = REGISTER_PATH.read_text(encoding="utf-8")
    csv_path = REPO_ROOT / "data" / "simclaim_all92_candidate_pool_v1" / "strict_silver_max_v1" / "strict_silver_max_candidates_v1.csv"
    if not csv_path.exists():
        pytest.skip("Source CSV not found; cannot sample raw text.")
    import pandas as pd
    df = pd.read_csv(csv_path, keep_default_na=False)
    for idx in [0, 111, 333]:
        if idx < len(df):
            claim = df.iloc[idx]["claim_text"]
            evidence = df.iloc[idx]["evidence_text"]
            if claim and len(claim) > 40:
                assert claim not in register_text, (
                    f"Raw claim_text from row {idx} leaked into register."
                )
            if evidence and len(evidence) > 40:
                assert evidence not in register_text, (
                    f"Raw evidence_text from row {idx} leaked into register."
                )
