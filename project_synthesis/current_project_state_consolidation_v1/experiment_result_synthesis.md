# Experiment Result Synthesis

**Date:** 2026-07-05
**Experiments synthesized:** 9

## R4 strong_action results

- **R4 strong_F1 = 0.3967** (silver 444); **0.3000** (matched 100)
- **R4 strong_recall = 0.4562** (silver 444); **0.36** (matched 100, catches 9/25 silver=strong)
- **R4 macro_F1 = 0.4238** (silver 444); **0.3280** (matched 100)
- **Baseline strong_F1 = 0.2408**; absolute gap = **+0.2231**
- **R4 captures 8 LLM-missed strong_action cases** (out of 100 matched)
- **Screening utility:** FP/TP = 2.89, review burden = 35%

**Verdict:** R4 retains targeted Level-2 high-risk strong_action screening value. R4 is a screening complement, NOT an overall-beats-LLM classifier (R4 macro_F1 0.3280 < LLM 0.5523).

## LLM (GPT-5.5 / DeepSeek-V3) results

- **GPT-5.5 macro_F1 = 0.5523** (matched 100); **strong_F1 = 0.0769**, **strong_recall = 0.04** (1/25)
- **DeepSeek-V3 macro_F1 = 0.5270** (200); **strong_F1 = 0.0769**, **strong_recall = 0.04** (1/25)
- **GPT structured vs standard:** no improvement (both strong_F1=0.0769, strong_recall=0.04)
- **LLM pred_strong_rate = 0.04** vs **R4 = 0.36** (9x conservatism gap)

**Verdict:** LLM conservatism CONFIRMED. LLMs under-detect strong_action under tested prompts. This is a controlled silver-stage finding, not a fundamental LLM limit. Gold adjudication is the protocol-locked mechanism that determines whether this pattern is treated as established.

## Non-gold credibility checks (§VIII.D)

- **Label-shift stress:** R4 advantage robust at 70% retention; marginal-positive at 60%; positive-but-statistically-weaker at 50% (CI crosses zero); below 50% downgrade per §VII.G.
- **Screening utility (§VIII.D.B):** FP/TP=2.89, review burden=35%, R4 captures 8 LLM-missed strong cases.
- **Evidence necessity (§VIII.D.D):** R4 uses evidence (not gaming via claim-only cues); claim-only TF-IDF separability gap = -0.0066 (LOW leakage).
- **Boundary collapse (§VIII.D.E):** If taxonomy collapses to 3-class (supported/overclaim/contradiction), strong_action isolation is lost.

**Caveat preserved:** Non-gold checks do NOT replace gold adjudication (§VIII.D opening caveat).

## Low-prevalence screening simulation

- **R4 recall stable ~0.36** across 1%-25% prevalence (1000 resamples per level)
- **FP/TP ratio:** 3.8 (at 25%) → 121 (at 1%)
- **R4 NOT viable standalone <10% prevalence; viable as first-stage filter**
- Two-stage pipeline (R4 first-stage + LLM second-stage) motivated but NOT evaluated end-to-end

**Caveat:** Simulation uses heuristic non-strong composition; NOT a real natural-distribution study.

## Claim realism audit

- **0% high-risk claims** (automatic rules); 52.3% contradiction_mechanical; 76.6% group template risk
- **safe_as_diagnostic_set = true; safe_as_naturalistic = false**
- SimClaim is a controlled counterfactual diagnostic set, NOT a naturalistic corpus
- Gold realism check (§VII.J Layer 2) still pending

## Scalar / RIGOURATE-style baseline

- **rule_scalar_score ROC-AUC = 0.5062** (mild_vs_strong, chance-level)
- **llm_scalar_proxy ROC-AUC = 0.5874** (weak, below 0.70)
- **nli_scalar_score:** all "blocked" (444)
- **Official RIGOURATE code/data/model NOT available** (blocked)
- Scalar cannot distinguish mild vs strong; R4 retains independent value on strong_action screening

**Caveat:** Scalar baseline is PROXY (rule-based / LLM-label-derived), NOT official RIGOURATE.

## Boundary collapse fallback

- If taxonomy collapses to 3-class (supported/overclaim/contradiction), strong_action isolation is lost
- **4-class R4 macro_F1 = 0.328**; **3-class fallback macro_F1 = higher** but loses strong_action screening
- **Three-class fallback is CONTINGENCY (Route C), not primary** — primary is Route A (four-class + relation+realism gold)

## LLM conservatism + error direction

- **LLM pred_strong_rate = 0.04** (GPT standard, GPT structured, DeepSeek all = 0.04)
- **R4 pred_strong_rate = 0.36** (9x higher)
- **LLM error direction splits:**
  - GPT standard/structured: over-route to contradiction (14/25 = 56%)
  - DeepSeek: compress to mild/supported (19/25 = 76%)
- **Complementarity:** 50/100 matched samples show R4-LLM complementary cases (LLM-only-correct + R4-only-correct)

## R4 false positive root cause

- **26 FP out of 35 strong predictions** (fp_rate = 0.7429)
- FP concentrated in **mild→strong boundary** (same confusion as scalar collapse)
- R4 over-routes mild to strong; this is the cost of higher recall
- **Implication:** R4 is a high-recall first-stage filter, not a precision classifier; two-stage pipeline (R4 + LLM) motivated

## Overall evidence status

All experiments are **silver-stage evidence** pending the §VII protocol-locked gold adjudication. No gold has been collected. The mainline survives with mandatory revisions (mainline_survives=true, needs_dataset_redesign=false, needs_relation_realism_gold=true). The hierarchical taxonomy (V3.15) reduces the "forced four-class" reviewer risk by converting it to a pre-registered graceful-degradation path (§VII.K fallback rules).
