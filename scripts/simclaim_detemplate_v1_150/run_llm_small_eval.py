import argparse
import csv
import json
import os
import re
import threading
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


ROOT = Path(r"D:\ocn")
SPLIT_ROOT = ROOT / "data" / "simclaim_detemplate_v1_150" / "splits_group_stratified"
EXP_ROOT = ROOT / "experiments" / "simclaim_detemplate_v1_150_llm_small_eval"
PRED_DIR = EXP_ROOT / "predictions"
RAW_DIR = EXP_ROOT / "raw_outputs"
METRIC_DIR = EXP_ROOT / "metrics"
REPORT_DIR = EXP_ROOT / "reports"

PRED_CSV = PRED_DIR / "llm_small_eval_predictions.csv"
RAW_JSONL = RAW_DIR / "llm_small_eval_raw_outputs.jsonl"
METRICS_CSV = METRIC_DIR / "llm_small_eval_metrics.csv"
REPORT_MD = REPORT_DIR / "llm_small_eval_report.md"
SUMMARY_JSON = REPORT_DIR / "llm_small_eval_summary.json"

TARGETS = [
    "issue_binary_label_guess",
    "escalation_binary_label_guess",
    "candidate_label_guess",
]

SETTINGS = [
    "claim_evidence",
    "claim_only",
    "evidence_only",
]

LABEL_OPTIONS = {
    "issue_binary_label_guess": ["0", "1"],
    "escalation_binary_label_guess": ["0", "1"],
    "candidate_label_guess": [
        "supported",
        "mild_scope_overclaim",
        "strong_action_overclaim",
        "contradiction_candidate",
    ],
}


def ensure_dirs():
    for p in [PRED_DIR, RAW_DIR, METRIC_DIR, REPORT_DIR]:
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
            for k in row:
                if k not in seen:
                    fieldnames.append(k)
                    seen.add(k)
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


def normalize_space(text):
    return re.sub(r"\s+", " ", (text or "")).strip()


def truncate(text, n=1800):
    text = normalize_space(text)
    return text[:n]


def prompt_for(row, target, setting):
    claim = truncate(row.get("claim_text", ""), 700)
    evidence = truncate(row.get("evidence_text", ""), 1800)
    paper = row.get("paper_title", "")

    if target == "issue_binary_label_guess":
        instruction = (
            "Predict whether the claim has any support issue relative to the evidence. "
            "Return label 0 if the claim is adequately supported; return label 1 if it is an overclaim, unsupported extrapolation, "
            "action/policy leap, or contradiction."
        )
        options = "0 or 1"
    elif target == "escalation_binary_label_guess":
        instruction = (
            "Predict whether the claim escalates beyond the evidence in scope, certainty, causal strength, or actionability. "
            "Return label 0 for no escalation; return label 1 for escalation. A pure contradiction is not necessarily an escalation unless it also overstates scope/action/certainty."
        )
        options = "0 or 1"
    else:
        instruction = (
            "Choose the best candidate type: supported, mild_scope_overclaim, strong_action_overclaim, or contradiction_candidate. "
            "supported means directly entailed by evidence; mild_scope_overclaim broadens the finding; strong_action_overclaim implies deployment/action/policy/safety use; "
            "contradiction_candidate conflicts with the evidence."
        )
        options = ", ".join(LABEL_OPTIONS[target])

    if setting == "claim_evidence":
        content = f"Paper: {paper}\n\nClaim:\n{claim}\n\nEvidence:\n{evidence}\n\n{instruction}\nAllowed labels: {options}"
    elif setting == "claim_only":
        content = f"Paper: {paper}\n\nClaim:\n{claim}\n\nEvidence is hidden for this ablation.\n\n{instruction}\nAllowed labels: {options}"
    else:
        content = f"Paper: {paper}\n\nClaim is hidden for this ablation.\n\nEvidence:\n{evidence}\n\n{instruction}\nAllowed labels: {options}"

    return [
        {
            "role": "system",
            "content": (
                "You are evaluating scientific claim-evidence candidates. "
                "Return strict JSON only with keys label, confidence, rationale. The label must be one of the allowed labels."
            ),
        },
        {"role": "user", "content": content + "\n\nJSON only."},
    ]


def post_chat(messages, api_key, base_url, model, timeout=90):
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "max_tokens": 220,
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


def extract_json(text):
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def existing_keys():
    if not PRED_CSV.exists():
        return set()
    keys = set()
    for row in read_csv(PRED_CSV):
        keys.add((row["candidate_id"], row["target"], row["setting"]))
    return keys


FIELDS = [
    "candidate_id",
    "target",
    "setting",
    "true_label",
    "pred_label",
    "correct",
    "confidence",
    "parse_status",
    "rationale",
    "error",
]


