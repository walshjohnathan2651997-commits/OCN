"""
Task R - SimClaim 100/200-sample LLM Judge Baseline.

Calls DeepSeek (OpenAI-compatible) API to judge 100 (pilot) or 200 SimClaim pairs.
Compares LLM judge vs frozen R4 on the same samples.
No data mutation, no gold writing, no full-dataset runs.

Usage:
  # Dry run (no API call, just generate input CSV):
  python run_llm_judge_baseline_v1.py --dry_run --n_samples 100

  # Real run (pilot 100):
  $env:DEEPSEEK_API_KEY = "sk-..."
  python run_llm_judge_baseline_v1.py --n_samples 100

  # Expand to 200 (only after 100 pilot passes gate):
  python run_llm_judge_baseline_v1.py --n_samples 200
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
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PAPER_STRICT_CSV = Path(
    r"D:\ocn\data\simclaim_all92_candidate_pool_v1\strict_silver_max_v1\strict_silver_max_candidates_v1.csv"
)
HCM_FEATURES_CSV = Path(r"D:\ocn\experiments\cese_ocn_hcm_v1\hcm_features.csv")
SAMPLE_PLAN_CSV = Path(r"D:\ocn\experiments\v3_external_gold_llm_plan_v1\llm_baseline_sample_plan.csv")
FROZEN_R4_DIR = Path(r"D:\ocn\experiments\mixed_framework_v2_frozen_r4_baseline")

EXP_DIR = Path(r"D:\ocn\experiments\llm_judge_baseline_v1")
EXP_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = EXP_DIR / "run.log"
LOG_PATH.write_text("", encoding="utf-8")

# ---------------------------------------------------------------------------
# API config
# ---------------------------------------------------------------------------
API_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
API_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
API_TIMEOUT = 60
API_MAX_RETRIES = 2
API_SLEEP_BETWEEN = 0.5

# DeepSeek pricing (USD per 1M tokens, as of 2024-2025 public listing)
PRICE_INPUT_CACHE_HIT = 0.14
PRICE_INPUT_CACHE_MISS = 0.27
PRICE_OUTPUT = 0.28

# ---------------------------------------------------------------------------
# Labels and features (mirrors Task L/P)
# ---------------------------------------------------------------------------
LABELS_4 = ["supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate"]
LABEL_TO_IDX = {lab: i for i, lab in enumerate(LABELS_4)}
IDX_TO_LABEL = {i: lab for i, lab in enumerate(LABELS_4)}

NLI_FEATURES = [
    "entailment_correct", "neutral_correct", "contradiction_correct",
    "ent_minus_con_correct", "con_minus_ent_correct", "max_prob_correct", "entropy_correct",
]

CLAIM_ACTION_TERMS = [
    "deploy", "deployment", "real-world", "real world", "production", "operational",
    "safe", "robust", "guarantee", "all scenarios", "all settings", "all environments",
    "replace", "should be used", "policy", "engineering decision", "ready for use",
    "in practice", "uniformly", "without caveat", "irrespective", "across all",
    "will be", "must be", "always",
]
EVIDENCE_ACTION_SUPPORT_TERMS = [
    "real-world validation", "field deployment", "production test", "external validation",
    "safety certification", "multi-site evaluation", "stress test", "failure analysis",
    "operational trial", "empirical validation", "benchmark results", "ablation",
    "evaluation", "experiments show", "results demonstrate", "we evaluate",
    "we compare", "performance", "accuracy", "ground truth",
]
CERTAINTY_TERMS = ["will", "must", "always", "guarantee", "ensure", "definitely", "certainly"]
DEPLOYMENT_TERMS = ["deploy", "deployment", "production", "operational", "field"]
GENERALIZATION_TERMS = ["all scenarios", "all settings", "all environments", "across all", "uniformly", "generaliz"]
METRIC_TERMS = ["metric", "accuracy", "precision", "recall", "f1", "score", "benchmark", "baseline"]
SAFETY_TERMS = ["safe", "safety", "risk", "hazard", "failure", "robust"]
SCOPE_TERMS = ["may", "might", "could", "some", "subset", "narrow", "broad", "scope", "boundary", "limit"]

EXPERT_FEATURES = NLI_FEATURES + [
    "action_escalation_gap", "claim_action_strength", "evidence_action_support",
    "deployment_gap", "metric_to_action_gap", "certainty_gap", "scope_gap",
    "length_diff", "claim_evidence_overlap",
]
SVM_FEATURES = NLI_FEATURES + ["scope_gap"]


def log(msg: str) -> None:
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def count_terms(text: str, terms: list) -> int:
    text_lower = str(text).lower()
    return sum(1 for t in terms if t.lower() in text_lower)


# ---------------------------------------------------------------------------
# Feature building (for R4 comparison)
# ---------------------------------------------------------------------------
def build_action_gap_features(df: pd.DataFrame) -> None:
    claim_text = df["claim_text"].astype(str)
    evidence_text = df["evidence_text"].astype(str)
    df["claim_action_strength"] = claim_text.apply(lambda x: count_terms(x, CLAIM_ACTION_TERMS))
    df["evidence_action_support"] = evidence_text.apply(lambda x: count_terms(x, EVIDENCE_ACTION_SUPPORT_TERMS))
    df["action_escalation_gap"] = df["claim_action_strength"] - df["evidence_action_support"]
    df["certainty_gap"] = claim_text.apply(lambda x: count_terms(x, CERTAINTY_TERMS)) - evidence_text.apply(lambda x: count_terms(x, CERTAINTY_TERMS))
    df["deployment_gap"] = claim_text.apply(lambda x: count_terms(x, DEPLOYMENT_TERMS)) - evidence_text.apply(lambda x: count_terms(x, DEPLOYMENT_TERMS))
    df["metric_to_action_gap"] = df["claim_action_strength"] - evidence_text.apply(lambda x: count_terms(x, METRIC_TERMS))
    df["scope_gap"] = claim_text.apply(lambda x: count_terms(x, SCOPE_TERMS)) - evidence_text.apply(lambda x: count_terms(x, SCOPE_TERMS))
    df["claim_length"] = claim_text.str.len()
    df["evidence_length"] = evidence_text.str.len()
    df["length_diff"] = df["claim_length"] - df["evidence_length"]
    vec = TfidfVectorizer(ngram_range=(1, 1), min_df=1, stop_words="english")
    all_text = list(claim_text) + list(evidence_text)
    tfidf_matrix = vec.fit_transform(all_text)
    claim_tfidf = tfidf_matrix[:len(claim_text)]
    evidence_tfidf = tfidf_matrix[len(claim_text):]
    overlap = np.array([cosine_similarity(claim_tfidf[i], evidence_tfidf[i])[0, 0] for i in range(len(claim_text))])
    df["claim_evidence_overlap"] = overlap


# ---------------------------------------------------------------------------
# Metrics (mirrors Task L/P)
# ---------------------------------------------------------------------------
def compute_all_metrics(y_4idx, y_strong, y_esc, y_contra, pred_4idx):
    m_flat4_macro = float(f1_score(y_4idx, pred_4idx, average="macro", zero_division=0))
    per_label = {}
    for lab in [0, 1, 2, 3]:
        per_label[IDX_TO_LABEL[lab]] = float(f1_score(y_4idx, pred_4idx, labels=[lab], average="macro", zero_division=0))
    pred_strong = (pred_4idx == LABEL_TO_IDX["strong_action_overclaim"]).astype(int)
    pred_esc = (pred_4idx != LABEL_TO_IDX["supported"]).astype(int)
    pred_contra = (pred_4idx == LABEL_TO_IDX["contradiction_candidate"]).astype(int)
    return {
        "flat4_macro_f1": m_flat4_macro,
        "flat4_supported_f1": per_label["supported"],
        "flat4_mild_f1": per_label["mild_scope_overclaim"],
        "flat4_strong_f1": per_label["strong_action_overclaim"],
        "flat4_contradiction_f1": per_label["contradiction_candidate"],
        "strong_positive_f1": float(f1_score(y_strong, pred_strong, pos_label=1, zero_division=0)),
        "strong_precision": float(precision_score(y_strong, pred_strong, pos_label=1, zero_division=0)),
        "strong_recall": float(recall_score(y_strong, pred_strong, pos_label=1, zero_division=0)),
        "escalation_macro_f1": float(f1_score(y_esc, pred_esc, average="macro", zero_division=0)),
        "contradiction_positive_f1": float(f1_score(y_contra, pred_contra, pos_label=1, zero_division=0)),
        "accuracy": float(accuracy_score(y_4idx, pred_4idx)),
    }


# ---------------------------------------------------------------------------
# R4 routing (mirrors Task L/P)
# ---------------------------------------------------------------------------
def route_conservative_strong(p_contra, p_strong, p_svm, t_contra, t_contra_low, t_strong, t_svm, n):
    pred = np.empty(n, dtype=int)
    for i in range(n):
        if p_contra[i] >= t_contra:
            pred[i] = LABEL_TO_IDX["contradiction_candidate"]
        elif p_strong[i] >= t_strong and p_contra[i] < t_contra_low:
            pred[i] = LABEL_TO_IDX["strong_action_overclaim"]
        else:
            pred[i] = LABEL_TO_IDX["supported"] if p_svm[i] < t_svm else LABEL_TO_IDX["mild_scope_overclaim"]
    return pred


def train_r4_and_predict(df, train_mask, dev_mask, test_mask):
    """Train R4 on train, tune on dev, predict on test. Matches Task L exactly."""
    feature_cols_nli = [c for c in NLI_FEATURES if c in df.columns]
    feature_cols_expert = [c for c in EXPERT_FEATURES if c in df.columns]
    feature_cols_svm = [c for c in SVM_FEATURES if c in df.columns]

    y_4idx = df["label_4_idx"].values
    y_strong = df["y_strong"].values
    y_esc = df["y_esc"].values
    y_contra = df["y_contra"].values

    scaler_nli = StandardScaler()
    Xtr_nli = scaler_nli.fit_transform(df.iloc[train_mask][feature_cols_nli].values)
    Xdev_nli = scaler_nli.transform(df.iloc[dev_mask][feature_cols_nli].values)
    Xte_nli = scaler_nli.transform(df.iloc[test_mask][feature_cols_nli].values)

    scaler_exp = StandardScaler()
    Xtr_exp = scaler_exp.fit_transform(df.iloc[train_mask][feature_cols_expert].values)
    Xdev_exp = scaler_exp.transform(df.iloc[dev_mask][feature_cols_expert].values)
    Xte_exp = scaler_exp.transform(df.iloc[test_mask][feature_cols_expert].values)

    scaler_svm = StandardScaler()
    Xtr_svm = scaler_svm.fit_transform(df.iloc[train_mask][feature_cols_svm].values)
    Xdev_svm = scaler_svm.transform(df.iloc[dev_mask][feature_cols_svm].values)
    Xte_svm = scaler_svm.transform(df.iloc[test_mask][feature_cols_svm].values)

    clf_contra = LogisticRegression(class_weight="balanced", max_iter=3000, random_state=42)
    clf_contra.fit(Xtr_nli, y_contra[train_mask])
    clf_strong = LogisticRegression(class_weight="balanced", max_iter=3000, random_state=42)
    clf_strong.fit(Xtr_exp, y_strong[train_mask])

    y_svm_int = df["y_svm"].apply(lambda x: int(x) if x is not None and not (isinstance(x, float) and np.isnan(x)) else -1).values
    svm_train_mask = (y_svm_int >= 0) & train_mask
    if svm_train_mask.sum() > 0 and len(np.unique(y_svm_int[svm_train_mask])) > 1:
        clf_svm = LogisticRegression(class_weight="balanced", max_iter=3000, random_state=42)
        clf_svm.fit(Xtr_svm[svm_train_mask[train_mask]], y_svm_int[svm_train_mask])
        p_svm_dev = clf_svm.predict_proba(Xdev_svm)[:, 1]
        p_svm_test = clf_svm.predict_proba(Xte_svm)[:, 1]
    else:
        p_svm_dev = np.zeros(int(dev_mask.sum()))
        p_svm_test = np.zeros(int(test_mask.sum()))

    p_contra_dev = clf_contra.predict_proba(Xdev_nli)[:, 1]
    p_strong_dev = clf_strong.predict_proba(Xdev_exp)[:, 1]
    p_contra_test = clf_contra.predict_proba(Xte_nli)[:, 1]
    p_strong_test = clf_strong.predict_proba(Xte_exp)[:, 1]

    T_CONTRA_GRID = [0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
    T_STRONG_GRID = [0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
    T_SVM_GRID = [0.4, 0.45, 0.5, 0.55, 0.6]
    T_CONTRA_LOW_GRID = [0.2, 0.25, 0.3, 0.35, 0.4]

    n_dev = int(dev_mask.sum())
    n_test = int(test_mask.sum())

    best_score = -1.0
    best_thresh = (0.5, 0.3, 0.5, 0.5)
    if n_dev > 0:
        for t_c in T_CONTRA_GRID:
            for t_cl in T_CONTRA_LOW_GRID:
                for t_s in T_STRONG_GRID:
                    for t_sv in T_SVM_GRID:
                        pred_dev = route_conservative_strong(p_contra_dev, p_strong_dev, p_svm_dev, t_c, t_cl, t_s, t_sv, n_dev)
                        m = compute_all_metrics(y_4idx[dev_mask], y_strong[dev_mask], y_esc[dev_mask], y_contra[dev_mask], pred_dev)
                        score = 0.4 * m["flat4_macro_f1"] + 0.3 * m["strong_positive_f1"] + 0.2 * m["contradiction_positive_f1"] + 0.1 * m["escalation_macro_f1"]
                        if score > best_score:
                            best_score = score
                            best_thresh = (t_c, t_cl, t_s, t_sv)

    t_c, t_cl, t_s, t_sv = best_thresh
    pred_test = route_conservative_strong(p_contra_test, p_strong_test, p_svm_test, t_c, t_cl, t_s, t_sv, n_test)
    metrics = compute_all_metrics(y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], pred_test)
    return pred_test, metrics, best_thresh


# ---------------------------------------------------------------------------
# Label helpers
# ---------------------------------------------------------------------------
def to_strong_action_binary(label):
    return 1 if label == "strong_action_overclaim" else 0

def to_escalation_binary(label):
    return 0 if label == "supported" else 1

def to_contradiction_binary(label):
    return 1 if label == "contradiction_candidate" else 0

def to_supported_vs_mild(label):
    if label == "supported": return 0
    if label == "mild_scope_overclaim": return 1
    return None


# ---------------------------------------------------------------------------
# LLM prompt construction
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are an evidence-relation auditor for technical/scientific claims. You will receive a claim and its supporting evidence text. You must judge the relation between the claim and the evidence, NOT the truth of the claim in the world.

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

DECISION_RULES = """Decision rules (apply in order):
1. If the evidence directly conflicts with the claim, output "contradiction_candidate".
2. If the evidence is about metrics/benchmarks/ablations only, but the claim makes a deployment / action / safety / real-world / cross-environment generalization claim that the evidence does NOT substantiate, output "strong_action_overclaim".
3. If the evidence supports the core of the claim but the claim slightly broadens scope (not a deployment/action/safety claim), output "mild_scope_overclaim".
4. If the evidence is sufficient to support the claim as stated, output "supported".
5. If unsure between two labels, set uncertain=true and pick the more conservative (more severe) label.

