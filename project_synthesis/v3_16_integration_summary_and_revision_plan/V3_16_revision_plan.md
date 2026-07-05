# V3.16 Revision Plan

**Date:** 2026-07-05
**Status:** Plan only. NO paper modification. NO submission draft. NO experiments.
**Base version:** V3.12 With Three Credibility Checks (silver-stage draft).
**Synthesis inputs:** T1-T5 gates + V3.12 readiness gate + RIGOURATE related-work insert.

> This document specifies *what to change* in V3.16; it does NOT change the paper.
> All wording directions are advisory; final phrasing is the author's responsibility.

---

## 1. Abstract

**Current issue:** V3.12 abstract mentions three non-gold credibility checks but does not mention the RIGOURATE-style proxy baseline, the low-prevalence simulation, or the realism audit. The screening positioning implies standalone deployment.

**Needed change:**
- Add one sentence on RIGOURATE-style scalar proxy baseline (labelled as proxy).
- Add one sentence on low-prevalence screening simulation (frame R4 as first-stage filter).
- Add one sentence on realism audit + gold protocol v2.
- Replace any "screener" wording with "first-stage filter in a two-stage pipeline."

**Source evidence:** T1 gate (proxy); T2 gate (low-prev); T3 gate (realism); T4 gate (gold v2).

**Exact wording direction:**
> "We further construct a RIGOURATE-style scalar overstatement proxy baseline (official RIGOURATE artifacts unavailable as of 2026-07-05), and show that scalar severity cannot recover the mild-vs-strong_action boundary (ROC-AUC <= 0.59). A low-prevalence screening simulation (1%-25%) shows R4 retains stable recall (~0.36) but is not viable as a standalone screener below 10% prevalence; we propose a two-stage pipeline (R4 -> LLM/human) as future work. An automatic realism audit (4.7% overall risk, 9.0% for strong_action) motivates a two-layer gold protocol (relation + realism), pre-registered and pending annotation."

---

## 2. Introduction

**Current issue:** V3.12 introduction positions CESE-OCN as a four-class relation-typing framework with screening orientation, but does not explicitly contrast with scalar severity (RIGOURATE) or address the low-prevalence deployment gap.

**Needed change:**
- Add a paragraph explicitly contrasting relation typing (CESE-OCN) vs. scalar severity (RIGOURATE), citing T5 score-collapse findings.
- Reframe screening orientation as "first-stage high-recall filter" rather than "standalone screener."
- Mention that SimClaim is a controlled counterfactual diagnostic set, not a naturalistic corpus.

**Source evidence:** T5 gate (score collapse); T2 gate (low-prevalence); T3 gate (realism); RIGOURATE related-work insert (Section 4).

**Exact wording direction:**
> "Where RIGOURATE-style approaches produce a continuous scalar overstatement score, we decompose the same underlying phenomenon into a four-class relation taxonomy that isolates strong_action_overclaim as a separate high-risk boundary class. We show empirically (Section X) that scalar compression cannot recover this boundary (rule ROC-AUC = 0.5062; LLM-derived scalar ROC-AUC = 0.5874; mild/strong score-overlap ratio = 1.02). R4, our mixed relation-routing framework, is positioned as a first-stage high-recall filter in a two-stage pipeline, not a standalone deployment-ready screener."

---

## 3. Related Work

**Current issue:** V3.12 related work may not include RIGOURATE, ForceBench, CLAIM-BENCH (these were drafted in T1 docs but not yet inserted into the paper).

**Needed change:**
- Insert the four prepared paragraphs from `docs/rigourate_reproduction_and_simclaim_baseline_v1/rigourate_forcebench_claimbench_related_work_insert.md` (RIGOURATE, ForceBench, CLAIM-BENCH, CESE-OCN differentiation).
- Insert the comparison table (Section 5 of the insert).
- Cross-check against existing Related Work to avoid duplication.

**Source evidence:** T1 docs (paste-ready paragraphs); T5 results (scalar insufficiency).

**Exact wording direction:** Use the prepared paragraphs verbatim, with the placeholder citations [RIGOURATE: James et al., 2026], [ForceBench: ref 35], [CLAIM-BENCH: ref 28]. Add the reproducibility note about official RIGOURATE artifacts being unavailable.

---

## 4. Data

**Current issue:** V3.12 Data section describes SimClaim but does not include the realism audit results or the controlled-counterfactual design caveats.

