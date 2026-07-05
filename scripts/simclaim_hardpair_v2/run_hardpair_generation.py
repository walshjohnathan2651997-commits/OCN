import argparse
import csv
import datetime as dt
import json
import os
import random
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


ROOT = Path(r"D:\ocn")
SOURCE_CSV = ROOT / "data" / "simclaim_detemplate_v1_150" / "candidates" / "simclaim_detemplate_candidates_150.csv"
OUT_ROOT = ROOT / "data" / "simclaim_hardpair_v2"
OUT_CAND = OUT_ROOT / "candidates" / "simclaim_hardpair_v2_268.csv"
OUT_JSONL = OUT_ROOT / "candidates" / "simclaim_hardpair_v2_268.jsonl"
OUT_SPLITS = OUT_ROOT / "splits_group_stratified"
OUT_AUDIT = OUT_ROOT / "audit"
OUT_RAW = OUT_ROOT / "raw_llm"
REPORT_ROOT = ROOT / "reports" / "simclaim_hardpair_v2"

RAW_JSONL = OUT_RAW / "hardpair_generation_raw_outputs.jsonl"
GROUP_AUDIT = OUT_AUDIT / "hardpair_generation_audit.csv"
QUALITY_AUDIT = OUT_AUDIT / "hardpair_quality_audit.csv"
SPLIT_AUDIT = OUT_AUDIT / "hardpair_split_distribution_audit.csv"
PREFIX_DIAG = REPORT_ROOT / "hardpair_prefix_leakage_diagnostic.csv"
SUMMARY_JSON = REPORT_ROOT / "hardpair_v2_summary.json"
REPORT_MD = REPORT_ROOT / "hardpair_v2_report.md"


LABELS = [
    "supported",
    "mild_scope_overclaim",
    "strong_action_overclaim",
    "contradiction_candidate",
]

BANNED_CUES = [
    "the passage reports",
    "the paper reports",
    "a bounded reading",
    "bounded rewrite",
    "the claim suggests",
    "the claim moves",
    "supported claim",
    "overclaim",
    "unsupported",
    "contradiction",
    "contradicts",
    "opposite",
    "deployment-ready",
    "ready for deployment",
    "policy action",
    "broader settings",
    "generalized beyond",
]

TARGETS = [
    "issue_binary_label_guess",
    "escalation_binary_label_guess",
    "contradiction_binary_label_guess",
    "candidate_label_guess",
]


def utc_now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_dirs():
    for p in [OUT_CAND.parent, OUT_SPLITS, OUT_AUDIT, OUT_RAW, REPORT_ROOT]:
        p.mkdir(parents=True, exist_ok=True)


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fieldnames=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = infer_fieldnames(rows)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


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


def infer_fieldnames(rows):
    out = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                out.append(key)
                seen.add(key)
    return out


def normalize_space(text):
    return re.sub(r"\s+", " ", (text or "")).strip()


def word_count(text):
    return len(re.findall(r"\b[\w-]+\b", text or ""))


def banned_hits(text):
    lower = (text or "").lower()
    return [cue for cue in BANNED_CUES if cue in lower]


def truncate(text, n):
    text = normalize_space(text)
    return text[:n]


def group_source_rows(rows):
    groups = defaultdict(list)
    for row in rows:
        gid = row.get("split_group_id") or row.get("source_pair_id") or row.get("candidate_id")
        groups[gid].append(row)
    grouped = []
    for gid, items in sorted(groups.items()):
        supported = [r for r in items if r.get("candidate_label_guess") == "supported" or r.get("variant_type") == "supported"]
        base = supported[0] if supported else items[0]
        grouped.append((gid, base, items))
    return grouped


