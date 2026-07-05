# Updated Allowed vs. Forbidden Claims (Post-Realignment v1)

**Date:** 2026-07-05
**Basis:** V3.17 baseline frozen metrics + V3.18 intelligent upgrade negative result + canonicalized R4 evidence-sufficiency pipeline
**Supersedes:** `project_synthesis/current_project_state_consolidation_clean_v1/allowed_vs_forbidden_claims_current.md` (which anchored on V3.15 hierarchical taxonomy)

---

## Allowed claims

These claims are supported by the current evidence and may be made in project records, reports, and (with appropriate caveats) paper text:

### A1. PDF retrieval is feasible

BM25 top-k retrieval over a scientific PDF corpus produces candidate evidence chunks usable by downstream screening.

**Evidence:** `experiments/simclaim_pdf_corpus_retrieval_v1/`; `experiments/r4_evidence_canonicalization_v1/` (raw_bm25_top1 produces strong_F1=0.1806, non-trivial signal).

### A2. Raw retrieved chunks degrade R4 screening

Raw BM25 top1 chunks feed R4 a strong_F1 of only 0.1806, well below the oracle-span strong_F1 of 0.4257. The format shift (metadata + length + multi-sentence concatenation) is the dominant cause, confirmed by ablation (oracle_lengthened drops strong_F1 to 0.0938).

**Evidence:** `experiments/r4_evidence_canonicalization_v1/evidence_canonicalization_gate.json` (`canonicalization_improves_over_raw=true`, `format_shift_confirmed=true`, `main_bottleneck=format_shift`).

### A3. Evidence canonicalization restores strong_action screening

`best_sentence_top5_overlap` canonicalization restores strong_F1 to 0.4503, a +0.2697 gain over raw BM25 top1, and is only -0.0246 below oracle span. Evidence canonicalization is the critical bridge between BM25 retrieval and R4 screening.

**Evidence:** `experiments/r4_evidence_canonicalization_v1/` (`best_canonical_format=best_sentence_from_top5`, `best_canonical_strong_f1=0.4503`, `canonicalization_gain_vs_raw=0.2697`, `oracle_to_best_gap=-0.0246`).

### A4. Simple overlap-based canonicalization is robust

The V3.18 intelligent upgrade attempted to replace the handcrafted overlap selector with sklearn learned models (LogisticRegression / RandomForest / HistGradientBoosting, group-aware split). The learned selector did NOT improve over the simple overlap selector (learned strong_F1 = 0.4444 vs baseline 0.4503). Simple overlap-based canonicalization is therefore the robust choice under the current feature space.

**Evidence:** `experiments/v3_18_intelligent_upgrade_v1/v3_18_intelligent_upgrade_gate.json` (`selector_upgrade_passed=false`, `best_overall_method=V3.17_baseline`).

### A5. R4 is a second-stage screening router, not standalone

R4 is positioned as an offline, auditable, second-stage strong_action screening router. Standalone viability is false (FP/TP @ 1% = 66.82); second-stage viability is true (FP/TP @ 5% = 11.24 / 12.84 with recall ≥ 0.6). R4 is NOT a standalone detector and NOT a flat 4-class best classifier.

**Evidence:** `experiments/canonicalized_review_queue_v1/canonicalized_review_queue_gate.json` (`standalone_viable=false`, `second_stage_viable=true`, `recommended_mode=second-stage`); `experiments/canonicalized_risk_ranking_v1/risk_ranking_gate.json` (`standalone_usable=false`, `low_prevalence_second_stage_usable=true`).

### A6. V3.17 baseline is the selected main method

The selected main method is V3.17 baseline: BM25 top-k → `best_sentence_top5_overlap` canonicalization → restored R4 (10 seeds, per-seed thresholds, majority vote) → `G_conservative_precision` ranking → second-stage review queue. Frozen metrics: strong_F1=0.4503, P@20=0.45, R@100=0.3303, FP/TP@5%=11.24.

**Evidence:** `experiments/v3_18_intelligent_upgrade_v1/v3_17_frozen_baseline_metrics.json`; `experiments/canonicalized_risk_ranking_v1/risk_ranking_gate.json` (`best_variant=G_conservative_precision`).

### A7. SimClaim is a controlled silver diagnostic test set

SimClaim is a controlled counterfactual diagnostic set (444 pairs, 111 groups, 6 domains, balanced 1:1:1:1) using real evidence spans and generated claim variants. It is NOT a natural-prevalence corpus and NOT a naturalistic corpus. Silver labels; gold adjudication pending.

**Evidence:** `data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/`; overnight pipeline Task A (TF-IDF gap=-0.0066, low leakage); `safe_as_diagnostic_set=true`, `safe_as_naturalistic=false`.

### A8. R4 macro_F1 lower than LLM, but R4 captures Level-2 strong_action signal

R4 macro_F1 (0.3280) is lower than GPT-5.5 (0.5523) and DeepSeek-V3 (0.5270) on matched 100 samples. The paper does NOT claim R4 overall beats LLM. R4 provides targeted Level-2 strong_action screening signal (R4 captures 8 LLM-missed strong cases; R4 strong_recall=0.7064 vs LLM strong_recall=0.04 on tested prompts). This is a controlled silver-stage finding, not a fundamental limit of LLMs.

