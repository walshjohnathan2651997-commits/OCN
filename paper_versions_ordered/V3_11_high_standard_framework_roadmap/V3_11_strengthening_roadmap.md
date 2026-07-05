# V3.11 Strengthening Roadmap

**Date:** 2026-07-04
**Scope:** Three-layer strengthening plan for the CESE-OCN evidence sufficiency calibration framework, from immediate no-data fixes to Q1-sprint validation.
**Constraint:** No new experiments, no API calls, no gold annotation in Layer 1. Layer 2 and Layer 3 require gold annotation but no model retuning and no threshold tuning.

---

## Layer 1 — Immediate Strengthening (No New Data, No Gold)

These items can be completed immediately using existing frozen artifacts. They strengthen the paper's framework-level contribution without touching any experimental number.

### L1.1 — Claim-Evidence Example Table

- **Purpose:** Make the four-class taxonomy concrete with traceable, readable examples so a reviewer can see the boundary distinctions at a glance.
- **Input:** `table_taxonomy_examples_v3_6_clean.csv`, `strict_silver_max_candidates_v1.csv`, `trusted_case_bank.csv`.
- **Output:** An expanded Table 0 with 12 examples (3 per class), each with claim text, evidence text (short), silver label, decision-tree path, and the key boundary cue. All cases traceable to candidate_id.
- **Supports:** Contribution 2 (four-class taxonomy). Defends against "the taxonomy is abstract and unclear."
- **If fails:** If trusted cases are too few to populate 3 per class, fall back to 2 per class with explicit note that the third example is a boundary case from `high_risk_sample_bank.csv`.

### L1.2 — Taxonomy Decision Tree (Already in §III.B, Strengthen with Boundary Rules)

- **Purpose:** Show the decision tree is operational, not aspirational.
- **Input:** `taxonomy_boundary_decision_tree.md`, Figure 2.
- **Output:** A supplementary table listing the cue words for each boundary (action/deployment cue list, scope-expansion cue list, detail-swapping detection rule), with 2 worked examples per boundary.
- **Supports:** Contribution 2 (taxonomy) and Contribution 4 (R4 routing rationale). Defends against "the decision tree is a flowchart with no operational rules."
- **If fails:** If a cue list is incomplete, mark it as "partial cue list, full version in `taxonomy_boundary_decision_tree.md`" — do not fabricate cues.

### L1.3 — Error Taxonomy

- **Purpose:** Show that R4 and LLM judges make *different* errors, not just different scores. This is the strongest evidence for the "complement" positioning.
- **Input:** `llm_vs_r4_100.csv`, `gpt_vs_r4_deepseek_comparison.csv`, frozen R4 predictions.
- **Output:** A table of error modes: (a) LLM over-contradiction (strong_action → contradiction), (b) LLM over-milding (strong_action → mild), (c) LLM over-supporting (strong_action → supported), (d) R4 over-routing (supported → strong, mild → strong). Counts per error mode, with 2 illustrative cases each.
- **Supports:** Contribution 5 (complementary screening signal). Defends against "R4 is just a different classifier, not a complement."
- **If fails:** If error counts are too small to be stable (e.g., <5 per mode), report raw counts with explicit "small-sample" caveat.

### L1.4 — R4 False-Positive Analysis

- **Purpose:** Quantify the screening cost (FP/TP ratio) and show it is acceptable for a high-recall screening layer.
- **Input:** Frozen R4 predictions, `frozen_r4_metrics_summary.json`, §VIII.A FP/TP estimate (~4.9).
- **Output:** A dedicated subsection or table: 98 supported→strong FP + 24 mild→strong FP = 122 FP, against ~25 true strong_action = FP/TP ≈ 4.9. Breakdown by domain and by cue type (which action cues triggered the FP).
- **Supports:** Contribution 4 (R4 as screening complement) and the §VII.G criterion 4 (FP/TP ≤ 10 on gold). Defends against "R4 is impractical."
- **If fails:** If FP/TP on silver is >10, reframe as "silver-stage FP/TP is high; the gold-subset FP/TP (Table G3) is the decisive test."

### L1.5 — LLM strong_action Error Case Analysis