def make_prompt(gid, base, items):
    existing_examples = []
    for row in items[:6]:
        existing_examples.append({
            "label": row.get("candidate_label_guess") or row.get("variant_type"),
            "claim": normalize_space(row.get("claim_text", ""))[:400],
        })
    evidence = truncate(base.get("evidence_text") or base.get("evidence_text_original") or "", 1800)
    finding = truncate(base.get("evidence_base_finding") or "", 700)
    title = base.get("paper_title", "")
    domain = base.get("domain", "")
    return [
        {
            "role": "system",
            "content": (
                "You create controlled scientific claim-evidence hard pairs for a dataset. "
                "Return strict JSON only. Preserve the source evidence; generate only new claims."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Group id: {gid}\n"
                f"Paper/domain: {title} / {domain}\n\n"
                f"Evidence base finding:\n{finding}\n\n"
                f"Evidence passage:\n{evidence}\n\n"
                f"Existing rough examples, for intent only; do not copy wording:\n{json.dumps(existing_examples, ensure_ascii=False)}\n\n"
                "Generate exactly four claims for the same evidence, one for each label:\n"
                "1. supported: directly entailed by the evidence.\n"
                "2. mild_scope_overclaim: slightly broadens the supported finding or certainty.\n"
                "3. strong_action_overclaim: implies practical use, operational suitability, decision support, or safety/action consequence beyond the evidence.\n"
                "4. contradiction_candidate: conflicts with one material fact in the evidence.\n\n"
                "Hard-pair constraints:\n"
                "- Make the four claims similar in length, tone, and sentence shape so label cannot be guessed from style alone.\n"
                "- Each claim should be 20-38 words when possible.\n"
                "- Avoid label-like cues or stock phrases: supported, overclaim, unsupported, contradiction, opposite, broader settings, deployment-ready, policy action, the passage reports.\n"
                "- Do not use the exact same opening phrase across all four claims.\n"
                "- Do not invent paper titles, citations, datasets, or numerical results not suggested by the evidence.\n"
                "- Claims should sound like natural scientific summary statements, not annotation instructions.\n\n"
                "Return JSON with keys:\n"
                "{\n"
                "  \"shared_style_plan\": \"...\",\n"
                "  \"variants\": [\n"
                "    {\"label\": \"supported\", \"claim_text\": \"...\", \"semantic_delta\": \"...\", \"style_risk\": \"low|medium|high\"},\n"
                "    ... exactly four objects ...\n"
                "  ]\n"
                "}\n"
                "JSON only, no markdown."
            ),
        },
    ]


def extract_json(text):
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def post_chat(messages, api_key, base_url, model, timeout=120):
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.35,
        "max_tokens": 950,
        "response_format": {"type": "json_object"},
    }
    return _post(payload, api_key, base_url, timeout)


def _post(payload, api_key, base_url, timeout):
    req = urllib.request.Request(
        base_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        if e.code in (400, 422) and "response_format" in body and "response_format" in payload:
            payload2 = dict(payload)
            payload2.pop("response_format", None)
            return _post(payload2, api_key, base_url, timeout)
        raise RuntimeError(f"HTTP {e.code}: {body[:500]}")


def fallback_variants(base):
    finding = normalize_space(base.get("evidence_base_finding") or base.get("claim_text") or "")
    if not finding:
        finding = "The evidence describes a specific experimental or system property."
    finding = finding.rstrip(".")
    return {
        "shared_style_plan": "local fallback with matched single-sentence scientific claims",
        "variants": [
            {
                "label": "supported",
                "claim_text": f"{finding}.",
                "semantic_delta": "directly follows evidence",
                "style_risk": "medium",
            },
            {
                "label": "mild_scope_overclaim",
                "claim_text": f"{finding} in comparable settings beyond the reported case.",
                "semantic_delta": "slightly broadens scope",
                "style_risk": "medium",
            },
            {
                "label": "strong_action_overclaim",
                "claim_text": f"{finding}, making the approach suitable for practical decision-making without further validation.",
                "semantic_delta": "adds practical/action consequence",
                "style_risk": "medium",
            },
            {
                "label": "contradiction_candidate",
                "claim_text": f"The reported evidence does not show that {finding[0].lower() + finding[1:] if len(finding) > 1 else finding}.",
                "semantic_delta": "negates material finding",
                "style_risk": "medium",
            },
        ],
    }


def validate_payload(payload):
    variants = payload.get("variants", [])
    if not isinstance(variants, list):
        raise ValueError("variants is not a list")
    by_label = {}
    for item in variants:
        label = normalize_space(str(item.get("label", "")))
        claim = normalize_space(str(item.get("claim_text", "")))
        if label in LABELS and claim:
            by_label[label] = {
                "label": label,
                "claim_text": claim,
                "semantic_delta": normalize_space(str(item.get("semantic_delta", ""))),
                "style_risk": normalize_space(str(item.get("style_risk", ""))).lower() or "unknown",
            }
    missing = [label for label in LABELS if label not in by_label]
    if missing:
        raise ValueError(f"missing labels: {missing}")
    return {
        "shared_style_plan": normalize_space(str(payload.get("shared_style_plan", ""))),
        "variants": [by_label[label] for label in LABELS],
    }


def generate_group(gid, base, items, api_key, base_url, model):
    messages = make_prompt(gid, base, items)
    last_error = ""
    for attempt in range(1, 4):
        try:
            response = post_chat(messages, api_key, base_url, model)
            content = response["choices"][0]["message"]["content"]
            payload = validate_payload(extract_json(content))
            raw = {
                "hardpair_group_id": gid,
                "status": "success",
                "attempt": attempt,
                "model": model,
                "response": response,
            }
            return payload, raw, "success", ""
        except Exception as exc:
            last_error = str(exc)
            time.sleep(min(20, 2 ** attempt + random.random()))
    payload = validate_payload(fallback_variants(base))
    raw = {
        "hardpair_group_id": gid,
        "status": "fallback_after_llm_error",
        "model": model,
        "error": last_error[:1000],
    }
    return payload, raw, "fallback_after_llm_error", last_error[:500]


GROUP_AUDIT_FIELDS = [
    "hardpair_group_id",
    "generation_status",
    "source_v1_candidate_id",
    "shared_style_plan",
    "supported_claim",
    "mild_scope_overclaim_claim",
    "strong_action_overclaim_claim",
    "contradiction_candidate_claim",
    "error",
]


def load_existing_groups():
    if not GROUP_AUDIT.exists():
        return {}
    out = {}
    for row in read_csv(GROUP_AUDIT):
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
                "semantic_delta": "",
                "style_risk": "",
            })
        if ok:
            out[gid] = {
                "shared_style_plan": row.get("shared_style_plan", ""),
                "variants": variants,
                "generation_status": row.get("generation_status", ""),
            }
    return out


