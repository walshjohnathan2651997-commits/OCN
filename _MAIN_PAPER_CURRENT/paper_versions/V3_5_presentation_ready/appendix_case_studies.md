# Appendix: Case Studies

**Purpose:** Provide concrete examples that make the four-class taxonomy and its hardest boundaries visible to readers. Cases are drawn from `trusted_case_bank.csv` (trusted) and `high_risk_sample_bank.csv` (boundary). Boundary cases are used to illustrate task difficulty, not to support strong claims.

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
- **issue:** None — the claim restates the evidence without over-extension.
- **why it matters:** Establishes the baseline: when a claim's strength matches the evidence, the label is `supported`. `supported` does not mean "absolutely true" — it means the evidence is sufficient for the claim's stated strength.
- **how V3.5 handles it:** Used as a clear illustrative case in Table 2 and in this appendix. The decision tree (Figure 2) routes this case: Step 1 (no directional conflict) → Step 2 (no action/deployment cue) → Step 4 (no scope over-extension) → `supported`.

### Case T2 — mild_scope_overclaim

- **case_id:** TCB_008
- **candidate_id:** SBV2-ALL92-G214-C02
- **domain:** policy_simulation
- **silver label:** mild_scope_overclaim
- **evidence:** "The best-performing system achieves only 24.5% accuracy on comprehensive scenarios and 15.04% on targeted sub-tasks, highlighting the gap between existing tools and the requirements for effective..."
- **claim:** "The benchmark reports its best-performing system above 30% accuracy on broad cases and 15.04% accuracy on targeted sub-tasks."
- **issue:** The claim inflates the broad-case accuracy (24.5% → "above 30%") but does not assert an action/deployment/safety conclusion.
- **why it matters:** Shows the canonical `mild_scope_overclaim` pattern: scope/precision over-extension without action consequences. The decision tree (Figure 2) routes: Step 1 (number conflict — but on the *same metric* this is contradiction, not mild; in this case the audit judged the inflation as scope/precision over-extension rather than directional conflict, because "broad cases" ≠ "comprehensive scenarios" exactly — a boundary nuance).
- **how V3.5 handles it:** Used as a clear illustrative case in Table 2. The decision tree's Step 1 would flag this as a potential contradiction (number inflation), but the audit judged it as mild because the categories are not strictly identical. This illustrates that the decision tree is a labeling aid, not a deterministic rule — boundary judgment is still needed. (This case is more nuanced than initially apparent; future gold adjudication should clarify whether number inflation on near-identical categories is contradiction or mild.)

### Case T3 — strong_action_overclaim

- **case_id:** TCB_012
- **candidate_id:** SBV2-ALL92-G107-C03
- **domain:** digital_twin
- **silver label:** strong_action_overclaim
- **evidence:** "This dual-component approach provably converges to the optimal policy, and outperforms existing methods in extensive numerical experiments based on the biopharmaceutical manufacturing domain."
- **claim:** "The approach jointly calibrates the digital twin and searches for an optimal control rule, outperforming existing methods in numerical biopharmaceutical experiments and direct physical plant trials."
- **issue:** The evidence mentions only numerical experiments; the claim asserts "direct physical plant trials" — an operational/deployment escalation beyond the evidence scope.
- **why it matters:** This is the canonical `strong_action_overclaim` pattern: the claim's direction is consistent with the evidence (both describe outperforming existing methods), but the claim's *strength* (operational deployment in physical plant trials) exceeds what the evidence (numerical experiments only) warrants. `strong_action_overclaim` does NOT require directional conflict — it requires action/strength escalation beyond evidence.
- **how V3.5 handles it:** Used as a clear illustrative case in Table 2 and as Case T3 in this appendix. The decision tree (Figure 2) routes: Step 1 (no directional conflict) → Step 2 (action/deployment cue present — "direct physical plant trials" is operational deployment language) → Step 3 (evidence limited to numerical experiments; claim asserts physical plant trials) → `strong_action_overclaim`. This is one of the clearest strong_action cases in the trusted case bank.

