# V3.16 Mainline Impact Summary

**Date:** 2026-07-05
**Status:** Synthesis only. NO experiments, NO API calls, NO gold, NO paper modification, NO original data modification.
**Scope:** Five-task integration judgment based on T1-T5 gate files + V3.12 readiness gate.

---

## Q1. Is the current mainline still valid?

**Verdict: YES — the mainline survives, but with mandatory revisions.**

The mainline — *CESE-OCN as a four-class relation-typing framework with R4 as a screening-oriented complement to LLM judges, targeting high-risk strong_action_overclaim* — is supported by all five tasks:

- T1 (RIGOURATE proxy): scalar cannot replace R4; R4 retains strong_F1 advantage.
- T2 (low-prevalence sim): R4 recall stable ~0.36 across prevalences; captures LLM-missed strong.
- T3 (realism audit): realism risk is non-trivial but below 25% threshold; SimClaim usable as diagnostic set.
- T4 (gold v2): two-layer protocol drafted; path to gold defined.
- T5 (scalar deep test): scalar cannot separate mild/strong; score collapse confirmed; R4 retains advantage.

**Mandatory revisions:** (a) qualify R4 as first-stage filter in two-stage pipeline (not standalone below 10% prevalence); (b) add realism caveat to Limitations; (c) clearly distinguish silver-stage from gold-validated claims; (d) label scalar baseline as PROXY, not official RIGOURATE.

---

## Q2. Should the paper still position strong_action as a rare high-risk screening target?

**Verdict: YES — but with explicit two-stage deployment framing.**

- T2 simulation confirms R4 has *stable recall* (~0.36) regardless of prevalence, which is the screening-oriented property the paper claims.
- T2 also confirms R4 is NOT viable as a *standalone* screener below 10% prevalence (FP/TP=25-121, NNR=27-159).
- The screening positioning must therefore be reframed: R4 is a *first-stage high-recall filter* in a two-stage pipeline (R4 -> LLM/human second-stage). The two-stage pipeline is PROPOSED but NOT evaluated in this paper.

**Implication:** keep the screening positioning, but downgrade from "deployment-ready screener" to "first-stage filter candidate; deployment requires two-stage evaluation, which is future work."

---

## Q3. Does RIGOURATE constitute fatal overlap / homogenisation?

**Verdict: NO.**

Three reasons:

1. **Output representation differs.** RIGOURATE produces a continuous scalar overstatement score in [0,1]; CESE-OCN produces a four-class relation label. These are not interchangeable (T5 confirms scalar cannot replace the four-class decomposition).
2. **Empirical complementarity.** T5 shows scalar score collapse (mild/strong overlap=1.02) and ROC-AUC near chance for mild/strong boundary. R4 retains F1=0.30 vs scalar F1=0.14 on matched-100.
3. **Reproducibility blocker.** Official RIGOURATE code/data/model are unavailable as of 2026-07-05; the proxy baseline is explicitly labelled, and the paper must state this clearly.

**Implication:** RIGOURATE is a *complementary related work*, not a fatal overlap. The paper should position scalar severity (RIGOURATE) and relation typing (CESE-OCN) as addressing different facets of evidential proportionality.

---

## Q4. Does the scalar baseline weaken R4?

**Verdict: NO.** The scalar baseline *strengthens* the case for R4 by providing a controlled comparison.

- T5: R4 strong_F1=0.30 vs scalar F1=0.14 (matched-100); R4 recall=0.36 vs scalar 0.12.
- T5: R4 captures 8 LLM-missed strong_action; scalar captures only 3.
- T1: R4 strong_F1=0.3967 vs scalar best-F1=0.3844 (444 silver); R4 captures 8/24 LLM-missed strong.
- T5: score collapse (4 indicators) shows scalar compression loses the action-vs-scope distinction that R4's routing preserves.

**Implication:** the scalar baseline is empirical support for the four-class decomposition, not a threat to R4.

---

## Q5. Does the low-prevalence simulation support deployment-style screening?

**Verdict: PARTIAL — supports first-stage filter role; does NOT support standalone deployment.**

