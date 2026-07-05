# V3.16 No-Gold Revision Plan

**Task:** No-Gold Evidence Integration Plan for V3.16 - Section 7
**Date:** 2026-07-05
**Base version:** V3.15 (hierarchical taxonomy revision)
**Scope:** Plan only. **Do NOT modify the paper main text in this task.** All proposed edits below are *drafts* to be applied in a separate V3.16 revision pass after advisor sign-off.

**Hard constraints:**
- No gold annotation.
- No API calls.
- No model training.
- No original-data modification.
- No proxy-as-official-RIGOURATE.
- No simulation-as-natural-distribution.
- No silver-as-gold.

---

## 1. Abstract

**Edit:** Add a one-sentence positioning clause after the existing abstract paragraph:

> "We further validate the four-class decomposition against a RIGOURATE-style scalar overstatement proxy, a cue-based scalar baseline, and a low-prevalence screening simulation; none of these alternatives can replace relation-specific strong_action screening, supporting the hierarchical taxonomy."

**Must NOT change:** All existing experiment numbers (R4 strong-F1 = 0.3967, macro-F1 = 0.4238, etc.).

**Must down-tone:** The abstract's "high-risk action overclaim screening" claim must be qualified as "screening-oriented complement to LLM judges", not "standalone high-risk detector".

---

## 2. Introduction

**Add paragraph (after current intro):**

> "Three alternative formulations are conceivable: (i) a continuous scalar overstatement score in the spirit of RIGOURATE; (ii) a generic LLM judge applied directly to the four-class task; (iii) a low-prevalence screening simulation that mirrors natural deployment. We construct each alternative without gold annotation and show that none of them replaces the four-class relation-typing approach: scalar scores collapse mild_scope vs strong_action (ROC-AUC <= 0.59); LLM judges are 9x more conservative than R4 on strong_action (LLM strong-recall = 0.04 vs R4 strong-recall = 0.4562); and standalone R4 screening is impractical below 10% prevalence (FP/TP >= 25 at 5%). These results motivate the four-class decomposition and the two-stage deployment recommendation."

**Must NOT change:** The existing problem-statement and contribution bullets.

**Must down-tone:** Replace any "R4 detects high-risk overclaims" with "R4 contributes a screening-oriented strong_action signal complementary to LLM judges".

---

## 3. Related Work

**Add paragraphs** from `public_dataset_positioning_insert.md`:
- RIGOURATE paragraph (complementary; proxy baseline here).
- ForceBench paragraph (blocked; no public data; positioning only).
- SciFact / CLAIM-BENCH / VitaminC paragraphs (complementary public benchmarks).

**Must NOT change:** Existing related-work citations.

**Must down-tone:** All references to "official RIGOURATE reproduction" must be replaced with "RIGOURATE-style proxy baseline".

---

## 4. Data

**Add subsection: SimClaim as controlled counterfactual diagnostic set.**

Reuse the `public_dataset_positioning_insert.md` Section 6 paragraph verbatim, with the realism limitation:

> "SimClaim claims are generated counterfactual variants, not author-written claims. An automatic heuristic realism audit (Section §X) flagged 0.2% high-risk and 2.0% medium-risk claims; SimClaim is therefore suitable as a controlled diagnostic set for relation-type separability, NOT as a natural-prevalence corpus. The 25% strong_action prevalence in SimClaim is an intentional oversampling for diagnostic power, not a natural prevalence estimate."

**Must NOT change:** The 444 / 111 / 6-domain numbers.

**Must down-tone:** Remove any phrasing that implies SimClaim reflects natural claim distributions.

---

## 5. Results

**Add three new result subsections:**

### 5.1 RIGOURATE-style scalar baseline (proxy)
- Reuse `scalar_baseline_report.md` numbers verbatim.
- State: "rule_scalar_score cannot distinguish mild vs strong_action (ROC-AUC = 0.5054); llm_scalar_proxy is barely above chance (ROC-AUC = 0.5874). Scalar overstatement scores cannot replace hierarchical relation typing."

### 5.2 Scalar vs R4 vs LLM on strong_action
- Reuse `scalar_vs_r4_llm_report.md` numbers verbatim.
- State: "R4 strong-F1 = 0.3967 vs rule_scalar strong-F1 = 0.2996 vs LLM strong-F1 = 0.0769. R4 captures 8/24 (33.3%) of LLM-missed strong_action cases on the 100 matched subset. R4 retains independent value as a strong_action screening complement."

### 5.3 Low-prevalence screening simulation
- Reuse `low_prevalence_screening_report.md` numbers verbatim.
- State: "R4 recall is stable (~0.36) across 1-25% prevalence; FP/TP ratio is unacceptable below 10% (158 @1%, 11.7 @5%, 11.7 @10%). R4 must be deployed as a second-stage router in a two-stage pipeline below 10% prevalence. Accuracy is misleading at low prevalence and must not be the headline metric."

**Must NOT change:** Any existing V3.15 result table numbers.

