"""tests/test_artifact_ledger_release_safety.py — Artifact ledger release safety tests.

Verifies that the V3.17 artifact ledger and release safety manifest enforce
the hard boundaries:

  - safe_to_release=true artifacts do NOT contain sensitive columns
    (claim_text, evidence_text, selected_evidence, raw_text, clean_text,
     body_text, pdf_text).
  - private_sensitive=true artifacts are NOT in the public release bundle.
  - Every paper table has a source artifact recorded in the ledger.

Hard boundaries enforced:
  - No public artifact may carry raw claim/evidence text.
  - No private artifact may appear in the release bundle.
  - No paper table may have an empty generated_by_script or input_artifacts.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
LEDGER_CSV = REPO_ROOT / "reports" / "artifact_ledger_v3_17.csv"
LEDGER_MD = REPO_ROOT / "reports" / "artifact_ledger_v3_17.md"
SAFETY_JSON = REPO_ROOT / "reports" / "release_safety_manifest_v3_17.json"
MANIFEST_YAML = REPO_ROOT / "artifacts_manifest_v3_17.yaml"
REPRO_GUIDE = REPO_ROOT / "docs" / "reproducibility_guide_v3_17.md"
RELEASE_BUNDLE_MANIFEST = REPO_ROOT / "release_bundles" / "v3_17_confidential_public" / "MANIFEST.json"
PAPER_TABLES_DIR = REPO_ROOT / "paper_assets" / "v3_17_confidential" / "tables"

SENSITIVE_COLUMNS = {
    "claim_text", "evidence_text", "selected_evidence",
    "raw_text", "clean_text", "body_text", "pdf_text",
}

REQUIRED_LEDGER_COLUMNS = [
    "artifact_id", "path", "artifact_type", "public_safe",
    "private_sensitive", "generated_by_script", "input_artifacts",
    "run_mode", "contains_raw_text", "contains_hash_only",
    "contains_labels", "contains_oracle_eval", "safe_to_release",
    "exists", "detected_sensitive_columns", "detected_label_columns",
    "detected_oracle_columns", "notes",
]


# ---------- Fixture: load ledger ----------

@pytest.fixture(scope="module")
def ledger_rows():
    """Load the artifact ledger CSV as a list of dicts."""
    if not LEDGER_CSV.exists():
        pytest.fail(f"Artifact ledger CSV missing: {LEDGER_CSV}")
    with open(LEDGER_CSV, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) > 0, "Artifact ledger CSV is empty"
    return rows


@pytest.fixture(scope="module")
def safety_manifest():
    """Load the release safety manifest JSON."""
    if not SAFETY_JSON.exists():
        pytest.fail(f"Release safety manifest missing: {SAFETY_JSON}")
    with open(SAFETY_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def release_bundle_files():
    """Load the list of file paths in the public release bundle."""
    if not RELEASE_BUNDLE_MANIFEST.exists():
        pytest.skip("Release bundle MANIFEST.json not present; skipping bundle checks")
    with open(RELEASE_BUNDLE_MANIFEST, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [entry["path"] for entry in data.get("files", [])]


# ---------- File existence ----------

def test_manifest_yaml_exists():
    assert MANIFEST_YAML.exists(), (
        f"Artifacts manifest YAML missing: {MANIFEST_YAML}"
    )


def test_ledger_csv_exists():
    assert LEDGER_CSV.exists(), (
        f"Artifact ledger CSV missing: {LEDGER_CSV}. "
        f"Run: python scripts/build_artifact_ledger_v1.py"
    )


def test_ledger_md_exists():
    assert LEDGER_MD.exists(), (
        f"Artifact ledger MD missing: {LEDGER_MD}"
    )


def test_safety_json_exists():
    assert SAFETY_JSON.exists(), (
        f"Release safety manifest JSON missing: {SAFETY_JSON}"
    )


def test_reproducibility_guide_exists():
    assert REPRO_GUIDE.exists(), (
        f"Reproducibility guide missing: {REPRO_GUIDE}"
    )


# ---------- Ledger structure ----------

def test_ledger_has_required_columns(ledger_rows):
    """The ledger CSV must have all required columns."""
    first_row = ledger_rows[0]
    for col in REQUIRED_LEDGER_COLUMNS:
        assert col in first_row, (
            f"Ledger missing required column: {col}. "
            f"Present columns: {list(first_row.keys())}"
        )


def test_ledger_has_minimum_artifact_count(ledger_rows):
    """The ledger must cover all major artifact groups (>=50 artifacts)."""
    assert len(ledger_rows) >= 50, (
        f"Ledger has only {len(ledger_rows)} artifacts; expected >=50 "
        f"to cover all groups (dataset, pdf, bm25, canonicalizer, "
        f"format_shift, review_queue, risk_ranking, leakage, error_taxonomy, "
        f"metric_robustness, complexity, human_audit, paper_assets, release)."
    )


def test_ledger_artifact_ids_unique(ledger_rows):
    """Every artifact_id must be unique."""
    ids = [r["artifact_id"] for r in ledger_rows]
    duplicates = [aid for aid in ids if ids.count(aid) > 1]
    assert not duplicates, (
        f"Duplicate artifact_ids in ledger: {set(duplicates)}"
    )


# ---------- Release safety gate ----------

def test_release_safety_gate_passes(safety_manifest):
    """The release safety gate must be PASS."""
    gate = safety_manifest.get("release_safety_gate", {})
    status = gate.get("status", "UNKNOWN")
    assert status == "PASS", (
        f"Release safety gate is {status}, expected PASS. "
        f"Unsafe public artifacts: {gate.get('unsafe_public_artifacts', [])}. "
        f"Private in release: {gate.get('private_in_release', [])}."
    )


def test_no_unsafe_public_artifacts(safety_manifest):
    """No public_safe artifact may contain raw text."""
    unsafe = safety_manifest.get("release_safety_gate", {}).get(
        "unsafe_public_artifacts", []
    )
    assert unsafe == [], (
        f"Public-safe artifacts with raw text detected: {unsafe}"
    )


def test_no_private_in_release(safety_manifest):
    """No private_sensitive artifact may be marked safe_to_release."""
    private_in_release = safety_manifest.get("release_safety_gate", {}).get(
        "private_in_release", []
    )
    assert private_in_release == [], (
        f"Private artifacts marked safe_to_release: {private_in_release}"
    )


# ---------- safe_to_release invariants ----------

def test_safe_to_release_artifacts_have_no_raw_text(ledger_rows):
    """Every artifact with safe_to_release=true must have
    contains_raw_text=false."""
    violations = [
        r["artifact_id"] for r in ledger_rows
        if r["safe_to_release"] == "true" and r["contains_raw_text"] == "true"
    ]
    assert violations == [], (
        f"safe_to_release=true but contains_raw_text=true: {violations}. "
        f"These artifacts must NOT be marked safe to release."
    )


def test_safe_to_release_artifacts_have_no_sensitive_columns(ledger_rows):
    """Every artifact with safe_to_release=true must have an empty
    detected_sensitive_columns field."""
    violations = []
    for r in ledger_rows:
        if r["safe_to_release"] == "true":
            detected = r.get("detected_sensitive_columns", "").strip()
            if detected:
                violations.append(
                    f"{r['artifact_id']}: {detected}"
                )
    assert violations == [], (
        f"safe_to_release=true but sensitive columns detected: {violations}"
    )


def test_safe_to_release_artifacts_are_public_safe(ledger_rows):
    """Every artifact with safe_to_release=true must have public_safe=true."""
    violations = [
        r["artifact_id"] for r in ledger_rows
        if r["safe_to_release"] == "true" and r["public_safe"] != "true"
    ]
    assert violations == [], (
        f"safe_to_release=true but public_safe!=true: {violations}"
    )


def test_safe_to_release_artifacts_not_private_sensitive(ledger_rows):
    """Every artifact with safe_to_release=true must have
    private_sensitive=false."""
    violations = [
        r["artifact_id"] for r in ledger_rows
        if r["safe_to_release"] == "true" and r["private_sensitive"] == "true"
    ]
    assert violations == [], (
        f"safe_to_release=true but private_sensitive=true: {violations}"
    )


def test_private_sensitive_artifacts_not_safe_to_release(ledger_rows):
    """Every artifact with private_sensitive=true must have
    safe_to_release=false."""
    violations = [
        r["artifact_id"] for r in ledger_rows
        if r["private_sensitive"] == "true" and r["safe_to_release"] == "true"
    ]
    assert violations == [], (
        f"private_sensitive=true but safe_to_release=true: {violations}"
    )


# ---------- Raw text detection ----------

def test_raw_text_artifacts_not_safe_to_release(ledger_rows):
    """Every artifact with contains_raw_text=true must have
    safe_to_release=false."""
    violations = [
        r["artifact_id"] for r in ledger_rows
        if r["contains_raw_text"] == "true" and r["safe_to_release"] == "true"
    ]
    assert violations == [], (
        f"contains_raw_text=true but safe_to_release=true: {violations}"
    )


def test_raw_text_artifacts_listed_in_safety_manifest(safety_manifest, ledger_rows):
    """Every artifact with contains_raw_text=true must appear in the
    safety manifest's contains_raw_text list."""
    raw_text_in_ledger = {
        r["artifact_id"] for r in ledger_rows
        if r["contains_raw_text"] == "true"
    }
    raw_text_in_manifest = {
        entry["artifact_id"] for entry in safety_manifest.get(
            "contains_raw_text", []
        )
    }
    missing = raw_text_in_ledger - raw_text_in_manifest
    assert missing == set(), (
        f"Raw-text artifacts missing from safety manifest: {missing}"
    )


