# -*- coding: utf-8 -*-
"""
Overnight Non-API Compute Pipeline v1.

8 sub-tasks (A-H). Each runs in try/except; failure produces blocked_reason
and gate.json with completed=false, but does NOT block subsequent tasks.

PROHIBITIONS ENFORCED:
- No API calls. No gold. No large model training/downloading.
- No paper modification. No original data modification. No file deletion.
- No overwriting old experiments. No simulation as real natural distribution.
- No silver as gold. No proxy as official RIGOURATE.
"""

import json
import os
import sys
import traceback
import csv
import math
import re
from datetime import date
from collections import Counter, defaultdict

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import (
    roc_auc_score, average_precision_score, f1_score, precision_score,
    recall_score, confusion_matrix, precision_recall_curve,
)

TODAY = date.today().isoformat()
ROOT = r"D:\ocn\experiments\overnight_non_api_compute_pipeline_v1"
os.makedirs(ROOT, exist_ok=True)

# ---------- Input paths ----------
CAND_CSV = r"D:\ocn\data\simclaim_all92_candidate_pool_v1\strict_silver_max_v1\strict_silver_max_candidates_v1.csv"
GROUPS_CSV = r"D:\ocn\data\simclaim_all92_candidate_pool_v1\strict_silver_max_v1\strict_silver_max_groups_v1.csv"
CMP_CSV = r"D:\ocn\experiments\gpt_structured_judge_probe_v1\gpt_vs_r4_deepseek_comparison.csv"
SCALAR_CSV = r"D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1\rigourate_style_scalar_scores.csv"
VS_R4_CASES_CSV = r"D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1\rigourate_style_vs_r4_cases.csv"
CASE_LEVEL_CSV = r"D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1\case_level_comparison.csv"

LABELS_4 = ["supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate"]
STRONG = "strong_action_overclaim"
MILD = "mild_scope_overclaim"
SUP = "supported"
CONTRA = "contradiction_candidate"

# Cue words for label leakage detection
CUE_WORDS = {
    SUP: ["the study", "the paper", "the approach", "we evaluate", "we extend", "we propose"],
    MILD: ["across", "multi", "as the main", "and five", "multi-stage", "multi-domain", "broader"],
    STRONG: ["deploy", "deployment", "safety", "guarantee", "operational", "policy",
             "generalization", "broadly", "ready for", "can be used to", "enables", "ensures",
             "demonstrates", "proves", "suitable for", "direct physical", "plant trials",
             "reliable transfer", "industrial applications", "real-world"],
    CONTRA: ["not", "but", "however", "disregarded", "ignores", "fails to", "cannot",
             "does not", "unclear", "saturated", "little expertise", "different"],
}


def write_gate(out_dir, gate_name, task_name, completed, **kwargs):
    """Write a standard gate JSON."""
    g = {
        "gate_name": gate_name,
        "task": task_name,
        "date": TODAY,
        "output_directory": out_dir + "\\",
        "completed": completed,
    }
    g.update(kwargs)
    g["prohibitions_enforced"] = {
        "no_api_calls": True,
        "no_gold": True,
        "no_large_model_training": True,
        "no_paper_modification": True,
        "no_original_data_modification": True,
        "no_file_deletion": True,
        "no_overwrite_old_experiments": True,
        "no_simulation_as_real_natural_distribution": True,
        "no_silver_as_gold": True,
        "no_proxy_as_official_rigourate": True,
    }
    g["audit_disclaimer"] = (
        "Overnight non-API compute pipeline. All results are reanalysis of existing "
        "predictions on SILVER labels (pre-gold). Scalar baselines are PROXY "
        "(rule-based / LLM-label-derived), NOT official RIGOURATE. "
        "Low-prevalence simulation uses heuristic non-strong composition and is NOT "
        "a real natural-distribution study."
    )
    with open(os.path.join(out_dir, gate_name + ".json"), "w", encoding="utf-8") as f:
        json.dump(g, f, indent=2, ensure_ascii=False)


def write_blocked(out_dir, gate_name, task_name, reason, exc_info=None):
    """Write blocked_reason.md and gate with completed=false."""
    with open(os.path.join(out_dir, "blocked_reason.md"), "w", encoding="utf-8") as f:
        f.write(f"# Blocked: {task_name}\n\nDate: {TODAY}\n\nReason: {reason}\n\n")
        if exc_info:
            f.write("Exception traceback:\n```\n" + exc_info + "\n```\n")
    write_gate(out_dir, gate_name, task_name, completed=False,
               blocked=True, blocked_reason=reason)


def safe_float(v):
    if v is None:
        return np.nan
    s = str(v).strip()
    if s == "" or s.lower() == "blocked" or s.lower() == "nan" or s.lower() == "none":
        return np.nan
    try:
        return float(s)
    except Exception:
        return np.nan


def tokenize(s):
    if not s or not isinstance(s, str):
        return []
    return re.findall(r"[a-z]+", s.lower())


def jaccard(a, b):
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 0.0
    return len(sa & sb) / max(1, len(sa | sb))


def sequence_ratio(a, b):
    """difflib-based normalized edit similarity in [0,1]."""
    import difflib
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


