import argparse
import csv
import datetime as dt
import hashlib
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
HELPER_PATH = ROOT / "scripts" / "simclaim_hardpair_v2" / "run_hardpair_generation.py"
INPUT_CSV = ROOT / "data" / "simclaim_hardpair_v2b" / "candidates" / "simclaim_hardpair_v2b_268.csv"
INPUT_SPLITS = ROOT / "data" / "simclaim_hardpair_v2b" / "splits_group_stratified"
OUT_ROOT = ROOT / "data" / "simclaim_hardpair_v3"
OUT_CSV = OUT_ROOT / "candidates" / "simclaim_hardpair_v3_268.csv"
OUT_JSONL = OUT_ROOT / "candidates" / "simclaim_hardpair_v3_268.jsonl"
OUT_SPLITS = OUT_ROOT / "splits_group_stratified"
OUT_AUDIT = OUT_ROOT / "audit"
OUT_RAW = OUT_ROOT / "raw_llm"
REPORT_ROOT = ROOT / "reports" / "simclaim_hardpair_v3"

RAW_JSONL = OUT_RAW / "v3_counterfactual_decoy_raw_outputs.jsonl"
GEN_AUDIT = OUT_AUDIT / "v3_counterfactual_generation_audit.csv"
QUALITY_AUDIT = OUT_AUDIT / "v3_fidelity_quality_audit.csv"
SPLIT_AUDIT = OUT_AUDIT / "v3_split_distribution_audit.csv"
PREFIX_DIAG = REPORT_ROOT / "v3_prefix_leakage_diagnostic.csv"
SUMMARY_JSON = REPORT_ROOT / "v3_summary.json"
REPORT_MD = REPORT_ROOT / "v3_report.md"

LABELS = ["supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate"]
TARGETS = [
    "issue_binary_label_guess",
    "escalation_binary_label_guess",
    "contradiction_binary_label_guess",
    "candidate_label_guess",
]

LEAKAGE_CUES = [
    "supported",
    "overclaim",
    "unsupported",
    "contradiction",
    "contradicts",
    "opposite",
    "deployment-ready",
    "ready for deployment",
    "all settings",
    "always",
    "never",
    "guarantees",
    "proves",
    "definitively",
]


