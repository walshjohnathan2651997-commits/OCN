import argparse
import csv
import datetime as dt
import json
import math
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
SOURCE_ALL = ROOT / "data" / "simclaim_mvp_expansion_v1_150" / "candidates" / "simclaim_mvp_expansion_candidates_150.csv"
SOURCE_SPLITS = ROOT / "data" / "simclaim_mvp_expansion_v1_150" / "splits"
OUT_ROOT = ROOT / "data" / "simclaim_detemplate_v1_150"
OUT_CANDIDATES = OUT_ROOT / "candidates" / "simclaim_detemplate_candidates_150.csv"
OUT_CANDIDATES_JSONL = OUT_ROOT / "candidates" / "simclaim_detemplate_candidates_150.jsonl"
OUT_SPLITS = OUT_ROOT / "splits"
OUT_AUDIT = OUT_ROOT / "audit"
OUT_RAW = OUT_ROOT / "raw_llm"
REPORT_ROOT = ROOT / "reports" / "simclaim_detemplate_v1_150"

RAW_JSONL = OUT_RAW / "detemplate_raw_outputs.jsonl"
REWRITE_AUDIT = OUT_AUDIT / "detemplate_rewrite_audit.csv"
QUALITY_AUDIT = OUT_AUDIT / "detemplate_quality_audit.csv"
PREFIX_DIAG = REPORT_ROOT / "prefix_leakage_after_detemplate.csv"
SUMMARY_JSON = REPORT_ROOT / "detemplate_summary.json"
REPORT_MD = REPORT_ROOT / "detemplate_report.md"


BANNED_CUES = [
    "the passage reports",
    "the paper reports",
    "a bounded reading",
    "bounded rewrite",
    "the study demonstrates",
    "this result can be generalized",
    "broader settings",
    "the claim suggests",
    "the claim moves",
    "opposite",
    "contradiction",
    "contradicts",
    "deployment-ready",
    "can be directly deployed",
    "ready for deployment",
    "policy action",
    "safety-certified",
]


TARGETS = [
    "escalation_binary_label_guess",
    "issue_binary_label_guess",
    "contradiction_binary_label_guess",
    "candidate_label_guess",
]


