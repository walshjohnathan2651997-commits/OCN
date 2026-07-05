# Next Route Decision

**Date:** 2026-07-05
**Status:** Decision support document. NO commitment. NO paper modification. NO experiments.

Three routes are evaluated. Each is scored on: applicable conditions, evidence needed, risks, pros, cons, recommended priority.

---

## Route A — Continue four-class + relation+realism gold

**Description:** Keep the four-class taxonomy (supported / mild_scope_overclaim / strong_action_overclaim / contradiction_candidate) as the central CESE-OCN claim. Run the v2 two-layer gold pilot (50 pairs). Apply pre-registered decision rules. Proceed to full 444-pair gold if pilot passes.

**Applicable conditions:**
- Gold pilot mild_vs_strong kappa >= 0.40.
- Strong_action retention >= 0.40.
- Class-level realism_score<=2 rate <= 25%.
- Paper-level realism_score<=2 rate <= 25%.
- Layer-2 Pearson r >= 0.40.

**Evidence needed:**
- v2 50-pair gold pilot results (Layer 1 + Layer 2 agreement).
- Re-evaluation of R4 / LLM / scalar on gold-validated subset.
- Re-run of low-prevalence simulation with gold labels.

**Risks:**
- If kappa < 0.40, taxonomy revision triggers; four-class claim collapses; paper must be substantially rewritten.
- If realism_score<=2 rate > 25% for strong_action, paper-claim downgrade triggers; strong_action screening positioning weakened.
- Time and annotator cost (estimated 4h per annotator + adjudication).
- v2 protocol is DRAFT; annotators untrained on Layer 2; agreement untested.

**Pros:**
- Maintains the strongest paper claim (four-class + strong_action isolation).
- T5 already shows scalar cannot replace four-class; gold validation locks in this finding.
- T4 v2 protocol is drafted, silver-leakage-free, ready for annotation.
- Most aligned with V3.12's existing structure; minimal rewriting.

**Cons:**
- Highest annotation cost.
- Highest risk of pre-registered downgrade triggers.
- Longest timeline to advisor-ready draft.

**Recommended priority: 1 (PRIMARY).** The evidence from T1-T5 supports the four-class claim; the pre-registered rules provide a graceful degradation path; the v2 protocol is ready. This is the highest-expected-value route.

---

## Route B — Keep four-class diagnostic set, but main paper focus on strong_action screening

**Description:** Retain the four-class SimClaim design (for diagnostic separability) but reframe the paper's central claim around strong_action screening specifically. Mild vs strong becomes a *secondary* diagnostic axis, not the primary paper claim. Gold pilot still runs Layer 1 + Layer 2 but the paper's headline metric is strong_action screening (F1, FP/TP, NNR).

**Applicable conditions:**
- Gold pilot shows strong_action retention >= 0.40 (strong label reliable).
- Mild vs strong kappa is borderline (0.30-0.40) — taxonomy revision triggers but strong_action is salvageable as a binary high-risk class.
- Author wants a tighter, more defensible paper claim.

**Evidence needed:**
- v2 50-pair gold pilot results.
- Re-evaluation of R4 / LLM / scalar on strong-vs-non-strong binary task.
- Low-prevalence simulation on gold-validated strong_action labels.

**Risks:**
- Loses the fine-grained four-class typing claim — weakens differentiation from RIGOURATE / ForceBench.
- May complicate §VII gold protocol (Layer 1 becomes secondary).
- Risks reviewer pushback ("why four classes if you only use strong_action?").

**Pros:**
- Stronger paper claim (binary strong_action screening is more defensible than four-class typing).
- Lower annotation cost (gold pilot can focus on strong_action reliability).
- Better aligned with T2 low-prevalence findings (screening is the practical value).
- Faster path to advisor-ready draft.

**Cons:**
- Wastes the four-class diagnostic design (T5 score-collapse evidence becomes secondary).
- Reduces paper novelty vs. RIGOURATE (which already covers severity screening).
- May require SimClaim redesign to add more strong_action variants.

**Recommended priority: 2 (FALLBACK).** Adopt if Route A's gold pilot returns borderline kappa (0.30-0.40) or strong_action retention >= 0.40 but mild-strong is unstable.

---

## Route C — Downgrade to three-class (supported / overclaim / contradiction), strong_action as overclaim subtype

**Description:** Collapse mild_scope_overclaim and strong_action_overclaim into a single "overclaim" class. strong_action becomes a *subtype tag* within overclaim, not a separate class. Reduces the taxonomy to three classes plus a subtype annotation.

**Applicable conditions:**
- Gold pilot returns mild_vs_strong kappa < 0.40 (taxonomy revision triggers per T4 pre-registered rule).
- Strong_action retention < 0.40 (paper-claim downgrade triggers).
- Author accepts loss of strong_action as a first-class label.

**Evidence needed:**
- v2 gold pilot results showing kappa < 0.40.
- Re-tagging of SimClaim with three-class labels + strong_action subtype.
- Re-evaluation of R4 / LLM / scalar on three-class task.

**Risks:**
- Loses the central paper claim (strong_action isolation).
- T5 evidence (scalar cannot separate mild/strong) becomes a *limitation*, not a *contribution*.
- Substantial paper rewrite required.
- Reviewer pushback ("why did you build a four-class set if you downgraded to three?").
- May invalidate the RIGOURATE differentiation argument (T1, T5).

**Pros:**
- Lower annotation cost (three-class is easier).
- Cleaner agreement statistics (fewer boundary classes).
- More defensible if kappa is genuinely too low.

**Cons:**
- Contradicts T5 empirical evidence (four-class captures distinctions scalar loses).
- Wastes the entire V3.12 / SimClaim design effort.
- Loses the screening-oriented positioning (no separate strong_action class to screen for).
- Reduces paper to a less novel three-class overclaim detector.

**Recommended priority: 3 (CONTINGENCY).** Adopt ONLY if Route A's gold pilot triggers both taxonomy-revision AND paper-claim-downgrade rules. Do NOT pre-emptively choose this route.

---

## Summary recommendation

| Route | Priority | Trigger condition | Expected timeline | Risk |
|---|---|---|---|---|
| A (four-class + gold) | PRIMARY | default | longest | highest (kappa, realism) |
| B (strong_action focus) | FALLBACK | borderline kappa, strong retention OK | medium | medium |
| C (three-class) | CONTINGENCY | kappa<0.40 AND retention<0.40 | shortest (rewrite) | highest (loses main claim) |

**Default action:** Proceed with Route A. Run v2 50-pair gold pilot. Apply pre-registered decision rules. Reassess at pilot completion.
