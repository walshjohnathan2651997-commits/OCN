# Current Mainline (Confidential Lightweight V3.17) — Detailed Specification

**Date:** 2026-07-06
**Authority:** This file is the detailed companion to `CURRENT_MAINLINE.md`. If any other document conflicts with this file on the current mainline, this file wins.

---

## 1. Problem framing

This project studies **retrieval-to-screening format shift in confidential local PDF review**.

In confidential settings (proprietary simulation reports, internal technical reviews, restricted-access scientific PDFs), evidence-sufficiency screening must run locally: no API calls, no cloud dependency, no model training on raw text. A retrieval-based screening pipeline fetches candidate evidence from local PDFs and feeds it to a downstream relation-specific classifier (R4).

The naive assumption is that high-recall PDF retrieval directly yields usable downstream screening signal. This assumption fails. Raw retrieved PDF chunks are not screening-compatible evidence units, and the downstream R4 classifier — which relies on NLI pair features and handcrafted action-gap features — collapses when fed raw chunks.

The contribution of this project is to show that a simple, unsupervised, local evidence canonicalization step restores the screening signal sufficiently to construct a conservative second-stage human review queue, without any API calls, cloud dependency, or new training.

---

## 2. Why high-recall retrieval is insufficient

High-recall BM25 retrieval successfully finds relevant PDF chunks: the retrieval step is not the bottleneck. The bottleneck is **what the downstream classifier receives**.

R4 screening uses two feature families:

1. **NLI pair features (7 dims).** A pretrained NLI model scores the (evidence, claim) pair. The model expects a single, coherent evidence sentence. When fed a multi-sentence chunk, the pair becomes semantically diluted: the NLI model cannot isolate which sentence is the actual evidence.
2. **Action-gap lexicon features (9 dims).** Handcrafted lexicons count action / deployment / safety / scope / certainty terms in the claim minus the evidence. These lexicons are designed for sentence-scale evidence. When the evidence is a multi-sentence chunk, term counts are inflated by irrelevant sentences, and the gap signal is washed out.

The result: raw BM25 top1 chunk produces strong_F1 = 0.1806, far below the oracle-span upper bound of 0.4257. Retrieval found the right region of the PDF, but the format of the retrieved unit broke the downstream classifier.

---

## 3. What retrieval-to-screening format shift means

"Retrieval-to-screening format shift" is the mismatch between:

- **What retrieval returns:** long, noisy, multi-sentence PDF chunks with page metadata, section headers, and concatenated paragraphs.
- **What the screening classifier expects:** clean, single-sentence evidence units matched against a single claim.

This is not a retrieval quality problem (BM25 finds the right pages). It is not a classifier quality problem (R4 works well on clean sentence evidence). It is an **interface problem** between the two stages.

The format shift has two components, confirmed by ablation:

- **Lengthening (dominant).** Concatenating multiple sentences into one evidence unit inflates NLI dilution and lexicon noise. Ablation drop: 0.3320 (oracle span artificially lengthened to chunk-scale).
- **Metadata contamination (minor).** Page headers, titles, and reference markers add irrelevant tokens. Ablation drop: 0.0101 (oracle span with metadata prepended).

---

## 4. Why raw chunks fail

Raw BM25 chunks fail for three concrete reasons:

1. **NLI dilution.** The NLI model receives (multi_sentence_chunk, claim). The entailment / neutral / contradiction probabilities are computed over the entire chunk, not the relevant sentence. A chunk where one sentence entails the claim and four sentences are neutral produces a diluted "neutral-ish" signal.
2. **Action-gap inflation.** The lexicon counter scans the entire chunk for action / deployment / safety terms. Irrelevant sentences inflate the evidence-side count, shrinking the claim-minus-evidence gap that R4 uses to detect escalation.
3. **Length mismatch.** R4's SVM sub-classifier uses `length_diff` (claim length minus evidence length) as a feature. A 3-word claim vs. a 200-word chunk produces an extreme negative `length_diff` that the SVM never saw in training (where evidence was sentence-scale).