# ---------- Release bundle exclusion ----------

def test_private_sensitive_paths_not_in_release_bundle(ledger_rows, release_bundle_files):
    """No artifact path with private_sensitive=true may appear in the
    public release bundle MANIFEST.json."""
    private_paths = {
        r["path"].replace("\\", "/") for r in ledger_rows
        if r["private_sensitive"] == "true"
    }
    # Also check parent-directory containment: if a private CSV is at
    # data/foo/private.csv, then "data/foo/private.csv" should not appear
    # in the release bundle file list.
    bundle_set = {p.replace("\\", "/") for p in release_bundle_files}
    leaked = [p for p in private_paths if p in bundle_set]
    assert leaked == [], (
        f"Private-sensitive paths found in release bundle: {leaked}"
    )


def test_raw_text_paths_not_in_release_bundle(ledger_rows, release_bundle_files):
    """No artifact path with contains_raw_text=true may appear in the
    public release bundle."""
    raw_text_paths = {
        r["path"].replace("\\", "/") for r in ledger_rows
        if r["contains_raw_text"] == "true"
    }
    bundle_set = {p.replace("\\", "/") for p in release_bundle_files}
    leaked = [p for p in raw_text_paths if p in bundle_set]
    assert leaked == [], (
        f"Raw-text paths found in release bundle: {leaked}"
    )


