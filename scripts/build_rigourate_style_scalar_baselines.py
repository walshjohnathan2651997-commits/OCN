"""Build 3 RIGOURATE-style scalar overstatement baselines on SimClaim 444 pairs.

Baselines:
  A. rule_scalar_score: cue-based 0-3 score on action/deployment/safety/policy/
     generalization/guarantee/always/fully/replace + evidence limitation cues.
  B. nli_scalar_score: reuses HCM/NLI features. BLOCKED - features not in repo.
  C. llm_scalar_proxy: maps existing LLM parsed outputs to scalar
     (supported=0, mild=1, strong=2, contradiction=3). LLM-label-derived proxy.

Output: rigourate_style_scalar_scores.csv with fields:
  candidate_id, sample_id_if_available, silver_label, claim_text, evidence_text,
  domain, rule_scalar_score, nli_scalar_score, llm_scalar_score_if_available,
  score_notes

Prohibitions enforced:
  - No paid API calls
  - No gold creation
  - No silver-as-gold
  - No claiming proxy as official RIGOURATE
  - No modification of original data
"""
import os
import re
import csv
import json

import pandas as pd

BASE = r"D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1"
SILVER_DIR = r"D:\ocn\experiments\strict_silver_max_v1"
LLM_200 = r"D:\ocn\experiments\llm_judge_baseline_v1\llm_parsed_outputs_200.csv"
LLM_100 = r"D:\ocn\experiments\llm_judge_baseline_v1\llm_parsed_outputs_100.csv"
OUT_CSV = os.path.join(BASE, "rigourate_style_scalar_scores.csv")
OUT_NOTES = os.path.join(BASE, "baseline_build_notes.md")

# Cue lists for rule_scalar_score (Baseline A)
# Per task spec: action/deployment/safety/policy/generalization/guarantee/always/fully/replace
# plus evidence limitation cues.

STRONG_ACTION_CUES = [
    "action", "actions",
    "deployment", "deploy", "deploying", "deployed",
    "safety", "safe",
    "policy", "policies",
    "generalization", "generalize", "generalises", "generalizes", "generalisable", "generalizable",
    "guarantee", "guarantees", "guaranteed",
    "always",
    "fully", "full",
    "replace", "replaces", "replacing", "replaced",
    "operational", "operationally",
    "ready", "readiness",
    "production-ready", "deployment-ready",
    "robust", "robustly", "robustness",
    "fail-safe", "failsafe",
]

MILD_SCOPE_CUES = [
    "broader", "broaden", "broad",
    "all", "every", "each",
    "more", "most",
    "extends", "extended", "extend",
    "comprehensive", "comprehensively",
    "universal", "universally",
    "complete", "completely",
    "various", "diverse",
    "any",
    "across",
    "wide", "widely",
]

CONTRADICTION_CUES = [
    "not ", "n't ", "cannot", "can't", "does not", "does n't", "do not", "do n't",
    "is not", "are not", "was not", "were not",
    "fails", "failed", "failing",
    "unable", "unable to",
    "contradict", "contradicts", "contradicted", "contradiction",
    "however", "but ", "although", "though",
    "despite", "in contrast",
    "no ", "none",
    "never",
    "opposite", "opposes", "opposed",
]

EVIDENCE_LIMITATION_CUES = [
    "limited", "limitation", "limits",
    "single", "only one", "one ",
    "small sample", "small-scale", "small scale",
    "few ", "a few",
    "preliminary",
    "initial",
    "partial", "partially",
    "narrow",
    "specific", "specifically",
    "under", "under-powered", "underpowered",
    "insufficient",
    "lack", "lacks", "lacking",
    "not enough",
    "modest",
    "restricted",
]


def normalize_text(text):
    if not isinstance(text, str):
        return ""
    return text.lower()


def count_cue_matches(text_lower, cues):
    """Count how many distinct cues from the list appear in text."""
    matches = []
    for cue in cues:
        # Use word-boundary matching for short cues; substring for longer
        if len(cue.strip()) <= 3:
            pattern = r'\b' + re.escape(cue.strip()) + r'\b'
            if re.search(pattern, text_lower):
                matches.append(cue)
        else:
            if cue in text_lower:
                matches.append(cue)
    return matches