---

## 5. Why evidence canonicalization is the current contribution

Evidence canonicalization bridges the retrieval-to-screening interface. The method is simple, unsupervised, and local:

1. For each claim, BM25 retrieves top-5 PDF chunks.
2. Each chunk is split into sentences.
3. For each sentence, compute F1 token overlap with the claim: `2 * |claim_tokens ∩ sent_tokens| / (|claim_tokens| + |sent_tokens|)`.
4. Select the sentence with the highest overlap as the screening evidence.

No labels are used. No model is trained. No API is called. The selector runs locally on token overlap.

**Result:** strong_F1 improves from 0.1806 (raw BM25 top1) to 0.4503 (canonicalized), a +0.2697 gain, only -0.0246 below the oracle-span upper bound (0.4257). The canonicalization step recovers 97% of the oracle-to-raw gap.

**Robustness:** 6 of 9 canonicalization formats achieve strong_F1 > 0.40. The V3.18 learned selector (sklearn, group-aware split) did NOT improve over the simple overlap selector (strong_F1 = 0.4444 < 0.4503), confirming that the simple method is robust under the current feature space.

---

## 6. Why the system is second-stage review queue only

R4's strong_recall is high (0.7064) but strong_precision is low (0.3305). This means R4 catches most true strong_action overclaims but also flags many false positives.

- **Standalone viability is false.** At 1% prevalence (realistic for unfiltered corpora), FP/TP = 66.82. Every true positive comes with 66 false positives. This is unusable as a standalone detector.
- **Second-stage viability is true.** At 5% prevalence (after a pre-filter or in a focused review batch), FP/TP = 11.24, and recall ≥ 0.6. This is acceptable as a review-queue generator: the queue prioritizes candidates for human adjudication, and humans make the final call.

The system is therefore positioned as a **conservative second-stage screener / review queue generator**, not a standalone classifier, not an automatic peer reviewer, and not a replacement for human judgment.

---

## 7. Relationship to SciFact-Open / SciClaimHunt / RIGOURATE / LLM-as-judge

This work is **narrower and complementary** to existing work in scientific claim verification and overstatement detection.

| Work family | Scope | This project (V3.17) |
|---|---|---|
| **SciFact-Open** | Open scientific claim verification over published corpora | Focuses on verification label (supports/refutes/none). Does not study retrieval-to-screening format shift. This project focuses on the interface failure between retrieval and screening, using a confidential local corpus. |
| **SciClaimHunt** | Claim-evidence retrieval benchmark | Focuses on retrieval quality. Does not study downstream screening. This project shows retrieval quality is necessary but not sufficient; the format of retrieved units matters. |
| **RIGOURATE** | General scientific overstatement scoring | Broad overstatement scoring across scientific claims. Official code/data not public. This project is narrower: simulation claim escalation screening (strong action / deployment / safety overclaims), with an offline auditable second-stage review queue. |
| **LLM-as-judge** | LLM-based judging of scientific claims | High overall macro_F1 (0.5270 DeepSeek-V3 / 0.5523 GPT-5.5) but under-detects strong_action (strong_recall = 0.04 under tested prompts). This project does not claim R4 beats LLM overall; R4 provides targeted strong_action recall where LLM under-detects. This is a controlled silver-stage finding, not a fundamental LLM limit. |

**Key distinction:** Existing works cover general claim verification (SciFact-Open), retrieval benchmarking (SciClaimHunt), broad overstatement scoring (RIGOURATE), or LLM judging (LLM-as-judge). None of them directly study the **retrieval-to-screening interface failure** in confidential local PDF review, which is the focus of this project.

This project does not claim to reproduce, beat, or replace any of the above. It addresses a narrower, complementary problem.

---

## 8. Frozen constraints

