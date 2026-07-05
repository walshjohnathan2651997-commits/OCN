# Allowed vs. Forbidden Claims (Current, Post-Realignment v1)

> **REALIGNMENT BANNER (2026-07-05):** This list has been superseded by `D:\ocn\project_synthesis\mainline_realignment_v1\updated_allowed_forbidden_claims.md`. The current mainline is the V3.17 baseline offline PDF-corpus evidence-sufficiency screening framework. New allowed claims: A1 (PDF retrieval feasible), A2 (raw chunks degrade R4), A3 (canonicalization restores strong_action screening), A4 (overlap robust), A5 (R4 second-stage), A6 (V3.17 selected), A7 (SimClaim diagnostic), A8 (R4 macro_F1 < LLM), A9 (V3.18 negative ablation). New forbidden claims: F6 (learned improves main method), F7 (raw BM25 solves screening), F8 (model fully understands). The V3.15-era content below is retained for traceability; where it conflicts with the realignment, the realignment prevails.

**Date:** 2026-07-05
**Basis (current):** V3.17 baseline frozen metrics + V3.18 intelligent upgrade negative result + canonicalized R4 evidence-sufficiency pipeline
**Basis (historical, retained):** V3.15 hierarchical taxonomy revision + V3.16 integration gate + overnight pipeline + all recent task gates. Silver-stage evidence only; gold adjudication pending.

---

## Allowed claims

These claims are supported by the current evidence and may be made in the paper:

### 1. Controlled counterfactual diagnostic set

SimClaim is a **controlled counterfactual diagnostic set** that uses real evidence spans and generated claim variants to pressure-test boundary recognition under matched evidence. It is NOT a natural-prevalence corpus and NOT a naturalistic corpus. The balanced four-way design (111 per class) is a deliberate construction for diagnostic pressure-testing.

**Evidence:** §V.A synthetic/counterfactual transparency statement; claim_realism_audit (0% high-risk, safe_as_diagnostic=true); overnight pipeline Task A (TF-IDF gap=-0.0066, low leakage).

### 2. Hierarchical diagnostic taxonomy

The paper operationalizes a **hierarchical diagnostic taxonomy**: Level 1 (supported / overclaim / contradiction); Level 2 (scope_expansion / strong_action under overclaim). The four operational labels remain the experimental label space; interpretation is hierarchical. `mild_scope_overclaim` is a boundary-sensitive buffer subtype, NOT a naturally stable discrete class.

**Evidence:** V3.15 §III.A Table 0a; §VIII.G; readiness gate (hierarchical_taxonomy_inserted=true, flat_four_class_deemphasized=true).

### 3. R4 screening-oriented complement

R4 is a **relation-specific screening router under the hierarchical taxonomy** that targets Level-2 high-risk strong_action screening as a complement to LLM judges. R4 is NOT a flat 4-class best classifier and NOT a competitive replacement for LLM judges.

**Evidence:** §IV.A; §VI.A–§VI.B; R4 strong_F1=0.3967 (silver 444), 0.3000 (matched 100); R4 captures 8 LLM-missed strong cases.

### 4. LLM under-detection under tested prompts

Under tested prompts, strong LLM judges (GPT-5.5, DeepSeek-V3) **consistently under-detect strong_action** (strong-F1=0.0769, recall 0.04 = 1/25 across both models and both prompt designs). This is a controlled silver-stage diagnostic finding, NOT a fundamental limit of LLMs.

**Evidence:** §VI.B; overnight pipeline Task E (LLM pred_strong_rate=0.04 vs R4=0.36, 9x gap); LLM conservatism confirmed.

### 5. Non-gold robustness checks

Non-gold credibility checks (label-shift stress, screening utility, evidence necessity, boundary collapse) provide **diagnostic evidence** that R4's screening value is robust to simulated label shift down to ~60% retention and that R4 uses evidence (not gaming via claim-only cues). These checks do NOT replace gold adjudication.

**Evidence:** §VIII.D; v3_11_three_core_credibility_experiments; overnight pipeline Task D (boundary collapse).

### 6. Relation + realism gold pending

The §VII pre-registered gold adjudication protocol (Layer 1 relation + Layer 2 realism) is **planned and frozen**, with ready_for_blind_annotation=true. Annotation has NOT begun. The protocol includes pre-registered downgrade criteria (§VII.G) and hierarchical fallback rules (§VII.K).

