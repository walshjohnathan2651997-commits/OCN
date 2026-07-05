# Appendix: Case Studies (V3.6 — Integrity Checked)

**Purpose:** Provide concrete examples that make the four-class taxonomy and its hardest boundaries visible to readers. Cases are drawn from `trusted_case_bank.csv` (trusted) and `high_risk_sample_bank.csv` (boundary). Boundary cases are used to illustrate task difficulty, not to support strong claims.

**V3.6 changes from V3.5:**

- **T2 (mild) replaced.** V3.5 T2 was SBV2-ALL92-G214-C02 (claim said "above 30% accuracy" vs evidence "24.5% accuracy" — number inflation that a reviewer would judge as contradiction, not mild). V3.6 T2 is SBV2-ALL92-G170-C02 (claim adds "multi-stage" scope adjective; numbers match exactly; clean mild scope over-extension).
- **B4 placeholder replaced.** V3.5 B4 was a "representative placeholder" with no real candidate_id. V3.6 B4 is HRC_001 = SBV2-ALL92-G003-STRONG (real candidate_id, real evidence, real claim, real root_cause: claim_too_abstract).
- All 8 cases now have traceable candidate_ids in `strict_silver_max_candidates_v1.csv`.

**Important:** None of these cases are claimed as gold. They are silver-label illustrations. "Trusted" means author sanity audit rated "reasonable" or evidence/claim clarity is high — not that the label is independently adjudicated.

---

## Part 1: Trusted Cases (4 cases, one per class)

### Case T1 — supported

- **case_id:** TCB_004
- **candidate_id:** SBV2-ALL92-G067-C01
- **domain:** cyber_defense
- **silver label:** supported
- **evidence:** "We evaluate six frontier AI systems under matched prompts and budgets."
- **claim:** "The AgentCyberRange study evaluates six frontier AI systems under matched prompts and matched computational budgets for the reported cyber-range comparison."
- **why this case is used:** Establishes the baseline: when a claim's strength matches the evidence, the label is `supported`. `supported` does not mean "absolutely true" — it means the evidence is sufficient for the claim's stated strength. The decision tree (Figure 2) routes this case: Step 1 (no directional conflict) → Step 2 (no action/deployment cue) → Step 4 (no scope over-extension) → `supported`.
- **why not gold:** Silver label (AI-preannotated, author-screened). Author sanity audit rated "reasonable" but no independent adjudication. Even this clean case could shift under gold if an annotator disagrees that the claim's "matched computational budgets" framing exactly matches the evidence's "matched prompts and budgets."
- **how the paper handles it:** Used as a clear illustrative case in Table 2 and as Case T1 in this appendix. The paper explicitly states that all silver labels are exploratory and pending independent gold adjudication.

### Case T2 — mild_scope_overclaim (V3.6 REPLACED)

- **case_id:** TCB_NEW_MILD_2
- **candidate_id:** SBV2-ALL92-G170-C02
- **domain:** robotics
- **silver label:** mild_scope_overclaim
- **evidence:** "In multi-task generalization experiments, our method achieves a success rate of 83% on trained tasks and 75% on unseen tasks in simulation."
- **claim:** "In simulation, GRaD-Nav++ reports success rates of 83% on trained tasks and 75% on unseen multi-stage tasks during evaluation."
- **why this case is used:** Canonical `mild_scope_overclaim` pattern: the claim adds a scope adjective ("multi-stage") to "unseen tasks" that is not in the evidence. The numbers match exactly (83% / 75%), so there is no directional conflict and no number swap — the over-extension is purely a scope/precision expansion without action consequences. This is the cleanest mild case in the trusted case bank. The decision tree (Figure 2) routes: Step 1 (no directional conflict — numbers match) → Step 2 (no action/deployment cue) → Step 4 (scope over-extension: "multi-stage" added) → `mild_scope_overclaim`.
- **why not gold:** Silver label. Author sanity audit did not directly audit this case, but the pattern (scope adjective added, numbers preserved) is the textbook mild pattern. An independent annotator might still judge "multi-stage" as a harmless paraphrase rather than a scope over-extension, which would shift the label to `supported`.
- **how the paper handles it:** Used as a clear illustrative case in Table 2 and as Case T2 in this appendix. The paper explicitly states that the supported/mild boundary is the weakest boundary in the taxonomy (mild-F1 = 0.1266) and is treated as an open problem.

### Case T3 — strong_action_overclaim

