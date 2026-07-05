# V3.13 Revision Recommendation

**Task:** RIGOURATE Reproduction + SimClaim Differentiation v1 - Section 11
**Date:** 2026-07-05
**Status:** RECOMMENDATION ONLY. Does NOT modify V3.12 or V3.13. Does NOT create new paper version.

## 1. Context

V3.13 (`V3_13_differentiated_against_rigourate_forcebench`) was created as a positioning-differentiation revision against RIGOURATE / ForceBench / CLAIM-BENCH. It includes:
- New §II.A Related Work subsection with three paragraphs and Table X.
- Condensed contribution list (5 → 3 items).
- Abstract and Intro adjustments removing "first to propose" framing.
- §V.A counterfactual transparency paragraph for SimClaim.
- §VII.I gold-realism audit proposal.
- §VIII.F fine-grained typing subsection.
- §IX items 9-10 (new limitations).
- `rigourate_style_baseline_plan.md` (PLAN ONLY — no results).

The current task (RIGOURATE Reproduction + SimClaim Differentiation v1) has now produced **actual experimental results** for the RIGOURATE-style scalar baseline (Sections 4-7). The question is whether V3.13 should be revised to include these results, or whether the results should wait for V3.14.

## 2. Should we enter a new V3.13 revision (V3.13.1 / V3.14)?

**Recommendation: YES — but as V3.14, not as a V3.13 revision.**

**Rationale:**
- V3.13 is positioned as a *positioning* revision (narrative only, no new experiments, no new numbers). Revising it to include the RIGOURATE-style baseline results would change its character from "positioning revision" to "positioning + new baseline results revision", which is a different kind of contribution.
- The RIGOURATE-style baseline results are new experimental content that was not in V3.13's scope. Adding them would violate V3.13's "no new experiments" constraint.
- A V3.14 that builds on V3.13's positioning and adds the RIGOURATE-style baseline as a new results section is cleaner, more defensible, and easier to communicate to the advisor.
- V3.13 stays as the positioning-stable version; V3.14 becomes the positioning + baseline-results version.

**Naming recommendation:** `V3_14_rigourate_style_baseline_results` (or similar).

## 3. Title recommendation for V3.14

**Current V3.13 title:** "Evidence Sufficiency Calibration for Scientific Claims: A Mixed Relation-Routing Framework"

**Recommendation:** Keep the title unchanged. The title already reflects the contribution accurately. Adding "and a RIGOURATE-style Scalar Baseline Comparison" would over-specify and dilute the focus.

**Rationale:** The RIGOURATE-style baseline is a supporting experiment that strengthens the positioning, not a co-equal contribution. The title should remain focused on the framework and the four-class decomposition.

## 4. Abstract recommendation for V3.14

**Recommendation:** Add ONE sentence to the V3.13 abstract, after the existing sentence about LLM under-detection:

> "We further construct a RIGOURATE-style scalar overstatement baseline and show that, while a scalar score can identify the broad supported-vs-overclaim distinction (ROC-AUC = 0.85 when LLM-derived), it cannot reliably distinguish mild_scope_overclaim from strong_action_overclaim (ROC-AUC <= 0.59) and cannot match R4's strong_action screening F1, providing empirical support for the four-class decomposition."

**Rationale:** This is a single-sentence addition that summarises the key empirical finding from Section 5. It does not change the abstract's structure or claims; it adds one piece of empirical evidence for the taxonomy's incremental value.

**Do NOT add:**
- A claim of "we reproduce RIGOURATE" (we did not — official reproduction is blocked).
- A claim of "we beat RIGOURATE" (we did not — we built a proxy, not the official system).
- Specific FP/TP numbers in the abstract (too detailed for abstract; belongs in results).

## 5. Contribution list recommendation for V3.14

**Recommendation:** Keep the V3.13 contribution list at 3 items. Add the RIGOURATE-style baseline as a sub-bullet of contribution #2 (Diagnostic contribution), not as a new contribution.

**Revised contribution #2 (addition in bold):**

> 2. **Diagnostic contribution.** On the controlled silver-stage evaluation, we show that under the tested prompts, generic LLM judges (GPT-5.5, DeepSeek-V3) consistently under-detect strong_action_overclaim (strong-F1 = 0.0769, recall 0.04), while R4 reaches strong-F1 = 0.3000 on matched samples. **We further construct a RIGOURATE-style scalar overstatement baseline and show that scalar compression cannot reliably distinguish mild_scope_overclaim from strong_action_overclaim (ROC-AUC <= 0.59), providing empirical support for the four-class decomposition.**

