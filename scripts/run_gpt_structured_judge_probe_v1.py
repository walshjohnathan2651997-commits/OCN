"""
Task T - GPT Standard vs Structured Evidence-Sufficiency Judge Probe.

Runs 100 SimClaim samples through two GPT prompt strategies:
  A) Standard judge (same as prior LLM baseline prompt)
  B) Structured evidence-sufficiency decomposition (5-step)

Compares GPT-standard, GPT-structured, R4, and DeepSeek on the same 100
samples. Decides whether GPT naturally solves strong_action_overclaim or
whether explicit evidence-sufficiency decomposition is necessary.

Hard constraints:
- <=100 samples; no full 444.
- No CSV mutation; no gold/final/human_audited writes; no GPT-as-gold.
- No paper/docx changes.
- API key from env var ONLY; never logged.
- Max 2 retries; if no GPT_API_KEY or GPT_MODEL, write missing_api_key_report.md and stop.
- No GPT output written back to main data.

Usage:
  # Set env vars first:
  $env:GPT_API_KEY = "sk-..."
  $env:GPT_BASE_URL = "https://api.holysheep.ai/v1"
  $env:GPT_MODEL = "gpt-5.5"

  # Dry run (no API call, just generate input CSV):
  python run_gpt_structured_judge_probe_v1.py --dry_run

  # Real run:
  python run_gpt_structured_judge_probe_v1.py

  # Resume (skip completed sample_ids in JSONL):
  python run_gpt_structured_judge_probe_v1.py --resume
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SAMPLE_PLAN_CSV = Path(r"D:\ocn\experiments\v3_external_gold_llm_plan_v1\llm_baseline_sample_plan.csv")
SIMCLAIM_CSV = Path(r"D:\ocn\data\simclaim_all92_candidate_pool_v1\strict_silver_max_v1\strict_silver_max_candidates_v1.csv")
DEEPSEEK_RESULTS_CSV = Path(r"D:\ocn\experiments\llm_judge_baseline_v1\llm_vs_r4_200.csv")
DEEPSEEK_METRICS_JSON = Path(r"D:\ocn\experiments\llm_judge_baseline_v1\llm_metrics_200.json")
R4_FROZEN_DIR = Path(r"D:\ocn\experiments\mixed_framework_v2_frozen_r4_baseline")

EXP_DIR = Path(r"D:\ocn\experiments\gpt_structured_judge_probe_v1")
EXP_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = EXP_DIR / "run.log"
LOG_PATH.write_text("", encoding="utf-8")

# ---------------------------------------------------------------------------
# API config (all from env)
# ---------------------------------------------------------------------------
GPT_API_KEY = os.environ.get("GPT_API_KEY", "").strip()
GPT_BASE_URL = os.environ.get("GPT_BASE_URL", "https://api.holysheep.ai/v1").strip().rstrip("/")
GPT_MODEL = os.environ.get("GPT_MODEL", "").strip()
GPT_TIMEOUT = 60
GPT_MAX_RETRIES = 2
GPT_SLEEP_BETWEEN = 0.5
GPT_MAX_TOKENS = 500

# Cost estimate (placeholder; actual pricing depends on proxy provider)
# Using conservative GPT-4-class rates. Real cost may differ.
COST_INPUT_PER_1M = 5.0   # USD per 1M input tokens (placeholder)
COST_OUTPUT_PER_1M = 15.0  # USD per 1M output tokens (placeholder)

# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------
LABELS_4 = ["supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate"]
LABEL_TO_IDX = {lab: i for i, lab in enumerate(LABELS_4)}
IDX_TO_LABEL = {i: lab for i, lab in enumerate(LABELS_4)}

N_PER_CLASS = 25  # 25 * 4 = 100 samples


def log(msg: str) -> None:
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ---------------------------------------------------------------------------
# Sample selection
# ---------------------------------------------------------------------------
def select_100_samples(plan_df: pd.DataFrame, deepseek_df: pd.DataFrame) -> pd.DataFrame:
    """Select 100 samples (25 per class) from the 200-sample plan.
    Prefer samples that have DeepSeek results for cross-comparison.
    Try to cover multiple domains.
    """
    # DeepSeek sample_ids (these have both llm_label and r4_label)
    deepseek_ids = set(deepseek_df["sample_id"].tolist()) if len(deepseek_df) > 0 else set()

    selected = []
    for label in LABELS_4:
        pool = plan_df[plan_df["label_4"] == label].copy()
        # Prefer samples in DeepSeek set
        pool["in_deepseek"] = pool["sample_id"].isin(deepseek_ids)
        pool = pool.sort_values(["in_deepseek"], ascending=False)
        # Take 25, but try to cover multiple domains
        taken = []
        seen_domains = set()
        # First pass: one per domain until we have 25 or run out
        for _, row in pool.iterrows():
            d = row["domain"]
            if d not in seen_domains:
                taken.append(row)
                seen_domains.add(d)
                if len(taken) >= N_PER_CLASS:
                    break
        # Second pass: fill remaining
        if len(taken) < N_PER_CLASS:
            for _, row in pool.iterrows():
                if row["sample_id"] not in {t["sample_id"] for t in taken}:
                    taken.append(row)
                    if len(taken) >= N_PER_CLASS:
                        break
        selected.extend(taken[:N_PER_CLASS])

    out = pd.DataFrame(selected)
    # Shuffle for API call order (so retries don't cluster by class)
    out = out.sample(frac=1, random_state=42).reset_index(drop=True)
    return out


def enrich_with_full_text(selected_df: pd.DataFrame, simclaim_df: pd.DataFrame) -> pd.DataFrame:
    """Join sample plan with full SimClaim CSV to get claim_text and evidence_text."""
    simclaim_subset = simclaim_df[["candidate_id", "claim_text", "evidence_text"]].copy()
    merged = selected_df.merge(simclaim_subset, on="candidate_id", how="left")
    # Check for missing
    missing = merged[merged["claim_text"].isna() | (merged["claim_text"] == "")]
    if len(missing) > 0:
        log(f"WARNING: {len(missing)} samples missing full claim_text after merge")
    return merged


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------
SYSTEM_PROMPT_STANDARD = """You are an evidence-relation auditor for technical/scientific claims. You will receive a claim and its supporting evidence text. You must judge the relation between the claim and the evidence, NOT the truth of the claim in the world.