**Evidence:** `experiments/llm_judge_baseline_v1/`; `experiments/gpt_structured_judge_probe_v1/`; overnight pipeline Task E.

### A9. V3.18 intelligent upgrade is an exploratory negative ablation

V3.18 attempted learned evidence selector + learned risk ranker as an upgrade over V3.17 baseline. Both modules failed to improve (selector strong_F1 -0.006; ranker P@20 -0.10). V3.18 is retained as an exploratory negative result for §VIII limitations / §IX future work and is NOT the selected main method.

**Evidence:** `experiments/v3_18_intelligent_upgrade_v1/v3_18_intelligent_upgrade_gate.json` (`supports_v3_18_intelligent_upgrade=false`, `best_overall_method=V3.17_baseline`).

---

## Forbidden claims

These claims are NOT supported by the current evidence and MUST NOT be made in project records, reports, or paper text:

### F1. R4 beats LLM overall

**Forbidden:** Claiming R4 outperforms LLM judges overall, R4 has higher macro_F1 than LLM, or R4 is a competitive replacement for LLM judges.

**Why forbidden:** R4 macro_F1=0.3280 < LLM=0.5523 (matched 100). R4 is a second-stage screening complement with targeted value on Level-2 strong_action, not an overall-beats-LLM classifier.

### F2. Gold validated

**Forbidden:** Claiming the four-class taxonomy is gold-validated, gold-confirmed, or that gold adjudication is complete.

**Why forbidden:** Gold annotation has NOT begun. All labels are silver. The §VII protocol is planned and frozen, not executed.

### F3. Natural prevalence corpus

**Forbidden:** Claiming SimClaim is a natural-prevalence corpus or estimates real-world prevalence of evidence-sufficiency relations.

**Why forbidden:** The balanced four-way design is deliberate for diagnostic pressure-testing, not prevalence estimation.

### F4. Full automatic review

**Forbidden:** Claiming the system performs full automatic review end-to-end without human review.

**Why forbidden:** R4 is explicitly a second-stage screening router; standalone viable=false. The pipeline produces a review queue for second-stage human review, not final adjudications.

### F5. Standalone detector

**Forbidden:** Claiming R4 is a standalone detector usable in isolation without an upstream filter or downstream human review.

**Why forbidden:** Standalone viability is false (FP/TP @ 1% = 66.82). R4 requires second-stage positioning.

### F6. Learned selector/ranker improves main method

**Forbidden:** Claiming the learned evidence selector or learned risk ranker improves the V3.17 main method, or that V3.18 intelligent upgrade is selected as the main method.

**Why forbidden:** V3.18 selector strong_F1=0.4444 < baseline 0.4503; V3.18 ranker P@20=0.35 < baseline 0.45. `supports_v3_18_intelligent_upgrade=false`; `best_overall_method=V3.17_baseline`.

### F7. BM25 raw chunks alone solve screening

**Forbidden:** Claiming raw BM25 retrieved chunks alone are sufficient for R4 screening without evidence canonicalization.

**Why forbidden:** Raw BM25 top1 strong_F1=0.1806 vs canonicalized 0.4503. Canonicalization is the critical bridge; raw chunks degrade screening badly.

### F8. The model fully understands scientific language

**Forbidden:** Claiming R4 or any model in the pipeline fully understands scientific language, scientific reasoning, or scientific causality.

**Why forbidden:** R4 is a feature-based relation-specific screening router using NLI + action-gap features. It does not perform language understanding in the LLM sense; it performs pattern-based screening.

### F9. Official RIGOURATE reproduced

**Forbidden:** Claiming to have reproduced the official RIGOURATE system, or that the scalar baseline represents RIGOURATE's actual performance.

**Why forbidden:** Official RIGOURATE code/data/model are NOT publicly available. The scalar baseline is explicitly a proxy.

### F10. First scientific overstatement benchmark

**Forbidden:** Claiming CESE-OCN is the first scientific overstatement detection benchmark or that it opens a new field.

**Why forbidden:** Scientific overstatement detection is an existing track (RIGOURATE, ForceBench, CLAIM-BENCH). CESE-OCN contributes an offline PDF-corpus evidence-sufficiency screening framework with canonicalization as the bridge.

---

## Borderline claims (require careful wording)

- **"R4 improves strong_action recall"** — allowed ONLY with "on controlled silver-stage evaluation" and "under tested prompts" caveats.
- **"Two-stage pipeline motivated"** — allowed ONLY as "motivated by complementarity analysis" NOT as "evaluated end-to-end".
- **"Gold will validate"** — allowed ONLY in conditional success-path language ("if gold supports...", "the success path is..."), NOT as "gold validates".
- **"Learned upgrade attempted"** — allowed as "exploratory negative ablation", NOT as "selected" or "improves".
- **"Hierarchical taxonomy"** — allowed as paper-level interpretation, NOT as the empirical mainline (the empirical mainline is the offline PDF-corpus screening pipeline).