**Needed change:**
- Add a paragraph on SimClaim as a controlled counterfactual diagnostic set (Section 6 of the related-work insert).
- Report realism audit headline numbers (0% high-risk; 4.7% overall; 9.0% strong_action).
- State explicitly that SimClaim is NOT a naturalistic corpus.
- Note that realism gold validation is part of the v2 gold protocol (pending).

**Source evidence:** T3 gate (realism audit); T4 gate (gold v2 Layer 2); RIGOURATE insert Section 6.

**Exact wording direction:**
> "SimClaim is a controlled counterfactual diagnostic set: 444 claim-evidence pairs across 111 evidence groups and 6 domains, with four generated claim variants per evidence group instantiating the four evidence-sufficiency relations. An automatic author-side realism audit (Section X) finds 4.7% overall realism risk and 9.0% for strong_action_overclaim — below the pre-registered 25% class-level threshold, but non-trivial. SimClaim is therefore safe as a diagnostic set but is NOT a naturalistic corpus. Human realism validation is included in the v2 gold protocol (Section VII) and is pending annotation."

---

## 5. Method

**Current issue:** V3.12 Method section describes R4 routing but does not explicitly state the screening-oriented trade-off (R4 macro-F1 < LLM macro-F1) or the two-stage pipeline framing.

**Needed change:**
- Add a paragraph stating the screening trade-off: R4 trades macro-F1 for strong_action positive-F1.
- Add a paragraph on the proposed two-stage pipeline (R4 -> LLM/human) as future deployment configuration.
- State frozen R4 thresholds (t_contra=0.48, t_strong=0.535, t_svm=0.51) explicitly.

**Source evidence:** V3.12 gate (numbers preserved); T2 gate (two-stage pipeline); T1 gate (R4 strong_F1 advantage).

**Exact wording direction:**
> "R4's routing is designed as a screening-oriented complement to LLM/NLI judges: it trades overall macro-F1 (R4 = 0.3280 vs LLM = 0.5523 on matched-100) for targeted strong_action positive-F1 (R4 = 0.3967 vs LLM = 0.0769). The frozen thresholds (t_contra=0.48, t_strong=0.535, t_svm=0.51) are not prevalence-aware; we therefore propose a two-stage deployment pipeline (R4 as first-stage high-recall filter, followed by LLM or human second-stage confirmation) as future work. This pipeline is not evaluated in the present paper."

---

## 6. Results

**Current issue:** V3.12 Results report R4/LLM numbers on SimClaim but do not include the RIGOURATE-style scalar baseline, the low-prevalence simulation, or the score-collapse analysis.

**Needed change:**
- Add a new subsection §VI.B (RIGOURATE-style scalar baseline results): 3 baselines, 4 binary tasks, 5-method comparison, case analysis.
- Add a new subsection §VI.C (Low-prevalence screening simulation): 7 prevalence levels, FP/TP, NNR, review burden, LLM high-accuracy/low-recall failure mode.
- Add a new subsection §VI.D (Scalar score-collapse analysis): 4 indicators, mild/strong overlap, contradiction vs strong mixing, supported false-positive rate.
- Preserve all V3.12 numbers byte-identical (0.3967, 0.0769, 0.3280, 0.5523, 0.2408, 0.2231).

**Source evidence:** T1 (baseline results); T2 (low-prev sim); T5 (score collapse).

**Exact wording direction:** Use the experimental numbers from T1/T2/T5 gates verbatim. Label scalar as "rule_scalar_score / llm_scalar_score", NOT "RIGOURATE". Mark all new results as "silver-stage, pre-gold."

---

## 7. Discussion

**Current issue:** V3.12 Discussion §VIII.A discusses R4 vs LLM macro-F1 trade-off and §VIII.D adds three credibility checks, but does not discuss the scalar-baseline complementarity or the low-prevalence deployment implication.

**Needed change:**
- Add a paragraph on scalar vs relation-specific screening complementarity (Section 7 of the related-work insert).
- Add a paragraph on the prevalence-dependence of R4's screening value (T2 findings).
- Add a paragraph on realism risk and the need for Layer-2 gold (T3 + T4).

**Source evidence:** T5 (scalar complementarity); T2 (prevalence dependence); T3+T4 (realism gold).