def rule_scalar_score(claim_text, evidence_text):
    """Compute rule-based scalar overstatement score in {0, 1, 2, 3}.

    Priority: contradiction (3) > strong action (2) > mild scope (1) > supported (0).
    Evidence limitation cues add +1 but score is capped at 3.

    Returns (score, matched_cues_dict)
    """
    claim_lower = normalize_text(claim_text)
    evidence_lower = normalize_text(evidence_text)

    contra_in_claim = count_cue_matches(claim_lower, CONTRADICTION_CUES)
    contra_in_evidence = count_cue_matches(evidence_lower, CONTRADICTION_CUES)
    action_in_claim = count_cue_matches(claim_lower, STRONG_ACTION_CUES)
    action_in_evidence = count_cue_matches(evidence_lower, STRONG_ACTION_CUES)
    mild_in_claim = count_cue_matches(claim_lower, MILD_SCOPE_CUES)
    mild_in_evidence = count_cue_matches(evidence_lower, MILD_SCOPE_CUES)
    limit_in_evidence = count_cue_matches(evidence_lower, EVIDENCE_LIMITATION_CUES)

    matched = {
        "contra_in_claim": contra_in_claim,
        "contra_in_evidence": contra_in_evidence,
        "action_in_claim": action_in_claim,
        "action_in_evidence": action_in_evidence,
        "mild_in_claim": mild_in_claim,
        "mild_in_evidence": mild_in_evidence,
        "limit_in_evidence": limit_in_evidence,
    }

    # Priority scoring
    if contra_in_claim or contra_in_evidence:
        base = 3
        reason = "contradiction_cue"
    elif action_in_claim or action_in_evidence:
        base = 2
        reason = "strong_action_cue"
    elif mild_in_claim or mild_in_evidence:
        base = 1
        reason = "mild_scope_cue"
    else:
        base = 0
        reason = "no_cue"

    # Evidence limitation adds +1 (capped at 3)
    if limit_in_evidence and base < 3:
        base = min(3, base + 1)
        reason = reason + "+evidence_limitation"

    return base, reason, matched


def map_label_to_scalar(label):
    """Map 4-class label to scalar score (Baseline C mapping).

    supported=0, mild_scope_overclaim=1, strong_action_overclaim=2, contradiction_candidate=3
    """
    if not isinstance(label, str):
        return None
    label = label.strip().lower()
    mapping = {
        "supported": 0,
        "mild_scope_overclaim": 1,
        "mild": 1,
        "strong_action_overclaim": 2,
        "strong": 2,
        "contradiction_candidate": 3,
        "contradiction": 3,
    }
    return mapping.get(label, None)


def derive_group_id(candidate_id):
    """Strip the last segment to get group_id.

    SBV2-ALL92-G004-SUPPORTED -> SBV2-ALL92-G004
    SBV2-ALL92-G028-C01 -> SBV2-ALL92-G028
    """
    parts = candidate_id.split("-")
    if len(parts) >= 4:
        return "-".join(parts[:-1])
    return candidate_id


def load_silver_data():
    """Load all 444 SimClaim silver pairs from train+dev+test.

    Silver label is in `candidate_label_guess` (final_label and gold_label are empty).
    """
    dfs = []
    for split in ["train", "dev", "test"]:
        path = os.path.join(SILVER_DIR, f"{split}.csv")
        df = pd.read_csv(path, keep_default_na=False)
        df["split"] = split
        dfs.append(df)
    all_df = pd.concat(dfs, ignore_index=True)
    # Use candidate_label_guess as silver label
    all_df["silver_label"] = all_df["candidate_label_guess"]
    # Derive group_id
    all_df["group_id"] = all_df["candidate_id"].apply(derive_group_id)
    return all_df


def load_llm_outputs():
    """Load LLM parsed outputs from 200-sample file (preferred) and 100-sample file.

    Returns dict: (group_id, silver_label) -> {sample_id, llm_label, llm_scalar, model}
    Key by (group_id, silver_label) so we can match to strict_silver candidates.
    """
    out = {}
    # Use 200 first, then 100 (200 is the larger set)
    for path in [LLM_200, LLM_100]:
        if not os.path.exists(path):
            continue
        df = pd.read_csv(path, keep_default_na=False)
        for _, row in df.iterrows():
            candidate_id = row.get("candidate_id", "")
            silver = row.get("label_4_silver", "")
            sample_id = row.get("sample_id", "")
            llm_label = row.get("llm_label", "")
            model = row.get("model", "")
            group_id = derive_group_id(candidate_id)
            key = (group_id, silver.strip().lower() if isinstance(silver, str) else "")
            llm_scalar = map_label_to_scalar(llm_label)
            if key not in out:  # don't overwrite 200 with 100
                out[key] = {
                    "sample_id": sample_id,
                    "llm_label": llm_label,
                    "llm_scalar": llm_scalar,
                    "model": model,
                }
    return out


