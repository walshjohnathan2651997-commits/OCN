# V3.6 Integrity Revision Log

**Date:** 2026-07-04
**Manuscript:** V3.6 — Case/Figure Integrity Checked
**Base version:** V3.5 (presentation ready)
**Stance:** Integrity pass — no new experiments, no API calls, no new data, no change to numeric results, no change to conclusions. The goal is to fix V3.5's presentation硬伤 (placeholder cases, broken figure links, controversial examples) so the paper is submittable.

---

## 1. What V3.6 Does

V3.6 is a case/figure integrity pass on V3.5. It does not:

- Run any new experiments.
- Call any APIs.
- Modify the original CSVs or frozen R4 baseline.
- Change any numeric results.
- Change the core thesis or conclusions.
- Treat silver labels as gold.
- Claim R4 outperforms LLM judges overall.

V3.6 does:

- Audit all V3.5 cases (trusted + boundary) against `strict_silver_max_candidates_v1.csv` to verify candidate_ids are real.
- Replace V3.5 T2 (TCB_008, problematic number inflation) with a clean scope-expansion case.
- Replace V3.5 B4 (placeholder with no real candidate_id) with a real high-risk case.
- Rebuild Table 2 (taxonomy examples) with 8 clean cases, all traceable to the strict_silver CSV.
- Rebuild Appendix case studies with 8 real cases (4 trusted + 4 boundary), all with traceable candidate_ids.
- Replace all `![Figure](figure_x.md)` markdown image links with inline ASCII renderings that work in docx and plain-text reviewers.
- Create renderable figure files (Figure 1/2/3) with inline ASCII + tables.

---

## 2. Case Integrity Audit Summary

Full audit in `case_integrity_audit.csv`. Summary of findings:

### 2.1 Trusted cases (TCB_001 to TCB_018)

| Severity | Count | Cases | Action |
| --- | --- | --- | --- |
| fatal_for_example | 2 | TCB_008 (mild, number inflation), TCB_013 (strong_action, 2.5x number inflation) | TCB_008 replaced in Table 2 with SBV2-ALL92-G170-C02; TCB_013 was already excluded from V3.5 Table 2 (correctly) |
| major | 2 | TCB_005 (mild, partial directional flip on sub-component), TCB_006 (mild, factual mismatch on entity description) | TCB_005 and TCB_006 NOT used in V3.6 Table 2; replaced with TCB_007 and SBV2-ALL92-G170-C02 |
| moderate | 1 | TCB_010 (strong_action, entity addition could be contradiction) | NOT used in V3.6 Table 2 |
| ok | 13 | TCB_001, TCB_002, TCB_003, TCB_004, TCB_007, TCB_009, TCB_011, TCB_012, TCB_014, TCB_015, TCB_016, TCB_017, TCB_018 | TCB_001, TCB_004, TCB_009, TCB_012, TCB_015, TCB_018 retained in V3.6 Table 2; TCB_007 promoted to V3.6 Table 2 |

### 2.2 Boundary cases (HRC_001 to HRC_025 + B4 placeholder)

| Severity | Count | Cases | Action |
| --- | --- | --- | --- |
| fatal_for_example | 1 | V3.5 B4 (placeholder, no real candidate_id) | Replaced with HRC_001 = SBV2-ALL92-G003-STRONG (real case, claim_too_abstract root_cause) |
| major | 2 | HRC_011 (same as TCB_010), HRC_019 (same as TCB_006) | NOT used in V3.6 appendix; available as boundary cases if needed |
| ok | 23 | HRC_001 to HRC_025 (excluding HRC_011 and HRC_019 which duplicate TCB_010/TCB_006 issues) | HRC_004, HRC_020, HRC_016, HRC_001 used as B1/B2/B3/B4 in V3.6 appendix |

### 2.3 T2 mild case — REPLACED

**V3.5 T2 (TCB_008 = SBV2-ALL92-G214-C02):**
- Evidence: "The best-performing system achieves only 24.5% accuracy on comprehensive scenarios and 15.04% on targeted sub-tasks."
- Claim: "The benchmark reports its best-performing system above 30% accuracy on broad cases and 15.04% accuracy on targeted sub-tasks."
- **Problem:** Number inflation on the same metric (24.5% → above 30%). A reviewer would judge this as contradiction (detail-swap), not mild.
- **Severity:** fatal_for_example

