# Current Project State — Master Report

> **REALIGNMENT BANNER (2026-07-05):** This master report has been superseded by `D:\ocn\project_synthesis\mainline_realignment_v1\updated_project_mainline_summary.md`. The current mainline is the **V3.17 baseline** offline PDF-corpus evidence-sufficiency screening pipeline (PDF → BM25 → `best_sentence_top5_overlap` canonicalization → restored R4 → `G_conservative_precision` ranking → second-stage review queue). V3.15 hierarchical taxonomy is retained as paper-level interpretation only. V3.18 intelligent upgrade is an exploratory negative ablation (not selected). The V3.15-era content below is retained for traceability.

**Date:** 2026-07-05
**Version (historical):** V3.15 Hierarchical Taxonomy Revision
**Prepared by:** Project State Consolidation v1 (read-only audit)
**Superseded by (current):** `mainline_realignment_v1/updated_project_mainline_summary.md`

---

## 1. One-page executive summary

The CESE-OCN project has transitioned from a flat four-class taxonomy to a **hierarchical diagnostic taxonomy** (V3.15). Level 1 separates supported / overclaim / contradiction; Level 2 under overclaim separates scope_expansion (mild) from strong_action (high-risk). The four operational labels remain the experimental label space; only interpretation changes. All experimental numbers are preserved byte-identical from V3.14. R4 is positioned as a Level-2 high-risk strong_action screening router, NOT a flat 4-class best classifier and NOT an overall-beats-LLM claim (R4 macro_F1=0.3280 < LLM=0.5523). The mainline survives with mandatory revisions: mainline_survives=true, needs_dataset_redesign=false, needs_relation_realism_gold=true. The single most decisive next action is executing the §VII 50-pair two-layer gold pilot (relation + realism) to determine whether the Level-2 mild_vs_strong boundary is reliably drawable (κ ≥ 0.40) or whether the paper falls back to Level-1 three-class + binary strong_action screening per the pre-registered §VII.K fallback rules.

---

## 2. Current mainline

**CESE-OCN R4** as a relation-specific screening router under the hierarchical diagnostic taxonomy, targeting Level-2 high-risk strong_action overclaim screening as a complement to LLM judges. Anchored on SimClaim (controlled counterfactual diagnostic set, 444 silver pairs) and the pre-registered §VII gold adjudication protocol (DRAFT, annotation NOT begun).

---

## 3. What changed in recent tasks

- **V3.15 hierarchical taxonomy revision:** 18 targeted string replacements across 9 sections; added Table 0a, §VII.K, §VIII.G; reframed R4 as hierarchical router; added pre-registered fallback rules.
- **Overnight non-API compute pipeline v1:** 8 sub-tasks (A-H) all completed; confirmed dataset integrity, LLM conservatism, R4 FP root cause, scalar collapse, complementarity.
- **V3.16 integration summary:** mainline_survives=true; three routes identified (A=PRIMARY four-class + gold, B=FALLBACK strong_action focus, C=CONTINGENCY three-class downgrade).
- **RIGOURATE reproduction:** official blocked; proxy scalar baseline built; scalar cannot replace R4.
- **Claim realism audit:** 0% high-risk; safe as diagnostic set, NOT as naturalistic corpus.
- **Low-prevalence screening simulation:** R4 recall stable ~0.36; NOT viable standalone <10%; viable as first-stage filter.
- **Scalar vs relation deep test:** scalar ROC-AUC=0.51 on mild_vs_strong; score collapse confirmed.
- **Gold protocol v2:** two-layer (relation + realism) DRAFT; ready_for_blind_annotation=true.

---

## 4. Completed / partial / blocked / missing tasks

### Completed (all gates report completed=true)
- Overnight non-API compute pipeline v1 (8 sub-tasks A-H)
- V3.15 hierarchical taxonomy revision (18 replacements, 10 quality checks PASS)
- V3.16 integration summary + revision plan
- RIGOURATE reproduction + SimClaim baseline (proxy, official blocked)
- Claim realism audit
- Low-prevalence screening simulation
- Scalar vs relation screening deep test
- Gold pilot relation+realism protocol v2 (DRAFT, ready for annotation)
- V3.14 mainline locked + consistency audit
- V3.13 RIGOURATE-differentiated + realism-aware
- V3.12 three credibility checks
- V3.11 three core credibility experiments
- Mixed framework v2 frozen R4 baseline
- LLM judge baseline v1 (DeepSeek, 200 samples)
- GPT structured judge probe v1 (100 samples)