def main():
    print("Loading SimClaim silver data...")
    silver_df = load_silver_data()
    print(f"  Total rows: {len(silver_df)}")
    print(f"  Splits: {silver_df['split'].value_counts().to_dict()}")
    print(f"  Silver label distribution: {silver_df['silver_label'].value_counts().to_dict()}")

    print("\nLoading LLM parsed outputs...")
    llm_map = load_llm_outputs()
    print(f"  LLM entries loaded: {len(llm_map)}")

    print("\nBuilding scalar baselines...")
    rows = []
    rule_label_dist = {0: 0, 1: 0, 2: 0, 3: 0}
    llm_matched = 0
    llm_unmatched = 0

    for _, row in silver_df.iterrows():
        candidate_id = row["candidate_id"]
        silver_label = row["silver_label"]
        claim_text = row["claim_text"]
        evidence_text = row["evidence_text"]
        domain = row["domain"]
        group_id = row["group_id"]

        # Baseline A: rule_scalar_score
        rule_score, rule_reason, matched_cues = rule_scalar_score(claim_text, evidence_text)
        rule_label_dist[rule_score] = rule_label_dist.get(rule_score, 0) + 1

        # Baseline B: nli_scalar_score - BLOCKED (no HCM/NLI features in repo)
        nli_score = "blocked"
        nli_notes = "HCM/NLI features not present in repo; searched D:\\ocn recursively for hcm*.csv, nli*.csv, *features*.csv - no matches outside .venv"

        # Baseline C: llm_scalar_proxy
        # Try to match via (group_id, silver_label)
        key = (group_id, silver_label.strip().lower() if isinstance(silver_label, str) else "")
        if key in llm_map:
            llm_entry = llm_map[key]
            llm_scalar = llm_entry["llm_scalar"]
            llm_sample_id = llm_entry["sample_id"]
            llm_matched += 1
            llm_note = f"matched via (group_id, silver_label); llm_label={llm_entry['llm_label']}; model={llm_entry['model']}"
        else:
            llm_scalar = ""
            llm_sample_id = ""
            llm_unmatched += 1
            llm_note = "no LLM parsed output for this (group_id, silver_label)"

        # Build score_notes
        cue_summary = []
        for cue_type, cues in matched_cues.items():
            if cues:
                cue_summary.append(f"{cue_type}={','.join(cues[:3])}")
        score_notes = f"rule_reason={rule_reason}; cues=[{'|'.join(cue_summary)}]; llm_note={llm_note}; nli_blocked"

        rows.append({
            "candidate_id": candidate_id,
            "sample_id_if_available": llm_sample_id,
            "silver_label": silver_label,
            "claim_text": claim_text,
            "evidence_text": evidence_text,
            "domain": domain,
            "rule_scalar_score": rule_score,
            "nli_scalar_score": nli_score,
            "llm_scalar_score_if_available": llm_scalar,
            "score_notes": score_notes,
        })

    out_df = pd.DataFrame(rows)
    out_df.to_csv(OUT_CSV, index=False, encoding="utf-8")
    print(f"\nWritten: {OUT_CSV} ({len(out_df)} rows)")

    print(f"\n=== Baseline A (rule_scalar_score) distribution ===")
    print(f"  Score distribution: {rule_label_dist}")
    # Cross-tab rule score vs silver label
    crosstab = pd.crosstab(out_df["rule_scalar_score"], out_df["silver_label"], margins=True)
    print(crosstab)

    print(f"\n=== Baseline B (nli_scalar_score) ===")
    print(f"  Status: BLOCKED for all 444 rows")
    print(f"  Reason: HCM/NLI features not present in repo")

    print(f"\n=== Baseline C (llm_scalar_proxy) ===")
    print(f"  Matched to LLM data: {llm_matched}")
    print(f"  Unmatched: {llm_unmatched}")
    if llm_matched > 0:
        matched_df = out_df[out_df["llm_scalar_score_if_available"] != ""].copy()
        matched_df["llm_scalar_int"] = matched_df["llm_scalar_score_if_available"].astype(int)
        print(f"  LLM scalar distribution: {matched_df['llm_scalar_int'].value_counts().sort_index().to_dict()}")

    # Write build notes
    notes = f"""# Scalar Baseline Build Notes

**Task:** RIGOURATE Reproduction + SimClaim Differentiation v1 - Section 4 Build 3 scalar baselines
**Date:** 2026-07-05
**Output:** rigourate_style_scalar_scores.csv ({len(out_df)} rows)

## Silver label source

The strict_silver_max_v1 CSVs have empty `final_label` and `gold_label` columns (silver is pre-gold).
The actual silver label is in `candidate_label_guess` (e.g., supported / mild_scope_overclaim /
strong_action_overclaim / contradiction_candidate). This is used as `silver_label` in the output.

## Baseline A: rule_scalar_score

- **Status:** COMPLETED for all 444 pairs.
- **Method:** Cue-based priority scoring on claim_text + evidence_text.
  - Priority: contradiction (3) > strong_action (2) > mild_scope (1) > supported (0).
  - Evidence limitation cues add +1 (capped at 3).
- **Cue lists:**
  - STRONG_ACTION_CUES: action, deployment, safety, policy, generalization, guarantee, always, fully, replace, operational, ready, production-ready, robust, etc.
  - MILD_SCOPE_CUES: broader, all, every, more, extends, comprehensive, universal, complete, various, any, across, wide, etc.
  - CONTRADICTION_CUES: not, cannot, does not, fails, unable, contradict, however, but, despite, no, none, never, opposite, etc.
  - EVIDENCE_LIMITATION_CUES: limited, single, only one, small sample, few, preliminary, initial, partial, narrow, specific, insufficient, lack, modest, restricted, etc.
- **Score distribution:** {rule_label_dist}

## Baseline B: nli_scalar_score

- **Status:** BLOCKED for all 444 pairs.
- **blocked_reason:** HCM/NLI features not present in repo. Searched D:\\ocn recursively for hcm*.csv, nli*.csv, *features*.csv - no matches outside .venv. The previously referenced path D:\\ocn\\_ARCHIVE_NON_MAINLINE\\experiments\\cese_ocn_hcm_v1\\ does not exist.
- **Implication:** Baseline B cannot be computed. Section 5 evaluation will use only Baseline A (rule_scalar_score) and Baseline C (llm_scalar_proxy).

## Baseline C: llm_scalar_proxy

- **Status:** COMPLETED for matched subset; empty for unmatched.
- **Method:** Map existing LLM parsed outputs to scalar:
  - supported=0, mild_scope_overclaim=1, strong_action_overclaim=2, contradiction_candidate=3
- **Source:** D:\\ocn\\experiments\\llm_judge_baseline_v1\\llm_parsed_outputs_200.csv (200 samples, primary) and llm_parsed_outputs_100.csv (100 samples, fallback).
- **Matching:** Joined to strict_silver via (group_id, silver_label). Group_id is derived by stripping the last segment of candidate_id (e.g., SBV2-ALL92-G028-C01 -> SBV2-ALL92-G028; SBV2-ALL92-G004-SUPPORTED -> SBV2-ALL92-G004). Silver label is from candidate_label_guess in strict_silver and label_4_silver in LLM file.
- **Matched:** {llm_matched} / 444 rows
- **Unmatched:** {llm_unmatched} / 444 rows
- **Important:** This is an LLM-LABEL-DERIVED PROXY. It does NOT call any new API. It is NOT the official RIGOURATE scalar score. It uses the LLM's predicted 4-class label mapped to a 0-3 scalar.

## Prohibitions enforced

- No paid API calls.
- No gold creation.
- No silver-as-gold.
- No claiming proxy as official RIGOURATE.
- No modification of original data.

## Output file

- **Path:** {OUT_CSV}
- **Rows:** {len(out_df)}
- **Fields:** candidate_id, sample_id_if_available, silver_label, claim_text, evidence_text, domain, rule_scalar_score, nli_scalar_score, llm_scalar_score_if_available, score_notes
"""
    with open(OUT_NOTES, "w", encoding="utf-8") as f:
        f.write(notes)
    print(f"\nWritten: {OUT_NOTES}")


if __name__ == "__main__":
    main()