**Rationale:** The RIGOURATE-style baseline is supporting evidence for the taxonomy, not a standalone contribution. It strengthens contribution #2 (Diagnostic) without inflating the contribution count.

## 6. Related Work insertion recommendation for V3.14

**Recommendation:** V3.13's §II.A Related Work subsection is sufficient. No additional Related Work insertion needed for V3.14.

**What to add instead:** A new **Section §VI.B** (or similar) titled "RIGOURATE-style Scalar Baseline Comparison" in the Results section, containing:
- The 3-baseline construction (rule_scalar, nli_scalar [blocked], llm_scalar_proxy).
- The 4-binary-task evaluation (supported_vs_overclaim, mild_vs_strong, strong_vs_contradiction, strong_vs_nonstrong).
- The 5-method comparison (rule_scalar, GPT standard, GPT structured, DeepSeek, R4).
- The case-level analysis.

**Where to insert:** After the existing §VI Results section, before §VII Gold Validation Protocol. This positions the baseline comparison as a results-section extension, not a related-work extension.

## 7. Data limitation recommendation for V3.14

**Recommendation:** Add the following to the Limitations section (§IX):

> "We constructed a RIGOURATE-style scalar overstatement proxy baseline (Section §VI.B) because the official RIGOURATE code, data, and model weights are not publicly available as of 5 July 2026 (arXiv v2 contains a placeholder URL). The proxy uses cue-based scoring and LLM-label-derived mapping; it is NOT the official RIGOURATE system and should not be interpreted as such. When the official RIGOURATE artifacts are released, the proxy comparison should be re-run against the official system to confirm the conclusions."

**Also add to Limitations:**

> "The RIGOURATE-style scalar baseline evaluation is conducted on silver labels (pre-gold) and on a 200-sample matched subset for the LLM-derived variant. Gold adjudication may shift the conclusions. The realism audit (Section §VIII) flagged 4.7% of SimClaim claims as having heuristic realism risk, with the strong_action_overclaim class at 9.0%; gold realism annotation is required to confirm that SimClaim claims are naturalistic enough to support the paper's main tables."

## 8. Can the RIGOURATE-style baseline be written as a result?

**Recommendation: YES, with explicit caveats.**

The RIGOURATE-style baseline results CAN be written as a results-section contribution in V3.14, provided that:

1. **The proxy is explicitly labelled as a proxy**, not as official RIGOURATE. Use phrases like "RIGOURATE-style scalar overstatement baseline", "cue-based scalar proxy", and "LLM-label-derived scalar proxy" throughout.
2. **The blocked status of official reproduction is explicitly stated** in the section opening and in the Limitations. The exact phrasing should be: "The official RIGOURATE code, data, and model weights are not publicly available as of [date]; we therefore construct a RIGOURATE-style proxy baseline. This proxy is NOT the official RIGOURATE system."
3. **The blocked NLI baseline (Baseline B) is reported as blocked**, with the blocked_reason, rather than being silently omitted.
4. **The 200-sample matched subset for the LLM-derived variant is clearly flagged** as a smaller-N evaluation, with the caveat that conclusions on this subset have higher variance.
5. **No claim of "we reproduce RIGOURATE" or "we beat RIGOURATE"** is made anywhere in the paper.
6. **The scalar baseline results are positioned as supporting evidence for the four-class taxonomy**, not as a standalone SOTA comparison.

## 9. How to phrase official RIGOURATE non-reproducibility

**Recommended phrasing (for the Results section opening and for Limitations):**

> "RIGOURATE [James et al., 2026] is the closest prior work to our evidence-sufficiency calibration task. We attempted an official reproduction but the RIGOURATE code, data, and model weights are not publicly available as of 5 July 2026 (the arXiv v2 paper carries a placeholder `[Github/HF Link]` URL that has not been replaced). We therefore construct a RIGOURATE-style scalar overstatement proxy baseline that captures the key design property of RIGOURATE — a single continuous overstatement score per (claim, evidence) pair — using (a) a cue-based scalar (rule_scalar_score) and (b) an LLM-label-derived scalar (llm_scalar_proxy) mapped from existing parsed LLM outputs. This proxy is NOT the official RIGOURATE system and the results should not be interpreted as a head-to-head comparison with RIGOURATE. When the official RIGOURATE artifacts are released, this comparison should be re-run."

