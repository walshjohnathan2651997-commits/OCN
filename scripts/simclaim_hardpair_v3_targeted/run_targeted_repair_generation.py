import argparse
import csv
import datetime as dt
import hashlib
import importlib.util
import json
import os
import re
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


ROOT = Path(r"D:\ocn")
HELPER_PATH = ROOT / "scripts" / "simclaim_hardpair_v2" / "run_hardpair_generation.py"
SOURCE_CSV = ROOT / "data" / "simclaim_hardpair_v3" / "candidates" / "simclaim_hardpair_v3_268.csv"
SOURCE_SPLITS = ROOT / "data" / "simclaim_hardpair_v3" / "splits_group_stratified"
REPAIR_QUEUE = ROOT / "data" / "simclaim_hardpair_v3" / "audit" / "v3_targeted_repair_queue.csv"
GROUP_RISK = ROOT / "data" / "simclaim_hardpair_v3" / "audit" / "v3_targeted_group_risk_audit.csv"
LEAK_TERMS = ROOT / "data" / "simclaim_hardpair_v3" / "audit" / "v3_claim_only_leakage_terms.csv"

OUT_ROOT = ROOT / "data" / "simclaim_hardpair_v3_targeted"
OUT_CSV = OUT_ROOT / "candidates" / "simclaim_hardpair_v3_targeted_268.csv"
OUT_JSONL = OUT_ROOT / "candidates" / "simclaim_hardpair_v3_targeted_268.jsonl"
OUT_SPLITS = OUT_ROOT / "splits_group_stratified"
OUT_AUDIT = OUT_ROOT / "audit"
OUT_RAW = OUT_ROOT / "raw_llm"
REPORT_ROOT = ROOT / "reports" / "simclaim_hardpair_v3_targeted_repair"

GEN_AUDIT = OUT_AUDIT / "v3_targeted_repair_generation_audit.csv"
RAW_JSONL = OUT_RAW / "v3_targeted_repair_raw_outputs.jsonl"
QUALITY_AUDIT = OUT_AUDIT / "v3_targeted_fidelity_quality_audit.csv"
SPLIT_AUDIT = OUT_AUDIT / "v3_targeted_split_distribution_audit.csv"
PREFIX_DIAG = REPORT_ROOT / "v3_targeted_prefix_diagnostic.csv"
SUMMARY_JSON = REPORT_ROOT / "v3_targeted_summary.json"
REPORT_MD = REPORT_ROOT / "v3_targeted_report.md"

LABELS = ["supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate"]
TARGETS = ["issue_binary_label_guess", "escalation_binary_label_guess", "contradiction_binary_label_guess", "candidate_label_guess"]


