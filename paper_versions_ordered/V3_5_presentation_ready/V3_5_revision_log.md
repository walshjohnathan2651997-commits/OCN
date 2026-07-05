# V3.5 Revision Log

**Date:** 2026-07-04
**Manuscript:** V3.5 Presentation Ready — Evidence Sufficiency Calibration
**Base version:** V3.4 (taxonomy hardened)
**Stance:** Presentation pass — no new experiments, no API calls, no new data, no change to conclusions. The goal is to make V3.4 *clearer*, not *longer*.

---

## 1. What V3.5 Does

V3.5 is a presentation-only revision of V3.4. It does not:

- Run any new experiments.
- Call any APIs.
- Modify the original CSVs or frozen R4 baseline.
- Change any numeric results.
- Change the core thesis or conclusions.
- Treat silver labels as gold.
- Claim R4 outperforms LLM judges overall.

V3.5 does:

- Tighten the abstract to ~200 words.
- Compress the introduction to six paragraphs + four contributions.
- Add three figures (Figure 1 method flow, Figure 2 taxonomy decision tree, Figure 3 LLM vs. R4 strong gap).
- Reduce the main body tables from 8+ to 3 clean tables (Table 1 internal R4, Table 2 LLM judge comparison, Table 3 boundary audit summary).
- Move detailed case material to a structured appendix (`appendix_case_studies.md`).
- Restructure the discussion into four subsections.
- Tighten the limitations to six items.
- Add a submission snapshot (`V3_5_submission_snapshot.md`).

---

## 2. Change Inventory (V3.4 → V3.5)

### 2.1 Abstract

**V3.4:** ~440 words across three paragraphs.
**V3.5:** ~189 words in a single tight paragraph. Includes: (1) problem framing, (2) task definition, (3) method (R4 mixed relation-routing), (4) key finding (LLMs higher macro-F1, R4 higher strong_action), (5) limitation (silver, prompt/model/sample-specific).

### 2.2 Introduction

**V3.4:** 8 paragraphs, including a long related-work-and-positioning preamble.
**V3.5:** 6 paragraphs following the prescribed structure: (1) support/refute insufficient, (2) evidence direction vs. evidence sufficiency for claim strength, (3) strong_action_overclaim as the core hard case, (4) LLM/NLI judges under-detect strong_action under tested prompts, (5) CESE-OCN R4 as targeted complement, (6) contributions (4 items, 1 sentence each). Related work compressed to a single §II.

### 2.3 Method (§IV)

- Added Figure 1 (method flow) insertion point with caption.
- Kept the routing-flow text but compressed the variants/ablation details (R1/R2/R3/R5, cost-sensitive cw4.0) to a single paragraph; full numbers remain in `V3_1_result_tables.csv` (referenced, not duplicated).
- Kept the "R4 is intentionally conservative" subsection but compressed.

### 2.4 Problem Definition (§III)

- Added Figure 2 (taxonomy decision tree) insertion point with caption.
- Compressed the decision tree description; full operational version remains in `taxonomy_boundary_decision_tree.md` (referenced).
- Moved Table 0 (taxonomy examples) to Table 2 in §VI (clean version in `table_taxonomy_examples_clean.csv`).

### 2.5 Results (§VI)

- Reduced from 8+ tables/subtables to 3 clean main tables:
  - **Table 1:** Internal R4 targeted result (baseline / R4 / cost-sensitive aux).
  - **Table 2:** LLM judge comparison (GPT-5.5 standard / structured / DeepSeek-V3 / R4 on matched 100 and 200).
  - **Table 3:** Boundary audit summary (40-case audit with root causes).
- Added Figure 3 (LLM vs. R4 strong gap) insertion point with caption.
- Kept the external sanity check (SciFact / VitaminC) but compressed to a single table with no ablation rows.
- Kept the explicit "R4 macro-F1 gap" discussion but compressed.

### 2.6 Discussion (§VII)

- Restructured into 4 subsections:
  1. **What R4 adds despite lower macro-F1** (2 paragraphs).
  2. **Why strong_action is difficult for LLM judges** (2 paragraphs).
  3. **Boundary cases are part of evidence sufficiency** (3 paragraphs — keeps the V3.4 boundary-case defense, which is central).
  4. **What remains unresolved** (2 paragraphs — gold adjudication, decision-tree validation, claim generation bias).

### 2.7 Limitations (§VIII)

- Reduced from 7+ items to 6:
  1. Silver labels are not gold labels.
  2. Author sanity audit is preliminary, not independent adjudication.
  3. LLM results are prompt/model/sample specific.
  4. R4 is not a general-purpose LLM judge replacement.
  5. Taxonomy boundary remains challenging.
  6. External datasets do not validate the four-class taxonomy.
