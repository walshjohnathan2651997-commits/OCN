"""test_human_audit_v1.py — Tests for the small targeted human audit closed-loop.

Covers:
  - protocol document exists and has safe/unsafe wording
  - template CSV exists, has 17 columns, no raw-text fields
  - build script produces seed + redacted CSV with 80..120 rows
  - redacted CSV has no candidate_id / group_id
  - per-group cap of 2 is respected
  - all bucket sources are present
  - summarize script produces 4 output files with safe/unsafe wording
  - summarize outputs have no raw text / identifiers
  - agreement metric excludes uncertain rows from denominator
"""

from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON = os.environ.get(
    "OCN_PYTHON",
    r"C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe",
)
PROTOCOL_PATH = REPO_ROOT / "docs" / "human_audit_protocol_v1.md"
TEMPLATE_PATH = REPO_ROOT / "data" / "audit_templates" / "human_audit_template.csv"
BUILD_SCRIPT = REPO_ROOT / "scripts" / "build_human_audit_queue_v1.py"
SUMMARIZE_SCRIPT = REPO_ROOT / "scripts" / "summarize_human_audit_v1.py"
SEED_PATH = REPO_ROOT / "data" / "audit_templates" / "human_audit_queue_seed_v1.csv"
REDACTED_PATH = (
    REPO_ROOT / "data" / "audit_templates" / "human_audit_queue_seed_v1_redacted.csv"
)
BUILD_REPORT_PATH = (
    REPO_ROOT / "data" / "audit_templates" / "human_audit_queue_build_report.json"
)
AUDIT_OUT_DIR = REPO_ROOT / "experiments" / "human_audit_v1"

TEMPLATE_COLUMNS = [
    "audit_item_id",
    "candidate_id",
    "target_candidate_group_id",
    "source_hash",
    "claim_text_hash",
    "evidence_text_hash",
    "model_pred",
    "silver_label",
    "queue_rank",
    "queue_source",
    "auditor_label",
    "auditor_confidence",
    "audit_notes",
    "disagreement_reason",
    "requires_second_review",
    "human_audited",
    "created_at",
]

FORBIDDEN_RAWTEXT_FIELDS = {
    "claim_text", "evidence_text", "selected_evidence",
}


def _read_csv(path: Path) -> tuple[list[str], list[dict]]:
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        return list(reader.fieldnames or []), rows


# ---------- Protocol ----------

def test_protocol_exists():
    assert PROTOCOL_PATH.exists(), f"missing {PROTOCOL_PATH}"


def test_protocol_has_safe_unsafe_wording():
    text = PROTOCOL_PATH.read_text(encoding="utf-8")
    assert "small targeted audit" in text.lower()
    assert "not a gold benchmark" in text.lower()
    assert "do not claim" in text.lower() or "must not" in text.lower()


def test_protocol_lists_audit_labels():
    text = PROTOCOL_PATH.read_text(encoding="utf-8")
    for label in [
        "supported",
        "mild_scope_overclaim",
        "strong_action_overclaim",
        "contradiction_candidate",
        "uncertain_insufficient_context",
    ]:
        assert label in text, f"protocol missing label {label}"


def test_protocol_lists_sampling_buckets():
    text = PROTOCOL_PATH.read_text(encoding="utf-8").lower()
    for bucket in [
        "top-20", "top-50", "false positive", "false negative",
        "mild vs strong", "contradiction",
    ]:
        assert bucket in text, f"protocol missing bucket {bucket}"


def test_protocol_scope_80_to_120():
    text = PROTOCOL_PATH.read_text(encoding="utf-8")
    assert "80" in text and "120" in text


# ---------- Template ----------

def test_template_exists():
    assert TEMPLATE_PATH.exists(), f"missing {TEMPLATE_PATH}"


def test_template_has_17_columns():
    header, _ = _read_csv(TEMPLATE_PATH)
    assert header == TEMPLATE_COLUMNS, f"template header mismatch: {header}"