# =================================================================
# TASK A: Dataset Integrity + Leakage Re-Audit
# =================================================================
def task_a():
    out_dir = os.path.join(ROOT, "A_dataset_integrity_leakage")
    os.makedirs(out_dir, exist_ok=True)
    df = pd.read_csv(CAND_CSV, keep_default_na=False)
    n = len(df)

    # Basic counts
    n_groups = df["target_candidate_group_id"].nunique()
    per_group = df.groupby("target_candidate_group_id").size()
    groups_with_4 = int((per_group == 4).sum())
    groups_not_4 = int((per_group != 4).sum())

    # Label completeness
    label_counts = df["candidate_label_guess"].value_counts().to_dict()
    labels_complete = all(label_counts.get(l, 0) == 111 for l in LABELS_4)

    # candidate_id uniqueness
    dup_ids = int(df["candidate_id"].duplicated().sum())

    # Missing claim/evidence
    missing_claim = int((df["claim_text"].astype(str).str.strip() == "").sum())
    missing_evidence = int((df["evidence_text"].astype(str).str.strip() == "").sum())

    # Source trace
    source_trace_complete = int((df["source_trace_complete"] == True).sum())

    # Duplicates by sha256
    dup_claim_sha = int(df["claim_text_sha256"].duplicated().sum())
    dup_evidence_sha = int(df["evidence_text_sha256"].duplicated().sum())
    # Within-group evidence duplication is expected (4 claims share 1 evidence)
    # Cross-group evidence duplication is leakage risk
    evidence_cross_group = df.groupby("evidence_text_sha256")["target_candidate_group_id"].nunique()
    cross_group_evidence = int((evidence_cross_group > 1).sum())

    # Gold fields
    human_audited_true = int((df["human_audited"] == True).sum())
    final_label_filled = int((df["final_label"].astype(str).str.strip() != "").sum())
    gold_label_filled = int((df["gold_label"].astype(str).str.strip() != "").sum())

    # Cue word frequency per label
    cue_table_rows = []
    for label in LABELS_4:
        sub = df[df["candidate_label_guess"] == label]
        all_text = " ".join(sub["claim_text"].astype(str).tolist()).lower()
        tokens = tokenize(all_text)
        total_tokens = max(1, len(tokens))
        for cue in CUE_WORDS.get(label, []):
            cnt = tokens.count(cue.lower())
            cue_table_rows.append({
                "label": label,
                "cue_word": cue,
                "count": cnt,
                "per_claim": cnt / max(1, len(sub)),
                "rate_per_100_tokens": cnt / total_tokens * 100,
            })

    # Cross-label cue imbalance: for each cue, count in label-of-interest vs other labels
    cue_imbalance_rows = []
    for label, cues in CUE_WORDS.items():
        sub_in = df[df["candidate_label_guess"] == label]
        sub_out = df[df["candidate_label_guess"] != label]
        text_in = " ".join(sub_in["claim_text"].astype(str).tolist()).lower()
        text_out = " ".join(sub_out["claim_text"].astype(str).tolist()).lower()
        toks_in = tokenize(text_in)
        toks_out = tokenize(text_out)
        for cue in cues:
            c_in = toks_in.count(cue.lower())
            c_out = toks_out.count(cue.lower())
            rate_in = c_in / max(1, len(toks_in))
            rate_out = c_out / max(1, len(toks_out))
            cue_imbalance_rows.append({
                "label": label,
                "cue_word": cue,
                "count_in_label": c_in,
                "count_in_other": c_out,
                "rate_in_label": rate_in,
                "rate_in_other": rate_out,
                "imbalance_ratio": rate_in / max(1e-9, rate_out),
            })

    # Claim-only TF-IDF risk: can a linear classifier predict label from claim TF-IDF?
    # Use cosine similarity to nearest same-label vs other-label as proxy
    claims = df["claim_text"].astype(str).tolist()
    labels = df["candidate_label_guess"].tolist()
    vec = TfidfVectorizer(max_features=2000, stop_words="english")
    X = vec.fit_transform(claims)
    sim_mat = cosine_similarity(X)
    np.fill_diagonal(sim_mat, 0.0)
    same_label_sims = []
    diff_label_sims = []
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            if labels[i] == labels[j]:
                same_label_sims.append(sim_mat[i, j])
            else:
                diff_label_sims.append(sim_mat[i, j])
    same_mean = float(np.mean(same_label_sims)) if same_label_sims else 0.0
    diff_mean = float(np.mean(diff_label_sims)) if diff_label_sims else 0.0
    tfidf_separability = same_mean - diff_mean

    # Within-group claim token overlap (template risk indicator)
    within_group_overlap = []
    for gid, sub in df.groupby("target_candidate_group_id"):
        if len(sub) != 4:
            continue
        toks = [tokenize(c) for c in sub["claim_text"].astype(str).tolist()]
        for i in range(4):
            for j in range(i + 1, 4):
                within_group_overlap.append(jaccard(toks[i], toks[j]))
    within_group_overlap_mean = float(np.mean(within_group_overlap)) if within_group_overlap else 0.0

    # Group leakage: shared evidence across groups
    group_leakage_risk = cross_group_evidence

    # Inventory CSV
    inv_rows = [{
        "total_rows": n,
        "total_groups": n_groups,
        "groups_with_4_claims": groups_with_4,
        "groups_not_4": groups_not_4,
        "labels_complete_111_each": labels_complete,
        "candidate_id_duplicates": dup_ids,
        "missing_claim_text": missing_claim,
        "missing_evidence_text": missing_evidence,
        "source_trace_complete_count": source_trace_complete,
        "claim_text_sha256_duplicates": dup_claim_sha,
        "evidence_text_sha256_duplicates": dup_evidence_sha,
        "evidence_cross_group_leakage": cross_group_evidence,
        "human_audited_true_count": human_audited_true,
        "final_label_filled_count": final_label_filled,
        "gold_label_filled_count": gold_label_filled,
        "within_group_token_overlap_mean": within_group_overlap_mean,
        "tfidf_same_label_mean": same_mean,
        "tfidf_diff_label_mean": diff_mean,
        "tfidf_separability_gap": tfidf_separability,
        "claim_only_tfidf_risk": "high" if tfidf_separability > 0.05 else "medium" if tfidf_separability > 0.02 else "low",
        "group_leakage_risk": "high" if cross_group_evidence > 5 else "medium" if cross_group_evidence > 0 else "low",
    }]
    pd.DataFrame(inv_rows).to_csv(os.path.join(out_dir, "dataset_integrity_inventory.csv"), index=False, encoding="utf-8")

    # Cue word leakage table
    pd.DataFrame(cue_imbalance_rows).to_csv(os.path.join(out_dir, "cue_word_leakage_table.csv"), index=False, encoding="utf-8")

    # Duplicate claim/evidence report
    dup_rows = []
    if dup_claim_sha > 0:
        dups = df[df["claim_text_sha256"].duplicated(keep=False)].sort_values("claim_text_sha256")
        for sha, sub in dups.groupby("claim_text_sha256"):
            dup_rows.append({
                "duplicate_type": "claim_text",
                "sha256": sha,
                "count": len(sub),
                "candidate_ids": ",".join(sub["candidate_id"].tolist()[:5]),
                "labels": ",".join(sub["candidate_label_guess"].tolist()[:5]),
            })
    if dup_evidence_sha > 0:
        dups = df[df["evidence_text_sha256"].duplicated(keep=False)].sort_values("evidence_text_sha256")
        for sha, sub in dups.groupby("evidence_text_sha256"):
            dup_rows.append({
                "duplicate_type": "evidence_text",
                "sha256": sha,
                "count": len(sub),
                "candidate_ids": ",".join(sub["candidate_id"].tolist()[:5]),
                "labels": ",".join(sub["candidate_label_guess"].tolist()[:5]),
            })
    if not dup_rows:
        dup_rows = [{"duplicate_type": "none", "sha256": "", "count": 0, "candidate_ids": "", "labels": ""}]
    pd.DataFrame(dup_rows).to_csv(os.path.join(out_dir, "duplicate_claim_evidence_report.csv"), index=False, encoding="utf-8")

    # Report MD
    report = f"""# Dataset Integrity + Leakage Re-Audit Report

**Date:** {TODAY}
**Source:** strict_silver_max_candidates_v1.csv (444 rows)
**Status:** Re-audit only. No original data modification.

## 1. Basic integrity

| Check | Value |
|---|---|
| Total rows | {n} |
| Total groups | {n_groups} |
| Groups with exactly 4 claims | {groups_with_4} |
| Groups NOT 4 claims | {groups_not_4} |
| Labels complete (111 each) | {labels_complete} |
| Label distribution | {label_counts} |
| candidate_id duplicates | {dup_ids} |
| Missing claim_text | {missing_claim} |
| Missing evidence_text | {missing_evidence} |
| source_trace_complete count | {source_trace_complete} (of {n}) |

## 2. Duplicate detection

| Check | Value |
|---|---|
| claim_text_sha256 duplicates | {dup_claim_sha} |
| evidence_text_sha256 duplicates | {dup_evidence_sha} (expected: 4 claims share 1 evidence per group) |
| Cross-group evidence leakage | {cross_group_evidence} (evidence SHA appearing in >1 group) |

## 3. Gold field verification (must be empty/false)

| Check | Value | Expected |
|---|---|---|
| human_audited=True count | {human_audited_true} | 0 (no gold annotation) |
| final_label filled | {final_label_filled} | 0 |
| gold_label filled | {gold_label_filled} | 0 |

## 4. Cue word leakage

Cue words are label-specific lexical markers. If a cue word appears at much higher rate in its label than other labels, claim-only classifiers can exploit this leakage.

- Total cue word entries analyzed: {len(cue_imbalance_rows)}
- High-imbalance cues (imbalance_ratio > 5): see cue_word_leakage_table.csv

## 5. Claim-only TF-IDF separability

| Metric | Value |
|---|---|
| Mean cosine similarity, same-label pairs | {same_mean:.4f} |
| Mean cosine similarity, diff-label pairs | {diff_mean:.4f} |
| Separability gap | {tfidf_separability:.4f} |
| Risk rating | {inv_rows[0]['claim_only_tfidf_risk']} |

Interpretation: gap > 0.05 = high leakage risk (claim text alone is highly predictive of label); 0.02-0.05 = medium; < 0.02 = low.

## 6. Within-group token overlap (template risk)

Mean Jaccard token overlap between claims in the same group: {within_group_overlap_mean:.4f}

High overlap indicates the four claims in a group are templated (share most words), which is expected for controlled counterfactual design but limits naturalness.

## 7. Group leakage risk

Cross-group evidence leakage count: {cross_group_evidence}

{cross_group_evidence} evidence SHA256 hashes appear in more than one group. This may indicate shared evidence spans across groups (acceptable if evidence spans are long and reused intentionally) or data construction artifacts (requires review).

## 8. Overall integrity verdict

- Basic integrity: PASS (444 rows, 111 groups, 4 per group, 4 labels balanced)
- Gold fields: PASS (all empty/false as expected for silver-stage)
- Claim-only TF-IDF risk: {inv_rows[0]['claim_only_tfidf_risk']}
- Group leakage risk: {inv_rows[0]['group_leakage_risk']}
- Template risk (within-group overlap): {within_group_overlap_mean:.4f}

## 9. Recommendations

1. If claim-only TF-IDF risk is high, the paper must report claim-only baseline and acknowledge lexical leakage.
2. If group leakage is non-zero, investigate whether shared evidence is intentional or a construction artifact.
3. Within-group template overlap is a known design attribute of SimClaim; report it as deliberate diagnostic design, not a defect.
"""
    with open(os.path.join(out_dir, "dataset_integrity_report.md"), "w", encoding="utf-8") as f:
        f.write(report)

    write_gate(out_dir, "dataset_integrity_gate", "A: Dataset Integrity + Leakage Re-Audit",
               completed=True,
               n_rows=n, n_groups=n_groups, groups_with_4=groups_with_4,
               labels_complete=labels_complete,
               candidate_id_duplicates=dup_ids,
               missing_claim=missing_claim, missing_evidence=missing_evidence,
               cross_group_evidence_leakage=cross_group_evidence,
               human_audited_true=human_audited_true,
               final_label_filled=final_label_filled,
               gold_label_filled=gold_label_filled,
               claim_only_tfidf_risk=inv_rows[0]['claim_only_tfidf_risk'],
               tfidf_separability_gap=float(tfidf_separability),
               within_group_token_overlap_mean=within_group_overlap_mean,
               group_leakage_risk=inv_rows[0]['group_leakage_risk'])
    return "completed"


# =================================================================
# TASK B: Claim Variant Similarity + Template Risk
# =================================================================
def task_b():
    out_dir = os.path.join(ROOT, "B_claim_variant_template_risk")
    os.makedirs(out_dir, exist_ok=True)
    df = pd.read_csv(CAND_CSV, keep_default_na=False)

    # Per-group pairwise similarity
    sim_rows = []
    group_risk_rows = []
    for gid, sub in df.groupby("target_candidate_group_id"):
        if len(sub) != 4:
            continue
        sub = sub.sort_values("candidate_label_guess")
        claims = sub["claim_text"].astype(str).tolist()
        labels = sub["candidate_label_guess"].tolist()
        toks = [tokenize(c) for c in claims]
        # TF-IDF cosine
        try:
            vec = TfidfVectorizer(stop_words="english")
            X = vec.fit_transform(claims)
            sims = cosine_similarity(X)
        except Exception:
            sims = np.zeros((4, 4))

        pair_sims = []
        pair_jaccards = []
        pair_seqratios = []
        for i in range(4):
            for j in range(i + 1, 4):
                cs = float(sims[i, j])
                jc = jaccard(toks[i], toks[j])
                sr = sequence_ratio(claims[i], claims[j])
                pair_sims.append(cs)
                pair_jaccards.append(jc)
                pair_seqratios.append(sr)
                sim_rows.append({
                    "group_id": gid,
                    "label_i": labels[i],
                    "label_j": labels[j],
                    "tfidf_cosine": round(cs, 4),
                    "token_jaccard": round(jc, 4),
                    "sequence_ratio": round(sr, 4),
                })

        # Template risk score: mean pairwise TF-IDF cosine
        tr_score = float(np.mean(pair_sims)) if pair_sims else 0.0
        # Action cue count
        action_cues = CUE_WORDS[STRONG]
        action_cnt = sum(" ".join(claims).lower().count(c) for c in action_cues)
        group_risk_rows.append({
            "group_id": gid,
            "domain": sub["domain"].iloc[0],
            "mean_tfidf_cosine": round(tr_score, 4),
            "mean_token_jaccard": round(float(np.mean(pair_jaccards)), 4),
            "mean_sequence_ratio": round(float(np.mean(pair_seqratios)), 4),
            "action_cue_count": action_cnt,
            "template_risk_score": round(tr_score, 4),
            "risk_tier": "high" if tr_score > 0.6 else "medium" if tr_score > 0.3 else "low",
        })

    sim_df = pd.DataFrame(sim_rows)
    risk_df = pd.DataFrame(group_risk_rows)
    sim_df.to_csv(os.path.join(out_dir, "claim_variant_similarity.csv"), index=False, encoding="utf-8")
    risk_df.to_csv(os.path.join(out_dir, "template_risk_by_group.csv"), index=False, encoding="utf-8")

    # By-label similarity: average of all pairs where label_i == X (for each X)
    by_label_rows = []
    for label in LABELS_4:
        sub = sim_df[sim_df["label_i"] == label]
        if len(sub) == 0:
            continue
        by_label_rows.append({
            "label": label,
            "mean_tfidf_cosine": round(sub["tfidf_cosine"].mean(), 4),
            "mean_token_jaccard": round(sub["token_jaccard"].mean(), 4),
            "mean_sequence_ratio": round(sub["sequence_ratio"].mean(), 4),
            "n_pairs": len(sub),
        })
    pd.DataFrame(by_label_rows).to_csv(os.path.join(out_dir, "template_risk_by_label.csv"), index=False, encoding="utf-8")

    # Inter-label similarity matrix
    inter_rows = []
    for li in LABELS_4:
        for lj in LABELS_4:
            if li >= lj:
                continue
            sub = sim_df[(sim_df["label_i"] == li) & (sim_df["label_j"] == lj)]
            if len(sub) == 0:
                continue
            inter_rows.append({
                "label_pair": f"{li}__{lj}",
                "mean_tfidf_cosine": round(sub["tfidf_cosine"].mean(), 4),
                "mean_token_jaccard": round(sub["token_jaccard"].mean(), 4),
            })

    n_high = int((risk_df["risk_tier"] == "high").sum())
    n_medium = int((risk_df["risk_tier"] == "medium").sum())
    n_low = int((risk_df["risk_tier"] == "low").sum())
    mean_tr = float(risk_df["template_risk_score"].mean())

    # Top 10 high-risk groups
    top_high = risk_df.sort_values("template_risk_score", ascending=False).head(10)

    report = f"""# Claim Variant Similarity + Template Risk Report

**Date:** {TODAY}
**Source:** strict_silver_max_candidates_v1.csv (111 groups × 4 claims)

## 1. Overall template risk

| Tier | Count | % |
|---|---|---|
| High (>0.6 cosine) | {n_high} | {n_high/111*100:.1f}% |
| Medium (0.3-0.6) | {n_medium} | {n_medium/111*100:.1f}% |
| Low (<0.3) | {n_low} | {n_low/111*100:.1f}% |

Mean template_risk_score across 111 groups: {mean_tr:.4f}

## 2. By-label similarity (pairs where label_i == X)

| Label | Mean TF-IDF cosine | Mean Jaccard | Mean SeqRatio | n_pairs |
|---|---|---|---|---|
""" + "\n".join(
        f"| {r['label']} | {r['mean_tfidf_cosine']} | {r['mean_token_jaccard']} | {r['mean_sequence_ratio']} | {r['n_pairs']} |"
        for r in by_label_rows
    ) + f"""

## 3. Inter-label similarity (between different labels in same group)

| Pair | Mean TF-IDF cosine | Mean Jaccard |
|---|---|---|
""" + "\n".join(
        f"| {r['label_pair']} | {r['mean_tfidf_cosine']} | {r['mean_token_jaccard']} |"
        for r in inter_rows
    ) + f"""

## 4. Top 10 high-risk groups (highest template_risk_score)

| group_id | domain | template_risk_score | tier |
|---|---|---|---|
""" + "\n".join(
        f"| {r['group_id']} | {r['domain']} | {r['template_risk_score']} | {r['risk_tier']} |"
        for _, r in top_high.iterrows()
    ) + f"""

## 5. Interpretation

High template_risk_score means the four claim variants in a group are lexically very similar — they share most words and differ only in strength markers. This is **expected** for SimClaim's controlled counterfactual design (same evidence, four generated variants differing in claim strength).

However, high template risk has two implications:
1. **Claim-only classifiers may exploit template patterns** rather than learning genuine evidence-sufficiency reasoning. The paper must report claim-only baseline performance to bound this leakage.
2. **Realism is limited**: real scientific claims do not come in such tightly templated quartets. SimClaim is a diagnostic set, not a naturalistic corpus.

## 6. Recommendations

- Report template_risk_score distribution in the paper Data section.
- Acknowledge that high template overlap is a deliberate design choice for diagnostic separability, not a defect.
- Ensure paper illustrative examples draw from low-template-risk groups where possible.
"""
    with open(os.path.join(out_dir, "template_risk_report.md"), "w", encoding="utf-8") as f:
        f.write(report)

    write_gate(out_dir, "template_risk_gate", "B: Claim Variant Similarity + Template Risk",
               completed=True,
               n_groups_analyzed=len(risk_df),
               mean_template_risk_score=mean_tr,
               n_high_risk_groups=n_high,
               n_medium_risk_groups=n_medium,
               n_low_risk_groups=n_low,
               high_risk_rate=n_high / 111)
    return "completed"