**Forbidden phrasings:**
- "We reproduce RIGOURATE." (False — official reproduction is blocked.)
- "We compare against RIGOURATE." (Misleading — we compare against a proxy, not the official system.)
- "RIGOURATE does not release code." (Misleading — they intend to release but have not yet; the link is a placeholder, not a refusal.)
- "Our proxy is equivalent to RIGOURATE." (False — the proxy uses cue-based and LLM-label-derived scoring, not a fine-tuned multimodal model.)

## 10. Should we send to advisor?

**Recommendation: YES — send V3.14 (with RIGOURATE-style baseline results) to advisor, NOT V3.13 alone.**

**Rationale:**
- V3.13 alone is a positioning revision with no new experimental evidence. It is ready for advisor review but is weaker than V3.14.
- V3.14 (V3.13 + RIGOURATE-style baseline results) provides concrete empirical evidence that the four-class decomposition is necessary (scalar cannot distinguish mild vs. strong). This is much stronger for advisor review.
- The RIGOURATE-style baseline results directly answer the reviewer question "why not just use a scalar score?" — this is a question the advisor is likely to ask.
- The realism audit (Section 8) and gold protocol extension (Section 9) are also stronger with the V3.14 package, because they show the work has been done to pre-empt reviewer concerns about SimClaim's synthetic nature.

**Recommended advisor cover note structure:**
1. V3.13 positioning revision (already done).
2. V3.14 RIGOURATE-style baseline results (new, this task).
3. Official RIGOURATE reproduction status (blocked, with blocked_reason).
4. RIGOURATE-style proxy baseline construction (3 baselines, 1 blocked).
5. Scalar baseline evaluation (4 binary tasks, ROC-AUC results).
6. Scalar vs. R4 comparison (5 methods, strong_action F1 comparison).
7. Case analysis and realism audit.
8. Gold protocol extension proposal (two-layer: relation + realism).
9. Recommended next steps (gold collection; re-run proxy when official RIGOURATE releases).

**Do NOT send to advisor before:**
- The V3.14 paper text is written (V3.13 + new §VI.B results section + Limitations additions).
- The advisor cover note is drafted.
- A final quality check confirms all prohibitions are enforced (no proxy-as-official, no silver-as-gold, no API calls, no V3.12 modification).

## 11. Risk assessment for V3.14

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| Reviewer questions why official RIGOURATE is not reproduced | High | Medium | Explicit blocked_reason in paper; proxy clearly labelled |
| Reviewer questions proxy validity | High | Medium | Multiple proxy variants (rule + LLM); pre-registered thresholds from V3.13 plan |
| Reviewer questions SimClaim realism | Medium | High | Realism audit + gold protocol extension with realism_score |
| Reviewer questions silver-only evaluation | High | Medium | Pre-registered gold protocol; silver clearly labelled |
| Reviewer questions 200-sample LLM subset | Medium | Low | Full 444-sample rule_scalar results; LLM subset clearly flagged |
| Reviewer questions R4 macro-F1 < LLM macro-F1 | Medium | Medium | Screening-oriented positioning; explicit cost-benefit analysis in §VI.B |

## 12. Prohibitions enforced

- Does NOT modify V3.12.
- Does NOT modify V3.13.
- Does NOT create a new paper version (recommendation only).
- Does NOT create gold.
- Does NOT call paid API.
- Does NOT claim proxy as official RIGOURATE.
- Does NOT claim silver as gold.
- Does NOT claim SimClaim claims as natural claims.

## 13. File references

- V3.13 paper: `D:\ocn\paper_versions_ordered\V3_13_differentiated_against_rigourate_forcebench\CESE_OCN_V3_13_differentiated_against_rigourate_forcebench.md`
- V3.13 baseline plan: `D:\ocn\paper_versions_ordered\V3_13_differentiated_against_rigourate_forcebench\rigourate_style_baseline_plan.md`
- V3.13 realism extension: `D:\ocn\paper_versions_ordered\V3_13_differentiated_against_rigourate_forcebench\proposed_gold_realism_extension.md`
- This task's Section 5 results: `D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1\scalar_baseline_report.md`
- This task's Section 6 results: `D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1\rigourate_style_vs_r4_report.md`
- This task's Section 8 audit: `D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1\claim_realism_audit_summary.md`
- This task's Section 9 protocol: `D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1\proposed_relation_realism_gold_protocol_v2.md`