- R4 NOT viable standalone below 10% prevalence (FP/TP=25-121).
- R4 marginal at 10% (FP/TP=12), viable at 25% (FP/TP=3.8) — matches balanced SimClaim prevalence.
- LLM judges exhibit a high-accuracy/low-recall failure mode (99% accuracy but 4.3% recall at 1% prevalence), making accuracy a misleading deployment metric.
- Two-stage pipeline (R4 -> LLM/human) is PROPOSED but NOT evaluated.

**Implication:** the paper must (a) NOT claim R4 is a deployment-ready standalone screener; (b) explicitly state that balanced SimClaim macro-F1 cannot be extrapolated to deployment; (c) propose the two-stage pipeline as future work; (d) report prevalence-aware metrics (FP/TP, NNR, review burden) alongside F1.

---

## Q6. Is the claim realism risk severe?

**Verdict: NO — non-trivial but below pre-registered thresholds.**

- T3: 0% high-risk claims; 4.7% overall realism risk; 9.0% for strong_action.
- All below the 25% pre-registered class-level threshold.
- Dominant risks are *design attributes* (templating 92.8%, mechanical-contradiction 52.3%, narrow-boundary 33.3%) rather than quality defects (extreme 7.0%, forced 0.9%, unnatural 0.2%).
- SimClaim is safe as a *controlled diagnostic set*, NOT as a *naturalistic corpus*.

**Implication:** SimClaim retains diagnostic value; the paper must state "controlled counterfactual diagnostic set, not naturalistic corpus" in Data and Limitations.

---

## Q7. Is relation+realism gold mandatory?

**Verdict: YES.**

- T3 realism audit is heuristic/automatic; cannot validate realism without human gold.
- T4 v2 protocol is drafted but NOT annotated.
- T1 recommends gold realism extension (Layer 2).
- V3.12 gold protocol (Layer 1 only) does not cover realism.
- Realism risk is concentrated in strong_action (9.0%), which is the high-risk class the paper claims to screen for.

**Implication:** the v2 two-layer gold pilot must be run before any external claim of "validated strong_action screening." Until gold is complete, all results are silver-stage directional support.

---

## Q8. Does the dataset need redesign?

**Verdict: NO.** SimClaim retains its diagnostic value.

- T3: realism risk below 25% threshold; safe as diagnostic set.
- T5: score collapse confirms the four-class design captures distinctions scalar loses.
- T2: low-prevalence simulation works on the existing 100 matched samples.
- T1: RIGOURATE proxy results align with V3.12 R4 results.

**Implication:** do NOT redesign SimClaim. Instead, (a) add realism gold validation; (b) state design attributes (templating, mechanical contradiction) as deliberate diagnostic design, not defects; (c) exclude extreme/templated cases from paper illustrative examples.

---

## Q9. Is downgrade to three-class fallback necessary?

**Verdict: NO — not at this stage.** Reserve as contingency.

- T5: scalar cannot separate mild/strong; this is evidence FOR the four-class decomposition, not against.
- T4 v2 pre-registered rule: "mild_vs_strong kappa < 0.40 -> taxonomy revision required." This rule has not fired; annotation has not begun.
- Three-class fallback (supported / overclaim / contradiction) would lose the high-risk strong_action class, which is the paper's central screening target.

**Implication:** keep four-class. If gold pilot returns mild_vs_strong kappa < 0.40 OR strong_action retention < 0.40 (T4 pre-registered rules), trigger taxonomy revision. Until then, three-class fallback is a documented contingency, not an active path.

---

## Summary table

| Question | Verdict | Revision required |
|---|---|---|
| Q1 Mainline valid? | YES | Mandatory qualifications (silver/gold, two-stage, proxy) |
| Q2 Strong_action screening positioning? | YES (first-stage filter, not standalone) | Reframe deployment claim |
| Q3 RIGOURATE fatal overlap? | NO | Position as complementary |
| Q4 Scalar weakens R4? | NO | Scalar strengthens four-class case |
| Q5 Low-prev supports deployment? | PARTIAL | Two-stage pipeline as future work |
| Q6 Realism risk severe? | NO (below 25%) | Realism gold needed; naturalistic caveat |
| Q7 Relation+realism gold mandatory? | YES | Run v2 pilot before external claims |
| Q8 Dataset redesign needed? | NO | Add realism gold; document design attributes |
| Q9 Three-class fallback? | NO (contingency only) | Reserve; trigger on kappa<0.40 |
