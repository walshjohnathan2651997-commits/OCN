# Current Mainline (V3.17) — Detailed Specification

**Date:** 2026-07-06
**Authority:** This file is the detailed companion to `CURRENT_MAINLINE.md`. If any other document conflicts with this file on the current mainline, this file wins.

---

## 1. Problem framing

This project studies **retrieval-to-screening format shift** in offline simulation claim evidence-sufficiency review.

Scientific simulation papers make claims that may overstate what the underlying evidence supports. A retrieval-based screening pipeline fetches candidate evidence from a PDF corpus and feeds it to a downstream relation-specific classifier (R4). The naive assumption is that high-recall PDF retrieval directly yields usable downstream screening signal.

This assumption fails. Raw retrieved PDF chunks are not screening-compatible evidence units: they are long, noisy, multi-sentence blocks that carry page metadata, section headers, and concatenated sentences. Downstream R4 screening — which relies on NLI pair features and handcrafted action-gap features — is built for single-sentence evidence units. Feeding raw chunks to R4 collapses strong_action_overclaim screening (strong_F1 = 0.1806).

The contribution of this project is to show that a simple, unsupervised evidence canonicalization step (selecting the best single sentence from the top-5 BM25 chunks by token overlap with the claim) restores the screening signal (strong_F1 = 0.4503), and that this canonicalized signal is sufficient to construct a conservative second-stage human review queue.

---

## 2. Pipeline

```text
PDF corpus
→ BM25 top-k retrieval (top-5 chunks per claim)
→ best_sentence_top5_overlap evidence canonicalization
    (split each chunk into sentences; pick the sentence with highest
     F1 token overlap with the claim; unsupervised, no labels used)
→ frozen R4 out-of-fold screening
    (10 seeds [11,22,33,44,55,66,77,88,99,111];
     per-seed thresholds; majority-vote aggregation;
     only test/dev OOF predictions used, no train-split leakage)
→ G_conservative_precision risk ranking
    (flag=1 AND p_contra < t_contra_low → rank by p_strong - entropy;
     else → fallback; best of 8 ranking variants by P@20)
→ second-stage human review queue (top-100 prioritized candidates)
```

### Stage-by-stage data flow

1. **Input.** SimClaim candidate pool (444 claim-evidence pairs, 111 evidence groups, 6 domains, balanced 1:1:1:1 across supported / mild_scope_overclaim / strong_action_overclaim / contradiction_candidate).
2. **Retrieval.** For each claim, BM25 retrieves top-5 chunks from the PDF corpus.
3. **Canonicalization.** For each candidate, each of the 5 chunks is split into sentences; the sentence with the highest F1 token overlap with the claim is selected as the screening evidence. No labels are used.
4. **Feature computation.** NLI model produces 7 features (entailment / neutral / contradiction probabilities + derived scores). Action-gap lexicons produce 9 features (claim-minus-evidence counts across 8 term categories + TF-IDF overlap). R4 uses NLI(7) for contradiction detection, NLI(7)+action-gap(9)=16 for strong_action detection, NLI(7)+scope_gap=8 for the SVM mild-vs-supported split.
5. **R4 screening.** 10 seeds each produce an out-of-fold prediction via a 3-classifier cascade (contradiction → strong_action → SVM). Per-seed thresholds route each candidate. Majority vote across seeds produces the final label; probability means become ranking inputs.
6. **Ranking.** 8 ranking variants are computed; G_conservative_precision is selected (P@20 = 0.45, best).
7. **Output.** Top-100 review queue for human adjudication.

---

## 3. Frozen constraints

The following are frozen and must not be changed:

- **R4 artifacts.** 10-seed classifiers, scalers, and per-seed thresholds in `experiments/r4_minimal_recovery_v1/artifacts/` are frozen. No retraining, no threshold tuning.
- **NLI cache.** NLI probabilities for all top-5 sentences are cached; model version is fixed to avoid drift.
- **V3.17 baseline metrics.** strong_F1 = 0.4503 and all companion metrics are the frozen reference for ablations.
- **SimClaim data.** 444 pairs with silver labels are frozen. Gold adjudication has not begun.
- **Group-aware split.** Train/dev/test splits use `target_candidate_group_id` to prevent group leakage across splits. No random splitting.
- **No LLM/API calls** in the mainline pipeline.
- **No new training.** No new model is trained for the mainline.
- **No threshold changes.** R4 per-seed thresholds are frozen.
- **No original data changes.** SimClaim CSV and PDF corpus are read-only.