def load_helper():
    spec = importlib.util.spec_from_file_location("helper", HELPER_PATH)
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
        fieldnames = infer_fields(rows)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def append_csv(path, row, fieldnames, lock):
    with lock:
        exists = path.exists() and path.stat().st_size > 0
        with path.open("a", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            if not exists:
                writer.writeheader()
            writer.writerow(row)


def append_jsonl(path, obj, lock):
    with lock:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def infer_fields(rows):
    fields = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fields.append(key)
                seen.add(key)
    return fields


def normalize_space(text):
    return re.sub(r"\s+", " ", text or "").strip()


def sha256_text(text):
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def word_count(text):
    return len(re.findall(r"\b[\w-]+\b", text or ""))


def cue_hits(text):
    lower = (text or "").lower()
    return [cue for cue in LEAKAGE_CUES if cue in lower]


def group_rows(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row.get("hardpair_group_id")].append(row)
    out = []
    for gid, items in sorted(groups.items()):
        items = sorted(items, key=lambda r: LABELS.index(r.get("candidate_label_guess", "supported")))
        out.append((gid, items))
    return out


def make_prompt(gid, items):
    base = items[0]
    evidence = normalize_space(base.get("evidence_text_original") or base.get("evidence_text") or "")[:1900]
    finding = normalize_space(base.get("evidence_base_finding") or "")[:700]
    current = [
        {"label": r.get("candidate_label_guess"), "claim": normalize_space(r.get("claim_text", ""))[:360]}
        for r in items
    ]
    return [
        {
            "role": "system",
            "content": (
                "You create scientific claim-evidence counterfactual decoys. "
                "Never rewrite the evidence. Generate only candidate claims. Return strict JSON only."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Group: {gid}\n"
                f"Paper: {base.get('paper_title','')}\n"
                f"Domain: {base.get('domain','')}\n\n"
                f"LOCKED evidence excerpt, do not rewrite:\n{evidence}\n\n"
                f"Evidence base finding:\n{finding}\n\n"
                f"Previous claims, for diagnosis only:\n{json.dumps(current, ensure_ascii=False)}\n\n"
                "Generate exactly four candidate claims for this same locked evidence: supported, mild_scope_overclaim, "
                "strong_action_overclaim, contradiction_candidate.\n\n"
                "Main goal: reduce claim-only leakage, especially escalation. Make the four claims plausible and similar when the evidence is hidden.\n\n"
                "Counterfactual-decoy rules:\n"
                "1. Use a shared neutral vocabulary frame across all four claims. Include similar words about evaluation, use, setting, or decision-making in both escalation=0 and escalation=1 claims when semantically possible.\n"
                "2. Do not make supported claims timid and strong claims dramatic. The supported claim may use applied/evaluation wording only if the evidence supports that narrow statement.\n"
                "3. Make mild and strong claims subtle: change scope/action relation, not obvious style.\n"
                "4. Make contradiction a plausible alternative factual statement; avoid explicit words like contradiction, opposite, false, unsupported.\n"
                "5. Similar length: 23-34 words each. Similar grammar: one sentence each.\n"
                "6. Avoid giveaway phrases: supported, overclaim, unsupported, contradiction, opposite, deployment-ready, policy action, always, never, guarantees, proves.\n"
                "7. Do not copy the locked evidence verbatim except short technical terms.\n"
                "8. Do not invent numbers, paper names, citations, or experimental results.\n\n"
                "For each output include:\n"
                "- label\n"
                "- claim_text\n"
                "- evidence_relation_note: why label follows from relation to locked evidence\n"
                "- shared_decoy_terms: terms intentionally shared across labels\n"
                "- claim_only_leakage_risk: low|medium|high\n\n"
                "Return JSON exactly as:\n"
                "{\n"
                "  \"decoy_style_plan\": \"...\",\n"
                "  \"locked_evidence_unchanged\": true,\n"
                "  \"variants\": [ ... four objects ... ]\n"
                "}\n"
                "JSON only."
            ),
        },
    ]


def validate_payload(helper, text):
    payload = helper.extract_json(text)
    variants = payload.get("variants", [])
    by_label = {}
    for item in variants:
        label = normalize_space(str(item.get("label", "")))
        claim = normalize_space(str(item.get("claim_text", "")))
        if label in LABELS and claim:
            by_label[label] = {
                "label": label,
                "claim_text": claim,
                "evidence_relation_note": normalize_space(str(item.get("evidence_relation_note", ""))),
                "shared_decoy_terms": normalize_space(str(item.get("shared_decoy_terms", ""))),
                "claim_only_leakage_risk": normalize_space(str(item.get("claim_only_leakage_risk", ""))).lower() or "unknown",
            }
    missing = [label for label in LABELS if label not in by_label]
    if missing:
        raise ValueError(f"missing labels: {missing}")
    return {
        "decoy_style_plan": normalize_space(str(payload.get("decoy_style_plan", ""))),
        "locked_evidence_unchanged": bool(payload.get("locked_evidence_unchanged", True)),
        "variants": [by_label[label] for label in LABELS],
    }


def fallback_payload(items):
    # Conservative fallback: copy v2b claims with provenance intact.
    by_label = {r["candidate_label_guess"]: r for r in items}
    return {
        "decoy_style_plan": "fallback copied v2b claims; provenance retained",
        "locked_evidence_unchanged": True,
        "variants": [
            {
                "label": label,
                "claim_text": normalize_space(by_label[label].get("claim_text", "")),
                "evidence_relation_note": "fallback copied previous candidate claim",
                "shared_decoy_terms": "",
                "claim_only_leakage_risk": "medium",
            }
            for label in LABELS
        ],
    }


AUDIT_FIELDS = [
    "hardpair_group_id",
    "generation_status",
    "decoy_style_plan",
    "locked_evidence_unchanged",
    "supported_claim",
    "mild_scope_overclaim_claim",
    "strong_action_overclaim_claim",
    "contradiction_candidate_claim",
    "error",
]


def load_existing():
    if not GEN_AUDIT.exists():
        return {}
    existing = {}
    for row in read_csv(GEN_AUDIT):
        gid = row.get("hardpair_group_id")
        if not gid:
            continue
        ok = True
        variants = []
        for label in LABELS:
            claim = row.get(f"{label}_claim", "")
            if not claim:
                ok = False
                break
            variants.append({
                "label": label,
                "claim_text": claim,
                "evidence_relation_note": "",
                "shared_decoy_terms": "",
                "claim_only_leakage_risk": "",
            })
        if ok:
            existing[gid] = {
                "decoy_style_plan": row.get("decoy_style_plan", ""),
                "locked_evidence_unchanged": row.get("locked_evidence_unchanged", "true").lower() == "true",
                "generation_status": row.get("generation_status", ""),
                "variants": variants,
            }
    return existing


def generate_group(helper, gid, items, api_key, base_url, model):
    messages = make_prompt(gid, items)
    last_error = ""
    for attempt in range(1, 4):
        try:
            response = helper.post_chat(messages, api_key, base_url, model, timeout=140)
            content = response["choices"][0]["message"]["content"]
            payload = validate_payload(helper, content)
            raw = {"hardpair_group_id": gid, "status": "success", "attempt": attempt, "model": model, "response": response}
            return payload, raw, "success", ""
        except Exception as exc:
            last_error = str(exc)
            time.sleep(min(22, 2 ** attempt))
    payload = fallback_payload(items)
    raw = {"hardpair_group_id": gid, "status": "fallback_after_llm_error", "model": model, "error": last_error[:1000]}
    return payload, raw, "fallback_after_llm_error", last_error[:500]


def run_generation(groups, api_key, base_url, model, max_workers):
    helper = load_helper()
    existing = load_existing()
    todo = [(gid, items) for gid, items in groups if gid not in existing]
    print(f"v3_existing_groups={len(existing)} v3_todo_groups={len(todo)}", flush=True)
    raw_lock = threading.Lock()
    audit_lock = threading.Lock()
    completed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(generate_group, helper, gid, items, api_key, base_url, model): (gid, items) for gid, items in todo}
        for fut in as_completed(futs):
            gid, _items = futs[fut]
            payload, raw, status, error = fut.result()
            append_jsonl(RAW_JSONL, raw, raw_lock)
            row = {
                "hardpair_group_id": gid,
                "generation_status": status,
                "decoy_style_plan": payload["decoy_style_plan"],
                "locked_evidence_unchanged": str(payload["locked_evidence_unchanged"]).lower(),
                "error": error,
            }
            for v in payload["variants"]:
                row[f"{v['label']}_claim"] = v["claim_text"]
            append_csv(GEN_AUDIT, row, AUDIT_FIELDS, audit_lock)
            payload["generation_status"] = status
            existing[gid] = payload
            completed += 1
            if completed % 10 == 0 or completed == len(todo):
                print(f"v3_progress={completed}/{len(todo)}", flush=True)
    return load_existing()