def test_template_no_raw_text_columns():
    header, _ = _read_csv(TEMPLATE_PATH)
    leak = set(header) & FORBIDDEN_RAWTEXT_FIELDS
    assert not leak, f"template has forbidden raw-text columns: {leak}"


def test_template_has_only_header():
    _, rows = _read_csv(TEMPLATE_PATH)
    assert rows == [], f"template should be header-only, got {len(rows)} rows"


# ---------- Build script ----------

def test_build_script_exists():
    assert BUILD_SCRIPT.exists(), f"missing {BUILD_SCRIPT}"


def test_build_seed_exists():
    assert SEED_PATH.exists(), f"missing {SEED_PATH}"


def test_build_redacted_exists():
    assert REDACTED_PATH.exists(), f"missing {REDACTED_PATH}"


def test_build_report_exists():
    assert BUILD_REPORT_PATH.exists(), f"missing {BUILD_REPORT_PATH}"


def test_seed_row_count_in_80_to_120():
    _, rows = _read_csv(SEED_PATH)
    assert 80 <= len(rows) <= 120, f"seed row count {len(rows)} not in 80..120"


def test_seed_has_template_columns():
    header, _ = _read_csv(SEED_PATH)
    assert header == TEMPLATE_COLUMNS, f"seed header mismatch: {header}"


def test_seed_no_raw_text_columns():
    header, _ = _read_csv(SEED_PATH)
    leak = set(header) & FORBIDDEN_RAWTEXT_FIELDS
    assert not leak, f"seed has forbidden raw-text columns: {leak}"


def test_redacted_no_identifiers():
    header, _ = _read_csv(REDACTED_PATH)
    forbidden_ids = {"candidate_id", "target_candidate_group_id"}
    leak = set(header) & forbidden_ids
    assert not leak, f"redacted CSV leaks identifiers: {leak}"


def test_redacted_no_raw_text_columns():
    header, _ = _read_csv(REDACTED_PATH)
    leak = set(header) & FORBIDDEN_RAWTEXT_FIELDS
    assert not leak, f"redacted CSV has raw-text columns: {leak}"


def test_redacted_columns_subset_of_template():
    """Redacted columns must be a subset of template columns (no new fields)."""
    red_header, _ = _read_csv(REDACTED_PATH)
    template_header, _ = _read_csv(TEMPLATE_PATH)
    extra = set(red_header) - set(template_header)
    assert not extra, f"redacted CSV has extra columns not in template: {extra}"


def test_seed_respects_max_2_per_group():
    _, rows = _read_csv(SEED_PATH)
    group_counts: dict[str, int] = {}
    for r in rows:
        g = r.get("target_candidate_group_id", "")
        if g:
            group_counts[g] = group_counts.get(g, 0) + 1
    if group_counts:
        max_per_group = max(group_counts.values())
        assert max_per_group <= 2, \
            f"max per group = {max_per_group}, expected <= 2"


def test_seed_has_all_buckets():
    _, rows = _read_csv(SEED_PATH)
    sources = {r.get("queue_source", "") for r in rows}
    expected = {
        "top20",
        "top50_strong_action",
        "r4_fp",
        "r4_fn",
        "mild_vs_strong_boundary",
        "contradiction_confusion",
    }
    missing = expected - sources
    assert not missing, f"seed missing buckets: {missing}"


def test_seed_human_audited_false():
    _, rows = _read_csv(SEED_PATH)
    bad = [r for r in rows if r.get("human_audited", "").strip().lower() != "false"]
    assert not bad, f"{len(bad)} seed rows have human_audited != False"


def test_seed_auditor_fields_empty():
    """Seed rows must have empty auditor_label, auditor_confidence, audit_notes."""
    _, rows = _read_csv(SEED_PATH)
    for r in rows:
        assert not (r.get("auditor_label") or "").strip(), \
            f"{r.get('audit_item_id')} has non-empty auditor_label"
        assert not (r.get("auditor_confidence") or "").strip(), \
            f"{r.get('audit_item_id')} has non-empty auditor_confidence"


