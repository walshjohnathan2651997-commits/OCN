# V3.4 Revision Log

**Date:** 2026-07-04
**Source:** V3.3 (`D:\ocn\paper_versions_ordered\V3_3_reviewer_defense_polished\`)
**Target:** V3.4 (`D:\ocn\paper_versions_ordered\V3_4_taxonomy_hardened\`)
**Constraint:** No new experiments, no API calls, no new data, no original file modification. V3.3 untouched. No silver label changes. No `human_audited=true`, no `gold_label`, no `final_label`.

---

## 1. Goal of V3.4

V3.4 addresses the **taxonomy boundary problem** exposed by the V3.2 author sanity audit (25/40 questionable/unclear). The goal is not to "fix" the silver labels or make the audit results look better, but to:

1. Diagnose *why* the 25 cases are questionable/unclear (root cause analysis).
2. Provide an operational decision tree that reduces boundary confusion in future annotation.
3. Build a trusted case bank (clear illustrative cases) and a high-risk sample bank (boundary cases for future gold priority).
4. Revise the paper to report root causes honestly, without hiding the 25/40 rate but also without treating it as evidence of total taxonomy failure.

---

## 2. Files in V3.4 Output Directory

1. `CESE_OCN_V3_4_taxonomy_hardened.md` — main paper (83 KB)
2. `CESE_OCN_V3_4_taxonomy_hardened.docx` — Word version
3. `taxonomy_boundary_decision_tree.md` — operational 4-step decision tree
4. `sanity_audit_error_diagnosis.csv` — 25 questionable/unclear cases with root cause
5. `trusted_case_bank.csv` — 18 trusted illustrative cases (6 strong_action, 4 supported, 4 mild, 4 contradiction)
6. `high_risk_sample_bank.csv` — 25 high-risk boundary cases
7. `V3_4_revision_log.md` — this file
8. `V3_4_remaining_risks.md` — honest remaining-risk assessment

---

## 3. Root Cause Analysis of 25 Questionable/Unclear Audit Cases

**File:** `sanity_audit_error_diagnosis.csv`

The 25 questionable/unclear cases from the V3.2 author sanity audit were diagnosed into four root causes:

| Root Cause | Count | % | Description |
|---|---|---|---|
| mild_vs_strong_boundary_unclear | 12 | 48% | Claim has some scope/strength cue, but the boundary between mild_scope_overclaim and strong_action_overclaim is genuinely fuzzy. Core taxonomy challenge. |
| strong_vs_contradiction_boundary_unclear | 6 | 24% | Claim swaps specific details (numbers, metrics, entity names) relative to evidence. Audit heuristic looked for explicit "contradicts" and missed the detail-swap pattern. |
| claim_too_abstract | 5 | 20% | Claim describes what the paper does ("presents", "evaluates") without explicit action/deployment language. Silver label strong_action may be too strong, but framing still over-extends. |
| audit_heuristic_too_conservative | 2 | 8% | Audit keyword heuristic missed action/strength cues that are present but implicit. Silver label likely defensible. |

**Key insight:** Only a small fraction of the 25 cases are candidates for *likely label noise*. The majority (48% + 24% = 72%) are *genuinely hard boundary cases* that any annotation scheme would struggle with. The audit's 62.5% questionable/unclear rate is *not* evidence of systematic label failure — it is evidence that the taxonomy surfaces the cases where human judgment is most needed, and the audit deliberately oversampled strong_action (20/40 = 50% of audit sample).

---

## 4. Changes from V3.3 to V3.4

### 4.1 New §III.C Taxonomy Decision Tree (Operational)

**What changed:** Added a new §III.C "Taxonomy Decision Tree (Operational, Added in V3.4)" with a 4-step decision procedure:
- Step 1: Directional conflict? → contradiction_candidate
- Step 2: Action/deployment/safety cue present? → Step 3 or Step 4
- Step 3: Evidence sufficient for action strength? → strong_action_overclaim or re-examine
- Step 4: Scope over-extension? → mild_scope_overclaim or supported

**Key contribution:** The decision tree operationalizes the detail-swapping pattern as contradiction (Step 1), which addresses the 6 strong_vs_contradiction cases the audit heuristic missed. It also clarifies that strong_action_overclaim does *not* require directional conflict.

**Why:** V3.3 defined the taxonomy in prose but did not provide an operational procedure. Reviewers (and future annotators) need a reproducible decision procedure, not just definitions.

### 4.2 Rewritten §V.D Audit Results with Root Cause Analysis

**What changed:** The §V.D audit results now include:
- Root cause distribution (12 mild_vs_strong, 6 strong_vs_contradiction, 5 claim_too_abstract, 2 audit_heuristic_too_conservative)
- Explanation that the 25 cases are *not* all label noise
- Cross-reference to `sanity_audit_error_diagnosis.csv` (full diagnosis)
- Cross-reference to `trusted_case_bank.csv` (18 clear cases) and `high_risk_sample_bank.csv` (25 boundary cases)

**Why:** V3.2/V3.3 reported "25/40 questionable/unclear" without explaining *why*. This made the audit result look like pure bad news. V3.4 shows that the 25 cases have identifiable root causes, most of which are taxonomy boundary issues (expected for a hard task) rather than label noise.

### 4.3 New §VII.F "Boundary Cases Are Not Noise to Hide"

**What changed:** Added a new §VII.F before §VIII that:
- Argues that evidence sufficiency is *inherently a boundary task*
- Explains that the 62.5% questionable/unclear rate (on an audit that oversampled strong_action) is expected, not evidence of taxonomy failure
- States that the paper's claims must be limited to *aggregate diagnostic patterns*, not individual case correctness
- Explains that trusted cases are used for paper examples, high-risk cases for risk disclosure
- Explicitly states "The boundary cases are not noise to hide. They are the cases where evidence sufficiency calibration is hardest and most consequential."

**Why:** V3.3 did not explicitly defend against the "62.5% means the taxonomy is too subjective" attack. V3.4 provides the defense: boundary cases are expected for a boundary task, and the paper does not hide them.

### 4.4 Strengthened §VIII Limitations

**What changed:**
- Expanded limitation 2 (author sanity audit is preliminary) to cross-reference the root cause analysis and `high_risk_sample_bank.csv`.
- Added a new limitation: "The mild/strong boundary remains the central annotation challenge" — explains that 12/25 questionable/unclear cases are mild_vs_strong, strong_action has 75% confusion rate, and future gold annotation must invest disproportionate effort in this boundary.

**Why:** V3.3's limitations were honest but did not specifically identify the mild/strong boundary as the central challenge. V3.4 makes this explicit so reviewers and future annotators know where to focus.

---

## 5. New Standalone Files

### `taxonomy_boundary_decision_tree.md`
- Full 4-step decision tree with operational rules.
- ASCII flow diagram.
- Boundary case discussion (mild vs strong, strong vs contradiction).
- "What This Decision Tree Does NOT Resolve" section.
- Recommended use for future gold annotation, paper case selection, and reviewer defense.

### `sanity_audit_error_diagnosis.csv`
- 25 rows (all questionable/unclear from V3.2 audit).
- Fields: audit_id, candidate_id, silver_label, author_sanity_decision, confusion_type, root_cause, is_taxonomy_problem, is_evidence_problem, is_claim_generation_problem, is_audit_rule_too_strict, is_potentially_usable_case, recommended_action, one_sentence_reason.
- Root causes: 12 mild_vs_strong_boundary_unclear, 6 strong_vs_contradiction_boundary_unclear, 5 claim_too_abstract, 2 audit_heuristic_too_conservative.

### `trusted_case_bank.csv`
- 18 rows (6 strong_action, 4 supported, 4 mild_scope, 4 contradiction).
- Fields: case_id, candidate_id, domain, label, evidence_text_short, claim_text, why_trusted, why_not_other_labels, recommended_location_in_paper.
- Sources: Table 0 examples (8) + reasonable audit cases (4) + clear silver cases (6).
- **Not gold.** Labeled as "trusted illustrative cases" only.

### `high_risk_sample_bank.csv`
- 25 rows (all questionable/unclear from V3.2 audit).
- Fields: case_id, candidate_id, silver_label, risk_type, why_risky, possible_alternative_label, recommended_handling.
- Recommended handling: boundary_case_only, future_gold_priority, exclude_from_main_examples.
- **No samples deleted.** All 25 retained for risk disclosure.

---

## 6. Whether New Experiments Were Required

**All V3.4 changes: NO new experiments, NO API calls, NO new data.**

| Change | New experiment? | New API call? | New data? |
|---|---|---|---|
| Taxonomy decision tree | No | No | No |
| Root cause analysis of 25 audit cases | No | No | No (re-reads existing audit CSV) |
| Trusted case bank | No | No | No (reads existing silver CSV) |
| High-risk sample bank | No | No | No (re-reads existing audit CSV) |
| §III.C decision tree section | No | No | No |
| §V.D root cause rewrite | No | No | No |
| §VII.F boundary discussion | No | No | No |
| §VIII limitations strengthening | No | No | No |

V3.4 is purely taxonomy/labeling/paper polish. All numbers come from V3.3's frozen result pack.

---

## 7. What V3.4 Does NOT Do

1. **Not** modify `strict_silver_max_candidates_v1.csv` (silver set untouched).
2. **Not** delete any samples (all 25 questionable/unclear retained in high_risk_sample_bank).
3. **Not** write `human_audited=true`, `gold_label`, or `final_label` anywhere.
4. **Not** generate train/dev/test splits.
5. **Not** run models, APIs, or experiments.
6. **Not** hide the 25/40 questionable/unclear rate — it is reported, diagnosed, and disclosed.
7. **Not** claim the taxonomy is "fully solved" — the decision tree is a labeling aid, not a gold standard.
8. **Not** claim trusted case bank cases are gold — they are "trusted illustrative cases" only.
9. **Not** modify V3.3 files.

---

## 8. V3.4 vs V3.3: Defensibility Comparison

| Dimension | V3.3 | V3.4 |
|---|---|---|
| Taxonomy operationalization | Prose definitions only | 4-step decision tree + prose |
| Audit result reporting | "25/40 questionable/unclear" (number only) | Root cause distribution + diagnosis |
| Boundary case handling | Mentioned but not analyzed | Dedicated §VII.F + high_risk_sample_bank |
| Case selection for paper | Table 0 (8 cases) | Table 0 + trusted_case_bank (18 cases) |
| Mild/strong boundary | Listed as limitation | Identified as central annotation challenge |
| Reviewer defense on subjectivity | General defense | Specific defense (boundary cases are expected for boundary task) |
| Defensibility | Q2/Q3-tier雏形 | Q2/Q3-tier雏形, more defensible on taxonomy subjectivity |

**V3.4 is strictly more defensible than V3.3** on the taxonomy subjectivity attack, which was the largest remaining risk after V3.3.