**V3.6 T2 (TCB_NEW_MILD_2 = SBV2-ALL92-G170-C02):**
- Evidence: "In multi-task generalization experiments, our method achieves a success rate of 83% on trained tasks and 75% on unseen tasks in simulation."
- Claim: "In simulation, GRaD-Nav++ reports success rates of 83% on trained tasks and 75% on unseen multi-stage tasks during evaluation."
- **Why clean:** Numbers match exactly (83% / 75%); the only difference is the scope adjective "multi-stage" added to "unseen tasks". This is a textbook mild scope over-extension — no directional conflict, no number swap.

### 2.4 B4 placeholder — REPLACED

**V3.5 B4:** "(representative; the SimClaim silver set has several cases where evidence excerpts are truncated)" — no real candidate_id, no real evidence, no real claim.

**V3.6 B4 (HRC_001 = SBV2-ALL92-G003-STRONG):**
- Evidence: "To address these limitations, we present nuPlan-R, a new reactive closed-loop planning benchmark that integrates learning-based reactive multi-agent simulation into the nuPlan framework."
- Claim: "nuPlan-R presents a reactive closed-loop planning benchmark that integrates learning-based reactive multi-agent simulation into nuPlan and validates planner behavior."
- Silver label: strong_action_overclaim
- Root cause: claim_too_abstract (5/25 audit cases)
- **Why this is the right replacement:** Real candidate_id, real evidence, real claim, real root_cause. The claim adds "validates planner behavior" — a description of what the paper does without explicit action/deployment/safety language. This is a `claim_too_abstract` boundary case, which is a real root_cause category in the audit (5/25 = 20% of questionable/unclear cases).

---

## 3. Figure Rendering Fix

### 3.1 V3.5 problem

V3.5 used `![Figure 1: Method Flow](figure_1_method_flow.md)` markdown image links to insert figures. These links:
- Do NOT render in docx (the docx builder ignores them).
- Do NOT render in plain-text reviewers (the link text appears but the figure content is in a separate file).
- Make the paper look unfinished when viewed in a markdown viewer that doesn't follow the link.

### 3.2 V3.6 fix

V3.6 replaces all three `![Figure](figure_x.md)` links with **inline ASCII renderings** copied directly into the paper body:

- **Figure 1 (Method Flow):** Inline ASCII flow diagram + a routing table (Route / Order / Decision / Threshold / Rationale). Renders in docx, plain text, and markdown.
- **Figure 2 (Taxonomy Decision Tree):** Inline ASCII decision tree + a four-label definition table. Renders in docx, plain text, and markdown.
- **Figure 3 (LLM vs R4 Strong Gap):** Inline ASCII bar charts (Overall Macro-F1, Strong-Action F1, Strong-Action Recall) + the data table. Renders in docx, plain text, and markdown.

The renderable figure files (`figure_1_method_flow_renderable.md`, `figure_2_taxonomy_decision_tree_renderable.md`, `figure_3_llm_vs_r4_strong_gap_renderable.md`) are also provided as standalone references, but the paper body now contains the inline versions and does NOT depend on the separate files.

---

## 4. Change Inventory (V3.5 → V3.6)

### 4.1 Main paper (`CESE_OCN_V3_6_case_figure_integrity_checked.md`)

- Version header updated (V3.5 → V3.6, change description updated).
- Figure 1 insertion block: `![Figure 1: Method Flow](figure_1_method_flow.md)` → inline ASCII flow diagram + routing table.
- Figure 2 insertion block: `![Figure 2: Taxonomy Decision Tree](figure_2_taxonomy_decision_tree.md)` → inline ASCII decision tree.
- Figure 3 insertion block: `![Figure 3: LLM vs R4 strong gap](figure_3_llm_vs_r4_strong_gap.md)` → inline ASCII bar charts (Overall Macro-F1, Strong-Action F1).
- Table 2 reference (§III.B): updated to point to `table_taxonomy_examples_v3_6_clean.csv` and note T2 replacement.
- Appendix A reference: updated to point to `appendix_case_studies_v3_6_clean.md` and note T2 + B4 replacements.

### 4.2 New files