- **case_id:** TCB_012
- **candidate_id:** SBV2-ALL92-G107-C03
- **domain:** digital_twin
- **silver label:** strong_action_overclaim
- **evidence:** "This dual-component approach provably converges to the optimal policy, and outperforms existing methods in extensive numerical experiments based on the biopharmaceutical manufacturing domain."
- **claim:** "The approach jointly calibrates the digital twin and searches for an optimal control rule, outperforming existing methods in numerical biopharmaceutical experiments and direct physical plant trials."
- **why this case is used:** This is the canonical `strong_action_overclaim` pattern: the claim's direction is consistent with the evidence (both describe outperforming existing methods), but the claim's *strength* (operational deployment in "direct physical plant trials") exceeds what the evidence (numerical experiments only) warrants. `strong_action_overclaim` does NOT require directional conflict — it requires action/strength escalation beyond evidence. The decision tree (Figure 2) routes: Step 1 (no directional conflict) → Step 2 (action/deployment cue present — "direct physical plant trials" is operational deployment language) → Step 3 (evidence limited to numerical experiments; claim asserts physical plant trials) → `strong_action_overclaim`. This is one of the clearest strong_action cases in the trusted case bank.
- **why not gold:** Silver label. Author sanity audit rated "reasonable" but no independent adjudication. An independent annotator might judge "direct physical plant trials" as a clear operational escalation (strong_action) OR as a fabricated claim that the evidence contradicts (contradiction). The decision tree (Figure 2, Step 1) treats this as no directional conflict because both claim and evidence describe "outperforming existing methods" — but a stricter annotator could disagree.
- **how the paper handles it:** Used as a clear illustrative case in Table 2 and as Case T3 in this appendix. The paper explicitly states that the strong_action numeric results (R4 strong-F1 = 0.3967, LLM strong-F1 = 0.0769) should be read as diagnostic evidence on a hard boundary, not as stable benchmark numbers.

### Case T4 — contradiction_candidate

- **case_id:** TCB_018
- **candidate_id:** SBV2-ALL92-G036-C04
- **domain:** autonomous_driving
- **silver label:** contradiction_candidate
- **evidence:** "As widely discussed in the community [42, 43], the lack of an official training set makes the comparisons of different methods in the system-level instead of the algorithm-level. Bench2Drive deal with these shortcomings by offering a large-scale, annotation-rich official training dataset alongside a multi-ability evaluation set."
- **claim:** "Bench2Drive describes official training data as already available, making method comparisons operate at algorithm level rather than system level."
- **why this case is used:** This is the canonical `contradiction_candidate` pattern: directional conflict on the same fact. The claim says training data is "already available" while the evidence describes "the lack of an official training set" as the prior state that Bench2Drive addresses. The decision tree (Figure 2) routes: Step 1 (directional conflict on data availability) → `contradiction_candidate`. No need to check Steps 2-4 — once a directional conflict is identified, the label is contradiction. Note that the audit's initial heuristic missed this kind of detail-swapping contradiction (it looked for explicit "however" / "but" language). The V3.4 decision tree (Figure 2, Step 1) now operationalizes detail-swapping as contradiction.
- **why not gold:** Silver label. Author sanity audit rated all 6 contradiction_candidate cases as "unclear" (75% confusion on the strong_vs_contradiction boundary), but this case is one of the clearest in the high-risk set because the directional conflict is on a single factual claim (data availability). An independent annotator might still judge this as `supported` if they read the evidence's "Bench2Drive deal with these shortcomings" as confirming the claim's framing — but the silver annotation judged the claim as contradicting the *prior state* described in the evidence.
- **how the paper handles it:** Used as a clear illustrative case in Table 2 and as Case T4 in this appendix. The paper explicitly states that 6/25 questionable/unclear audit cases are strong_vs_contradiction boundary cases and that the decision tree now operationalizes detail-swapping as contradiction.

---

## Part 2: Boundary Cases (4 cases — all REAL, used to illustrate task difficulty, NOT to support strong claims)

> **Important:** Boundary cases are NOT used to support strong claims in the paper. They are reported to illustrate where the taxonomy is hardest and where future gold adjudication should prioritize. All 4 boundary cases below are real candidates from `strict_silver_max_candidates_v1.csv`, with traceable candidate_ids, real evidence, and real claims. The 25 questionable/unclear cases in `high_risk_sample_bank.csv` are the full set of boundary cases for future gold adjudication priority; the 4 below are representative examples.

### Case B1 — Mild vs. Strong boundary

