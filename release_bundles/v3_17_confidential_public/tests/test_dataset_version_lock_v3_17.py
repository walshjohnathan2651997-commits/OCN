"""tests/test_dataset_version_lock_v3_17.py — Dataset version lock tests.

Verifies that the locked SimClaim Strict Silver Diagnostic Set v1 CSV
matches the immutable properties recorded in
docs/dataset_version_lock_v3_17.md.

If any test in this file fails, the dataset has been modified since
the lock was created. The lock document must be explicitly updated
(and the version bumped) before these tests will pass again.

Hard boundaries enforced:
  - Does NOT modify the source CSV.
  - Does NOT fill final_label / gold_label.
  - Does NOT set human_audited to True.
  - Does NOT output claim_text / evidence_text raw values.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "data" / "simclaim_all92_candidate_pool_v1" / "strict_silver_max_v1" / "strict_silver_max_candidates_v1.csv"
LOCK_DOC_PATH = REPO_ROOT / "docs" / "dataset_version_lock_v3_17.md"

# Locked values — must match docs/dataset_version_lock_v3_17.md
LOCKED_SHA256 = "13d6c66171cf54e1a456d5ef8674f00f91939aa79a60f0c65066f2a3ebe0a812"
LOCKED_ROW_COUNT = 444
LOCKED_GROUP_COUNT = 111
LOCKED_COLUMN_COUNT = 36
LOCKED_LABEL_COUNTS = {
    "supported": 111,
    "mild_scope_overclaim": 111,
    "strong_action_overclaim": 111,
    "contradiction_candidate": 111,
}
LOCKED_DOMAIN_COUNTS = {
    "autonomous_driving": 140,
    "policy_simulation": 84,
    "digital_twin": 68,
    "cyber_defense": 64,
    "marl": 52,
    "robotics": 36,
}


@pytest.fixture(scope="module")
def df():
    if not CSV_PATH.exists():
        pytest.skip(f"CSV not found: {CSV_PATH} (private data not available in CI)")
    return pd.read_csv(CSV_PATH, keep_default_na=False)


@pytest.fixture(scope="module")
def csv_sha256():
    if not CSV_PATH.exists():
        pytest.skip(f"CSV not found: {CSV_PATH}")
    h = hashlib.sha256()
    with open(CSV_PATH, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------- Lock document existence ----------

def test_lock_document_exists():
    assert LOCK_DOC_PATH.exists(), (
        f"Dataset version lock document missing: {LOCK_DOC_PATH}. "
        "Create it with the locked SHA256, row count, group count, "
        "label counts, and domain counts."
    )


def test_lock_document_has_dataset_name():
    text = LOCK_DOC_PATH.read_text(encoding="utf-8")
    assert "SimClaim Strict Silver Diagnostic Set v1" in text, (
        "Lock document must name the dataset 'SimClaim Strict Silver Diagnostic Set v1'."
    )


def test_lock_document_has_role():
    text = LOCK_DOC_PATH.read_text(encoding="utf-8")
    assert "controlled silver diagnostic set" in text.lower(), (
        "Lock document must state the role as 'controlled silver diagnostic set'."
    )


def test_lock_document_has_not_claims():
    text = LOCK_DOC_PATH.read_text(encoding="utf-8")
    required_not = [
        "gold benchmark",
        "human-audited benchmark",
        "natural prevalence dataset",
        "general scientific claim benchmark",
    ]
    missing = [n for n in required_not if n not in text.lower()]
    assert not missing, f"Lock document missing 'Not' claims: {missing}"


def test_lock_document_has_safe_caveat():
    raw = LOCK_DOC_PATH.read_text(encoding="utf-8")
    # Normalize whitespace to handle markdown line wraps (newlines -> spaces,
    # collapse runs of whitespace). Also strip blockquote `>` markers that
    # would otherwise split phrases across wrapped lines.
    text = re.sub(r">\s*", "", raw)
    text = re.sub(r"\s+", " ", text)
    # The caveat must appear (allowing for line wraps in markdown).
    # Check for key phrases.
    assert "source-traceable controlled silver diagnostic set" in text, (
        "Lock document must include the safe caveat."
    )
    assert "not gold or human-audited" in text, (
        "Lock document must state labels are not gold or human-audited."
    )
    assert "not be interpreted as benchmark-level model validation" in text, (
        "Lock document must state results should not be interpreted as "
        "benchmark-level model validation."
    )


def test_lock_document_has_sha256():
    text = LOCK_DOC_PATH.read_text(encoding="utf-8")
    assert LOCKED_SHA256 in text, (
        f"Lock document must record SHA256 = {LOCKED_SHA256}"
    )


def test_lock_document_has_row_count():
    text = LOCK_DOC_PATH.read_text(encoding="utf-8")
    assert "444" in text, "Lock document must record row count = 444"


def test_lock_document_has_group_count():
    text = LOCK_DOC_PATH.read_text(encoding="utf-8")
    assert "111" in text, "Lock document must record group count = 111"


def test_lock_document_has_known_limitations():
    text = LOCK_DOC_PATH.read_text(encoding="utf-8")
    assert "Known limitations" in text, (
        "Lock document must include a 'Known limitations' section."
    )


# ---------- CSV integrity ----------

def test_csv_exists():
    assert CSV_PATH.exists(), f"Locked CSV missing: {CSV_PATH}"


def test_csv_sha256_matches_lock(csv_sha256):
    assert csv_sha256 == LOCKED_SHA256, (
        f"CSV SHA256 mismatch.\n"
        f"  Expected (locked): {LOCKED_SHA256}\n"
        f"  Actual (current):  {csv_sha256}\n"
        f"The CSV has been modified since the lock was created. "
        f"If this is intentional, update docs/dataset_version_lock_v3_17.md "
        f"and LOCKED_SHA256 in this test."
    )


def test_lock_doc_sha256_matches_actual_csv(csv_sha256):
    """Lock document must contain the actual CSV SHA256."""
    text = LOCK_DOC_PATH.read_text(encoding="utf-8")
    assert csv_sha256 in text, (
        f"Lock document does not contain the actual CSV SHA256 ({csv_sha256}). "
        f"Update docs/dataset_version_lock_v3_17.md."
    )


def test_row_count(df):
    assert len(df) == LOCKED_ROW_COUNT, (
        f"Row count mismatch: expected {LOCKED_ROW_COUNT}, got {len(df)}"
    )


def test_column_count(df):
    assert len(df.columns) == LOCKED_COLUMN_COUNT, (
        f"Column count mismatch: expected {LOCKED_COLUMN_COUNT}, "
        f"got {len(df.columns)}"
    )


def test_group_count(df):
    n_groups = df["target_candidate_group_id"].nunique()
    assert n_groups == LOCKED_GROUP_COUNT, (
        f"Group count mismatch: expected {LOCKED_GROUP_COUNT}, got {n_groups}"
    )


def test_label_counts(df):
    counts = df["candidate_label_guess"].value_counts().to_dict()
    for label, expected in LOCKED_LABEL_COUNTS.items():
        actual = counts.get(label, 0)
        assert actual == expected, (
            f"Label '{label}' count mismatch: expected {expected}, got {actual}"
        )


def test_four_labels_each_111(df):
    counts = df["candidate_label_guess"].value_counts().to_dict()
    assert all(counts.get(label, 0) == 111 for label in LOCKED_LABEL_COUNTS), (
        f"Expected each of the 4 labels to have 111 candidates. "
        f"Got: {counts}"
    )


def test_domain_counts(df):
    counts = df["domain"].value_counts().to_dict()
    for domain, expected in LOCKED_DOMAIN_COUNTS.items():
        actual = counts.get(domain, 0)
        assert actual == expected, (
            f"Domain '{domain}' count mismatch: expected {expected}, got {actual}"
        )


# ---------- Critical field invariants ----------

def test_human_audited_all_false(df):
    s = df["human_audited"].astype(str).str.strip().str.lower()
    n_true = (s == "true").sum()
    n_false = (s == "false").sum()
    assert n_true == 0 and n_false == LOCKED_ROW_COUNT, (
        f"human_audited must be False for all {LOCKED_ROW_COUNT} rows. "
        f"Got true={n_true}, false={n_false}."
    )


def test_gold_label_all_empty(df):
    s = df["gold_label"].astype(str).str.strip()
    n_nonempty = (s != "").sum()
    assert n_nonempty == 0, (
        f"gold_label must be empty for all rows. "
        f"Found {n_nonempty} nonempty values."
    )


def test_final_label_all_empty(df):
    s = df["final_label"].astype(str).str.strip()
    n_nonempty = (s != "").sum()
    assert n_nonempty == 0, (
        f"final_label must be empty for all rows. "
        f"Found {n_nonempty} nonempty values."
    )


def test_source_trace_complete_all_true(df):
    s = df["source_trace_complete"].astype(str).str.strip().str.lower()
    n_true = (s == "true").sum()
    n_false = (s == "false").sum()
    assert n_true == LOCKED_ROW_COUNT and n_false == 0, (
        f"source_trace_complete must be True for all {LOCKED_ROW_COUNT} rows. "
        f"Got true={n_true}, false={n_false}."
    )


def test_silver_label_source_all_candidate_label_guess(df):
    counts = df["silver_label_source"].value_counts().to_dict()
    n_clg = counts.get("candidate_label_guess", 0)
    assert n_clg == LOCKED_ROW_COUNT, (
        f"silver_label_source must be 'candidate_label_guess' for all "
        f"{LOCKED_ROW_COUNT} rows. Got candidate_label_guess={n_clg}, "
        f"other={LOCKED_ROW_COUNT - n_clg}."
    )


def test_annotation_status_all_ai_preannotated(df):
    counts = df["annotation_status"].value_counts().to_dict()
    n_ai = counts.get("ai_preannotated", 0)
    assert n_ai == LOCKED_ROW_COUNT, (
        f"annotation_status must be 'ai_preannotated' for all rows. "
        f"Got ai_preannotated={n_ai}."
    )


def test_dataset_role_all_strict_silver_train_candidate(df):
    counts = df["dataset_role"].value_counts().to_dict()
    n_role = counts.get("strict_silver_train_candidate", 0)
    assert n_role == LOCKED_ROW_COUNT, (
        f"dataset_role must be 'strict_silver_train_candidate' for all rows. "
        f"Got strict_silver_train_candidate={n_role}."
    )


# ---------- Hash uniqueness ----------

def test_evidence_text_sha256_unique_is_111(df):
    n_unique = df["evidence_text_sha256"].nunique()
    assert n_unique == 111, (
        f"evidence_text_sha256 must have 111 unique values (4 claims per group "
        f"share evidence). Got {n_unique}."
    )


def test_claim_text_sha256_unique_is_444(df):
    n_unique = df["claim_text_sha256"].nunique()
    assert n_unique == 444, (
        f"claim_text_sha256 must have 444 unique values (all claims unique). "
        f"Got {n_unique}."
    )


def test_no_duplicate_claim_text_sha256(df):
    n_dups = df["claim_text_sha256"].duplicated().sum()
    assert n_dups == 0, (
        f"Found {n_dups} duplicate claim_text_sha256 values. "
        f"All 444 claim hashes must be unique."
    )


# ---------- Group completeness ----------

def test_all_groups_have_four_labels(df):
    group_label_nunique = df.groupby("target_candidate_group_id")["candidate_label_guess"].nunique()
    n_complete = (group_label_nunique == 4).sum()
    n_missing = (group_label_nunique != 4).sum()
    assert n_complete == LOCKED_GROUP_COUNT and n_missing == 0, (
        f"All {LOCKED_GROUP_COUNT} groups must have 4 labels complete. "
        f"Got complete={n_complete}, missing={n_missing}."
    )


# ---------- Schema presence ----------

def test_required_columns_present(df):
    required = [
        "candidate_id",
        "target_candidate_group_id",
        "source_id",
        "domain",
        "evidence_text",
        "evidence_text_sha256",
        "candidate_label_guess",
        "claim_text",
        "claim_text_sha256",
        "claim_generation_policy",
        "annotation_status",
        "human_audited",
        "final_label",
        "gold_label",
        "source_trace_complete",
        "silver_label_source",
        "dataset_role",
    ]
    missing = [c for c in required if c not in df.columns]
    assert not missing, f"Missing required columns: {missing}"


# ---------- Provenance ledger outputs (only if reports exist) ----------

def test_provenance_ledger_json_exists_or_skip():
    json_path = REPO_ROOT / "reports" / "dataset_provenance_ledger_v3_17.json"
    if not json_path.exists():
        pytest.skip(
            "Provenance ledger JSON not found. Run "
            "scripts/build_dataset_provenance_ledger_v1.py to generate it."
        )


def test_provenance_ledger_md_exists_or_skip():
    md_path = REPO_ROOT / "reports" / "dataset_provenance_ledger_v3_17.md"
    if not md_path.exists():
        pytest.skip(
            "Provenance ledger MD not found. Run "
            "scripts/build_dataset_provenance_ledger_v1.py to generate it."
        )


def test_provenance_ledger_csv_summary_exists_or_skip():
    csv_path = REPO_ROOT / "reports" / "dataset_schema_summary_v3_17.csv"
    if not csv_path.exists():
        pytest.skip(
            "Schema summary CSV not found. Run "
            "scripts/build_dataset_provenance_ledger_v1.py to generate it."
        )


def test_provenance_ledger_json_no_raw_text():
    """Ledger JSON must NOT contain claim_text or evidence_text raw values."""
    import json

    json_path = REPO_ROOT / "reports" / "dataset_provenance_ledger_v3_17.json"
    if not json_path.exists():
        pytest.skip("Provenance ledger JSON not found.")
    ledger = json.loads(json_path.read_text(encoding="utf-8"))

    # The ledger may reference field NAMES (e.g. "claim_text" as a key in
    # redacted_fields_present_in_csv), but must NOT contain actual claim
    # text values. We check that no value looks like a long sentence.
    def _check_no_long_strings(obj, path=""):
        if isinstance(obj, str):
            # Allow SHA256 hashes (64 hex chars), paths, short labels.
            if len(obj) > 200 and not re.match(r"^[0-9a-f]{64}$", obj):
                if " " in obj and "." in obj:
                    pytest.fail(
                        f"Ledger contains a suspiciously long string at {path} "
                        f"(len={len(obj)}). Possible raw text leak: {obj[:80]}..."
                    )
        elif isinstance(obj, dict):
            for k, v in obj.items():
                _check_no_long_strings(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                _check_no_long_strings(v, f"{path}[{i}]")

    _check_no_long_strings(ledger)


def test_provenance_ledger_md_no_raw_claim_text():
    """Ledger MD must NOT contain raw claim_text or evidence_text values.

    We check that none of the long sentences from the CSV appear in the MD.
    """
    md_path = REPO_ROOT / "reports" / "dataset_provenance_ledger_v3_17.md"
    if not md_path.exists():
        pytest.skip("Provenance ledger MD not found.")
    if not CSV_PATH.exists():
        pytest.skip("CSV not found; cannot sample raw text for leak check.")
    text = md_path.read_text(encoding="utf-8")
    df = pd.read_csv(CSV_PATH, keep_default_na=False)

    # Sample a few claim_text values and verify none appear verbatim.
    for sample_idx in [0, 1, 2, 111, 222, 333, 443]:
        if sample_idx < len(df):
            claim = df.iloc[sample_idx]["claim_text"]
            if claim and len(claim) > 30:
                assert claim not in text, (
                    f"Raw claim_text from row {sample_idx} found in ledger MD. "
                    f"Leak: {claim[:80]}..."
                )
            evidence = df.iloc[sample_idx]["evidence_text"]
            if evidence and len(evidence) > 30:
                assert evidence not in text, (
                    f"Raw evidence_text from row {sample_idx} found in ledger MD. "
                    f"Leak: {evidence[:80]}..."
                )


def test_schema_summary_csv_no_raw_text():
    """Schema summary CSV must NOT contain raw claim_text or evidence_text."""
    csv_path = REPO_ROOT / "reports" / "dataset_schema_summary_v3_17.csv"
    if not csv_path.exists():
        pytest.skip("Schema summary CSV not found.")
    if not CSV_PATH.exists():
        pytest.skip("Source CSV not found; cannot sample raw text.")
    summary = pd.read_csv(csv_path, keep_default_na=False)
    src = pd.read_csv(CSV_PATH, keep_default_na=False)

    # The summary is one row. Check it has no columns matching raw text fields.
    raw_cols = {"claim_text", "evidence_text", "generation_notes", "title", "url"}
    leaked = raw_cols.intersection(set(summary.columns))
    assert not leaked, (
        f"Schema summary CSV has raw-text columns: {leaked}. "
        f"Only hashes and aggregate counts are allowed."
    )

    # Check no cell value matches a sampled raw claim/evidence.
    for sample_idx in [0, 111, 333]:
        if sample_idx < len(src):
            claim = src.iloc[sample_idx]["claim_text"]
            evidence = src.iloc[sample_idx]["evidence_text"]
            for col in summary.columns:
                val = str(summary.iloc[0][col])
                if claim and len(claim) > 30:
                    assert claim not in val, (
                        f"Raw claim_text leaked into schema summary column '{col}'."
                    )
                if evidence and len(evidence) > 30:
                    assert evidence not in val, (
                        f"Raw evidence_text leaked into schema summary column '{col}'."
                    )
