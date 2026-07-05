# V3.6 Final Readiness Note

**Date:** 2026-07-04
**Manuscript:** V3.6 — Case/Figure Integrity Checked
**Stance:** Honest, conservative. V3.6 fixes V3.5's presentation硬伤 (placeholder case, broken figure links, controversial example) but is **still not Q1-ready**. The largest risk remains unchanged: lack of independent gold adjudication.

---

## 1. What V3.6 Fixed vs. V3.5

V3.6 is an **integrity pass** on V3.5. It fixes three presentation硬伤 that would have made V3.5 look unfinished to a reviewer:

### Fix 1: T2 mild case replaced

- **V3.5 T2 (TCB_008 = SBV2-ALL92-G214-C02):** Claim said "above 30% accuracy on broad cases" while evidence said "24.5% accuracy on comprehensive scenarios." This is number inflation on the same metric — a reviewer would judge it as contradiction (detail-swap), not mild. The case was misleading as a "trusted mild example."
- **V3.6 T2 (SBV2-ALL92-G170-C02):** Claim adds "multi-stage" scope adjective to "unseen tasks"; numbers match exactly (83% / 75%). This is a textbook mild scope over-extension — no directional conflict, no number swap.
- **Action:** TCB_008 demoted out of Table 2 and out of the trusted appendix case; replaced with SBV2-ALL92-G170-C02. The audit (`case_integrity_audit.csv`) records this as `fatal_for_example → replace`.

### Fix 2: B4 placeholder replaced with real case

- **V3.5 B4:** "(representative; the SimClaim silver set has several cases where evidence excerpts are truncated)" — no real candidate_id, no real evidence, no real claim. This was a placeholder that violated the integrity requirement.
- **V3.6 B4 (HRC_001 = SBV2-ALL92-G003-STRONG):** Real candidate_id, real evidence, real claim, real root_cause (`claim_too_abstract`). Silver label strong_action_overclaim; audit flagged as unclear because the claim describes what the paper does without explicit action/deployment/safety language. This is a real boundary case type (5/25 = 20% of questionable/unclear audit cases).
- **Action:** B4 placeholder eliminated; replaced with HRC_001. The audit records this as `fatal_for_example → replace_with_real_case`.

### Fix 3: Figure 1/2/3 broken markdown links replaced with inline ASCII renderings

- **V3.5 figures:** Used `![Figure 1: Method Flow](figure_1_method_flow.md)` markdown image links. These do NOT render in docx (the docx builder ignores them), do NOT render in plain-text reviewers, and make the paper look unfinished in markdown viewers that don't follow the link.
- **V3.6 figures:** All three `![Figure](.md)` links replaced with **inline ASCII renderings** copied directly into the paper body:
  - Figure 1: ASCII flow diagram + routing table (Route / Order / Decision / Threshold / Rationale).
  - Figure 2: ASCII decision tree + four-label definition table.
  - Figure 3: ASCII bar charts (Overall Macro-F1, Strong-Action F1) + data table.
- **Action:** Paper body now contains the inline figures; no dependency on external image files. Standalone renderable figure files also provided for reference.

### Additional integrity work

- **Table 2 rebuilt:** 8 clean cases (2 per class), all traceable to `strict_silver_max_candidates_v1.csv`. TCB_005 and TCB_006 (both with directional-flip / factual-mismatch issues) excluded; TCB_007 (clean framing expansion) promoted.
- **Appendix rebuilt:** 8 real cases (4 trusted + 4 boundary), all with traceable candidate_ids, real evidence, real claims. Each case now includes `why not gold` (in addition to `why this case is used` and `how the paper handles it`).
- **Case integrity audit:** Full audit of 26 cases (18 TCB + 25 HRC + B4 placeholder) in `case_integrity_audit.csv`, with severity, problem_found, why_problematic, recommended_action, replacement_candidate_id, final_decision for each case.

### What V3.6 did NOT change

- No new experiments, no API calls, no new data.
- No change to numeric results (every number is the same as V3.5/V3.4).
- No change to core thesis or conclusions.
- No change to silver-label framing.
- No change to LLM comparison framing.
- V3.5 main paper NOT modified (V3.6 is a sibling directory).

---

## 2. Is V3.6 Q1-Ready?

**No. V3.6 is NOT Q1-ready.**

The largest risk is unchanged from V3.5: **lack of independent gold adjudication**. All 444 SimClaim labels are still silver (AI-preannotated, author-screened). The author sanity audit flags 25/40 (62.5%) as questionable or unclear, with strong_action_overclaim having a 75% confusion rate. The LLM under-detection finding is computed against these silver labels — if the silver labels themselves systematically mis-label strong_action_overclaim, the under-detection pattern could be partly a label-noise artifact.

