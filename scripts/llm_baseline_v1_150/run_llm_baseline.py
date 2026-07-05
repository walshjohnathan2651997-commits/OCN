import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"D:\ocn")
EXP_ROOT = ROOT / "experiments" / "llm_baseline_v1_150"
INPUT_DIR = EXP_ROOT / "inputs"
RAW_DIR = EXP_ROOT / "raw_outputs"
PRED_DIR = EXP_ROOT / "predictions"
REPORT_DIR = EXP_ROOT / "reports"


def get_config():
    api_key = (
        os.environ.get("LLM_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("OPENROUTER_API_KEY")
        or os.environ.get("DEEPSEEK_API_KEY")
    )
    base_url = os.environ.get("LLM_BASE_URL") or "https://api.openai.com/v1/chat/completions"
    model = os.environ.get("LLM_MODEL") or "gpt-4o-mini"
    return api_key, base_url, model


def parse_label(text):
    raw = str(text or "").strip()
    try:
        obj = json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw, flags=re.S)
        if not m:
            return None, None, raw
        try:
            obj = json.loads(m.group(0))
        except Exception:
            return None, None, raw
    label = obj.get("label")
    confidence = obj.get("confidence")
    try:
        label = int(label)
    except Exception:
        label = None
    if label not in (0, 1):
        label = None
    try:
        confidence = float(confidence)
    except Exception:
        confidence = None
    return label, confidence, json.dumps(obj, ensure_ascii=False)


def call_chat(api_key, base_url, model, system_prompt, user_prompt, timeout=90):
    body = {
        "model": model,
        "temperature": 0,
        "max_tokens": 180,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(base_url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {api_key}")
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = resp.read().decode("utf-8")
    latency = time.perf_counter() - t0
    obj = json.loads(payload)
    content = obj["choices"][0]["message"]["content"]
    usage = obj.get("usage", {})
    return content, usage, latency, obj


def read_jsonl(path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def append_jsonl(path, row):
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", default=str(INPUT_DIR / "requests_all.jsonl"))
    parser.add_argument("--raw-output", default=str(RAW_DIR / "llm_raw_outputs.jsonl"))
    parser.add_argument("--pred-output", default=str(PRED_DIR / "llm_predictions.csv"))
    parser.add_argument("--limit", type=int, default=0, help="0 means all")
    parser.add_argument("--sleep", type=float, default=0.2)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    api_key, base_url, model = get_config()
    status = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "api_key_present": bool(api_key),
        "base_url": base_url,
        "model": model,
        "request_file": args.requests,
    }
    if not api_key:
        status["status"] = "blocked_no_llm_api_key"
        status["message"] = "Set LLM_API_KEY or OPENAI_API_KEY plus optional LLM_BASE_URL/LLM_MODEL, then rerun."
        (REPORT_DIR / "llm_run_status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return

    raw_path = Path(args.raw_output)
    pred_path = Path(args.pred_output)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    pred_path.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if args.resume and raw_path.exists():
        for row in read_jsonl(raw_path):
            if not row.get("error"):
                done.add(row.get("request_id"))

    import csv

    pred_fields = [
        "request_id",
        "target",
        "setting",
        "eval_split",
        "candidate_id",
        "gold_proxy_label",
        "pred_label",
        "confidence",
        "parse_ok",
        "latency_sec",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "raw_json",
    ]
    write_header = not pred_path.exists() or not args.resume
    pred_f = pred_path.open("a" if args.resume else "w", encoding="utf-8", newline="")
    writer = csv.DictWriter(pred_f, fieldnames=pred_fields, extrasaction="ignore")
    if write_header:
        writer.writeheader()

    n = 0
    errors = 0
    for item in read_jsonl(Path(args.requests)):
        if args.limit and n >= args.limit:
            break
        if item["request_id"] in done:
            continue
        try:
            content, usage, latency, full = call_chat(api_key, base_url, model, item["system_prompt"], item["user_prompt"])
            label, conf, raw_json = parse_label(content)
            parse_ok = label is not None
            raw_row = {
                "request_id": item["request_id"],
                "target": item["target"],
                "setting": item["setting"],
                "eval_split": item["eval_split"],
                "candidate_id": item["candidate_id"],
                "gold_proxy_label": item["gold_proxy_label"],
                "model": model,
                "content": content,
                "usage": usage,
                "latency_sec": latency,
                "full_response": full,
            }
            append_jsonl(raw_path, raw_row)
            writer.writerow(
                {
                    "request_id": item["request_id"],
                    "target": item["target"],
                    "setting": item["setting"],
                    "eval_split": item["eval_split"],
                    "candidate_id": item["candidate_id"],
                    "gold_proxy_label": item["gold_proxy_label"],
                    "pred_label": "" if label is None else label,
                    "confidence": "" if conf is None else conf,
                    "parse_ok": int(parse_ok),
                    "latency_sec": round(latency, 4),
                    "prompt_tokens": usage.get("prompt_tokens", ""),
                    "completion_tokens": usage.get("completion_tokens", ""),
                    "total_tokens": usage.get("total_tokens", ""),
                    "raw_json": raw_json,
                }
            )
        except urllib.error.HTTPError as e:
            errors += 1
            err_text = e.read().decode("utf-8", errors="replace")[:1000]
            append_jsonl(raw_path, {"request_id": item["request_id"], "error": f"HTTPError {e.code}", "detail": err_text})
        except Exception as e:
            errors += 1
            append_jsonl(raw_path, {"request_id": item["request_id"], "error": type(e).__name__, "detail": str(e)[:1000]})
        pred_f.flush()
        n += 1
        if args.sleep:
            time.sleep(args.sleep)

    pred_f.close()
    status.update({"status": "completed", "attempted": n, "errors": errors, "prediction_file": str(pred_path), "raw_file": str(raw_path)})
    (REPORT_DIR / "llm_run_status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(status, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