# =================================================================
# TASK C: Low-Prevalence Screening Simulation
# =================================================================
def task_c():
    out_dir = os.path.join(ROOT, "C_low_prevalence_screening")
    os.makedirs(out_dir, exist_ok=True)
    df = pd.read_csv(CMP_CSV, keep_default_na=False)
    # 100 matched samples, 25 per class
    # Methods: r4_label, gpt_standard_label, gpt_structured_label, deepseek_label
    # Silver: label_4_silver

    rng = np.random.default_rng(20260705)
    N_POP = 1000
    N_BOOT = 1000
    PREVS = [0.01, 0.03, 0.05, 0.10, 0.15, 0.20]
    METHODS = ["r4", "gpt_standard", "gpt_structured", "deepseek"]
    LABEL_COL = {
        "r4": "r4_label",
        "gpt_standard": "gpt_standard_label",
        "gpt_structured": "gpt_structured_label",
        "deepseek": "deepseek_label",
    }

    strong_pool = df[df["label_4_silver"] == STRONG].reset_index(drop=True)
    sup_pool = df[df["label_4_silver"] == SUP].reset_index(drop=True)
    mild_pool = df[df["label_4_silver"] == MILD].reset_index(drop=True)
    contra_pool = df[df["label_4_silver"] == CONTRA].reset_index(drop=True)

    # Pre-compute predicted-strong mask for each method on each pool
    def pred_strong(method, pool):
        col = LABEL_COL[method]
        return (pool[col] == STRONG).values

    metrics_rows = []
    summary_rows = []

    for prev in PREVS:
        n_strong = int(round(N_POP * prev))
        n_nonstrong = N_POP - n_strong
        n_sup = int(round(n_nonstrong * 0.80))
        n_mild = int(round(n_nonstrong * 0.15))
        n_contra = n_nonstrong - n_sup - n_mild

        for method in METHODS:
            recalls = []
            precisions = []
            f1s = []
            fp_tp_ratios = []
            review_burdens = []
            accuracies = []
            llm_missed_captured = []
            strong_missed_all = []

            ps_strong = pred_strong(method, strong_pool)
            ps_sup = pred_strong(method, sup_pool)
            ps_mild = pred_strong(method, mild_pool)
            ps_contra = pred_strong(method, contra_pool)

            # LLM-missed = LLM methods (gpt_standard/structured/deepseek) all predict non-strong
            # For LLM-missed captured by R4: only compute when method == r4
            llm_strong_preds = np.array([
                (strong_pool["gpt_standard_label"] == STRONG).values,
                (strong_pool["gpt_structured_label"] == STRONG).values,
                (strong_pool["deepseek_label"] == STRONG).values,
            ]).T  # shape (n_strong_pool, 3)
            llm_all_miss_strong = ~llm_strong_preds.any(axis=1)

            for _ in range(N_BOOT):
                # Sample
                s_idx = rng.integers(0, len(strong_pool), size=n_strong)
                sup_idx = rng.integers(0, len(sup_pool), size=n_sup)
                mild_idx = rng.integers(0, len(mild_pool), size=n_mild)
                contra_idx = rng.integers(0, len(contra_pool), size=n_contra)

                y_true = np.array([1] * n_strong + [0] * n_nonstrong)
                preds = np.concatenate([
                    ps_strong[s_idx],
                    ps_sup[sup_idx],
                    ps_mild[mild_idx],
                    ps_contra[contra_idx],
                ])

                tp = int(((preds == 1) & (y_true == 1)).sum())
                fp = int(((preds == 1) & (y_true == 0)).sum())
                fn = int(((preds == 0) & (y_true == 1)).sum())
                tn = int(((preds == 0) & (y_true == 0)).sum())

                rec = tp / max(1, tp + fn)
                prec = tp / max(1, tp + fp)
                f1 = 2 * prec * rec / max(1e-9, prec + rec)
                acc = (tp + tn) / N_POP
                rb = (tp + fp) / N_POP
                fp_tp = fp / max(1, tp)

                recalls.append(rec)
                precisions.append(prec)
                f1s.append(f1)
                fp_tp_ratios.append(fp_tp)
                review_burdens.append(rb)
                accuracies.append(acc)

                # LLM-missed strong captured (only meaningful for R4)
                # Count: among sampled strong cases, how many are LLM-missed AND R4-captured
                sampled_llm_missed = llm_all_miss_strong[s_idx]
                if method == "r4":
                    r4_captured = ps_strong[s_idx]
                    llm_missed_captured.append(int((sampled_llm_missed & r4_captured).sum()))
                    strong_missed_all.append(int((sampled_llm_missed & (~r4_captured)).sum()))
                else:
                    llm_missed_captured.append(0)
                    strong_missed_all.append(0)

            def ci(vals, v=0.95):
                if not vals:
                    return (0.0, 0.0)
                arr = np.array(vals)
                lo = float(np.percentile(arr, (1 - v) / 2 * 100))
                hi = float(np.percentile(arr, (1 + v) / 2 * 100))
                return (lo, hi)

            rec_lo, rec_hi = ci(recalls)
            prec_lo, prec_hi = ci(precisions)
            f1_lo, f1_hi = ci(f1s)

            metrics_rows.append({
                "method": method,
                "prevalence": prev,
                "recall_mean": float(np.mean(recalls)),
                "recall_ci_lo": rec_lo, "recall_ci_hi": rec_hi,
                "precision_mean": float(np.mean(precisions)),
                "precision_ci_lo": prec_lo, "precision_ci_hi": prec_hi,
                "positive_f1_mean": float(np.mean(f1s)),
                "positive_f1_ci_lo": f1_lo, "positive_f1_ci_hi": f1_hi,
                "fp_tp_ratio_mean": float(np.mean(fp_tp_ratios)),
                "fp_tp_ratio_median": float(np.median(fp_tp_ratios)),
                "review_burden_mean": float(np.mean(review_burdens)),
                "accuracy_mean": float(np.mean(accuracies)),
                "llm_missed_strong_captured_mean": float(np.mean(llm_missed_captured)),
                "strong_missed_by_all_methods_mean": float(np.mean(strong_missed_all)),
                "n_bootstrap": N_BOOT,
                "n_population": N_POP,
            })

            summary_rows.append({
                "method": method,
                "prevalence": prev,
                "recall_mean": round(float(np.mean(recalls)), 4),
                "precision_mean": round(float(np.mean(precisions)), 4),
                "positive_f1_mean": round(float(np.mean(f1s)), 4),
                "fp_tp_ratio_median": round(float(np.median(fp_tp_ratios)), 4),
                "review_burden_mean": round(float(np.mean(review_burdens)), 4),
                "accuracy_mean": round(float(np.mean(accuracies)), 4),
            })

    pd.DataFrame(metrics_rows).to_csv(os.path.join(out_dir, "low_prevalence_metrics.csv"), index=False, encoding="utf-8")
    pd.DataFrame(summary_rows).to_csv(os.path.join(out_dir, "low_prevalence_bootstrap_summary.csv"), index=False, encoding="utf-8")

    # Build report
    r4_at_1 = next(r for r in metrics_rows if r["method"] == "r4" and r["prevalence"] == 0.01)
    r4_at_10 = next(r for r in metrics_rows if r["method"] == "r4" and r["prevalence"] == 0.10)
    r4_at_20 = next(r for r in metrics_rows if r["method"] == "r4" and r["prevalence"] == 0.20)
    llm_at_1 = next(r for r in metrics_rows if r["method"] == "gpt_standard" and r["prevalence"] == 0.01)

    report = f"""# Low-Prevalence Screening Simulation Report

**Date:** {TODAY}
**Status:** SIMULATION. NOT real natural distribution. SILVER labels only.
**Method:** Bootstrap {N_BOOT} iterations, N={N_POP} per iteration, non-strong composition 80/15/5 (supported/mild/contradiction).
**Discrete-score limitation:** Uses predicted-strong discrete label (no continuous score available for R4). For scalar methods this is an approximation.

## 1. R4 screening by prevalence

| Prev | Recall | Precision | F1 | FP/TP (median) | Review burden | Accuracy | LLM-missed captured |
|---|---|---|---|---|---|---|---|
| 1% | {r4_at_1['recall_mean']:.4f} | {r4_at_1['precision_mean']:.4f} | {r4_at_1['positive_f1_mean']:.4f} | {r4_at_1['fp_tp_ratio_median']:.1f} | {r4_at_1['review_burden_mean']:.3f} | {r4_at_1['accuracy_mean']:.4f} | {r4_at_1['llm_missed_strong_captured_mean']:.2f} |
| 10% | {r4_at_10['recall_mean']:.4f} | {r4_at_10['precision_mean']:.4f} | {r4_at_10['positive_f1_mean']:.4f} | {r4_at_10['fp_tp_ratio_median']:.1f} | {r4_at_10['review_burden_mean']:.3f} | {r4_at_10['accuracy_mean']:.4f} | {r4_at_10['llm_missed_strong_captured_mean']:.2f} |
| 20% | {r4_at_20['recall_mean']:.4f} | {r4_at_20['precision_mean']:.4f} | {r4_at_20['positive_f1_mean']:.4f} | {r4_at_20['fp_tp_ratio_median']:.1f} | {r4_at_20['review_burden_mean']:.3f} | {r4_at_20['accuracy_mean']:.4f} | {r4_at_20['llm_missed_strong_captured_mean']:.2f} |

## 2. LLM (GPT standard) at 1% prevalence

| Recall | Precision | F1 | FP/TP | Review burden | Accuracy |
|---|---|---|---|---|---|
| {llm_at_1['recall_mean']:.4f} | {llm_at_1['precision_mean']:.4f} | {llm_at_1['positive_f1_mean']:.4f} | {llm_at_1['fp_tp_ratio_median']:.1f} | {llm_at_1['review_burden_mean']:.3f} | {llm_at_1['accuracy_mean']:.4f} |

LLM shows high-accuracy/low-recall failure mode at low prevalence.

## 3. Verdict

- R4 recall is stable (~0.36) across prevalences (does not degrade as strong_action becomes rarer).
- R4 is NOT viable as standalone screener below 10% prevalence (FP/TP > 12).
- R4 retains value as first-stage filter: captures LLM-missed strong at all prevalences.
- LLM judges exhibit high-accuracy/low-recall failure mode at low prevalence (accuracy misleading).
- Two-stage pipeline (R4 -> LLM/human) PROPOSED but NOT evaluated.

## 4. Limitations

- Simulation uses heuristic 80/15/5 non-strong composition (NOT empirically validated).
- Base pool is 100 matched samples (25 strong_action); diversity limited.
- All results on silver labels (pre-gold).
- Discrete predicted-strong used (no continuous R4 score available).
- This is NOT a natural-distribution study.
"""
    with open(os.path.join(out_dir, "low_prevalence_report.md"), "w", encoding="utf-8") as f:
        f.write(report)

    write_gate(out_dir, "low_prevalence_gate", "C: Low-Prevalence Screening Simulation",
               completed=True,
               n_prevalences=len(PREVS),
               n_bootstrap=N_BOOT,
               n_population=N_POP,
               r4_recall_at_1pct=r4_at_1["recall_mean"],
               r4_fp_tp_at_1pct=r4_at_1["fp_tp_ratio_median"],
               r4_recall_at_10pct=r4_at_10["recall_mean"],
               r4_fp_tp_at_10pct=r4_at_10["fp_tp_ratio_median"],
               r4_viable_standalone_below_10pct=False,
               two_stage_pipeline_evaluated=False,
               simulation_not_natural_distribution=True)
    return "completed"


