# Project Next 30 Days Plan

**Date:** 2026-07-04
**Scope:** 30-day plan from V3.11 framework to V3.12 gold-updated manuscript.
**Constraint:** No model retuning, no threshold tuning. Gold is validation only.

---

## Week 1 — V3.11 Framework + Advisor Feedback

### Goal
Send V3.11 to advisor; collect feedback on the three core questions (problem definition, taxonomy, R4 positioning).

### What to do
1. Send V3.11 main paper (.md + .docx), advisor cover note, strengthening roadmap, and reviewer risk map to advisor.
2. Schedule a 30-minute discussion meeting (or async feedback round).
3. While waiting, complete Layer 1 strengthening items that do not require advisor input:
   - L1.1 expanded example table (12 cases, 3 per class)
   - L1.4 R4 false-positive analysis (FP/TP breakdown by domain and cue)
   - L1.5 LLM strong_action error case analysis (10 missed cases with rationale)
   - L1.6 per-domain robustness summary
   - L1.8 reviewer-facing threat model table (from `reviewer_risk_to_evidence_map.csv`)
4. Prepare the 50-sample gold pilot materials (print annotation sheets, prepare the frozen protocol, train annotator B on the decision tree).

### Deliverables
- Advisor feedback summary (written notes on the 3 core questions).
- Layer 1 strengthening artifacts (5 items above).
- Annotator B trained on the decision tree and ready to label.
- `gold_pilot_candidate_50.csv` printed/blinded for annotation.

### Pass criteria
- Advisor confirms at least 2 of 3 core questions are worth pursuing.
- Layer 1 artifacts are ready to integrate into V3.11.1 if needed.
- Annotator B can apply the decision tree consistently on 5 practice cases (≥ 4/5 correct against annotator A).

### If fails
- If advisor rejects all 3 core questions: pause gold pilot; schedule a follow-up meeting to identify what is salvageable (problem formulation, dataset, method).
- If annotator B cannot apply the decision tree consistently: revise the decision tree cue lists before starting annotation; do not start gold labeling with an unreliable instrument.

---

## Week 2 — Taxonomy / Framing Revision (Based on Advisor Feedback)

### Goal
Apply advisor feedback to the taxonomy, framing, and positioning. Produce V3.11.1 (revised framework) if needed, or confirm V3.11 is ready for gold pilot.

### What to do
1. If advisor approves all 3 core questions: proceed to Week 3 preparation; V3.11 is the gold-pilot baseline.
2. If advisor requests taxonomy revision (e.g., merge strong_action into mild, or redefine boundary):
   a. Revise the decision tree (Figure 2) and boundary rules.
   b. Re-label the 50-sample gold pilot candidates under the revised taxonomy.
   c. Update §III, §VII downgrade criteria, and the reviewer risk map.
   d. Produce V3.11.1 with the revised taxonomy.
3. If advisor requests positioning revision (e.g., R4 as post-processing rule instead of screening complement):
   a. Revise §I contributions, §IV framework overview, §VIII discussion.
   b. Update the screening cost-benefit framing.
   c. Produce V3.11.1 with the revised positioning.
4. If advisor requests problem definition revision: schedule a follow-up before proceeding; this is a structural change that requires a new abstract and introduction.
5. Integrate Layer 1 artifacts (L1.1–L1.8) into the revised manuscript.

### Deliverables
- V3.11.1 (if revision needed) or V3.11 confirmed (if no revision needed).
- Updated reviewer risk map (if taxonomy or positioning changed).
- Frozen 50-sample gold pilot materials under the final taxonomy.

### Pass criteria
- Advisor confirms the revised (or confirmed) framework is ready for gold pilot.
- The 50-sample gold pilot materials are frozen under the final taxonomy.
- The decision tree is stable enough that two annotators can apply it independently.

### If fails
- If advisor and author cannot agree on the taxonomy after 2 rounds: default to the V3.11 four-class taxonomy and let the gold pilot decide (the pre-registered κ ≥ 0.40 criterion is the tiebreaker). Document the disagreement in the limitations.
- If the decision tree is still unstable after revision: delay the gold pilot by 3–5 days to stabilize the instrument; do not label with an unstable tree.

---

## Week 3 — 50 Gold Pilot

### Goal
Complete the 50-sample blind gold pilot: two annotators independently label, adjudicate disagreements, produce gold labels.

### What to do
1. Annotator A labels all 50 samples blind (silver labels hidden). Output: `pilot_50_blind_annotation_A.csv`.
2. Annotator B labels all 50 samples blind. Output: `pilot_50_blind_annotation_B.csv`.
3. Compute inter-annotator agreement: overall agreement, Cohen's κ, per-boundary κ (supported_vs_mild, mild_vs_strong, strong_vs_contradiction), unsure rate. This is Table G1.
4. Adjudicate disagreements: a third annotator (or adjudicator) resolves cases where A and B disagree. Output: `pilot_50_gold_labels.csv`.
5. Compute silver-gold consistency: silver-gold agreement, strong_action retention rate, mild-to-strong shift, strong-to-mild shift, contradiction retention rate. This is Table G2.
6. Do NOT look at model predictions during annotation or adjudication. Silver labels are hidden from annotators. Model predictions are hidden until gold labels are finalized.

### Deliverables
- `pilot_50_blind_annotation_A.csv` (annotator A raw labels)
- `pilot_50_blind_annotation_B.csv` (annotator B raw labels)
- `pilot_50_gold_labels.csv` (adjudicated gold labels)
- Table G1 (annotation agreement)
- Table G2 (silver-gold consistency)