def utc_now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_dirs():
    for p in [OUT_ROOT, OUT_CANDIDATES.parent, OUT_SPLITS, OUT_AUDIT, OUT_RAW, REPORT_ROOT]:
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
    path.parent.mkdir(parents=True, exist_ok=True)
    with lock:
        exists = path.exists() and path.stat().st_size > 0
        with path.open("a", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            if not exists:
                writer.writeheader()
            writer.writerow(row)


def append_jsonl(path, obj, lock):
    path.parent.mkdir(parents=True, exist_ok=True)
    with lock:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def infer_fieldnames(rows):
    fields = []
    seen = set()
    for row in rows:
        for k in row.keys():
            if k not in seen:
                fields.append(k)
                seen.add(k)
    return fields


def normalize_space(s):
    return re.sub(r"\s+", " ", (s or "")).strip()


def word_count(s):
    return len(re.findall(r"\b[\w-]+\b", s or ""))


def banned_hits(s):
    lower = (s or "").lower()
    return [cue for cue in BANNED_CUES if cue in lower]


def strip_common_template_prefix(s):
    text = normalize_space(s)
    patterns = [
        r"^The passage reports that\s+",
        r"^The passage reports:\s+",
        r"^The paper reports that\s+",
        r"^The paper reports:\s+",
        r"^A bounded rewrite supported by the passage is:\s+",
        r"^A bounded reading of the evidence is that\s+",
        r"^The study demonstrates that\s+",
    ]
    for pat in patterns:
        text = re.sub(pat, "", text, flags=re.IGNORECASE)
    return normalize_space(text)


def label_instruction(row):
    variant = (row.get("variant_type") or row.get("candidate_label_guess") or "").strip().lower()
    if variant == "supported":
        return (
            "Write a supported claim that is directly entailed by the evidence. "
            "Do not broaden scope, add deployment implications, add policy recommendations, or increase certainty."
        )
    if variant == "mild_scope_overclaim":
        return (
            "Write a natural mild scope overclaim: the claim should make the finding sound more general than the evidence warrants, "
            "but without using obvious labels such as scope overclaim, broader settings, generalized, or unsupported."
        )
    if variant == "strong_action_overclaim":
        return (
            "Write a natural strong action overclaim: the claim should imply practical deployment, operational use, policy action, "
            "or safety decision beyond the evidence, but avoid obvious cue phrases such as deployment-ready or policy action."
        )
    if variant == "contradiction_candidate":
        return (
            "Write a natural claim that conflicts with the evidence. Do not use words such as contradiction, opposite, false, or contradicts."
        )
    return (
        "Rewrite the claim in a natural paper-like style while preserving its intended candidate relation to the evidence."
    )


def make_prompt(row):
    original_claim = normalize_space(row.get("claim_text") or row.get("claim_text_original") or "")
    evidence = normalize_space(row.get("evidence_text") or row.get("evidence_text_original") or "")
    base_finding = normalize_space(row.get("evidence_base_finding") or "")
    variant = row.get("variant_type") or row.get("candidate_label_guess") or ""
    paper_title = row.get("paper_title") or ""
    domain = row.get("domain") or ""
    instruction = label_instruction(row)

    return [
        {
            "role": "system",
            "content": (
                "You rewrite AI-generated scientific claim candidates for a claim-evidence dataset. "
                "Return strict JSON only. Preserve the candidate's label semantics. Do not invent citations, numbers, datasets, or methods."
            ),
        },
        {
            "role": "user",
            "content": (
                "Task: rewrite only the claim into natural scientific prose and remove template cues.\n\n"
                f"Paper/domain: {paper_title} / {domain}\n"
                f"Candidate type: {variant}\n"
                f"Label constraint: {instruction}\n\n"
                f"Original claim:\n{original_claim}\n\n"
                f"Evidence base finding, if available:\n{base_finding}\n\n"
                f"Evidence passage:\n{evidence[:1800]}\n\n"
                "Hard constraints:\n"
                "- Return JSON with keys: detemplated_claim, rewrite_strategy, removed_template_cues, leakage_risk_after_rewrite, semantic_notes.\n"
                "- detemplated_claim should be 18-45 words when possible.\n"
                "- Keep the relation implied by Candidate type; do not turn all items into supported claims.\n"
                "- Avoid these cue/template phrases: The passage reports, The paper reports, A bounded reading, bounded rewrite, "
                "The study demonstrates, this result can be generalized, broader settings, The claim suggests, The claim moves, "
                "opposite, contradiction, contradicts, deployment-ready, can be directly deployed, ready for deployment.\n"
                "- Do not mention the labels supported, mild overclaim, strong overclaim, or contradiction inside the claim.\n"
                "- Do not add a citation placeholder or section reference.\n"
                "- JSON only, no markdown."
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
        pass
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        return json.loads(match.group(0))
    raise ValueError("No JSON object found")


def openai_chat(messages, api_key, base_url, model, timeout=90):
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.25,
        "max_tokens": 350,
        "response_format": {"type": "json_object"},
    }
    return _post_openai(payload, api_key, base_url, timeout=timeout)


def _post_openai(payload, api_key, base_url, timeout=90):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        base_url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        if e.code in (400, 422) and "response_format" in body and "response_format" in payload:
            payload2 = dict(payload)
            payload2.pop("response_format", None)
            return _post_openai(payload2, api_key, base_url, timeout=timeout)
        raise RuntimeError(f"HTTP {e.code}: {body[:500]}")


def fallback_rewrite(row):
    base = strip_common_template_prefix(row.get("claim_text") or row.get("claim_text_original") or "")
    variant = (row.get("variant_type") or "").lower()
    if variant == "strong_action_overclaim" and "use" not in base.lower():
        base = base.rstrip(".") + ", indicating that the approach is suitable for real-world operational use."
    elif variant == "mild_scope_overclaim" and "across" not in base.lower():
        base = base.rstrip(".") + " across similar settings."
    elif variant == "contradiction_candidate":
        base = base.rstrip(".")
    return normalize_space(base)


def rewrite_one(row, api_key, base_url, model, max_attempts=3):
    cid = row.get("candidate_id") or row.get("expand_id") or ""
    messages = make_prompt(row)
    last_error = ""
    for attempt in range(1, max_attempts + 1):
        try:
            response = openai_chat(messages, api_key, base_url, model)
            content = response["choices"][0]["message"]["content"]
            parsed = extract_json(content)
            claim = normalize_space(parsed.get("detemplated_claim") or "")
            if not claim:
                raise ValueError("empty detemplated_claim")
            raw_record = {
                "candidate_id": cid,
                "status": "success",
                "attempt": attempt,
                "model": model,
                "response": response,
            }
            return {
                "candidate_id": cid,
                "detemplate_status": "success",
                "detemplated_claim": claim,
                "rewrite_strategy": normalize_space(str(parsed.get("rewrite_strategy", ""))),
                "removed_template_cues": normalize_space(str(parsed.get("removed_template_cues", ""))),
                "leakage_risk_after_rewrite": normalize_space(str(parsed.get("leakage_risk_after_rewrite", ""))).lower() or "unknown",
                "semantic_notes": normalize_space(str(parsed.get("semantic_notes", ""))),
                "detemplate_error": "",
                "raw_record": raw_record,
            }
        except Exception as exc:
            last_error = str(exc)
            sleep_s = min(20, 2 ** attempt + random.random())
            time.sleep(sleep_s)

    claim = fallback_rewrite(row)
    return {
        "candidate_id": cid,
        "detemplate_status": "fallback_after_llm_error",
        "detemplated_claim": claim,
        "rewrite_strategy": "rule_fallback_template_prefix_removed",
        "removed_template_cues": ",".join(banned_hits(row.get("claim_text") or "")),
        "leakage_risk_after_rewrite": "high" if banned_hits(claim) else "medium",
        "semantic_notes": "LLM rewrite failed; used conservative local fallback.",
        "detemplate_error": last_error[:500],
        "raw_record": {
            "candidate_id": cid,
            "status": "fallback_after_llm_error",
            "model": model,
            "error": last_error[:1000],
        },
    }


REWRITE_FIELDS = [
    "candidate_id",
    "detemplate_status",
    "detemplated_claim",
    "rewrite_strategy",
    "removed_template_cues",
    "leakage_risk_after_rewrite",
    "semantic_notes",
    "detemplate_error",
]


def load_existing_rewrites():
    if not REWRITE_AUDIT.exists():
        return {}
    rows = read_csv(REWRITE_AUDIT)
    out = {}
    for row in rows:
        cid = row.get("candidate_id")
        if cid and row.get("detemplated_claim"):
            out[cid] = row
    return out


def run_rewrites(rows, api_key, base_url, model, max_workers):
    existing = load_existing_rewrites()
    todo = [r for r in rows if (r.get("candidate_id") or r.get("expand_id")) not in existing]
    print(f"rewrite_existing={len(existing)} rewrite_todo={len(todo)}", flush=True)

    if todo:
        raw_lock = threading.Lock()
        audit_lock = threading.Lock()
        completed = 0
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futs = {ex.submit(rewrite_one, row, api_key, base_url, model): row for row in todo}
            for fut in as_completed(futs):
                result = fut.result()
                cid = result["candidate_id"]
                append_jsonl(RAW_JSONL, result.pop("raw_record"), raw_lock)
                append_csv(REWRITE_AUDIT, result, REWRITE_FIELDS, audit_lock)
                existing[cid] = result
                completed += 1
                if completed % 10 == 0 or completed == len(todo):
                    print(f"rewrite_progress={completed}/{len(todo)}", flush=True)

    return load_existing_rewrites()


def split_membership():
    membership = {}
    for split in ["train", "dev", "test"]:
        p = SOURCE_SPLITS / f"{split}.csv"
        if not p.exists():
            continue
        for row in read_csv(p):
            cid = row.get("candidate_id") or row.get("expand_id")
            if cid:
                membership[cid] = split
    return membership


def build_dataset(source_rows, rewrites, model):
    created = utc_now()
    out_rows = []
    for row in source_rows:
        cid = row.get("candidate_id") or row.get("expand_id")
        rr = rewrites.get(cid, {})
        new_claim = normalize_space(rr.get("detemplated_claim") or fallback_rewrite(row))
        out = dict(row)
        out["claim_text_original_template"] = row.get("claim_text", "")
        out["claim_text_detemplated"] = new_claim
        out["claim_text"] = new_claim
        out["dataset_line"] = "simclaim_detemplate_v1_150"
        out["dataset_status"] = "ai_preannotated_trace_repaired_detemplated_candidate_set"
        out["source_dataset"] = "simclaim_mvp_expansion_v1_150"
        out["source_file"] = str(SOURCE_ALL)
        out["annotation_policy"] = "single_ai_preannotation_only_no_two_annotator_flow"
        out["human_audited"] = "false"
        out["final_label"] = "false"
        out["gold_label"] = "false"
        out["paper_valid"] = "false"
        out["paper_use_allowed"] = "false"
        out["main_text_allowed"] = "false"
        out["mvp_recommended_use"] = "paper_scaffold_and_pipeline_validation_only_not_gold_detemplated"
        out["claim_rewritten"] = "True"
        out["needs_human_review"] = "true"
        out["processing_version"] = "simclaim_detemplate_v1_150_derived_2026-07-01"
        out["detemplate_status"] = rr.get("detemplate_status", "fallback_missing_rewrite")
        out["detemplate_model"] = model
        out["rewrite_strategy"] = rr.get("rewrite_strategy", "")
        out["removed_template_cues"] = rr.get("removed_template_cues", "")
        out["leakage_risk_after_rewrite"] = rr.get("leakage_risk_after_rewrite", "unknown")
        out["detemplate_semantic_notes"] = rr.get("semantic_notes", "")
        out["detemplate_created_at_utc"] = created
        out_rows.append(out)

    fieldnames = list(source_rows[0].keys())
    additions = [
        "claim_text_original_template",
        "claim_text_detemplated",
        "detemplate_status",
        "detemplate_model",
        "rewrite_strategy",
        "removed_template_cues",
        "leakage_risk_after_rewrite",
        "detemplate_semantic_notes",
        "detemplate_created_at_utc",
    ]
    for f in additions:
        if f not in fieldnames:
            fieldnames.append(f)
    write_csv(OUT_CANDIDATES, out_rows, fieldnames)
    write_jsonl(OUT_CANDIDATES_JSONL, out_rows)

    membership = split_membership()
    split_counts = {}
    for split in ["train", "dev", "test"]:
        split_rows = [r for r in out_rows if membership.get(r.get("candidate_id") or r.get("expand_id")) == split]
        split_counts[split] = len(split_rows)
        write_csv(OUT_SPLITS / f"{split}.csv", split_rows, fieldnames)
        write_jsonl(OUT_SPLITS / f"{split}.jsonl", split_rows)
    write_csv(OUT_SPLITS / "all.csv", out_rows, fieldnames)
    write_jsonl(OUT_SPLITS / "all.jsonl", out_rows)
    return out_rows, split_counts, fieldnames


def prefix_key(text, mode):
    clean = normalize_space(re.sub(r"[^\w\s:-]", " ", (text or "").lower()))
    if mode == "before_colon":
        return clean.split(":", 1)[0][:80] if ":" in clean else clean.split(" ", 1)[0]
    words = clean.split()
    n = int(mode.replace("first", ""))
    return " ".join(words[:n])


def macro_f1(y_true, y_pred):
    labels = sorted(set(y_true) | set(y_pred))
    if not labels:
        return 0.0
    f1s = []
    for label in labels:
        tp = sum(1 for a, b in zip(y_true, y_pred) if a == label and b == label)
        fp = sum(1 for a, b in zip(y_true, y_pred) if a != label and b == label)
        fn = sum(1 for a, b in zip(y_true, y_pred) if a == label and b != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1s.append((2 * precision * recall / (precision + recall)) if precision + recall else 0.0)
    return sum(f1s) / len(f1s)


def accuracy(y_true, y_pred):
    if not y_true:
        return 0.0
    return sum(1 for a, b in zip(y_true, y_pred) if a == b) / len(y_true)


def train_prefix_classifier(train_rows, target, mode):
    global_majority = Counter((r.get(target) or "").strip() for r in train_rows).most_common(1)
    default = global_majority[0][0] if global_majority else ""
    by_key = defaultdict(Counter)
    for r in train_rows:
        by_key[prefix_key(r.get("claim_text", ""), mode)][(r.get(target) or "").strip()] += 1
    mapping = {k: c.most_common(1)[0][0] for k, c in by_key.items()}
    return mapping, default


def eval_prefix_classifier(train_rows, eval_rows, target, mode, split):
    mapping, default = train_prefix_classifier(train_rows, target, mode)
    y_true = [(r.get(target) or "").strip() for r in eval_rows]
    y_pred = [mapping.get(prefix_key(r.get("claim_text", ""), mode), default) for r in eval_rows]
    keys = [prefix_key(r.get("claim_text", ""), mode) for r in eval_rows]
    return {
        "dataset": "simclaim_detemplate_v1_150",
        "target": target,
        "prefix_mode": mode,
        "eval_split": split,
        "n_train": len(train_rows),
        "n_eval": len(eval_rows),
        "accuracy": f"{accuracy(y_true, y_pred):.6f}",
        "macro_f1": f"{macro_f1(y_true, y_pred):.6f}",
        "n_unique_eval_prefixes": len(set(keys)),
        "top_eval_prefix_share": f"{(Counter(keys).most_common(1)[0][1] / len(keys)):.6f}" if keys else "0.000000",
    }


def run_prefix_diagnostics(out_rows):
    membership = split_membership()
    by_split = {"train": [], "dev": [], "test": []}
    for row in out_rows:
        split = membership.get(row.get("candidate_id") or row.get("expand_id"))
        if split in by_split:
            by_split[split].append(row)
    diag = []
    for target in TARGETS:
        if not all(target in r for r in out_rows):
            continue
        for mode in ["first4", "first6", "before_colon"]:
            for split in ["dev", "test"]:
                diag.append(eval_prefix_classifier(by_split["train"], by_split[split], target, mode, split))
    write_csv(PREFIX_DIAG, diag)
    return diag


def quality_audit(out_rows):
    rows = []
    for r in out_rows:
        claim = r.get("claim_text", "")
        original = r.get("claim_text_original_template", "")
        hits = banned_hits(claim)
        rows.append({
            "candidate_id": r.get("candidate_id", ""),
            "variant_type": r.get("variant_type", ""),
            "candidate_label_guess": r.get("candidate_label_guess", ""),
            "word_count": word_count(claim),
            "unchanged_from_template_claim": str(normalize_space(claim).lower() == normalize_space(original).lower()).lower(),
            "banned_cue_hit_count": len(hits),
            "banned_cue_hits": "; ".join(hits),
            "prefix_first4": prefix_key(claim, "first4"),
            "prefix_first6": prefix_key(claim, "first6"),
            "leakage_risk_after_rewrite": r.get("leakage_risk_after_rewrite", ""),
            "detemplate_status": r.get("detemplate_status", ""),
            "source_trace_status": r.get("source_trace_status", ""),
            "claim_text_original_template": original,
            "claim_text_detemplated": claim,
            "detemplate_semantic_notes": r.get("detemplate_semantic_notes", ""),
        })
    write_csv(QUALITY_AUDIT, rows)
    return rows


def summarize(out_rows, quality_rows, prefix_diag, split_counts):
    n = len(out_rows)
    status_counts = Counter(r.get("detemplate_status", "") for r in out_rows)
    risk_counts = Counter((r.get("leakage_risk_after_rewrite", "") or "unknown").lower() for r in out_rows)
    label_counts = Counter(r.get("candidate_label_guess", "") for r in out_rows)
    variant_counts = Counter(r.get("variant_type", "") for r in out_rows)
    banned_after = sum(int(r.get("banned_cue_hit_count", 0)) > 0 for r in quality_rows)
    unchanged = sum(r.get("unchanged_from_template_claim") == "true" for r in quality_rows)
    source_trace_complete = sum(
        1 for r in out_rows
        if r.get("claim_source_url") and r.get("evidence_source_url") and r.get("source_location")
    )
    prefix_test = [
        d for d in prefix_diag
        if d["eval_split"] == "test" and d["prefix_mode"] in ("first4", "first6")
    ]
    worst_prefix_macro = max([float(d["macro_f1"]) for d in prefix_test], default=0.0)
    summary = {
        "dataset": "simclaim_detemplate_v1_150",
        "source_dataset": str(SOURCE_ALL),
        "n_rows": n,
        "split_counts": split_counts,
        "detemplate_status_counts": dict(status_counts),
        "leakage_risk_after_rewrite_counts": dict(risk_counts),
        "variant_counts": dict(variant_counts),
        "candidate_label_counts": dict(label_counts),
        "banned_cue_rows_after_rewrite": banned_after,
        "unchanged_rows_after_rewrite": unchanged,
        "source_trace_complete_rate": round(source_trace_complete / n, 6) if n else 0,
        "worst_test_prefix_macro_f1_first4_or_first6": round(worst_prefix_macro, 6),
        "outputs": {
            "candidates_csv": str(OUT_CANDIDATES),
            "candidates_jsonl": str(OUT_CANDIDATES_JSONL),
            "rewrite_audit_csv": str(REWRITE_AUDIT),
            "quality_audit_csv": str(QUALITY_AUDIT),
            "prefix_diagnostic_csv": str(PREFIX_DIAG),
            "report_md": str(REPORT_MD),
        },
        "created_at_utc": utc_now(),
    }
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(summary, prefix_diag)
    return summary


def write_report(summary, prefix_diag):
    def fmt_counts(d):
        return ", ".join(f"{k}={v}" for k, v in d.items()) if d else "none"

    lines = []
    lines.append("# SimClaim detemplate v1 150 report")
    lines.append("")
    lines.append("Purpose: create a small, paper-scaffold dataset whose claims are less template-driven while preserving labels, evidence, and source trace.")
    lines.append("")
    lines.append("## Result")
    lines.append("")
    lines.append(f"- Rows: {summary['n_rows']}")
    lines.append(f"- Splits: {summary['split_counts']}")
    lines.append(f"- Rewrite status: {fmt_counts(summary['detemplate_status_counts'])}")
    lines.append(f"- Leakage risk after rewrite: {fmt_counts(summary['leakage_risk_after_rewrite_counts'])}")
    lines.append(f"- Rows still containing banned cue phrases: {summary['banned_cue_rows_after_rewrite']}")
    lines.append(f"- Rows unchanged from templated claim: {summary['unchanged_rows_after_rewrite']}")
    lines.append(f"- Source trace complete rate: {summary['source_trace_complete_rate']}")
    lines.append(f"- Worst test prefix-only macro-F1 among first4/first6 diagnostics: {summary['worst_test_prefix_macro_f1_first4_or_first6']}")
    lines.append("")
    lines.append("## Prefix leakage diagnostics")
    lines.append("")
    lines.append("| target | prefix | split | acc | macro-F1 | unique prefixes | top prefix share |")
    lines.append("|---|---:|---|---:|---:|---:|---:|")
    for d in prefix_diag:
        lines.append(
            f"| {d['target']} | {d['prefix_mode']} | {d['eval_split']} | "
            f"{d['accuracy']} | {d['macro_f1']} | {d['n_unique_eval_prefixes']} | {d['top_eval_prefix_share']} |"
        )
    lines.append("")
    lines.append("## Files")
    lines.append("")
    for name, path in summary["outputs"].items():
        lines.append(f"- {name}: `{path}`")
    lines.append("")
    lines.append("## Recommended next step")
    lines.append("")
    if summary["banned_cue_rows_after_rewrite"] == 0 and summary["unchanged_rows_after_rewrite"] <= 3:
        lines.append(
            "Use this detemplated 150 set as the small-data scaffold. Next, run the same formal baselines and LLM baselines on this version; "
            "if claim-only/prefix-only leakage drops while claim+evidence remains strong, then expand to 300-600 candidates with the same schema."
        )
    else:
        lines.append(
            "Do one more rewrite cleanup pass on rows flagged in detemplate_quality_audit.csv before using the set for baseline claims."
        )
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-workers", type=int, default=6)
    parser.add_argument("--skip-llm", action="store_true")
    args = parser.parse_args()

    ensure_dirs()
    rows = read_csv(SOURCE_ALL)
    if len(rows) != 150:
        print(f"WARNING: expected 150 rows, got {len(rows)}", file=sys.stderr, flush=True)

    api_key = os.environ.get("LLM_API_KEY", "").strip()
    base_url = os.environ.get("LLM_BASE_URL", "https://api.holysheep.ai/v1/chat/completions").strip()
    model = os.environ.get("LLM_MODEL", "gpt-5.5").strip()

    if args.skip_llm:
        rewrites = {}
        for row in rows:
            cid = row.get("candidate_id") or row.get("expand_id")
            rewrites[cid] = {
                "candidate_id": cid,
                "detemplate_status": "local_fallback_skip_llm",
                "detemplated_claim": fallback_rewrite(row),
                "rewrite_strategy": "rule_fallback_template_prefix_removed",
                "removed_template_cues": ",".join(banned_hits(row.get("claim_text") or "")),
                "leakage_risk_after_rewrite": "high" if banned_hits(fallback_rewrite(row)) else "medium",
                "semantic_notes": "Local fallback because --skip-llm was used.",
                "detemplate_error": "",
            }
        write_csv(REWRITE_AUDIT, list(rewrites.values()), REWRITE_FIELDS)
    else:
        if not api_key:
            raise SystemExit("LLM_API_KEY is required unless --skip-llm is used.")
        rewrites = run_rewrites(rows, api_key, base_url, model, args.max_workers)

    out_rows, split_counts, _ = build_dataset(rows, rewrites, model)
    quality_rows = quality_audit(out_rows)
    prefix_diag = run_prefix_diagnostics(out_rows)
    summary = summarize(out_rows, quality_rows, prefix_diag, split_counts)
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