---

## 4. Metrics (frozen V3.17 reference, 436 eval candidates)

| Metric | Value | Note |
|---|---|---|
| strong_F1 | 0.4503 | main metric |
| strong_recall | 0.7064 | high recall, second-stage value |
| strong_precision | 0.3305 | low precision, motivates second-stage |
| macro_F1 | 0.3847 | lower than LLM; R4 is not overall-beats-LLM |
| precision@20 | 0.45 | review queue top-20 precision |
| precision@50 | 0.36 | review queue top-50 precision |
| recall@100 | 0.3303 | review queue top-100 coverage |
| FP/TP @ 5% prevalence | 11.24 | second-stage viable (threshold ≤ 20) |
| standalone viable | false | FP/TP @ 1% = 66.82; R4 is second-stage only |
| second-stage viable | true | R4 is second-stage only |
| raw BM25 top1 strong_F1 | 0.1806 | raw chunks degrade screening |
| oracle span strong_F1 | 0.4257 | upper bound |
| canonicalization gain | +0.2697 | 0.4503 − 0.1806 |
| oracle-to-best gap | −0.0246 | canonicalization near oracle |

---

## 5. Safe claims

- PDF retrieval is feasible.
- Raw retrieved chunks degrade R4 screening.
- Evidence canonicalization restores strong_action screening.
- Simple overlap-based canonicalization is robust (6/9 canonicalization formats achieve strong_F1 > 0.40; the V3.18 learned selector did not improve over the simple overlap selector).
- R4 is a second-stage screening router, not standalone.
- SimClaim is a controlled silver diagnostic test set (444 pairs, 111 groups, 6 domains, balanced 1:1:1:1).
- R4 provides targeted Level-2 strong_action screening signal (strong_recall = 0.7064) where LLM judges under-detect (strong_recall = 0.04 under tested prompts). This is a controlled silver-stage finding, not a fundamental limit of LLMs.

## Not-safe claims (do NOT make)

- "R4 beats LLM overall." — R4 macro_F1 (0.4238 historical / 0.3847 V3.17) is lower than LLM (0.5270 DeepSeek-V3 / 0.5523 GPT-5.5).
- "Gold validated." — All labels are silver; gold adjudication has not begun.
- "Natural distribution / natural prevalence." — SimClaim is a controlled counterfactual diagnostic set.
- "Full automatic review." — R4 produces a review queue for human second-stage review.
- "Standalone detector." — R4 standalone viability is false.
- "Learned selector/ranker improves main method." — V3.18 intelligent upgrade is a negative ablation; V3.17 baseline remains selected.
- "Raw BM25 chunks alone solve screening." — Raw BM25 top1 strong_F1 = 0.1806; canonicalization is required.
- "Local LLM baseline completed." — Local LLM baseline is future work.
- "Full shared-threshold CESE-OCN neural architecture validation." — The older CESE-OCN architecture is development history / future architecture, not the current empirical claim.
- "The model fully understands scientific language." — R4 is a feature-based screening router.

---

## 6. Relation to RIGOURATE

**RIGOURATE** is a general scientific overstatement scoring framework. It targets broad scientific claims and assigns ordinal overstatement scores across multiple dimensions.

**This project is narrower and complementary.** It focuses on **simulation claim escalation screening**, especially strong action / deployment / safety overclaims — cases where a simulation claim asserts stronger real-world action, deployment readiness, or safety guarantees than the evidence supports. The output is an offline, auditable, second-stage review queue, not a general overstatement score.

Key differences:

| Aspect | RIGOURATE | This project (V3.17) |
|---|---|---|
| Scope | General scientific overstatement | Simulation claim escalation (strong_action focus) |
| Output | Ordinal overstatement score | Second-stage review queue (prioritized) |
| Evidence handling | Assumes clean evidence input | Studies retrieval-to-screening format shift; canonicalization is the bridge |
| Architecture | General scoring model | R4 relation-specific screening router (NLI + action-gap features) |
| Auditability | Model-based | Feature-based, lexicon-traceable (auditable) |
| Validation status | External | Controlled silver diagnostic only; not gold; not human-audited |