### Pass criteria
- Overall agreement ≥ 0.70 and Cohen's κ ≥ 0.45 (H1).
- mild_vs_strong κ ≥ 0.40 (H2) — if this fails, trigger §VII.G criterion 1 (taxonomy revision).
- strong_action retention ≥ 0.60 (H3) — if this fails, trigger §VII.G criterion 2 (claim downgrade).
- If both H1 and H2 fail: the four-class taxonomy is not supported; revise to three-class before proceeding to Week 4.

### If fails
- If mild_vs_strong κ < 0.40: merge strong_action into mild_scope_overclaim; reframe the paper as a three-class framework; re-label the 50 gold samples under three-class; proceed to Week 4 with the three-class framing. The framework-level contribution survives.
- If strong_action retention < 0.50: the strong_action finding becomes a scope-overclaim finding; reframe §VI.B and §VIII accordingly; proceed to Week 4 with the revised framing.
- If overall κ < 0.45: the taxonomy is too hard for annotators; revise the decision tree and/or the cue lists; re-run a 20-sample pilot before the full 50. Delay Week 4 by 3–5 days.

---

## Week 4 — Gold Re-Score + V3.12 Gold-Updated Manuscript

### Goal
Re-score frozen R4 and LLM predictions against gold labels; produce V3.12 with gold-validated (or honestly downgraded) evidence.

### What to do
1. Re-score frozen R4 predictions against `pilot_50_gold_labels.csv`: macro-F1, strong precision/recall/F1, contradiction F1, FP/TP. This is R4's row in Table G3.
2. Re-score frozen LLM predictions (DeepSeek-V3, GPT-5.5 standard, GPT-5.5 structured) against gold. These are the LLM rows in Table G3.
3. If additional prompt variants (decision-tree, few-shot) were run: score them too. (This is optional for Week 4; can be deferred to the Q1 sprint.)
4. Compute LLM+R4 hybrid screening recall (if R4 flags + LLM judges): this tests H6 and §VII.G criterion 5.
5. Evaluate against pre-registered criteria:
   - H4: LLM strong recall remains low (≤ 0.20) → under-detection pattern survives gold.
   - H5: R4 strong recall meaningfully higher than LLM → complement value survives.
   - H6 / criterion 4: R4 FP/TP ≤ 10 on gold → screening positioning viable.
   - criterion 5: LLM+R4 hybrid improves screening recall → complementarity validated.
6. Produce V3.12 manuscript:
   - Insert gold results into Tables G1–G3.
   - Update §VI to report gold-validated numbers alongside (or instead of) silver-stage numbers, depending on results.
   - Update §VIII, §IX, §X to reflect the gold-validated (or downgraded) evidence.
   - Update the abstract and contributions to reflect the gold-validated positioning.
   - If gold supports the silver patterns: upgrade from "controlled silver-stage evidence" to "gold-validated evidence."
   - If gold does not support: apply §VII.G downgrade criteria honestly; the paper survives as a downgraded framework.

### Deliverables
- Table G3 (gold-subset model evaluation).
- V3.12 manuscript (.md + .docx): gold-updated.
- V3.12 readiness gate JSON: updated with gold results and final positioning.
- Decision memo: "gold supports / gold partially supports / gold does not support" — with the specific criteria that passed/failed.

### Pass criteria
- V3.12 is internally consistent: gold numbers in Tables G1–G3 match the text.
- If gold supports: V3.12 is ready for confirmatory study planning (Layer 3: 120–200 gold subset).
- If gold partially supports: V3.12 is honestly downgraded per §VII.G; the framework-level contribution survives.
- If gold does not support: V3.12 is restructured (e.g., three-class); the problem formulation contribution survives.

### If fails
- If R4 strong recall is not higher than LLM under gold: the complement positioning is weakened; reframe R4 as a "candidate flagging" tool rather than a "screening complement"; the framework contribution (taxonomy + benchmark) survives.
- If LLM strong recall is high under gold (because gold labels shift): the under-detection finding is downgraded to "silver-label artifact"; report this honestly; the taxonomy and benchmark contributions survive.
- If FP/TP > 10 on gold: the screening positioning is not viable; reframe R4 as a "diagnostic tool" rather than a "screening layer"; the framework contribution survives.

---

## Summary Timeline

| Week | Goal | Key Deliverable | Decision Point |
| --- | --- | --- | --- |
| 1 | V3.11 + advisor feedback | Advisor feedback summary | Proceed to Week 2 or pause |
| 2 | Taxonomy/framing revision | V3.11.1 or V3.11 confirmed | Proceed to gold pilot or revise again |
| 3 | 50 gold pilot | Tables G1, G2, gold labels | Taxonomy supported or revised |
| 4 | Gold re-score + V3.12 | Table G3, V3.12 manuscript | Gold-validated or honestly downgraded |

---

## Downgrade Survival (Cross-Week Guarantee)

The 30-day plan is designed so that **no single failure collapses the project**:

- If advisor rejects the framework (Week 1): the problem formulation and dataset survive; restructure.
- If the taxonomy fails gold (Week 3): merge to three-class; the framework and benchmark survive.
- If the silver-stage pattern fails gold (Week 4): the taxonomy and benchmark survive; the empirical claim is downgraded.
- If R4 screening fails gold (Week 4): the framework and benchmark survive; R4 is reframed as a diagnostic tool.

The only collapse scenario is simultaneous failure of (a) advisor rejection + (b) taxonomy failure + (c) pattern failure + (d) screening failure — which would require all four layers to be wrong at once. Even then, the problem formulation (evidence sufficiency calibration as a task) and the SimClaim benchmark survive as contributions.