- **R4 artifacts.** 10-seed classifiers, scalers, and per-seed thresholds are frozen. No retraining, no threshold tuning.
- **NLI cache.** NLI probabilities are cached; model version is fixed.
- **V3.17 metrics.** strong_F1 = 0.4503 and companion metrics are the frozen reference.
- **SimClaim data.** 444 pairs with silver labels are frozen. Gold adjudication has not begun.
- **Group-aware split.** No group leakage across train/dev/test.
- **No LLM/API/cloud calls** in the mainline pipeline.
- **No new training.** No new model is trained for the mainline.
- **No threshold changes.** R4 per-seed thresholds are frozen.
- **No original data changes.** SimClaim CSV and PDF corpus are read-only.

---

## 9. Metrics (frozen V3.17 reference, 436 eval candidates)

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

## 10. Safe claims

- local / no-API / no-cloud / no-training pipeline
- controlled silver diagnostic setting
- retrieval-to-screening format shift analysis
- evidence canonicalization restores strong_action_overclaim screening signal
- second-stage review queue support

## Not-safe claims (do NOT make)

- no gold benchmark claim
- no human-audited dataset claim
- no SOTA claim
- no natural-prevalence claim
- no full shared-threshold CESE-OCN validation claim
- no automatic peer review claim
- no standalone detector claim
- no "R4 beats LLM overall" claim
- no "learned selector/ranker improves main method" claim (V3.18 is a negative ablation)

---

## 11. Limitations

- **Silver labels.** All labels are AI-preannotated silver. Gold adjudication has not begun.
- **Controlled diagnostic set.** SimClaim is balanced 1:1:1:1 for diagnostic pressure-testing. Not natural-prevalence.
- **R4 second-stage only.** Standalone viability is false.
- **R4 hard thresholds.** Per-seed thresholds are frozen; cannot adapt to distribution shifts.
- **LLM comparison scope.** LLM strong_recall = 0.04 is a controlled silver-stage finding under tested prompts, not a fundamental LLM limit.
- **V3.18 negative ablation.** Learned selector/ranker did not improve over the rule-based baseline.
- **Confidential corpus.** Raw PDFs and real claim text are not released; see `docs/data_release_policy.md`.

---

## 12. Paper narrative

**Title direction:** Evidence Canonicalization Bridges Retrieval-to-Screening Format Shift in Confidential Local PDF Review for Simulation Claim Escalation Screening.

**Abstract core:** High-recall PDF retrieval does not automatically yield downstream screening quality. Raw retrieved PDF chunks introduce a retrieval-to-screening format shift that damages R4/NLI/action-gap features. A simple unsupervised local evidence canonicalization step (best_sentence_top5_overlap) restores strong_action_overclaim screening signal (strong_F1 from 0.1806 to 0.4503, +0.2697 gain) and supports a conservative second-stage review queue — all without API calls, cloud dependency, or new training.

**Contribution structure:**

1. **Finding.** Raw PDF chunks are not screening-compatible; format shift (lengthening dominant, metadata minor) breaks R4 features.
2. **Method.** Simple unsupervised local canonicalization restores the signal.
3. **Positioning.** R4 is an offline, auditable, second-stage screening router. Not standalone, not LLM replacement, not full CESE-OCN validation.
4. **Negative ablation.** V3.18 learned upgrade did not improve; simple overlap canonicalization is robust.
5. **Confidentiality.** Local/no-API/no-cloud pipeline; raw PDFs and real claim text are not released.

**Cross-reference:**
- `_MAINLINE_CURRENT/_FINAL_PAPER_OUTLINE_CURRENT.md` — full paper skeleton
- `_MAINLINE_CURRENT/_FINAL_NUMBERS_FOR_PAPER.csv` — paper-allowed numbers
- `docs/data_release_policy.md` — confidentiality policy
- `docs/leakage_and_confidentiality_policy.md` — forbidden-field rules