Constraints:
- Only use the provided evidence; do not use outside knowledge.
- If evidence is missing or empty, do not guess; set uncertain=true.
- Return only the JSON object, no other text."""


def build_user_prompt(claim_text: str, evidence_text: str) -> str:
    return f"""Claim:
{claim_text}

Evidence:
{evidence_text}

{LABEL_DEFINITIONS}

{DECISION_RULES}

Return only the JSON object."""


# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------
def call_deepseek_api(claim_text: str, evidence_text: str, api_key: str) -> dict:
    """Call DeepSeek API. Returns dict with raw_response, latency, usage, status, error."""
    session = requests.Session()
    session.trust_env = False  # bypass system proxy
    user_prompt = build_user_prompt(claim_text, evidence_text)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    result = {
        "request_time": datetime.now().isoformat(timespec="seconds"),
        "latency": 0.0,
        "status": "pending",
        "raw_response": "",
        "error_message": "",
        "input_tokens_est": 0,
        "output_tokens_est": 0,
        "cost_estimate": 0.0,
        "model": API_MODEL,
    }

    for attempt in range(API_MAX_RETRIES + 1):
        try:
            t0 = time.time()
            resp = session.post(
                f"{API_BASE_URL}/v1/chat/completions",
                json={
                    "model": API_MODEL,
                    "messages": messages,
                    "temperature": 0,
                    "top_p": 1,
                    "max_tokens": 300,
                },
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                timeout=API_TIMEOUT,
            )
            result["latency"] = round(time.time() - t0, 2)

            if resp.status_code != 200:
                result["status"] = "http_error"
                result["error_message"] = f"HTTP {resp.status_code}: {resp.text[:200]}"
                if attempt < API_MAX_RETRIES:
                    time.sleep(1.0)
                    continue
                return result

            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})

            prompt_cache_hit = usage.get("prompt_cache_hit_tokens", 0)
            prompt_cache_miss = usage.get("prompt_cache_miss_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            input_tokens = prompt_cache_hit + prompt_cache_miss

            cost = (prompt_cache_hit * PRICE_INPUT_CACHE_HIT / 1e6
                    + prompt_cache_miss * PRICE_INPUT_CACHE_MISS / 1e6
                    + output_tokens * PRICE_OUTPUT / 1e6)

            result.update({
                "status": "ok",
                "raw_response": content,
                "input_tokens_est": input_tokens,
                "output_tokens_est": output_tokens,
                "cost_estimate": round(cost, 6),
                "model": data.get("model", API_MODEL),
            })
            return result

        except Exception as e:
            result["latency"] = round(time.time() - t0, 2)
            result["status"] = "exception"
            result["error_message"] = f"{type(e).__name__}: {str(e)[:200]}"
            if attempt < API_MAX_RETRIES:
                time.sleep(1.0)
                continue
            return result

    return result


# ---------------------------------------------------------------------------
# Parse LLM output
# ---------------------------------------------------------------------------
def parse_llm_output(raw_text: str) -> dict:
    """Parse JSON from LLM output. Returns dict with status, label, confidence, etc."""
    result = {
        "parse_status": "pending",
        "label": "",
        "confidence": 0.0,
        "one_sentence_rationale": "",
        "evidence_used": False,
        "uncertain": False,
        "warnings": [],
    }

    # Try to extract JSON from the response
    text = raw_text.strip()
    # Remove markdown code fences if present
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    # Try direct JSON parse
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in text
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

    # Extract fields
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
    if confidence < 0:
        confidence = 0.0
        result["warnings"].append("confidence_clipped_low")
    elif confidence > 1:
        confidence = 1.0
        result["warnings"].append("confidence_clipped_high")

    rationale = str(obj.get("one_sentence_rationale", "")).strip()
    if not rationale:
        result["warnings"].append("empty_rationale")

    evidence_used = bool(obj.get("evidence_used", False))
    uncertain = bool(obj.get("uncertain", False))

    result.update({
        "parse_status": "ok",
        "label": label,
        "confidence": round(confidence, 3),
        "one_sentence_rationale": rationale,
        "evidence_used": evidence_used,
        "uncertain": uncertain,
    })
    return result


# ---------------------------------------------------------------------------
# Resume: load completed sample_ids from JSONL
# ---------------------------------------------------------------------------
def load_completed_ids(jsonl_path: Path) -> set:
    completed = set()
    if not jsonl_path.exists():
        return completed
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if obj.get("status") == "ok":
                    completed.add(obj["sample_id"])
            except json.JSONDecodeError:
                continue
    return completed


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def select_samples(sample_plan: pd.DataFrame, n_samples: int) -> pd.DataFrame:
    """Select first n per class (25 for 100, 50 for 200)."""
    per_class = n_samples // 4
    selected = []
    for label in LABELS_4:
        sub = sample_plan[sample_plan["label_4"] == label].head(per_class)
        selected.append(sub)
    return pd.concat(selected, ignore_index=True)


def run_llm_baseline(n_samples: int, dry_run: bool, api_key: str) -> None:
    suffix = str(n_samples)
    log(f"=" * 70)
    log(f"Task R: LLM Judge Baseline (n={n_samples}, dry_run={dry_run})")
    log(f"=" * 70)

    # Load sample plan
    sample_plan = pd.read_csv(SAMPLE_PLAN_CSV, keep_default_na=False)
    selected = select_samples(sample_plan, n_samples)
    log(f"Selected {len(selected)} samples ({selected['label_4'].value_counts().to_dict()})")

    # Load SimClaim data to get full claim_text and evidence_text
    df_full = pd.read_csv(PAPER_STRICT_CSV, keep_default_na=False)
    selected = selected.merge(
        df_full[["candidate_id", "claim_text", "evidence_text"]],
        on="candidate_id", how="left"
    )
    # Save LLM input
    input_path = EXP_DIR / f"llm_input_{suffix}.csv"
    selected.to_csv(input_path, index=False, encoding="utf-8")
    log(f"Saved {input_path.name} ({len(selected)} rows)")

    if dry_run:
        log("DRY RUN: no API calls. Exiting after generating input CSV.")
        log(f"  Input file: {input_path}")
        log(f"  To run for real: set $env:DEEPSEEK_API_KEY and re-run without --dry_run")
        return

    if not api_key:
        log("FATAL: DEEPSEEK_API_KEY not set in environment. Aborting.")
        return

    # Call API
    jsonl_path = EXP_DIR / f"llm_raw_outputs_{suffix}.jsonl"
    completed_ids = load_completed_ids(jsonl_path)
    log(f"Resume: {len(completed_ids)} samples already completed in {jsonl_path.name}")

    total_cost = 0.0
    n_api_calls = 0
    n_skipped = 0

    with open(jsonl_path, "a", encoding="utf-8") as f_jsonl:
        for idx, row in selected.iterrows():
            sid = row["sample_id"]
            if sid in completed_ids:
                n_skipped += 1
                continue

            log(f"  [{idx+1}/{len(selected)}] {sid} ({row['label_4']}) ...")
            result = call_deepseek_api(row["claim_text"], row["evidence_text"], api_key)
            total_cost += result.get("cost_estimate", 0.0)
            n_api_calls += 1

            record = {
                "sample_id": sid,
                "candidate_id": row["candidate_id"],
                "label_4_silver": row["label_4"],
                "domain": row["domain"],
                "model": result["model"],
                "request_time": result["request_time"],
                "latency": result["latency"],
                "input_tokens_est": result["input_tokens_est"],
                "output_tokens_est": result["output_tokens_est"],
                "cost_estimate": result["cost_estimate"],
                "status": result["status"],
                "error_message": result["error_message"],
                "raw_response": result["raw_response"],
            }
            f_jsonl.write(json.dumps(record, ensure_ascii=False) + "\n")
            f_jsonl.flush()

            if result["status"] != "ok":
                log(f"    FAILED: {result['status']} - {result['error_message'][:100]}")
            else:
                log(f"    OK: latency={result['latency']}s, cost=${result['cost_estimate']:.6f}")

            time.sleep(API_SLEEP_BETWEEN)

    log(f"API calls: {n_api_calls}, skipped (resumed): {n_skipped}, total cost: ${total_cost:.6f}")

    # Parse outputs
    parse_and_evaluate(suffix, selected, total_cost, n_api_calls)


def parse_and_evaluate(suffix: str, selected: pd.DataFrame, total_cost: float, n_api_calls: int) -> None:
    log(f"\n--- Parsing and evaluating ({suffix}) ---")
    jsonl_path = EXP_DIR / f"llm_raw_outputs_{suffix}.jsonl"

    # Load all raw outputs
    raw_records = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                raw_records.append(json.loads(line))

    # Parse each
    parsed_rows = []
    n_ok = 0
    n_parse_failed = 0
    n_invalid_label = 0
    for rec in raw_records:
        sid = rec["sample_id"]
        if rec["status"] != "ok":
            parsed_rows.append({
                "sample_id": sid,
                "candidate_id": rec["candidate_id"],
                "label_4_silver": rec["label_4_silver"],
                "domain": rec["domain"],
                "parse_status": rec["status"],
                "llm_label": "",
                "llm_confidence": 0.0,
                "llm_rationale": "",
                "llm_evidence_used": False,
                "llm_uncertain": False,
                "warnings": rec["error_message"],
                "model": rec["model"],
                "latency": rec["latency"],
                "input_tokens_est": rec.get("input_tokens_est", 0),
                "output_tokens_est": rec.get("output_tokens_est", 0),
                "cost_estimate": rec["cost_estimate"],
            })
            n_parse_failed += 1
            continue

        parsed = parse_llm_output(rec["raw_response"])
        if parsed["parse_status"] == "ok":
            n_ok += 1
        elif parsed["parse_status"] == "invalid_label":
            n_invalid_label += 1
        else:
            n_parse_failed += 1

        parsed_rows.append({
            "sample_id": sid,
            "candidate_id": rec["candidate_id"],
            "label_4_silver": rec["label_4_silver"],
            "domain": rec["domain"],
            "parse_status": parsed["parse_status"],
            "llm_label": parsed["label"],
            "llm_confidence": parsed["confidence"],
            "llm_rationale": parsed["one_sentence_rationale"],
            "llm_evidence_used": parsed["evidence_used"],
            "llm_uncertain": parsed["uncertain"],
            "warnings": ";".join(parsed["warnings"]),
            "model": rec["model"],
            "latency": rec["latency"],
            "input_tokens_est": rec.get("input_tokens_est", 0),
            "output_tokens_est": rec.get("output_tokens_est", 0),
            "cost_estimate": rec["cost_estimate"],
        })

    parsed_df = pd.DataFrame(parsed_rows)
    parsed_path = EXP_DIR / f"llm_parsed_outputs_{suffix}.csv"
    parsed_df.to_csv(parsed_path, index=False, encoding="utf-8")
    log(f"Saved {parsed_path.name} ({len(parsed_df)} rows)")
    log(f"  parse ok: {n_ok}, parse_failed: {n_parse_failed}, invalid_label: {n_invalid_label}")

    valid_rate = n_ok / len(parsed_rows) if parsed_rows else 0.0
    log(f"  valid_rate: {valid_rate:.4f}")

    # Compute total cost from ALL records (including resumed), not just new calls
    total_cost = float(sum(rec.get("cost_estimate", 0) for rec in raw_records))
    n_api_calls = len(raw_records)
    log(f"  total cost (all records): ${total_cost:.6f}, n_records: {n_api_calls}")

    # Compute LLM metrics (only on valid outputs)
    valid_df = parsed_df[parsed_df["parse_status"] == "ok"].copy()
    if len(valid_df) == 0:
        log("FATAL: no valid LLM outputs. Cannot compute metrics.")
        return

    valid_df["llm_label_idx"] = valid_df["llm_label"].map(LABEL_TO_IDX)
    valid_df["silver_idx"] = valid_df["label_4_silver"].map(LABEL_TO_IDX)
    y_true = valid_df["silver_idx"].values
    y_pred = valid_df["llm_label_idx"].values
    y_strong = (y_true == LABEL_TO_IDX["strong_action_overclaim"]).astype(int)
    pred_strong = (y_pred == LABEL_TO_IDX["strong_action_overclaim"]).astype(int)
    y_esc = (y_true != LABEL_TO_IDX["supported"]).astype(int)
    pred_esc = (y_pred != LABEL_TO_IDX["supported"]).astype(int)
    y_contra = (y_true == LABEL_TO_IDX["contradiction_candidate"]).astype(int)
    pred_contra = (y_pred == LABEL_TO_IDX["contradiction_candidate"]).astype(int)

    llm_metrics = compute_all_metrics(y_true, y_strong, y_esc, y_contra, y_pred)
    llm_metrics["n_valid"] = int(len(valid_df))
    llm_metrics["valid_rate"] = float(valid_rate)
    llm_metrics["evidence_used_rate"] = float(valid_df["llm_evidence_used"].mean())
    llm_metrics["uncertain_rate"] = float(valid_df["llm_uncertain"].mean())
    llm_metrics["mean_confidence"] = float(valid_df["llm_confidence"].mean())
    llm_metrics["support_vs_non_support_macro_f1"] = float(
        f1_score(y_esc, pred_esc, average="macro", zero_division=0)
    )

    # Save LLM metrics
    metrics_path = EXP_DIR / f"llm_metrics_{suffix}.json"
    (metrics_path).write_text(json.dumps(llm_metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"Saved {metrics_path.name}")
    log(f"  LLM flat4_macro_f1: {llm_metrics['flat4_macro_f1']:.4f}")
    log(f"  LLM strong_positive_f1: {llm_metrics['strong_positive_f1']:.4f}")
    log(f"  LLM contradiction_positive_f1: {llm_metrics['contradiction_positive_f1']:.4f}")

    # --- R4 comparison on same samples ---
    log("\n--- Training R4 on non-LLM samples, predicting on LLM samples ---")
    r4_metrics, r4_pred_df = train_r4_on_non_llm_and_predict(selected)
    if r4_metrics is None:
        log("R4 comparison failed. Saving LLM-only results.")
        return

    log(f"  R4 flat4_macro_f1: {r4_metrics['flat4_macro_f1']:.4f}")
    log(f"  R4 strong_positive_f1: {r4_metrics['strong_positive_f1']:.4f}")
    log(f"  R4 contradiction_positive_f1: {r4_metrics['contradiction_positive_f1']:.4f}")

    # --- LLM vs R4 comparison ---
    r4_pred_map = dict(zip(r4_pred_df["candidate_id"], r4_pred_df["r4_pred_label"]))
    valid_df["r4_label"] = valid_df["candidate_id"].map(r4_pred_map)
    valid_df["r4_label_idx"] = valid_df["r4_label"].map(LABEL_TO_IDX)
    valid_df["llm_correct"] = (valid_df["llm_label_idx"] == valid_df["silver_idx"]).astype(int)
    valid_df["r4_correct"] = (valid_df["r4_label_idx"] == valid_df["silver_idx"]).astype(int)
    valid_df["llm_vs_r4"] = valid_df.apply(
        lambda r: "both_correct" if r["llm_correct"] and r["r4_correct"]
        else "llm_only" if r["llm_correct"]
        else "r4_only" if r["r4_correct"]
        else "both_wrong", axis=1
    )

    vs_path = EXP_DIR / f"llm_vs_r4_{suffix}.csv"
    valid_df.to_csv(vs_path, index=False, encoding="utf-8")
    log(f"Saved {vs_path.name} ({len(valid_df)} rows)")

    # Error cases
    error_df = valid_df[valid_df["llm_correct"] == 0].copy()
    error_path = EXP_DIR / f"llm_error_cases_{suffix}.csv"
    error_df.to_csv(error_path, index=False, encoding="utf-8")
    log(f"Saved {error_path.name} ({len(error_df)} LLM errors)")

    # Cost report
    mean_latency = float(parsed_df["latency"].mean())
    total_tokens_in = int(parsed_df["input_tokens_est"].sum())
    total_tokens_out = int(parsed_df["output_tokens_est"].sum())
    cost_md = f"""# LLM Baseline Cost Report ({suffix} samples)