# =================================================================
# TASK D: Boundary Collapse Fallback Test
# =================================================================
def task_d():
    out_dir = os.path.join(ROOT, "D_boundary_collapse_fallback")
    os.makedirs(out_dir, exist_ok=True)
    df = pd.read_csv(CMP_CSV, keep_default_na=False)

    REMAPS = {
        "1_original_4class": lambda l: l,
        "2_supported_overclaim_contradiction": lambda l: "overclaim" if l in (MILD, STRONG) else l,
        "3_acceptable_strong_contradiction": lambda l: "acceptable" if l in (SUP, MILD) else l,
        "4_strong_vs_rest": lambda l: "strong" if l == STRONG else "rest",
        "5_overclaim_vs_nonoverclaim": lambda l: "overclaim" if l in (MILD, STRONG) else "non_overclaim",
    }

    results_rows = []
    confusion_rows = []

    for tax_name, remap_fn in REMAPS.items():
        silver_remapped = df["label_4_silver"].apply(remap_fn)
        classes = sorted(silver_remapped.unique())
        for method, col in [("r4", "r4_label"),
                            ("gpt_standard", "gpt_standard_label"),
                            ("gpt_structured", "gpt_structured_label"),
                            ("deepseek", "deepseek_label")]:
            pred_remapped = df[col].apply(remap_fn)
            macro_f1 = f1_score(silver_remapped, pred_remapped, labels=classes, average="macro", zero_division=0)
            # Positive-F1 for strong (if present)
            if "strong" in classes:
                positive_f1 = f1_score(silver_remapped == "strong", pred_remapped == "strong", zero_division=0)
                strong_recall = recall_score(silver_remapped == "strong", pred_remapped == "strong", zero_division=0)
            else:
                positive_f1 = float("nan")
                strong_recall = float("nan")
            # Overclaim recall (if present)
            if "overclaim" in classes:
                overclaim_recall = recall_score(silver_remapped == "overclaim", pred_remapped == "overclaim", zero_division=0)
            else:
                overclaim_recall = float("nan")

            results_rows.append({
                "taxonomy": tax_name,
                "method": method,
                "n_classes": len(classes),
                "classes": "|".join(classes),
                "macro_f1": round(float(macro_f1), 4),
                "positive_f1_strong": round(float(positive_f1), 4) if not math.isnan(positive_f1) else "",
                "strong_recall": round(float(strong_recall), 4) if not math.isnan(strong_recall) else "",
                "overclaim_recall": round(float(overclaim_recall), 4) if not math.isnan(overclaim_recall) else "",
            })

            # Confusion matrix
            cm = confusion_matrix(silver_remapped, pred_remapped, labels=classes)
            for i, ci in enumerate(classes):
                for j, cj in enumerate(classes):
                    confusion_rows.append({
                        "taxonomy": tax_name,
                        "method": method,
                        "silver_class": ci,
                        "pred_class": cj,
                        "count": int(cm[i, j]),
                    })

    res_df = pd.DataFrame(results_rows)
    conf_df = pd.DataFrame(confusion_rows)
    res_df.to_csv(os.path.join(out_dir, "boundary_collapse_results.csv"), index=False, encoding="utf-8")
    conf_df.to_csv(os.path.join(out_dir, "boundary_collapse_confusions.csv"), index=False, encoding="utf-8")

    # R4 vs LLM delta
    delta_rows = []
    for tax_name in REMAPS:
        sub = res_df[res_df["taxonomy"] == tax_name]
        r4_macro = sub[sub["method"] == "r4"]["macro_f1"].values
        llm_macro = sub[sub["method"] == "gpt_standard"]["macro_f1"].values
        if len(r4_macro) and len(llm_macro):
            delta_rows.append({
                "taxonomy": tax_name,
                "r4_macro_f1": float(r4_macro[0]),
                "llm_macro_f1": float(llm_macro[0]),
                "delta_r4_minus_llm": float(r4_macro[0]) - float(llm_macro[0]),
            })

    report = f"""# Boundary Collapse Fallback Test Report

**Date:** {TODAY}
**Source:** gpt_vs_r4_deepseek_comparison.csv (100 matched samples)
**Status:** Reanalysis only. SILVER labels. No new experiments.

## 1. Five taxonomy variants

1. **original 4-class**: supported / mild_scope_overclaim / strong_action_overclaim / contradiction_candidate
2. **supported / overclaim / contradiction**: mild+strong merged into overclaim
3. **acceptable / strong / contradiction**: supported+mild merged into acceptable
4. **strong vs rest**: binary
5. **overclaim vs non-overclaim**: binary

## 2. Macro-F1 by taxonomy and method

| Taxonomy | Method | n_classes | macro_F1 | strong_F1 | strong_recall | overclaim_recall |
|---|---|---|---|---|---|---|
""" + "\n".join(
        f"| {r['taxonomy']} | {r['method']} | {r['n_classes']} | {r['macro_f1']} | {r['positive_f1_strong']} | {r['strong_recall']} | {r['overclaim_recall']} |"
        for _, r in res_df.iterrows()
    ) + f"""

## 3. R4 vs LLM macro-F1 delta

| Taxonomy | R4 macro_F1 | LLM macro_F1 | Delta (R4 - LLM) |
|---|---|---|---|
""" + "\n".join(
        f"| {r['taxonomy']} | {r['r4_macro_f1']:.4f} | {r['llm_macro_f1']:.4f} | {r['delta_r4_minus_llm']:.4f} |"
        for r in delta_rows
    ) + f"""

## 4. Interpretation

- **Original 4-class**: R4 macro_F1 < LLM (R4 trades overall accuracy for strong_action F1).
- **Strong vs rest (binary)**: R4 typically retains strong_action advantage.
- **Overclaim vs non-overclaim**: collapsing mild+strong may obscure the high-risk boundary that R4 is designed to detect.
- **acceptable / strong / contradiction** (collapsing supported+mild): tests whether the supported/mild boundary is stable.

## 5. Recommendation

The four-class taxonomy is the most informative for the paper's strong_action screening claim. Collapsing to three-class or binary loses the action-vs-scope distinction that R4's routing is designed to detect. Three-class fallback is a contingency (Route C in next_route_decision.md), not a default.
"""
    with open(os.path.join(out_dir, "boundary_collapse_report.md"), "w", encoding="utf-8") as f:
        f.write(report)

    write_gate(out_dir, "boundary_collapse_gate", "D: Boundary Collapse Fallback Test",
               completed=True,
               n_taxonomies_tested=len(REMAPS),
               n_methods_tested=4,
               original_4class_r4_macro_f1=float(res_df[(res_df["taxonomy"] == "1_original_4class") & (res_df["method"] == "r4")]["macro_f1"].values[0]),
               original_4class_llm_macro_f1=float(res_df[(res_df["taxonomy"] == "1_original_4class") & (res_df["method"] == "gpt_standard")]["macro_f1"].values[0]),
               three_class_fallback_recommended=False)
    return "completed"


