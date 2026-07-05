import pandas as pd

a = pd.read_csv(r"D:\ocn\gold_pilot_relation_realism_protocol_v2\pilot_50_relation_realism_annotation_A.csv", keep_default_na=False)
b = pd.read_csv(r"D:\ocn\gold_pilot_relation_realism_protocol_v2\pilot_50_relation_realism_annotation_B.csv", keep_default_na=False)

print("A rows:", len(a), "cols:", len(a.columns))
print("B rows:", len(b), "cols:", len(b.columns))
print("A cols:", list(a.columns))
print("B cols:", list(b.columns))

# Silver leakage check
forbidden = {
    "silver_label", "silver_label_hidden_or_visible", "candidate_label_guess",
    "issue_binary_label_guess", "escalation_binary_label_guess", "contradiction_binary_label_guess",
    "sample_source", "boundary_type", "why_selected", "do_not_use_as_gold_yet",
    "final_label", "gold_label", "human_audited",
    # v1 annotation fields should also not be in v2
    "annotator_label", "confidence_1_to_5", "rationale_one_sentence", "confusion_if_any", "needs_adjudication",
}
a_leak = set(a.columns) & forbidden
b_leak = set(b.columns) & forbidden
print("---silver/v1 leakage check---")
print("A forbidden fields:", a_leak if a_leak else "NONE")
print("B forbidden fields:", b_leak if b_leak else "NONE")

# To-fill fields empty check
to_fill = [
    "annotator_relation_label", "relation_confidence_1_to_5", "relation_rationale_one_sentence",
    "relation_confusion_if_any", "needs_relation_adjudication",
    "claim_realism_score_1_to_5", "claim_realism_issue", "realism_rationale_one_sentence",
    "claim_usable_for_paper_example", "needs_realism_adjudication",
]
print("---to-fill fields empty check---")
for col in to_fill:
    a_nonempty = (a[col].astype(str).str.strip() != "").sum()
    b_nonempty = (b[col].astype(str).str.strip() != "").sum()
    print(f"  {col}: A nonempty={a_nonempty}, B nonempty={b_nonempty}")

# Basic fields populated check
basic = ["pilot_id", "candidate_id", "domain", "evidence_text", "claim_text"]
print("---basic fields populated check---")
for col in basic:
    a_empty = (a[col].astype(str).str.strip() == "").sum()
    b_empty = (b[col].astype(str).str.strip() == "").sum()
    print(f"  {col}: A empty={a_empty}, B empty={b_empty}")

# A and B same pilot_ids in same order
print("---pilot_id alignment check---")
print("A pilot_ids == B pilot_ids:", list(a.pilot_id) == list(b.pilot_id))
print("A pilot_ids count:", len(a.pilot_id), "unique:", a.pilot_id.nunique())