You may ONLY use the provided evidence. You may NOT use outside knowledge to supply missing evidence. You may NOT use common sense to bridge gaps.

Output strictly valid JSON with these fields:
{
  "label": "supported" | "mild_scope_overclaim" | "strong_action_overclaim" | "contradiction_candidate",
  "confidence": float in [0,1],
  "one_sentence_rationale": string,
  "evidence_used": true | false,
  "uncertain": true | false
}"""

LABEL_DEFINITIONS = """Label definitions:

- supported: Evidence directly and sufficiently supports the claim without material overstatement.
- mild_scope_overclaim: Claim is mostly aligned with evidence but slightly broadens scope, setting, population, condition, or generality.
- strong_action_overclaim: Evidence may be relevant, but the claim makes an unjustified action, deployment, safety, policy, engineering, guarantee, or broad real-world conclusion beyond the evidence.
- contradiction_candidate: Claim directly conflicts with or negates the evidence."""

DECISION_RULES_STANDARD = """Decision rules (apply in order):
1. If the evidence directly conflicts with the claim, output "contradiction_candidate".
2. If the evidence is about metrics/benchmarks/ablations only, but the claim makes a deployment / action / safety / real-world / cross-environment generalization claim that the evidence does NOT substantiate, output "strong_action_overclaim".
3. If the evidence supports the core of the claim but the claim slightly broadens scope (not a deployment/action/safety claim), output "mild_scope_overclaim".
4. If the evidence is sufficient to support the claim as stated, output "supported".
5. If unsure between two labels, set uncertain=true and pick the more conservative (more severe) label.

Constraints:
- Only use the provided evidence; do not use outside knowledge.
- If evidence is missing or empty, do not guess; set uncertain=true.
- Return only the JSON object, no other text."""


def build_standard_user_prompt(claim_text: str, evidence_text: str) -> str:
    return f"""Claim:
{claim_text}

Evidence:
{evidence_text}

{LABEL_DEFINITIONS}

{DECISION_RULES_STANDARD}

Return only the JSON object."""


SYSTEM_PROMPT_STRUCTURED = """You are an evidence-relation auditor for technical/scientific claims. You will receive a claim and its supporting evidence text. You must judge the relation between the claim and the evidence, NOT the truth of the claim in the world.

You must perform a structured 5-step evidence-sufficiency decomposition before producing the final label.

You may ONLY use the provided evidence. You may NOT use outside knowledge to supply missing evidence. You may NOT use common sense to bridge gaps.

Output strictly valid JSON with these fields:
{
  "factual_alignment": "supported" | "unsupported" | "contradicted" | "unclear",
  "scope_expansion": true | false,
  "action_or_deployment_claim": true | false,
  "evidence_sufficient_for_action": true | false,
  "label": "supported" | "mild_scope_overclaim" | "strong_action_overclaim" | "contradiction_candidate",
  "confidence": float in [0,1],
  "one_sentence_rationale": string,
  "evidence_used": true | false,
  "uncertain": true | false
}"""

STRUCTURED_STEPS = """Perform the following 5 steps IN ORDER. Each step informs the next.

Step 1 - Factual alignment:
Does the evidence support the factual content of the claim?
- "supported": evidence aligns with claim facts
- "unsupported": evidence does not address claim facts
- "contradicted": evidence asserts the opposite
- "unclear": cannot determine

Step 2 - Scope expansion:
Does the claim broaden scope versus the evidence? (e.g., setting, population, condition, metric, domain, or generality breadth)
- true: claim broadens scope
- false: scope is faithful

Step 3 - Action / deployment / safety claim:
Does the claim contain any of:
- deployment readiness
- engineering recommendation
- policy decision
- safety guarantee
- real-world operational use
- replacement of prior methods
- broad action conclusion
- cross-environment generalization assertion
- true: claim has action/deployment/safety language
- false: claim is descriptive only

Step 4 - Evidence sufficiency for action:
If Step 3 is true, does the evidence DIRECTLY support that stronger action/deployment/safety/generalization conclusion (not merely a related metric/result)?
- true: evidence substantiates the action claim
- false: evidence only supports a narrower result (e.g., benchmark/metric/ablation), insufficient for the action claim
- (if Step 3 is false, set this to true)

Step 5 - Final label:
- "supported": evidence directly and sufficiently supports the claim as stated
- "mild_scope_overclaim": mostly aligned but slightly broadens scope (Step 2 = true, Step 3 = false)
- "strong_action_overclaim": evidence relevant but insufficient to support action/deployment/safety/policy/engineering/guarantee/broad real-world conclusion (Step 3 = true AND Step 4 = false)
- "contradiction_candidate": claim conflicts with evidence (Step 1 = "contradicted")

If unsure between two labels, set uncertain=true and pick the more conservative (more severe) label.

Constraints:
- Only use the provided evidence; do not use outside knowledge.
- If evidence is missing or empty, do not guess; set uncertain=true.
- Return only the JSON object, no other text."""


def build_structured_user_prompt(claim_text: str, evidence_text: str) -> str:
    return f"""Claim:
{claim_text}

Evidence:
{evidence_text}

{LABEL_DEFINITIONS}

{STRUCTURED_STEPS}

