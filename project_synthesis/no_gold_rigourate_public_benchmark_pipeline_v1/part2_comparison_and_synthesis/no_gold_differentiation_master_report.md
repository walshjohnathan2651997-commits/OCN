# No-Gold Differentiation Master Report

**Task:** No-Gold RIGOURATE + Public Benchmark Pipeline Part 2 - Section 5
**Date:** 2026-07-05
**Status:** Author-side synthesis. No gold created. No API calls. No paper modification.

---

## Executive summary

Under the no-gold constraint, the CESE-OCN main line **survives with revisions**. R4 retains a clear advantage on strong_action screening over scalar baselines (R4 strong_F1=0.3967 vs rule_scalar strong_F1=0.2996). RIGOURATE does not constitute fatal homogenization because its code/data/model are unavailable (blocked) and its scalar formulation cannot replace the hierarchical relation typing (Part 1 mild_vs_strong ROC-AUC < 0.60). ForceBench is also blocked (no public data). Claim realism risk is non-trivial but manageable (0% high-risk, 2.0% medium-risk) and consistent with SimClaim's controlled counterfactual design.

**The main line does NOT require dataset redesign.** The hierarchical taxonomy is supported without gold, with the explicit caveat that gold adjudication is required to confirm the mild_vs_strong boundary. The three-class + strong_action binary fallback remains pre-registered.

---

## Q1. Under the no-gold constraint, does the main line still hold?

**YES, with caveats.**

The main line rests on three empirical claims:
1. R4 outperforms scalar baselines on strong_action screening.
2. Scalar scores cannot distinguish mild_scope_overclaim from strong_action_overclaim.
3. The hierarchical taxonomy (Level 1 + Level 2) has incremental value over a scalar score.

All three claims are supported by no-gold evidence:
- R4 strong_F1=0.3967 (silver 444) vs rule_scalar strong_F1=0.2996 (silver 444): R4 wins by 0.0971 F1 points.
- Part 1 mild_vs_strong ROC-AUC: rule_scalar=0.5054 (chance), llm_scalar_proxy=0.5874 (weak). Both < 0.60.
- R4 captures 8/24 LLM-missed strong_action cases (33.3% capture rate) on 100 matched samples.

**Caveats:**
- All evaluation is on silver labels (AI-preannotated, author-screened, not gold-adjudicated).
- The 200-sample LLM subset is not random (matched by group_id and silver_label).
- Gold adjudication may shift the mild_vs_strong boundary conclusion.

**Conclusion:** The main line holds under no-gold, but gold adjudication is required to confirm the Level-2 mild_vs_strong boundary. If gold κ < 0.40 on mild_vs_strong, the pre-registered fallback to three-class + strong_action binary applies.

---

## Q2. Does RIGOURATE constitute fatal homogenization?

**NO.**

Three reasons:
1. **RIGOURATE official artifacts are unavailable.** As of 2026-07-05, no public code/data/model exists (Part 1 audit: blocked). We cannot reproduce RIGOURATE, and reviewers cannot ask us to reproduce it. A RIGOURATE-style scalar proxy baseline is the strongest comparison possible under the no-gold constraint.

2. **RIGOURATE's scalar formulation is different, not homogenizing.** RIGOURATE produces a continuous overstatement score [0,1]; we produce a hierarchical relation label (Level 1 + Level 2). The scalar compresses the action-vs-scope distinction; the hierarchy preserves it. Part 1 confirms scalar cannot replace hierarchy (mild_vs_strong ROC-AUC < 0.60).

3. **RIGOURATE's evidence source and claim source differ.** RIGOURATE uses full paper bodies and author-written claims; SimClaim uses real evidence spans and generated counterfactual claim variants. The data designs are fundamentally different.

**Conclusion:** RIGOURATE is the closest related work but does not homogenize CESE-OCN. The differentiation argument holds: scalar severity vs. hierarchical relation typing, natural claims vs. controlled counterfactual, broad screening vs. high-risk action-overcall isolation.

---

## Q3. Does the scalar baseline weaken R4?

**NO.**