- **Purpose:** Show *why* LLMs miss strong_action — not just that they miss it.
- **Input:** `llm_vs_r4_100.csv` (llm_rationale column), `gpt_vs_r4_deepseek_comparison.csv`.
- **Output:** Qualitative analysis of 10 LLM-missed strong_action cases: what the LLM said (rationale), what the silver label is, what cue the LLM missed. Group by error mode (over-contradiction, over-milding, over-supporting).
- **Supports:** Contribution 5 (LLM under-detection pattern). Defends against "the LLM numbers are just noise."
- **If fails:** If rationales are too short to analyze, report the pattern without per-case rationale, with explicit "rationale depth varies" caveat.

### L1.6 — Per-Domain / Per-Source Robustness Summary

- **Purpose:** Show the strong_action gap is not driven by a single domain.
- **Input:** Frozen R4 and LLM predictions, `strict_silver_max_candidates_v1.csv` (domain column).
- **Output:** A per-domain breakdown of strong_action-F1 for R4 vs. LLM, across the six domains (policy_simulation, marl, digital_twin, robotics, autonomous_driving, cyber_defense).
- **Supports:** Contribution 5 (pattern is cross-domain, not single-domain). Defends against "the result is driven by one easy domain."
- **If fails:** If a domain has <10 strong_action cases, report the domain but mark it as "small-sample domain, interpret with caution."

### L1.7 — Ablation and Screening-Utility Explanation

- **Purpose:** Show that NLI and action-gap features are complementary, and that the routing order is principled.
- **Input:** `frozen_r4_ablation_summary.json` (A0=0.3934, A1=0.3648, A2=0.4209).
- **Output:** A paragraph + table explaining: (a) NLI-only captures contradiction but misses action; (b) action-gap-only captures action but misses contradiction; (c) combining them improves both. The routing order is the operationalization of this complementarity.
- **Supports:** Contribution 4 (R4 design rationale). Defends against "R4 is a rule stack with no theoretical motivation."
- **If fails:** If the ablation numbers are contested, report them as "frozen ablation, not re-tuned" and point to the pre-registered gold re-score.

### L1.8 — Reviewer-Facing Threat Model

- **Purpose:** Pre-empt the strongest reviewer attacks by naming them and pointing to the evidence.
- **Input:** `reviewer_attack_report_v3_9.md` (from the V3.9 audit), this manuscript.
- **Output:** A table in the Discussion or Appendix: "Reviewer Attack → Current Evidence → Missing Evidence → Strengthening Action." (This is the `reviewer_risk_to_evidence_map.csv` produced alongside this roadmap.)
- **Supports:** All contributions. Defends against surprise reviewer attacks.
- **If fails:** If a threat has no current evidence, mark it as "Layer 2/3 strengthening required" — do not hide it.

---

## Layer 2 — Low-Cost Validation Strengthening (50-Sample Blind Gold Pilot)

These items require the 50-sample blind gold pilot specified in §VII. No model retuning, no threshold tuning, no re-fitting. Gold is used only as an independent evaluation reference.

### L2.1 — 50-Sample Blind Gold Pilot

- **Purpose:** Provide the first independent gold adjudication of the SimClaim taxonomy.
- **Input:** `gold_pilot_candidate_50.csv` (25 high-risk + 16 trusted + 9 random), `adjudication_protocol_v1.md`, frozen decision tree (Figure 2).
- **Output:** `pilot_50_blind_annotation_A.csv`, `pilot_50_blind_annotation_B.csv`, adjudicated `pilot_50_gold_labels.csv`. Two annotators independently label under the frozen protocol; disagreements adjudicated by a third annotator.
- **Supports:** Contribution 2 (taxonomy separability) and Contribution 5 (silver-stage pattern survival). Populates Tables G1–G3.
- **If fails:** If mild_vs_strong κ < 0.40, trigger §VII.G criterion 1 — revise taxonomy (merge strong_action into mild, reframe as three-class). The paper is explicitly designed to be downgradable.

### L2.2 — Silver-Gold Consistency

- **Purpose:** Determine whether the silver labels are substantially consistent with gold.
- **Input:** `pilot_50_gold_labels.csv`, original silver labels for the same 50 samples.
- **Output:** Table G2: silver-gold agreement, strong_action retention rate, mild-to-strong shift, strong-to-mild shift, contradiction retention rate.
- **Supports:** Contribution 3 (SimClaim benchmark quality) and Contribution 5 (silver-stage finding survival).
- **If fails:** If strong_action retention < 0.50, trigger §VII.G criterion 2 — downgrade the strong_action finding to a scope-overclaim finding. The paper is reframed but does not collapse.

