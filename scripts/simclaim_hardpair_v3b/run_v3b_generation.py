import argparse
import csv
import datetime as dt
import hashlib
import importlib.util
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(r"D:\ocn")
V3_LIB = ROOT / "scripts" / "simclaim_hardpair_v3" / "run_counterfactual_decoy_generation.py"
INPUT_CSV = ROOT / "data" / "simclaim_hardpair_v3" / "candidates" / "simclaim_hardpair_v3_268.csv"
INPUT_SPLITS = ROOT / "data" / "simclaim_hardpair_v3" / "splits_group_stratified"
OUT_ROOT = ROOT / "data" / "simclaim_hardpair_v3b"
OUT_CSV = OUT_ROOT / "candidates" / "simclaim_hardpair_v3b_268.csv"
OUT_JSONL = OUT_ROOT / "candidates" / "simclaim_hardpair_v3b_268.jsonl"
OUT_SPLITS = OUT_ROOT / "splits_group_stratified"
OUT_AUDIT = OUT_ROOT / "audit"
OUT_RAW = OUT_ROOT / "raw_llm"
REPORT_ROOT = ROOT / "reports" / "simclaim_hardpair_v3b"

RAW_JSONL = OUT_RAW / "v3b_relation_decoy_raw_outputs.jsonl"
GEN_AUDIT = OUT_AUDIT / "v3b_relation_decoy_generation_audit.csv"
QUALITY_AUDIT = OUT_AUDIT / "v3b_fidelity_quality_audit.csv"
SPLIT_AUDIT = OUT_AUDIT / "v3b_split_distribution_audit.csv"
PREFIX_DIAG = REPORT_ROOT / "v3b_prefix_leakage_diagnostic.csv"
SUMMARY_JSON = REPORT_ROOT / "v3b_summary.json"
REPORT_MD = REPORT_ROOT / "v3b_report.md"

LABELS = ["supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate"]
TARGETS = [
    "issue_binary_label_guess",
    "escalation_binary_label_guess",
    "contradiction_binary_label_guess",
    "candidate_label_guess",
]


def load_v3():
    spec = importlib.util.spec_from_file_location("v3lib", V3_LIB)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def utc_now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_space(text):
    return re.sub(r"\s+", " ", text or "").strip()


def sha256_text(text):
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


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
                    fieldnames.append(key)
                    seen.add(key)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def make_prompt(gid, items):
    base = items[0]
    evidence = normalize_space(base.get("evidence_text_original_locked") or base.get("evidence_text_original") or base.get("evidence_text") or "")[:1900]
    finding = normalize_space(base.get("evidence_base_finding") or "")[:700]
    current = [
        {"label": r.get("candidate_label_guess"), "claim": normalize_space(r.get("claim_text", ""))[:360]}
        for r in items
    ]
    return [
        {
            "role": "system",
            "content": (
                "You create scientific claim-evidence hard decoys. The evidence excerpt is locked and must never be rewritten. "
                "Generate only candidate claims. Return strict JSON only."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Group: {gid}\nPaper: {base.get('paper_title','')}\nDomain: {base.get('domain','')}\n\n"
                f"LOCKED evidence excerpt:\n{evidence}\n\nEvidence base finding:\n{finding}\n\n"
                f"Previous claims, for diagnosis only:\n{json.dumps(current, ensure_ascii=False)}\n\n"
                "Generate exactly four new candidate claims for the same locked evidence: supported, mild_scope_overclaim, "
                "strong_action_overclaim, contradiction_candidate.\n\n"
                "v3b objective: make labels depend on claim-evidence relation, not claim-only style. "
                "A reader who sees only the claim should find all four claims similarly plausible and similarly framed.\n\n"
                "Rules:\n"
                "1. Use one shared neutral frame across all four claims, such as evaluation context, use case, benchmark interpretation, practical assessment, or decision context. "
                "These words must appear across both escalation=0 and escalation=1 claims, not only in strong_action_overclaim.\n"
                "2. Do NOT make strong_action_overclaim visually dramatic. Avoid deploy, deployment, policy, safety, guarantee, proves, always, never.\n"
                "3. supported may include the same neutral use/evaluation vocabulary, but only within what the evidence truly states.\n"
                "4. contradiction_candidate should look like the same kind of neutral scientific statement, but assert one plausible alternative factual relation that conflicts with the evidence. Avoid explicit negation if possible.\n"
                "5. mild_scope_overclaim and strong_action_overclaim should be subtle relational shifts, not obvious words.\n"
                "6. Similar length, 24-34 words, one sentence each, same level of specificity.\n"
                "7. Avoid giveaway words: supported, overclaim, unsupported, contradiction, opposite, false, deployment-ready.\n"
                "8. Do not copy evidence verbatim except short technical terms. Do not invent numbers or citations.\n\n"
                "Return JSON exactly:\n"
                "{\n"
                "  \"decoy_style_plan\": \"...\",\n"
                "  \"locked_evidence_unchanged\": true,\n"
                "  \"shared_claim_only_decoy_terms\": \"...\",\n"
                "  \"variants\": [\n"
                "    {\"label\": \"supported\", \"claim_text\": \"...\", \"evidence_relation_note\": \"...\", \"claim_only_leakage_risk\": \"low|medium|high\"},\n"
                "    ... four labels exactly ...\n"
                "  ]\n"
                "}\n"
                "JSON only."
            ),
        },
    ]


