# Advisor Note — V3.9 Pre-Gold Complete Manuscript

**To:** Advisor
**From:** Author
**Date:** 2026-07-04
**Re:** V3.9 Pre-Gold Complete Manuscript — request for structural review before gold annotation

## Summary

I have prepared V3.9 as a **pre-gold complete manuscript**. It is a complete draft of the paper in which all sections, figures, tables, and arguments are in place, except that the gold validation numbers are not yet populated. The gold validation slots are designed as `TO_BE_FILLED_AFTER_GOLD` placeholders (Tables G1, G2, G3) so that gold results can be inserted later without restructuring the paper.

**This is not a submission-ready manuscript.** It is a draft for your structural review.

## What I Would Like You To Judge

Before I invest the time and annotator effort to do the gold pilot, I would like your judgment on **whether the paper's structure and positioning are worth continuing**. Specifically:

1. **Is the four-class taxonomy (supported / mild_scope_overclaim / strong_action_overclaim / contradiction_candidate) worth defending?** The author sanity audit flags 62.5% of audited silver labels as questionable/unclear, with strong_action_overclaim at 75% confusion. The pre-gold findings suggest the taxonomy is useful, but only gold can confirm whether the boundaries are reliably drawable.

2. **Is the "R4 as a complement to LLM judges" positioning convincing?** R4 has lower macro-F1 than LLM judges (0.3280 vs. 0.5523) but higher strong_action-F1 (0.3000 vs. 0.0769) on matched samples. The paper does not claim R4 is better overall — it claims R4 provides targeted value on the strong_action relation that LLM judges miss under the tested prompts. Is this complementary positioning worth a paper, or does the lower macro-F1 disqualify it?

3. **Is the pre-gold LLM under-detection finding worth investigating with gold?** Both GPT-5.5 (standard and structured) and DeepSeek-V3 converge on strong_action-F1 = 0.0769 (recall 0.04 = 1/25). This is computed against silver labels, so it is not yet an established property of LLM judges. Is this finding interesting enough to justify a gold pilot?

4. **Are the pre-registered success and downgrade criteria reasonable?** I have frozen six success criteria and six downgrade triggers in `gold_validation_protocol_section.md`. If gold triggers a downgrade, the paper is explicitly downgraded (e.g., merged to three classes) rather than quietly re-tuned against gold. Does this pre-registration match your expectations for a falsifiable pilot study?

5. **Is the gold subset (50 samples) appropriate?** 25 high-risk + 16 trusted + 9 random. This is a pilot — sufficient to estimate per-boundary kappa, not sufficient for confirmatory benchmark claims. Should I aim larger for the gold pilot, or is 50 appropriate for the next step?

## What V3.9 Contains

The manuscript is structured as follows (full file: `CESE_OCN_V3_9_pre_gold_complete.md`):

- §I Introduction — frames evidence sufficiency calibration as a four-class task
- §II Related Work — positions vs FEVER/SNLI/SciFact, RIGOURATE, evidence-licensed claims, LLM-as-judge surveys
- §III Task Formulation — taxonomy, decision tree (Figure 2), 8 illustrative examples (Table 0)
- §IV CESE-OCN R4 Framework — routing flow (Figure 1), three routes, frozen thresholds
- §V Data and Protocol — SimClaim 444-pair silver set, LLM judge protocol, external sanity check, author sanity audit
- §VI Results (Silver-Stage) — Tables 1-3, Figure 3, all explicitly labeled as pre-gold
- **§VII Planned Gold Validation (new in V3.9)** — why gold is needed, what it tests, what it reports, what triggers downgrade
- §VIII Discussion — what R4 adds, why strong_action is hard, boundary cases, what remains unresolved
- §IX Limitations — silver labels, preliminary audit, prompt/model/sample specificity, R4 not a replacement, taxonomy boundary, external datasets, **new: pre-gold complete draft statement**
- §X Conclusion — cautious summary, ends with "The current silver-stage evidence motivates gold validation rather than replacing it."
- Appendix A — 8 case studies
- Appendix B — language guardrails (safe claims, forbidden claims, cautious language)
- References — 34 references including recent 2025-2026 work

## What I Did NOT Do

- No gold annotation was performed.
- No `gold_label` or `final_label` values were written.
- No models were run.
- No APIs were called (no GPT, no DeepSeek).
- No training was done.
- No silver results were re-labeled as gold.
- No "submission-ready" claim was made.
- V3.8 was not deleted or modified.
- Original data was not modified.

## What I Need From You

Please review V3.9 and tell me:

- **(a) If the structure is right** — go ahead with gold annotation per the protocol in `gold_validation_protocol_section.md`.
- **(b) If the structure needs revision** — tell me what to change (taxonomy, positioning, framing) and I will revise the paper first, then do gold. I would rather redo the structure now than redo gold later.
- **(c) If the project should pivot** — if you think the four-class evidence-sufficiency framing is not the right target, tell me now. Gold annotation is a substantial investment and I do not want to make it on a structure that may still change.

I will not start gold annotation until I hear from you.

## Files For Your Review

- `D:\ocn\paper_versions_ordered\V3_9_pre_gold_complete\CESE_OCN_V3_9_pre_gold_complete.md` — main manuscript
- `D:\ocn\paper_versions_ordered\V3_9_pre_gold_complete\CESE_OCN_V3_9_pre_gold_complete.docx` — DOCX version
- `D:\ocn\paper_versions_ordered\V3_9_pre_gold_complete\gold_validation_placeholder_tables.csv` — three placeholder tables (G1, G2, G3)
- `D:\ocn\paper_versions_ordered\V3_9_pre_gold_complete\gold_validation_protocol_section.md` — pre-registered success and downgrade criteria
- `D:\ocn\paper_versions_ordered\V3_9_pre_gold_complete\pre_gold_completion_log.md` — completion log documenting all V3.8 → V3.9 changes

For reference, the V3.8 manuscript is preserved at:
- `D:\ocn\paper_versions_ordered\V3_8_reference_refreshed\CESE_OCN_V3_8_reference_refreshed.md`

The frozen gold pilot protocol (independent of V3.9) is at:
- `D:\ocn\gold_pilot_protocol_freeze_v1\` (10 files including frozen annotation guideline, decision tree, examples, boundary rules, blind templates, adjudication protocol, agreement metric plan, freeze report)

Thank you for your time.
