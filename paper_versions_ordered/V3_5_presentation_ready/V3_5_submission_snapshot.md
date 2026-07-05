# V3.5 Submission Snapshot

**Date:** 2026-07-04
**Manuscript:** V3.5 Presentation Ready — Evidence Sufficiency Calibration for Scientific Claims
**Stance:** Honest, conservative. V3.5 is a presentation pass on V3.4. It is more readable than V3.4 but is **not** Q1-ready. The largest risk remains unchanged: lack of independent gold adjudication.

---

## 1. Current Strongest Selling Point

**A falsifiable framework for evidence sufficiency calibration, with a frozen main method (R4) that provides targeted value on the most consequential and hardest class (strong_action_overclaim), and a matched-sample LLM judge comparison showing that under the tested prompts, generic LLM judges (GPT-5.5, DeepSeek-V3) consistently under-detect strong_action_overclaim — bounded by silver-label and single-run limitations.**

Concretely:

- A four-class taxonomy (supported / mild_scope_overclaim / strong_action_overclaim / contradiction_candidate) with an operational decision tree (Figure 2) and 8 illustrative examples (Table 2).
- A frozen R4 mixed relation-routing framework (Figure 1) that improves strong_action positive-F1 from 0.2408 to 0.3967 (+0.1559, CI [0.1058, 0.1988], 10/10 seeds positive) on the silver-label pilot, while preserving contradiction performance.
- A matched-sample LLM judge comparison (Figure 3, Table 2) showing that GPT-5.5 standard, GPT-5.5 structured, and DeepSeek-V3 all converge on strong_action-F1 = 0.0769 (recall 0.04 = 1/25), while R4 achieves strong_F1 = 0.3000 on the same 100 samples — but with substantially lower overall macro-F1 (0.3280 vs. 0.5523). R4 is positioned as a relation-specific complement, not a replacement.
- An honest author sanity audit (40 cases) that explicitly flags 25/40 (62.5%) as questionable or unclear, with root cause analysis showing the cases are concentrated at the two hardest taxonomy boundaries (mild-vs-strong, strong-vs-contradiction).
- External sanity checks on SciFact and VitaminC showing R4-compatible methods run on public data, but public data cannot test the four-class taxonomy.

The selling point is **not** "R4 beats LLMs." The selling point is **"evidence sufficiency is a real and consequential task; LLM judges under-detect the most consequential class under tested prompts; R4 provides targeted complementary value; all claims are bounded by silver-label limitations."**

---

## 2. Current Largest Risk

**R-1 (unchanged from V3.4): Lack of independent gold adjudication.**

All 444 SimClaim labels are silver (AI-preannotated, author-screened). The author sanity audit flags 25/40 (62.5%) as questionable or unclear, with strong_action_overclaim having a 75% confusion rate. The LLM under-detection finding is computed against these silver labels — if the silver labels themselves systematically mis-label strong_action_overclaim, the under-detection pattern could be partly a label-noise artifact. The consistency across GPT, DeepSeek, and the structured prompt does not rule this out — consistency could reflect shared LLM bias or shared silver-label bias.

**Impact on the central claim:** If gold adjudication reveals that the mild/strong boundary is not reliably drawable (κ < 0.4 on this boundary), the strong_action_overclaim class itself may need to be merged with mild, which would weaken the paper's central contribution. The decision tree (Figure 2) is a starting operationalization, but it is not validated against gold.

**What is needed:** Independent two-annotator adjudication of 300-500 pairs, with inter-annotator agreement reported *separately for each boundary* (mild_vs_strong, strong_vs_contradiction, supported_vs_mild). The 25 cases in `high_risk_sample_bank.csv` are the priority cases for this adjudication.

**Secondary risks (in order):**

- R-2: Mild/strong boundary is the central annotation challenge (12/25 questionable/unclear cases; 75% confusion on strong_action).
- R-3: Decision tree is not validated against gold (new risk in V3.4).
- R-4: Trusted case bank (18 cases) is not gold — "reasonable" by author audit ≠ "correct" by independent adjudication.
- R-5: Claim generation may introduce bias (5/25 claim_too_abstract).
- R-7: Small dataset (444 pairs, ~16 test per seed), single-run LLM with no variance estimate, GPT via third-party proxy.

---

## 3. Current Venue Type

V3.5 is suitable as a **Q2/Q3-tier diagnostic paper雏形 (paper draft)**, more defensible than V3.4 because:

- The 25 questionable/unclear audit cases now have *identifiable root causes* (not a black box).
- The taxonomy is now *operationalizable* via a 4-step decision tree (Figure 2).
- The paper *does not hide* the 25/40 rate — it reports, diagnoses, and discloses it.
- Trusted illustrative cases are separated from high-risk boundary cases.
- The presentation is now readable: tight abstract, compressed introduction, 3 figures, 3 clean tables, structured appendix, conservative limitations.

**Suitable venue types:**

- Workshop on NLP evaluation, scientific claim verification, or LLM-as-judge (e.g., ACL/EMNAACL workshops).
- Q3-tier conference with diagnostic / pilot-study track.
- Findings track (ACL/EMNAACL Findings) — *if* the silver-label limitations are framed carefully and the contribution is positioned as a falsifiable framework rather than a benchmark.

**NOT yet suitable for:**

- Q1 main conference (ACL/EMNAACP/NAACL main conference) — requires independent gold adjudication.
- TACL / Computational Linguistics — requires gold validation and significance tests.
- NeurIPS / ICLR main track — wrong venue type (this is an NLP evaluation paper, not a ML methods paper).

---

## 4. What's Missing for Q2

