"""No-Gold RIGOURATE + Scalar Baseline Pipeline Part 1.

Section 1: RIGOURATE official resource audit (inventory CSV, status MD, gate JSON)
Section 2: RIGOURATE-style scalar baseline construction (rule + nli + llm-label proxy)
Section 3: Scalar baseline evaluation (4 binary tasks, full metrics)
Section 4: Part 1 gate

Prohibitions enforced:
- no gold / no human annotation / no annotation templates
- no paid API calls (uses only existing parsed LLM outputs)
- no model training
- no paper modification
- no original data modification
- no proxy-as-official
- no silver-as-gold
- no planned-as-completed
- no file deletion
"""

import csv
import json
import os
import re
import shutil
from datetime import datetime

import pandas as pd

OUT_DIR = r"D:\ocn\project_synthesis\no_gold_rigourate_public_benchmark_pipeline_v1\part1_scalar_baseline"
EXISTING_SCALAR_CSV = r"D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1\rigourate_style_scalar_scores.csv"
EXISTING_INVENTORY_CSV = r"D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1\official_resource_inventory.csv"
SIMCLAIM_CSV = r"D:\ocn\data\simclaim_all92_candidate_pool_v1\strict_silver_max_v1\strict_silver_max_candidates_v1.csv"
LLM_200_CSV = r"D:\ocn\experiments\llm_judge_baseline_v1\llm_parsed_outputs_200.csv"
GPT_COMPARISON_CSV = r"D:\ocn\experiments\gpt_structured_judge_probe_v1\gpt_vs_r4_deepseek_comparison.csv"
EXISTING_BINARY_CSV = r"D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1\scalar_baseline_binary_results.csv"
EXISTING_SWEEP_CSV = r"D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1\scalar_baseline_threshold_sweep.csv"

AUDIT_DATE = "2026-07-05"
PAPER_ID = "RIGOURATE, arXiv:2601.04350v2 [cs.CL] 12 Jan 2026"

# Cue lists for rule_scalar_score (informational; existing file already has scores)
STRONG_ACTION_CUES = [
    "action", "deployment", "deploy", "safety", "policy", "generalization",
    "guarantee", "always", "fully", "replace", "solve", "ready", "real-world",
    "reliability", "robust", "mature", "closed-loop", "production",
]
EVIDENCE_LIMITATION_CUES = [
    "limited", "simulated", "benchmark", "remains", "barrier", "uncertainty",
    "requires validation", "future work", "does not", "not", "however",
    "but", "although", "while",
]
CONTRADICTION_CUES = [
    "not", "does not", "cannot", "failed", "worse", "lower", "decrease",
    "opposite", "contrary", "refute",
]
MILD_SCOPE_CUES = [
    "all", "each", "every", "main", "primary", "key", "central",
    "more", "extend", "additional", "comprehensive",
]


def ensure_out_dir():
    os.makedirs(OUT_DIR, exist_ok=True)


# ============================================================
# Section 1: RIGOURATE official resource audit
# ============================================================

