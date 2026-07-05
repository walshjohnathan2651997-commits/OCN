"""Generate blind annotation templates A and B from gold_pilot_candidate_50.csv.

This script ONLY transforms CSV data. It does NOT run models, call APIs,
modify original data, or fill any labels. Output templates have all label
fields empty by design.
"""
import csv
import os

SRC = r"D:\ocn\gold_pilot_preparation_v1\gold_pilot_candidate_50.csv"
OUT_DIR = r"D:\ocn\gold_pilot_protocol_freeze_v1"
OUT_A = os.path.join(OUT_DIR, "pilot_50_blind_annotation_A.csv")
OUT_B = os.path.join(OUT_DIR, "pilot_50_blind_annotation_B.csv")

BLIND_FIELDS = [
    "pilot_id",
    "candidate_id",
    "domain",
    "evidence_text",
    "claim_text",
    "annotator_label",
    "confidence_1_to_5",
    "rationale_one_sentence",
    "confusion_if_any",
    "needs_adjudication",
]

EXCLUDE_FIELDS = {
    "silver_label_hidden_or_visible",
    "sample_source",
    "boundary_type",
    "why_selected",
    "do_not_use_as_gold_yet",
}


def build_blind_template(src_path, out_path):
    rows_written = 0
    silver_leaked = 0
    with open(src_path, "r", encoding="utf-8", newline="") as fin:
        reader = csv.DictReader(fin)
        with open(out_path, "w", encoding="utf-8", newline="") as fout:
            writer = csv.DictWriter(fout, fieldnames=BLIND_FIELDS, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            for row in reader:
                blind_row = {
                    "pilot_id": row["pilot_id"],
                    "candidate_id": row["candidate_id"],
                    "domain": row["domain"],
                    "evidence_text": row["evidence_text"],
                    "claim_text": row["claim_text"],
                    "annotator_label": "",
                    "confidence_1_to_5": "",
                    "rationale_one_sentence": "",
                    "confusion_if_any": "",
                    "needs_adjudication": "",
                }
                # Safety check: no silver label or excluded fields leak
                for ex in EXCLUDE_FIELDS:
                    if ex in blind_row:
                        silver_leaked += 1
                writer.writerow(blind_row)
                rows_written += 1
    return rows_written, silver_leaked


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    a_count, a_leak = build_blind_template(SRC, OUT_A)
    b_count, b_leak = build_blind_template(SRC, OUT_B)
    print(f"A: {a_count} rows, silver_leaked={a_leak} -> {OUT_A}")
    print(f"B: {b_count} rows, silver_leaked={b_leak} -> {OUT_B}")

    # Verify no excluded fields in output headers
    for path in (OUT_A, OUT_B):
        with open(path, "r", encoding="utf-8") as f:
            header = f.readline().strip()
        for ex in EXCLUDE_FIELDS:
            if ex in header:
                print(f"ERROR: {ex} leaked into header of {path}")
        print(f"Header OK: {path}")