- `case_integrity_audit.csv` — full audit of 26 cases (18 TCB + 25 HRC + B4 placeholder).
- `table_taxonomy_examples_v3_6_clean.csv` — 8 clean cases (2 per class), all traceable to strict_silver CSV.
- `appendix_case_studies_v3_6_clean.md` — 8 real cases (4 trusted + 4 boundary), all with traceable candidate_ids.
- `figure_1_method_flow_renderable.md` — inline ASCII + table version.
- `figure_2_taxonomy_decision_tree_renderable.md` — inline ASCII + table version.
- `figure_3_llm_vs_r4_strong_gap_renderable.md` — inline ASCII bar charts + table version.
- `V3_6_integrity_revision_log.md` — this file.
- `V3_6_final_readiness_note.md` — final readiness assessment.
- `CESE_OCN_V3_6_case_figure_integrity_checked.md` — main paper.
- `CESE_OCN_V3_6_case_figure_integrity_checked.docx` — Word version.

**Total: 10 files.**

---

## 5. What V3.6 Does NOT Change

- **Core thesis:** Evidence sufficiency calibration for scientific claims.
- **Core conclusion:** R4 is not a general-purpose replacement for LLM judges. It provides targeted value for strong_action_overclaim detection under the tested prompts and silver diagnostic setting.
- **Frozen R4 baseline:** `D:\ocn\experiments\mixed_framework_v2_frozen_r4_baseline` — unchanged.
- **All numeric results:** Every number in V3.6 is the same as in V3.5 and V3.4. No re-runs, no re-computations.
- **V3.5 main paper:** `CESE_OCN_V3_5_presentation_ready.md` is NOT modified. V3.6 is a sibling directory.
- **Silver label framing:** All SimClaim labels remain silver. No claim of gold/human-audited performance.
- **LLM comparison framing:** All LLM results remain single-run, temperature 0, prompt/model/sample specific.
- **Forbidden phrases:** All V3.5 forbidden phrases remain forbidden in V3.6.

---

## 6. Final Checks

| Check | Status |
| --- | --- |
| V3.5 original manuscript not modified | ✅ V3.5 directory and main paper unchanged |
| V3.6 output directory has 10 files | ✅ (see file list in §4.2) |
| All trusted cases have real candidate_id | ✅ All 4 trusted cases (TCB_004, SBV2-ALL92-G170-C02, TCB_012, TCB_018) traceable to strict_silver CSV |
| All boundary cases have real evidence/claim | ✅ All 4 boundary cases (HRC_004, HRC_020, HRC_016, HRC_001) have real candidate_ids, real evidence, real claims |
| T2 mild problem handled | ✅ TCB_008 replaced with SBV2-ALL92-G170-C02 (clean scope expansion, numbers match) |
| B4 placeholder eliminated | ✅ V3.5 placeholder replaced with HRC_001 = SBV2-ALL92-G003-STRONG (real case) |
| Figure 1/2/3 not using broken md image links | ✅ All three figures use inline ASCII renderings; no `![Figure](.md)` links in body |
| Silver not written as gold | ✅ All SimClaim labels explicitly silver |
| No claim that R4 beats LLM overall | ✅ Explicit "R4 macro-F1 substantially lower" statements throughout |
| No new experiments / API / model calls | ✅ Integrity-only revision |

---

## 7. Relationship to Prior Versions

| Version | Focus | Key change |
| --- | --- | --- |
| V3.0 | Original draft | Generic claim verification framing |
| V3.1 | Evidence sufficiency main line | Reframed around evidence sufficiency calibration |
| V3.2 | P0 repair | Added Table 0; 40-case author sanity audit; macro-F1 gap discussion |
| V3.3 | Reviewer defense | Conservative positioning |
| V3.4 | Taxonomy hardened | Operational decision tree; root cause analysis; trusted/high-risk case banks |
| V3.5 | Presentation ready | Tightened abstract; compressed introduction; 3 figures; 3 clean tables; appendix; submission snapshot |
| **V3.6** | **Case/figure integrity checked** | **Replaced problematic T2 mild case; replaced B4 placeholder with real case; rebuilt Table 2 and appendix with all-real cases; replaced broken figure md links with inline ASCII renderings. No new experiments.** |

V3.6 is the version to share with advisors / co-authors / reviewers. It fixes the硬伤 (placeholder, broken links, controversial examples) that would have made V3.5 look unfinished. It does not supersede V3.5 numerically — it presents V3.5 with cleaner cases and renderable figures.