def run_one(row, target, setting, api_key, base_url, model):
    cid = row.get("candidate_id", "")
    true = (row.get(target) or "").strip()
    allowed = LABEL_OPTIONS[target]
    messages = prompt_for(row, target, setting)
    last_error = ""
    for attempt in range(1, 4):
        try:
            response = post_chat(messages, api_key, base_url, model)
            content = response["choices"][0]["message"]["content"]
            parsed = extract_json(content)
            label = normalize_space(str(parsed.get("label", "")))
            if label not in allowed:
                lowered = label.lower()
                match = [x for x in allowed if lowered == x.lower()]
                if match:
                    label = match[0]
            if label not in allowed:
                raise ValueError(f"label not allowed: {label}")
            pred = {
                "candidate_id": cid,
                "target": target,
                "setting": setting,
                "true_label": true,
                "pred_label": label,
                "correct": str(label == true).lower(),
                "confidence": normalize_space(str(parsed.get("confidence", ""))),
                "parse_status": "ok",
                "rationale": normalize_space(str(parsed.get("rationale", "")))[:500],
                "error": "",
            }
            raw = {"candidate_id": cid, "target": target, "setting": setting, "status": "ok", "response": response}
            return pred, raw
        except Exception as exc:
            last_error = str(exc)
            time.sleep(min(20, 2 ** attempt))
    pred = {
        "candidate_id": cid,
        "target": target,
        "setting": setting,
        "true_label": true,
        "pred_label": "",
        "correct": "false",
        "confidence": "",
        "parse_status": "error",
        "rationale": "",
        "error": last_error[:500],
    }
    raw = {"candidate_id": cid, "target": target, "setting": setting, "status": "error", "error": last_error}
    return pred, raw


def f1_by_class(y_true, y_pred):
    labels = sorted(set(y_true) | set(y_pred))
    out = {}
    for label in labels:
        tp = sum(1 for a, b in zip(y_true, y_pred) if a == label and b == label)
        fp = sum(1 for a, b in zip(y_true, y_pred) if a != label and b == label)
        fn = sum(1 for a, b in zip(y_true, y_pred) if a == label and b != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        out[label] = f1
    return out


def score_predictions():
    rows = [r for r in read_csv(PRED_CSV) if r.get("parse_status") == "ok"]
    metric_rows = []
    for target in TARGETS:
        for setting in SETTINGS:
            sub = [r for r in rows if r["target"] == target and r["setting"] == setting]
            y_true = [r["true_label"] for r in sub]
            y_pred = [r["pred_label"] for r in sub]
            f1s = f1_by_class(y_true, y_pred)
            acc = sum(1 for a, b in zip(y_true, y_pred) if a == b) / len(y_true) if y_true else 0.0
            macro = sum(f1s.values()) / len(f1s) if f1s else 0.0
            metric_rows.append({
                "dataset": "simclaim_detemplate_v1_150_group_stratified",
                "model": "gpt-5.5",
                "split": "test",
                "target": target,
                "setting": setting,
                "n": len(sub),
                "parse_ok": len(sub),
                "accuracy": f"{acc:.6f}",
                "macro_f1": f"{macro:.6f}",
                "positive_class_f1": f"{f1s.get('1', ''):.6f}" if "1" in f1s else "",
                "label_distribution": json.dumps(dict(Counter(y_true)), ensure_ascii=False),
            })
    write_csv(METRICS_CSV, metric_rows)
    write_report(metric_rows)
    return metric_rows


def write_report(metric_rows):
    lines = []
    lines.append("# LLM small eval report: detemplated v1 150")
    lines.append("")
    lines.append("Model: `gpt-5.5`; split: group-stratified test; settings: claim+evidence, claim-only, evidence-only.")
    lines.append("")
    lines.append("| target | setting | n | acc | macro-F1 | positive F1 |")
    lines.append("|---|---|---:|---:|---:|---:|")
    for row in metric_rows:
        lines.append(
            f"| {row['target']} | {row['setting']} | {row['n']} | "
            f"{row['accuracy']} | {row['macro_f1']} | {row['positive_class_f1']} |"
        )
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    SUMMARY_JSON.write_text(json.dumps({
        "metrics_csv": str(METRICS_CSV),
        "predictions_csv": str(PRED_CSV),
        "report_md": str(REPORT_MD),
        "rows": metric_rows,
    }, ensure_ascii=False, indent=2), encoding="utf-8")


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

    test_rows = read_csv(SPLIT_ROOT / "test.csv")
    done = existing_keys()
    jobs = []
    for row in test_rows:
        cid = row.get("candidate_id", "")
        for target in TARGETS:
            for setting in SETTINGS:
                key = (cid, target, setting)
                if key not in done:
                    jobs.append((row, target, setting))
    print(f"llm_existing={len(done)} llm_todo={len(jobs)}", flush=True)

    pred_lock = threading.Lock()
    raw_lock = threading.Lock()
    completed = 0
    with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futs = {
            ex.submit(run_one, row, target, setting, api_key, base_url, model): (row, target, setting)
            for row, target, setting in jobs
        }
        for fut in as_completed(futs):
            pred, raw = fut.result()
            append_csv(PRED_CSV, pred, FIELDS, pred_lock)
            append_jsonl(RAW_JSONL, raw, raw_lock)
            completed += 1
            if completed % 30 == 0 or completed == len(jobs):
                print(f"llm_progress={completed}/{len(jobs)}", flush=True)

    metrics = score_predictions()
    print(json.dumps(metrics, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