**Important:** Official RIGOURATE code/data/models are not publicly available. Any RIGOURATE-related baseline in this repository is an explicit scalar proxy inspired by RIGOURATE's design, not an official reproduction.

This project does not claim to reproduce RIGOURATE, beat RIGOURATE, or replace RIGOURATE. It addresses a narrower, complementary problem (simulation claim escalation screening with retrieval-to-screening canonicalization) that RIGOURATE does not directly solve.

---

## 7. Limitations

- **Silver labels.** All labels are AI-preannotated silver. Gold adjudication has not begun. Silver label noise may affect selector/ranker training (relevant to V3.18 negative ablation).
- **Controlled diagnostic set.** SimClaim is balanced 1:1:1:1 for diagnostic pressure-testing. It is not a natural-prevalence corpus; results cannot be extrapolated to real-world prevalence.
- **R4 second-stage only.** Standalone viability is false (FP/TP @ 1% = 66.82). R4 must feed a human second-stage review queue.
- **R4 hard thresholds.** Per-seed thresholds are frozen and cannot adapt to input distribution shifts.
- **LLM comparison scope.** LLM strong_recall = 0.04 is a controlled silver-stage finding under tested prompts (DeepSeek-V3, GPT-5.5 standard/structured). It is not a fundamental limit of LLMs.
- **V3.18 negative ablation.** Learned selector strong_F1 = 0.4444 < baseline 0.4503; learned ranker P@20 = 0.35 < baseline 0.45. The learned upgrade did not improve over the simple rule-based baseline. Possible causes: feature space saturation, silver label noise, small sample size, R4 hard threshold limitations.
- **Not full CESE-OCN validation.** The older full shared-threshold CESE-OCN neural architecture is development history / future architecture, not the current empirical claim.

---

## 8. Paper narrative

**Title direction:** Evidence Canonicalization Bridges Retrieval-to-Screening Format Shift for Offline Simulation Claim Escalation Review.

**Abstract core:** High-recall PDF retrieval does not automatically yield downstream screening quality. Raw retrieved PDF chunks introduce a retrieval-to-screening format shift that damages R4/NLI/action-gap features. A simple unsupervised evidence canonicalization step (best_sentence_top5_overlap) restores strong_action_overclaim screening signal (strong_F1 from 0.1806 to 0.4503, +0.2697 gain, only −0.0246 below oracle) and supports a conservative second-stage review queue.

**Contribution structure:**

1. **Finding.** Raw PDF/BM25 chunks are not screening-compatible evidence units. The downstream failure is mainly retrieval-to-screening format shift (lengthening ablation drop = 0.3320; metadata ablation drop = 0.0101).
2. **Method.** Simple unsupervised evidence canonicalization (token-overlap sentence selection from top-5 BM25 chunks) restores the screening signal.
3. **Positioning.** R4 is an offline, auditable, second-stage strong_action screening router (standalone_viable = false; second_stage_viable = true). It is not a standalone detector, not an LLM replacement, and not a full shared-threshold CESE-OCN validation.
4. **Negative ablation.** V3.18 learned selector/ranker did not improve over the rule-based baseline, confirming that simple overlap-based canonicalization is robust under the current feature space.

**Safety framing:** All results are silver-label diagnostic only. Not gold. Not human-audited. Not SOTA. Not natural-distribution prevalence. Not a standalone classifier. Not automatic peer review. Not a replacement for human judgment.

**Cross-reference:**
- `_MAINLINE_CURRENT/_FINAL_PAPER_OUTLINE_CURRENT.md` — full paper skeleton
- `_MAINLINE_CURRENT/_FINAL_NUMBERS_FOR_PAPER.csv` — paper-allowed numbers
- `_MAINLINE_CURRENT/_MAINLINE_EVIDENCE_MAP.md` — claim → evidence → metric → source
- `experiments/v3_18_intelligent_upgrade_v1/v3_17_frozen_baseline_metrics.json` — frozen metrics
- `experiments/r4_evidence_canonicalization_v1/evidence_canonicalization_gate.json` — canonicalization gate
- `experiments/canonicalized_review_queue_v1/canonicalized_review_queue_gate.json` — review queue gate