For Q2-tier acceptance, the following would substantially strengthen the paper:

1. **Two-annotator pilot gold adjudication on the 25 high-risk boundary cases** (in `high_risk_sample_bank.csv`), with Cohen's κ reported separately for mild_vs_strong and strong_vs_contradiction. Even a small pilot (25 cases × 2 annotators + adjudication) would substantially strengthen the paper's credibility. If κ on mild_vs_strong is > 0.4, the taxonomy is defensible; if not, the boundary needs revision.
2. **Re-run R4 and LLM comparisons on the gold-adjudicated subset** (even 25-50 cases), to verify that the LLM under-detection pattern holds under gold labels.
3. **Paired bootstrap significance tests** for the R4-vs-LLM strong_F1 gap on matched samples (currently single-run, no variance estimate).
4. **A second structured prompt design** (different from the 5-step decomposition) to test whether the under-detection pattern is prompt-specific or model-specific.
5. **Open-source LLM replication** (e.g., Llama-3-70B or Mistral-Large) to verify the pattern is not specific to GPT/DeepSeek.

Items 1-2 are the most consequential. Items 3-5 are desirable but not strictly required for Q2.

---

## 5. What's Missing for Q1

For Q1-tier acceptance, all of the Q2 items plus:

1. **Independent gold adjudication of 300-500 pairs** with κ/α reported separately for each boundary (mild_vs_strong, strong_vs_contradiction, supported_vs_mild). The full 25-case high-risk set is the priority; the remaining cases should be sampled to cover all six domains.
2. **Validate the decision tree (Figure 2) against gold labels.** If the decision tree's labels match gold labels on >80% of cases, it is a useful aid; if not, it needs revision.
3. **Case study on gold subset** (10-20 cases where LLM disagrees with gold) — qualitative analysis of why LLMs under-detect strong_action.
4. **Prompt robustness sweep** — at least 3 prompt designs × 2 models, to verify the under-detection pattern is robust across prompts.
5. **Few-shot and chain-of-thought LLM baselines** — to test whether prompt engineering can fix the under-detection pattern (the V3.5 structured 5-step decomposition is a single design; other decompositions are untested).
6. **External validation of the four-class taxonomy** — public datasets cannot test action-overclaim, so a new annotated subset of a public scientific claim dataset (e.g., SciFact extension with action-overclaim labels) would be needed.
7. **Significance tests** for all comparisons (paired bootstrap or permutation tests).

Items 1-2 are Q1-blocking. Items 3-7 are Q1-strengthening.

---

## 6. Should We Continue New Algorithm Work?

**No. Continuing new algorithm work is NOT recommended at this stage.**

Rationale:

1. **The current bottleneck is not algorithmic.** R4's strong_F1 = 0.3967 on silver labels is the frozen main method; the cost-sensitive variant (cw4.0) gives only +0.0254 (below the +0.03 threshold). Further algorithm tuning will produce marginal gains on silver labels that may not hold under gold.

2. **The current bottleneck is data quality.** The author sanity audit flags 62.5% of silver labels as questionable or unclear. Until gold adjudication is done, any algorithm improvement on silver is potentially optimizing against noisy labels.

3. **The current bottleneck is presentation.** V3.5 is the first version that is genuinely readable (tight abstract, compressed introduction, 3 figures, 3 clean tables, structured appendix). The next priority should be **getting V3.5 in front of advisors / co-authors / reviewers** for feedback, not tuning R5/R6.

4. **The current bottleneck is validation.** The LLM under-detection finding is single-run, silver-vs-silver, prompt-specific. Until it is validated on gold with multiple prompts and models, it remains a *hypothesis*, not a *finding*. No amount of algorithm work will change this.

**Recommended priority order:**

1. **Writing / figures / gold-postponed** (immediate): finalize V3.5 with advisors, get feedback on the presentation, and prepare a gold-adjudication plan (small pilot on the 25 high-risk cases).
2. **Gold adjudication** (next): two-annotator pilot on the 25 high-risk cases, with κ reported per boundary.
3. **Re-run R4 + LLM on gold subset** (after gold): verify the under-detection pattern holds under gold.
4. **Prompt robustness sweep** (parallel): test 2-3 additional prompt designs on the same 100 samples.
5. **New algorithms** (only if 1-4 are done and the pattern holds): R5/R6 variants, cost-sensitive extensions, ordinal regression. But this is the *last* priority, not the first.

**Explicit answer:** Do NOT continue new algorithm work. Prioritize writing / figures / gold-postponed. The framework is falsifiable and the main method is frozen — the next step is validation, not optimization.

---

## 7. Honest Bottom Line

V3.5 is the most readable and most defensible version so far. It is suitable for sharing with advisors and submitting to Q2/Q3-tier venues or workshops. It is **not** Q1-ready.

The largest risk is unchanged: lack of independent gold adjudication. Until this is resolved, the LLM under-detection finding must be framed as *diagnostic evidence against silver labels, pending independent gold adjudication* — not as an established property of LLM judges.

The strongest contribution is the falsifiable framework: a four-class taxonomy with an operational decision tree, a frozen R4 main method with targeted strong_action value, and a matched-sample LLM comparison showing a consistent under-detection pattern under tested prompts. This contribution holds even if individual silver labels shift under gold — the *pattern* may persist, but this is not guaranteed.

**Recommended next steps:**

1. Share V3.5 with advisors for feedback on presentation and framing.
2. Plan a small gold-adjudication pilot (25 high-risk cases, 2 annotators + adjudication).
3. Do NOT run new algorithms or APIs until gold pilot is complete.
4. Prepare a Q2-tier submission target (workshop or Findings track) for after advisor feedback.