V3.6 fixed presentation硬伤 but did not (and could not, without new experiments) fix the underlying data quality issue. Q1 readiness requires:

1. Independent two-annotator gold adjudication of 300-500 pairs, with κ/α reported separately for each boundary (mild_vs_strong, strong_vs_contradiction, supported_vs_mild).
2. Validation of the decision tree (Figure 2) against gold labels.
3. Re-run R4 and LLM comparisons on the gold-adjudicated subset.
4. Prompt robustness sweep (≥3 prompt designs × ≥2 models).
5. Significance tests for all comparisons.

None of these are present in V3.6. V3.6 is a presentation-ready draft, not a Q1 paper.

---

## 3. Can V3.6 Be Shared with Advisors / Co-authors?

**Yes. V3.6 is suitable for sharing with advisors and co-authors.**

V3.6 fixes the three presentation硬伤 that would have made V3.5 look unfinished:

- No more placeholder cases (B4 is now a real case).
- No more controversial "trusted" examples that a reviewer would immediately challenge (T2 is now a clean scope-expansion case).
- No more broken figure links (figures render inline in docx and plain text).

Advisors and co-authors can now read the paper without getting distracted by presentation issues, and can focus their feedback on the substance (framing, positioning, limitations, next steps).

**Recommended sharing format:** `CESE_OCN_V3_6_case_figure_integrity_checked.docx` (renders figures and tables correctly) + `appendix_case_studies_v3_6_clean.md` (for detailed case review) + `case_integrity_audit.csv` (for transparency about case selection).

---

## 4. Can V3.6 Be a Q2/Q3 Draft?

**Yes. V3.6 is suitable as a Q2/Q3-tier diagnostic paper draft**, more defensible than V3.5 because:

- All cases are now real and traceable — no placeholder, no controversial "trusted" example.
- All figures render inline — no broken links, no dependency on external image files.
- The case integrity audit (`case_integrity_audit.csv`) provides transparency about case selection, which strengthens the paper's credibility.
- The decision tree (Figure 2) is operationalizable and the appendix case studies show how it applies to real cases.

**Suitable venue types:**

- Workshop on NLP evaluation, scientific claim verification, or LLM-as-judge (e.g., ACL/EMNAACP workshops).
- Q3-tier conference with diagnostic / pilot-study track.
- Findings track (ACL/EMNAACP Findings) — *if* the silver-label limitations are framed carefully and the contribution is positioned as a falsifiable framework rather than a benchmark.

**NOT yet suitable for:**

- Q1 main conference (ACL/EMNAACP/NAACL main conference) — requires independent gold adjudication.
- TACL / Computational Linguistics — requires gold validation and significance tests.
- NeurIPS / ICLR main track — wrong venue type.

---

## 5. Largest Remaining Risk

**R-1 (unchanged from V3.5): Lack of independent gold adjudication.**

All 444 SimClaim labels are silver (AI-preannotated, author-screened). The author sanity audit flags 25/40 (62.5%) as questionable or unclear, with strong_action_overclaim having a 75% confusion rate. The LLM under-detection finding is computed against these silver labels — if the silver labels themselves systematically mis-label strong_action_overclaim, the under-detection pattern could be partly a label-noise artifact. The consistency across GPT, DeepSeek, and the structured prompt does not rule this out — consistency could reflect shared LLM bias or shared silver-label bias.

**Impact on the central claim:** If gold adjudication reveals that the mild/strong boundary is not reliably drawable (κ < 0.4 on this boundary), the strong_action_overclaim class itself may need to be merged with mild, which would weaken the paper's central contribution. The decision tree (Figure 2) is a starting operationalization, but it is not validated against gold.

**What is needed:** Independent two-annotator adjudication of 300-500 pairs, with inter-annotator agreement reported *separately for each boundary* (mild_vs_strong, strong_vs_contradiction, supported_vs_mild). The 25 cases in `high_risk_sample_bank.csv` are the priority cases for this adjudication.

**Secondary risks (in order):**

- R-2: Mild/strong boundary is the central annotation challenge (12/25 questionable/unclear cases; 75% confusion on strong_action).
- R-3: Decision tree is not validated against gold (introduced in V3.4).
- R-4: Trusted case bank (18 cases) is not gold — "reasonable" by author audit ≠ "correct" by independent adjudication.
- R-5: Claim generation may introduce bias (5/25 claim_too_abstract).
- R-7: Small dataset (444 pairs, ~16 test per seed), single-run LLM with no variance estimate, GPT via third-party proxy.