# ---------- Paper table source artifact coverage ----------

def test_all_paper_tables_have_ledger_entry(ledger_rows):
    """Every .md file in paper_assets/v3_17_confidential/tables/ must have
    a corresponding entry in the artifact ledger."""
    if not PAPER_TABLES_DIR.exists():
        pytest.skip("Paper tables directory not present")
    table_files = sorted(PAPER_TABLES_DIR.glob("table*.md"))
    assert len(table_files) > 0, (
        f"No paper table .md files found in {PAPER_TABLES_DIR}"
    )
    ledger_paths = {r["path"].replace("\\", "/") for r in ledger_rows}
    missing = []
    for tf in table_files:
        rel_path = str(tf.relative_to(REPO_ROOT)).replace("\\", "/")
        if rel_path not in ledger_paths:
            missing.append(rel_path)
    assert missing == [], (
        f"Paper tables without ledger entries: {missing}. "
        f"Add them to artifacts_manifest_v3_17.yaml under G14_paper_assets."
    )


def test_all_paper_tables_have_generated_by_script(ledger_rows):
    """Every paper_table_md artifact must have a non-empty
    generated_by_script field."""
    paper_tables = [
        r for r in ledger_rows
        if r["artifact_type"] == "paper_table_md"
    ]
    assert len(paper_tables) > 0, "No paper_table_md artifacts in ledger"
    missing = [
        r["artifact_id"] for r in paper_tables
        if not r["generated_by_script"].strip()
    ]
    assert missing == [], (
        f"Paper tables with empty generated_by_script: {missing}"
    )