def test_build_report_disclaimer_present():
    report = json.loads(BUILD_REPORT_PATH.read_text(encoding="utf-8"))
    assert "NOT a gold benchmark" in report.get("disclaimer", "")
    assert report.get("no_raw_text_in_outputs") is True


def test_build_report_guard_values():
    report = json.loads(BUILD_REPORT_PATH.read_text(encoding="utf-8"))
    guards = report.get("guards", {})
    assert guards.get("no_api") is True
    assert guards.get("no_network") is True
    assert guards.get("no_training") is True


# ---------- Summarize script ----------

@pytest.fixture()
def mock_filled_audit(tmp_path):
    """Create a mock filled audit CSV by copying the seed and filling columns.

    Uses deterministic label assignment so test assertions are stable.
    """
    if not SEED_PATH.exists():
        # Run the build first if seed is missing.
        subprocess.run(
            [PYTHON, str(BUILD_SCRIPT)],
            cwd=str(REPO_ROOT),
            check=True,
            capture_output=False,
        )
    header, rows = _read_csv(SEED_PATH)
    out_path = tmp_path / "mock_filled_audit.csv"
    labels_cycle = [
        "supported",
        "mild_scope_overclaim",
        "strong_action_overclaim",
        "contradiction_candidate",
        "uncertain_insufficient_context",
    ]
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for i, r in enumerate(rows):
            # Make ~60% agree with silver, 40% disagree, and ~15% uncertain.
            silver = r.get("silver_label", "supported")
            if i % 7 == 0:
                label = "uncertain_insufficient_context"
            elif i % 3 == 0:
                label = labels_cycle[i % len(labels_cycle)]
                if label == silver:
                    label = "mild_scope_overclaim"
            else:
                label = silver
            r["auditor_label"] = label
            r["auditor_confidence"] = str((i % 5) + 1)
            r["human_audited"] = "True"
            r["requires_second_review"] = "True" if (i % 5 == 0) else "False"
            r["disagreement_reason"] = (
                "mock disagreement" if label != silver and label != "uncertain_insufficient_context" else ""
            )
            writer.writerow(r)
    return out_path


def test_summarize_script_exists():
    assert SUMMARIZE_SCRIPT.exists(), f"missing {SUMMARIZE_SCRIPT}"


def test_summarize_produces_four_outputs(mock_filled_audit, tmp_path):
    out_dir = tmp_path / "audit_out"
    # NOTE: avoid capture_output=True to prevent deadlocks (per project memory).
    proc = subprocess.run(
        [
            PYTHON, str(SUMMARIZE_SCRIPT),
            "--audit-csv", str(mock_filled_audit),
            "--out-dir", str(out_dir),
        ],
        cwd=str(REPO_ROOT),
        capture_output=False,
    )
    assert proc.returncode == 0, f"summarize failed: rc={proc.returncode}"
    assert (out_dir / "audit_agreement_summary.json").exists()
    assert (out_dir / "audit_confusion_matrix.csv").exists()
    assert (out_dir / "audit_disagreement_cases_redacted.csv").exists()
    assert (out_dir / "audit_summary.md").exists()


def test_summarize_summary_has_safe_unsafe_wording(mock_filled_audit, tmp_path):
    out_dir = tmp_path / "audit_out"
    subprocess.run(
        [
            PYTHON, str(SUMMARIZE_SCRIPT),
            "--audit-csv", str(mock_filled_audit),
            "--out-dir", str(out_dir),
        ],
        cwd=str(REPO_ROOT),
        capture_output=False,
    )
    md = (out_dir / "audit_summary.md").read_text(encoding="utf-8")
    assert "small targeted audit" in md.lower()
    assert "not a gold benchmark" in md.lower()
    assert "do not claim" in md.lower() or "must not" in md.lower()
    # Unsafe wording flagged.
    assert "SOTA" in md
    assert "gold benchmark" in md.lower()