def run_generation(grouped, api_key, base_url, model, max_workers):
    existing = load_existing_groups()
    todo = [(gid, base, items) for gid, base, items in grouped if gid not in existing]
    print(f"hardpair_existing_groups={len(existing)} hardpair_todo_groups={len(todo)}", flush=True)
    raw_lock = threading.Lock()
    audit_lock = threading.Lock()
    completed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {
            ex.submit(generate_group, gid, base, items, api_key, base_url, model): (gid, base, items)
            for gid, base, items in todo
        }
        for fut in as_completed(futs):
            gid, base, _items = futs[fut]
            payload, raw, status, error = fut.result()
            append_jsonl(RAW_JSONL, raw, raw_lock)
            audit_row = {
                "hardpair_group_id": gid,
                "generation_status": status,
                "source_v1_candidate_id": base.get("candidate_id", ""),
                "shared_style_plan": payload.get("shared_style_plan", ""),
                "error": error,
            }
            for variant in payload["variants"]:
                audit_row[f"{variant['label']}_claim"] = variant["claim_text"]
            append_csv(GROUP_AUDIT, audit_row, GROUP_AUDIT_FIELDS, audit_lock)
            payload["generation_status"] = status
            existing[gid] = payload
            completed += 1
            if completed % 10 == 0 or completed == len(todo):
                print(f"hardpair_progress={completed}/{len(todo)}", flush=True)
    return load_existing_groups()


def binary_labels(label):
    return {
        "issue_binary_label_guess": "0" if label == "supported" else "1",
        "escalation_binary_label_guess": "1" if label in {"mild_scope_overclaim", "strong_action_overclaim"} else "0",
        "contradiction_binary_label_guess": "1" if label == "contradiction_candidate" else "0",
    }