def split_membership():
    membership = {}
    for split in ["train", "dev", "test"]:
        for row in read_csv(INPUT_SPLITS / f"{split}.csv"):
            membership[row["candidate_id"]] = split
    return membership


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
        for v in payload["variants"]:
            by_group_label[(gid, v["label"])] = (payload, v)

    rows = []
    for row in source_rows:
        gid = row["hardpair_group_id"]
        label = row["candidate_label_guess"]
        payload, variant = by_group_label[(gid, label)]
        evidence_locked = row.get("evidence_text_original") or row.get("evidence_text") or ""
        out = dict(row)
        out["dataset_line"] = "simclaim_hardpair_v3_268"
        out["dataset_status"] = "ai_generated_counterfactual_decoy_candidate_set_not_gold"
        out["source_dataset"] = "simclaim_hardpair_v2b_268"
        out["source_file"] = str(INPUT_CSV)
        out["claim_text_before_v3"] = row.get("claim_text", "")
        out["claim_text"] = variant["claim_text"]
        out["claim_text_detemplated"] = variant["claim_text"]
        out["candidate_label_guess"] = label
        out["variant_type"] = label
        out.update(binary_labels(label))
        out["claim_generation_role"] = "synthetic_candidate_claim_for_locked_evidence"
        out["evidence_text_original_locked"] = evidence_locked
        out["evidence_text_locked_sha256"] = sha256_text(evidence_locked)
        out["evidence_lock_status"] = "locked_from_source_excerpt_not_modified"
        out["evidence_fidelity_policy"] = "evidence text/source/location copied from source; only candidate claim text generated"
        out["v3_generation_model"] = model
        out["v3_generation_status"] = payload.get("generation_status", "")
        out["v3_decoy_style_plan"] = payload.get("decoy_style_plan", "")
        out["v3_evidence_relation_note"] = variant.get("evidence_relation_note", "")
        out["v3_shared_decoy_terms"] = variant.get("shared_decoy_terms", "")
        out["v3_claim_only_leakage_risk"] = variant.get("claim_only_leakage_risk", "")
        out["human_audited"] = "false"
        out["final_label"] = "false"
        out["gold_label"] = "false"
        out["paper_valid"] = "false"
        out["paper_use_allowed"] = "false"
        out["main_text_allowed"] = "false"
        out["needs_human_review"] = "true"
        out["processing_version"] = "simclaim_hardpair_v3_268_derived_2026-07-01"
        out["created_at_utc"] = created
        rows.append(out)
    return rows


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
                    "dataset": "simclaim_hardpair_v3_268",
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