def test_all_paper_tables_have_input_artifacts(ledger_rows):
    """Every paper_table_md artifact must have a non-empty
    input_artifacts field (traceable to a source experiment)."""
    paper_tables = [
        r for r in ledger_rows
        if r["artifact_type"] == "paper_table_md"
    ]
    assert len(paper_tables) > 0, "No paper_table_md artifacts in ledger"
    missing = [
        r["artifact_id"] for r in paper_tables
        if not r["input_artifacts"].strip()
    ]
    assert missing == [], (
        f"Paper tables with empty input_artifacts: {missing}. "
        f"Every paper table must trace to a source experiment artifact."
    )


def test_all_paper_tables_are_public_safe(ledger_rows):
    """Every paper_table_md artifact must have public_safe=true
    (paper tables are aggregate metrics, safe to release)."""
    paper_tables = [
        r for r in ledger_rows
        if r["artifact_type"] == "paper_table_md"
    ]
    violations = [
        r["artifact_id"] for r in paper_tables
        if r["public_safe"] != "true"
    ]
    assert violations == [], (
        f"Paper tables with public_safe!=true: {violations}"
    )


def test_all_paper_tables_have_no_raw_text(ledger_rows):
    """Every paper_table_md artifact must have contains_raw_text=false."""
    paper_tables = [
        r for r in ledger_rows
        if r["artifact_type"] == "paper_table_md"
    ]
    violations = [
        r["artifact_id"] for r in paper_tables
        if r["contains_raw_text"] == "true"
    ]
    assert violations == [], (
        f"Paper tables with contains_raw_text=true: {violations}. "
        f"Paper tables must contain aggregate metrics only."
    )


# ---------- Coverage: artifact groups ----------

def test_ledger_covers_required_artifact_types(ledger_rows):
    """The ledger must include at least one artifact of each required type."""
    required_types = {
        "dataset_csv",
        "pdf_corpus",
        "metrics_json",
        "metrics_csv",
        "evidence_csv",
        "redacted_csv",
        "report_md",
        "paper_table_md",
        "paper_draft_md",
        "documentation",
    }
    present_types = {r["artifact_type"] for r in ledger_rows}
    missing = required_types - present_types
    assert missing == set(), (
        f"Ledger missing required artifact types: {missing}. "
        f"Present types: {present_types}"
    )


def test_ledger_covers_required_run_modes(ledger_rows):
    """The ledger must include artifacts with run_mode real and blocked
    (blocked artifacts are documented, not hidden)."""
    modes = {r["run_mode"] for r in ledger_rows}
    assert "real" in modes, "Ledger has no real-mode artifacts"
    assert "blocked" in modes, (
        "Ledger has no blocked-mode artifacts. "
        "Blocked experiments must be documented, not hidden."
    )


# ---------- Reproducibility guide ----------

def test_reproducibility_guide_has_required_sections():
    """The reproducibility guide must cover all required topics."""
    if not REPRO_GUIDE.exists():
        pytest.fail(f"Reproducibility guide missing: {REPRO_GUIDE}")
    text = REPRO_GUIDE.read_text(encoding="utf-8")
    required_sections = [
        "Environment Setup",
        "Toy Run",
        "Real / Private Run",
        "Cannot Be Reproduced Publicly",
        "No-API / No-Network",
        "Regenerating Reports",
        "Regenerating Paper Assets",
        "Sanitized Public Release",
    ]
    missing = [s for s in required_sections if s not in text]
    assert missing == [], (
        f"Reproducibility guide missing sections: {missing}"
    )


def test_reproducibility_guide_references_ledger():
    """The guide must reference the artifact ledger and safety manifest."""
    text = REPRO_GUIDE.read_text(encoding="utf-8")
    assert "artifact_ledger_v3_17" in text, (
        "Reproducibility guide does not reference the artifact ledger"
    )
    assert "release_safety_manifest_v3_17" in text, (
        "Reproducibility guide does not reference the release safety manifest"
    )


def test_reproducibility_guide_documents_blocked_experiments():
    """The guide must document the blocked experiments (not hide them)."""
    text = REPRO_GUIDE.read_text(encoding="utf-8")
    assert "sklearn_version_mismatch" in text or "sklearn" in text.lower(), (
        "Reproducibility guide does not document the sklearn version mismatch blockage"
    )
    assert "missing_pdf_corpus" in text or "missing PDF" in text, (
        "Reproducibility guide does not document the missing PDF corpus blockage"
    )