**Evidence:** §VII; gold_pilot_protocol_freeze_v1; gold_pilot_relation_realism_protocol_v2 (ready_for_blind_annotation=true, does_not_modify_v1=true).

### 7. Scalar baseline / proxy result (completed)

The RIGOURATE-style scalar baseline is a **proxy** (rule-based / LLM-label-derived), NOT official RIGOURATE. Official RIGOURATE code/data/model are NOT publicly available (blocked). The proxy scalar score cannot distinguish mild vs strong (ROC-AUC=0.5062, chance-level) and cannot replace R4 on strong_action screening.

**Evidence:** §VI.E; rigourate_reproduction_readiness_gate (official_reproduction_possible=false); v3_15_scalar_vs_relation_deep_test (scalar_can_separate_mild_strong=false, scalar_can_replace_r4=false).

---

## Forbidden claims

These claims are NOT supported by the current evidence and MUST NOT be made in the paper:

### 1. Natural prevalence corpus

**Forbidden:** Claiming SimClaim is a natural-prevalence corpus or estimates real-world prevalence of evidence-sufficiency relations.

**Why forbidden:** The balanced four-way design is deliberate; in natural corpora, contradiction and strong_action are substantially rarer. Low-prevalence simulation uses heuristic non-strong composition, NOT real distribution.

### 2. Gold validated

**Forbidden:** Claiming the four-class taxonomy is gold-validated, gold-confirmed, or that gold adjudication is complete.

**Why forbidden:** Gold annotation has NOT begun. All labels are silver (AI-preannotated). The §VII protocol is planned and frozen, not executed. Only the conditional success path (§VII.G criterion 6) describes future gold-validated numbers.

### 3. R4 beats LLM overall

**Forbidden:** Claiming R4 outperforms LLM judges overall, R4 has higher macro_F1 than LLM, or R4 is a competitive replacement for LLM judges.

**Why forbidden:** R4 macro_F1=0.3280 < LLM=0.5523 (matched 100). R4 is a screening complement with targeted value on Level-2 strong_action, NOT an overall-beats-LLM classifier.

### 4. Official RIGOURATE reproduced

**Forbidden:** Claiming to have reproduced the official RIGOURATE system, or that the scalar baseline represents RIGOURATE's actual performance.

**Why forbidden:** Official RIGOURATE code/data/model are NOT publicly available (blocked). The scalar baseline is explicitly a PROXY (rule-based / LLM-label-derived).

### 5. First scientific overstatement benchmark

**Forbidden:** Claiming CESE-OCN is the first scientific overstatement detection benchmark, or that it opens a new field.

**Why forbidden:** Scientific overstatement detection is an existing track (RIGOURATE [30], ForceBench [35], CLAIM-BENCH [28]). CESE-OCN contributes a hierarchical relation-typed decomposition, not a new field.

### 6. mild_scope as naturally stable category

**Forbidden:** Claiming mild_scope_overclaim is a naturally stable discrete class, naturally discrete, or naturally drawable.

**Why forbidden:** The §V.D audit flags 75% confusion on strong_action boundary. V3.15 explicitly states mild_scope is a boundary-sensitive buffer subtype, NOT a naturally stable discrete class. Gold adjudication will determine whether the Level-2 boundary is reliably drawable.

### 7. Simulation as real-world distribution

**Forbidden:** Claiming the low-prevalence screening simulation represents real-world strong_action prevalence, or that the simulation is a natural-distribution study.

**Why forbidden:** The simulation uses heuristic non-strong composition and resampling; it is NOT a real natural-distribution study. It provides diagnostic evidence of R4's recall stability, not prevalence estimates.

---

## Borderline claims (require careful wording)

These claims are conditionally allowed with explicit caveats:

- **"R4 improves strong_action recall"** — allowed ONLY with "on controlled silver-stage evaluation" and "under tested prompts" caveats.
- **"Two-stage pipeline motivated"** — allowed ONLY as "motivated by complementarity analysis" NOT as "evaluated end-to-end".
- **"Gold will validate"** — allowed ONLY in conditional success-path language ("if gold supports...", "the success path is..."), NOT as "gold validates".
- **"Hierarchical taxonomy"** — allowed, but must include the fallback design (§VII.K) and must NOT claim mild_scope is naturally stable.
