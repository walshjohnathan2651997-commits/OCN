"""Build v2 relation + realism gold pilot annotation templates (A and B).

Reads v1 pilot_50_blind_annotation_A.csv (and B) — only the basic 5 fields
(pilot_id, candidate_id, domain, evidence_text, claim_text). Drops v1's
annotation fields (annotator_label, confidence, rationale, etc.) and replaces
them with the v2 two-layer schema: Layer 1 relation + Layer 2 realism.

Does NOT modify v1 files. Does NOT leak silver labels. Does NOT fill gold.
All v2 to-fill fields are empty strings.
"""
import shutil
from pathlib import Path

import pandas as pd

V1_DIR = Path(r"D:\ocn\gold_pilot_protocol_freeze_v1")
V2_DIR = Path(r"D:\ocn\gold_pilot_relation_realism_protocol_v2")
V2_DIR.mkdir(parents=True, exist_ok=True)

V1_A = V1_DIR / "pilot_50_blind_annotation_A.csv"
V1_B = V1_DIR / "pilot_50_blind_annotation_B.csv"

V2_A = V2_DIR / "pilot_50_relation_realism_annotation_A.csv"
V2_B = V2_DIR / "pilot_50_relation_realism_annotation_B.csv"

# Basic fields (carried over from v1, populated)
BASIC_FIELDS = ["pilot_id", "candidate_id", "domain", "evidence_text", "claim_text"]

# Layer 1 relation (empty, to be filled by annotator)
LAYER1_FIELDS = [
    "annotator_relation_label",
    "relation_confidence_1_to_5",
    "relation_rationale_one_sentence",
    "relation_confusion_if_any",
    "needs_relation_adjudication",
]

# Layer 2 realism (empty, to be filled by annotator)
LAYER2_FIELDS = [
    "claim_realism_score_1_to_5",
    "claim_realism_issue",
    "realism_rationale_one_sentence",
    "claim_usable_for_paper_example",
    "needs_realism_adjudication",
]

V2_COLUMNS = BASIC_FIELDS + LAYER1_FIELDS + LAYER2_FIELDS

# Silver-leakage forbidden fields (must NOT appear in v2 templates)
FORBIDDEN_FIELDS = {
    "silver_label_hidden_or_visible",
    "silver_label",
    "candidate_label_guess",
    "issue_binary_label_guess",
    "escalation_binary_label_guess",
    "contradiction_binary_label_guess",
    "sample_source",
    "boundary_type",
    "why_selected",
    "do_not_use_as_gold_yet",
    "final_label",
    "gold_label",
    "human_audited",
    "annotation_status",
    "annotator_label",  # v1 field — replaced by annotator_relation_label
    "confidence_1_to_5",
    "rationale_one_sentence",
    "confusion_if_any",
    "needs_adjudication",
}


def build_template(v1_path: Path, v2_path: Path):
    """Read v1, keep only basic 5 fields, append empty Layer1 + Layer2 columns."""
    df = pd.read_csv(v1_path, keep_default_na=False)
    # Verify only basic fields are present in v1 (no silver leakage)
    v1_cols = set(df.columns)
    forbidden_in_v1 = v1_cols & FORBIDDEN_FIELDS
    # v1's annotator_label etc. are present but empty — they're not silver leakage,
    # they're the v1 annotation fields. We drop them in v2.
    # Check no silver leakage in v1:
    silver_fields_in_v1 = v1_cols & {
        "silver_label", "silver_label_hidden_or_visible", "candidate_label_guess",
        "final_label", "gold_label", "human_audited", "sample_source", "why_selected",
    }
    if silver_fields_in_v1:
        raise RuntimeError(f"FATAL: v1 template {v1_path} contains silver fields: {silver_fields_in_v1}")

    # Keep only basic fields
    basic_df = df[BASIC_FIELDS].copy()
    # Append empty Layer 1 + Layer 2 columns
    for col in LAYER1_FIELDS + LAYER2_FIELDS:
        basic_df[col] = ""
    # Reorder to ensure exact column order
    basic_df = basic_df[V2_COLUMNS]
    # Write v2
    basic_df.to_csv(v2_path, index=False, encoding="utf-8")
    print(f"Wrote {v2_path} ({len(basic_df)} rows, {len(basic_df.columns)} cols)")
    return basic_df


def verify_template(v2_path: Path):
    """Verify v2 template: 50 rows, 15 cols, all to-fill fields empty, no silver leakage."""
    df = pd.read_csv(v2_path, keep_default_na=False)
    assert len(df) == 50, f"Expected 50 rows, got {len(df)}"
    assert list(df.columns) == V2_COLUMNS, f"Column mismatch. Got: {list(df.columns)}"
    # Check no forbidden fields
    forbidden_present = set(df.columns) & FORBIDDEN_FIELDS
    assert not forbidden_present, f"Forbidden fields present: {forbidden_present}"
    # Check all to-fill fields are empty
    for col in LAYER1_FIELDS + LAYER2_FIELDS:
        non_empty = (df[col].astype(str).str.strip() != "").sum()
        assert non_empty == 0, f"Column {col} has {non_empty} non-empty values (should be 0)"
    # Check basic fields are populated
    for col in BASIC_FIELDS:
        empty_count = (df[col].astype(str).str.strip() == "").sum()
        assert empty_count == 0, f"Basic field {col} has {empty_count} empty values (should be 0)"
    print(f"  Verified: {v2_path.name} — 50 rows, 15 cols, no silver leakage, all to-fill fields empty")
    return True


def main():
    print("Building v2 relation + realism annotation templates...")
    print()
    build_template(V1_A, V2_A)
    build_template(V1_B, V2_B)
    print()
    print("Verifying templates...")
    verify_template(V2_A)
    verify_template(V2_B)
    print()
    print("=== V2 TEMPLATES READY ===")
    print(f"A: {V2_A}")
    print(f"B: {V2_B}")
    print()
    print("Column schema (15 fields):")
    print("  Basic (5, populated): " + ", ".join(BASIC_FIELDS))
    print("  Layer 1 relation (5, empty): " + ", ".join(LAYER1_FIELDS))
    print("  Layer 2 realism (5, empty): " + ", ".join(LAYER2_FIELDS))


if __name__ == "__main__":
    main()