Return only the JSON object."""


# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------
def build_chat_url(base_url: str) -> str:
    """Build chat completions URL from base URL.
    If base_url ends with /v1, append /chat/completions.
    Otherwise append /v1/chat/completions.
    """
    if base_url.endswith("/v1"):
        return f"{base_url}/chat/completions"
    elif base_url.endswith("/v1/"):
        return f"{base_url}chat/completions"
    else:
        return f"{base_url}/v1/chat/completions"


def call_gpt_api(
    claim_text: str,
    evidence_text: str,
    api_key: str,
    prompt_type: str,
) -> dict:
    """Call GPT API. prompt_type is 'standard' or 'structured'.
    Returns dict with raw_response, latency, usage, status, error.
    """
    session = requests.Session()
    session.trust_env = False  # bypass system proxy

    if prompt_type == "standard":
        system_prompt = SYSTEM_PROMPT_STANDARD
        user_prompt = build_standard_user_prompt(claim_text, evidence_text)
    else:
        system_prompt = SYSTEM_PROMPT_STRUCTURED
        user_prompt = build_structured_user_prompt(claim_text, evidence_text)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    result = {
        "request_time": datetime.now().isoformat(timespec="seconds"),
        "prompt_type": prompt_type,
        "latency": 0.0,
        "status": "pending",
        "raw_response": "",
        "error_message": "",
        "input_tokens_est": 0,
        "output_tokens_est": 0,
        "cost_estimate": 0.0,
        "model": GPT_MODEL,
    }

    url = build_chat_url(GPT_BASE_URL)

    for attempt in range(GPT_MAX_RETRIES + 1):
        try:
            t0 = time.time()
            resp = session.post(
                url,
                json={
                    "model": GPT_MODEL,
                    "messages": messages,
                    "temperature": 0,
                    "top_p": 1,
                    "max_tokens": GPT_MAX_TOKENS,
                },
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                timeout=GPT_TIMEOUT,
            )
            result["latency"] = round(time.time() - t0, 2)

            if resp.status_code != 200:
                result["status"] = "http_error"
                # Never log full response body (may contain key echoes in some proxies)
                result["error_message"] = f"HTTP {resp.status_code}: {resp.text[:200]}"
                if attempt < GPT_MAX_RETRIES:
                    time.sleep(1.0)
                    continue
                return result

            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})

            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)

            cost = (input_tokens * COST_INPUT_PER_1M / 1e6
                    + output_tokens * COST_OUTPUT_PER_1M / 1e6)

            result.update({
                "status": "ok",
                "raw_response": content,
                "input_tokens_est": input_tokens,
                "output_tokens_est": output_tokens,
                "cost_estimate": round(cost, 6),
                "model": data.get("model", GPT_MODEL),
            })
            return result

        except Exception as e:
            result["latency"] = round(time.time() - t0, 2)
            result["status"] = "exception"
            result["error_message"] = f"{type(e).__name__}: {str(e)[:200]}"
            if attempt < GPT_MAX_RETRIES:
                time.sleep(1.0)
                continue
            return result

    return result


# ---------------------------------------------------------------------------
# Parse LLM output
# ---------------------------------------------------------------------------
def parse_standard_output(raw_text: str) -> dict:
    """Parse standard JSON output."""
    result = {
        "parse_status": "pending",
        "label": "",
        "confidence": 0.0,
        "one_sentence_rationale": "",
        "evidence_used": False,
        "uncertain": False,
        "warnings": [],
    }
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
        if match:
            try:
                obj = json.loads(match.group(0))
            except json.JSONDecodeError:
                result["parse_status"] = "parse_failed"
                result["warnings"].append("json_decode_failed")
                return result
        else:
            result["parse_status"] = "parse_failed"
            result["warnings"].append("no_json_found")
            return result

    label = str(obj.get("label", "")).strip().lower()
    if label not in LABEL_TO_IDX:
        result["parse_status"] = "invalid_label"
        result["warnings"].append(f"label_not_in_schema:{label}")
        result["label"] = label
        return result

    confidence = obj.get("confidence", 0.0)
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))

    result.update({
        "parse_status": "ok",
        "label": label,
        "confidence": confidence,
        "one_sentence_rationale": str(obj.get("one_sentence_rationale", ""))[:500],
        "evidence_used": bool(obj.get("evidence_used", False)),
        "uncertain": bool(obj.get("uncertain", False)),
    })
    return result


def parse_structured_output(raw_text: str) -> dict:
    """Parse structured JSON output. Check for required fields."""
    result = {
        "parse_status": "pending",
        "factual_alignment": "",
        "scope_expansion": None,
        "action_or_deployment_claim": None,
        "evidence_sufficient_for_action": None,
        "label": "",
        "confidence": 0.0,
        "one_sentence_rationale": "",
        "evidence_used": False,
        "uncertain": False,
        "warnings": [],
    }
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
        if match:
            try:
                obj = json.loads(match.group(0))
            except json.JSONDecodeError:
                result["parse_status"] = "parse_failed"
                result["warnings"].append("json_decode_failed")
                return result
        else:
            result["parse_status"] = "parse_failed"
            result["warnings"].append("no_json_found")
            return result

    label = str(obj.get("label", "")).strip().lower()
    if label not in LABEL_TO_IDX:
        result["parse_status"] = "invalid_label"
        result["warnings"].append(f"label_not_in_schema:{label}")
        result["label"] = label
        return result

    # Required structured fields
    fa = str(obj.get("factual_alignment", "")).strip().lower()
    if fa not in ("supported", "unsupported", "contradicted", "unclear"):
        result["warnings"].append(f"factual_alignment_invalid:{fa}")
        fa = ""

    se = obj.get("scope_expansion", None)
    adc = obj.get("action_or_deployment_claim", None)
    esa = obj.get("evidence_sufficient_for_action", None)

    # Coerce to bool with warning if missing
    for fname, fval in [("scope_expansion", se), ("action_or_deployment_claim", adc), ("evidence_sufficient_for_action", esa)]:
        if fval is None:
            result["warnings"].append(f"{fname}_missing")
        elif not isinstance(fval, bool):
            result["warnings"].append(f"{fname}_not_bool:{fval}")

    confidence = obj.get("confidence", 0.0)
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))

    result.update({
        "parse_status": "ok",
        "factual_alignment": fa,
        "scope_expansion": bool(se) if se is not None else None,
        "action_or_deployment_claim": bool(adc) if adc is not None else None,
        "evidence_sufficient_for_action": bool(esa) if esa is not None else None,
        "label": label,
        "confidence": confidence,
        "one_sentence_rationale": str(obj.get("one_sentence_rationale", ""))[:500],
        "evidence_used": bool(obj.get("evidence_used", False)),
        "uncertain": bool(obj.get("uncertain", False)),
    })
    return result


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
def compute_all_metrics(y_true_label, y_pred_label):
    """y_true_label, y_pred_label: lists of label strings.
    Returns dict of flat4 + binary metrics."""
    y_true_idx = [LABEL_TO_IDX[l] for l in y_true_label]
    y_pred_idx = [LABEL_TO_IDX[l] for l in y_pred_label]

    y_strong = [1 if l == "strong_action_overclaim" else 0 for l in y_true_label]
    p_strong = [1 if l == "strong_action_overclaim" else 0 for l in y_pred_label]
    y_esc = [0 if l == "supported" else 1 for l in y_true_label]
    p_esc = [0 if l == "supported" else 1 for l in y_pred_label]
    y_contra = [1 if l == "contradiction_candidate" else 0 for l in y_true_label]
    p_contra = [1 if l == "contradiction_candidate" else 0 for l in y_pred_label]

    per_label = {}
    for lab in [0, 1, 2, 3]:
        per_label[IDX_TO_LABEL[lab]] = float(f1_score(y_true_idx, y_pred_idx, labels=[lab], average="macro", zero_division=0))

    return {
        "flat4_macro_f1": float(f1_score(y_true_idx, y_pred_idx, average="macro", zero_division=0)),
        "flat4_supported_f1": per_label["supported"],
        "flat4_mild_f1": per_label["mild_scope_overclaim"],
        "flat4_strong_f1": per_label["strong_action_overclaim"],
        "flat4_contradiction_f1": per_label["contradiction_candidate"],
        "strong_positive_f1": float(f1_score(y_strong, p_strong, pos_label=1, zero_division=0)),
        "strong_precision": float(precision_score(y_strong, p_strong, pos_label=1, zero_division=0)),
        "strong_recall": float(recall_score(y_strong, p_strong, pos_label=1, zero_division=0)),
        "escalation_macro_f1": float(f1_score(y_esc, p_esc, average="macro", zero_division=0)),
        "contradiction_positive_f1": float(f1_score(y_contra, p_contra, pos_label=1, zero_division=0)),
        "accuracy": float(accuracy_score(y_true_idx, y_pred_idx)),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def write_missing_key_report(reason: str):
    """Write missing_api_key_report.md and stop."""
    report = f"""# Missing API Key Report

