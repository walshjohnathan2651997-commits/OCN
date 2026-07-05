# Flat Four-Class Attack Response — Reviewer Defense Document

**Date:** 2026-07-05
**Version:** V3.15 Hierarchical Taxonomy Revision
**Purpose:** Pre-emptive responses to likely reviewer attacks on the flat four-class framing. Each entry gives a short answer and the in-paper location where the defense is anchored.

**Status:** This document is a reviewer-defense aid. It does **not** modify the paper, does **not** claim gold validation, does **not** claim mild_scope is naturally stable, and does **not** claim R4 overall beats LLM. All paper claims remain controlled silver-stage evidence pending the §VII protocol-locked gold adjudication.

---

## Q1. Isn't `mild_scope_overclaim` arbitrary?

**Short answer.** Yes — and we explicitly say so. `mild_scope_overclaim` is not claimed to be a naturally discrete or naturally stable category. Under the V3.15 hierarchical taxonomy (§III.A, Table 0a), it is a **boundary-sensitive buffer subtype** between `supported` and `strong_action_overclaim`, used to isolate the high-risk action-overclaim boundary for screening. The primary scientific question is not "is mild_scope a natural class" but "does action/deployment overclaim behave differently from ordinary scope expansion" (Abstract; §III.A hierarchical interpretation paragraph). If gold adjudication shows the mild_vs_strong boundary is not reliably drawable, the paper falls back to a Level-1 three-class framing (supported / overclaim / contradiction) + binary strong_action screening per §VII.K and `hierarchical_gold_validation_plan.md`.

**In-paper defense location.** Abstract (standard wording: "We do not assume that mild_scope_overclaim is a naturally discrete category. Instead, it is used as a diagnostic buffer subtype..."); §I contribution 1; §III.A "Hierarchical interpretation" paragraph; §VIII.G "Why the Taxonomy Is Hierarchical Rather Than Flat"; §VII.K fallback rule 3.1.

---

## Q2. Are the four labels naturally discrete?

**Short answer.** No — and we do not claim they are. The four operational labels (supported, mild_scope_overclaim, strong_action_overclaim, contradiction_candidate) are **experimental label space**, not a claim of natural discreteness. Their interpretation is hierarchical: Level 1 (supported / overclaim / contradiction) is the primary relation separation; Level 2 (scope_expansion / strong_action under overclaim) is a risk-stratified subtype decomposition. The §V.D author sanity audit flags 25/40 (62.5%) of audited silver labels as questionable or unclear, with strong_action at 75% confusion — empirical evidence that the boundaries are NOT naturally sharp. The decision tree (Figure 2) is a labeling aid, not a validated annotation scheme; the pre-registered gold adjudication (§VII) is the mechanism that determines whether the boundaries are reliably drawable.

**In-paper defense location.** §III.A "Hierarchical interpretation" paragraph ("mild_scope_overclaim is a *boundary-sensitive buffer subtype*... It is **not** claimed to be a naturally stable discrete class"); §V.D author sanity audit (62.5% questionable/unclear rate reported transparently); §VII.G downgrade criterion 1 (mild_vs_strong κ < 0.40 → taxonomy revised); §VIII.G fallback logic.

---

## Q3. Why not just three classes (supported / overclaim / contradiction)?

**Short answer.** Three classes is the **fallback**, not the primary framing — but the primary framing does not force four classes as natural. The hierarchical taxonomy (§III.A) treats Level 1 (supported / overclaim / contradiction) as the primary separation and Level 2 (scope_expansion / strong_action) as a risk-stratified subtype under overclaim. The reason to retain the Level-2 distinction is risk semantics: `strong_action_overclaim` corresponds to action / deployment / safety / policy / generalization overclaims with downstream risk, while `mild_scope_overclaim` is an editorial writing-strength issue (§VIII.F). A single `overclaim` class would collapse these two qualitatively different risk profiles. R4's screening value (R4 strong-F1 = 0.3967 vs. baseline 0.2408 on silver 444; R4 strong-F1 = 0.3000 vs. LLM 0.0769 on matched 100) is precisely on the Level-2 strong_action subtype — collapsing to three classes would lose this signal. **However**, if gold adjudication shows Level-2 κ is insufficient (mild_vs_strong κ < 0.40), the paper falls back to three classes + binary strong_action screening per §VII.K fallback rule 3.1. The four-class framing is therefore not forced; it is the primary framing with a pre-registered three-class fallback.

**In-paper defense location.** §III.A Table 0a (Level 1 / Level 2 structure); §VIII.F "Why Fine-Grained Relation Typing Is Valuable"; §VIII.G "Why the Taxonomy Is Hierarchical Rather Than Flat"; §VII.K fallback rule 3.1; `hierarchical_gold_validation_plan.md` §3.1.

---

## Q4. Why not just a scalar overstatement score (RIGOURATE-style)?

**Short answer.** Because a scalar score cannot reliably distinguish mild_scope from strong_action — the exact boundary the paper targets. §VI.E reports controlled silver-stage evidence that `rule_scalar_score` achieves ROC-AUC = 0.5062 on mild_vs_strong (chance-level) and `llm_scalar_proxy` achieves ROC-AUC = 0.5874 (weak, below 0.70). The scalar compresses the action-vs-scope distinction, which is the high-risk boundary the taxonomy is designed to isolate. R4 retains targeted screening value on Level-2 strong_action (R4 strong-F1 = 0.3967 vs. rule_scalar best-F1 = 0.3844 on silver 444; R4 strong-F1 = 0.3000 vs. rule_scalar = 0.1364 on matched 100). Scalar scoring and relation-specific screening are **complementary**: scalar for broad severity ranking (ROC-AUC = 0.85 on supported_vs_overclaim), relation-specific for high-risk action-overclaim screening. The §VI.E RIGOURATE-style baseline is explicitly labelled as proxy (official RIGOURATE code/data/model not publicly available as of 2026-07-05); the paper does not claim to outperform the official RIGOURATE system.