def load_helper():
    spec = importlib.util.spec_from_file_location("helper", HELPER_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def utc_now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def append_csv(path, row, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def append_jsonl(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
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


def normalize(text):
    return re.sub(r"\s+", " ", text or "").strip()


def sha256_text(text):
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def group_rows(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[r["hardpair_group_id"]].append(r)
    return {gid: sorted(items, key=lambda r: LABELS.index(r["candidate_label_guess"])) for gid, items in groups.items()}


def flagged_groups():
    rows = read_csv(GROUP_RISK)
    return [r["hardpair_group_id"] for r in rows]


def risky_terms_by_group():
    queue = read_csv(REPAIR_QUEUE)
    out = defaultdict(Counter)
    for r in queue:
        for term in (r.get("risk_terms_in_claim", "") or "").split(";"):
            term = term.strip()
            if term:
                out[r["hardpair_group_id"]][term] += 1
    return out


def make_prompt(gid, items, group_terms):
    base = items[0]
    evidence = normalize(base.get("evidence_text_original_locked") or base.get("evidence_text_original") or base.get("evidence_text") or "")[:1900]
    finding = normalize(base.get("evidence_base_finding") or "")[:700]
    current = [{"label": r["candidate_label_guess"], "claim": normalize(r["claim_text"])} for r in items]
    terms = ", ".join([t for t, _ in group_terms.most_common(20)])
    return [
        {
            "role": "system",
            "content": (
                "You repair a small set of scientific claim-evidence candidate claims. "
                "The evidence is locked and must not be changed. Return strict JSON only."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Group: {gid}\nPaper: {base.get('paper_title','')}\nDomain: {base.get('domain','')}\n\n"
                f"LOCKED evidence excerpt:\n{evidence}\n\nEvidence base finding:\n{finding}\n\n"
                f"Current four claims:\n{json.dumps(current, ensure_ascii=False, indent=2)}\n\n"
                f"Known claim-only leakage terms to avoid or redistribute: {terms}\n\n"
                "Rewrite exactly four candidate claims for the same locked evidence, preserving these labels: "
                "supported, mild_scope_overclaim, strong_action_overclaim, contradiction_candidate.\n\n"
                "Targeted repair rules:\n"
                "1. Keep labels determined by claim-evidence relation, not by surface wording.\n"
                "2. Remove or redistribute known leakage terms so no term is unique to one label.\n"
                "3. Do not use giveaway words: supported, overclaim, unsupported, contradiction, opposite, false, deployment-ready, policy action, guarantee, proves, always, never.\n"
                "4. Avoid label-specific phrases: strong/action claims must not all use 'basis', 'selecting', 'decisions', 'guide'; contradictions must not all use 'rather than'.\n"
                "5. Make all four claims similar in length, grammar, and specificity, 22-34 words each.\n"
                "6. Do not copy locked evidence verbatim except short technical terms. Do not invent numbers, citations, or paper names.\n"
                "7. The supported claim may be a faithful paraphrase. The mild claim subtly broadens scope/certainty. The strong claim subtly adds practical/action implication. The contradiction claim asserts a plausible conflicting factual relation without explicit contradiction wording.\n\n"
                "Return JSON:\n"
                "{\n"
                "  \"repair_strategy\": \"...\",\n"
                "  \"locked_evidence_unchanged\": true,\n"
                "  \"variants\": [\n"
                "    {\"label\": \"supported\", \"claim_text\": \"...\", \"relation_note\": \"...\", \"leakage_terms_removed\": \"...\"},\n"
                "    ... exactly four labels ...\n"
                "  ]\n"
                "}\n"
                "JSON only."
            ),
        },
    ]


def parse_payload(helper, text):
    obj = helper.extract_json(text)
    variants = obj.get("variants", [])
    by_label = {}
    for v in variants:
        label = normalize(str(v.get("label", "")))
        claim = normalize(str(v.get("claim_text", "")))
        if label in LABELS and claim:
            by_label[label] = {
                "label": label,
                "claim_text": claim,
                "relation_note": normalize(str(v.get("relation_note", ""))),
                "leakage_terms_removed": normalize(str(v.get("leakage_terms_removed", ""))),
            }
    missing = [l for l in LABELS if l not in by_label]
    if missing:
        raise ValueError(f"missing labels: {missing}")
    return {
        "repair_strategy": normalize(str(obj.get("repair_strategy", ""))),
        "locked_evidence_unchanged": bool(obj.get("locked_evidence_unchanged", True)),
        "variants": [by_label[l] for l in LABELS],
    }


def generate_group(helper, gid, items, terms, api_key, base_url, model):
    messages = make_prompt(gid, items, terms)
    last_error = ""
    for attempt in range(1, 4):
        try:
            response = helper.post_chat(messages, api_key, base_url, model, timeout=140)
            payload = parse_payload(helper, response["choices"][0]["message"]["content"])
            return payload, {"hardpair_group_id": gid, "status": "success", "attempt": attempt, "response": response}, "success", ""
        except Exception as exc:
            last_error = str(exc)
            time.sleep(min(18, 2 ** attempt))
    # fallback: keep original group if repair fails
    payload = {
        "repair_strategy": "fallback_keep_v3_claims",
        "locked_evidence_unchanged": True,
        "variants": [
            {"label": r["candidate_label_guess"], "claim_text": r["claim_text"], "relation_note": "fallback kept v3", "leakage_terms_removed": ""}
            for r in items
        ],
    }
    return payload, {"hardpair_group_id": gid, "status": "fallback_after_llm_error", "error": last_error[:1000]}, "fallback_after_llm_error", last_error[:500]


AUDIT_FIELDS = [
    "hardpair_group_id",
    "repair_status",
    "repair_strategy",
    "supported_claim",
    "mild_scope_overclaim_claim",
    "strong_action_overclaim_claim",
    "contradiction_candidate_claim",
    "error",
]


def load_existing_repairs():
    if not GEN_AUDIT.exists():
        return {}
    out = {}
    for row in read_csv(GEN_AUDIT):
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
            variants.append({"label": label, "claim_text": claim, "relation_note": "", "leakage_terms_removed": ""})
        if ok:
            out[gid] = {"repair_strategy": row.get("repair_strategy", ""), "repair_status": row.get("repair_status", ""), "variants": variants}
    return out


def run_repairs(groups, flagged, terms, api_key, base_url, model, max_workers):
    helper = load_helper()
    repairs = load_existing_repairs()
    todo = [gid for gid in flagged if gid not in repairs]
    print(f"targeted_existing_repairs={len(repairs)} targeted_todo_groups={len(todo)}", flush=True)
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(generate_group, helper, gid, groups[gid], terms[gid], api_key, base_url, model): gid for gid in todo}
        done = 0
        for fut in as_completed(futures):
            gid = futures[fut]
            payload, raw, status, error = fut.result()
            append_jsonl(RAW_JSONL, raw)
            row = {"hardpair_group_id": gid, "repair_status": status, "repair_strategy": payload["repair_strategy"], "error": error}
            for v in payload["variants"]:
                row[f"{v['label']}_claim"] = v["claim_text"]
            append_csv(GEN_AUDIT, row, AUDIT_FIELDS)
            payload["repair_status"] = status
            repairs[gid] = payload
            done += 1
            print(f"targeted_progress={done}/{len(todo)}", flush=True)
    return load_existing_repairs()


def binary_labels(label):
    return {
        "issue_binary_label_guess": "0" if label == "supported" else "1",
        "escalation_binary_label_guess": "1" if label in {"mild_scope_overclaim", "strong_action_overclaim"} else "0",
        "contradiction_binary_label_guess": "1" if label == "contradiction_candidate" else "0",
    }


def build_dataset(source_rows, repairs, flagged, model):
    created = utc_now()
    out = []
    for row in source_rows:
        gid = row["hardpair_group_id"]
        label = row["candidate_label_guess"]
        new = dict(row)
        if gid in flagged and gid in repairs:
            variant = next(v for v in repairs[gid]["variants"] if v["label"] == label)
            new["claim_text_before_targeted_repair"] = row["claim_text"]
            new["claim_text"] = variant["claim_text"]
            new["claim_text_detemplated"] = variant["claim_text"]
            new["targeted_repair_applied"] = "true"
            new["targeted_repair_status"] = repairs[gid].get("repair_status", "")
            new["targeted_repair_strategy"] = repairs[gid].get("repair_strategy", "")
        else:
            new["claim_text_before_targeted_repair"] = row["claim_text"]
            new["targeted_repair_applied"] = "false"
            new["targeted_repair_status"] = "not_flagged"
            new["targeted_repair_strategy"] = ""
        new["dataset_line"] = "simclaim_hardpair_v3_targeted_268"
        new["dataset_status"] = "targeted_repair_candidate_set_not_gold"
        new["source_dataset"] = "simclaim_hardpair_v3_268"
        new["source_file"] = str(SOURCE_CSV)
        new["targeted_repair_model"] = model if new["targeted_repair_applied"] == "true" else ""
        evidence_locked = new.get("evidence_text_original_locked") or new.get("evidence_text_original") or new.get("evidence_text") or ""
        new["evidence_text_original_locked"] = evidence_locked
        new["evidence_text_locked_sha256"] = sha256_text(evidence_locked)
        new["evidence_lock_status"] = "locked_from_source_excerpt_not_modified"
        new.update(binary_labels(label))
        new["human_audited"] = "false"
        new["final_label"] = "false"
        new["gold_label"] = "false"
        new["paper_valid"] = "false"
        new["paper_use_allowed"] = "false"
        new["main_text_allowed"] = "false"
        new["needs_human_review"] = "true"
        new["processing_version"] = "simclaim_hardpair_v3_targeted_268_derived_2026-07-01"
        new["created_at_utc"] = created
        out.append(new)
    return out


def split_membership():
    mem = {}
    for split in ["train", "dev", "test"]:
        for r in read_csv(SOURCE_SPLITS / f"{split}.csv"):
            mem[r["candidate_id"]] = split
    return mem


def write_splits(rows, fields):
    mem = split_membership()
    counts = {}
    for split in ["train", "dev", "test"]:
        part = [r for r in rows if mem.get(r["candidate_id"]) == split]
        counts[split] = len(part)
        write_csv(OUT_SPLITS / f"{split}.csv", part, fields)
        write_jsonl(OUT_SPLITS / f"{split}.jsonl", part)
    write_csv(OUT_SPLITS / "all.csv", rows, fields)
    write_jsonl(OUT_SPLITS / "all.jsonl", rows)
    return counts


def prefix_key(text, n):
    clean = normalize(re.sub(r"[^\w\s:-]", " ", (text or "").lower()))
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


def prefix_diag():
    by_split = {s: read_csv(OUT_SPLITS / f"{s}.csv") for s in ["train", "dev", "test"]}
    rows = []
    for target in TARGETS:
        for n in [1, 4, 6]:
            default = Counter(r[target] for r in by_split["train"]).most_common(1)[0][0]
            maps = defaultdict(Counter)
            for r in by_split["train"]:
                maps[prefix_key(r["claim_text"], n)][r[target]] += 1
            mapping = {k: c.most_common(1)[0][0] for k, c in maps.items()}
            for split in ["dev", "test"]:
                part = by_split[split]
                y_true = [r[target] for r in part]
                y_pred = [mapping.get(prefix_key(r["claim_text"], n), default) for r in part]
                acc = sum(1 for a, b in zip(y_true, y_pred) if a == b) / len(y_true) if y_true else 0
                rows.append({"target": target, "prefix_mode": f"first{n}", "eval_split": split, "accuracy": f"{acc:.6f}", "macro_f1": f"{macro_f1(y_true, y_pred):.6f}"})
    write_csv(PREFIX_DIAG, rows)
    return rows


def quality(rows, split_counts, prefix_rows, flagged):
    dup = Counter(normalize(r["claim_text"]).lower() for r in rows)
    q = []
    for r in rows:
        locked = r.get("evidence_text_original_locked", "")
        current = r.get("evidence_text_original") or r.get("evidence_text") or ""
        q.append({
            "candidate_id": r["candidate_id"],
            "hardpair_group_id": r["hardpair_group_id"],
            "candidate_label_guess": r["candidate_label_guess"],
            "targeted_repair_applied": r["targeted_repair_applied"],
            "duplicate_claim_count": dup[normalize(r["claim_text"]).lower()],
            "evidence_locked_unchanged": str(locked == current and sha256_text(locked) == r.get("evidence_text_locked_sha256")).lower(),
            "source_trace_complete": str(bool(r.get("claim_source_url") and r.get("evidence_source_url") and r.get("source_location"))).lower(),
            "claim_text": r["claim_text"],
        })
    write_csv(QUALITY_AUDIT, q)
    split_rows = []
    for split in ["train", "dev", "test"]:
        part = read_csv(OUT_SPLITS / f"{split}.csv")
        for target in TARGETS:
            for label, count in sorted(Counter(r[target] for r in part).items()):
                split_rows.append({"split": split, "target": target, "label": label, "count": count})
    write_csv(SPLIT_AUDIT, split_rows)
    n = len(rows)
    summary = {
        "dataset": "simclaim_hardpair_v3_targeted_268",
        "source_dataset": str(SOURCE_CSV),
        "n_rows": n,
        "n_flagged_groups_repaired": len(flagged),
        "split_counts": split_counts,
        "label_counts": dict(Counter(r["candidate_label_guess"] for r in rows)),
        "repair_status_counts": dict(Counter(r.get("targeted_repair_status", "") for r in rows)),
        "evidence_locked_unchanged_rate": round(sum(1 for x in q if x["evidence_locked_unchanged"] == "true") / n, 6),
        "source_trace_complete_rate": round(sum(1 for x in q if x["source_trace_complete"] == "true") / n, 6),
        "duplicate_claim_rows": sum(1 for x in q if int(x["duplicate_claim_count"]) > 1),
        "worst_test_prefix_macro_f1": max([float(r["macro_f1"]) for r in prefix_rows if r["eval_split"] == "test"], default=0),
        "outputs": {"candidates_csv": str(OUT_CSV), "quality_audit_csv": str(QUALITY_AUDIT), "prefix_diagnostic_csv": str(PREFIX_DIAG), "report_md": str(REPORT_MD)},
    }
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text("# v3 targeted repair report\n\n" + json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-workers", type=int, default=3)
    args = parser.parse_args()
    for p in [OUT_CSV.parent, OUT_SPLITS, OUT_AUDIT, OUT_RAW, REPORT_ROOT]:
        p.mkdir(parents=True, exist_ok=True)
    api_key = os.environ.get("LLM_API_KEY", "").strip()
    base_url = os.environ.get("LLM_BASE_URL", "https://api.holysheep.ai/v1/chat/completions").strip()
    model = os.environ.get("LLM_MODEL", "gpt-5.5").strip()
    if not api_key:
        raise SystemExit("LLM_API_KEY required")
    source_rows = read_csv(SOURCE_CSV)
    groups = group_rows(source_rows)
    flagged = flagged_groups()
    terms = risky_terms_by_group()
    repairs = run_repairs(groups, flagged, terms, api_key, base_url, model, args.max_workers)
    out_rows = build_dataset(source_rows, repairs, set(flagged), model)
    fields = infer_fields(out_rows)
    write_csv(OUT_CSV, out_rows, fields)
    write_jsonl(OUT_JSONL, out_rows)
    split_counts = write_splits(out_rows, fields)
    prefix_rows = prefix_diag()
    summary = quality(out_rows, split_counts, prefix_rows, set(flagged))
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