def build_rows(grouped, payloads, model):
    created = utc_now()
    out = []
    for group_index, (gid, base, _items) in enumerate(grouped, start=1):
        payload = payloads[gid]
        for variant_index, variant in enumerate(payload["variants"], start=1):
            label = variant["label"]
            row = dict(base)
            row["candidate_id"] = f"HP2-{group_index:03d}-{variant_index}"
            row["expand_id"] = row["candidate_id"]
            row["hardpair_group_id"] = f"HP2-G{group_index:03d}"
            row["hardpair_source_group_id"] = gid
            row["hardpair_variant_index"] = variant_index
            row["source_v1_candidate_id"] = base.get("candidate_id", "")
            row["source_v1_claim_text"] = base.get("claim_text", "")
            row["dataset_line"] = "simclaim_hardpair_v2_268"
            row["dataset_status"] = "ai_generated_hardpair_candidate_set_not_gold"
            row["source_dataset"] = "simclaim_detemplate_v1_150"
            row["source_file"] = str(SOURCE_CSV)
            row["sample_id_original"] = f"{gid}_{label}"
            row["variant_type"] = label
            row["candidate_label_guess"] = label
            row.update(binary_labels(label))
            row["claim_text_original_template"] = base.get("claim_text_original_template") or base.get("source_v1_claim_text", "")
            row["claim_text_detemplated"] = variant["claim_text"]
            row["claim_text"] = variant["claim_text"]
            row["claim_text_original"] = variant["claim_text"]
            row["label_guess_source"] = "llm_hardpair_generation_v2; not_gold"
            row["label_derivation_rule"] = "hardpair controlled generation: one claim per label per evidence group"
            row["label_rederived"] = "True"
            row["annotation_status"] = "ai_preannotated_hardpair_candidate"
            row["annotation_policy"] = "single_ai_preannotation_only_no_two_annotator_flow"
            row["human_audited"] = "false"
            row["final_label"] = "false"
            row["gold_label"] = "false"
            row["paper_valid"] = "false"
            row["paper_use_allowed"] = "false"
            row["main_text_allowed"] = "false"
            row["needs_human_review"] = "true"
            row["mvp_recommended_use"] = "paper_scaffold_and_pipeline_validation_only_not_gold_hardpair_v2"
            row["hardpair_generation_model"] = model
            row["hardpair_generation_status"] = payload.get("generation_status", "")
            row["hardpair_shared_style_plan"] = payload.get("shared_style_plan", "")
            row["hardpair_semantic_delta"] = variant.get("semantic_delta", "")
            row["hardpair_style_risk"] = variant.get("style_risk", "")
            row["processing_version"] = "simclaim_hardpair_v2_268_derived_2026-07-01"
            row["created_at_utc"] = created
            out.append(row)
    return out


def split_groups(grouped):
    # 67 groups -> 40/13/14 groups, whole source groups only.
    gids = [gid for gid, _base, _items in grouped]
    membership = {}
    for idx, gid in enumerate(gids):
        if idx < 40:
            split = "train"
        elif idx < 53:
            split = "dev"
        else:
            split = "test"
        membership[gid] = split
    return membership


def write_splits(rows, grouped, fieldnames):
    group_split = split_groups(grouped)
    counts = {}
    for split in ["train", "dev", "test"]:
        split_rows = [r for r in rows if group_split.get(r.get("hardpair_source_group_id")) == split]
        counts[split] = len(split_rows)
        write_csv(OUT_SPLITS / f"{split}.csv", split_rows, fieldnames)
        write_jsonl(OUT_SPLITS / f"{split}.jsonl", split_rows)
    write_csv(OUT_SPLITS / "all.csv", rows, fieldnames)
    write_jsonl(OUT_SPLITS / "all.jsonl", rows)
    return counts, group_split


def prefix_key(text, mode):
    clean = normalize_space(re.sub(r"[^\w\s:-]", " ", (text or "").lower()))
    words = clean.split()
    n = int(mode.replace("first", ""))
    return " ".join(words[:n])