---

## 6. Should We Continue New Algorithm Work?

**No. Continuing new algorithm work is NOT recommended at this stage.**

Rationale (unchanged from V3.5):

1. **The current bottleneck is not algorithmic.** R4's strong_F1 = 0.3967 on silver labels is the frozen main method; the cost-sensitive variant (cw4.0) gives only +0.0254 (below the +0.03 threshold). Further algorithm tuning will produce marginal gains on silver labels that may not hold under gold.
2. **The current bottleneck is data quality.** The author sanity audit flags 62.5% of silver labels as questionable or unclear. Until gold adjudication is done, any algorithm improvement on silver is potentially optimizing against noisy labels.
3. **The current bottleneck is validation.** The LLM under-detection finding is single-run, silver-vs-silver, prompt-specific. Until it is validated on gold with multiple prompts and models, it remains a *hypothesis*, not a *finding*. No amount of algorithm work will change this.

**Recommended priority order:**

1. **Writing / figures / gold-postponed** (immediate): share V3.6 with advisors, get feedback, prepare a gold-adjudication plan.
2. **Gold adjudication** (next): two-annotator pilot on the 25 high-risk cases, with κ reported per boundary.
3. **Re-run R4 + LLM on gold subset** (after gold): verify the under-detection pattern holds under gold.
4. **Prompt robustness sweep** (parallel): test 2-3 additional prompt designs on the same 100 samples.
5. **New algorithms** (only if 1-4 are done and the pattern holds): R5/R6 variants, cost-sensitive extensions, ordinal regression. But this is the *last* priority, not the first.

**Explicit answer:** Do NOT continue new algorithm work. Prioritize writing / figures / gold-postponed. The framework is falsifiable and the main method is frozen — the next step is validation, not optimization.

---

## 7. Should We Do a Gold Pilot Next?

**Yes — recommended, but can be postposed.**

A small gold pilot (25-50 cases, two annotators + adjudication, with κ reported separately for the mild_vs_strong and strong_vs_contradiction boundaries) would substantially strengthen the paper's credibility. Even a small pilot would:

- Test whether the mild/strong boundary is reliably drawable (κ > 0.4 would be encouraging; κ < 0.4 would require taxonomy revision).
- Test whether the LLM under-detection pattern holds under gold labels (if it does, the central claim is strengthened; if it does not, the paper needs major revision).
- Provide inter-annotator agreement statistics that are currently missing.

**However, the gold pilot can be postposed** if the immediate goal is to get advisor/co-author feedback on the V3.6 draft. The gold pilot is the natural next step *after* advisor feedback, not before. Advisors may have different priorities (e.g., reframing, additional baselines, different venue targets) that should be addressed first.

**Recommended sequence:**

1. Share V3.6 with advisors (immediate).
2. Incorporate advisor feedback into V3.7 (next 1-2 weeks).
3. Plan and execute gold pilot on 25-50 high-risk cases (next 2-4 weeks, can run in parallel with V3.7 writing).
4. Re-run R4 + LLM on gold subset (after gold pilot).
5. Decide on Q2-tier submission target based on gold pilot results.

---

## 8. Honest Bottom Line

V3.6 is the most presentation-ready and most case-integrity-checked version so far. It fixes the three硬伤 (placeholder case, broken figure links, controversial example) that would have made V3.5 look unfinished. It is suitable for sharing with advisors and submitting to Q2/Q3-tier venues or workshops. It is **not** Q1-ready.

The largest risk is unchanged: lack of independent gold adjudication. Until this is resolved, the LLM under-detection finding must be framed as *diagnostic evidence against silver labels, pending independent gold adjudication* — not as an established property of LLM judges.

The strongest contribution is the falsifiable framework: a four-class taxonomy with an operational decision tree, a frozen R4 main method with targeted strong_action value, and a matched-sample LLM comparison showing a consistent under-detection pattern under tested prompts. This contribution holds even if individual silver labels shift under gold — the *pattern* may persist, but this is not guaranteed.

**Recommended next steps:**

1. Share V3.6 with advisors for feedback on presentation, framing, and case selection.
2. Plan a small gold-adjudication pilot (25 high-risk cases, 2 annotators + adjudication) — can be postposed until after advisor feedback.
3. Do NOT run new algorithms or APIs until gold pilot is complete.
4. Prepare a Q2-tier submission target (workshop or Findings track) for after advisor feedback and gold pilot.