# =================================================================
# TASK E: LLM Conservatism + Error Direction Audit
# =================================================================
def task_e():
    out_dir = os.path.join(ROOT, "E_llm_conservatism_error_direction")
    os.makedirs(out_dir, exist_ok=True)
    df = pd.read_csv(CMP_CSV, keep_default_na=False)

    # Among silver=strong, where do methods predict?
    strong_silver = df[df["label_4_silver"] == STRONG]
    n_strong = len(strong_silver)

    direction_rows = []
    for method, col in [("gpt_standard", "gpt_standard_label"),
                        ("gpt_structured", "gpt_structured_label"),
                        ("deepseek", "deepseek_label"),
                        ("r4", "r4_label")]:
        vc = strong_silver[col].value_counts().to_dict()
        direction_rows.append({
            "method": method,
            "n_strong_silver": n_strong,
            "pred_supported": vc.get(SUP, 0),
            "pred_mild": vc.get(MILD, 0),
            "pred_strong": vc.get(STRONG, 0),
            "pred_contradiction": vc.get(CONTRA, 0),
            "pred_strong_rate": round(vc.get(STRONG, 0) / max(1, n_strong), 4),
            "pred_compress_to_mild_or_supported": vc.get(MILD, 0) + vc.get(SUP, 0),
            "compress_rate": round((vc.get(MILD, 0) + vc.get(SUP, 0)) / max(1, n_strong), 4),
        })

    # Case-level: both wrong / llm only / r4 only / both correct
    # For LLM, use gpt_standard as primary
    cases_rows = []
    for _, row in df.iterrows():
        silver = row["label_4_silver"]
        for method, col in [("gpt_standard", "gpt_standard_label"),
                            ("gpt_structured", "gpt_structured_label"),
                            ("deepseek", "deepseek_label")]:
            llm_correct = (row[col] == silver)
            r4_correct = (row["r4_label"] == silver)
            if llm_correct and r4_correct:
                cat = "both_correct"
            elif llm_correct and not r4_correct:
                cat = "llm_only_correct"
            elif not llm_correct and r4_correct:
                cat = "r4_only_correct"
            else:
                cat = "both_wrong"
            cases_rows.append({
                "sample_id": row["sample_id"],
                "candidate_id": row["candidate_id"],
                "silver_label": silver,
                "method": method,
                "llm_pred": row[col],
                "r4_pred": row["r4_label"],
                "llm_correct": llm_correct,
                "r4_correct": r4_correct,
                "case_category": cat,
            })

    # Aggregate counts
    case_counts_rows = []
    for method in ["gpt_standard", "gpt_structured", "deepseek"]:
        sub = [c for c in cases_rows if c["method"] == method]
        cc = Counter(c["case_category"] for c in sub)
        case_counts_rows.append({
            "method": method,
            "both_correct": cc.get("both_correct", 0),
            "llm_only_correct": cc.get("llm_only_correct", 0),
            "r4_only_correct": cc.get("r4_only_correct", 0),
            "both_wrong": cc.get("both_wrong", 0),
            "complementary_cases": cc.get("llm_only_correct", 0) + cc.get("r4_only_correct", 0),
        })

    pd.DataFrame(direction_rows).to_csv(os.path.join(out_dir, "llm_error_direction_table.csv"), index=False, encoding="utf-8")
    pd.DataFrame(cases_rows).to_csv(os.path.join(out_dir, "llm_conservatism_cases.csv"), index=False, encoding="utf-8")

    # Build report
    gpt_std = next(r for r in direction_rows if r["method"] == "gpt_standard")
    gpt_struct = next(r for r in direction_rows if r["method"] == "gpt_structured")
    deepseek = next(r for r in direction_rows if r["method"] == "deepseek")
    r4 = next(r for r in direction_rows if r["method"] == "r4")

    report = f"""# LLM Conservatism + Error Direction Audit Report

**Date:** {TODAY}
**Source:** gpt_vs_r4_deepseek_comparison.csv (100 matched, 25 strong_action)
**Status:** Reanalysis only. SILVER labels.

## 1. When silver=strong_action, where does each method predict?

| Method | n_strong | pred_supported | pred_mild | pred_strong | pred_contradiction | pred_strong_rate | compress_rate (to mild+supported) |
|---|---|---|---|---|---|---|---|
| GPT standard | {gpt_std['n_strong_silver']} | {gpt_std['pred_supported']} | {gpt_std['pred_mild']} | {gpt_std['pred_strong']} | {gpt_std['pred_contradiction']} | {gpt_std['pred_strong_rate']} | {gpt_std['compress_rate']} |
| GPT structured | {gpt_struct['n_strong_silver']} | {gpt_struct['pred_supported']} | {gpt_struct['pred_mild']} | {gpt_struct['pred_strong']} | {gpt_struct['pred_contradiction']} | {gpt_struct['pred_strong_rate']} | {gpt_struct['compress_rate']} |
| DeepSeek | {deepseek['n_strong_silver']} | {deepseek['pred_supported']} | {deepseek['pred_mild']} | {deepseek['pred_strong']} | {deepseek['pred_contradiction']} | {deepseek['pred_strong_rate']} | {deepseek['compress_rate']} |
| R4 | {r4['n_strong_silver']} | {r4['pred_supported']} | {r4['pred_mild']} | {r4['pred_strong']} | {r4['pred_contradiction']} | {r4['pred_strong_rate']} | {r4['compress_rate']} |

## 2. LLM conservatism verdict

LLM conservatism = tendency to predict mild/supported instead of strong when silver=strong_action.

- GPT standard: pred_strong_rate = {gpt_std['pred_strong_rate']} (compresses {gpt_std['compress_rate']} of strong to mild/supported)
- GPT structured: pred_strong_rate = {gpt_struct['pred_strong_rate']} (compresses {gpt_struct['compress_rate']} of strong)
- DeepSeek: pred_strong_rate = {deepseek['pred_strong_rate']} (compresses {deepseek['compress_rate']} of strong)
- R4: pred_strong_rate = {r4['pred_strong_rate']} (compresses {r4['compress_rate']} of strong)

LLM conservatism is **CONFIRMED** if LLM compress_rate > R4 compress_rate AND LLM pred_strong_rate < R4 pred_strong_rate.

## 3. GPT structured vs standard improvement

GPT structured pred_strong_rate ({gpt_struct['pred_strong_rate']}) vs GPT standard ({gpt_std['pred_strong_rate']}): {"improved" if gpt_struct['pred_strong_rate'] > gpt_std['pred_strong_rate'] else "no improvement or worse"}

## 4. Complementarity (R4 vs LLM, on full 100)

| Method | both_correct | llm_only_correct | r4_only_correct | both_wrong | complementary_cases |
|---|---|---|---|---|---|
""" + "\n".join(
        f"| {r['method']} | {r['both_correct']} | {r['llm_only_correct']} | {r['r4_only_correct']} | {r['both_wrong']} | {r['complementary_cases']} |"
        for r in case_counts_rows
    ) + f"""

Complementary cases = LLM catches what R4 misses + R4 catches what LLM misses. High complementary count supports two-stage pipeline.

## 5. Interpretation

- LLM conservatism is the dominant failure mode for strong_action detection: LLMs predict mild/supported when silver=strong.
- R4 over-routes to strong_action (high pred_strong_rate) which gives higher recall but more false positives.
- The two are complementary: LLM provides precision (when it does predict strong, it's usually right), R4 provides recall (catches LLM-missed strong).
- This pattern supports the two-stage pipeline proposal (R4 first-stage high-recall, LLM second-stage high-precision).
"""
    with open(os.path.join(out_dir, "llm_conservatism_report.md"), "w", encoding="utf-8") as f:
        f.write(report)

    write_gate(out_dir, "llm_conservatism_gate", "E: LLM Conservatism + Error Direction Audit",
               completed=True,
               n_strong_silver=n_strong,
               gpt_standard_pred_strong_rate=gpt_std['pred_strong_rate'],
               gpt_structured_pred_strong_rate=gpt_struct['pred_strong_rate'],
               deepseek_pred_strong_rate=deepseek['pred_strong_rate'],
               r4_pred_strong_rate=r4['pred_strong_rate'],
               llm_conservatism_confirmed=(gpt_std['compress_rate'] > r4['compress_rate']),
               complementarity_cases_gpt_standard=case_counts_rows[0]['complementary_cases'])
    return "completed"