## Summary

- **Model**: {API_MODEL}
- **N samples**: {len(parsed_df)}
- **N valid (parsed OK)**: {n_ok}
- **Valid rate**: {valid_rate:.4f}
- **Total API calls**: {n_api_calls}

## Token Usage

- **Total input tokens**: {total_tokens_in}
- **Total output tokens**: {total_tokens_out}
- **Mean input tokens/call**: {total_tokens_in / max(n_api_calls, 1):.1f}
- **Mean output tokens/call**: {total_tokens_out / max(n_api_calls, 1):.1f}

## Cost

- **Total cost estimate**: ${total_cost:.6f}
- **Mean cost/call**: ${total_cost / max(n_api_calls, 1):.6f}
- **Pricing used**: input cache hit ${PRICE_INPUT_CACHE_HIT}/1M, cache miss ${PRICE_INPUT_CACHE_MISS}/1M, output ${PRICE_OUTPUT}/1M

## Latency

- **Mean latency**: {mean_latency:.2f}s
- **Max latency**: {float(parsed_df['latency'].max()):.2f}s
- **Min latency**: {float(parsed_df['latency'].min()):.2f}s

## LLM vs R4 Cost Comparison

- **LLM cost**: ${total_cost:.6f} for {n_ok} valid predictions
- **R4 cost**: $0 (deterministic local model, no API)
- **LLM latency**: {mean_latency:.2f}s/call (amortized)
- **R4 latency**: <0.01s/call (local inference)

