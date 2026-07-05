# Scalar Baseline Build Notes

**Task:** RIGOURATE Reproduction + SimClaim Differentiation v1 - Section 4 Build 3 scalar baselines
**Date:** 2026-07-05
**Output:** rigourate_style_scalar_scores.csv (444 rows)

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
- **Score distribution:** {0: 118, 1: 80, 2: 107, 3: 139}

## Baseline B: nli_scalar_score

- **Status:** BLOCKED for all 444 pairs.
- **blocked_reason:** HCM/NLI features not present in repo. Searched D:\ocn recursively for hcm*.csv, nli*.csv, *features*.csv - no matches outside .venv. The previously referenced path D:\ocn\_ARCHIVE_NON_MAINLINE\experiments\cese_ocn_hcm_v1\ does not exist.
- **Implication:** Baseline B cannot be computed. Section 5 evaluation will use only Baseline A (rule_scalar_score) and Baseline C (llm_scalar_proxy).

## Baseline C: llm_scalar_proxy

- **Status:** COMPLETED for matched subset; empty for unmatched.
- **Method:** Map existing LLM parsed outputs to scalar:
  - supported=0, mild_scope_overclaim=1, strong_action_overclaim=2, contradiction_candidate=3
- **Source:** D:\ocn\experiments\llm_judge_baseline_v1\llm_parsed_outputs_200.csv (200 samples, primary) and llm_parsed_outputs_100.csv (100 samples, fallback).
- **Matching:** Joined to strict_silver via (group_id, silver_label). Group_id is derived by stripping the last segment of candidate_id (e.g., SBV2-ALL92-G028-C01 -> SBV2-ALL92-G028; SBV2-ALL92-G004-SUPPORTED -> SBV2-ALL92-G004). Silver label is from candidate_label_guess in strict_silver and label_4_silver in LLM file.
- **Matched:** 200 / 444 rows
- **Unmatched:** 244 / 444 rows
- **Important:** This is an LLM-LABEL-DERIVED PROXY. It does NOT call any new API. It is NOT the official RIGOURATE scalar score. It uses the LLM's predicted 4-class label mapped to a 0-3 scalar.

## Prohibitions enforced

- No paid API calls.
- No gold creation.
- No silver-as-gold.
- No claiming proxy as official RIGOURATE.
- No modification of original data.

## Output file

- **Path:** D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1\rigourate_style_scalar_scores.csv
- **Rows:** 444
- **Fields:** candidate_id, sample_id_if_available, silver_label, claim_text, evidence_text, domain, rule_scalar_score, nli_scalar_score, llm_scalar_score_if_available, score_notes