### Partial / blocked
- None. All recent tasks completed. RIGOURATE official reproduction is blocked (official artifacts unavailable) but the proxy baseline is completed and labeled as proxy.

### Missing
- None. All 17 scanned directories exist.

### Planned (NOT completed — must not be written as completed)
- §VII 50-pair two-layer gold pilot annotation (NOT begun)
- Gold adjudication and κ computation (NOT begun)
- Two-stage pipeline end-to-end evaluation (NOT done; only complementarity analyzed)
- Official RIGOURATE reproduction (blocked; proxy only)

---

## 5. Paper version status

| Version | Status | Notes |
|---|---|---|
| V3.15 hierarchical_taxonomy_revision | **CURRENT RECOMMENDED** | Hierarchical taxonomy; all quality checks PASS; 157953 bytes MD |
| V3.14 mainline_locked_consistency_audit | Predecessor (frozen) | Source for V3.15; experimental numbers byte-identical |
| V3.13_rigourate_differentiated_realism_aware | Historical | Superseded by V3.14 |
| V3.13_differentiated_against_rigourate_forcebench | Historical | First differentiation pass |
| V3.12_1 / V3.12 | Historical | Three credibility checks |
| V3.11 | Historical | Framework roadmap |
| V3.10 / V3.10_1 | Historical | Advisor ready silver stage |
| V3.9 / V3.9_audit | Historical | Pre-gold complete |
| V3.8 | Historical | Reference refreshed |
| V3.7 | Historical | Advisor handoff (was V3.7-era current) |
| V3.6 / V3.5 / V3.4 | Historical | Early versions |

**Note:** `_PROJECT_INDEX/current_paper_paths.md` references V3.7 as current — OUTDATED. Current is V3.15.

---

## 6. Experiment evidence status

All experiments are **silver-stage evidence** pending §VII gold adjudication. Key results (all preserved byte-identical in V3.15):

- **R4 strong_F1:** 0.3967 (silver 444), 0.3000 (matched 100)
- **R4 macro_F1:** 0.4238 (silver 444), 0.3280 (matched 100)
- **LLM strong_F1:** 0.0769 (matched 100); strong_recall=0.04 (1/25)
- **LLM macro_F1:** 0.5523 (GPT-5.5, matched 100), 0.5270 (DeepSeek, 200)
- **Baseline strong_F1:** 0.2408; absolute gap +0.2231
- **R4 strong_recall:** 0.4562 (silver 444), 0.36 (matched 100)
- **Screening utility:** FP/TP=2.89, review burden=35%, R4 captures 8 LLM-missed strong
- **LLM conservatism:** pred_strong_rate=0.04 (LLM) vs 0.36 (R4), 9x gap
- **Scalar ROC-AUC (mild_vs_strong):** 0.5062 (rule), 0.5874 (llm proxy)
- **Dataset integrity:** TF-IDF gap=-0.0066 (low leakage)
- **Claim realism:** 0% high-risk; safe_as_diagnostic=true, safe_as_naturalistic=false

**Non-gold checks caveat preserved:** Non-gold robustness checks do NOT replace gold adjudication.

---

## 7. Code/script status