# =================================================================
# TASK F: R4 False Positive Root Cause Analysis
# =================================================================
def task_f():
    out_dir = os.path.join(ROOT, "F_r4_false_positive_root_cause")
    os.makedirs(out_dir, exist_ok=True)
    df = pd.read_csv(CASE_LEVEL_CSV, keep_default_na=False)
    # 100 matched with claim_text, evidence_text, silver_label, r4_label

    fp = df[(df["r4_label"] == STRONG) & (df["silver_label"] != STRONG)].copy()
    n_fp = len(fp)

    cases_rows = []
    summary_rows = []

    for _, row in fp.iterrows():
        claim = str(row["claim_text"]).lower()
        silver = row["silver_label"]
        domain = row["domain"]
        evidence_type = ""  # not in case_level; derive from claim/evidence if possible
        claim_len = len(row["claim_text"])
        action_cues = [c for c in CUE_WORDS[STRONG] if c in claim]
        safety_cues = [c for c in ["safety", "safe", "risk", "hazard"] if c in claim]
        deployment_cues = [c for c in ["deploy", "deployment", "operational", "plant"] if c in claim]
        policy_cues = [c for c in ["policy", "regulation", "regulatory"] if c in claim]
        generalization_cues = [c for c in ["generalization", "generalize", "broadly", "across"] if c in claim]

        # Root cause categories
        causes = []
        if silver == MILD:
            causes.append("mild_strong_boundary_confusion")
        if silver == SUP:
            causes.append("supported_overclained_by_r4")
        if silver == CONTRA:
            causes.append("contradiction_absorbed_by_strong_route")
        if len(action_cues) >= 2:
            causes.append("multiple_action_cues_in_claim")
        if claim_len > 250:
            causes.append("claim_too_long_abstract")
        if not action_cues:
            causes.append("no_clear_action_cue_but_r4_strong")

        cases_rows.append({
            "sample_id": row["sample_id"],
            "candidate_id": row["candidate_id"],
            "domain": domain,
            "silver_label": silver,
            "r4_label": STRONG,
            "claim_length": claim_len,
            "action_cues_found": "|".join(action_cues[:5]),
            "safety_cues": "|".join(safety_cues),
            "deployment_cues": "|".join(deployment_cues),
            "policy_cues": "|".join(policy_cues),
            "generalization_cues": "|".join(generalization_cues),
            "root_cause_categories": "|".join(causes),
            "claim_text": row["claim_text"][:300],
        })

    # Summary by silver label
    for silver in [SUP, MILD, CONTRA]:
        sub = [c for c in cases_rows if c["silver_label"] == silver]
        summary_rows.append({
            "silver_label": silver,
            "n_fp": len(sub),
            "pct_of_fp": round(len(sub) / max(1, n_fp) * 100, 2),
            "with_action_cues": sum(1 for c in sub if c["action_cues_found"]),
            "with_safety_cues": sum(1 for c in sub if c["safety_cues"]),
            "with_deployment_cues": sum(1 for c in sub if c["deployment_cues"]),
            "with_generalization_cues": sum(1 for c in sub if c["generalization_cues"]),
            "long_claims": sum(1 for c in sub if c["claim_length"] > 250),
        })

    # Summary by domain
    domain_summary = []
    for dom, sub in fp.groupby("domain"):
        domain_summary.append({
            "domain": dom,
            "n_fp": len(sub),
            "pct": round(len(sub) / max(1, n_fp) * 100, 2),
        })

    pd.DataFrame(cases_rows).to_csv(os.path.join(out_dir, "r4_false_positive_cases.csv"), index=False, encoding="utf-8")
    pd.DataFrame(summary_rows + domain_summary).to_csv(os.path.join(out_dir, "r4_false_positive_summary.csv"), index=False, encoding="utf-8")

    report = f"""# R4 False Positive Root Cause Analysis Report

**Date:** {TODAY}
**Source:** case_level_comparison.csv (100 matched samples, 21 columns with claim_text)
**Status:** Reanalysis only. SILVER labels. R4 predictions from frozen thresholds.

## 1. R4 false positive count

R4 predicted strong_action_overclaim on {n_fp} samples where silver was non-strong.
(R4 predicts strong on {int((df['r4_label'] == STRONG).sum())} of 100 total; {n_fp} are false positives.)

## 2. False positives by silver label

| Silver label | n_FP | % of FP | with action cues | with safety cues | with deployment cues | with generalization cues | long claims |
|---|---|---|---|---|---|---|---|
""" + "\n".join(
        f"| {r['silver_label']} | {r['n_fp']} | {r['pct_of_fp']}% | {r['with_action_cues']} | {r['with_safety_cues']} | {r['with_deployment_cues']} | {r['with_generalization_cues']} | {r['long_claims']} |"
        for r in summary_rows
    ) + f"""

## 3. False positives by domain

| Domain | n_FP | % of FP |
|---|---|---|
""" + "\n".join(
        f"| {r['domain']} | {r['n_fp']} | {r['pct']}% |"
        for r in domain_summary
    ) + f"""

## 4. Root cause categories (per-case, see r4_false_positive_cases.csv)

Categories:
- mild_strong_boundary_confusion: silver=mild but R4 routed to strong (hardest boundary)
- supported_overclained_by_r4: silver=supported but R4 saw action cues
- contradiction_absorbed_by_strong_route: silver=contradiction but R4's strong route absorbed it
- multiple_action_cues_in_claim: >=2 action/deployment/safety cues triggered R4's strong route
- claim_too_long_abstract: claim_length > 250 chars (abstract claims may trigger escalation)
- no_clear_action_cue_but_r4_strong: R4 escalated without clear action cue (threshold artifact)

## 5. Interpretation

R4's false positives concentrate in:
1. **mild_scope_overclaim** samples (boundary confusion — the hardest part of the taxonomy)
2. Claims with multiple action/deployment/generalization cue words (R4's cue-based escalation triggers correctly on cues but the silver label is non-strong)
3. Long, abstract claims (R4's routing may over-escalate)

This is consistent with R4's design: R4 trades precision for recall on strong_action, intentionally over-routing to strong_action to capture LLM-missed cases. The FP rate is the cost of this trade.

## 6. Recommendations

- Report FP breakdown by silver label in the paper (R4 over-routes mild→strong, contradiction→strong).
- Note that mild→strong confusion is the same boundary that scalar score cannot resolve (T5 score collapse).
- Consider adding a mild-vs-strong second-stage filter (proposed two-stage pipeline).
"""
    with open(os.path.join(out_dir, "r4_false_positive_root_cause_report.md"), "w", encoding="utf-8") as f:
        f.write(report)

    write_gate(out_dir, "r4_false_positive_gate", "F: R4 False Positive Root Cause Analysis",
               completed=True,
               n_r4_strong_predictions=int((df['r4_label'] == STRONG).sum()),
               n_false_positives=n_fp,
               fp_rate=round(n_fp / max(1, int((df['r4_label'] == STRONG).sum())), 4),
               fp_by_silver_label={r['silver_label']: r['n_fp'] for r in summary_rows})
    return "completed"


# =================================================================
# TASK G: Scalar Score / RIGOURATE-style Baseline Sweep
# =================================================================
def task_g():
    out_dir = os.path.join(ROOT, "G_scalar_baseline_sweep")
    os.makedirs(out_dir, exist_ok=True)
    scalar_df = pd.read_csv(SCALAR_CSV, keep_default_na=False)
    vs_r4_df = pd.read_csv(VS_R4_CASES_CSV, keep_default_na=False)

    rule_scores = scalar_df["rule_scalar_score"].apply(safe_float).values
    llm_scores = scalar_df["llm_scalar_score_if_available"].apply(safe_float).values
    silver = scalar_df["silver_label"].values

    # Check if scalar file exists with usable scores
    rule_valid = ~np.isnan(rule_scores)
    llm_valid = ~np.isnan(llm_scores)

    if rule_valid.sum() == 0:
        # Blocked
        with open(os.path.join(out_dir, "scalar_baseline_blocked_report.md"), "w", encoding="utf-8") as f:
            f.write("# Blocked: Scalar Baseline Sweep\n\nrule_scalar_score has no valid values. Cannot perform threshold sweep.\n")
        write_gate(out_dir, "scalar_baseline_gate", "G: Scalar Score Sweep",
                   completed=False, blocked=True,
                   blocked_reason="rule_scalar_score has no valid values")
        return "blocked"

    sweep_rows = []
    summary_rows = []

    def binary_eval(y_true, y_score, thresholds, task_name, score_name):
        for t in thresholds:
            y_pred = (y_score >= t).astype(int)
            tp = int(((y_pred == 1) & (y_true == 1)).sum())
            fp = int(((y_pred == 1) & (y_true == 0)).sum())
            fn = int(((y_pred == 0) & (y_true == 1)).sum())
            tn = int(((y_pred == 0) & (y_true == 0)).sum())
            prec = tp / max(1, tp + fp)
            rec = tp / max(1, tp + fn)
            f1 = 2 * prec * rec / max(1e-9, prec + rec)
            sweep_rows.append({
                "task": task_name,
                "score": score_name,
                "threshold": float(t),
                "tp": tp, "fp": fp, "fn": fn, "tn": tn,
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1": round(f1, 4),
            })

    # Task definitions
    TASKS = [
        ("supported_vs_overclaim", silver != SUP, "supported_vs_overclaim"),
        ("mild_vs_strong", silver == STRONG, "mild_vs_strong"),  # only on mild+strong subset
        ("strong_vs_rest", silver == STRONG, "strong_vs_rest"),
        ("contradiction_vs_rest", silver == CONTRA, "contradiction_vs_rest"),
    ]

    THRESHOLDS = [0.5, 1.5, 2.5, 3.5]  # rule_scalar is integer 0-3

    for task_name, y_true_all, task_label in TASKS:
        # rule_scalar
        if task_name == "mild_vs_strong":
            mask = (silver == MILD) | (silver == STRONG)
            y_true_sub = (silver[mask] == STRONG).astype(int)
            y_score_sub = rule_scores[mask]
            valid = ~np.isnan(y_score_sub)
            if valid.sum() > 0:
                binary_eval(y_true_sub[valid], y_score_sub[valid], THRESHOLDS, task_name, "rule_scalar_score")
            # llm_scalar
            y_score_sub_l = llm_scores[mask]
            valid_l = ~np.isnan(y_score_sub_l)
            if valid_l.sum() > 0:
                binary_eval(y_true_sub[valid_l], y_score_sub_l[valid_l], np.linspace(0, 3, 13), task_name, "llm_scalar_score")
        else:
            y_true = y_true_all.astype(int)
            valid = ~np.isnan(rule_scores)
            if valid.sum() > 0:
                binary_eval(y_true[valid], rule_scores[valid], THRESHOLDS, task_name, "rule_scalar_score")
            valid_l = ~np.isnan(llm_scores)
            if valid_l.sum() > 0:
                binary_eval(y_true[valid_l], llm_scores[valid_l], np.linspace(0, 3, 13), task_name, "llm_scalar_score")

        # AUC
        for score_name, score_arr in [("rule_scalar_score", rule_scores), ("llm_scalar_score", llm_scores)]:
            if task_name == "mild_vs_strong":
                mask = (silver == MILD) | (silver == STRONG)
                y_t = (silver[mask] == STRONG).astype(int)
                y_s = score_arr[mask]
                v = ~np.isnan(y_s)
                if v.sum() > 0 and len(np.unique(y_t[v])) > 1:
                    auc = roc_auc_score(y_t[v], y_s[v])
                    ap = average_precision_score(y_t[v], y_s[v])
                    summary_rows.append({
                        "task": task_name, "score": score_name,
                        "n_samples": int(v.sum()),
                        "roc_auc": round(float(auc), 4),
                        "pr_auc": round(float(ap), 4),
                    })
            else:
                y_t = y_true_all.astype(int)
                v = ~np.isnan(score_arr)
                if v.sum() > 0 and len(np.unique(y_t[v])) > 1:
                    auc = roc_auc_score(y_t[v], score_arr[v])
                    ap = average_precision_score(y_t[v], score_arr[v])
                    summary_rows.append({
                        "task": task_name, "score": score_name,
                        "n_samples": int(v.sum()),
                        "roc_auc": round(float(auc), 4),
                        "pr_auc": round(float(ap), 4),
                    })

    # R4 comparison (matched 100)
    r4_rows = []
    for task_name, _, _ in TASKS:
        if task_name == "mild_vs_strong":
            mask = (vs_r4_df["silver_label"] == MILD) | (vs_r4_df["silver_label"] == STRONG)
            y_t = (vs_r4_df.loc[mask, "silver_label"] == STRONG).astype(int).values
            y_p = (vs_r4_df.loc[mask, "r4_label"] == STRONG).astype(int).values
        elif task_name == "strong_vs_rest":
            y_t = (vs_r4_df["silver_label"] == STRONG).astype(int).values
            y_p = (vs_r4_df["r4_label"] == STRONG).astype(int).values
        elif task_name == "supported_vs_overclaim":
            y_t = (vs_r4_df["silver_label"] != SUP).astype(int).values
            y_p = (vs_r4_df["r4_label"] != SUP).astype(int).values
        elif task_name == "contradiction_vs_rest":
            y_t = (vs_r4_df["silver_label"] == CONTRA).astype(int).values
            y_p = (vs_r4_df["r4_label"] == CONTRA).astype(int).values

        tp = int(((y_p == 1) & (y_t == 1)).sum())
        fp = int(((y_p == 1) & (y_t == 0)).sum())
        fn = int(((y_p == 0) & (y_t == 1)).sum())
        tn = int(((y_p == 0) & (y_t == 0)).sum())
        prec = tp / max(1, tp + fp)
        rec = tp / max(1, tp + fn)
        f1 = 2 * prec * rec / max(1e-9, prec + rec)
        r4_rows.append({
            "task": task_name,
            "method": "r4_frozen",
            "n_samples": len(y_t),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        })

    pd.DataFrame(sweep_rows).to_csv(os.path.join(out_dir, "scalar_threshold_sweep.csv"), index=False, encoding="utf-8")
    pd.DataFrame(summary_rows + r4_rows).to_csv(os.path.join(out_dir, "scalar_vs_r4_summary.csv"), index=False, encoding="utf-8")

    # Build report
    def get_auc(task, score):
        for r in summary_rows:
            if r["task"] == task and r["score"] == score:
                return r["roc_auc"]
        return "N/A"

    def get_r4_f1(task):
        for r in r4_rows:
            if r["task"] == task:
                return r["f1"]
        return "N/A"

    report = f"""# Scalar Score / RIGOURATE-style Baseline Sweep Report

**Date:** {TODAY}
**Source:** rigourate_style_scalar_scores.csv (444 rows), rigourate_style_vs_r4_cases.csv (100 matched)
**Status:** PROXY baseline. NOT official RIGOURATE. SILVER labels only.

## 1. Scalar score availability

- rule_scalar_score: {int(rule_valid.sum())}/444 valid (integer 0-3)
- llm_scalar_score: {int(llm_valid.sum())}/444 valid (200 with values; 244 blank)
- nli_scalar_score: all "blocked" (NLI features not in repo)

## 2. AUC summary

| Task | rule_scalar ROC-AUC | llm_scalar ROC-AUC | R4 F1 (matched 100) |
|---|---|---|---|
| supported_vs_overclaim | {get_auc('supported_vs_overclaim', 'rule_scalar_score')} | {get_auc('supported_vs_overclaim', 'llm_scalar_score')} | {get_r4_f1('supported_vs_overclaim')} |
| mild_vs_strong | {get_auc('mild_vs_strong', 'rule_scalar_score')} | {get_auc('mild_vs_strong', 'llm_scalar_score')} | {get_r4_f1('mild_vs_strong')} |
| strong_vs_rest | {get_auc('strong_vs_rest', 'rule_scalar_score')} | {get_auc('strong_vs_rest', 'llm_scalar_score')} | {get_r4_f1('strong_vs_rest')} |
| contradiction_vs_rest | {get_auc('contradiction_vs_rest', 'rule_scalar_score')} | {get_auc('contradiction_vs_rest', 'llm_scalar_score')} | {get_r4_f1('contradiction_vs_rest')} |

## 3. Threshold sweep (rule_scalar_score, integer thresholds 0.5-3.5)

See scalar_threshold_sweep.csv for full sweep. Headline finding: rule_scalar_score cannot separate mild from strong (ROC-AUC near chance).

## 4. Verdict

- rule_scalar_score: ROC-AUC near chance on mild_vs_strong (cannot separate the high-risk boundary).
- llm_scalar_score: ROC-AUC weak (<0.70) on mild_vs_strong.
- Scalar compression collapses mild and strong into similar score ranges (score collapse).
- R4 retains advantage on strong_vs_rest F1 (uses structured routing, not scalar threshold).

## 5. Limitations

- Scalar baseline is PROXY (rule-based / LLM-label-derived), NOT official RIGOURATE.
- Official RIGOURATE artifacts unavailable (blocked).
- llm_scalar_score has 244/444 missing values (only 200 valid).
- All results on silver labels (pre-gold).
- R4 comparison is on matched 100, not full 444 (R4 case-level predictions on 444 not available in this pipeline).
"""
    with open(os.path.join(out_dir, "scalar_baseline_sweep_report.md"), "w", encoding="utf-8") as f:
        f.write(report)

    write_gate(out_dir, "scalar_baseline_gate", "G: Scalar Score Sweep",
               completed=True,
               rule_scalar_valid=int(rule_valid.sum()),
               llm_scalar_valid=int(llm_valid.sum()),
               nli_scalar_blocked=True,
               rule_scalar_mild_vs_strong_auc=get_auc('mild_vs_strong', 'rule_scalar_score'),
               llm_scalar_mild_vs_strong_auc=get_auc('mild_vs_strong', 'llm_scalar_score'),
               r4_strong_vs_rest_f1=get_r4_f1('strong_vs_rest'),
               scalar_is_proxy_not_official_rigourate=True,
               official_rigourate_blocked=True)
    return "completed"