The scalar baseline *strengthens* R4's positioning, not weakens it:
- rule_scalar_score is at chance level for strong_action (ROC-AUC=0.5036, Part 1). A scalar baseline that fails at the task R4 is designed for is evidence *for* R4, not against it.
- llm_scalar_proxy (LLM-label-derived) is also at chance level for strong_action (ROC-AUC=0.5154, Part 1). Even an LLM-derived scalar cannot replace R4's structured routing.
- R4 captures 8/24 LLM-missed strong_action cases (33.3% capture rate). R4 catches what scalar/LLM miss.

**Conclusion:** The scalar baseline confirms that scalar overstatement scoring and relation-specific screening are complementary, not competitive. R4's structured routing provides screening signal that scalar compression cannot replicate. This is the empirical motivation for CESE-OCN's positioning as a fine-grained complement to scalar overstatement scoring work.

---

## Q4. Can ForceBench provide side support?

**NO, currently blocked.**

ForceBench data is not publicly available (Section 2: blocked). The contrastive preference comparison between ForceBench and CESE-OCN remains at the conceptual level.

However, ForceBench's *existence* as a related benchmark provides indirect support:
- ForceBench validates the *evidence-force calibration* research direction, confirming that the evidence-claim force relationship is a recognized research problem.
- ForceBench's five force dimensions (relation, modality, scope, temporal validity, numeric specificity) overlap with our taxonomy's scope axis, suggesting convergent validity.
- ForceBench's contrastive preference formulation is different from our typing formulation, reinforcing our differentiation argument.

**Conclusion:** ForceBench provides conceptual side support but no empirical comparison. If ForceBench data becomes available, a direct comparison would strengthen the paper; currently, the paper must position ForceBench as a complementary benchmark with conceptual overlap.

---

## Q5. Is claim realism risk severe?

**NO, but it is non-trivial and must be disclosed.**

Section 3 realism audit results:
- **0% high-risk claims** — no single claim is obviously broken.
- **2.0% medium-risk claims** — a non-trivial fraction has medium realism risk.
- **strong_action forced rate = 0.0%** — strong_action claims sometimes use forced cues (expected by design).
- **contradiction mechanical rate = 0.9%** — contradiction claims sometimes use mechanical cues.
- **group template risk rate = 3.6%** — most groups have at least one medium-risk claim (expected by design).

**Why the risk is manageable:**
1. SimClaim is explicitly a *controlled counterfactual diagnostic set*, not a natural-prevalence corpus. Template-like structure is expected because the four variants share evidence and differ only in claim strength.
2. The forced cues in strong_action claims are *the signal*, not noise: strong_action claims are generated by adding action cues to the evidence.
3. A pre-registered realism audit is part of the gold protocol, pending human validation.

**Required paper disclosure:**
- SimClaim MUST be labeled as "controlled counterfactual diagnostic set, NOT natural-prevalence corpus" in the paper.
- A realism limitation section MUST state that SimClaim claims are generated variants, not author-written claims.
- The paper MUST NOT claim naturalistic generalization from SimClaim results.

**Conclusion:** Realism risk is non-trivial but manageable with proper disclosure. SimClaim remains suitable as a controlled diagnostic set. The paper must explicitly state the realism limitation.

---

## Q6. Is dataset redesign required?

**NO.**

SimClaim does not need to be redesigned. The current design (444 pairs, 111 groups, 6 domains, balanced 1:1:1:1, controlled counterfactual) is fit for purpose:
- It enables per-relation separability analysis (the diagnostic purpose).
- It oversamples strong_action (25% prevalence) for meaningful screening evaluation.
- The controlled counterfactual design is the *strength*, not the weakness — it enables diagnosis that natural-claim benchmarks cannot provide.

What IS required:
1. **Gold adjudication** of the 50-pair two-layer relation+realism pilot (pre-registered protocol v2).
2. **Realism disclosure** in the paper (limitation section).
3. **Realism audit** as part of the gold protocol (human validation of heuristic flags).

**Conclusion:** No dataset redesign. The data design is sound for the diagnostic purpose. Gold adjudication and realism disclosure are the required next steps.

---

## Q7. Should the hierarchical taxonomy be retained?

**YES.**