- **Total scripts:** 47 in `D:\ocn\scripts\`
- **Safe to run:** V3.15/V3.16/overnight builders + audit/view scripts (no API, no gold, no original data modification)
- **Not safe to run (frozen):** Historical experiment runners (run_cese_ocn_lite_v3, run_llm_judge_baseline_v1, run_gpt_structured_judge_probe_v1, etc.) — results frozen
- **Calls API:** 2 scripts (run_llm_judge_baseline_v1, run_gpt_structured_judge_probe_v1) — require user authorization + API key
- **Trains model:** 2 scripts (run_mixed_framework_router_optimization_v2, run_mixed_framework_new_algorithm_sweep_v1) — frozen
- **Outdated registry:** `_PROJECT_INDEX/script_registry_mainline.csv` references V3.7 as current; should be updated to V3.15 (documentation task, not refactoring)

No dangerous or duplicate scripts found.

---

## 8. Dataset/gold status

### SimClaim dataset
- 444 silver claim-evidence pairs, 111 groups, 6 domains, balanced 1:1:1:1
- Controlled counterfactual diagnostic set (NOT natural-prevalence, NOT naturalistic)
- TF-IDF separability gap = -0.0066 (LOW leakage risk)
- Template risk high (76/111 groups) but design attribute, not defect
- Claim realism: 0% high-risk; 52.3% contradiction_mechanical
- All labels silver (AI-preannotated); §V.D audit flagged 62.5% questionable/unclear

### Gold status
- **§VII gold adjudication protocol:** PLANNED and FROZEN, NOT executed
- **gold_pilot_protocol_freeze_v1:** 50-sample preparation pack, ready
- **gold_pilot_relation_realism_protocol_v2:** two-layer (relation + realism) DRAFT, ready_for_blind_annotation=true
- **Annotation:** NOT begun
- **Downgrade criteria:** pre-registered (§VII.G) + hierarchical fallback (§VII.K)

---

## 9. Biggest risks

### Risk 1: Level-2 mild_vs_strong boundary not reliably drawable
- **Likelihood:** Moderate (§V.D audit: 75% confusion on strong_action)
- **Impact:** High — if gold κ < 0.40, paper falls back to Level-1 three-class + binary strong_action screening (§VII.K rule 3.1)
- **Mitigation:** Pre-registered fallback rules; hierarchical taxonomy converts "forced four-class" attack into graceful-degradation path

### Risk 2: Gold adjudication may downgrade strong_action
- **Likelihood:** Low-moderate (strong_action has clear risk semantics: deployment/safety/policy)
- **Impact:** High — if strong_action retention < 0.50, R4 screening claim downgrades to exploratory (§VII.K rule 3.3)
- **Mitigation:** Pre-registered thresholds; §VIII.D.C label-shift stress test pre-quantifies robustness (break-even ~50%)

### Risk 3: RIGOURATE proxy may not match official system
- **Likelihood:** Unknown (official artifacts unavailable)
- **Impact:** Moderate — scalar baseline conclusions may shift when official RIGOURATE becomes available
- **Mitigation:** Explicit proxy caveat in §VI.E and §IX limitation 11; paper does not claim to outperform official RIGOURATE

### Secondary risks
- R4 high false positive rate (fp_rate=0.7429) — cost of higher recall; two-stage pipeline motivated but not evaluated
- SimClaim counterfactual design limits natural-claim transferability — §VII.J Layer 2 realism audit pending
- _PROJECT_INDEX registry outdated (references V3.7) — documentation gap, not a technical risk

---

## 10. Next 5 concrete actions

### Action 1: Execute §VII 50-pair two-layer gold pilot
- Use `gold_pilot_protocol_freeze_v1` + `gold_pilot_relation_realism_protocol_v2`
- Blind annotation A and B (50 pairs each) → adjudicate → compute Level-1 κ, Level-2 κ, strong_action retention
- Apply §VII.K fallback rules
- **Priority:** CRITICAL — determines whether hierarchical taxonomy is validated or downgraded

### Action 2: Insert gold results into paper
- Once gold pilot completes, insert results into Tables G1–G3
- Do NOT restructure the paper; only fill in the pre-registered table slots
- Update §VII readiness gate based on gold outcomes

### Action 3: Update _PROJECT_INDEX registry
- Update `script_registry_mainline.csv` and `current_paper_paths.md` to reference V3.15 as current
- Documentation task; no code changes needed

### Action 4: Evaluate two-stage pipeline end-to-end (post-gold)
- Currently only complementarity is analyzed (50/100 complementary cases)
- After gold validation, evaluate R4 first-stage + LLM second-stage end-to-end
- Report FP/TP, review burden, and net recall improvement

### Action 5: Prepare V3.16 main paper revision (post-gold)
- Based on gold outcomes, either retain V3.15 hierarchical taxonomy (Route A) or fall back to Level-1 three-class + binary screening (Route C)
- V3.16 revision plan already drafted in `project_synthesis/v3_16_integration_summary_and_revision_plan/`
- Do NOT begin V3.16 revision until gold pilot completes
