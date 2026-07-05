# RIGOURATE-Style Scalar Overstatement Baseline Plan (V3.13, Plan-Only)

**Date:** 2026-07-05
**Paper version:** V3.13 Differentiated Against RIGOURATE / ForceBench / CLAIM-BENCH
**Status:** **PLAN ONLY. NOT A COMPLETED EXPERIMENT. NOT A RUN BASELINE.**

## Purpose

This file specifies the plan for a **RIGOURATE-style scalar overstatement baseline** to be run in V3.14+ (corresponding to P2 of the V3.13 strengthening plan). It is **plan-only** in V3.13: no API calls, no model runs, no results. The plan is documented here so the advisor can review the proposed methodology before authorizing the run.

## Why This Baseline Is Needed

§II.A of the V3.13 paper claims that RIGOURATE [30] estimates the **degree of overstatement** as a continuous score, while CESE-OCN diagnoses the **type of evidence-sufficiency mismatch** as a four-class relation. In particular, the paper claims that "RIGOURATE does not isolate mild scope expansion from high-risk action/deployment overclaim as separate operational classes."

This is currently a **conceptual argument** (§IX item 9 explicitly states the differentiation is positioning-level, not empirical). To convert it to an **empirically demonstrated** argument, we need to test whether a RIGOURATE-style scalar score alone can distinguish `mild_scope_overclaim` from `strong_action_overclaim`, or whether the four-class relation-type decomposition is operationally necessary.

## Branch A — RIGOURATE Public Model Available (Preferred)

### Trigger
If RIGOURATE's public model / code / checkpoint is available (search arXiv, GitHub, Hugging Face for the RIGOURATE paper [30] release), run it directly on SimClaim.

### Steps
1. **Locate RIGOURATE release.** Search for the official RIGOURATE code repository, model checkpoint, or inference API.
2. **Input formatting.** Convert each of the 444 SimClaim claim-evidence pairs into RIGOURATE's expected input format (claim text + retrieved evidence passage). For SimClaim, the evidence passage is already provided per pair; no retrieval step is needed.
3. **Run RIGOURATE inference.** Produce a continuous overstatement score per claim-evidence pair. RIGOURATE's original output scale is preserved (e.g., 0–3 or 0–1, depending on the release).
4. **Save predictions.** Write `rigourate_branch_a_predictions.csv` with columns: `pair_id`, `silver_label`, `rigourate_score`.
5. **Evaluate.** Proceed to the Evaluation section below.

### Cost
- Engineering time: ~1–2 days to integrate RIGOURATE inference.
- Compute: modest if CPU-compatible; higher if GPU inference is required.
- API cost: $0 (no LLM API needed if RIGOURATE has a public checkpoint).

### Risk
- RIGOURATE may not have a public release. In that case, fall back to Branch B.
- RIGOURATE may have been trained on a different domain distribution than SimClaim's six domains; cross-domain score calibration may be needed.

## Branch B — Construct RIGOURATE-Style Scalar Baseline (Fallback)

### Trigger
If RIGOURATE's public model / code / checkpoint is NOT available, construct a RIGOURATE-style scalar baseline using a comparable scoring approach.

### Approach B1 — Fine-Tuned Regressor on SimClaim Silver Labels

1. **Train a regressor** on SimClaim silver labels (train split only) producing a continuous overstatement score per claim-evidence pair.
   - Input: claim text + evidence text (concatenated, or with NLI-style features).
   - Output: scalar score in [0, 1] or [0, 3].
   - Model: a gradient-boosted regressor (e.g., LightGBM) over TF-IDF features, or a fine-tuned small LM (e.g., DeBERTa-v3-base).
   - Training signal: silver overstatement severity — `supported` → 0, `mild_scope_overclaim` → 1, `strong_action_overclaim` → 2, `contradiction_candidate` → 3 (or treat contradiction separately and train on the three overclaim levels).
2. **Threshold to binary.** Pick a threshold τ on a held-out dev split to separate `no-overclaim` (score < τ) from `overclaim` (score ≥ τ).
3. **Test mild vs. strong separation.** Among the cases classified as `overclaim` (score ≥ τ), test whether a second threshold τ' can separate `mild_scope_overclaim` from `strong_action_overclaim` at above-chance accuracy.
4. **Save predictions.** Write `rigourate_branch_b1_predictions.csv`.

### Approach B2 — LLM Scalar Overstatement Rater

1. **Prompt a strong LLM** (GPT-5.5 or DeepSeek-V3) to rate overstatement severity per claim-evidence pair on a 0–3 or 0–1 scale. The prompt must NOT reveal the four-class taxonomy or the silver label; it must ask only for a scalar overstatement rating.
2. **Threshold to binary.** Same as B1 step 2.
3. **Test mild vs. strong separation.** Same as B1 step 3.
4. **Save predictions.** Write `rigourate_branch_b2_predictions.csv`.

### Approach B3 — Both B1 and B2
Run both B1 and B2; report both. If they agree, the scalar-baseline conclusion is robust; if they disagree, report the disagreement.

