import csv
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(r"D:\ocn")
QUEUE_CSV = ROOT / "data" / "simclaim_v4_scaffold" / "generation_queue" / "v4_generation_queue_600_candidate_slots.csv"
OUT_ROOT = ROOT / "data" / "simclaim_hardpair_v4b_no_llm_style_control"
OUT_CSV = OUT_ROOT / "candidates" / "simclaim_hardpair_v4b_no_llm_style_control_600.csv"
OUT_JSONL = OUT_ROOT / "candidates" / "simclaim_hardpair_v4b_no_llm_style_control_600.jsonl"
OUT_AUDIT = OUT_ROOT / "audit" / "style_control_audit.csv"
REPORT_MD = ROOT / "reports" / "simclaim_hardpair_v4b_no_llm_style_control" / "style_control_report.md"

LABELS = ["supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate"]
NEUTRAL_SUFFIXES = [
    "within the reported study context",
    "under the stated study conditions",
    "for the described study setting",
    "inside the same measurement scope",
]


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fieldnames=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fieldnames.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize_space(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def evidence_stem(text, max_words=18):
    clean = normalize_space(text)
    clean = re.split(r"(?<=[.!?])\s+", clean)[0]
    words = clean.split()
    if len(words) > max_words:
        clean = " ".join(words[:max_words])
    clean = clean.strip(" ,;:.")
    if not clean:
        clean = "the reported simulation result"
    return clean


def group_index(group_id):
    m = re.search(r"(\d+)$", group_id)
    return int(m.group(1)) if m else 0


def suffix_for(group_id, label):
    gidx = group_index(group_id)
    lidx = LABELS.index(label)
    return NEUTRAL_SUFFIXES[(gidx + lidx) % len(NEUTRAL_SUFFIXES)]


def main():
    rows = read_csv(QUEUE_CSV)
    out = []
    audit = []
    for row in rows:
        copied = dict(row)
        stem = evidence_stem(row.get("evidence_text", ""))
        suffix = suffix_for(row["v4_group_id"], row["candidate_label_guess"])
        claim = f"The selected passage describes {stem}, framed {suffix}."
        copied["claim_text"] = normalize_space(claim)
        copied["claim_generation_status"] = "success"
        copied["claim_generation_policy"] = "no_llm_style_control_negative_control"
        copied["style_control_suffix"] = suffix
        copied["style_control_note"] = "diagnostic_only_not_semantic_candidate_generation"
        copied["evidence_text_original_locked"] = copied["evidence_text"]
        copied["evidence_lock_check_sha256"] = copied.get("evidence_text_sha256", "")
        copied["human_audited"] = "false"
        copied["final_label"] = ""
        copied["gold_label"] = ""
        out.append(copied)
        audit.append({
            "candidate_id": copied["candidate_id"],
            "v4_group_id": copied["v4_group_id"],
            "candidate_label_guess": copied["candidate_label_guess"],
            "split": copied["split"],
            "style_control_suffix": suffix,
            "claim_word_count": len(copied["claim_text"].split()),
            "evidence_unchanged": str(copied["evidence_text"] == copied["evidence_text_original_locked"]).lower(),
        })

    write_csv(OUT_CSV, out)
    write_jsonl(OUT_JSONL, out)
    write_csv(OUT_AUDIT, audit)

    suffix_label_counts = Counter((r["candidate_label_guess"], r["style_control_suffix"]) for r in audit)
    split_counts = Counter(r["split"] for r in audit)
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# v4b no-LLM style-control negative control",
        "",
        "This is not a final dataset. It is a diagnostic negative control built without any LLM calls.",
        "",
        "Purpose: test whether frame-locked claim style can suppress claim-only label leakage.",
        "",
        "## Summary",
        "",
        f"- Rows: {len(out)}",
        f"- Groups: {len({r['v4_group_id'] for r in out})}",
        f"- Evidence unchanged: {sum(1 for r in audit if r['evidence_unchanged'] == 'true')}/{len(audit)}",
        f"- Duplicate claim rows: {len(out) - len({r['claim_text'] for r in out})}",
        "",
        "## Split rows",
        "",
        "| split | rows |",
        "|---|---:|",
    ]
    for split, count in split_counts.most_common():
        lines.append(f"| {split} | {count} |")
    lines.extend([
        "",
        "## Interpretation rule",
        "",
        "- If claim-only performance falls toward chance, frame-locking is working as a leakage control.",
        "- If claim+evidence also falls, this confirms that a real v4b still needs semantic claim generation, not this local negative control.",
        "",
        "## Outputs",
        "",
        f"- Candidates: `{OUT_CSV}`",
        f"- Audit: `{OUT_AUDIT}`",
    ])
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({
        "status": "ok",
        "rows": len(out),
        "groups": len({r["v4_group_id"] for r in out}),
        "candidates_csv": str(OUT_CSV),
        "audit_csv": str(OUT_AUDIT),
        "report_md": str(REPORT_MD),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