def configure_v3_module(v3):
    v3.INPUT_CSV = INPUT_CSV
    v3.INPUT_SPLITS = INPUT_SPLITS
    v3.OUT_ROOT = OUT_ROOT
    v3.OUT_CSV = OUT_CSV
    v3.OUT_JSONL = OUT_JSONL
    v3.OUT_SPLITS = OUT_SPLITS
    v3.OUT_AUDIT = OUT_AUDIT
    v3.OUT_RAW = OUT_RAW
    v3.REPORT_ROOT = REPORT_ROOT
    v3.RAW_JSONL = RAW_JSONL
    v3.GEN_AUDIT = GEN_AUDIT
    v3.QUALITY_AUDIT = QUALITY_AUDIT
    v3.SPLIT_AUDIT = SPLIT_AUDIT
    v3.PREFIX_DIAG = PREFIX_DIAG
    v3.SUMMARY_JSON = SUMMARY_JSON
    v3.REPORT_MD = REPORT_MD
    v3.make_prompt = make_prompt


def binary_labels(label):
    return {
        "issue_binary_label_guess": "0" if label == "supported" else "1",
        "escalation_binary_label_guess": "1" if label in {"mild_scope_overclaim", "strong_action_overclaim"} else "0",
        "contradiction_binary_label_guess": "1" if label == "contradiction_candidate" else "0",
    }


def build_rows(source_rows, payloads, model):
    created = utc_now()
    by_group_label = {}
    for gid, payload in payloads.items():
        for variant in payload["variants"]:
            by_group_label[(gid, variant["label"])] = (payload, variant)

    out = []
    for row in source_rows:
        gid = row["hardpair_group_id"]
        label = row["candidate_label_guess"]
        payload, variant = by_group_label[(gid, label)]
        evidence_locked = row.get("evidence_text_original_locked") or row.get("evidence_text_original") or row.get("evidence_text") or ""
        new = dict(row)
        new["dataset_line"] = "simclaim_hardpair_v3b_268"
        new["dataset_status"] = "ai_generated_relation_decoy_candidate_set_not_gold"
        new["source_dataset"] = "simclaim_hardpair_v3_268"
        new["source_file"] = str(INPUT_CSV)
        new["claim_text_before_v3b"] = row.get("claim_text", "")
        new["claim_text"] = variant["claim_text"]
        new["claim_text_detemplated"] = variant["claim_text"]
        new["candidate_label_guess"] = label
        new["variant_type"] = label
        new.update(binary_labels(label))
        new["claim_generation_role"] = "synthetic_candidate_claim_for_locked_evidence_relation_decoy"
        new["evidence_text_original_locked"] = evidence_locked
        new["evidence_text_locked_sha256"] = sha256_text(evidence_locked)
        new["evidence_lock_status"] = "locked_from_source_excerpt_not_modified"
        new["evidence_fidelity_policy"] = "evidence text/source/location copied from source; only candidate claim text generated"
        new["v3b_generation_model"] = model
        new["v3b_generation_status"] = payload.get("generation_status", "")
        new["v3b_decoy_style_plan"] = payload.get("decoy_style_plan", "")
        new["v3b_evidence_relation_note"] = variant.get("evidence_relation_note", "")
        new["v3b_claim_only_leakage_risk"] = variant.get("claim_only_leakage_risk", "")
        new["human_audited"] = "false"
        new["final_label"] = "false"
        new["gold_label"] = "false"
        new["paper_valid"] = "false"
        new["paper_use_allowed"] = "false"
        new["main_text_allowed"] = "false"
        new["needs_human_review"] = "true"
        new["processing_version"] = "simclaim_hardpair_v3b_268_derived_2026-07-01"
        new["created_at_utc"] = created
        out.append(new)
    return out