def macro_f1(y_true, y_pred):
    labels = sorted(set(y_true) | set(y_pred))
    vals = []
    for label in labels:
        tp = sum(1 for a, b in zip(y_true, y_pred) if a == label and b == label)
        fp = sum(1 for a, b in zip(y_true, y_pred) if a != label and b == label)
        fn = sum(1 for a, b in zip(y_true, y_pred) if a == label and b != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        vals.append((2 * precision * recall / (precision + recall)) if precision + recall else 0.0)
    return sum(vals) / len(vals) if vals else 0.0


def accuracy(y_true, y_pred):
    return sum(1 for a, b in zip(y_true, y_pred) if a == b) / len(y_true) if y_true else 0.0


def prefix_diagnostic(rows, group_split):
    by_split = {"train": [], "dev": [], "test": []}
    for row in rows:
        split = group_split.get(row.get("hardpair_source_group_id"))
        if split in by_split:
            by_split[split].append(row)
    out = []
    for target in TARGETS:
        for mode in ["first1", "first4", "first6"]:
            mapping = defaultdict(Counter)
            default = Counter(r.get(target, "") for r in by_split["train"]).most_common(1)[0][0]
            for row in by_split["train"]:
                mapping[prefix_key(row.get("claim_text", ""), mode)][row.get(target, "")] += 1
            key_to_label = {k: c.most_common(1)[0][0] for k, c in mapping.items()}
            for split in ["dev", "test"]:
                eval_rows = by_split[split]
                y_true = [r.get(target, "") for r in eval_rows]
                y_pred = [key_to_label.get(prefix_key(r.get("claim_text", ""), mode), default) for r in eval_rows]
                keys = [prefix_key(r.get("claim_text", ""), mode) for r in eval_rows]
                out.append({
                    "dataset": "simclaim_hardpair_v2_268",
                    "target": target,
                    "prefix_mode": mode,
                    "eval_split": split,
                    "n_train": len(by_split["train"]),
                    "n_eval": len(eval_rows),
                    "accuracy": f"{accuracy(y_true, y_pred):.6f}",
                    "macro_f1": f"{macro_f1(y_true, y_pred):.6f}",
                    "n_unique_eval_prefixes": len(set(keys)),
                    "top_eval_prefix_share": f"{Counter(keys).most_common(1)[0][1] / len(keys):.6f}" if keys else "0.000000",
                })
    write_csv(PREFIX_DIAG, out)
    return out


def audits(rows, group_split, split_counts, prefix_rows):
    quality = []
    seen_claims = Counter(normalize_space(r.get("claim_text", "")).lower() for r in rows)
    group_len = defaultdict(list)
    for r in rows:
        group_len[r.get("hardpair_group_id")].append(word_count(r.get("claim_text", "")))
    for row in rows:
        claim = row.get("claim_text", "")
        hits = banned_hits(claim)
        lens = group_len[row.get("hardpair_group_id")]
        quality.append({
            "candidate_id": row.get("candidate_id", ""),
            "hardpair_group_id": row.get("hardpair_group_id", ""),
            "hardpair_source_group_id": row.get("hardpair_source_group_id", ""),
            "candidate_label_guess": row.get("candidate_label_guess", ""),
            "word_count": word_count(claim),
            "group_word_count_min": min(lens),
            "group_word_count_max": max(lens),
            "group_word_count_spread": max(lens) - min(lens),
            "banned_cue_hit_count": len(hits),
            "banned_cue_hits": "; ".join(hits),
            "duplicate_claim_count": seen_claims[normalize_space(claim).lower()],
            "prefix_first1": prefix_key(claim, "first1"),
            "prefix_first4": prefix_key(claim, "first4"),
            "hardpair_style_risk": row.get("hardpair_style_risk", ""),
            "source_trace_complete": str(bool(row.get("claim_source_url") and row.get("evidence_source_url") and row.get("source_location"))).lower(),
            "claim_text": claim,
        })
    write_csv(QUALITY_AUDIT, quality)

    split_audit = []
    for split in ["train", "dev", "test"]:
        split_rows = [r for r in rows if group_split.get(r.get("hardpair_source_group_id")) == split]
        for target in TARGETS:
            for label, count in sorted(Counter(r.get(target, "") for r in split_rows).items()):
                split_audit.append({
                    "split": split,
                    "target": target,
                    "label": label,
                    "count": count,
                })
    write_csv(SPLIT_AUDIT, split_audit)

    n = len(rows)
    source_trace_ok = sum(1 for q in quality if q["source_trace_complete"] == "true")
    summary = {
        "dataset": "simclaim_hardpair_v2_268",
        "source_dataset": str(SOURCE_CSV),
        "n_rows": n,
        "n_groups": len(set(r.get("hardpair_source_group_id") for r in rows)),
        "split_counts": split_counts,
        "label_counts": dict(Counter(r.get("candidate_label_guess", "") for r in rows)),
        "issue_binary_counts": dict(Counter(r.get("issue_binary_label_guess", "") for r in rows)),
        "escalation_binary_counts": dict(Counter(r.get("escalation_binary_label_guess", "") for r in rows)),
        "contradiction_binary_counts": dict(Counter(r.get("contradiction_binary_label_guess", "") for r in rows)),
        "generation_status_counts": dict(Counter(r.get("hardpair_generation_status", "") for r in rows)),
        "banned_cue_rows": sum(1 for q in quality if int(q["banned_cue_hit_count"]) > 0),
        "duplicate_claim_rows": sum(1 for q in quality if int(q["duplicate_claim_count"]) > 1),
        "mean_group_word_count_spread": round(sum(int(q["group_word_count_spread"]) for q in quality) / len(quality), 3) if quality else 0,
        "source_trace_complete_rate": round(source_trace_ok / n, 6) if n else 0,
        "worst_test_prefix_macro_f1": max(
            [float(r["macro_f1"]) for r in prefix_rows if r["eval_split"] == "test" and r["prefix_mode"] in {"first4", "first6"}],
            default=0.0,
        ),
        "outputs": {
            "candidates_csv": str(OUT_CAND),
            "splits_dir": str(OUT_SPLITS),
            "quality_audit_csv": str(QUALITY_AUDIT),
            "split_audit_csv": str(SPLIT_AUDIT),
            "prefix_diagnostic_csv": str(PREFIX_DIAG),
            "report_md": str(REPORT_MD),
        },
        "recommended_next_step": "Run traditional and LLM small eval. If claim-only is still close to claim+evidence, perform another style-neutralization pass.",
        "created_at_utc": utc_now(),
    }
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(summary, prefix_rows)
    return summary


def write_report(summary, prefix_rows):
    lines = []
    lines.append("# SimClaim hard-pair v2 report")
    lines.append("")
    lines.append("Hard-pair v2 generates four label variants for each evidence group, with matched claim style, length, and tone.")
    lines.append("")
    lines.append("## Status")
    lines.append("")
    lines.append(f"- Rows: {summary['n_rows']}")
    lines.append(f"- Groups: {summary['n_groups']}")
    lines.append(f"- Split counts: {summary['split_counts']}")
    lines.append(f"- Label counts: {summary['label_counts']}")
    lines.append(f"- Banned cue rows: {summary['banned_cue_rows']}")
    lines.append(f"- Duplicate claim rows: {summary['duplicate_claim_rows']}")
    lines.append(f"- Source trace complete rate: {summary['source_trace_complete_rate']}")
    lines.append(f"- Worst test prefix macro-F1: {summary['worst_test_prefix_macro_f1']}")
    lines.append("")
    lines.append("## Prefix diagnostic")
    lines.append("")
    lines.append("| target | prefix | split | acc | macro-F1 | unique prefixes |")
    lines.append("|---|---:|---|---:|---:|---:|")
    for row in prefix_rows:
        lines.append(f"| {row['target']} | {row['prefix_mode']} | {row['eval_split']} | {row['accuracy']} | {row['macro_f1']} | {row['n_unique_eval_prefixes']} |")
    lines.append("")
    lines.append("## Files")
    lines.append("")
    for key, value in summary["outputs"].items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    lines.append("## Recommended next step")
    lines.append("")
    lines.append(summary["recommended_next_step"])
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-workers", type=int, default=6)
    parser.add_argument("--skip-llm", action="store_true")
    args = parser.parse_args()

    ensure_dirs()
    source_rows = read_csv(SOURCE_CSV)
    grouped = group_source_rows(source_rows)
    api_key = os.environ.get("LLM_API_KEY", "").strip()
    base_url = os.environ.get("LLM_BASE_URL", "https://api.holysheep.ai/v1/chat/completions").strip()
    model = os.environ.get("LLM_MODEL", "gpt-5.5").strip()
    if args.skip_llm:
        payloads = {}
        for gid, base, _items in grouped:
            payload = validate_payload(fallback_variants(base))
            payload["generation_status"] = "local_fallback_skip_llm"
            payloads[gid] = payload
    else:
        if not api_key:
            raise SystemExit("LLM_API_KEY is required unless --skip-llm is used.")
        payloads = run_generation(grouped, api_key, base_url, model, args.max_workers)

    out_rows = build_rows(grouped, payloads, model)
    fieldnames = infer_fieldnames(out_rows)
    write_csv(OUT_CAND, out_rows, fieldnames)
    write_jsonl(OUT_JSONL, out_rows)
    split_counts, group_split = write_splits(out_rows, grouped, fieldnames)
    prefix_rows = prefix_diagnostic(out_rows, group_split)
    summary = audits(out_rows, group_split, split_counts, prefix_rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