The hierarchical taxonomy (Level 1: supported/overclaim/contradiction; Level 2: scope_expansion/strong_action under overclaim) is supported by no-gold evidence:
- Part 1 confirms scalar cannot distinguish Level-2 subtypes (mild_vs_strong ROC-AUC < 0.60 for both rule and LLM-derived scalars).
- R4's strong_action route achieves strong_F1=0.3967, providing screening signal that scalar compression cannot replicate.
- The taxonomy isolates high-risk action overclaims as a separate Level-2 subtype, which is the paper's core differentiator.

**Caveat:** The Level-2 mild_vs_strong boundary requires gold validation. If gold κ < 0.40 on mild_vs_strong, the pre-registered fallback to three-class + strong_action binary applies (§VII.K of V3.15).

**Conclusion:** Retain the hierarchical taxonomy. The Level-2 boundary is conditionally supported pending gold adjudication, with a pre-registered fallback.

---

## Q8. Should three-class + strong_action binary be the fallback?

**YES, as a pre-registered fallback (already in V3.15 §VII.K).**

The three-class + strong_action binary fallback is:
- Level 1: supported / overclaim / contradiction (three classes)
- Level 2 (binary): strong_action_overclaim vs. non-strong (binary screen)

This fallback is triggered if gold κ < 0.40 on mild_vs_strong. The fallback:
- Preserves the strong_action screening capability (R4's core value).
- Collapses mild_scope_overclaim into overclaim (Level 1 only).
- Maintains the paper's high-risk action-overclaim isolation argument.

**Current status:** The fallback is pre-registered but NOT triggered. The four-class taxonomy is the primary formulation; the fallback is the safety net.

**Conclusion:** The three-class + strong_action binary fallback should remain pre-registered. It is the safety net for the Level-2 boundary, not the primary formulation.

---

## Q9. How should the next paper version be revised?

**V3.16 revision plan (no-gold, no-experiment):**

1. **Related Work section:** Insert the public dataset positioning paragraphs (Section 4 of this report) for RIGOURATE, ForceBench, SciFact, CLAIM-BENCH, VitaminC. Explicitly state that these datasets do not replace SimClaim and that SimClaim is a controlled counterfactual diagnostic set.

2. **Method section:** Retain the hierarchical taxonomy (Level 1 + Level 2). Add a note that the Level-2 boundary is conditionally supported pending gold adjudication, with a pre-registered fallback.

3. **Results section:** Add the scalar baseline comparison (Section 1 of this report) showing R4 outperforms scalar on strong_action screening. Add the LLM-missed strong_action capture rate (33.3%).

4. **Limitations section:** Add the realism limitation (Section 3 of this report). State that SimClaim is a controlled counterfactual diagnostic set, NOT a natural-prevalence corpus. State that gold adjudication is pending.

5. **Discussion section:** Strengthen the complementarity argument: scalar for broad severity, relation-specific (R4) for high-risk action-overclaim screening. Cite the scalar baseline results as empirical evidence.

6. **Gold protocol section:** Reaffirm the pre-registered 50-pair two-layer relation+realism gold pilot as the next required action.

7. **No new experiments, no new API calls, no gold creation, no data modification.** This is a no-gold, no-experiment revision.

**Conclusion:** V3.16 should be a no-gold, no-experiment revision that integrates the scalar baseline comparison, the realism audit, the public dataset positioning, and the strengthened complementarity argument. Gold adjudication remains the next required action.

---

## Summary table

| Question | Answer |
| --- | --- |
| Q1. Main line holds under no-gold? | YES, with caveats (gold pending) |
| Q2. RIGOURATE fatal homogenization? | NO |
| Q3. Scalar weakens R4? | NO (strengthens positioning) |
| Q4. ForceBench side support? | NO (blocked, conceptual only) |
| Q5. Realism risk severe? | NO (manageable with disclosure) |
| Q6. Dataset redesign required? | NO |
| Q7. Retain hierarchical taxonomy? | YES (with gold-pending caveat) |
| Q8. Three-class + binary fallback? | YES (pre-registered, not triggered) |
| Q9. Next paper version? | V3.16 no-gold revision |

---

## Prohibitions enforced

- No gold created.
- No paid API calls.
- No model training.
- No paper modification (this is a report, not a paper edit).
- No original data modification.
- No proxy-as-official.
- No silver-as-gold.
- No planned-as-completed.
- No simulation-as-natural-distribution.