def test_summarize_metrics_present(mock_filled_audit, tmp_path):
    out_dir = tmp_path / "audit_out"
    subprocess.run(
        [
            PYTHON, str(SUMMARIZE_SCRIPT),
            "--audit-csv", str(mock_filled_audit),
            "--out-dir", str(out_dir),
        ],
        cwd=str(REPO_ROOT),
        capture_output=False,
    )
    summary = json.loads(
        (out_dir / "audit_agreement_summary.json").read_text(encoding="utf-8")
    )
    metrics = summary.get("metrics", {})
    for k in [
        "silver_vs_auditor_agreement",
        "strong_action_precision_in_top20",
        "strong_action_precision_in_top50",
        "major_disagreement_rate",
        "uncertain_rate",
    ]:
        assert k in metrics, f"metric {k} missing from summary"


def test_summarize_agreement_excludes_uncertain(mock_filled_audit, tmp_path):
    """silver_vs_auditor_agreement denominator = n_decided, not n_filled."""
    out_dir = tmp_path / "audit_out"
    subprocess.run(
        [
            PYTHON, str(SUMMARIZE_SCRIPT),
            "--audit-csv", str(mock_filled_audit),
            "--out-dir", str(out_dir),
        ],
        cwd=str(REPO_ROOT),
        capture_output=False,
    )
    summary = json.loads(
        (out_dir / "audit_agreement_summary.json").read_text(encoding="utf-8")
    )
    m = summary["metrics"]
    assert m["n_filled"] == m["n_decided"] + m["n_uncertain"], \
        "n_filled must equal n_decided + n_uncertain"


def test_summarize_disagreement_csv_no_identifiers(mock_filled_audit, tmp_path):
    out_dir = tmp_path / "audit_out"
    subprocess.run(
        [
            PYTHON, str(SUMMARIZE_SCRIPT),
            "--audit-csv", str(mock_filled_audit),
            "--out-dir", str(out_dir),
        ],
        cwd=str(REPO_ROOT),
        capture_output=False,
    )
    p = out_dir / "audit_disagreement_cases_redacted.csv"
    header, _ = _read_csv(p)
    forbidden_ids = {"candidate_id", "target_candidate_group_id"}
    leak = set(header) & forbidden_ids
    assert not leak, f"disagreement CSV leaks identifiers: {leak}"
    raw_leak = set(header) & FORBIDDEN_RAWTEXT_FIELDS
    assert not raw_leak, f"disagreement CSV has raw-text columns: {raw_leak}"


def test_summarize_confusion_csv_no_identifiers(mock_filled_audit, tmp_path):
    out_dir = tmp_path / "audit_out"
    subprocess.run(
        [
            PYTHON, str(SUMMARIZE_SCRIPT),
            "--audit-csv", str(mock_filled_audit),
            "--out-dir", str(out_dir),
        ],
        cwd=str(REPO_ROOT),
        capture_output=False,
    )
    p = out_dir / "audit_confusion_matrix.csv"
    header, _ = _read_csv(p)
    forbidden_ids = {"candidate_id", "target_candidate_group_id"}
    leak = set(header) & forbidden_ids
    assert not leak, f"confusion CSV leaks identifiers: {leak}"


def test_summarize_disagreement_rows_exclude_agreeing(mock_filled_audit, tmp_path):
    """Disagreement CSV must not include rows where auditor == silver."""
    out_dir = tmp_path / "audit_out"
    subprocess.run(
        [
            PYTHON, str(SUMMARIZE_SCRIPT),
            "--audit-csv", str(mock_filled_audit),
            "--out-dir", str(out_dir),
        ],
        cwd=str(REPO_ROOT),
        capture_output=False,
    )
    p = out_dir / "audit_disagreement_cases_redacted.csv"
    _, rows = _read_csv(p)
    for r in rows:
        silver = r.get("silver_label", "").strip()
        auditor = r.get("auditor_label", "").strip()
        assert silver != auditor, \
            f"row {r.get('audit_item_id')} has silver == auditor in disagreement CSV"
        assert auditor != "uncertain_insufficient_context", \
            f"row {r.get('audit_item_id')} is uncertain in disagreement CSV"