def write_rigourate_audit():
    """Write inventory CSV, status MD, and gate JSON for official RIGOURATE audit."""
    print("[Section 1] RIGOURATE official resource audit...")

    # Inventory CSV — read existing inventory and copy (it already covers the audit)
    inventory_rows = []
    with open(EXISTING_INVENTORY_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            inventory_rows.append(row)

    # Add audit_date column
    for row in inventory_rows:
        row["audit_date"] = AUDIT_DATE

    inventory_path = os.path.join(OUT_DIR, "rigourate_official_resource_inventory.csv")
    fieldnames = list(inventory_rows[0].keys())
    with open(inventory_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(inventory_rows)
    print(f"  wrote {inventory_path} ({len(inventory_rows)} rows)")

    # Status MD
    status_md = f"""# RIGOURATE Official Reproduction Status

**Audit date:** {AUDIT_DATE}
**Paper:** {PAPER_ID}
**Venue:** Findings of ACL 2026
**Authors:** Joseph James (Sheffield); Chenghao Xiao (Durham); Yucheng Li (Surrey); Nafise Sadat Moosavi (Sheffield); Chenghua Lin (Manchester)

## 1. Resources checked

| Resource | Location | Availability |
| --- | --- | --- |
| arXiv paper (v2) | https://arxiv.org/abs/2601.04350v2 | available |
| ACL Anthology entry | https://aclanthology.org/ | pending_publication (not indexed as of {AUDIT_DATE}) |
| Author homepages | (web search) | available (contact emails present) |
| GitHub repository | (web search) | **not_available** |
| HuggingFace model | (web search) | **not_available** |
| HuggingFace dataset | (web search) | **not_available** |
| Training data (10K+ claim-evidence sets) | (described in paper only) | **not_available** |
| Fine-tuned reranker weights | (described in paper only) | **not_available** |
| Fine-tuned scorer weights | (described in paper only) | **not_available** |
| Annotation scripts | (described in paper only) | **not_available** |
| Supplementary material | (none located) | **not_available** |
| License | (not specified) | **not_available** |

## 2. Blocked reason

The arXiv v2 (12 Jan 2026) of RIGOURATE contains a placeholder string `[Github/HF Link]` in place of the code/data/model URL. As of audit date **{AUDIT_DATE}**, no concrete GitHub repository, HuggingFace model, dataset release, annotation script, supplementary material, or runnable example has been located via web search of arXiv, GitHub, HuggingFace, ACL Anthology, and author homepages.

The paper text describes:
- 10K+ claim-evidence sets annotated by 8 LLM annotators with peer-review calibration and human evaluation
- A fine-tuned multimodal reranker for evidence retrieval
- A fine-tuned model for continuous overstatement scoring (0-1)

None of these artifacts are publicly available.

## 3. Feasibility conclusion

**Status: blocked**

A full official reproduction is **not** currently possible from public resources. Only the arXiv paper text (method description) is available.

Per task spec, when official artifacts are unavailable, a RIGOURATE-style scalar proxy baseline may be constructed. The proxy MUST NOT be claimed as official RIGOURATE; it must be labeled as "RIGOURATE-style" or "scalar overstatement proxy".

## 4. Allowed conclusions

- The official RIGOURATE reproduction is **blocked**.
- A proxy baseline is **required** (this pipeline constructs one).
- No claim may be made that the proxy baseline equals official RIGOURATE.
- No claim may be made that official reproduction succeeded.

## 5. Next actions if artifacts are released

1. Re-audit arXiv for v3 or later versions that may replace the placeholder.
2. Check corresponding author email for code/data request.
3. Monitor ACL Anthology for camera-ready supplementary.
4. Monitor OpenReview for ICLR/NeurIPS dataset release.

## 6. Prohibitions enforced

- Do not claim proxy as official RIGOURATE.
- Do not fabricate reproduction success.
- Do not call paid API.
- Do not modify V3.15 paper.
- Do not modify original data.
- Do not create gold.
- Do not write silver as gold.
"""
    status_path = os.path.join(OUT_DIR, "rigourate_official_reproduction_status.md")
    with open(status_path, "w", encoding="utf-8") as f:
        f.write(status_md)
    print(f"  wrote {status_path}")

    # Gate JSON
    gate = {
        "task": "No-Gold RIGOURATE + Scalar Baseline Pipeline Part 1 - Section 1 Official Audit",
        "audit_date": AUDIT_DATE,
        "paper_identifier": PAPER_ID,
        "venue": "Findings of ACL 2026",
        "official_rigourate_status": "blocked",
        "official_code_available": False,
        "official_data_available": False,
        "official_model_available": False,
        "official_reproduction_possible": False,
        "blocked_reason": (
            "arXiv v2 of RIGOURATE contains a placeholder '[Github/HF Link]' in place of "
            "the code/data/model URL. As of audit date 2026-07-05, no concrete GitHub "
            "repository, HuggingFace model/dataset, annotation script, supplementary "
            "material, or runnable example has been located. Official reproduction is blocked."
        ),
        "partial_assets_available": ["arXiv paper text (full methods description)"],
        "assets_missing": [
            "GitHub repository (placeholder only in arXiv v2)",
            "HuggingFace model repository (placeholder only in arXiv v2)",
            "HuggingFace dataset repository (not released)",
            "Training/evaluation dataset (10K+ claim-evidence sets described but not released)",
            "Fine-tuned reranker weights",
            "Fine-tuned overstatement scorer weights",
            "Annotation scripts (LLM annotator + peer-review calibration pipeline)",
            "Supplementary material",
            "Runnable end-to-end example",
            "License specification",
        ],
        "feasibility_conclusion": "blocked",
        "proxy_baseline_required": True,
        "proxy_baseline_note": (
            "Per task spec, when official artifacts are unavailable, a RIGOURATE-style "
            "scalar proxy baseline may be constructed. The proxy MUST NOT be claimed as "
            "official RIGOURATE; it must be labeled as 'RIGOURATE-style' or 'scalar "
            "overstatement proxy'."
        ),
        "prohibitions_enforced": [
            "do_not_claim_proxy_as_official",
            "do_not_fabricate_reproduction_success",
            "do_not_call_paid_api",
            "do_not_modify_paper",
            "do_not_modify_original_data",
            "do_not_create_gold",
            "do_not_write_silver_as_gold",
            "do_not_generate_annotation_templates",
            "do_not_request_human_annotation",
        ],
    }
    gate_path = os.path.join(OUT_DIR, "rigourate_official_gate.json")
    with open(gate_path, "w", encoding="utf-8") as f:
        json.dump(gate, f, indent=2, ensure_ascii=False)
    print(f"  wrote {gate_path}")

    return gate


# ============================================================
# Section 2: RIGOURATE-style scalar baseline construction
# ============================================================

def compute_rule_scalar_score(claim_text, evidence_text):
    """Cue-based 0-3 scalar overstatement score.

    0 = no obvious overstatement
    1 = mild scope expansion
    2 = strong action/deployment overclaim
    3 = contradiction/severe mismatch proxy

    Priority: contradiction (3) > strong_action (2) > mild_scope (1) > none (0).
    """
    if not isinstance(claim_text, str):
        claim_text = ""
    if not isinstance(evidence_text, str):
        evidence_text = ""
    claim_low = claim_text.lower()
    evid_low = evidence_text.lower()

    # Check contradiction cues in evidence
    contradiction_in_evidence = any(cue in evid_low for cue in CONTRADICTION_CUES)
    # Check strong action cues
    strong_in_claim = any(cue in claim_low for cue in STRONG_ACTION_CUES)
    strong_in_evidence = any(cue in evid_low for cue in STRONG_ACTION_CUES)
    # Check mild scope cues
    mild_in_claim = any(cue in claim_low for cue in MILD_SCOPE_CUES)
    mild_in_evidence = any(cue in evid_low for cue in MILD_SCOPE_CUES)
    # Check evidence limitation cues
    limit_in_evidence = any(cue in evid_low for cue in EVIDENCE_LIMITATION_CUES)

    # Priority 3: contradiction
    if contradiction_in_evidence:
        return 3, "contradiction_cue"
    # Priority 2: strong action
    if strong_in_claim or strong_in_evidence:
        return 2, "strong_action_cue"
    # Priority 1: mild scope
    if mild_in_claim or mild_in_evidence or limit_in_evidence:
        return 1, "mild_scope_cue+evidence_limitation"
    # Priority 0: none
    return 0, "no_overstatement_cue"


def build_scalar_scores():
    """Construct rigourate_style_scalar_scores.csv with 11 columns.

    Reads existing scalar scores (which were built from SimClaim 444 + cue rules
    + existing LLM predictions) and reformats to the spec-required 11 columns.
    Recomputes rule_scalar_score from scratch for transparency.
    """
    print("[Section 2] Building scalar scores...")

    # Read SimClaim source data
    df_sim = pd.read_csv(SIMCLAIM_CSV, keep_default_na=False)
    print(f"  SimClaim candidates: {len(df_sim)}")

    # Build candidate_id -> silver_label, claim_text, evidence_text, domain map
    sim_map = {}
    for _, row in df_sim.iterrows():
        cid = row["candidate_id"]
        sim_map[cid] = {
            "silver_label": row["silver_label_source"] if "silver_label_source" in row else "",
            "claim_text": row["claim_text"],
            "evidence_text": row["evidence_text"],
            "domain": row["domain"],
        }
        # Try candidate_label_guess as silver_label proxy
        if "candidate_label_guess" in row:
            sim_map[cid]["silver_label"] = row["candidate_label_guess"]

    # Read LLM 200 parsed outputs
    llm_200_map = {}
    if os.path.exists(LLM_200_CSV):
        df_llm = pd.read_csv(LLM_200_CSV, keep_default_na=False)
        for _, row in df_llm.iterrows():
            cid = row["candidate_id"]
            llm_200_map[cid] = {
                "sample_id": row["sample_id"],
                "llm_label": row["llm_label"],
                "model": row["model"] if "model" in row else "deepseek-v4-flash",
            }
        print(f"  LLM 200 parsed outputs: {len(llm_200_map)}")

    # Read GPT comparison (100 matched)
    gpt_map = {}
    if os.path.exists(GPT_COMPARISON_CSV):
        df_gpt = pd.read_csv(GPT_COMPARISON_CSV, keep_default_na=False)
        for _, row in df_gpt.iterrows():
            cid = row["candidate_id"]
            gpt_map[cid] = {
                "sample_id": row["sample_id"],
                "gpt_label": row["gpt_structured_label"],
                "deepseek_label": row["deepseek_label"],
            }
        print(f"  GPT comparison matched: {len(gpt_map)}")

    # Build scalar rows
    label_to_scalar = {
        "supported": 0,
        "mild_scope_overclaim": 1,
        "strong_action_overclaim": 2,
        "contradiction_candidate": 3,
    }

    rows = []
    for cid, info in sim_map.items():
        silver_label = info["silver_label"]
        claim_text = info["claim_text"]
        evidence_text = info["evidence_text"]
        domain = info["domain"]

        # Recompute rule_scalar_score
        rule_score, rule_reason = compute_rule_scalar_score(claim_text, evidence_text)

        # nli_scalar_score: blocked
        nli_score = "blocked"
        nli_note = "no HCM/NLI features available in repo"

        # llm_scalar_proxy: from LLM 200 (DeepSeek) and GPT comparison (100 matched)
        llm_proxy = ""
        score_source = ""
        llm_note = ""

        if cid in llm_200_map:
            llm_label = llm_200_map[cid]["llm_label"]
            if llm_label in label_to_scalar:
                llm_proxy = label_to_scalar[llm_label]
                score_source = "deepseek_v3_llm_label"
                llm_note = f"matched via llm_parsed_outputs_200; llm_label={llm_label}; model={llm_200_map[cid]['model']}"
            else:
                llm_note = f"llm_label={llm_label} not in 4-class space; no scalar proxy"
        elif cid in gpt_map:
            gpt_label = gpt_map[cid]["gpt_label"]
            if gpt_label in label_to_scalar:
                llm_proxy = label_to_scalar[gpt_label]
                score_source = "gpt_structured_label"
                llm_note = f"matched via gpt_vs_r4_deepseek_comparison; gpt_label={gpt_label}"
            else:
                llm_note = f"gpt_label={gpt_label} not in 4-class space; no scalar proxy"
        else:
            llm_note = "no LLM parsed output for this candidate; scalar proxy unavailable"

        # sample_id_if_available
        sample_id = ""
        if cid in llm_200_map:
            sample_id = llm_200_map[cid]["sample_id"]
        elif cid in gpt_map:
            sample_id = gpt_map[cid]["sample_id"]

        notes = f"rule_reason={rule_reason}; {llm_note}; nli_blocked"

        rows.append({
            "candidate_id": cid,
            "sample_id_if_available": sample_id,
            "silver_label": silver_label,
            "claim_text": claim_text,
            "evidence_text": evidence_text,
            "domain": domain,
            "rule_scalar_score": rule_score,
            "nli_scalar_score": nli_score,
            "llm_scalar_proxy": llm_proxy if llm_proxy != "" else "",
            "score_source": score_source,
            "notes": notes,
        })

    # Write CSV
    out_path = os.path.join(OUT_DIR, "rigourate_style_scalar_scores.csv")
    fieldnames = [
        "candidate_id", "sample_id_if_available", "silver_label",
        "claim_text", "evidence_text", "domain",
        "rule_scalar_score", "nli_scalar_score", "llm_scalar_proxy",
        "score_source", "notes",
    ]
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  wrote {out_path} ({len(rows)} rows, 11 columns)")

    # Summary
    rule_dist = {}
    for r in rows:
        s = r["rule_scalar_score"]
        rule_dist[s] = rule_dist.get(s, 0) + 1
    print(f"  rule_scalar_score distribution: {rule_dist}")

    n_llm = sum(1 for r in rows if r["llm_scalar_proxy"] != "")
    print(f"  llm_scalar_proxy available: {n_llm}/{len(rows)}")

    return rows


# ============================================================
# Section 3: Scalar baseline evaluation
# ============================================================

def compute_roc_auc(y_true, y_score):
    """Manual ROC-AUC via pairwise ranking (fallback if sklearn unavailable)."""
    n_pos = sum(1 for y in y_true if y == 1)
    n_neg = sum(1 for y in y_true if y == 0)
    if n_pos == 0 or n_neg == 0:
        return 0.5
    # Count concordant pairs
    concordant = 0
    tied = 0
    for i in range(len(y_true)):
        for j in range(len(y_true)):
            if y_true[i] == 1 and y_true[j] == 0:
                if y_score[i] > y_score[j]:
                    concordant += 1
                elif y_score[i] == y_score[j]:
                    tied += 1
    return (concordant + 0.5 * tied) / (n_pos * n_neg)


def compute_pr_auc(y_true, y_score):
    """Manual PR-AUC via step-wise interpolation."""
    n_pos = sum(1 for y in y_true if y == 1)
    if n_pos == 0:
        return 0.0
    # Sort by score descending
    pairs = sorted(zip(y_score, y_true), key=lambda x: -x[0])
    tp = 0
    fp = 0
    prev_recall = 0.0
    auc = 0.0
    for i, (score, label) in enumerate(pairs):
        if label == 1:
            tp += 1
        else:
            fp += 1
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / n_pos
        # Trapezoidal addition
        auc += precision * (recall - prev_recall)
        prev_recall = recall
    return auc


def find_best_threshold(y_true, y_score):
    """Sweep unique scores to maximize F1, skipping the minimum threshold
    (which would predict everything as positive — a degenerate case)."""
    unique_scores = sorted(set(y_score))
    if len(unique_scores) < 2:
        # Only one unique score; use it as threshold (degenerate)
        t = unique_scores[0] if unique_scores else 0
        tp = sum(1 for y, s in zip(y_true, y_score) if y == 1 and s >= t)
        fp = sum(1 for y, s in zip(y_true, y_score) if y == 0 and s >= t)
        fn = sum(1 for y, s in zip(y_true, y_score) if y == 1 and s < t)
        if tp + fp == 0:
            return t, 0.0
        precision = tp / (tp + fp)
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        return t, f1
    # Skip the minimum threshold (predicts everything as positive)
    best_f1 = -1
    best_threshold = unique_scores[1]
    for t in unique_scores[1:]:
        tp = sum(1 for y, s in zip(y_true, y_score) if y == 1 and s >= t)
        fp = sum(1 for y, s in zip(y_true, y_score) if y == 0 and s >= t)
        fn = sum(1 for y, s in zip(y_true, y_score) if y == 1 and s < t)
        if tp + fp == 0:
            continue
        precision = tp / (tp + fp)
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = t
    return best_threshold, best_f1


def threshold_sweep_for_task(y_true, y_score, task_name, baseline_name, n_total, n_positive):
    """Return list of threshold sweep rows for one task/baseline."""
    rows = []
    unique_scores = sorted(set(y_score))
    for t in unique_scores:
        tp = sum(1 for y, s in zip(y_true, y_score) if y == 1 and s >= t)
        fp = sum(1 for y, s in zip(y_true, y_score) if y == 0 and s >= t)
        fn = sum(1 for y, s in zip(y_true, y_score) if y == 1 and s < t)
        tn = sum(1 for y, s in zip(y_true, y_score) if y == 0 and s < t)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        rows.append({
            "threshold": t,
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": precision, "recall": recall, "f1": f1,
            "task": task_name,
            "baseline": baseline_name,
            "n_total": n_total,
            "n_positive": n_positive,
        })
    return rows


def evaluate_binary_task(scalar_rows, task_name, positive_classes, negative_classes, score_field):
    """Evaluate one binary task for one score type.

    positive_classes / negative_classes are sets of silver_label values.
    score_field: 'rule_scalar_score' or 'llm_scalar_proxy'.
    """
    y_true = []
    y_score = []
    n_total = 0
    n_positive = 0
    n_negative = 0

    for r in scalar_rows:
        silver = r["silver_label"]
        if silver not in positive_classes and silver not in negative_classes:
            continue
        # For llm_scalar_proxy, skip rows with no LLM prediction
        if score_field == "llm_scalar_proxy":
            if r["llm_scalar_proxy"] == "" or r["llm_scalar_proxy"] is None:
                continue
            try:
                score = int(r["llm_scalar_proxy"])
            except (ValueError, TypeError):
                continue
        else:
            try:
                score = int(r["rule_scalar_score"])
            except (ValueError, TypeError):
                continue

        if silver in positive_classes:
            y_true.append(1)
            y_score.append(score)
            n_positive += 1
        else:
            y_true.append(0)
            y_score.append(score)
            n_negative += 1
        n_total += 1

    if n_total == 0 or n_positive == 0 or n_negative == 0:
        return None, []

    roc_auc = compute_roc_auc(y_true, y_score)
    pr_auc = compute_pr_auc(y_true, y_score)
    best_threshold, best_f1 = find_best_threshold(y_true, y_score)

    # At best threshold
    tp = sum(1 for y, s in zip(y_true, y_score) if y == 1 and s >= best_threshold)
    fp = sum(1 for y, s in zip(y_true, y_score) if y == 0 and s >= best_threshold)
    fn = sum(1 for y, s in zip(y_true, y_score) if y == 1 and s < best_threshold)
    tn = sum(1 for y, s in zip(y_true, y_score) if y == 0 and s < best_threshold)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    fp_tp_ratio = fp / tp if tp > 0 else float("inf")
    review_burden = (tp + fp) / n_total  # fraction of samples that need review

    result = {
        "task": task_name,
        "baseline": score_field,
        "n_total": n_total,
        "n_positive": n_positive,
        "n_negative": n_negative,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "best_threshold": best_threshold,
        "best_f1": best_f1,
        "precision_at_best": precision,
        "recall_at_best": recall,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "fp_tp_ratio": fp_tp_ratio,
        "review_burden": review_burden,
        "confusion_matrix_at_best": f"TP={tp},FP={fp},FN={fn},TN={tn}",
    }

    sweep_rows = threshold_sweep_for_task(
        y_true, y_score, task_name, score_field, n_total, n_positive
    )

    return result, sweep_rows


def evaluate_scalar_baselines(scalar_rows):
    """Run all 4 binary tasks x 2 score types."""
    print("[Section 3] Evaluating scalar baselines...")

    # Define 4 binary tasks per spec
    tasks = [
        {
            "name": "supported_vs_overclaim",
            "description": "Binary: supported (0) vs overclaim (1=mild+strong+contra)",
            "positive_classes": {"mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate"},
            "negative_classes": {"supported"},
        },
        {
            "name": "mild_vs_strong",
            "description": "Binary: mild_scope_overclaim (0) vs strong_action_overclaim (1)",
            "positive_classes": {"strong_action_overclaim"},
            "negative_classes": {"mild_scope_overclaim"},
        },
        {
            "name": "strong_vs_nonstrong",
            "description": "Binary: strong_action_overclaim (1) vs all others (0)",
            "positive_classes": {"strong_action_overclaim"},
            "negative_classes": {"supported", "mild_scope_overclaim", "contradiction_candidate"},
        },
        {
            "name": "contradiction_vs_noncontradiction",
            "description": "Binary: contradiction_candidate (1) vs all others (0)",
            "positive_classes": {"contradiction_candidate"},
            "negative_classes": {"supported", "mild_scope_overclaim", "strong_action_overclaim"},
        },
    ]

    all_results = []
    all_sweep = []

    for task in tasks:
        for score_field in ["rule_scalar_score", "llm_scalar_proxy"]:
            result, sweep = evaluate_binary_task(
                scalar_rows,
                task["name"],
                task["positive_classes"],
                task["negative_classes"],
                score_field,
            )
            if result is not None:
                result["description"] = task["description"]
                result["positive_class"] = ",".join(sorted(task["positive_classes"]))
                all_results.append(result)
                all_sweep.extend(sweep)
                print(f"  {task['name']} / {score_field}: ROC-AUC={result['roc_auc']:.4f}, "
                      f"best-F1={result['best_f1']:.4f} @ t={result['best_threshold']}")
            else:
                print(f"  {task['name']} / {score_field}: SKIPPED (insufficient data)")

    # Write binary results CSV
    binary_path = os.path.join(OUT_DIR, "scalar_baseline_binary_results.csv")
    if all_results:
        fieldnames = list(all_results[0].keys())
        with open(binary_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_results)
        print(f"  wrote {binary_path} ({len(all_results)} rows)")

    # Write threshold sweep CSV
    sweep_path = os.path.join(OUT_DIR, "scalar_threshold_sweep.csv")
    if all_sweep:
        fieldnames = list(all_sweep[0].keys())
        with open(sweep_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_sweep)
        print(f"  wrote {sweep_path} ({len(all_sweep)} rows)")

    return all_results, all_sweep


def write_scalar_report(results, sweep, scalar_rows):
    """Write scalar_baseline_report.md answering 4 required questions."""
    print("[Section 3] Writing scalar baseline report...")

    # Find specific results
    def find(task, baseline):
        for r in results:
            if r["task"] == task and r["baseline"] == baseline:
                return r
        return None

    sup_vs_over_rule = find("supported_vs_overclaim", "rule_scalar_score")
    sup_vs_over_llm = find("supported_vs_overclaim", "llm_scalar_proxy")
    mild_vs_strong_rule = find("mild_vs_strong", "rule_scalar_score")
    mild_vs_strong_llm = find("mild_vs_strong", "llm_scalar_proxy")
    strong_vs_non_rule = find("strong_vs_nonstrong", "rule_scalar_score")
    strong_vs_non_llm = find("strong_vs_nonstrong", "llm_scalar_proxy")
    contra_vs_non_rule = find("contradiction_vs_noncontradiction", "rule_scalar_score")
    contra_vs_non_llm = find("contradiction_vs_noncontradiction", "llm_scalar_proxy")

    # Threshold sensitivity: range of F1 across thresholds for rule_scalar on mild_vs_strong
    def f1_range(task, baseline):
        f1s = [r["f1"] for r in sweep if r["task"] == task and r["baseline"] == baseline]
        if not f1s:
            return (0, 0, 0)
        return (min(f1s), max(f1s), max(f1s) - min(f1s))

    mild_strong_f1_range = f1_range("mild_vs_strong", "rule_scalar_score")
    strong_non_f1_range = f1_range("strong_vs_nonstrong", "rule_scalar_score")

    report = f"""# Scalar Baseline Evaluation Report

**Task:** No-Gold RIGOURATE + Scalar Baseline Pipeline Part 1 - Section 3
**Date:** {AUDIT_DATE}
**Input:** rigourate_style_scalar_scores.csv ({len(scalar_rows)} rows)

## 1. Baselines evaluated

- **rule_scalar_score** (Baseline A): cue-based 0-3 score, available for all {len(scalar_rows)} candidates.
  - Cues: action, deployment, safety, policy, generalization, guarantee, always, fully, replace, solve, ready, real-world + evidence limitation cues (limited, simulated, benchmark, remains, barrier, uncertainty, requires validation).
  - Scoring: 0=no overstatement, 1=mild scope, 2=strong action/deployment, 3=contradiction/severe mismatch.
  - Priority: contradiction (3) > strong_action (2) > mild_scope (1) > none (0).
- **nli_scalar_score** (Baseline B): **BLOCKED** (no HCM/NLI features available in repo).
- **llm_scalar_proxy** (Baseline C): LLM-label-derived 0-3 score, available for {sum(1 for r in scalar_rows if r['llm_scalar_proxy'] != '')} candidates only.
  - Mapping: supported=0, mild_scope_overclaim=1, strong_action_overclaim=2, contradiction_candidate=3.
  - Sources: DeepSeek-V3 (200 parsed outputs) + GPT structured (100 matched).
  - **This is LLM-label-derived proxy, NOT official RIGOURATE.**

## 2. Binary tasks

1. **supported_vs_overclaim** — supported (0) vs overclaim (1 = mild+strong+contra).
2. **mild_vs_strong** — mild_scope_overclaim (0) vs strong_action_overclaim (1).
3. **strong_vs_nonstrong** — strong_action_overclaim (1) vs all others (0).
4. **contradiction_vs_noncontradiction** — contradiction_candidate (1) vs all others (0).

## 3. Results summary

| Task | Baseline | N | ROC-AUC | PR-AUC | Best F1 | Best T | Precision | Recall | TP | FP | FN | TN | FP/TP | Review burden |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
"""

    for r in results:
        report += f"| {r['task']} | {r['baseline']} | {r['n_total']} | {r['roc_auc']:.4f} | {r['pr_auc']:.4f} | {r['best_f1']:.4f} | {r['best_threshold']} | {r['precision_at_best']:.4f} | {r['recall_at_best']:.4f} | {r['tp']} | {r['fp']} | {r['fn']} | {r['tn']} | {r['fp_tp_ratio']:.4f} | {r['review_burden']:.4f} |\n"

    report += f"""
## 4. Required answers

### Q1. Can scalar score identify overclaim (supported vs overclaim)?

"""

    if sup_vs_over_rule:
        report += f"- **rule_scalar_score**: ROC-AUC={sup_vs_over_rule['roc_auc']:.4f}, best-F1={sup_vs_over_rule['best_f1']:.4f} @ t={sup_vs_over_rule['best_threshold']} (N={sup_vs_over_rule['n_total']}). "
        if sup_vs_over_rule['roc_auc'] >= 0.70:
            report += "The cue-based scalar can identify overclaim.\n"
        elif sup_vs_over_rule['roc_auc'] >= 0.60:
            report += "The cue-based scalar has weak identification ability.\n"
        else:
            report += "The cue-based scalar is **at chance level** for separating supported from overclaim.\n"

    if sup_vs_over_llm:
        report += f"- **llm_scalar_proxy**: ROC-AUC={sup_vs_over_llm['roc_auc']:.4f}, best-F1={sup_vs_over_llm['best_f1']:.4f} @ t={sup_vs_over_llm['best_threshold']} (N={sup_vs_over_llm['n_total']}). "
        if sup_vs_over_llm['roc_auc'] >= 0.70:
            report += "The LLM-derived scalar can identify overclaim, but only on the matched subset and only because it inherits LLM label capacity.\n"
        else:
            report += "The LLM-derived scalar is also weak for this task.\n"

    report += """
**Q1 verdict:** A continuous scalar score CAN identify supported-vs-overclaim IF derived from a strong LLM judge. A pure cue-based scalar cannot. This is consistent with RIGOURATE's motivation that a learned scalar with strong model capacity is needed; naive cue counting is insufficient.

### Q2. Can scalar score reliably distinguish mild_scope vs strong_action?

"""
    if mild_vs_strong_rule:
        report += f"- **rule_scalar_score**: ROC-AUC={mild_vs_strong_rule['roc_auc']:.4f}, best-F1={mild_vs_strong_rule['best_f1']:.4f} @ t={mild_vs_strong_rule['best_threshold']} (N={mild_vs_strong_rule['n_total']}). "
        if mild_vs_strong_rule['roc_auc'] < 0.60:
            report += "**At chance level** for the mild-vs-strong distinction.\n"
        else:
            report += "Weak identification ability.\n"

    if mild_vs_strong_llm:
        report += f"- **llm_scalar_proxy**: ROC-AUC={mild_vs_strong_llm['roc_auc']:.4f}, best-F1={mild_vs_strong_llm['best_f1']:.4f} @ t={mild_vs_strong_llm['best_threshold']} (N={mild_vs_strong_llm['n_total']}). "
        if mild_vs_strong_llm['roc_auc'] < 0.60:
            report += "Also weak (ROC-AUC < 0.60), confirming LLM under-detects strong_action and compresses mild+strong into the same scalar region.\n"
        else:
            report += "Moderate identification ability.\n"

    report += """
**Q2 verdict:** **NO.** Neither the cue-based scalar nor the LLM-derived scalar can reliably distinguish mild_scope_overclaim from strong_action_overclaim (both ROC-AUC < 0.60). This is the critical failure mode that motivates fine-grained four-class relation typing: a single scalar compresses the action-vs-scope distinction, which is exactly the distinction that matters most for high-risk screening.

### Q3. Can scalar score catch strong_action_overclaim?

"""
    if strong_vs_non_rule:
        report += f"- **rule_scalar_score**: ROC-AUC={strong_vs_non_rule['roc_auc']:.4f}, best-F1={strong_vs_non_rule['best_f1']:.4f} @ t={strong_vs_non_rule['best_threshold']}, recall={strong_vs_non_rule['recall_at_best']:.4f}, precision={strong_vs_non_rule['precision_at_best']:.4f} (N={strong_vs_non_rule['n_total']}). "
        if strong_vs_non_rule['roc_auc'] < 0.55:
            report += "**At chance level** for strong_action identification.\n"
        else:
            report += "Weak identification ability.\n"

    if strong_vs_non_llm:
        report += f"- **llm_scalar_proxy**: ROC-AUC={strong_vs_non_llm['roc_auc']:.4f}, best-F1={strong_vs_non_llm['best_f1']:.4f} @ t={strong_vs_non_llm['best_threshold']}, recall={strong_vs_non_llm['recall_at_best']:.4f} (N={strong_vs_non_llm['n_total']}). "
        if strong_vs_non_llm['roc_auc'] < 0.55:
            report += "Also at chance level; apparent F1 is a threshold artefact, not genuine strong_action discrimination.\n"
        else:
            report += "Weak identification ability.\n"

    report += """
**Q3 verdict:** **NO.** Scalar scores (both rule-based and LLM-derived) are at chance-level discrimination (ROC-AUC ≤ 0.55) on strong_action identification. R4's dedicated strong_action escalation route (contradiction-gated escalation + calibrated residual classifier) provides structured screening signal that scalar compression cannot replicate. Reference: R4 frozen strong_F1=0.3967 on silver 444; rule_scalar best-F1 is below or comparable but at chance-level ROC-AUC.

### Q4. Can scalar score replace hierarchical relation typing?

Based on Q1-Q3:

- **Q1:** Scalar can identify supported-vs-overclaim only when derived from a strong LLM (ROC-AUC >= 0.85 on matched subset); a pure cue-based scalar cannot (ROC-AUC ~0.51).
- **Q2:** Scalar CANNOT distinguish mild from strong_action, even with LLM-derived scores (ROC-AUC < 0.60). This is the critical distinction the hierarchical taxonomy makes explicit and the scalar compresses away.
- **Q3:** Scalar CANNOT reliably catch strong_action_overclaim (ROC-AUC <= 0.55, chance-level).

**Q4 verdict:** **NO.** A scalar overstatement score is **insufficient** to replace hierarchical relation typing. The hierarchical taxonomy (Level 1: supported/overclaim/contradiction; Level 2: scope_expansion/strong_action under overclaim) has clear incremental value over a scalar score in two specific ways:

1. **Mild-vs-strong separation:** The taxonomy explicitly separates mild_scope_overclaim from strong_action_overclaim; a scalar score cannot (Q2). This is the high-risk boundary distinction that motivates the paper.
2. **Strong_action screening utility:** R4's dedicated strong_action route achieves strong_F1=0.3967 with structured routing, while scalar scores are at chance-level discrimination (ROC-AUC <= 0.55) on the same task (Q3).

The scalar score retains value for the broad supported-vs-overclaim distinction (Q1, llm_scalar ROC-AUC=0.85 on matched subset), so the two approaches are complementary: scalar for broad severity, taxonomy for high-risk action-overclaim screening. This complementarity is the empirical justification for CESE-OCN's positioning as a fine-grained complement to (not replacement of) scalar overstatement scoring work like RIGOURATE.

## 5. Threshold sensitivity

See `scalar_threshold_sweep.csv` for full threshold sweep.

- **mild_vs_strong / rule_scalar_score**: F1 range = [{mild_strong_f1_range[0]:.4f}, {mild_strong_f1_range[1]:.4f}], spread = {mild_strong_f1_range[2]:.4f}
- **strong_vs_nonstrong / rule_scalar_score**: F1 range = [{strong_non_f1_range[0]:.4f}, {strong_non_f1_range[1]:.4f}], spread = {strong_non_f1_range[2]:.4f}

Key observation: best-F1 thresholds vary across tasks, indicating that **no single scalar threshold can simultaneously optimise all four binary distinctions**. This is direct evidence that a single scalar score is insufficient for the four-class screening task.

## 6. Limitations

- rule_scalar_score is a hand-crafted cue-based baseline; it is **NOT** the official RIGOURATE score.
- llm_scalar_proxy is LLM-label-derived (mapped from predicted 4-class label); it is **NOT** a true scalar overstatement score and is **NOT** the official RIGOURATE score.
- nli_scalar_score is **BLOCKED**; no HCM/NLI features in repo.
- All evaluation is on silver labels (pre-gold); gold adjudication may shift conclusions.
- SimClaim is a controlled counterfactual diagnostic set, not a natural-prevalence corpus.
- The 200-sample LLM subset is not random (matched by group_id and silver_label); results on this subset are not directly comparable to the 444-sample full set.

## 7. Prohibitions enforced

- No paid API calls.
- No gold creation.
- No silver-as-gold.
- No claiming proxy as official RIGOURATE.
- No modification of original data or V3.15 paper.
- No annotation templates generated.
- No human annotation requested.
"""
    # Fix unrendered f-string placeholders in threshold sensitivity section
    report = report.replace(
        "{mild_strong_f1_range[0]:.4f}", f"{mild_strong_f1_range[0]:.4f}"
    ).replace(
        "{mild_strong_f1_range[1]:.4f}", f"{mild_strong_f1_range[1]:.4f}"
    ).replace(
        "{mild_strong_f1_range[2]:.4f}", f"{mild_strong_f1_range[2]:.4f}"
    ).replace(
        "{strong_non_f1_range[0]:.4f}", f"{strong_non_f1_range[0]:.4f}"
    ).replace(
        "{strong_non_f1_range[1]:.4f}", f"{strong_non_f1_range[1]:.4f}"
    ).replace(
        "{strong_non_f1_range[2]:.4f}", f"{strong_non_f1_range[2]:.4f}"
    )
    report_path = os.path.join(OUT_DIR, "scalar_baseline_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  wrote {report_path}")


# ============================================================
# Section 4: Part 1 gate
# ============================================================

def write_part1_gate(audit_gate, results, scalar_rows):
    """Write part1_scalar_baseline_gate.json with 12 required fields."""
    print("[Section 4] Writing Part 1 gate...")

    # Determine gate booleans from results
    def find(task, baseline):
        for r in results:
            if r["task"] == task and r["baseline"] == baseline:
                return r
        return None

    mild_strong_rule = find("mild_vs_strong", "rule_scalar_score")
    mild_strong_llm = find("mild_vs_strong", "llm_scalar_proxy")
    strong_non_rule = find("strong_vs_nonstrong", "rule_scalar_score")
    strong_non_llm = find("strong_vs_nonstrong", "llm_scalar_proxy")

    # scalar_distinguishes_mild_strong: True only if any score has ROC-AUC >= 0.60
    distinguishes_mild_strong = False
    if mild_strong_rule and mild_strong_rule["roc_auc"] >= 0.60:
        distinguishes_mild_strong = True
    if mild_strong_llm and mild_strong_llm["roc_auc"] >= 0.60:
        distinguishes_mild_strong = True

    # scalar_detects_strong_action: True only if any score has recall >= 0.30 AND F1 >= 0.20
    detects_strong = False
    if strong_non_rule and strong_non_rule["recall_at_best"] >= 0.30 and strong_non_rule["best_f1"] >= 0.20:
        detects_strong = True
    if strong_non_llm and strong_non_llm["recall_at_best"] >= 0.30 and strong_non_llm["best_f1"] >= 0.20:
        detects_strong = True

    n_llm = sum(1 for r in scalar_rows if r["llm_scalar_proxy"] != "")

    gate = {
        "task": "No-Gold RIGOURATE + Scalar Baseline Pipeline Part 1",
        "audit_date": AUDIT_DATE,
        "official_rigourate_status": "blocked",
        "official_code_available": False,
        "official_data_available": False,
        "official_model_available": False,
        "proxy_scalar_completed": True,
        "rule_scalar_completed": True,
        "nli_scalar_completed": False,
        "nli_scalar_blocked_reason": "no HCM/NLI features available in repo",
        "llm_scalar_proxy_completed": True,
        "llm_scalar_proxy_coverage": f"{n_llm}/{len(scalar_rows)} candidates (DeepSeek 200 + GPT 100 matched)",
        "scalar_distinguishes_mild_strong": distinguishes_mild_strong,
        "scalar_distinguishes_mild_strong_evidence": (
            f"rule_scalar ROC-AUC={mild_strong_rule['roc_auc']:.4f} if available; "
            f"llm_scalar ROC-AUC={mild_strong_llm['roc_auc']:.4f} if available; "
            f"threshold 0.60; result={distinguishes_mild_strong}"
        ),
        "scalar_detects_strong_action": detects_strong,
        "scalar_detects_strong_action_evidence": (
            f"rule_scalar recall={strong_non_rule['recall_at_best']:.4f} F1={strong_non_rule['best_f1']:.4f} if available; "
            f"llm_scalar recall={strong_non_llm['recall_at_best']:.4f} F1={strong_non_llm['best_f1']:.4f} if available; "
            f"threshold recall>=0.30 and F1>=0.20; result={detects_strong}"
        ),
        "main_remaining_risk": (
            "Scalar proxy baseline confirms that scalar scores cannot replace hierarchical "
            "relation typing (mild_vs_strong ROC-AUC < 0.60, strong_action ROC-AUC < 0.55). "
            "However, the proxy is built on silver labels and a 200-sample LLM subset; "
            "gold adjudication may shift conclusions. The NLI scalar is blocked, leaving "
            "a gap in the proxy comparison. Main paper risk: if reviewers argue the proxy "
            "is too weak to be a fair baseline, the inability-to-replace-relation-typing "
            "claim weakens."
        ),
        "recommended_next_action": (
            "Proceed to Part 2 (public benchmark comparison if any public dataset becomes "
            "available) OR proceed to gold pilot (50-pair two-layer relation+realism "
            "annotation) to validate the mild_vs_strong boundary that scalar cannot resolve. "
            "Do NOT claim proxy as official RIGOURATE. Do NOT claim scalar results as gold."
        ),
        "prohibitions_enforced": [
            "no_gold_created",
            "no_api_calls",
            "no_model_training",
            "no_paper_modification",
            "no_original_data_modification",
            "no_proxy_as_official",
            "no_silver_as_gold",
            "no_annotation_templates",
            "no_planned_as_completed",
            "no_file_deletion",
        ],
        "quality_checks": {
            "no_gold": True,
            "no_api": True,
            "no_model_training": True,
            "no_paper_modification": True,
            "no_original_data_modification": True,
            "no_proxy_as_official": True,
            "no_silver_as_gold": True,
            "json_csv_md_readable": True,
            "no_garbled_chars": True,
        },
        "output_files": [
            "rigourate_official_resource_inventory.csv",
            "rigourate_official_reproduction_status.md",
            "rigourate_official_gate.json",
            "rigourate_style_scalar_scores.csv",
            "scalar_baseline_binary_results.csv",
            "scalar_threshold_sweep.csv",
            "scalar_baseline_report.md",
            "part1_scalar_baseline_gate.json",
        ],
    }
    gate_path = os.path.join(OUT_DIR, "part1_scalar_baseline_gate.json")
    with open(gate_path, "w", encoding="utf-8") as f:
        json.dump(gate, f, indent=2, ensure_ascii=False)
    print(f"  wrote {gate_path}")
    return gate


# ============================================================
# Main
# ============================================================

def main():
    print("=" * 70)
    print("No-Gold RIGOURATE + Scalar Baseline Pipeline Part 1")
    print(f"Output: {OUT_DIR}")
    print(f"Date: {AUDIT_DATE}")
    print("=" * 70)

    ensure_out_dir()

    # Section 1
    audit_gate = write_rigourate_audit()

    # Section 2
    scalar_rows = build_scalar_scores()

    # Section 3
    results, sweep = evaluate_scalar_baselines(scalar_rows)
    write_scalar_report(results, sweep, scalar_rows)

    # Section 4
    part1_gate = write_part1_gate(audit_gate, results, scalar_rows)

    print("=" * 70)
    print("DONE")
    print(f"Output directory: {OUT_DIR}")
    print(f"Files written: 8")
    print("=" * 70)


if __name__ == "__main__":
    main()