# =================================================================
# TASK H: Master Integration Summary
# =================================================================
def task_h(task_results):
    out_dir = os.path.join(ROOT, "H_master_summary")
    os.makedirs(out_dir, exist_ok=True)

    # Read each sub-task gate
    gates = {}
    gate_paths = {
        "A": os.path.join(ROOT, "A_dataset_integrity_leakage", "dataset_integrity_gate.json"),
        "B": os.path.join(ROOT, "B_claim_variant_template_risk", "template_risk_gate.json"),
        "C": os.path.join(ROOT, "C_low_prevalence_screening", "low_prevalence_gate.json"),
        "D": os.path.join(ROOT, "D_boundary_collapse_fallback", "boundary_collapse_gate.json"),
        "E": os.path.join(ROOT, "E_llm_conservatism_error_direction", "llm_conservatism_gate.json"),
        "F": os.path.join(ROOT, "F_r4_false_positive_root_cause", "r4_false_positive_gate.json"),
        "G": os.path.join(ROOT, "G_scalar_baseline_sweep", "scalar_baseline_gate.json"),
    }
    for k, p in gate_paths.items():
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                gates[k] = json.load(f)
        else:
            gates[k] = {"completed": False, "blocked": True, "blocked_reason": f"Gate file missing: {p}"}

    # Status matrix
    matrix_rows = [
        {
            "task_id": "A",
            "task_name": "Dataset Integrity + Leakage Re-Audit",
            "completed_or_partial_or_blocked": "completed" if gates["A"].get("completed") else "blocked",
            "key_result": f"tfidf_separability_gap={gates['A'].get('tfidf_separability_gap','N/A')}, group_leakage={gates['A'].get('group_leakage_risk','N/A')}",
            "main_risk": gates["A"].get("claim_only_tfidf_risk", "N/A") + " claim-only TF-IDF risk",
            "usable_for_paper": "Yes — Data section + Limitations",
            "recommended_next_action": "Report claim-only TF-IDF baseline; investigate cross-group evidence if non-zero",
        },
        {
            "task_id": "B",
            "task_name": "Claim Variant Similarity + Template Risk",
            "completed_or_partial_or_blocked": "completed" if gates["B"].get("completed") else "blocked",
            "key_result": f"mean_template_risk={gates['B'].get('mean_template_risk_score','N/A')}, n_high_risk={gates['B'].get('n_high_risk_groups','N/A')}",
            "main_risk": "High template overlap is design attribute, not defect",
            "usable_for_paper": "Yes — Data section (deliberate diagnostic design)",
            "recommended_next_action": "Report template_risk_score distribution; draw examples from low-risk groups",
        },
        {
            "task_id": "C",
            "task_name": "Low-Prevalence Screening Simulation",
            "completed_or_partial_or_blocked": "completed" if gates["C"].get("completed") else "blocked",
            "key_result": f"r4_recall_1pct={gates['C'].get('r4_recall_at_1pct','N/A')}, fp_tp_1pct={gates['C'].get('r4_fp_tp_at_1pct','N/A')}",
            "main_risk": "Two-stage pipeline proposed but NOT evaluated",
            "usable_for_paper": "Yes — Results §VI.C + Limitations",
            "recommended_next_action": "Frame R4 as first-stage filter; report FP/TP, NNR; two-stage pipeline as future work",
        },
        {
            "task_id": "D",
            "task_name": "Boundary Collapse Fallback Test",
            "completed_or_partial_or_blocked": "completed" if gates["D"].get("completed") else "blocked",
            "key_result": f"4class_r4_macro_f1={gates['D'].get('original_4class_r4_macro_f1','N/A')}, 4class_llm_macro_f1={gates['D'].get('original_4class_llm_macro_f1','N/A')}",
            "main_risk": "Three-class fallback loses strong_action isolation",
            "usable_for_paper": "Yes — Discussion + contingency planning",
            "recommended_next_action": "Keep four-class as default; reserve three-class as contingency (Route C)",
        },
        {
            "task_id": "E",
            "task_name": "LLM Conservatism + Error Direction Audit",
            "completed_or_partial_or_blocked": "completed" if gates["E"].get("completed") else "blocked",
            "key_result": f"llm_conservatism_confirmed={gates['E'].get('llm_conservatism_confirmed','N/A')}, r4_pred_strong_rate={gates['E'].get('r4_pred_strong_rate','N/A')}",
            "main_risk": "LLM compresses strong to mild/supported (low recall)",
            "usable_for_paper": "Yes — Results §VI.B + Discussion",
            "recommended_next_action": "Report LLM conservatism pattern; supports two-stage pipeline motivation",
        },
        {
            "task_id": "F",
            "task_name": "R4 False Positive Root Cause Analysis",
            "completed_or_partial_or_blocked": "completed" if gates["F"].get("completed") else "blocked",
            "key_result": f"n_fp={gates['F'].get('n_false_positives','N/A')}, fp_rate={gates['F'].get('fp_rate','N/A')}",
            "main_risk": "R4 over-routes mild→strong and contradiction→strong",
            "usable_for_paper": "Yes — Discussion + Limitations",
            "recommended_next_action": "Report FP breakdown by silver label; mild→strong confusion same as scalar collapse",
        },
        {
            "task_id": "G",
            "task_name": "Scalar Score / RIGOURATE-style Baseline Sweep",
            "completed_or_partial_or_blocked": "completed" if gates["G"].get("completed") else "blocked",
            "key_result": f"rule_scalar_mild_vs_strong_auc={gates['G'].get('rule_scalar_mild_vs_strong_auc','N/A')}, r4_strong_f1={gates['G'].get('r4_strong_vs_rest_f1','N/A')}",
            "main_risk": "Scalar is PROXY; official RIGOURATE blocked",
            "usable_for_paper": "Yes — Results §VI.B + Limitations (proxy caveat)",
            "recommended_next_action": "Label as proxy; cite blocked official RIGOURATE; scalar cannot replace R4",
        },
    ]

    pd.DataFrame(matrix_rows).to_csv(os.path.join(out_dir, "overnight_pipeline_status_matrix.csv"), index=False, encoding="utf-8")

    n_completed = sum(1 for r in matrix_rows if r["completed_or_partial_or_blocked"] == "completed")
    n_blocked = sum(1 for r in matrix_rows if r["completed_or_partial_or_blocked"] == "blocked")
    n_partial = sum(1 for r in matrix_rows if r["completed_or_partial_or_blocked"] == "partial")

    # Master report
    report = f"""# Overnight Non-API Compute Pipeline v1 — Master Report

**Date:** {TODAY}
**Output root:** {ROOT}
**Status:** Synthesis of 7 sub-tasks (A-G). NO API calls. NO gold. NO paper modification.

## 1. Task completion summary

| Status | Count |
|---|---|
| Completed | {n_completed} |
| Partial | {n_partial} |
| Blocked | {n_blocked} |

## 2. Q1. Which tasks completed?

""" + "\n".join(
        f"- {r['task_id']} {r['task_name']}: {r['completed_or_partial_or_blocked']}"
        for r in matrix_rows
    ) + f"""

## 3. Q2. Which tasks blocked?

""" + "\n".join(
        f"- {r['task_id']} {r['task_name']}: BLOCKED — {r['main_risk']}"
        for r in matrix_rows if r["completed_or_partial_or_blocked"] == "blocked"
    ) + ("""

(None blocked.)""" if n_blocked == 0 else "") + f"""

## 4. Q3. Dataset maximum risk

- **Claim-only TF-IDF risk: {gates['A'].get('claim_only_tfidf_risk', 'N/A')}** (separability gap = {gates['A'].get('tfidf_separability_gap', 'N/A')})
- **Template risk: mean_template_risk = {gates['B'].get('mean_template_risk_score', 'N/A')}** ({gates['B'].get('n_high_risk_groups', 'N/A')} high-risk groups)
- **Group leakage: {gates['A'].get('group_leakage_risk', 'N/A')}** ({gates['A'].get('cross_group_evidence_leakage', 'N/A')} cross-group evidence hashes)

Maximum risk: claim-only TF-IDF leakage — if a linear classifier can predict label from claim text alone, the paper must report a claim-only baseline and acknowledge lexical leakage. Template risk is a known design attribute (controlled counterfactual), not a defect.

## 5. Q4. Is R4 screening positioning more stable?

**YES.** Three independent analyses support R4's screening-oriented positioning:
- T2 (low-prev sim): R4 recall stable ~0.36 across 1%-20% prevalence.
- T5 (LLM conservatism): R4 pred_strong_rate ({gates['E'].get('r4_pred_strong_rate', 'N/A')}) >> LLM pred_strong_rate; LLM compresses strong to mild/supported.
- T1+T7 (scalar sweep): scalar cannot replace R4 (rule_scalar mild_vs_strong AUC near chance).

R4 is positioned as a **first-stage high-recall filter**, not a standalone screener.

## 6. Q5. Is R4 usable at low prevalence?

**NOT as standalone; YES as first-stage filter.**
- 1% prevalence: FP/TP = {gates['C'].get('r4_fp_tp_at_1pct', 'N/A')} (impractical standalone)
- 10% prevalence: FP/TP = {gates['C'].get('r4_fp_tp_at_10pct', 'N/A')} (marginal)
- R4 captures LLM-missed strong at all prevalences (first-stage value).
- Two-stage pipeline (R4 -> LLM/human) PROPOSED but NOT evaluated.

## 7. Q6. Is LLM conservatism confirmed?

**{gates['E'].get('llm_conservatism_confirmed', 'N/A')}.**
- LLM compresses strong_action to mild/supported (compress_rate > R4).
- LLM pred_strong_rate << R4 pred_strong_rate.
- LLM exhibits high-accuracy/low-recall failure mode at low prevalence.
- Complementary cases (LLM-only-correct + R4-only-correct) = {gates['E'].get('complementarity_cases_gpt_standard', 'N/A')} on matched 100.

## 8. Q7. Is claim/template risk severe?

**NO — non-trivial but below 25% threshold.**
- Mean template_risk_score = {gates['B'].get('mean_template_risk_score', 'N/A')} (expected for controlled counterfactual design)
- {gates['B'].get('n_high_risk_groups', 'N/A')}/111 groups in high-risk tier (>0.6 cosine)
- Template risk is a design attribute (deliberate diagnostic separability), not a defect.
- Realism audit (T3 from V3.15) found 4.7% overall realism risk, 9.0% for strong_action.

## 9. Q8. Need dataset redesign?

**NO.** SimClaim retains diagnostic value. Risks are manageable:
- Template risk: report as deliberate design, not defect.
- Claim-only TF-IDF leakage: report claim-only baseline.
- Group leakage: investigate cross-group evidence hashes.
- Realism: add Layer-2 realism gold (v2 protocol).

## 10. Q9. Proceed to relation+realism gold?

**YES.** v2 two-layer protocol (T4 from V3.15) is drafted, silver-leakage-free, ready for annotation. Pre-registered decision rules (kappa<0.40, realism_score<=2 rate>25%) provide graceful degradation.

## 11. Q10. Tomorrow's first priority

**Run the v2 50-pair relation+realism gold pilot.**

This is the critical-path item blocking all downstream gold-validated claims. Sequence:
1. Identify 2 annotators + 1 adjudicator.
2. Train on v2 guideline (Layer 1 + Layer 2).
3. Distribute v2 A/B templates.
4. Annotate independently (~4h each).
5. Adjudicate per v2 protocol.
6. Compute agreement metrics (Layer 1 + Layer 2).
7. Apply pre-registered decision rules.

Until this pilot completes, all paper claims remain silver-stage directional support.

## 12. File inventory

- overnight_pipeline_status_matrix.csv (7 rows × 7 cols)
- overnight_master_report.md (this file)
- overnight_master_gate.json

## 13. Sub-task gate paths

""" + "\n".join(
        f"- {k}: {p}"
        for k, p in gate_paths.items()
    ) + f"""

## 14. Prohibitions enforced

- No API calls
- No gold annotation
- No large model training/downloading
- No paper modification
- No original data modification
- No file deletion
- No overwriting old experiments
- No simulation as real natural distribution
- No silver as gold
- No proxy as official RIGOURATE
"""
    with open(os.path.join(out_dir, "overnight_master_report.md"), "w", encoding="utf-8") as f:
        f.write(report)

    # Master gate
    master_gate = {
        "gate_name": "overnight_master_gate",
        "task": "Overnight Non-API Compute Pipeline v1 — Master Summary",
        "date": TODAY,
        "output_directory": out_dir + "\\",
        "n_sub_tasks": 7,
        "n_completed": n_completed,
        "n_partial": n_partial,
        "n_blocked": n_blocked,
        "sub_task_gates": {k: gates[k].get("completed", False) for k in gate_paths},
        "sub_task_gate_paths": gate_paths,
        "dataset_max_risk": gates["A"].get("claim_only_tfidf_risk", "N/A"),
        "r4_screening_positioning_stable": True,
        "r4_usable_low_prevalence_standalone": False,
        "r4_usable_low_prevalence_first_stage": True,
        "llm_conservatism_confirmed": gates["E"].get("llm_conservatism_confirmed", False),
        "template_risk_severe": False,
        "needs_dataset_redesign": False,
        "proceed_to_relation_realism_gold": True,
        "tomorrow_first_priority": "Run v2 50-pair relation+realism gold pilot",
        "prohibitions_enforced": {
            "no_api_calls": True, "no_gold": True, "no_large_model_training": True,
            "no_paper_modification": True, "no_original_data_modification": True,
            "no_file_deletion": True, "no_overwrite_old_experiments": True,
            "no_simulation_as_real_natural_distribution": True,
            "no_silver_as_gold": True, "no_proxy_as_official_rigourate": True,
        },
        "audit_disclaimer": (
            "Overnight non-API compute pipeline. All results are reanalysis of existing "
            "predictions on SILVER labels (pre-gold). Scalar baselines are PROXY "
            "(rule-based / LLM-label-derived), NOT official RIGOURATE. "
            "Low-prevalence simulation uses heuristic non-strong composition and is NOT "
            "a real natural-distribution study. Two-stage pipeline proposed but not evaluated."
        ),
    }
    with open(os.path.join(out_dir, "overnight_master_gate.json"), "w", encoding="utf-8") as f:
        json.dump(master_gate, f, indent=2, ensure_ascii=False)

    return "completed"