### Case T4 — contradiction_candidate

- **case_id:** TCB_018
- **candidate_id:** SBV2-ALL92-G036-C04
- **domain:** autonomous_driving
- **silver label:** contradiction_candidate
- **evidence:** "As widely discussed in the community [42, 43], the lack of an official training set makes the comparisons of different methods in the system-level instead of the algorithm-level."
- **claim:** "Bench2Drive describes official training data as already available, making method comparisons operate at algorithm level rather than system level."
- **issue:** The claim says training data is already available; the evidence says there is a lack of official training set. Directions conflict on the same fact (data availability).
- **why it matters:** This is the canonical `contradiction_candidate` pattern: directional conflict on the same fact. The decision tree (Figure 2) routes: Step 1 (directional conflict on data availability) → `contradiction_candidate`. No need to check Steps 2-4 — once a directional conflict is identified, the label is contradiction.
- **how V3.5 handles it:** Used as a clear illustrative case in Table 2 and as Case T4 in this appendix. Note that the audit's initial heuristic missed this kind of detail-swapping contradiction (it looked for explicit "however" / "but" language). The V3.4 decision tree (Figure 2, Step 1) now operationalizes detail-swapping as contradiction, which should reduce this confusion in future annotation.

---

## Part 2: Boundary Cases (4 cases — used to illustrate task difficulty, NOT to support strong claims)

> **Important:** Boundary cases are NOT used to support strong claims in the paper. They are reported to illustrate where the taxonomy is hardest and where future gold adjudication should prioritize. The 25 questionable/unclear cases in `high_risk_sample_bank.csv` are the full set of boundary cases; the 4 below are representative examples.

### Case B1 — Mild vs. Strong boundary

- **case_id:** HRC_004
- **candidate_id:** SBV2-ALL92-G069-C03
- **domain:** (strong_action silver label)
- **silver label:** strong_action_overclaim
- **audit decision:** unclear (mild_vs_strong confusion)
- **root cause:** mild_vs_strong_boundary_unclear
- **evidence:** (from SimClaim silver set; see `high_risk_sample_bank.csv` for full text)
- **claim:** (describes what the paper does, with no clear action/deployment/safety cue)
- **issue:** The claim has no explicit action/deployment/safety cue. The decision tree (Figure 2) Step 2 would route this to Step 4 (mild/supported), but the silver label is strong_action. The mild-vs-strong boundary is genuinely unclear here.
- **why it matters:** This is the hardest boundary in the taxonomy (12/25 questionable/unclear audit cases are mild_vs_strong). The decision tree operationalizes the boundary, but cases without explicit action cues remain ambiguous. Future gold annotation must invest disproportionate effort here.
- **how V3.5 handles it:** Retained in `high_risk_sample_bank.csv` as a boundary case for future gold adjudication priority. NOT used as a trusted illustrative case. The paper explicitly discloses that 12/25 questionable/unclear cases are mild_vs_strong boundary cases and that the strong_action numeric results should be read as diagnostic evidence on a hard boundary, not as stable benchmark numbers.

### Case B2 — Strong vs. Contradiction boundary

- **case_id:** HRC_020
- **candidate_id:** SBV2-ALL92-G002-CONTRA
- **domain:** autonomous_driving
- **silver label:** contradiction_candidate
- **audit decision:** unclear (strong_vs_contradiction confusion)
- **root cause:** strong_vs_contradiction_boundary_unclear (audit heuristic missed detail-swap)
- **evidence:** (describes planner metrics and benchmark characteristics)
- **claim:** (swaps specific metrics or numbers relative to evidence)
- **issue:** The claim swaps specific details (numbers, metrics, or entity names) relative to evidence. This is genuine contradiction by the V3.4 decision tree (Step 1 — detail-swapping is contradiction), but the audit heuristic looked for explicit "contradicts" language and missed the pattern.
- **why it matters:** This boundary was the source of 6/25 questionable/unclear cases in the audit. The decision tree (Figure 2, Step 1) now operationalizes detail-swapping as contradiction, which should reduce this confusion in future annotation. But the boundary between "inflating a number" (contradiction) and "inflating the strength of a result" (strong_action) remains genuinely hard.
- **how V3.5 handles it:** Retained in `high_risk_sample_bank.csv` as a boundary case. The paper explicitly discloses that 6/25 questionable/unclear cases are strong_vs_contradiction boundary cases and that the decision tree now operationalizes detail-swapping as contradiction.