def split_membership():
    membership = {}
    for split in ["train", "dev", "test"]:
        for row in read_csv(INPUT_SPLITS / f"{split}.csv"):
            membership[row["candidate_id"]] = split
    return membership


def write_splits(rows, fieldnames):
    membership = split_membership()
    counts = {}
    for split in ["train", "dev", "test"]:
        split_rows = [r for r in rows if membership.get(r["candidate_id"]) == split]
        counts[split] = len(split_rows)
        write_csv(OUT_SPLITS / f"{split}.csv", split_rows, fieldnames)
        write_jsonl(OUT_SPLITS / f"{split}.jsonl", split_rows)
    write_csv(OUT_SPLITS / "all.csv", rows, fieldnames)
    write_jsonl(OUT_SPLITS / "all.jsonl", rows)
    return counts


def prefix_key(text, n):
    clean = normalize_space(re.sub(r"[^\w\s:-]", " ", (text or "").lower()))
    return " ".join(clean.split()[:n])


def macro_f1(y_true, y_pred):
    labels = sorted(set(y_true) | set(y_pred))
    vals = []
    for label in labels:
        tp = sum(1 for a, b in zip(y_true, y_pred) if a == label and b == label)
        fp = sum(1 for a, b in zip(y_true, y_pred) if a != label and b == label)
        fn = sum(1 for a, b in zip(y_true, y_pred) if a == label and b != label)
        p = tp / (tp + fp) if tp + fp else 0
        r = tp / (tp + fn) if tp + fn else 0
        vals.append((2 * p * r / (p + r)) if p + r else 0)
    return sum(vals) / len(vals) if vals else 0


def accuracy(y_true, y_pred):
    return sum(1 for a, b in zip(y_true, y_pred) if a == b) / len(y_true) if y_true else 0


def prefix_diag():
    by_split = {split: read_csv(OUT_SPLITS / f"{split}.csv") for split in ["train", "dev", "test"]}
    rows = []
    for target in TARGETS:
        for n in [1, 4, 6]:
            default = Counter(r[target] for r in by_split["train"]).most_common(1)[0][0]
            maps = defaultdict(Counter)
            for r in by_split["train"]:
                maps[prefix_key(r["claim_text"], n)][r[target]] += 1
            mapping = {k: c.most_common(1)[0][0] for k, c in maps.items()}
            for split in ["dev", "test"]:
                eval_rows = by_split[split]
                y_true = [r[target] for r in eval_rows]
                y_pred = [mapping.get(prefix_key(r["claim_text"], n), default) for r in eval_rows]
                rows.append({
                    "dataset": "simclaim_hardpair_v3b_268",
                    "target": target,
                    "prefix_mode": f"first{n}",
                    "eval_split": split,
                    "n_train": len(by_split["train"]),
                    "n_eval": len(eval_rows),
                    "accuracy": f"{accuracy(y_true, y_pred):.6f}",
                    "macro_f1": f"{macro_f1(y_true, y_pred):.6f}",
                    "n_unique_eval_prefixes": len(set(prefix_key(r["claim_text"], n) for r in eval_rows)),
                })
    write_csv(PREFIX_DIAG, rows)
    return rows


def word_count(text):
    return len(re.findall(r"\b[\w-]+\b", text or ""))