**In-paper defense location.** §VI.E "Scalar Overstatement Baseline vs. Relation-Specific Screening"; §II.A RIGOURATE positioning paragraph; §VIII.F; §IX limitation 11 (proxy caveat); Table X (positioning against RIGOURATE / ForceBench / CLAIM-BENCH).

---

## Q5. Does the balanced four-way data distort reality?

**Short answer.** The balanced design is a deliberate construction for diagnostic pressure-testing, not a natural-prevalence estimate — and we state this explicitly. §V.A "Synthetic / counterfactual transparency statement" says: SimClaim is **not** a natural-prevalence corpus; the four-way balanced design (111 per class) is a deliberate construction for pressure-testing boundary recognition under matched evidence, **not** an estimate of the natural prevalence of these relations in real scientific writing. In natural scientific corpora, `contradiction_candidate` and `strong_action_overclaim` are expected to be substantially rarer than `supported` and `mild_scope_overclaim`. SimClaim is appropriate for boundary recognition pressure-testing and controlled comparison of relation-specific routing strategies; it is **not** appropriate for estimating real-world prevalence or training a calibrated prior. Downstream deployments that use R4 as a screening layer should re-calibrate the operating threshold against the target corpus's expected base rate. The §VII.J two-layer gold protocol includes a realism audit (Layer 2: `claim_realism_score_1_to_5`) to assess whether the generated claim variants are realistic enough for natural-claim transferability. The §VIII.D.C label-shift stress test quantifies robustness to simulated strong-label shift (break-even retention ~50%).

**In-paper defense location.** §V.A "Synthetic / counterfactual transparency statement"; §VII.J two-layer gold protocol (realism audit); §VIII.D.C label-shift stress test; §IX limitation 10 (SimClaim is counterfactual, not natural-prevalence); Abstract (controlled counterfactual diagnostic set framing preserved).

---

## Q6. What happens if gold cannot separate mild and strong?

**Short answer.** The paper has a pre-registered fallback — it does not force the four-class framing if gold does not support it. §VII.K and `hierarchical_gold_validation_plan.md` specify three fallback rules:

1. **If Level-1 κ is acceptable but Level-2 κ < 0.40:** the main paper is downgraded to a Level-1 three-class framing (supported / overclaim / contradiction) + binary strong_action screening. The four operational labels remain in experimental tables, but primary claims are reframed at Level 1.
2. **If strong_action retention ≥ 0.60:** the Level-2 high-risk strong_action subtype is retained as a validated screening target; R4's Level-2 screening claim is preserved.
3. **If strong_action retention < 0.50:** strong_action is reported only as an exploratory risk flag, not as a validated class; R4's screening claim is downgraded to exploratory status per §VII.G criterion 2.

These fallback rules are pre-registered before gold collection and cannot be relaxed after results are known. They map directly to the existing §VII.G downgrade criteria (criterion 1: mild_vs_strong κ < 0.40 → taxonomy revised; criterion 2: strong_action retention < 0.50 → claim downgraded; criterion 6: success path). The §VIII.D.C label-shift stress test pre-quantifies the robustness: at 70% retention the R4 advantage is robust; at 60% marginal-positive; at 50% positive-but-statistically-weaker (CI crosses zero); below 50% downgrade per §VII.G.

**In-paper defense location.** §VII.K "Hierarchical Gold Validation Plan (Level-1 + Level-2 + Fallback)"; `hierarchical_gold_validation_plan.md` §3 (three fallback rules); §VII.G pre-registered downgrade criteria; §VIII.D.C label-shift stress test (break-even retention); §VIII.G fallback logic paragraph.

---

## Summary: How V3.15 Defuses the "Forced Four-Class" Reviewer Risk

| Reviewer attack | V3.15 defense | Anchor |
|---|---|---|
| mild_scope arbitrary | Buffer subtype, not natural class | §III.A, §VIII.G |
| Four labels not discrete | Hierarchical, not flat; gold adjudication pending | §III.A Table 0a, §VII |
| Why not three classes | Three classes is the fallback; Level-2 retained for risk semantics | §VII.K, §VIII.F |
| Why not scalar score | Scalar cannot separate mild vs. strong (ROC-AUC ≤ 0.59) | §VI.E |
| Balanced data distorts reality | Deliberate diagnostic construction, not prevalence estimate | §V.A, §IX limitation 10 |
| Gold cannot separate mild/strong | Pre-registered 3-class + binary fallback | §VII.K, `hierarchical_gold_validation_plan.md` |

**Key reframe.** V3.15 does not claim the four classes are natural; it claims that strong_action is a high-risk overclaim subtype worth screening separately, with a pre-registered downgrade path if the Level-2 boundary is not reliably drawable. This shifts the paper's burden from "prove four natural classes" to "prove one high-risk subtype is worth screening" — a substantially weaker and more defensible claim.

**Prohibitions enforced.** This document does not claim mild_scope is naturally stable, does not delete the four operational labels, does not change experimental numbers, does not treat the three-class fallback as already executed, does not claim gold is complete, preserves the R4 macro-F1 < LLM fact, and preserves the non-gold checks caveat.