### Case B3 — Supported vs. Mild boundary

- **case_id:** HRC_016
- **candidate_id:** SBV2-ALL92-G067-C02
- **domain:** (mild_scope_overclaim silver label)
- **silver label:** mild_scope_overclaim
- **audit decision:** unclear (mild_vs_strong confusion, but the supported-vs-mild distinction is also at play)
- **root cause:** mild_vs_strong_boundary_unclear (with supported-vs-mild nuance)
- **evidence:** (describes scope of an evaluation)
- **claim:** (adds a slight scope detail not in evidence)
- **issue:** The scope-expansion cue is weak — the claim adds a slight detail that may or may not be supported. The boundary between supported and mild is genuinely fuzzy when the scope expansion is minor.
- **why it matters:** The supported/mild boundary is the weakest boundary in the taxonomy (supported-F1 = 0.4424, mild-F1 = 0.1266). The decision tree (Figure 2, Step 4) operationalizes it, but minor scope expansions remain genuinely hard.
- **how V3.5 handles it:** Retained in `high_risk_sample_bank.csv`. The paper explicitly discloses that the supported/mild boundary remains weak (mild-F1 = 0.1266) and is treated as an open problem, not a solved subtask.

### Case B4 — Evidence too short / context missing

- **case_id:** (representative; the SimClaim silver set has several cases where evidence excerpts are truncated)
- **silver label:** (varies)
- **audit decision:** unclear
- **root cause:** evidence_too_short_or_context_missing (a claim generation / data extraction issue, not a taxonomy issue)
- **evidence:** (truncated excerpt — full context not available)
- **claim:** (asserts something that may or may not be supported, but the truncated evidence makes it hard to judge)
- **issue:** The decision tree cannot compensate for missing context. Even a perfect annotator cannot reliably label a case where the evidence excerpt is truncated.
- **why it matters:** This is a *data quality* issue, not a taxonomy issue. It affects label quality but does not invalidate the taxonomy. Future data collection should ensure evidence excerpts are complete enough for annotation.
- **how V3.5 handles it:** Cases with truncated evidence are flagged in `high_risk_sample_bank.csv` as `evidence_context_missing`. The paper explicitly discloses this as a data quality issue, not a taxonomy issue. Future data collection should ensure evidence excerpts are complete.

---

## Summary

| Case | Type | Class | Used for |
| --- | --- | --- | --- |
| T1 (TCB_004) | Trusted | supported | Clear illustrative case |
| T2 (TCB_008) | Trusted | mild_scope_overclaim | Clear illustrative case (with nuance) |
| T3 (TCB_012) | Trusted | strong_action_overclaim | Clear illustrative case — canonical action escalation |
| T4 (TCB_018) | Trusted | contradiction_candidate | Clear illustrative case — canonical directional conflict |
| B1 (HRC_004) | Boundary | strong_action (silver) | Mild-vs-strong boundary difficulty |
| B2 (HRC_020) | Boundary | contradiction (silver) | Strong-vs-contradiction boundary difficulty |
| B3 (HRC_016) | Boundary | mild (silver) | Supported-vs-mild boundary difficulty |
| B4 | Boundary | varies | Evidence too short / context missing |

**Total: 8 cases (4 trusted + 4 boundary).**

None of these cases are claimed as gold. Trusted cases are illustrative; boundary cases are risk-disclosure. The 25 questionable/unclear cases in `high_risk_sample_bank.csv` are the full set of boundary cases for future gold adjudication priority.
