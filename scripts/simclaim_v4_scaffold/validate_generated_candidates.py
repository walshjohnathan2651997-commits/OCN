import argparse
import csv
import importlib.util
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(r"D:\ocn")
GEN_SCRIPT = ROOT / "scripts" / "simclaim_v4_scaffold" / "run_v4_claim_generation.py"
TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_\-]+")
NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?\b")
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "into",
    "is", "it", "of", "on", "or", "that", "the", "their", "this", "to", "was",
    "were", "with", "within", "same", "described", "research", "context",
}
MISMATCH_CUES = {
    "absent", "cannot", "different", "inaccurate", "inefficient", "unrealistic",
    "underperforms", "easy", "homogeneous", "causes", "eliminates", "missing",
}


def load_generator():
    spec = importlib.util.spec_from_file_location("v4_generation", GEN_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_csv(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fieldnames=None):
    path = Path(path)
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


def content_tokens(text):
    return {
        tok for tok in TOKEN_RE.findall((text or "").lower())
        if tok not in STOPWORDS and len(tok) > 2
    }


def numbers(text):
    return set(NUMBER_RE.findall((text or "").lower()))


def semantic_suspicion(row):
    label = row.get("candidate_label_guess", "")
    if label == "supported":
        return ""
    claim_tokens = content_tokens(row.get("claim_text", ""))
    evidence_tokens = content_tokens(row.get("evidence_text", ""))
    if not claim_tokens:
        return f"semantic_suspicious_{label}_empty_claim_tokens"
    claim_only = claim_tokens - evidence_tokens
    claim_only_rate = len(claim_only) / len(claim_tokens)
    claim_nums = numbers(row.get("claim_text", ""))
    evidence_nums = numbers(row.get("evidence_text", ""))
    has_number_mismatch = bool(claim_nums and evidence_nums and not claim_nums <= evidence_nums)
    has_mismatch_cue = bool(claim_tokens & MISMATCH_CUES)
    if claim_only_rate < 0.12 and not has_number_mismatch and not has_mismatch_cue:
        return f"semantic_suspicious_{label}_low_claim_only_signal"
    return ""


def validate_file(input_csv, audit_csv, summary_json, report_md):
    mod = load_generator()
    rows = read_csv(input_csv)
    generated = [r for r in rows if r.get("claim_generation_status") == "success"]
    by_group = defaultdict(list)
    for r in generated:
        by_group[r["v4_group_id"]].append({
            "label": r["candidate_label_guess"],
            "claim_text": r.get("claim_text", ""),
            "semantic_note": r.get("v4_semantic_note", ""),
        })

    audit = []
    for gid, claims in sorted(by_group.items()):
        ok, reason = mod.validate_payload({"claims": claims})
        source_rows = [r for r in generated if r["v4_group_id"] == gid]
        evidence_ok = all(r.get("evidence_text", "") == r.get("evidence_text_original_locked", r.get("evidence_text", "")) for r in source_rows)
        claim_texts = [r.get("claim_text", "") for r in source_rows]
        semantic_reasons = [semantic_suspicion(r) for r in source_rows]
        semantic_reasons = [r for r in semantic_reasons if r]
        if ok and semantic_reasons:
            ok = False
            reason = semantic_reasons[0]
        audit.append({
            "v4_group_id": gid,
            "n_rows": len(source_rows),
            "validator_ok": str(ok).lower(),
            "validator_reason": reason,
            "evidence_unchanged": str(evidence_ok).lower(),
            "duplicate_claims_in_group": len(claim_texts) - len(set(claim_texts)),
            "semantic_suspicion_count": len(semantic_reasons),
            "semantic_suspicion_reasons": ";".join(semantic_reasons),
        })

    counts = Counter(r["validator_ok"] for r in audit)
    reason_counts = Counter(r["validator_reason"] for r in audit if r["validator_ok"] != "true")
    summary = {
        "input_csv": str(input_csv),
        "generated_rows": len(generated),
        "generated_groups": len(by_group),
        "validator_pass_groups": counts.get("true", 0),
        "validator_fail_groups": counts.get("false", 0),
        "failure_reasons": dict(reason_counts),
        "audit_csv": str(audit_csv),
        "report_md": str(report_md),
    }
    write_csv(audit_csv, audit)
    Path(summary_json).parent.mkdir(parents=True, exist_ok=True)
    Path(summary_json).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# generated candidate validation report",
        "",
        f"- Input: `{input_csv}`",
        f"- Generated rows: {len(generated)}",
        f"- Generated groups: {len(by_group)}",
        f"- Validator pass groups: {summary['validator_pass_groups']}",
        f"- Validator fail groups: {summary['validator_fail_groups']}",
        "",
        "## Failure reasons",
        "",
        "| reason | groups |",
        "|---|---:|",
    ]
    for reason, count in reason_counts.most_common():
        lines.append(f"| {reason} | {count} |")
    lines.extend([
        "",
        f"Audit CSV: `{audit_csv}`",
    ])
    Path(report_md).parent.mkdir(parents=True, exist_ok=True)
    Path(report_md).write_text("\n".join(lines), encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--audit-csv", required=True)
    parser.add_argument("--summary-json", required=True)
    parser.add_argument("--report-md", required=True)
    args = parser.parse_args()
    summary = validate_file(args.input_csv, args.audit_csv, args.summary_json, args.report_md)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