## Notes

- Cost is an estimate based on public DeepSeek pricing; actual billing may vary.
- R4 is a local deterministic model with zero marginal API cost.
- LLM provides natural-language rationales; R4 provides transparent routing thresholds.
"""
    (EXP_DIR / f"llm_cost_report_{suffix}.md").write_text(cost_md, encoding="utf-8")
    log(f"Saved llm_cost_report_{suffix}.md")

    # --- Run gate ---
    frozen_r4 = json.loads((FROZEN_R4_DIR / "frozen_r4_metrics_summary.json").read_text(encoding="utf-8"))
    r4_ref_strong = frozen_r4.get("r4_strong_positive_f1", 0.3967)

    llm_beats_r4_strong = llm_metrics["strong_positive_f1"] > r4_metrics["strong_positive_f1"]
    llm_beats_r4_macro = llm_metrics["flat4_macro_f1"] > r4_metrics["flat4_macro_f1"]
    usable = valid_rate >= 0.95 and n_ok >= 95
    recommend_expand = usable and (suffix == "100")

    # Result interpretation
    if llm_metrics["flat4_macro_f1"] > r4_metrics["flat4_macro_f1"] + 0.05:
        interpretation = "LLM is a strong black-box judge; R4 remains transparent, auditable, low-cost, and deterministic."
    elif abs(llm_metrics["flat4_macro_f1"] - r4_metrics["flat4_macro_f1"]) <= 0.05:
        interpretation = "R4 achieves competitive pilot performance with interpretable routing."
    else:
        interpretation = "Action-overclaim calibration remains difficult even for LLM judges."

    gate = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "model": API_MODEL,
        "base_url_redacted": API_BASE_URL.replace("https://", "***://"),
        "n_requested": int(len(parsed_df)),
        "n_completed": int(n_api_calls),
        "n_valid": int(n_ok),
        "valid_rate": float(valid_rate),
        "total_cost_estimate": float(total_cost),
        "macro_f1": float(llm_metrics["flat4_macro_f1"]),
        "strong_f1": float(llm_metrics["strong_positive_f1"]),
        "contradiction_f1": float(llm_metrics["contradiction_positive_f1"]),
        "escalation_macro_f1": float(llm_metrics["escalation_macro_f1"]),
        "evidence_used_rate": float(llm_metrics["evidence_used_rate"]),
        "uncertain_rate": float(llm_metrics["uncertain_rate"]),
        "r4_strong_f1_reference": float(r4_ref_strong),
        "r4_strong_f1_on_same_samples": float(r4_metrics["strong_positive_f1"]),
        "r4_macro_f1_on_same_samples": float(r4_metrics["flat4_macro_f1"]),
        "llm_beats_r4_on_strong": bool(llm_beats_r4_strong),
        "llm_beats_r4_on_macro": bool(llm_beats_r4_macro),
        "delta_llm_minus_r4_strong": float(llm_metrics["strong_positive_f1"] - r4_metrics["strong_positive_f1"]),
        "delta_llm_minus_r4_macro": float(llm_metrics["flat4_macro_f1"] - r4_metrics["flat4_macro_f1"]),
        "usable_for_paper": bool(usable),
        "recommend_expand_to_200": bool(recommend_expand),
        "interpretation": interpretation,
        "main_risk": "small_sample_pilot" if n_ok < 95 else "none",
        "recommended_next_step": (
            "expand to 200 samples if user approves" if recommend_expand
            else "pilot sufficient; do not expand" if usable
            else "fix parse failures before expanding"
        ),
        "llm_vs_r4_breakdown": {
            "both_correct": int((valid_df["llm_vs_r4"] == "both_correct").sum()),
            "llm_only": int((valid_df["llm_vs_r4"] == "llm_only").sum()),
            "r4_only": int((valid_df["llm_vs_r4"] == "r4_only").sum()),
            "both_wrong": int((valid_df["llm_vs_r4"] == "both_wrong").sum()),
        },
    }
    gate_path = EXP_DIR / f"llm_run_gate_{suffix}.json"
    gate_path.write_text(json.dumps(gate, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"Saved {gate_path.name}")
    log(f"  usable_for_paper: {usable}")
    log(f"  recommend_expand_to_200: {recommend_expand}")
    log(f"  interpretation: {interpretation}")


def train_r4_on_non_llm_and_predict(llm_selected: pd.DataFrame):
    """Train R4 on non-LLM samples, predict on LLM samples."""
    df = pd.read_csv(PAPER_STRICT_CSV, keep_default_na=False)
    hcm = pd.read_csv(HCM_FEATURES_CSV, keep_default_na=False)
    df = df.merge(
        hcm[["candidate_id"] + NLI_FEATURES + ["s_correct", "s_wrong", "margin"]],
        on="candidate_id", how="left"
    )
    build_action_gap_features(df)

    df["label_4"] = df["candidate_label_guess"].astype(str)
    df["label_4_idx"] = df["label_4"].map(LABEL_TO_IDX)
    df["y_strong"] = df["label_4"].apply(to_strong_action_binary)
    df["y_esc"] = df["label_4"].apply(to_escalation_binary)
    df["y_contra"] = df["label_4"].apply(to_contradiction_binary)
    df["y_svm"] = df["label_4"].apply(to_supported_vs_mild)

    llm_candidate_ids = set(llm_selected["candidate_id"].values)
    is_llm = df["candidate_id"].isin(llm_candidate_ids)
    test_mask = is_llm.values
    non_llm = df[~is_llm].copy()

    # Group-aware split of non-LLM into train/dev
    group_ids = non_llm["target_candidate_group_id"].values
    rng = np.random.RandomState(42)
    unique_groups = np.array(sorted(set(group_ids.tolist())))
    rng.shuffle(unique_groups)
    n = len(unique_groups)
    n_train = int(round(n * 0.85))
    train_g = unique_groups[:n_train]
    dev_g = unique_groups[n_train:]

    non_llm["split"] = "none"
    non_llm.loc[non_llm["target_candidate_group_id"].isin(train_g), "split"] = "train"
    non_llm.loc[non_llm["target_candidate_group_id"].isin(dev_g), "split"] = "dev"

    # Build masks on full df
    df["split"] = "test_llm"
    for idx, row in non_llm.iterrows():
        df.loc[idx, "split"] = row["split"]

    train_mask = (df["split"] == "train").values
    dev_mask = (df["split"] == "dev").values
    test_mask_full = (df["split"] == "test_llm").values

    log(f"  R4 split: train={train_mask.sum()}, dev={dev_mask.sum()}, test(LLM)={test_mask_full.sum()}")

    if train_mask.sum() < 50 or dev_mask.sum() < 10:
        log(f"  WARNING: insufficient train/dev samples")
        return None, None

    pred_test, metrics, thresholds = train_r4_and_predict(df, train_mask, dev_mask, test_mask_full)

    r4_pred_df = pd.DataFrame({
        "candidate_id": df.iloc[test_mask_full]["candidate_id"].values,
        "r4_pred_idx": pred_test,
        "r4_pred_label": [IDX_TO_LABEL[i] for i in pred_test],
    })
    return metrics, r4_pred_df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Task R: LLM Judge Baseline")
    parser.add_argument("--n_samples", type=int, default=100, choices=[100, 200])
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()

    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    try:
        run_llm_baseline(args.n_samples, args.dry_run, api_key)
    except Exception as e:
        log(f"FATAL: {e}")
        log(traceback.format_exc())
        raise

    log("\n" + "=" * 70)
    log("Task R complete.")
    log("=" * 70)


if __name__ == "__main__":
    main()
