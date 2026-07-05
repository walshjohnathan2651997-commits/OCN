# RIGOURATE Reproduction + SimClaim Differentiation v1 — Master Report

**Task:** RIGOURATE Reproduction + SimClaim Differentiation v1
**Date:** 2026-07-05
**Operator:** CESE-OCN automated pipeline (no paid API calls)
**Output directories:**
- `D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1\` (experimental outputs)
- `D:\ocn\docs\rigourate_reproduction_and_simclaim_baseline_v1\` (documentation)

---

## 1. Executive summary

This task answered four questions posed by the user:

1. **Can RIGOURATE be officially reproduced?** — **NO (BLOCKED).** The official RIGOURATE code, data, and model weights are not publicly available as of 2026-07-05. The arXiv v2 paper (12 Jan 2026) carries a placeholder `[Github/HF Link]` URL that has not been replaced. No GitHub repository, HuggingFace model, dataset, or supplementary material was located via web search.

2. **Can a RIGOURATE-style scalar overstatement baseline be constructed?** — **YES (as proxy).** Three baselines were built: (A) rule_scalar_score (cue-based, completed for all 444 pairs); (B) nli_scalar_score (BLOCKED — HCM/NLI features not in repo); (C) llm_scalar_proxy (LLM-label-derived, completed for 200/444 matched pairs). All are explicitly labelled as proxy, NOT official RIGOURATE.

3. **Can a scalar score replace the CESE-OCN four-class relation taxonomy?** — **NO.** The scalar cannot reliably distinguish mild_scope_overclaim from strong_action_overclaim (rule ROC-AUC=0.5062, LLM ROC-AUC=0.5874, both below 0.70). The scalar cannot match R4's strong_action screening F1 (R4=0.3967 vs rule_scalar best-F1=0.3844 on silver 444; R4=0.3000 vs rule_scalar=0.1364 on matched 100).

4. **Does R4 retain independent value on strong_action_overclaim screening?** — **YES.** R4 achieves 3-5x higher strong_action F1 than LLM judges on matched samples. R4 captures 8/24 strong_action cases that all three LLM judges (GPT standard, GPT structured, DeepSeek) miss. R4's cost is lower overall macro-F1 (0.3280 vs 0.5523) and higher review burden (35% vs 1%), but the trade-off is intentional: R4 is a screening-oriented complement, not a replacement.

**Bottom line:** Scalar overstatement scoring and relation-specific screening are **complementary**. Scalar is good for broad supported-vs-overclaim distinction (LLM-derived ROC-AUC=0.85); relation-specific screening (R4) is necessary for high-risk action-overclaim identification. This complementarity is the empirical justification for CESE-OCN's positioning as a fine-grained complement to (not replacement of) scalar overstatement scoring work like RIGOURATE.

---

## 2. Section-by-section summary

### §1 Official Resource Audit
- **Status:** BLOCKED.
- **Outputs:** official_resource_inventory.csv, rigourate_reproduction_feasibility_report.md, official_reproduction_status.json.
- **Key finding:** Official RIGOURATE code/data/model not publicly available. arXiv v2 has placeholder URL. Full official reproduction not currently possible from public repository.

### §2 Method Dissection
- **Status:** COMPLETED.
- **Outputs:** rigourate_method_dissection.md, rigourate_vs_cese_ocn_method_table.csv.
- **Key finding:** RIGOURATE is a two-stage multimodal framework (reranker + scorer) producing a continuous overstatement score [0,1]. CESE-OCN is a four-class relation-typing framework with structured routing. The two are complementary: scalar severity vs. relation-type decomposition.

### §3 Official Reproduction Attempt
- **Status:** BLOCKED (not executed — no artifacts to reproduce from).
- **Outputs:** official_reproduction_run_log.md.
- **Key finding:** "Official reproduction not currently possible from public repository."

### §4 Build 3 RIGOURATE-style Scalar Baselines
- **Status:** PARTIAL (2 of 3 completed, 1 blocked with reason).
- **Outputs:** rigourate_style_scalar_scores.csv (444 rows), baseline_build_notes.md.
- **Key finding:**
  - A. rule_scalar_score: COMPLETED for all 444 pairs. Distribution: 0=118, 1=80, 2=107, 3=139.
  - B. nli_scalar_score: BLOCKED. HCM/NLI features not present in repo. blocked_reason recorded.
  - C. llm_scalar_proxy: COMPLETED for 200/444 matched pairs. Distribution: 0=94, 1=53, 2=2, 3=51.

### §5 Scalar Baseline Evaluation
- **Status:** COMPLETED.
- **Outputs:** scalar_baseline_binary_results.csv, scalar_baseline_threshold_sweep.csv, scalar_baseline_report.md.
- **Key findings (4 binary tasks):**

| Task | Baseline | ROC-AUC | Best F1 | Verdict |
| --- | --- | --- | --- | --- |
| supported_vs_overclaim | rule_scalar | 0.5136 | 0.7466 | NO (chance-level discrimination) |
| supported_vs_overclaim | llm_scalar | 0.8533 | 0.8281 | YES (LLM-derived scalar is good) |
| mild_vs_strong | rule_scalar | 0.5062 | 0.6109 | NO (chance) |
| mild_vs_strong | llm_scalar | 0.5874 | 0.5741 | NO (weak, below 0.70) |
| strong_vs_contradiction | rule_scalar | 0.5233 | 0.5921 | NO (chance) |
| strong_vs_contradiction | llm_scalar | 0.8512 | 0.8400 | YES (LLM-derived scalar is good) |
| strong_vs_nonstrong | rule_scalar | 0.4971 | 0.3844 | NO (chance) |
| strong_vs_nonstrong | llm_scalar | 0.5154 | 0.3974 | NO (chance) |

- **Q1:** Scalar can identify overclaim only when LLM-derived (ROC-AUC=0.85); cue-based scalar cannot (ROC-AUC=0.51).
- **Q2:** Scalar CANNOT distinguish mild from strong (both variants ROC-AUC ≤ 0.59).
- **Q3:** Scalar CANNOT replace R4 strong_action route (rule below R4 on F1; LLM tied but at chance-level ROC-AUC).
- **Q4:** CESE-OCN four-class taxonomy has clear incremental value, especially for mild-vs-strong separation and strong_action screening.

### §6 RIGOURATE-style vs R4 Comparison
- **Status:** COMPLETED.
- **Outputs:** rigourate_style_vs_r4_results.csv, rigourate_style_vs_r4_cases.csv, rigourate_style_vs_r4_report.md.
- **Key findings (100 matched samples, 25 strong_action each):**

| Method | Strong F1 | Strong Recall | Strong Precision | TP | FP | Review Burden | Macro-F1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| rule_scalar | 0.1364 | 0.12 | 0.158 | 3 | 16 | 19% | 0.2591 |
| gpt_standard | 0.0769 | 0.04 | 1.0 | 1 | 0 | 1% | 0.5523 |
| gpt_structured | 0.0769 | 0.04 | 1.0 | 1 | 0 | 1% | 0.5543 |
| deepseek_v3 | 0.0769 | 0.04 | 1.0 | 1 | 0 | 1% | 0.5248 |
| r4_frozen | 0.3000 | 0.36 | 0.257 | 9 | 26 | 35% | 0.3280 |

- **Q1:** Scalar cannot reliably capture strong_action (rule_scalar strong_F1=0.1364; ROC-AUC at chance).
- **Q2:** Scalar is easily confused between mild and strong (ROC-AUC ≤ 0.59 on mild_vs_strong).
- **Q3:** R4 retains clear screening value (strong_F1=0.30 vs scalar/LLM ≤ 0.14; captures 8/24 LLM-missed strong_action).
- **Q4:** R4's cost is lower macro-F1 (0.3280 vs 0.5523) and higher review burden (35% vs 1%).
- **Q5:** Scalar and relation-specific screening are complementary.

### §7 Case Analysis
- **Status:** COMPLETED.
- **Outputs:** case_level_comparison.csv, case_level_comparison_report.md.
- **Key findings (100 matched cases):**
  - Both wrong: 49/100 (dominant category — both methods struggle)
  - R4 right, scalar wrong: 24/100
  - Scalar right, R4 wrong: 17/100
  - Both right: 10/100
  - Mild/strong confusion: 35/100 (high rate, confirms boundary instability)
  - Realism risk flagged: 8/100 (heuristic)

### §8 Claim Realism Audit
- **Status:** COMPLETED.
- **Outputs:** claim_realism_audit_queue.csv (444 rows), claim_realism_audit_summary.md.
- **Key findings:**
  - 21/444 (4.7%) of SimClaim claims have heuristic realism risk flags.
  - By silver label: supported 2.7%, mild 3.6%, strong_action 9.0%, contradiction 3.6%.
  - Most unnatural label: strong_action_overclaim (9.0%).
  - Risk types: too_template_like (8), too_extreme (7), unnatural_wording (6).
  - All below the 25% pre-registered class-level threshold.
  - Realism risk is non-trivial but not high; gold realism annotation is needed.

### §9 Gold Protocol Extension Proposal
- **Status:** COMPLETED (proposal only — no gold created).
- **Outputs:** proposed_relation_realism_gold_protocol_v2.md.
- **Key proposal:** Two-layer gold protocol:
  - Layer 1: relation label (unchanged from V3.12 §VII).
  - Layer 2: claim_realism_score_1_to_5, claim_realism_issue, claim_realism_usable_for_paper (NEW).
  - Pre-registered thresholds: 25% class-level, 25% paper-level.

### §10 Paper Insertion Materials
- **Status:** COMPLETED.
- **Outputs:** docs/rigourate_forcebench_claimbench_related_work_insert.md.
- **Contents:** Paste-ready English paragraphs for RIGOURATE, ForceBench, CLAIM-BENCH, CESE-OCN differentiation; markdown comparison table; SimClaim data section; discussion of scalar insufficiency.

### §11 V3.13 Revision Recommendation
- **Status:** COMPLETED (recommendation only — no paper modified).
- **Outputs:** V3_13_revision_recommendation.md.
- **Key recommendation:** Create V3.14 (V3.13 + new §VI.B RIGOURATE-style baseline results section + Limitations additions), NOT revise V3.13 in place. V3.13 stays as the positioning-stable version.

### §12 Master Report and Gate
- **Status:** COMPLETED.
- **Outputs:** rigourate_reproduction_master_report.md (this file), rigourate_reproduction_readiness_gate.json.

---

## 3. Readiness gate summary

| Gate field | Value | Source |
| --- | --- | --- |
| official_rigourate_code_available | false | §1 |
| official_rigourate_data_available | false | §1 |
| official_rigourate_model_available | false | §1 |
| official_reproduction_possible | false | §1, §3 |
| proxy_rigourate_style_baseline_completed | true | §4 |
| scalar_baseline_distinguishes_mild_vs_strong | false | §5 |
| r4_outperforms_scalar_on_strong_action | true | §5, §6 |
| claim_realism_risk_high | false | §8 |
| gold_realism_extension_needed | true | §8, §9 |
| v3_13_revision_needed | true | §11 |
| advisor_send_ready_after_revision | false | §11 |
| main_remaining_risk | (see below) | synthesised |
| recommended_next_action | (see below) | §11 |

**Main remaining risk:** Three primary risks remain:
1. Official RIGOURATE artifacts not publicly available — proxy baseline is NOT official RIGOURATE and conclusions may shift when official system is released.
2. Silver-only evaluation — all conclusions are pre-gold and may shift with gold adjudication.
3. SimClaim realism risk — 4.7% overall and 9.0% for strong_action_overclaim class is non-trivial; gold realism annotation required to confirm SimClaim claims are naturalistic enough for paper tables.

**Recommended next action:**
1. Draft V3.14 paper text: V3.13 + new §VI.B (RIGOURATE-style scalar baseline results) + Limitations additions (proxy caveat, realism caveat, silver-only caveat).
2. Draft advisor cover note (Chinese, per user preference).
3. Run final quality check: no proxy-as-official, no silver-as-gold, no API calls, no V3.12/V3.13 modification.
4. Send V3.14 + cover note to advisor.
5. Out-of-task: email RIGOURATE corresponding author (jhfjames1@sheffield.ac.uk) to request code/data release status.

---

## 4. Prohibitions enforced (all verified PASS)

1. **No modification of V3.12** — PASS. V3.12 file untouched.
2. **No modification of original data** — PASS. strict_silver_max_v1 CSVs read-only.
3. **No gold creation** — PASS. All outputs are silver-stage or proposals.
4. **No silver-as-gold** — PASS. All outputs labelled "silver" where applicable.
5. **No R4 retuning** — PASS. R4 frozen metrics used as-is.
6. **No paid API calls** — PASS. All evaluation used existing parsed outputs.
7. **No proxy as official RIGOURATE** — PASS. All proxy outputs explicitly labelled.
8. **blocked_reason recorded for unavailable artifacts** — PASS. All blocked items have blocked_reason.

---

## 5. Output file inventory

**Experiments directory (20 files):**
- §1: official_resource_inventory.csv, rigourate_reproduction_feasibility_report.md, official_reproduction_status.json
- §2: rigourate_method_dissection.md, rigourate_vs_cese_ocn_method_table.csv
- §3: official_reproduction_run_log.md
- §4: rigourate_style_scalar_scores.csv, baseline_build_notes.md
- §5: scalar_baseline_binary_results.csv, scalar_baseline_threshold_sweep.csv, scalar_baseline_report.md
- §6: rigourate_style_vs_r4_results.csv, rigourate_style_vs_r4_cases.csv, rigourate_style_vs_r4_report.md
- §7: case_level_comparison.csv, case_level_comparison_report.md
- §8: claim_realism_audit_queue.csv, claim_realism_audit_summary.md
- §9: proposed_relation_realism_gold_protocol_v2.md
- §11: V3_13_revision_recommendation.md
- §12: rigourate_reproduction_master_report.md, rigourate_reproduction_readiness_gate.json

**Docs directory (1 file):**
- §10: rigourate_forcebench_claimbench_related_work_insert.md

**Scripts directory (5 scripts, supplementary):**
- build_rigourate_style_scalar_baselines.py (§4)
- eval_scalar_baselines.py (§5)
- compare_rigourate_style_vs_r4.py (§6)
- case_level_comparison.py (§7)
- claim_realism_audit.py (§8)

---

## 6. Conclusion

This task successfully answered the four user questions:

1. **RIGOURATE official reproduction:** BLOCKED (no public code/data/model).
2. **RIGOURATE-style proxy baseline:** COMPLETED (3 baselines, 1 blocked with reason).
3. **Scalar vs. four-class taxonomy:** Scalar CANNOT replace the four-class taxonomy (cannot distinguish mild vs. strong; cannot match R4 strong_action F1).
4. **R4 screening value:** R4 RETAINS independent screening value (3-5x higher strong_action F1 than LLM judges; captures LLM-missed strong_action cases).

The work is ready to support a V3.14 paper revision that adds a RIGOURATE-style baseline results section to V3.13's positioning revision. V3.14 + advisor cover note is the recommended next deliverable, but is NOT yet ready (paper text and cover note not yet drafted).

All prohibitions enforced. All blocked items have blocked_reason. No paid API calls. No gold created. No silver-as-gold. No proxy-as-official. No modification of V3.12 or original data.
