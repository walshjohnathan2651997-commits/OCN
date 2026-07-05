import argparse
import csv
import datetime as dt
import importlib.util
import json
import os
import re
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


ROOT = Path(r"D:\ocn")
LIB_PATH = ROOT / "scripts" / "simclaim_hardpair_v2" / "run_hardpair_generation.py"
INPUT_CSV = ROOT / "data" / "simclaim_hardpair_v2" / "candidates" / "simclaim_hardpair_v2_268.csv"
INPUT_SPLIT_DIR = ROOT / "data" / "simclaim_hardpair_v2" / "splits_group_stratified"
OUT_ROOT = ROOT / "data" / "simclaim_hardpair_v2b"
OUT_CSV = OUT_ROOT / "candidates" / "simclaim_hardpair_v2b_268.csv"
OUT_JSONL = OUT_ROOT / "candidates" / "simclaim_hardpair_v2b_268.jsonl"
OUT_SPLITS = OUT_ROOT / "splits_group_stratified"
OUT_AUDIT = OUT_ROOT / "audit"
OUT_RAW = OUT_ROOT / "raw_llm"
REPORT_ROOT = ROOT / "reports" / "simclaim_hardpair_v2b"

RAW_JSONL = OUT_RAW / "style_neutralization_raw_outputs.jsonl"
NEUTRAL_AUDIT = OUT_AUDIT / "style_neutralization_audit.csv"
QUALITY_AUDIT = OUT_AUDIT / "hardpair_v2b_quality_audit.csv"
PREFIX_DIAG = REPORT_ROOT / "hardpair_v2b_prefix_leakage_diagnostic.csv"
SUMMARY_JSON = REPORT_ROOT / "hardpair_v2b_summary.json"
REPORT_MD = REPORT_ROOT / "hardpair_v2b_report.md"

LABELS = [
    "supported",
    "mild_scope_overclaim",
    "strong_action_overclaim",
    "contradiction_candidate",
]
TARGETS = [
    "issue_binary_label_guess",
    "escalation_binary_label_guess",
    "contradiction_binary_label_guess",
    "candidate_label_guess",
]
STYLE_CUES = [
    "supported",
    "overclaim",
    "unsupported",
    "contradiction",
    "contradicts",
    "opposite",
    "deployment",
    "deploy",
    "policy",
    "safety",
    "safe",
    "real-world",
    "real world",
    "all ",
    "always",
    "never",
    "fully",
    "sufficient",
    "guarantee",
    "guarantees",
    "proves",
    "clearly",
]


