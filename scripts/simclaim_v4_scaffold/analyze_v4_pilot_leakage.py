import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(r"D:\ocn")
CANDIDATES_CSV = ROOT / "data" / "simclaim_hardpair_v4_pilot" / "candidates" / "simclaim_hardpair_v4_pilot_candidates.csv"
METRICS_REPORT = ROOT / "experiments" / "simclaim_hardpair_v4_pilot_small_baselines" / "reports" / "v4_pilot_small_data_baseline_report.md"
OUT_AUDIT = ROOT / "data" / "simclaim_hardpair_v4_pilot" / "audit" / "v4_pilot_claim_only_leakage_terms.csv"
OUT_REPORT = ROOT / "reports" / "simclaim_hardpair_v4_pilot" / "v4_pilot_gate_and_leakage_report.md"
OUT_SUMMARY = ROOT / "reports" / "simclaim_hardpair_v4_pilot" / "v4_pilot_gate_and_leakage_summary.json"

LABEL_FIELD = "candidate_label_guess"
LABELS = ["supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate"]
STOP = {
    "the", "a", "an", "and", "or", "of", "to", "in", "for", "with", "as", "by", "on", "at", "from",
    "is", "are", "was", "were", "be", "been", "being", "this", "that", "these", "those", "it", "its",
    "into", "over", "under", "while", "through", "using", "uses", "used", "described", "study",
}


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


def tokenize(text):
    toks = re.findall(r"[a-z][a-z0-9\-]+", str(text or "").lower())
    return [t for t in toks if t not in STOP and len(t) > 2]


def ngrams(tokens, n):
    return [" ".join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]


def terms(text):
    toks = tokenize(text)
    return set(toks + ngrams(toks, 2))


def main():
    rows = [r for r in read_csv(CANDIDATES_CSV) if r.get("claim_generation_status") == "success"]
    label_docs = defaultdict(list)
    for r in rows:
        label_docs[r[LABEL_FIELD]].append(r.get("claim_text", ""))

    term_doc_counts = {label: Counter() for label in LABELS}
    label_n = {label: len(label_docs[label]) for label in LABELS}
    for label in LABELS:
        for text in label_docs[label]:
            term_doc_counts[label].update(terms(text))

    audit_rows = []
    for label in LABELS:
        other_n = sum(label_n[l] for l in LABELS if l != label)
        for term, count in term_doc_counts[label].items():
            other_count = sum(term_doc_counts[l][term] for l in LABELS if l != label)
            p_label = (count + 0.5) / (label_n[label] + 1)
            p_other = (other_count + 0.5) / (other_n + 1)
            log_ratio = math.log(p_label / p_other)
            if count >= 2 or log_ratio > 1.2:
                audit_rows.append({
                    "label": label,
                    "term": term,
                    "label_doc_count": count,
                    "label_doc_rate": round(count / max(label_n[label], 1), 4),
                    "other_doc_count": other_count,
                    "other_doc_rate": round(other_count / max(other_n, 1), 4),
                    "log_rate_ratio": round(log_ratio, 4),
                    "risk": "high" if log_ratio > 1.5 and count >= 2 else "medium",
                })
    audit_rows.sort(key=lambda r: (r["risk"] != "high", -float(r["log_rate_ratio"]), -int(r["label_doc_count"]), r["label"], r["term"]))
    write_csv(OUT_AUDIT, audit_rows)

    top_by_label = {}
    for label in LABELS:
        top_by_label[label] = [r for r in audit_rows if r["label"] == label][:12]

    evidence_unchanged = sum(1 for r in rows if r.get("evidence_text") == r.get("evidence_text_original_locked"))
    duplicate_claims = len(rows) - len({r.get("claim_text", "") for r in rows})
    metrics_text = METRICS_REPORT.read_text(encoding="utf-8") if METRICS_REPORT.exists() else ""
    summary = {
        "n_generated_rows": len(rows),
        "n_generated_groups": len({r["v4_group_id"] for r in rows}),
        "evidence_unchanged_rate": round(evidence_unchanged / max(len(rows), 1), 4),
        "duplicate_claims": duplicate_claims,
        "leakage_audit_csv": str(OUT_AUDIT),
        "report_md": str(OUT_REPORT),
        "top_terms_by_label": top_by_label,
    }
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# v4 pilot gate and leakage report",
        "",
        "## Decision",
        "",
        "Do not expand the current v4 prompt to the full 600 rows yet.",
        "",
        "The generation pipeline works technically and preserves evidence, but the v4-mini metric gate failed because claim-only signals remain too strong, especially for the four-class candidate label.",
        "",
        "## Fidelity",
        "",
        f"- Generated rows: {len(rows)}",
        f"- Generated groups: {summary['n_generated_groups']}",
        f"- Evidence unchanged rate: {summary['evidence_unchanged_rate']:.2%}",
        f"- Duplicate generated claims: {duplicate_claims}",
        "",
        "## Metric gate",
        "",
        metrics_text.strip() if metrics_text else "Metric report missing.",
        "",
        "## Top claim-only leakage terms by label",
        "",
    ]
    for label in LABELS:
        lines.extend([
            f"### {label}",
            "",
            "| term | label rate | other rate | risk |",
            "|---|---:|---:|---|",
        ])
        for r in top_by_label[label][:10]:
            lines.append(f"| {r['term']} | {float(r['label_doc_rate']):.2%} | {float(r['other_doc_rate']):.2%} | {r['risk']} |")
        lines.append("")
    lines.extend([
        "## Next prompt fix",
        "",
        "The next recipe should force matched lexical frames within each evidence group. In practice, that means generating four claims from a shared sentence skeleton, keeping subject, verbs, modality, and sentence length aligned, and changing only the semantic relation to the locked evidence.",
        "",
        "Do not run more bulk LLM generation until this prompt is revised and tested on another small batch.",
        "",
        "## Files",
        "",
        f"- Leakage audit CSV: `{OUT_AUDIT}`",
        f"- Metrics report: `{METRICS_REPORT}`",
    ])
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