def audits(rows, split_counts, prefix_rows):
    dup = Counter(normalize_space(r["claim_text"]).lower() for r in rows)
    source_evidence_unchanged = 0
    quality = []
    for r in rows:
        locked = r.get("evidence_text_original_locked", "")
        current_original = r.get("evidence_text_original") or r.get("evidence_text") or ""
        unchanged = locked == current_original and sha256_text(locked) == r.get("evidence_text_locked_sha256")
        if unchanged:
            source_evidence_unchanged += 1
        hits = cue_hits(r.get("claim_text", ""))
        quality.append({
            "candidate_id": r["candidate_id"],
            "hardpair_group_id": r["hardpair_group_id"],
            "candidate_label_guess": r["candidate_label_guess"],
            "word_count": word_count(r["claim_text"]),
            "leakage_cue_hit_count": len(hits),
            "leakage_cue_hits": "; ".join(hits),
            "duplicate_claim_count": dup[normalize_space(r["claim_text"]).lower()],
            "evidence_locked_unchanged": str(unchanged).lower(),
            "evidence_text_locked_sha256": r["evidence_text_locked_sha256"],
            "source_trace_complete": str(bool(r.get("claim_source_url") and r.get("evidence_source_url") and r.get("source_location"))).lower(),
            "claim_generation_role": r["claim_generation_role"],
            "claim_text": r["claim_text"],
        })
    write_csv(QUALITY_AUDIT, quality)

    split_audit = []
    for split in ["train", "dev", "test"]:
        split_rows = read_csv(OUT_SPLITS / f"{split}.csv")
        for target in TARGETS:
            for label, count in sorted(Counter(r[target] for r in split_rows).items()):
                split_audit.append({"split": split, "target": target, "label": label, "count": count})
    write_csv(SPLIT_AUDIT, split_audit)

    n = len(rows)
    summary = {
        "dataset": "simclaim_hardpair_v3_268",
        "source_dataset": str(INPUT_CSV),
        "n_rows": n,
        "n_groups": len(set(r["hardpair_group_id"] for r in rows)),
        "split_counts": split_counts,
        "label_counts": dict(Counter(r["candidate_label_guess"] for r in rows)),
        "generation_status_counts": dict(Counter(r.get("v3_generation_status", "") for r in rows)),
        "evidence_locked_unchanged_rate": round(source_evidence_unchanged / n, 6) if n else 0,
        "source_trace_complete_rate": round(sum(1 for q in quality if q["source_trace_complete"] == "true") / n, 6) if n else 0,
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
    lines.append("# SimClaim hard-pair v3 report")
    lines.append("")
    lines.append("v3 is a fidelity-preserving counterfactual-decoy dataset. Evidence excerpts are locked; only synthetic candidate claims are regenerated.")
    lines.append("")
    lines.append("## Status")
    lines.append("")
    lines.append(f"- Rows: {summary['n_rows']}")
    lines.append(f"- Groups: {summary['n_groups']}")
    lines.append(f"- Label counts: {summary['label_counts']}")
    lines.append(f"- Split counts: {summary['split_counts']}")
    lines.append(f"- Evidence locked unchanged rate: {summary['evidence_locked_unchanged_rate']}")
    lines.append(f"- Source trace complete rate: {summary['source_trace_complete_rate']}")
    lines.append(f"- Duplicate claim rows: {summary['duplicate_claim_rows']}")
    lines.append(f"- Leakage cue rows: {summary['leakage_cue_rows']}")
    lines.append(f"- Worst test prefix macro-F1: {summary['worst_test_prefix_macro_f1']}")
    lines.append("")
    lines.append("## Prefix diagnostic")
    lines.append("")
    lines.append("| target | prefix | split | acc | macro-F1 |")
    lines.append("|---|---:|---|---:|---:|")
    for r in prefix_rows:
        lines.append(f"| {r['target']} | {r['prefix_mode']} | {r['eval_split']} | {r['accuracy']} | {r['macro_f1']} |")
    lines.append("")
    lines.append("## Files")
    lines.append("")
    for k, v in summary["outputs"].items():
        lines.append(f"- {k}: `{v}`")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-workers", type=int, default=6)
    args = parser.parse_args()
    ensure_dirs()
    api_key = os.environ.get("LLM_API_KEY", "").strip()
    base_url = os.environ.get("LLM_BASE_URL", "https://api.holysheep.ai/v1/chat/completions").strip()
    model = os.environ.get("LLM_MODEL", "gpt-5.5").strip()
    if not api_key:
        raise SystemExit("LLM_API_KEY is required")
    source_rows = read_csv(INPUT_CSV)
    groups = group_rows(source_rows)
    payloads = run_generation(groups, api_key, base_url, model, args.max_workers)
    out_rows = build_rows(source_rows, payloads, model)
    fields = infer_fields(out_rows)
    write_csv(OUT_CSV, out_rows, fields)
    write_jsonl(OUT_JSONL, out_rows)
    split_counts = write_splits(out_rows, fields)
    prefix_rows = prefix_diag()
    summary = audits(out_rows, split_counts, prefix_rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