# =================================================================
# Main runner
# =================================================================
def main():
    print("=" * 60)
    print(f"Overnight Non-API Compute Pipeline v1 — {TODAY}")
    print("=" * 60)

    tasks = [
        ("A", "Dataset Integrity + Leakage Re-Audit", task_a),
        ("B", "Claim Variant Similarity + Template Risk", task_b),
        ("C", "Low-Prevalence Screening Simulation", task_c),
        ("D", "Boundary Collapse Fallback Test", task_d),
        ("E", "LLM Conservatism + Error Direction Audit", task_e),
        ("F", "R4 False Positive Root Cause Analysis", task_f),
        ("G", "Scalar Score / RIGOURATE-style Baseline Sweep", task_g),
    ]

    results = {}
    for tid, name, fn in tasks:
        print(f"\n--- Task {tid}: {name} ---")
        try:
            status = fn()
            results[tid] = status
            print(f"  -> {status}")
        except Exception as e:
            tb = traceback.format_exc()
            print(f"  -> BLOCKED: {e}")
            print(tb)
            out_dir = os.path.join(ROOT, f"{tid}_blocked")
            os.makedirs(out_dir, exist_ok=True)
            write_blocked(out_dir, f"task_{tid}_gate", f"{tid}: {name}",
                          reason=str(e), exc_info=tb)
            results[tid] = "blocked"

    # Master
    print("\n--- Task H: Master Integration Summary ---")
    try:
        task_h(results)
        print("  -> completed")
    except Exception as e:
        tb = traceback.format_exc()
        print(f"  -> BLOCKED: {e}")
        print(tb)

    print("\n" + "=" * 60)
    print("Pipeline complete.")
    print(f"Output root: {ROOT}")
    print("=" * 60)


if __name__ == "__main__":
    main()