### L2.3 — Boundary Kappa

- **Purpose:** Test the two hardest boundaries (mild_vs_strong, strong_vs_contradiction) with independent annotators.
- **Input:** `pilot_50_blind_annotation_A.csv`, `pilot_50_blind_annotation_B.csv`.
- **Output:** Table G1: overall agreement, Cohen's κ, per-boundary κ (supported_vs_mild, mild_vs_strong, strong_vs_contradiction), unsure rate.
- **Supports:** Contribution 2 (taxonomy separability is a tested hypothesis, not an assumption).
- **If fails:** If mild_vs_strong κ < 0.40, the strong_action class may need to be merged. If strong_vs_contradiction κ < 0.40, the contradiction boundary rules need revision. Both are survivable — see §VII.G.

### L2.4 — strong_action Retention Rate

- **Purpose:** Test whether silver-stage strong_action cases survive as strong_action under gold.
- **Input:** `pilot_50_gold_labels.csv`, silver strong_action labels.
- **Output:** strong_action retention rate (silver→gold), reported in Table G2.
- **Supports:** Contribution 5 (the strong_action finding is about action overclaim, not scope overclaim).
- **If fails:** If retention < 0.50, the finding becomes a scope-overclaim finding. The R4 complement positioning may still hold but the framing shifts.

### L2.5 — Re-Score Existing R4/LLM Outputs Against Gold

- **Purpose:** Determine whether the silver-stage pattern (R4 > LLM on strong_action) survives gold.
- **Input:** Frozen R4 predictions, frozen LLM predictions, `pilot_50_gold_labels.csv`.
- **Output:** Table G3: for each method (Flat baseline, NLI baseline, GPT standard, GPT decision-tree, GPT few-shot, DeepSeek, R4, LLM+R4 hybrid) — macro-F1, strong precision, strong recall, strong F1, contradiction F1, FP/TP, status.
- **Supports:** Contribution 5 (the central empirical claim). This is the decisive test.
- **If fails:** If R4 strong recall is not meaningfully higher than LLM under gold, the complement positioning is weakened. If LLM strong recall is high under gold (because gold labels shift), the under-detection finding is downgraded per §VII.G criterion 4. If GPT few-shot/decision-tree closes the gap, the finding is prompt-specific per §VII.G criterion 3.

### L2.6 — No Model Retuning, No Threshold Tuning

- **Purpose:** Ensure gold is a validation mechanism, not a tuning opportunity.
- **Input:** Frozen R4 thresholds (t_contra=0.48, t_strong=0.535, t_svm=0.51), frozen routing order.
- **Output:** A statement in §VII.B confirming that gold results do not trigger any threshold or routing change.
- **Supports:** The "protocol-locked validation" positioning.
- **If fails:** If gold reveals a threshold is catastrophically wrong, document it as a known limitation and a follow-up issue — do not silently re-tune.

---

## Layer 3 — Q1 Sprint Strengthening (120–200 Gold Subset + Cross-Domain + Multi-Prompt)

These items are for the Q1-sprint (SCI Zone 1) submission. They require a larger gold subset and additional prompt/model variants.

### L3.1 — 120–200 Gold Subset

- **Purpose:** Scale the gold validation from pilot (50) to confirmatory (120–200).
- **Input:** `gold_pilot_candidate_50.csv` + expansion to 120–200 samples, additional annotator hours.
- **Output:** Expanded Tables G1–G3 with tighter κ confidence intervals.
- **Supports:** Confirmatory benchmark claims. Moves the paper from "controlled silver-stage evidence" to "gold-validated evidence."
- **If fails:** If the 120–200 gold subset reveals the same taxonomy problems as the 50-sample pilot, the taxonomy revision from L2.1 is confirmed. The paper is restructured, not abandoned.

### L3.2 — Cross-Domain Robustness

