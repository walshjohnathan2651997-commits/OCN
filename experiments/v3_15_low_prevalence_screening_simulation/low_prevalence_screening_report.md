# Low-Prevalence Screening Simulation Report

**Task:** V3.15 Low-Prevalence Screening Simulation + Natural Distribution Stress Test
**Date:** 2026-07-05
**Status:** Simulated low-prevalence screening analysis (NOT real natural distribution; NOT gold; NOT new experiments)
**Output directory:** `D:\ocn\experiments\v3_15_low_prevalence_screening_simulation\`

---

## 1. Simulation design

**Base data:** 100 matched samples from `gpt_vs_r4_deepseek_comparison.csv` (25 supported, 25 mild_scope_overclaim, 25 strong_action_overclaim, 25 contradiction_candidate; all four methods' predictions available: R4, GPT standard, GPT structured, DeepSeek).

**Simulation method:** Bootstrap resampling with controlled prevalence.

- **Prevalence levels tested:** 1%, 3%, 5%, 10%, 15%, 20%, 25% (strong_action_overclaim).
- **Simulated population size per bootstrap:** N=1000.
- **Non-strong composition (fixed):** 80% supported, 15% mild_scope_overclaim, 5% contradiction_candidate (approximating natural scientific writing where supported dominates).
- **Bootstrap iterations per prevalence:** 1000.
- **Random seed:** 20260705 (frozen for reproducibility).
- **No gold, no API, no new model training, no threshold retuning, no original data modification.**

**Important caveats:**
- This is a **simulated low-prevalence screening analysis**, NOT a real natural-distribution study.
- The simulation reuses existing R4/LLM predictions on 100 matched samples; it does NOT collect new predictions.
- The non-strong composition (80/15/5) is a reasonable approximation but NOT empirically validated against a real natural-prevalence corpus.
- All results are on silver labels (pre-gold); gold adjudication may shift conclusions.

---

## 2. Headline results

### R4 screening metrics by prevalence (mean over 1000 bootstraps)

| Prevalence | Recall | Precision | Positive-F1 | FP/TP (median) | Review Burden | NNR | Accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1% | 0.3626 | 0.0078 | 0.0153 | 121.0 | 46.3% | 159.3 | 0.534 |
| 3% | 0.3606 | 0.0235 | 0.0441 | 41.0 | 46.1% | 45.7 | 0.531 |
| 5% | 0.3585 | 0.0391 | 0.0704 | 24.7 | 45.9% | 26.6 | 0.527 |
| 10% | 0.3632 | 0.0799 | 0.1310 | 11.5 | 45.4% | 12.7 | 0.518 |
| 15% | 0.3621 | 0.1208 | 0.1811 | 7.3 | 45.0% | 8.4 | 0.509 |
| 20% | 0.3605 | 0.1626 | 0.2240 | 5.2 | 44.3% | 6.2 | 0.501 |
| 25% | 0.3606 | 0.2061 | 0.2622 | 3.8 | 43.7% | 4.9 | 0.493 |

**NNR = Number Needed to Review per true strong_action case (lower is better).**

### LLM judges (GPT standard / GPT structured / DeepSeek) — all three nearly identical

| Prevalence | Recall | Precision | Positive-F1 | FP/TP (median) | Review Burden | Accuracy |
| --- | --- | --- | --- | --- | --- | --- |
| 1% | 0.0432 | 0.353 | 0.0759 | 0.0 | 0.04% | 0.990 |
| 5% | 0.0399 | 0.869 | 0.0755 | 0.0 | 0.20% | 0.952 |
| 10% | 0.0395 | 0.985 | 0.0754 | 0.0 | 0.40% | 0.904 |
| 25% | 0.0404 | 1.000 | 0.0774 | 0.0 | 1.01% | 0.760 |

### LLM-missed strong_action captured by R4

| Prevalence | LLM-missed strong captured by R4 (mean) | Strong cases missed by ALL methods (mean) |
| --- | --- | --- |
| 1% | 3.19 | 6.37 |
| 3% | 9.64 | 19.18 |
| 5% | 15.93 | 32.07 |
| 10% | 32.36 | 63.68 |
| 25% | 80.04 | 159.85 |

---

## 3. Required answers

### Q1. At strong_action prevalence = 1%, does R4 still have practical screening value?

**Verdict: NO — not as a standalone screener. R4 at 1% prevalence has FP/TP = 121 (median), precision = 0.78%, and review burden = 46.3%. This means: to catch 36% of true strong_action cases (recall = 0.36), R4 flags 46% of the entire population for review, and for every true strong_action found, 159 non-strong cases must be reviewed. This is operationally impractical as a standalone screener.**

However, R4 retains *complementary* value at 1% prevalence:
- R4 captures 3.19 strong_action cases (per 1000 samples) that ALL three LLM judges miss.
- LLM judges at 1% prevalence have recall = 0.043 (capture only 4.3% of true strong_action), but accuracy = 0.990 (because 99% of samples are non-strong, and LLMs correctly classify most non-strong as non-strong).
- **The high-accuracy / low-recall pattern of LLMs at 1% prevalence is the screening failure mode:** LLMs appear to perform well (99% accuracy) but miss 95.7% of true strong_action cases.

**Conclusion for Q1:** R4 at 1% prevalence is NOT viable as a standalone screener (FP/TP = 121, review burden = 46%). R4 retains value only as a high-recall first-stage filter in a two-stage pipeline (R4 → LLM/human second-stage confirmation), where its 36% recall captures cases LLMs miss.

### Q2. At prevalence = 3% / 5% / 10%, is FP/TP acceptable?

**Verdict:**
- **3% prevalence:** FP/TP = 41 (median), precision = 2.3%, review burden = 46%. **NOT acceptable as standalone.** NNR = 46 (must review 46 cases per true strong found).
- **5% prevalence:** FP/TP = 25 (median), precision = 3.9%, review burden = 46%. **Borderline at best.** NNR = 27.
- **10% prevalence:** FP/TP = 12 (median), precision = 8.0%, review burden = 45%. **Marginal.** NNR = 13. This is the threshold where R4 starts to become operationally viable as a standalone screener for high-risk applications where the cost of missing a strong_action overclaim is very high (e.g., safety-critical claim review).

**For context:** In medical screening, FP/TP ratios of 5–10 are common for high-risk screenings (e.g., mammography, colonoscopy triage). R4 at 10% prevalence (FP/TP = 12) is in this range. R4 at 5% prevalence (FP/TP = 25) is above this range but may be acceptable for very-high-risk applications. R4 at 1–3% prevalence (FP/TP = 41–121) is outside the acceptable range for standalone screening.

### Q3. Is R4's review burden controllable?

**Verdict: NO — R4's review burden is essentially fixed at ~45% regardless of prevalence, because R4 over-routes a large fraction of samples to strong_action (35/100 in the base data, including 26 false positives). This is a known trade-off (§IX item 5): R4 improves strong recall at the cost of supported/mild → strong false positives.**

The review burden does NOT decrease with lower prevalence because:
- R4's strong_action prediction rate is determined by its thresholds (frozen: t_contra=0.48, t_strong=0.535, t_svm=0.51), NOT by the true prevalence.
- At 1% prevalence, R4 still flags ~46% of samples as strong_action, but only 0.78% of those flagged are true strong (precision = 0.78%).

**Implication:** To control review burden at low prevalence, R4 would need either (a) a prevalence-aware threshold adjustment (NOT done in this paper — thresholds are frozen), or (b) a second-stage confirmation filter (e.g., LLM-as-judge on R4-flagged samples). Option (b) is the recommended two-stage pipeline.

### Q4. Do LLMs show high accuracy but low recall at low prevalence?

**Verdict: YES — this is the dominant LLM failure mode at low prevalence.**

| Prevalence | LLM Accuracy | LLM Recall | LLM Precision |
| --- | --- | --- | --- |
| 1% | 0.990 | 0.043 | 0.353 |
| 5% | 0.952 | 0.040 | 0.869 |
| 10% | 0.904 | 0.040 | 0.985 |
| 25% | 0.760 | 0.040 | 1.000 |

**Pattern:** At 1% prevalence, LLMs achieve 99% accuracy (because 99% of samples are non-strong, and LLMs correctly classify most non-strong as non-strong), but only 4.3% recall (they miss 95.7% of true strong_action cases). At 25% prevalence, LLM accuracy drops to 76% (because 25% of samples are strong, and LLMs miss most of them), but recall is still only 4%.

**This is the screening failure mode the paper highlights:** accuracy is a misleading metric for screening at low prevalence. A system that predicts "non-strong" for everything achieves ~99% accuracy at 1% prevalence but has 0% recall. LLMs under the tested prompts approximate this failure mode.

**R4 vs. LLM at low prevalence:**
- R4: low accuracy (~53% at 1%), moderate recall (36%), very low precision (0.78%), high review burden (46%).
- LLM: high accuracy (~99% at 1%), very low recall (4.3%), moderate-high precision (35% at 1%, rising to 100% at 25%), very low review burden (0.04%).

**The two are complementary:** R4 provides the recall LLMs lack; LLMs provide the precision R4 lacks. A two-stage pipeline (R4 → LLM) could achieve both.

### Q5. Is R4 still suitable as a front-stage screener for human/LLM-assisted review?

**Verdict: YES — but only as the first stage of a two-stage pipeline, NOT as a standalone classifier.**

**R4's role in a two-stage pipeline:**
1. **Stage 1 (R4):** High-recall coarse filter. R4 flags ~46% of samples as strong_action candidates. This captures 36% of true strong_action cases (recall = 0.36), including cases all LLM judges miss.
2. **Stage 2 (LLM or human):** High-precision fine filter. LLM/human reviews the R4-flagged samples and confirms/rejects the strong_action label. LLMs achieve near-100% precision on their own predictions (when they do predict strong, they're almost always right), so LLM-as-second-stage on R4-flagged samples could dramatically reduce false positives.

**Why R4 is NOT suitable as a standalone screener at low prevalence:**
- At 1% prevalence, R4 flags 46% of samples for review, with FP/TP = 121. No human review team can afford to review 46% of all scientific claims.
- At 10% prevalence, R4 flags 45% of samples for review, with FP/TP = 12. This is borderline for high-risk applications but still very heavy.

**Why R4 IS suitable as a first-stage filter:**
- R4 captures 36% of true strong_action cases that LLMs miss (at all prevalences).
- R4's recall is stable (0.36) regardless of prevalence — it doesn't degrade as strong_action becomes rarer.
- R4's false positives are concentrated in the R4-flagged set, making second-stage LLM/human review efficient.

**Recommended pipeline:** R4 (stage 1, high recall) → LLM-as-judge (stage 2, high precision) → human review (stage 3, final confirmation). This is future work; the current paper does NOT implement or evaluate this pipeline.

### Q6. Which metric best represents R4's practical value at low prevalence?

**Verdict: FP/TP ratio and Number Needed to Review (NNR) are the most operationally meaningful metrics. Accuracy is misleading.**

**Metric ranking for low-prevalence screening:**
1. **FP/TP ratio** (false positives per true positive) — directly measures the operational cost of screening. R4 at 1% prevalence: FP/TP = 121 (impractical); at 10%: FP/TP = 12 (marginal); at 25%: FP/TP = 3.8 (acceptable).
2. **Number Needed to Review (NNR)** — number of cases a human reviewer must examine per true strong_action found. R4 at 1%: NNR = 159; at 10%: NNR = 13; at 25%: NNR = 5.
3. **Recall** — fraction of true strong_action cases captured. R4: stable at 0.36 across all prevalences. This is R4's strength.
4. **Precision** — fraction of flagged cases that are true strong. R4 at 1%: 0.78%; at 10%: 8.0%; at 25%: 20.6%.
5. **Positive-F1** — harmonic mean of precision and recall. R4 at 1%: 0.015; at 10%: 0.131; at 25%: 0.262.
6. **Accuracy** — MISLEADING at low prevalence. R4 at 1%: 53% (looks bad); LLM at 1%: 99% (looks good). But LLM misses 96% of true strong_action. Accuracy hides the screening failure mode.
7. **Review burden** — fraction of population flagged for review. R4: ~45% (fixed, high); LLM: <1% (low). Useful for capacity planning but not for screening quality.

**The paper should report FP/TP, NNR, recall, and precision as the primary screening metrics, with accuracy only as a secondary diagnostic.**

---

## 4. Review budget curve analysis

The review budget curve (`review_budget_curve.csv`) shows, for each review budget (fraction of population reviewed), the recall and precision achieved by each method using discrete-priority ordering (predicted strong > contradiction > mild > supported).

**Key observations (R4 at 5% prevalence):**

| Review Budget | N Reviewed | Recall | Precision | FP/TP |
| --- | --- | --- | --- | --- |
| 1% | 10 | 0.200 | 1.000 | 0.0 |
| 3% | 30 | 0.362 | 0.603 | 0.73 |
| 5% | 50 | 0.362 | 0.362 | 1.88 |
| 10% | 100 | 0.362 | 0.181 | 4.76 |
| 20% | 200 | 0.362 | 0.090 | 10.51 |
| 50% | 500 | 0.629 | 0.063 | 15.36 |

**Interpretation:**
- At 3% review budget (review 30 of 1000 samples), R4 achieves 36% recall with 60% precision (FP/TP = 0.73). This is the **optimal operating point** for R4 at 5% prevalence: minimal review burden, maximum precision at that recall.
- At 10% review budget, R4's precision drops to 18% (FP/TP = 4.76) because the additional reviewed samples are mostly false positives.
- At 50% review budget, R4's recall jumps to 63% because the budget now includes samples R4 predicted as non-strong but which are actually strong (silver label strong but R4 predicted mild/contradiction/supported).

**Discrete-priority approximation caveat:** This curve uses discrete priority ordering (predicted strong > contradiction > mild > supported), NOT a continuous score. A continuous score (e.g., RIGOURATE-style scalar) would allow finer-grained prioritization. The discrete-priority curve is a lower bound on what a continuous-score approach could achieve.

---

## 5. Summary verdict

| Prevalence | R4 standalone viable? | R4 as first-stage filter? | LLM standalone viable? | Recommended configuration |
| --- | --- | --- | --- | --- |
| 1% | NO (FP/TP=121) | YES (captures LLM-missed) | NO (recall=4.3%) | Two-stage: R4 → LLM/human |
| 3% | NO (FP/TP=41) | YES | NO (recall=4.0%) | Two-stage: R4 → LLM/human |
| 5% | BORDERLINE (FP/TP=25) | YES | NO (recall=4.0%) | Two-stage: R4 → LLM/human |
| 10% | MARGINAL (FP/TP=12) | YES | NO (recall=4.0%) | Two-stage or R4 standalone for high-risk |
| 25% (balanced) | YES (FP/TP=3.8) | YES | NO (recall=4.0%) | R4 standalone (matches balanced SimClaim) |

**Key takeaway:** R4's screening value is **prevalence-dependent**. On the balanced SimClaim diagnostic set (25% prevalence), R4 is viable as a standalone screener (FP/TP = 3.8). At realistic low prevalence (1–5%), R4 is NOT viable as a standalone screener but retains value as a high-recall first-stage filter in a two-stage pipeline. LLMs are NOT viable as standalone screeners at any prevalence (recall ≤ 4.3%) despite high accuracy at low prevalence.

**This simulation SUPPORTS the paper's positioning of R4 as a screening-oriented complement, NOT a standalone classifier.** The paper's §VI.B and §VIII.D.B results (on balanced SimClaim) are diagnostic-stage; the low-prevalence simulation shows that deployment-stage screening requires a two-stage pipeline.

---

## 6. Prohibitions enforced

- No gold annotation — PASS (all results on silver labels).
- No API calls — PASS (only existing predictions reused).
- No new model training — PASS (only existing R4/LLM predictions).
- No threshold retuning — PASS (R4 thresholds frozen).
- No original data modification — PASS (only bootstrap resampling).
- No simulation written as real natural distribution — PASS (clearly labelled "simulated low-prevalence screening analysis").
- No silver written as gold — PASS (all results labelled silver-stage).

---

## 7. Limitations of this simulation

1. **Base data is 100 matched samples.** The bootstrap resamples from a small pool (25 strong_action cases), so the diversity of strong_action cases is limited. A larger base pool would give more realistic prevalence simulation.
2. **Non-strong composition (80/15/5) is a heuristic approximation.** Real natural-prevalence composition is unknown and may vary by domain.
3. **R4's prediction distribution is fixed.** R4 flags ~35% of samples as strong_action regardless of true prevalence (because thresholds are frozen). A prevalence-aware threshold adjustment could improve low-prevalence precision, but is NOT tested here (frozen thresholds).
4. **LLM predictions are single-run, temperature 0, no variance estimate.** LLM recall = 4% may be prompt-specific; different prompts could yield different recall.
5. **All results are on silver labels (pre-gold).** Gold adjudication may shift the base predictions and therefore the simulation results.
6. **The simulation does NOT test the two-stage pipeline.** The recommended R4 → LLM pipeline is a proposal, not an empirical result.
7. **Discrete-priority review budget curve is a lower bound.** A continuous-score approach could achieve better precision at the same recall.