- Practical limitations (small dataset, single-run LLM, GPT via proxy, etc.) kept as a brief paragraph at the end.

### 2.8 Appendix

- Added `appendix_case_studies.md` with 8 case studies (4 trusted + 4 boundary).
- Moved detailed taxonomy examples to `table_taxonomy_examples_clean.csv` (8 cases, 2 per class).
- Kept the language guardrails (safe claims, forbidden claims, cautious language) as Appendix B.

### 2.9 New files

- `figure_1_method_flow.md` — Mermaid + ASCII version of R4 routing flow.
- `figure_2_taxonomy_decision_tree.md` — Mermaid + ASCII version of the 4-step decision tree.
- `figure_3_llm_vs_r4_strong_gap.md` — Data table + ASCII bar charts of macro-F1 vs. strong_F1.
- `table_main_results_clean.csv` — Tables 1, 2, 3 in a single CSV.
- `table_taxonomy_examples_clean.csv` — 8 illustrative cases (2 per class).
- `appendix_case_studies.md` — 8 detailed case studies.
- `V3_5_submission_snapshot.md` — Submission readiness assessment.
- `V3_5_revision_log.md` — This file.
- `CESE_OCN_V3_5_presentation_ready.md` — Main paper.
- `CESE_OCN_V3_5_presentation_ready.docx` — Word version (generated from .md).

**Total: 10 files.**

---

## 3. What V3.5 Does NOT Change

- **Core thesis:** Evidence sufficiency calibration for scientific claims.
- **Core conclusion:** R4 is not a general-purpose replacement for LLM judges. It provides targeted value for strong_action_overclaim detection under the tested prompts and silver diagnostic setting.
- **Frozen R4 baseline:** `D:\ocn\experiments\mixed_framework_v2_frozen_r4_baseline` — unchanged.
- **All numeric results:** Every number in V3.5 is the same as in V3.4. No re-runs, no re-computations.
- **V3.4 main paper:** `CESE_OCN_V3_4_taxonomy_hardened.md` is NOT modified. V3.5 is a sibling directory.
- **Silver label framing:** All SimClaim labels remain silver. No claim of gold/human-audited performance.
- **LLM comparison framing:** All LLM results remain single-run, temperature 0, prompt/model/sample specific. No claim that "LLMs cannot solve strong_action_overclaim."
- **Forbidden phrases:** All V3.4 forbidden phrases remain forbidden in V3.5 (SOTA, prove, fully solved, gold benchmark, all LLMs, R4 outperforms LLM overall, systematic blind spot).

---

## 4. Final Checks

| Check | Status |
| --- | --- |
| V3.4 original manuscript not modified | ✅ V3.4 directory and main paper unchanged |
| V3.5 output directory has 10 files | ✅ (see file list in §2.9) |
| Abstract is 180-220 words | ✅ ~189 words |
| Introduction is 5-7 paragraphs | ✅ 6 paragraphs |
| Figure 1 / 2 / 3 generated | ✅ Three figure files (Mermaid + ASCII) |
| Main tables clean, not stacked with numbers | ✅ 3 main tables in `table_main_results_clean.csv` |
| Appendix case studies completed | ✅ 8 cases (4 trusted + 4 boundary) |
| Limitations conservative | ✅ 6 items, no overclaims |
| Silver not written as gold | ✅ All SimClaim labels explicitly silver |
| No claim that R4 beats LLM overall | ✅ Explicit "R4 macro-F1 substantially lower" statements throughout |
| No new experiments / API / model calls | ✅ Presentation-only revision |

---

## 5. Relationship to Prior Versions

| Version | Focus | Key change |
| --- | --- | --- |
| V3.0 | Original draft | Generic claim verification framing |
| V3.1 | Evidence sufficiency main line | Reframed around evidence sufficiency calibration; integrated GPT/DeepSeek comparison |
| V3.2 | P0 repair | Added Table 0 taxonomy examples; 40-case author sanity audit; explicit macro-F1 gap discussion; softened "blind spot" language |
| V3.3 | Reviewer defense | Added reviewer defense matrix; conservative positioning |
| V3.4 | Taxonomy hardened | Added operational decision tree; root cause analysis of 25 questionable/unclear cases; trusted case bank; high-risk sample bank; boundary-case discussion |
| **V3.5** | **Presentation ready** | **Tightened abstract; compressed introduction; added 3 figures; reduced to 3 clean main tables; added appendix case studies; added submission snapshot. No new experiments.** |

V3.5 is the version to share with advisors / co-authors / reviewers for readability. It does not supersede V3.4 numerically — it presents V3.4 more clearly.