def audits(rows, split_counts, prefix_rows):
    cues = ["supported", "overclaim", "unsupported", "contradiction", "opposite", "false", "deployment-ready"]
    dup = Counter(normalize_space(r["claim_text"]).lower() for r in rows)
    quality = []
    for row in rows:
        locked = row.get("evidence_text_original_locked", "")
        current = row.get("evidence_text_original") or row.get("evidence_text") or ""
        unchanged = locked == current and sha256_text(locked) == row.get("evidence_text_locked_sha256")
        hits = [cue for cue in cues if cue in row["claim_text"].lower()]
        quality.append({
            "candidate_id": row["candidate_id"],
            "hardpair_group_id": row["hardpair_group_id"],
            "candidate_label_guess": row["candidate_label_guess"],
            "word_count": word_count(row["claim_text"]),
            "leakage_cue_hit_count": len(hits),
            "leakage_cue_hits": "; ".join(hits),
            "duplicate_claim_count": dup[normalize_space(row["claim_text"]).lower()],
            "evidence_locked_unchanged": str(unchanged).lower(),
            "evidence_text_locked_sha256": row["evidence_text_locked_sha256"],
            "source_trace_complete": str(bool(row.get("claim_source_url") and row.get("evidence_source_url") and row.get("source_location"))).lower(),
            "claim_generation_role": row["claim_generation_role"],
            "claim_text": row["claim_text"],
        })
    write_csv(QUALITY_AUDIT, quality)

    split_rows = []
    for split in ["train", "dev", "test"]:
        part = read_csv(OUT_SPLITS / f"{split}.csv")
        for target in TARGETS:
            for label, count in sorted(Counter(r[target] for r in part).items()):
                split_rows.append({"split": split, "target": target, "label": label, "count": count})
    write_csv(SPLIT_AUDIT, split_rows)

    n = len(rows)
    summary = {
        "dataset": "simclaim_hardpair_v3b_268",
        "source_dataset": str(INPUT_CSV),
        "n_rows": n,
        "n_groups": len(set(r["hardpair_group_id"] for r in rows)),
        "split_counts": split_counts,
        "label_counts": dict(Counter(r["candidate_label_guess"] for r in rows)),
        "generation_status_counts": dict(Counter(r.get("v3b_generation_status", "") for r in rows)),
        "evidence_locked_unchanged_rate": round(sum(1 for q in quality if q["evidence_locked_unchanged"] == "true") / n, 6),
        "source_trace_complete_rate": round(sum(1 for q in quality if q["source_trace_complete"] == "true") / n, 6),
        "duplicate_claim_rows": sum(1 for q in quality if int(q["duplicate_claim_count"]) > 1),
        "leakage_cue_rows": sum(1 for q in quality if int(q["leakage_cue_hit_count"]) > 0),
        "worst_test_prefix_macro_f1": max([float(r["macro_f1"]) for r in prefix_rows if r["eval_split"] == "test"], default=0),
        "outputs": {
            "candidates_csv": str(OUT_CSV),
            "splits_dir": str(OUT_SPLITS),
            "quality_audit_csv": str(QUALITY_AUDIT),
            "split_audit_csv": str(SPLIT_AUDIT),
            "prefix_diagnostic_csv": str(PREFIX_DIAG),
            "report_md": str(REPORT_MD),
        },
        "created_at_utc": utc_now(),
    }
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(summary, prefix_rows)
    return summary


def write_report(summary, prefix_rows):
    lines = []
    lines.append("# SimClaim hard-pair v3b report")
    lines.append("")
    lines.append("v3b preserves locked evidence and rewrites only synthetic candidate claims to reduce claim-only leakage.")
    lines.append("")
    lines.append(f"- Rows: {summary['n_rows']}")
    lines.append(f"- Groups: {summary['n_groups']}")
    lines.append(f"- Label counts: {summary['label_counts']}")
    lines.append(f"- Evidence locked unchanged rate: {summary['evidence_locked_unchanged_rate']}")
    lines.append(f"- Source trace complete rate: {summary['source_trace_complete_rate']}")
    lines.append(f"- Duplicate claim rows: {summary['duplicate_claim_rows']}")
    lines.append(f"- Leakage cue rows: {summary['leakage_cue_rows']}")
    lines.append("")
    lines.append("| target | prefix | split | acc | macro-F1 |")
    lines.append("|---|---:|---|---:|---:|")
    for r in prefix_rows:
        lines.append(f"| {r['target']} | {r['prefix_mode']} | {r['eval_split']} | {r['accuracy']} | {r['macro_f1']} |")
    lines.append("")
    for k, v in summary["outputs"].items():
        lines.append(f"- {k}: `{v}`")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-workers", type=int, default=4)
    args = parser.parse_args()

    for p in [OUT_CSV.parent, OUT_SPLITS, OUT_AUDIT, OUT_RAW, REPORT_ROOT]:
        p.mkdir(parents=True, exist_ok=True)

    api_key = os.environ.get("LLM_API_KEY", "").strip()
    base_url = os.environ.get("LLM_BASE_URL", "https://api.holysheep.ai/v1/chat/completions").strip()
    model = os.environ.get("LLM_MODEL", "gpt-5.5").strip()
    if not api_key:
        raise SystemExit("LLM_API_KEY is required")

    v3 = load_v3()
    configure_v3_module(v3)
    source_rows = read_csv(INPUT_CSV)
    groups = v3.group_rows(source_rows)
    payloads = v3.run_generation(groups, api_key, base_url, model, args.max_workers)
    out_rows = build_rows(source_rows, payloads, model)
    fields = []
    seen = set()
    for row in out_rows:
        for key in row:
            if key not in seen:
                fields.append(key)
                seen.add(key)
    write_csv(OUT_CSV, out_rows, fields)
    write_jsonl(OUT_JSONL, out_rows)
    split_counts = write_splits(out_rows, fields)
    prefix_rows = prefix_diag()
    summary = audits(out_rows, split_counts, prefix_rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