### Cost
- B1 engineering time: ~2–3 days to train and evaluate the regressor.
- B2 API cost: ~$5–$20 for 444 pairs at current DeepSeek/GPT rates (DeepSeek-V3 is cheaper).
- B3 cost: B1 + B2.

### Risk
- B1 may overfit SimClaim silver labels (since it is trained on them). Mitigation: train on train split only; evaluate on dev/test split; report train/test gap.
- B2 may leak taxonomy knowledge through the prompt. Mitigation: prompt asks only for scalar overstatement rating, no taxonomy terms.
- B2 LLM may produce inconsistent scores across runs. Mitigation: run 3 times with temperature 0; report mean and variance.

## Evaluation (Both Branches)

Once scalar scores are produced (Branch A or B), evaluate as follows.

### Evaluation 1 — Can a Scalar Score Distinguish Mild vs. Strong?

For each pair of classes (mild_scope_overclaim vs. strong_action_overclaim), compute:
- **AUC-ROC** of the scalar score for separating the two classes.
- **Optimal-threshold accuracy** on a held-out dev split.
- **Per-class score distribution** (violin plot or box plot).

**Pre-registered interpretation:**
- If AUC-ROC ≥ 0.85 and optimal-threshold accuracy ≥ 0.80, the scalar score CAN distinguish mild from strong. The four-class decomposition loses its operational-necessity argument; downgrade §VIII.F per P2 failure route.
- If AUC-ROC < 0.70 OR optimal-threshold accuracy < 0.65, the scalar score CANNOT distinguish mild from strong. The four-class decomposition is operationally necessary; §II.A differentiation claim is empirically supported.
- If 0.70 ≤ AUC-ROC < 0.85, the result is mixed; report both, add §IX item that scalar score has partial separability but relation-type decomposition adds operational value at the boundary.

### Evaluation 2 — R4 strong_action Screening vs. Scalar Baseline

Convert the scalar score to a binary `strong_action_screen` flag using a threshold chosen to maximize recall on `strong_action_overclaim` (on dev split only). Then compare:

| Metric | R4 strong_action screen | Scalar-baseline strong_action screen |
| --- | --- | --- |
| Recall on `strong_action_overclaim` | (from §VIII.D.B: 0.360) | (from this baseline) |
| FP/TP ratio | (from §VIII.D.B: 2.89) | (from this baseline) |
| Precision | (from §VIII.D.B) | (from this baseline) |

**Pre-registered interpretation:**
- If R4 recall > scalar-baseline recall by ≥ 0.10 AND R4 FP/TP ≤ scalar-baseline FP/TP, R4's relation-specific routing adds value over a thresholded scalar score; the screening-method contribution is empirically supported.
- If scalar-baseline recall ≥ R4 recall OR scalar-baseline FP/TP ≤ R4 FP/TP, the scalar baseline matches or beats R4; the screening-method contribution weakens; add §IX item per P2 failure route.
- If results are mixed, report both metrics and add §IX item specifying the trade-off.

### Evaluation 3 — Report in §VI.D

If P2 is run and succeeds, add a new §VI.D "Scalar Overstatement Baseline Comparison" with:
- Table of AUC-ROC, optimal-threshold accuracy, per-class score distribution.
- Table of R4 vs. scalar-baseline screening metrics.
- Update §II.A and Table X with an empirical column (e.g., "Empirical separation of mild vs. strong: AUC = X.XX").
- Update §IX item 9 from "positioning-level, not empirical head-to-head" to "empirically demonstrated complementarity, see §VI.D".

## What This Plan Does NOT Do

- **Does NOT claim any result.** No predictions have been generated; no AUC-ROC has been computed; no R4-vs-scalar comparison has been done.
- **Does NOT modify V3.13.** The V3.13 paper retains §IX item 9 ("positioning-level, not empirical head-to-head") until P2 is actually run.
- **Does NOT call any API in V3.13.** Branch B2 (LLM scalar rater) is specified for V3.14+; it is NOT run in V3.13.
- **Does NOT train any model in V3.13.** Branch B1 (fine-tuned regressor) is specified for V3.14+; it is NOT run in V3.13.
- **Does NOT claim RIGOURATE is available or unavailable.** Branch A vs Branch B decision is deferred to V3.14+.
- **Does NOT claim the four-class decomposition is empirically necessary.** That conclusion depends on Evaluation 1 results, which have not been generated.

## Pre-Registration

The thresholds and interpretations in the Evaluation section above are **pre-registered** in V3.13. When P2 is run in V3.14+, the results will be interpreted against these pre-registered thresholds. If the results fall in a mixed zone, the paper will report both metrics and add an explicit §IX limitation; it will NOT selectively highlight the more favorable metric.

## Cross-References

- §II.A (RIGOURATE differentiation paragraph)
- §VIII.D.B (R4 screening utility: recall 0.360, FP/TP 2.89)
- §VIII.F (why fine-grained relation typing is valuable)
- §IX item 9 (differentiation is positioning-level, not empirical)
- `V3_13_strengthening_plan_after_related_work_shift.md` (P2 entry)
- `related_work_differentiation_table.md` (Table X)