**Exact wording direction:**
> "The scalar-baseline comparison (Section VI.B) shows that continuous overstatement scores and four-class relation typing are complementary: scalar severity provides broad-coverage ranking, while relation typing isolates the action-vs-scope boundary that scalar compression loses. R4's screening value is prevalence-dependent: stable recall (~0.36) across 1%-25%, but precision drops sharply at low prevalence. Realism risk is non-trivial (9.0% for strong_action) and requires Layer-2 human gold validation before any naturalistic claim."

---

## 8. Limitations

**Current issue:** V3.12 Limitations has 8 items, including the non-gold caveat. It does not include the RIGOURATE proxy caveat, the low-prevalence simulation caveat, or the realism-audit-as-heuristic caveat.

**Needed change:** Add at least four new limitations items:
- §IX.9: RIGOURATE-style scalar baseline is a rule-based / LLM-label-derived proxy. Official RIGOURATE artifacts unavailable. Conclusions may shift if official system is released.
- §IX.10: Low-prevalence simulation uses heuristic 80/15/5 non-strong composition and 100 matched base samples. Absolute FP/TP values may shift with real natural-prevalence corpus.
- §IX.11: Two-stage pipeline (R4 -> LLM/human) is proposed but not evaluated.
- §IX.12: Realism audit is automatic/heuristic; not human gold. SimClaim is a controlled counterfactual diagnostic set, not a naturalistic corpus.

**Source evidence:** T1 (proxy caveat); T2 (simulation caveat + two-stage caveat); T3 (realism heuristic caveat).

**Exact wording direction:**
> "9. The RIGOURATE-style scalar baseline is a rule-based / LLM-label-derived proxy. Official RIGOURATE code, data, and model are unavailable as of 2026-07-05. Conclusions about scalar insufficiency may shift if the official system provides a stronger continuous score. 10. The low-prevalence simulation uses a heuristic 80/15/5 non-strong composition and 100 matched base samples; absolute FP/TP values may shift with a real natural-prevalence corpus. 11. The two-stage pipeline (R4 -> LLM/human) is proposed as future work and is not evaluated in this paper. 12. The realism audit is automatic and heuristic; it is not human gold. SimClaim is a controlled counterfactual diagnostic set, not a naturalistic corpus; naturalistic claims require a separate natural-prevalence corpus study."

---

## 9. Gold Protocol

**Current issue:** V3.12 §VII Pre-Registered Gold Validation Protocol is the v1 Layer-1-only protocol (FROZEN). The v2 two-layer protocol (relation + realism) has been drafted but is not yet reflected in the paper.

**Needed change:**
- DO NOT modify §VII (it is FROZEN as v1).
- Add a new §VII.G or §VII-bis: "Gold Protocol v2 (Relation + Realism) — DRAFT."
- Describe the two-layer independence (Layer 1 relation, Layer 2 realism).
- List the 9 realism_issue types and 5-point realism scale.
- List the 6 pre-registered decision rules (kappa<0.40, retention<0.40, realism_score<=2 rate>25%, etc.).
- State clearly that v2 is DRAFT, annotation NOT begun, and v1 remains FROZEN.

**Source evidence:** T4 gate (v2 protocol details, pre-registered rules, template details).

**Exact wording direction:**
> "Gold Protocol v2 extends v1 with an independent Layer 2 (realism) annotation: claim_realism_score_1_to_5, claim_realism_issue (9 types), realism_rationale_one_sentence, claim_usable_for_paper_example, needs_realism_adjudication. Layer 1 (relation) is carried over from v1 (FROZEN). Six pre-registered decision rules govern taxonomy revision, paper-claim downgrade, and realism downgrade. v2 is DRAFT; annotation has not begun. v1 remains FROZEN and is not modified. The 50-pair v2 pilot will determine whether the four-class taxonomy survives human annotation and whether SimClaim's realism is acceptable for paper use."

---

## Cross-cutting prohibitions for V3.16 drafting

- Do NOT write proxy as official RIGOURATE.
- Do NOT write silver as gold.
- Do NOT write planned two-stage pipeline as evaluated.
- Do NOT write simulation as natural-prevalence corpus study.
- Do NOT write realism audit as human gold.
- Do NOT modify V3.12 source files (create V3.16 as a new file).
- Do NOT change any experimental number from V3.12 (0.3967, 0.0769, 0.3280, 0.5523, 0.2408, 0.2231).
- Do NOT delete the "R4 macro-F1 < LLM macro-F1" fact.
- Do NOT delete the "gold not yet performed" fact.