**Must down-tone:** All low-prevalence results must be labelled as "simulation over silver labels with imposed prevalence, NOT natural-distribution results".

---

## 6. Discussion

**Add subsection: Why scalar overstatement score may be insufficient for high-risk action-overclaim screening.**

Reuse the `public_dataset_positioning_insert.md` Section 7 paragraph verbatim.

**Add subsection: Two-stage deployment recommendation.**

> "Given R4's stable recall but high FP/TP at low prevalence, we recommend a two-stage deployment: a high-precision LLM first stage (LLM precision ~1.0 on strong_action) filters obvious negatives, then R4 acts as a second-stage recall booster on LLM-rejected cases. This combines LLM's precision with R4's recall and recovers LLM-missed strong_action cases."

**Must NOT change:** Existing discussion of hierarchical taxonomy and fallback plan.

---

## 7. Limitations

**Add four explicit limitations:**

1. **Silver-only evaluation.** "All quantitative results in this paper are computed on silver labels (AI-preannotated, author-screened). Gold adjudication (50-pair two-layer relation+realism pilot, pre-registered, pending) may shift the mild_vs_strong boundary conclusion. If gold κ < 0.40 on mild_vs_strong, the pre-registered fallback to three-class + strong_action binary will be triggered, weakening the Level-2 decomposition."

2. **RIGOURATE proxy, not official reproduction.** "RIGOURATE's official code, data, and model are not publicly available as of 2026-07-05. We construct a RIGOURATE-style scalar overstatement proxy (rule-based + LLM-derived) and explicitly label it as a proxy, not as the official RIGOURATE system. If RIGOURATE's artifacts are released, the proxy comparison must be re-run with the official system."

3. **ForceBench blocked.** "ForceBench's public data is not available; the ForceBench feasibility check is blocked. The ForceBench comparison is positioning-only; no empirical comparison is reported."

4. **Simulation, not natural distribution.** "The low-prevalence screening simulation imposes prevalence levels by resampling silver-labelled data; the FP/TP and recall numbers must NOT be reported as natural-distribution results. The simulation informs R4's *operational positioning*, not its real-world performance."

5. **Realism risk.** "SimClaim claims are generated counterfactual variants. The heuristic realism audit flagged 2.0% medium-risk claims; the gold realism layer (Layer 2 of the gold protocol) is required to validate whether the heuristic risk translates to human-judged unrealistic claims."

**Must NOT change:** Existing limitations text.

---

## 8. What can be written vs. future work vs. must-down-tone

### 8.1 What CAN be written in V3.16 (no gold, no API)

- The four-class decomposition is *empirically supported* against scalar and LLM alternatives **on silver labels**.
- R4 retains independent value as a strong_action screening complement (captures LLM-missed cases).
- R4 is standalone-usable at prevalence >= 10% and two-stage-usable below.
- SimClaim is a controlled counterfactual diagnostic set, NOT a natural-prevalence corpus.
- The hierarchical taxonomy survives without gold, with the explicit caveat that Level-2 mild_vs_strong requires gold adjudication.

### 8.2 What can ONLY be written as future work

- Gold-validated mild_vs_strong separability numbers.
- Official RIGOURATE comparison (blocked on artifact release).
- ForceBench empirical comparison (blocked on data release).
- Natural-prevalence strong_action screening performance (blocked on natural corpus).
- Two-stage pipeline end-to-end evaluation (blocked on a held-out evaluation set).

### 8.3 What MUST be down-toned in V3.16

- Any "R4 detects high-risk overclaims" phrasing -> "R4 contributes a screening-oriented strong_action signal complementary to LLM judges".
- Any "R4 is a high-recall strong_action screen" -> "R4 recall is stable at ~0.36 but FP/TP is impractical below 10% prevalence; R4 must be deployed as a second-stage router".
- Any "SimClaim represents real claim distributions" -> "SimClaim is a controlled counterfactual diagnostic set".
- Any "official RIGOURATE reproduction" -> "RIGOURATE-style scalar proxy baseline".
- Any "low-prevalence simulation reflects real deployment" -> "low-prevalence simulation with imposed prevalence for operational positioning only".

---

## 9. Pre-registered fallback (unchanged from V3.15)

If the gold pilot (50-pair two-layer relation+realism) yields κ < 0.40 on mild_vs_strong, the paper MUST trigger the pre-registered fallback:
- Level-1 three-class (supported / overclaim / contradiction) + binary strong_action screen.
- Level-2 mild_scope vs strong_action is downgraded to "exploratory subtype, not validated".
- All four-class numbers are retained but the Level-2 decomposition is explicitly labelled as "diagnostic only, pending gold validation".

---

## 10. Prohibitions enforced

- No gold annotation.
- No human annotation.
- No API calls.
- No model training.
- No paper main-text modification (this is a PLAN; the actual revision is a separate pass).
- No original-data modification.
- No silver-as-gold.
- No proxy-as-official-RIGOURATE.
- No simulation-as-natural-distribution.