- **case_id:** HRC_004
- **candidate_id:** SBV2-ALL92-G069-C03
- **domain:** cyber_defense
- **silver label:** strong_action_overclaim
- **audit decision:** unclear (mild_vs_strong confusion)
- **root cause:** mild_vs_strong_boundary_unclear
- **evidence:** "However, systematic evaluation of their offensive capabilities remains constrained by limited access to open, reproducible, multi-host cyber-range infrastructure."
- **claim:** "Systematic evaluation of offensive capabilities remains constrained by missing open, reproducible, multi-host cyber-range infrastructure for frontier systems for reproducible multi-host cyber-range experiments."
- **why this case is used:** The claim has no explicit action/deployment/safety cue — it describes a constraint, not an action. The decision tree (Figure 2) Step 2 would route this to Step 4 (mild/supported), but the silver label is strong_action. The mild-vs-strong boundary is genuinely unclear here because the claim's "for frontier systems" and repeated "for reproducible multi-host cyber-range experiments" could be read as scope expansion (mild) OR as operational framing (strong). This is the hardest boundary in the taxonomy (12/25 questionable/unclear audit cases are mild_vs_strong).
- **why not gold:** Silver label; audit flagged as unclear. The decision tree operationalizes the boundary, but cases without explicit action cues remain ambiguous. Future gold annotation must invest disproportionate effort here.
- **how the paper handles it:** Retained in `high_risk_sample_bank.csv` as a boundary case for future gold adjudication priority. NOT used as a trusted illustrative case. The paper explicitly discloses that 12/25 questionable/unclear cases are mild_vs_strong boundary cases and that the strong_action numeric results should be read as diagnostic evidence on a hard boundary, not as stable benchmark numbers.

### Case B2 — Strong vs. Contradiction boundary

- **case_id:** HRC_020
- **candidate_id:** SBV2-ALL92-G002-CONTRA
- **domain:** autonomous_driving
- **silver label:** contradiction_candidate
- **audit decision:** unclear (strong_vs_contradiction confusion)
- **root cause:** audit_conservative_plus_taxonomy_boundary (audit heuristic missed detail-swap)
- **evidence:** "Moreover, we extend the benchmark with two complementary metrics, Success Rate (SR) and All-Core Pass Rate (PR), to assess a planner's robustness and overall performance balance across multiple dimensions."
- **claim:** "nuPlan-R adds Lane Distance and Map Coverage Rate metrics to assess planner routing geometry and map exploration balance over multiple dimensions."
- **why this case is used:** The claim swaps the metric names (Lane Distance / Map Coverage Rate vs Success Rate / All-Core Pass Rate) and the assessment target (routing geometry / map exploration vs robustness / performance balance). This is genuine contradiction by detail-swap (entity/metric name substitution), but the audit heuristic looked for explicit "contradicts" language and missed the pattern. The V3.4 decision tree (Figure 2, Step 1) now operationalizes detail-swapping as contradiction, which should reduce this confusion in future annotation. The boundary between "swapping metric names" (contradiction) and "inflating the strength of a result" (strong_action) remains genuinely hard.
- **why not gold:** Silver label; audit flagged as unclear. Even with the decision tree, an independent annotator might judge this as `strong_action` if they read the metric-name swap as a strength inflation rather than a factual contradiction. The audit heuristic was too conservative (looked for explicit contradiction language); the decision tree is more operational but still requires human judgment.
- **how the paper handles it:** Retained in `high_risk_sample_bank.csv` as a boundary case. The paper explicitly discloses that 6/25 questionable/unclear cases are strong_vs_contradiction boundary cases and that the decision tree now operationalizes detail-swapping as contradiction.

### Case B3 — Supported vs. Mild boundary (evidence-context-missing)

- **case_id:** HRC_016
- **candidate_id:** SBV2-ALL92-G067-C02
- **domain:** cyber_defense
- **silver label:** mild_scope_overclaim
- **audit decision:** unclear (evidence_context_missing)
- **root cause:** evidence_context_missing
- **evidence:** "We evaluate six frontier AI systems under matched prompts and budgets."
- **claim:** "The AgentCyberRange study evaluates six frontier AI systems under matched prompts, budgets, and environment configurations for the reported cyber-range comparison."
- **why this case is used:** The evidence is short (11 words) and the claim adds "and environment configurations" and "for the reported cyber-range comparison" — scope/precision expansion that may or may not be supported by the truncated evidence. The boundary between supported and mild is genuinely fuzzy when the evidence excerpt is short and the scope expansion is minor. The supported/mild boundary is the weakest boundary in the taxonomy (supported-F1 = 0.4424, mild-F1 = 0.1266). The decision tree (Figure 2, Step 4) operationalizes it, but minor scope expansions on short evidence remain genuinely hard.
- **why not gold:** Silver label; audit flagged as unclear with root_cause `evidence_context_missing`. The decision tree cannot compensate for missing context — even a perfect annotator cannot reliably label a case where the evidence excerpt is truncated. An independent annotator with access to the full paper might judge "environment configurations" as implied by the evidence (supported) or as a scope expansion (mild).
- **how the paper handles it:** Retained in `high_risk_sample_bank.csv`. The paper explicitly discloses that the supported/mild boundary remains weak (mild-F1 = 0.1266) and is treated as an open problem, not a solved subtask. Future data collection should ensure evidence excerpts are complete enough for annotation.