def load_lib():
    spec = importlib.util.spec_from_file_location("hardpair_lib", LIB_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def utc_now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_dirs():
    for p in [OUT_CSV.parent, OUT_SPLITS, OUT_AUDIT, OUT_RAW, REPORT_ROOT]:
        p.mkdir(parents=True, exist_ok=True)


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


def append_csv(path, row, fields, lock):
    with lock:
        exists = path.exists() and path.stat().st_size > 0
        with path.open("a", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            if not exists:
                writer.writeheader()
            writer.writerow(row)


def append_jsonl(path, obj, lock):
    with lock:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize_space(text):
    return re.sub(r"\s+", " ", text or "").strip()


def word_count(text):
    return len(re.findall(r"\b[\w-]+\b", text or ""))


def style_hits(text):
    lower = (text or "").lower()
    return [cue.strip() for cue in STYLE_CUES if cue in lower]


def group_rows(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row.get("hardpair_group_id", "")].append(row)
    out = []
    for gid, items in sorted(groups.items()):
        items = sorted(items, key=lambda r: int(r.get("hardpair_variant_index") or 0))
        out.append((gid, items))
    return out


def make_prompt(gid, items):
    evidence = normalize_space(items[0].get("evidence_text", ""))[:1800]
    title = items[0].get("paper_title", "")
    current = [
        {
            "label": row.get("candidate_label_guess"),
            "claim": normalize_space(row.get("claim_text", "")),
        }
        for row in items
    ]
    return [
        {
            "role": "system",
            "content": (
                "You revise controlled scientific hard-pair claims. Return strict JSON only. "
                "Preserve labels and evidence relation; rewrite only claim wording."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Group: {gid}\nPaper: {title}\n\nEvidence:\n{evidence}\n\n"
                f"Current four claims:\n{json.dumps(current, ensure_ascii=False, indent=2)}\n\n"
                "Rewrite the four claims to reduce claim-only label leakage.\n\n"
                "Requirements:\n"
                "- Preserve the exact label semantics for each claim.\n"
                "- Make the four claims similar in length, tone, specificity, and grammar.\n"
                "- Use neutral scientific wording; avoid making supported claims consistently cautious and issue claims consistently dramatic.\n"
                "- Avoid obvious surface cues: supported, overclaim, unsupported, contradiction, opposite, deployment, policy, safety, safe, all, always, never, fully, sufficient, guarantees, proves.\n"
                "- For contradiction, assert an alternative material fact instead of using explicit negation words like 'not', 'no', or 'does not' when possible.\n"
                "- For strong action, use subtle applied consequence wording instead of explicit deployment/safety/policy language.\n"
                "- 22-34 words each if possible.\n"
                "- Do not use the same first four words for all four claims.\n\n"
                "Return JSON:\n"
                "{\n"
                "  \"neutralization_strategy\": \"...\",\n"
                "  \"variants\": [\n"
                "    {\"label\": \"supported\", \"claim_text\": \"...\", \"style_leakage_risk\": \"low|medium|high\", \"semantic_check\": \"...\"},\n"
                "    ... exactly four labels ...\n"
                "  ]\n"
                "}\n"
                "JSON only."
            ),
        },
    ]


def validate_payload(payload):
    variants = payload.get("variants", [])
    by_label = {}
    for item in variants:
        label = normalize_space(str(item.get("label", "")))
        claim = normalize_space(str(item.get("claim_text", "")))
        if label in LABELS and claim:
            by_label[label] = {
                "label": label,
                "claim_text": claim,
                "style_leakage_risk": normalize_space(str(item.get("style_leakage_risk", ""))).lower() or "unknown",
                "semantic_check": normalize_space(str(item.get("semantic_check", ""))),
            }
    missing = [label for label in LABELS if label not in by_label]
    if missing:
        raise ValueError(f"missing labels: {missing}")
    return {
        "neutralization_strategy": normalize_space(str(payload.get("neutralization_strategy", ""))),
        "variants": [by_label[label] for label in LABELS],
    }


def fallback_payload(items):
    variants = []
    for row in sorted(items, key=lambda r: LABELS.index(r.get("candidate_label_guess", "supported"))):
        claim = normalize_space(row.get("claim_text", ""))
        claim = claim.replace("deployment-ready", "usable in applied evaluation")
        claim = claim.replace("policy action", "follow-up decision")
        variants.append({
            "label": row.get("candidate_label_guess"),
            "claim_text": claim,
            "style_leakage_risk": "medium",
            "semantic_check": "fallback copied and lightly cleaned",
        })
    return {"neutralization_strategy": "fallback_light_cleanup", "variants": variants}


AUDIT_FIELDS = [
    "hardpair_group_id",
    "neutralization_status",
    "neutralization_strategy",
    "supported_claim",
    "mild_scope_overclaim_claim",
    "strong_action_overclaim_claim",
    "contradiction_candidate_claim",
    "error",
]


def load_existing():
    if not NEUTRAL_AUDIT.exists():
        return {}
    existing = {}
    for row in read_csv(NEUTRAL_AUDIT):
        gid = row.get("hardpair_group_id")
        if not gid:
            continue
        variants = []
        ok = True
        for label in LABELS:
            claim = row.get(f"{label}_claim", "")
            if not claim:
                ok = False
                break
            variants.append({
                "label": label,
                "claim_text": claim,
                "style_leakage_risk": "",
                "semantic_check": "",
            })
        if ok:
            existing[gid] = {
                "neutralization_strategy": row.get("neutralization_strategy", ""),
                "neutralization_status": row.get("neutralization_status", ""),
                "variants": variants,
            }
    return existing


def neutralize_group(lib, gid, items, api_key, base_url, model):
    messages = make_prompt(gid, items)
    last_error = ""
    for attempt in range(1, 4):
        try:
            response = lib.post_chat(messages, api_key, base_url, model, timeout=120)
            parsed = validate_payload(lib.extract_json(response["choices"][0]["message"]["content"]))
            raw = {"hardpair_group_id": gid, "status": "success", "attempt": attempt, "model": model, "response": response}
            return parsed, raw, "success", ""
        except Exception as exc:
            last_error = str(exc)
            time.sleep(min(18, 2 ** attempt))
    parsed = validate_payload(fallback_payload(items))
    raw = {"hardpair_group_id": gid, "status": "fallback_after_llm_error", "model": model, "error": last_error[:1000]}
    return parsed, raw, "fallback_after_llm_error", last_error[:500]


def run_neutralization(groups, api_key, base_url, model, max_workers):
    lib = load_lib()
    existing = load_existing()
    todo = [(gid, items) for gid, items in groups if gid not in existing]
    print(f"neutral_existing_groups={len(existing)} neutral_todo_groups={len(todo)}", flush=True)
    raw_lock = threading.Lock()
    audit_lock = threading.Lock()
    completed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(neutralize_group, lib, gid, items, api_key, base_url, model): (gid, items) for gid, items in todo}
        for fut in as_completed(futs):
            gid, _items = futs[fut]
            payload, raw, status, error = fut.result()
            append_jsonl(RAW_JSONL, raw, raw_lock)
            row = {
                "hardpair_group_id": gid,
                "neutralization_status": status,
                "neutralization_strategy": payload["neutralization_strategy"],
                "error": error,
            }
            for variant in payload["variants"]:
                row[f"{variant['label']}_claim"] = variant["claim_text"]
            append_csv(NEUTRAL_AUDIT, row, AUDIT_FIELDS, audit_lock)
            payload["neutralization_status"] = status
            existing[gid] = payload
            completed += 1
            if completed % 10 == 0 or completed == len(todo):
                print(f"neutral_progress={completed}/{len(todo)}", flush=True)
    return load_existing()


def split_membership():
    membership = {}
    for split in ["train", "dev", "test"]:
        for row in read_csv(INPUT_SPLIT_DIR / f"{split}.csv"):
            membership[row["candidate_id"]] = split
    return membership


def write_splits(rows, fieldnames):
    membership = split_membership()
    counts = {}
    for split in ["train", "dev", "test"]:
        split_rows = [r for r in rows if membership.get(r.get("candidate_id")) == split]
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
        vals.append(2 * p * r / (p + r) if p + r else 0)
    return sum(vals) / len(vals) if vals else 0


def accuracy(y_true, y_pred):
    return sum(1 for a, b in zip(y_true, y_pred) if a == b) / len(y_true) if y_true else 0


def prefix_diag(rows):
    by_split = {split: read_csv(OUT_SPLITS / f"{split}.csv") for split in ["train", "dev", "test"]}
    out = []
    for target in TARGETS:
        for n in [1, 4, 6]:
            default = Counter(r[target] for r in by_split["train"]).most_common(1)[0][0]
            maps = defaultdict(Counter)
            for row in by_split["train"]:
                maps[prefix_key(row["claim_text"], n)][row[target]] += 1
            mapping = {k: c.most_common(1)[0][0] for k, c in maps.items()}
            for split in ["dev", "test"]:
                eval_rows = by_split[split]
                y_true = [r[target] for r in eval_rows]
                y_pred = [mapping.get(prefix_key(r["claim_text"], n), default) for r in eval_rows]
                out.append({
                    "dataset": "simclaim_hardpair_v2b_268",
                    "target": target,
                    "prefix_mode": f"first{n}",
                    "eval_split": split,
                    "n_train": len(by_split["train"]),
                    "n_eval": len(eval_rows),
                    "accuracy": f"{accuracy(y_true, y_pred):.6f}",
                    "macro_f1": f"{macro_f1(y_true, y_pred):.6f}",
                    "n_unique_eval_prefixes": len(set(prefix_key(r["claim_text"], n) for r in eval_rows)),
                })
    write_csv(PREFIX_DIAG, out)
    return out


def build_rows(source_rows, payloads, model):
    created = utc_now()
    out = []
    by_group_payload = payloads
    for row in source_rows:
        gid = row["hardpair_group_id"]
        label = row["candidate_label_guess"]
        variant = next(v for v in by_group_payload[gid]["variants"] if v["label"] == label)
        new = dict(row)
        new["dataset_line"] = "simclaim_hardpair_v2b_268"
        new["dataset_status"] = "ai_generated_hardpair_style_neutralized_candidate_set_not_gold"
        new["source_dataset"] = "simclaim_hardpair_v2_268"
        new["source_file"] = str(INPUT_CSV)
        new["claim_text_before_style_neutralization"] = row["claim_text"]
        new["claim_text"] = variant["claim_text"]
        new["claim_text_detemplated"] = variant["claim_text"]
        new["hardpair_v2b_neutralization_model"] = model
        new["hardpair_v2b_neutralization_status"] = by_group_payload[gid].get("neutralization_status", "")
        new["hardpair_v2b_neutralization_strategy"] = by_group_payload[gid].get("neutralization_strategy", "")
        new["hardpair_v2b_style_leakage_risk"] = variant.get("style_leakage_risk", "")
        new["hardpair_v2b_semantic_check"] = variant.get("semantic_check", "")
        new["human_audited"] = "false"
        new["final_label"] = "false"
        new["gold_label"] = "false"
        new["paper_valid"] = "false"
        new["paper_use_allowed"] = "false"
        new["main_text_allowed"] = "false"
        new["needs_human_review"] = "true"
        new["processing_version"] = "simclaim_hardpair_v2b_268_derived_2026-07-01"
        new["created_at_utc"] = created
        out.append(new)
    return out


def audits(rows, split_counts, prefix_rows):
    dup = Counter(normalize_space(r["claim_text"]).lower() for r in rows)
    quality = []
    for row in rows:
        claim = row["claim_text"]
        hits = style_hits(claim)
        quality.append({
            "candidate_id": row["candidate_id"],
            "hardpair_group_id": row["hardpair_group_id"],
            "candidate_label_guess": row["candidate_label_guess"],
            "word_count": word_count(claim),
            "style_cue_hit_count": len(hits),
            "style_cue_hits": "; ".join(hits),
            "duplicate_claim_count": dup[normalize_space(claim).lower()],
            "prefix_first4": prefix_key(claim, 4),
            "source_trace_complete": str(bool(row.get("claim_source_url") and row.get("evidence_source_url") and row.get("source_location"))).lower(),
            "before_claim": row.get("claim_text_before_style_neutralization", ""),
            "after_claim": claim,
        })
    write_csv(QUALITY_AUDIT, quality)
    n = len(rows)
    summary = {
        "dataset": "simclaim_hardpair_v2b_268",
        "source_dataset": str(INPUT_CSV),
        "n_rows": n,
        "n_groups": len(set(r["hardpair_group_id"] for r in rows)),
        "split_counts": split_counts,
        "label_counts": dict(Counter(r["candidate_label_guess"] for r in rows)),
        "neutralization_status_counts": dict(Counter(r.get("hardpair_v2b_neutralization_status", "") for r in rows)),
        "style_cue_rows": sum(1 for q in quality if int(q["style_cue_hit_count"]) > 0),
        "duplicate_claim_rows": sum(1 for q in quality if int(q["duplicate_claim_count"]) > 1),
        "source_trace_complete_rate": round(sum(1 for q in quality if q["source_trace_complete"] == "true") / n, 6) if n else 0,
        "worst_test_prefix_macro_f1": max([float(r["macro_f1"]) for r in prefix_rows if r["eval_split"] == "test"], default=0),
        "outputs": {
            "candidates_csv": str(OUT_CSV),
            "splits_dir": str(OUT_SPLITS),
            "quality_audit_csv": str(QUALITY_AUDIT),
            "prefix_diagnostic_csv": str(PREFIX_DIAG),
            "report_md": str(REPORT_MD),
        },
    }
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(summary, prefix_rows)
    return summary


def write_report(summary, prefix_rows):
    lines = []
    lines.append("# SimClaim hard-pair v2b report")
    lines.append("")
    lines.append("v2b is a style-neutralized rewrite of v2, intended to reduce claim-only label leakage.")
    lines.append("")
    lines.append(f"- Rows: {summary['n_rows']}")
    lines.append(f"- Groups: {summary['n_groups']}")
    lines.append(f"- Split counts: {summary['split_counts']}")
    lines.append(f"- Label counts: {summary['label_counts']}")
    lines.append(f"- Neutralization status: {summary['neutralization_status_counts']}")
    lines.append(f"- Style cue rows: {summary['style_cue_rows']}")
    lines.append(f"- Duplicate claim rows: {summary['duplicate_claim_rows']}")
    lines.append(f"- Source trace complete rate: {summary['source_trace_complete_rate']}")
    lines.append(f"- Worst test prefix macro-F1: {summary['worst_test_prefix_macro_f1']}")
    lines.append("")
    lines.append("| target | prefix | split | acc | macro-F1 |")
    lines.append("|---|---:|---|---:|---:|")
    for row in prefix_rows:
        lines.append(f"| {row['target']} | {row['prefix_mode']} | {row['eval_split']} | {row['accuracy']} | {row['macro_f1']} |")
    lines.append("")
    for key, value in summary["outputs"].items():
        lines.append(f"- {key}: `{value}`")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-workers", type=int, default=6)
    args = parser.parse_args()
    ensure_dirs()
    rows = read_csv(INPUT_CSV)
    groups = group_rows(rows)
    api_key = os.environ.get("LLM_API_KEY", "").strip()
    base_url = os.environ.get("LLM_BASE_URL", "https://api.holysheep.ai/v1/chat/completions").strip()
    model = os.environ.get("LLM_MODEL", "gpt-5.5").strip()
    if not api_key:
        raise SystemExit("LLM_API_KEY is required")
    payloads = run_neutralization(groups, api_key, base_url, model, args.max_workers)
    out_rows = build_rows(rows, payloads, model)
    fieldnames = []
    for row in out_rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    write_csv(OUT_CSV, out_rows, fieldnames)
    write_jsonl(OUT_JSONL, out_rows)
    split_counts = write_splits(out_rows, fieldnames)
    prefix_rows = prefix_diag(out_rows)
    summary = audits(out_rows, split_counts, prefix_rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