The GPT structured judge probe could not run because: **{reason}**

## Required environment variables

- `GPT_API_KEY` - API key for the OpenAI-compatible endpoint (must NOT be empty)
- `GPT_BASE_URL` - Base URL (default: https://api.holysheep.ai/v1)
- `GPT_MODEL` - Model name (must NOT be empty; do NOT auto-substitute)

## How to set in PowerShell

```powershell
$env:GPT_API_KEY = "sk-..."
$env:GPT_BASE_URL = "https://api.holysheep.ai/v1"
$env:GPT_MODEL = "gpt-5.5"
```

Then re-run:

```
python D:\\ocn\\scripts\\run_gpt_structured_judge_probe_v1.py
```

## Constraints

- API key is read from env var ONLY.
- API key is never written to logs, scripts, or output files.
- If GPT_MODEL is not set, the script stops and asks the user to set it;
  it does NOT auto-substitute another model.
"""
    (EXP_DIR / "missing_api_key_report.md").write_text(report, encoding="utf-8")
    log(f"Missing API key report written: {reason}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry_run", action="store_true", help="Generate input CSV without API calls")
    parser.add_argument("--resume", action="store_true", help="Skip completed sample_ids in JSONL")
    args = parser.parse_args()

    log("=" * 70)
    log("Task T - GPT Standard vs Structured Evidence-Sufficiency Judge Probe")
    log("=" * 70)
    log(f"Output dir: {EXP_DIR}")
    log(f"Base URL: {GPT_BASE_URL}")
    log(f"Model: {GPT_MODEL or '(not set)'}")
    log(f"Dry run: {args.dry_run}")
    log(f"Resume: {args.resume}")

    # ---- Check API config ----
    if not GPT_API_KEY:
        write_missing_key_report("GPT_API_KEY environment variable is empty or not set")
        return
    if not GPT_MODEL:
        write_missing_key_report("GPT_MODEL environment variable is empty or not set (do NOT auto-substitute)")
        return
    log("API key and model configured (key not logged).")

    # ---- Load data ----
    log("[1] Loading sample plan + DeepSeek results + SimClaim CSV...")
    plan_df = pd.read_csv(SAMPLE_PLAN_CSV)
    deepseek_df = pd.read_csv(DEEPSEEK_RESULTS_CSV)
    simclaim_df = pd.read_csv(SIMCLAIM_CSV, keep_default_na=False)
    log(f"  Plan: {len(plan_df)} samples")
    log(f"  DeepSeek results: {len(deepseek_df)} samples")
    log(f"  SimClaim CSV: {len(simclaim_df)} rows")

    # ---- Select 100 samples ----
    log("[2] Selecting 100 samples (25 per class)...")
    selected = select_100_samples(plan_df, deepseek_df)
    log(f"  Selected: {len(selected)} samples")
    log(f"  Label dist: {selected['label_4'].value_counts().to_dict()}")
    log(f"  Domain count: {selected['domain'].nunique()}")
    log(f"  Domain dist: {selected['domain'].value_counts().to_dict()}")

    # ---- Enrich with full text ----
    selected = enrich_with_full_text(selected, simclaim_df)
    # Add task fields
    selected["task"] = "gpt_probe_100"
    selected["n_per_class"] = N_PER_CLASS

    # Save input
    selected.to_csv(EXP_DIR / "gpt_probe_input_100.csv", index=False)
    log(f"  Saved gpt_probe_input_100.csv ({len(selected)} rows)")

    if args.dry_run:
        log("Dry run complete. No API calls made.")
        return

    # ---- Resume: load completed sample_ids ----
    standard_jsonl = EXP_DIR / "gpt_standard_raw_outputs_100.jsonl"
    structured_jsonl = EXP_DIR / "gpt_structured_raw_outputs_100.jsonl"
    completed_standard = set()
    completed_structured = set()
    if args.resume:
        if standard_jsonl.exists():
            with open(standard_jsonl, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        rec = json.loads(line)
                        if rec.get("status") == "ok":
                            completed_standard.add(rec.get("sample_id"))
                    except Exception:
                        pass
        if structured_jsonl.exists():
            with open(structured_jsonl, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        rec = json.loads(line)
                        if rec.get("status") == "ok":
                            completed_structured.add(rec.get("sample_id"))
                    except Exception:
                        pass
        log(f"Resume: standard completed={len(completed_standard)}, structured completed={len(completed_structured)}")

    # ---- Run standard prompt ----
    log("[3] Running Prompt A (standard) on 100 samples...")
    standard_records = []
    if standard_jsonl.exists() and args.resume:
        with open(standard_jsonl, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    standard_records.append(json.loads(line))
                except Exception:
                    pass

    for i, row in selected.iterrows():
        sample_id = row["sample_id"]
        if sample_id in completed_standard:
            continue
        claim_text = str(row["claim_text"])
        evidence_text = str(row["evidence_text"])
        log(f"  [{i+1}/100] standard {sample_id}...")
        result = call_gpt_api(claim_text, evidence_text, GPT_API_KEY, "standard")
        result["sample_id"] = sample_id
        result["candidate_id"] = row["candidate_id"]
        result["label_4_silver"] = row["label_4"]
        standard_records.append(result)
        # Append to JSONL immediately
        with open(standard_jsonl, "a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
        time.sleep(GPT_SLEEP_BETWEEN)

    log(f"  Standard done. Records: {len(standard_records)}")

    # ---- Run structured prompt ----
    log("[4] Running Prompt B (structured) on 100 samples...")
    structured_records = []
    if structured_jsonl.exists() and args.resume:
        with open(structured_jsonl, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    structured_records.append(json.loads(line))
                except Exception:
                    pass

    for i, row in selected.iterrows():
        sample_id = row["sample_id"]
        if sample_id in completed_structured:
            continue
        claim_text = str(row["claim_text"])
        evidence_text = str(row["evidence_text"])
        log(f"  [{i+1}/100] structured {sample_id}...")
        result = call_gpt_api(claim_text, evidence_text, GPT_API_KEY, "structured")
        result["sample_id"] = sample_id
        result["candidate_id"] = row["candidate_id"]
        result["label_4_silver"] = row["label_4"]
        structured_records.append(result)
        with open(structured_jsonl, "a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
        time.sleep(GPT_SLEEP_BETWEEN)

    log(f"  Structured done. Records: {len(structured_records)}")

    # ---- Parse outputs ----
    log("[5] Parsing outputs...")
    standard_parsed_rows = []
    for rec in standard_records:
        if rec.get("status") != "ok":
            standard_parsed_rows.append({
                "sample_id": rec.get("sample_id"),
                "candidate_id": rec.get("candidate_id"),
                "label_4_silver": rec.get("label_4_silver"),
                "parse_status": rec.get("status", "no_response"),
                "label": "",
                "confidence": 0.0,
                "one_sentence_rationale": "",
                "evidence_used": False,
                "uncertain": False,
                "warnings": "no_valid_response",
                "model": rec.get("model", GPT_MODEL),
                "latency": rec.get("latency", 0),
                "input_tokens_est": rec.get("input_tokens_est", 0),
                "output_tokens_est": rec.get("output_tokens_est", 0),
                "cost_estimate": rec.get("cost_estimate", 0),
            })
            continue
        parsed = parse_standard_output(rec["raw_response"])
        standard_parsed_rows.append({
            "sample_id": rec.get("sample_id"),
            "candidate_id": rec.get("candidate_id"),
            "label_4_silver": rec.get("label_4_silver"),
            "parse_status": parsed["parse_status"],
            "label": parsed["label"],
            "confidence": parsed["confidence"],
            "one_sentence_rationale": parsed["one_sentence_rationale"],
            "evidence_used": parsed["evidence_used"],
            "uncertain": parsed["uncertain"],
            "warnings": "|".join(parsed["warnings"]),
            "model": rec.get("model", GPT_MODEL),
            "latency": rec.get("latency", 0),
            "input_tokens_est": rec.get("input_tokens_est", 0),
            "output_tokens_est": rec.get("output_tokens_est", 0),
            "cost_estimate": rec.get("cost_estimate", 0),
        })
    standard_parsed_df = pd.DataFrame(standard_parsed_rows)
    standard_parsed_df.to_csv(EXP_DIR / "gpt_standard_parsed_100.csv", index=False)

    structured_parsed_rows = []
    for rec in structured_records:
        if rec.get("status") != "ok":
            structured_parsed_rows.append({
                "sample_id": rec.get("sample_id"),
                "candidate_id": rec.get("candidate_id"),
                "label_4_silver": rec.get("label_4_silver"),
                "parse_status": rec.get("status", "no_response"),
                "factual_alignment": "",
                "scope_expansion": None,
                "action_or_deployment_claim": None,
                "evidence_sufficient_for_action": None,
                "label": "",
                "confidence": 0.0,
                "one_sentence_rationale": "",
                "evidence_used": False,
                "uncertain": False,
                "warnings": "no_valid_response",
                "model": rec.get("model", GPT_MODEL),
                "latency": rec.get("latency", 0),
                "input_tokens_est": rec.get("input_tokens_est", 0),
                "output_tokens_est": rec.get("output_tokens_est", 0),
                "cost_estimate": rec.get("cost_estimate", 0),
            })
            continue
        parsed = parse_structured_output(rec["raw_response"])
        structured_parsed_rows.append({
            "sample_id": rec.get("sample_id"),
            "candidate_id": rec.get("candidate_id"),
            "label_4_silver": rec.get("label_4_silver"),
            "parse_status": parsed["parse_status"],
            "factual_alignment": parsed["factual_alignment"],
            "scope_expansion": parsed["scope_expansion"],
            "action_or_deployment_claim": parsed["action_or_deployment_claim"],
            "evidence_sufficient_for_action": parsed["evidence_sufficient_for_action"],
            "label": parsed["label"],
            "confidence": parsed["confidence"],
            "one_sentence_rationale": parsed["one_sentence_rationale"],
            "evidence_used": parsed["evidence_used"],
            "uncertain": parsed["uncertain"],
            "warnings": "|".join(parsed["warnings"]),
            "model": rec.get("model", GPT_MODEL),
            "latency": rec.get("latency", 0),
            "input_tokens_est": rec.get("input_tokens_est", 0),
            "output_tokens_est": rec.get("output_tokens_est", 0),
            "cost_estimate": rec.get("cost_estimate", 0),
        })
    structured_parsed_df = pd.DataFrame(structured_parsed_rows)
    structured_parsed_df.to_csv(EXP_DIR / "gpt_structured_parsed_100.csv", index=False)

    # ---- QC ----
    standard_valid = standard_parsed_df[standard_parsed_df["parse_status"] == "ok"]
    structured_valid = structured_parsed_df[structured_parsed_df["parse_status"] == "ok"]
    standard_valid_rate = len(standard_valid) / len(standard_parsed_df) if len(standard_parsed_df) > 0 else 0
    structured_valid_rate = len(structured_valid) / len(structured_parsed_df) if len(structured_parsed_df) > 0 else 0
    log(f"  Standard valid: {len(standard_valid)}/{len(standard_parsed_df)} ({standard_valid_rate:.1%})")
    log(f"  Structured valid: {len(structured_valid)}/{len(structured_parsed_df)} ({structured_valid_rate:.1%})")

    # Check structured field completeness
    struct_field_complete = structured_valid[
        structured_valid["action_or_deployment_claim"].notna()
        & structured_valid["evidence_sufficient_for_action"].notna()
    ]
    log(f"  Structured with all required fields: {len(struct_field_complete)}/{len(structured_valid)}")

    # ---- Compute metrics ----
    log("[6] Computing metrics...")

    def safe_metrics(y_true, y_pred):
        if len(y_true) == 0:
            return {k: None for k in ["flat4_macro_f1", "flat4_supported_f1", "flat4_mild_f1", "flat4_strong_f1", "flat4_contradiction_f1", "strong_positive_f1", "strong_precision", "strong_recall", "escalation_macro_f1", "contradiction_positive_f1", "accuracy", "n_valid"]}
        m = compute_all_metrics(y_true, y_pred)
        m["n_valid"] = len(y_true)
        return m

    # Standard metrics
    std_y_true = standard_valid["label_4_silver"].tolist()
    std_y_pred = standard_valid["label"].tolist()
    std_metrics = safe_metrics(std_y_true, std_y_pred)

    # Structured metrics
    str_y_true = structured_valid["label_4_silver"].tolist()
    str_y_pred = structured_valid["label"].tolist()
    str_metrics = safe_metrics(str_y_true, str_y_pred)

    with open(EXP_DIR / "gpt_standard_metrics_100.json", "w", encoding="utf-8") as f:
        json.dump(std_metrics, f, indent=2, default=str)
    with open(EXP_DIR / "gpt_structured_metrics_100.json", "w", encoding="utf-8") as f:
        json.dump(str_metrics, f, indent=2, default=str)

    log(f"  Standard macro_f1: {std_metrics.get('flat4_macro_f1')}")
    log(f"  Standard strong_f1: {std_metrics.get('flat4_strong_f1')}")
    log(f"  Structured macro_f1: {str_metrics.get('flat4_macro_f1')}")
    log(f"  Structured strong_f1: {str_metrics.get('flat4_strong_f1')}")

    # ---- Join with DeepSeek + R4 for same-sample comparison ----
    log("[7] Joining with DeepSeek + R4 for same-sample comparison...")
    deepseek_subset = deepseek_df[["sample_id", "candidate_id", "label_4_silver", "llm_label", "r4_label"]].copy()
    deepseek_subset = deepseek_subset.rename(columns={"llm_label": "deepseek_label"})

    # Build comparison table
    comparison_rows = []
    for _, row in selected.iterrows():
        sid = row["sample_id"]
        cid = row["candidate_id"]
        silver = row["label_4"]
        # GPT standard
        std_row = standard_parsed_df[standard_parsed_df["sample_id"] == sid]
        std_label = std_row.iloc[0]["label"] if len(std_row) > 0 and std_row.iloc[0]["parse_status"] == "ok" else ""
        # GPT structured
        str_row = structured_parsed_df[structured_parsed_df["sample_id"] == sid]
        str_label = str_row.iloc[0]["label"] if len(str_row) > 0 and str_row.iloc[0]["parse_status"] == "ok" else ""
        # DeepSeek + R4
        ds_row = deepseek_subset[deepseek_subset["sample_id"] == sid]
        ds_label = ds_row.iloc[0]["deepseek_label"] if len(ds_row) > 0 else ""
        r4_label = ds_row.iloc[0]["r4_label"] if len(ds_row) > 0 else ""

        comparison_rows.append({
            "sample_id": sid,
            "candidate_id": cid,
            "label_4_silver": silver,
            "gpt_standard_label": std_label,
            "gpt_structured_label": str_label,
            "deepseek_label": ds_label,
            "r4_label": r4_label,
            "gpt_standard_correct": int(std_label == silver) if std_label else 0,
            "gpt_structured_correct": int(str_label == silver) if str_label else 0,
            "deepseek_correct": int(ds_label == silver) if ds_label else 0,
            "r4_correct": int(r4_label == silver) if r4_label else 0,
        })
    comparison_df = pd.DataFrame(comparison_rows)
    comparison_df.to_csv(EXP_DIR / "gpt_vs_r4_deepseek_comparison.csv", index=False)

    # Same-sample R4 metrics
    r4_valid = comparison_df[comparison_df["r4_label"] != ""]
    r4_y_true = r4_valid["label_4_silver"].tolist()
    r4_y_pred = r4_valid["r4_label"].tolist()
    r4_metrics = safe_metrics(r4_y_true, r4_y_pred)

    # Same-sample DeepSeek metrics
    ds_valid = comparison_df[comparison_df["deepseek_label"] != ""]
    ds_y_true = ds_valid["label_4_silver"].tolist()
    ds_y_pred = ds_valid["deepseek_label"].tolist()
    ds_metrics = safe_metrics(ds_y_true, ds_y_pred)

    log(f"  R4 same-sample macro_f1: {r4_metrics.get('flat4_macro_f1')} (n={r4_metrics.get('n_valid')})")
    log(f"  R4 same-sample strong_f1: {r4_metrics.get('flat4_strong_f1')}")
    log(f"  DeepSeek same-sample macro_f1: {ds_metrics.get('flat4_macro_f1')} (n={ds_metrics.get('n_valid')})")
    log(f"  DeepSeek same-sample strong_f1: {ds_metrics.get('flat4_strong_f1')}")

    # ---- Strong error cases ----
    log("[8] Extracting strong_action_overclaim error cases...")
    error_rows = []
    for _, row in comparison_df.iterrows():
        silver = row["label_4_silver"]
        if silver != "strong_action_overclaim":
            continue
        # Cases where strong was missed
        errors = {}
        for method, pred_col in [("gpt_standard", "gpt_standard_label"), ("gpt_structured", "gpt_structured_label"), ("deepseek", "deepseek_label"), ("r4", "r4_label")]:
            pred = row[pred_col]
            if pred != "strong_action_overclaim":
                errors[method] = pred
        if errors:
            error_rows.append({
                "sample_id": row["sample_id"],
                "candidate_id": row["candidate_id"],
                "silver_label": silver,
                "gpt_standard_pred": row["gpt_standard_label"],
                "gpt_structured_pred": row["gpt_structured_label"],
                "deepseek_pred": row["deepseek_label"],
                "r4_pred": row["r4_label"],
                "errors": json.dumps(errors),
            })
    error_df = pd.DataFrame(error_rows)
    error_df.to_csv(EXP_DIR / "gpt_strong_error_cases.csv", index=False)
    log(f"  Strong error cases: {len(error_df)}")

    # ---- Cost report ----
    log("[9] Computing cost report...")
    total_input_std = sum(rec.get("input_tokens_est", 0) for rec in standard_records)
    total_output_std = sum(rec.get("output_tokens_est", 0) for rec in standard_records)
    total_input_str = sum(rec.get("input_tokens_est", 0) for rec in structured_records)
    total_output_str = sum(rec.get("output_tokens_est", 0) for rec in structured_records)
    total_cost_std = sum(rec.get("cost_estimate", 0) for rec in standard_records)
    total_cost_str = sum(rec.get("cost_estimate", 0) for rec in structured_records)
    total_cost = total_cost_std + total_cost_str
    total_api_calls = len(standard_records) + len(structured_records)

    cost_md = f"""# GPT Structured Judge Probe - Cost Report

## Summary

- **Model**: {GPT_MODEL}
- **Base URL**: {GPT_BASE_URL}
- **Total API calls**: {total_api_calls}
- **Total cost (estimated)**: ${total_cost:.6f}

## Standard Prompt (Prompt A)

- API calls: {len(standard_records)}
- Input tokens: {total_input_std:,}
- Output tokens: {total_output_std:,}
- Cost (estimated): ${total_cost_std:.6f}

## Structured Prompt (Prompt B)

- API calls: {len(structured_records)}
- Input tokens: {total_input_str:,}
- Output tokens: {total_output_str:,}
- Cost (estimated): ${total_cost_str:.6f}

## Pricing assumption

- Input: ${COST_INPUT_PER_1M}/1M tokens (placeholder; actual pricing depends on proxy provider)
- Output: ${COST_OUTPUT_PER_1M}/1M tokens (placeholder)

If the proxy returns its own `usage` field, token counts are taken from there.
Actual billing may differ from this estimate.
"""
    (EXP_DIR / "gpt_cost_report.md").write_text(cost_md, encoding="utf-8")

    # ---- Readiness gate ----
    log("[10] Writing readiness gate...")

    std_strong_f1 = std_metrics.get("flat4_strong_f1", 0) or 0
    str_strong_f1 = str_metrics.get("flat4_strong_f1", 0) or 0
    r4_strong_f1 = r4_metrics.get("flat4_strong_f1", 0) or 0
    ds_strong_f1 = ds_metrics.get("flat4_strong_f1", 0) or 0
    std_strong_recall = std_metrics.get("strong_recall", 0) or 0
    str_strong_recall = str_metrics.get("strong_recall", 0) or 0
    std_macro_f1 = std_metrics.get("flat4_macro_f1", 0) or 0
    str_macro_f1 = str_metrics.get("flat4_macro_f1", 0) or 0
    r4_macro_f1 = r4_metrics.get("flat4_macro_f1", 0) or 0
    ds_macro_f1 = ds_metrics.get("flat4_macro_f1", 0) or 0
    std_contra_f1 = std_metrics.get("flat4_contradiction_f1", 0) or 0
    str_contra_f1 = str_metrics.get("flat4_contradiction_f1", 0) or 0

    # Interpretation rules (A/B/C/D)
    does_standard_solve_strong = bool(std_strong_f1 >= r4_strong_f1 - 0.05)  # rule A threshold
    does_structured_fix_strong = bool(str_strong_f1 > std_strong_f1 + 0.05)  # B requires structured > standard
    does_structured_hurt_contra = bool(
        str_contra_f1 < std_contra_f1 - 0.05  # contradiction F1 drops
        or str_macro_f1 < std_macro_f1 - 0.05  # or macro drops
    )

    # Paper positioning logic
    if does_standard_solve_strong:
        positioning = "r4_as_interpretable_baseline_only"  # rule A
    elif does_structured_fix_strong and not does_structured_hurt_contra:
        positioning = "structured_prompt_supports_decomposition"  # rule B
    elif str_strong_f1 < r4_strong_f1 and std_strong_f1 < r4_strong_f1:
        positioning = "llm_blindspot_supported"  # rule C
    elif does_structured_fix_strong and does_structured_hurt_contra:
        positioning = "llm_blindspot_supported"  # rule D - structured helps strong but hurts macro/contra
    else:
        positioning = "inconclusive"

    gate = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "model": GPT_MODEL,
        "n_samples": len(selected),
        "standard_valid_rate": float(standard_valid_rate),
        "structured_valid_rate": float(structured_valid_rate),
        "standard_macro_f1": float(std_macro_f1) if std_macro_f1 else None,
        "structured_macro_f1": float(str_macro_f1) if str_macro_f1 else None,
        "r4_macro_f1_same_samples": float(r4_macro_f1) if r4_macro_f1 else None,
        "deepseek_macro_f1_same_samples": float(ds_macro_f1) if ds_macro_f1 else None,
        "standard_strong_f1": float(std_strong_f1) if std_strong_f1 else None,
        "structured_strong_f1": float(str_strong_f1) if str_strong_f1 else None,
        "r4_strong_f1_same_samples": float(r4_strong_f1) if r4_strong_f1 else None,
        "deepseek_strong_f1_same_samples": float(ds_strong_f1) if ds_strong_f1 else None,
        "standard_strong_recall": float(std_strong_recall) if std_strong_recall else None,
        "structured_strong_recall": float(str_strong_recall) if str_strong_recall else None,
        "standard_contradiction_f1": float(std_contra_f1) if std_contra_f1 else None,
        "structured_contradiction_f1": float(str_contra_f1) if str_contra_f1 else None,
        "does_standard_gpt_solve_strong": does_standard_solve_strong,
        "does_structured_prompt_fix_strong": does_structured_fix_strong,
        "does_structured_prompt_hurt_contradiction": does_structured_hurt_contra,
        "recommended_paper_positioning": positioning,
        "main_risk": (
            "Small N=100; silver labels (not gold); GPT model accessed via third-party proxy "
            "(pricing/availability may change); single temperature=0 run (no variance estimate)."
        ),
        "recommended_next_step": (
            "Use positioning to update paper Section on LLM judge comparison. "
            "Do NOT claim GPT as gold; do NOT replace SimClaim gold with GPT labels."
        ),
        "total_cost_estimate": float(total_cost),
        "total_api_calls": int(total_api_calls),
        "interpretation_rule_triggered": {
            "A_standard_solves_strong": does_standard_solve_strong,
            "B_structured_fixes_strong_clean": does_structured_fix_strong and not does_structured_hurt_contra,
            "C_both_below_r4": (str_strong_f1 < r4_strong_f1 and std_strong_f1 < r4_strong_f1),
            "D_structured_helps_but_hurts": does_structured_fix_strong and does_structured_hurt_contra,
        },
    }
    with open(EXP_DIR / "gpt_structured_probe_gate.json", "w", encoding="utf-8") as f:
        json.dump(gate, f, indent=2, ensure_ascii=False, default=str)

    # ---- Final log ----
    log("=" * 70)
    log("Task T COMPLETE")
    log("=" * 70)
    log(f"Model: {GPT_MODEL}")
    log(f"Total cost: ${total_cost:.6f}")
    log(f"Standard GPT: macro_f1={std_macro_f1:.4f}, strong_f1={std_strong_f1:.4f}, strong_recall={std_strong_recall:.4f}, contra_f1={std_contra_f1:.4f}")
    log(f"Structured GPT: macro_f1={str_macro_f1:.4f}, strong_f1={str_strong_f1:.4f}, strong_recall={str_strong_recall:.4f}, contra_f1={str_contra_f1:.4f}")
    log(f"R4 (same 100): macro_f1={r4_macro_f1:.4f}, strong_f1={r4_strong_f1:.4f}")
    log(f"DeepSeek (same 100): macro_f1={ds_macro_f1:.4f}, strong_f1={ds_strong_f1:.4f}")
    log(f"Standard solves strong? {does_standard_solve_strong}")
    log(f"Structured fixes strong? {does_structured_fix_strong}")
    log(f"Structured hurts contra/macro? {does_structured_hurt_contra}")
    log(f"Paper positioning: {positioning}")
    log(f"Output dir: {EXP_DIR}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"FATAL: {type(e).__name__}: {e}")
        log(traceback.format_exc())
        sys.exit(1)