### Case B4 — Claim too abstract (V3.6 REPLACED placeholder with real case)

- **case_id:** HRC_001
- **candidate_id:** SBV2-ALL92-G003-STRONG
- **domain:** autonomous_driving
- **silver label:** strong_action_overclaim
- **audit decision:** unclear (claim_too_abstract)
- **root cause:** claim_too_abstract
- **evidence:** "To address these limitations, we present nuPlan-R, a new reactive closed-loop planning benchmark that integrates learning-based reactive multi-agent simulation into the nuPlan framework."
- **claim:** "nuPlan-R presents a reactive closed-loop planning benchmark that integrates learning-based reactive multi-agent simulation into nuPlan and validates planner behavior."
- **why this case is used:** The claim adds "validates planner behavior" — but this is a description of what the paper does, not an explicit action/deployment/safety assertion. The decision tree (Figure 2) Step 2 would look for an action/deployment cue ("validates" could be read as operational, but it is weak). The silver label is strong_action_overclaim, but a reviewer could argue this is `supported` (the paper does validate planner behavior as part of presenting a benchmark) or `mild_scope_overclaim` (the claim adds a scope detail not in the evidence). This is a `claim_too_abstract` boundary case — 5/25 questionable/unclear audit cases are of this type. It is a *claim generation* issue (the claim describes what the paper does without explicit action language) rather than a *taxonomy* issue, but it affects label quality.
- **why not gold:** Silver label; audit flagged as unclear with root_cause `claim_too_abstract`. This is a data quality issue (claim generation sometimes produces claims too abstract to clearly map to the taxonomy), not a taxonomy issue. Future claim generation should produce claims with clearer action/deployment/safety cues when the silver label is strong_action.
- **how the paper handles it:** Retained in `high_risk_sample_bank.csv` as a boundary case. The paper explicitly discloses that 5/25 questionable/unclear cases are `claim_too_abstract` — a claim generation issue that affects label quality but does not invalidate the taxonomy. Future data collection should ensure claims with strong_action silver labels contain explicit action/deployment/safety cues.

---

## Summary

| Case | Type | Class | candidate_id | Used for |
| --- | --- | --- | --- | --- |
| T1 (TCB_004) | Trusted | supported | SBV2-ALL92-G067-C01 | Clear illustrative case |
| T2 (TCB_NEW_MILD_2) | Trusted | mild_scope_overclaim | SBV2-ALL92-G170-C02 | Clear illustrative case — clean scope expansion (V3.6 replaced V3.5 TCB_008) |
| T3 (TCB_012) | Trusted | strong_action_overclaim | SBV2-ALL92-G107-C03 | Clear illustrative case — canonical action escalation |
| T4 (TCB_018) | Trusted | contradiction_candidate | SBV2-ALL92-G036-C04 | Clear illustrative case — canonical directional conflict |
| B1 (HRC_004) | Boundary | strong_action (silver) | SBV2-ALL92-G069-C03 | Mild-vs-strong boundary difficulty |
| B2 (HRC_020) | Boundary | contradiction (silver) | SBV2-ALL92-G002-CONTRA | Strong-vs-contradiction boundary difficulty |
| B3 (HRC_016) | Boundary | mild (silver) | SBV2-ALL92-G067-C02 | Supported-vs-mild / evidence-context-missing boundary |
| B4 (HRC_001) | Boundary | strong_action (silver) | SBV2-ALL92-G003-STRONG | Claim-too-abstract boundary (V3.6 replaced placeholder) |

**Total: 8 cases (4 trusted + 4 boundary). All 8 have traceable candidate_ids in `strict_silver_max_candidates_v1.csv`.**

None of these cases are claimed as gold. Trusted cases are illustrative; boundary cases are risk-disclosure. The 25 questionable/unclear cases in `high_risk_sample_bank.csv` are the full set of boundary cases for future gold adjudication priority.