- **Purpose:** Confirm the strong_action gap is not driven by a subset of domains.
- **Input:** 120–200 gold labels, per-domain breakdown.
- **Output:** Per-domain strong_action-F1 for R4 vs. LLM, with confidence intervals.
- **Supports:** Contribution 5 (cross-domain pattern).
- **If fails:** If the gap is driven by 1–2 domains, reframe as "domain-specific complement" rather than "universal complement."

### L3.3 — Additional LLM Prompts/Models

- **Purpose:** Test whether the under-detection pattern is prompt-specific or model-specific.
- **Input:** GPT few-shot prompt, GPT decision-tree prompt, optional open-source LLM (e.g., Llama-3).
- **Output:** Table G3 expanded with 2–3 additional prompt/model rows.
- **Supports:** Contribution 5 (the pattern is not a single-prompt artifact). Defends against "you only tested one prompt."
- **If fails:** If a prompt closes the gap, downgrade per §VII.G criterion 3. The finding becomes "under-detection under standard and structured prompts, but fixable with [X] prompt."

### L3.4 — Screening Cost-Benefit Curve

- **Purpose:** Quantify the operational trade-off: how many false positives per true positive at different R4 thresholds.
- **Input:** Frozen R4 predictions, gold labels, threshold sweep (for analysis only — the main threshold stays frozen).
- **Output:** A cost-benefit curve: FP/TP vs. strong recall, at multiple threshold values.
- **Supports:** Contribution 4 (R4 as screening complement). Moves from "FP/TP ≈ 4.9 at the frozen threshold" to "FP/TP ranges from X to Y across thresholds, with the frozen threshold at point Z."
- **If fails:** If the curve shows no acceptable operating point (FP/TP > 10 at all useful recall levels), the screening positioning is weakened.

### L3.5 — External Expert Adjudication

- **Purpose:** Strengthen the gold labels with a domain expert (not just two trained annotators).
- **Input:** 50–120 gold labels, external expert annotator.
- **Output:** Expert-adjudicated gold labels, inter-annotator agreement including the expert.
- **Supports:** Contribution 2 (taxonomy is not just author-defined).
- **If fails:** If the expert disagrees with the trained annotators on a large fraction of cases, the taxonomy boundary rules need revision.

### L3.6 — Release-Ready Benchmark Documentation

- **Purpose:** Prepare SimClaim for public release (with appropriate licensing and documentation).
- **Input:** Full SimClaim dataset, data card, annotation protocol, decision tree.
- **Output:** A release-ready data card, license, and benchmark documentation.
- **Supports:** Contribution 3 (SimClaim as a controlled diagnostic benchmark, not just an internal dataset).
- **If fails:** If licensing or privacy issues block release, document SimClaim as "available under request for research purposes" with a clear data card.

---

## Summary: Which Layer Supports Which Contribution

| Contribution | Layer 1 (immediate) | Layer 2 (50 gold) | Layer 3 (Q1 sprint) |
| --- | --- | --- | --- |
| 1. Problem formulation | L1.8 (threat model) | — | — |
| 2. Four-class taxonomy | L1.1, L1.2, L1.8 | L2.1, L2.3 | L3.1, L3.5 |
| 3. SimClaim benchmark | L1.1, L1.6 | L2.2 | L3.6 |
| 4. R4 screening framework | L1.4, L1.7 | L2.6 | L3.4 |
| 5. Silver evidence + gold validation | L1.3, L1.5, L1.6 | L2.4, L2.5 | L3.2, L3.3 |

---

## Downgrade Survival

The framework is explicitly designed to survive any Layer 2 failure:
- mild_vs_strong κ < 0.40 → merge to three-class (§VII.G criterion 1). Paper survives as a three-class framework.
- strong_action retention < 0.50 → reframe as scope-overclaim finding (§VII.G criterion 2). Paper survives.
- Prompt fixes the gap → downgrade to prompt-specific finding (§VII.G criterion 3). Paper survives.
- FP/TP too high → screening positioning weakened but framework-level contribution intact (§VII.G criterion 4).
- No hybrid gain → complementarity weakened but screening positioning may still hold (§VII.G criterion 5).

The only collapse scenario is *simultaneous* failure of criteria 1 + 2 + 4 + 5, which would require the taxonomy to be invalid, the labels to be wrong, the screening to be impractical, and the complementarity to be absent — all at once. This is the worst case, and even then the problem formulation (Contribution 1) survives.
