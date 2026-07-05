# Homogenization Risk Audit — V3.14 Mainline Locked

**Date:** 2026-07-05
**Version:** V3.14 Mainline Locked + Reviewer-Grade Consistency Audit
**Source:** §II.A, §VI.E, §VII.J, §IX of CESE_OCN_V3_14_mainline_locked.md; `D:\ocn\docs\rigourate_reproduction_and_simclaim_baseline_v1\rigourate_forcebench_claimbench_related_work_insert.md`.

This audit answers 7 reviewer-grade questions about the homogenization (同质化) risk between CESE-OCN and the three closest related works: RIGOURATE [30], ForceBench [35], and CLAIM-BENCH [28].

---

## Q1. Is CESE-OCN homogenous with RIGOURATE?

**Verdict: NOT homogenous, but the overlap is the largest among the three and must be carefully controlled.**

**Overlap (acknowledged):**
- Both study scientific claim overstatement relative to evidence.
- Both use claim-evidence pairs as the unit of analysis.
- Both target overclaim detection as the broad goal.

**Non-overlap (the differentiation):**
| Dimension | RIGOURATE | CESE-OCN |
| --- | --- | --- |
| Output | Continuous scalar overstatement score [0,1] | Four-class relation label + strong_action screening signal |
| High-risk action overclaim | Not isolated as a separate class | Isolated as `strong_action_overclaim` with a dedicated R4 escalation route |
| Claim source | Natural author-written claims (ICLR/NeurIPS abstracts + introductions) | Generated counterfactual claim variants (controlled) |
| Evidence | Full paper body (text + figures + tables), retrieved by fine-tuned reranker | Real evidence spans (extracted, not retrieved) |
| Scale | 10K+ claim-evidence sets, 872 papers | 444 pairs, 111 evidence groups, 6 domains |
| Validation | 8 LLM annotators + peer-review calibration + human evaluation | Silver (AI pre-annotation + author screening); two-layer gold protocol (PROTOCOL FROZEN, annotation NOT begun) |
| Primary question | How overstated is this claim, given retrieved evidence? | What *type* of mismatch is this, and is it a high-risk action overclaim? |

**Key control:** §VI.E provides controlled silver-stage evidence that a scalar score (RIGOURATE-style proxy) cannot reliably distinguish mild from strong_action (ROC-AUC ≤ 0.59) and cannot match R4's strong_action screening F1. This is the empirical justification for the four-class decomposition. The proxy is explicitly NOT the official RIGOURATE system (official code/data/model not publicly available as of 2026-07-05).

**Residual risk:** If the official RIGOURATE system is released and its scalar score CAN distinguish mild from strong_action (e.g., via a finer-grained regression head), the CESE-OCN differentiation weakens. Mitigation: the §VI.E result is on SimClaim (controlled counterfactual), not on RIGOURATE's natural-claim corpus; transferability is not claimed.

---

## Q2. Is CESE-OCN homogenous with ForceBench?

**Verdict: NOT homogenous. The input form and output type are structurally different.**

**Overlap:**
- Both study evidence-force / evidence-strength calibration.
- Both are interested in whether claims over-claim relative to evidence.

**Non-overlap:**
| Dimension | ForceBench | CESE-OCN |
| --- | --- | --- |
| Input form | Paired claims (calibrated vs. force-raised) on a fixed cited passage | Single claim + single evidence span |
| Output | Contrastive preference signal (monotonic preference) | Four-class relation label + screening signal |
| Force dimensions | 5 (relation, modality, scope, temporal, numeric) | 4 classes (supported, mild_scope, strong_action, contradiction) |
| Task | Contrastive preference testing | Single-instance relation typing + screening |
| Orientation | Cited-RAG orientation | Scientific claim-evidence calibration / diagnostic screening |

**Key control:** ForceBench tests *whether a model recognizes force mismatch at all* (via paired comparison); CESE-OCN outputs *what type of mismatch* on a single instance and *whether it is a high-risk action overclaim*. The two are complementary: ForceBench-style contrastive tests can probe force-sensitivity; CESE-OCN-style typing can output an operational screening label.

**Residual risk:** Low. The input-form difference (paired vs. single-instance) is structural and not easily collapsed.

---

## Q3. Is CESE-OCN homogenous with CLAIM-BENCH?

**Verdict: NOT homogenous. The primary question is different.**

**Overlap:**
- Both study scientific claim-evidence relationships.
- Both use real scientific papers as evidence source.

**Non-overlap:**
| Dimension | CLAIM-BENCH | CESE-OCN |
| --- | --- | --- |
| Primary question | Is evidence correctly extracted and does it support the claim? | What *type* of evidence-sufficiency mismatch is this? |
| Output | Document-level extraction + validation label (support/refute/NEI-style) | Four-class relation label + screening signal |
| Strength mismatch taxonomy | Not introduced (organized around support/refute/NEI) | Introduced (separates mild scope from high-risk action) |
| Task | Extraction + validation | Single-instance relation typing + screening |
| Scale | Larger full-paper benchmark | 444 pairs, 6 domains |

**Key control:** CLAIM-BENCH focuses on *whether evidence supports claims* (extraction + validation); CESE-OCN focuses on *whether evidence is sufficient for the strength and actionability of claims* (calibration of claim strength to evidence). The two are sequential: CLAIM-BENCH-style extraction-validation can feed CESE-OCN-style relation typing.

**Residual risk:** Low. The primary-question difference (extraction-validation vs. strength-calibration) is clear.

---

## Q4. Where must "first" claims be avoided?

**The following "first" claims are FORBIDDEN in V3.14:**

1. "First scientific overstatement benchmark" — RIGOURATE [30] is the prior art for scientific overstatement scoring.
2. "First evidence-force calibration benchmark" — ForceBench [35] is the prior art for evidence-force calibration.
3. "First scientific claim-evidence extraction benchmark" — CLAIM-BENCH [28] is the prior art for full-paper claim-evidence extraction.
4. "First to propose evidence sufficiency calibration" — the evidence-licensed claims perspective [31] and RIGOURATE [30] are prior art.
5. "First to introduce scientific overstatement detection as a new field" — RIGOURATE [30] already does this.
6. "First to use LLM annotators for scientific overstatement" — RIGOURATE [30] uses 8 LLM annotators.
7. "First to study evidence-claim mismatch in scientific papers" — CLAIM-BENCH [28] and RIGOURATE [30] both study this.

**Allowed "first" claims (narrow, defensible):**
- "First to isolate `strong_action_overclaim` as a separate high-risk boundary class with a dedicated screening route" — defensible if gold validation confirms the class is reliably drawable.
- "First to propose a two-layer gold protocol (relation + realism) for controlled counterfactual claim diagnostic sets" — defensible as a protocol-level contribution.

**Even these "first" claims should be hedged with "to our knowledge" until gold validation is complete.**

---

## Q5. What is the minimum safe contribution?

**The minimum safe contribution (defensible even if gold validation fails or official RIGOURATE is released):**

1. **A fine-grained four-class relation taxonomy** for evidence-sufficiency mismatch, with an operational decision tree (Figure 2), concrete examples (Table 0), and explicit boundary rules — *as a labeling aid, not a validated annotation scheme*.
2. **A controlled silver-stage diagnostic finding** that, under tested prompts, generic LLM judges under-detect strong_action_overclaim — *as a prompt/model/sample-specific finding, not a fundamental limit of LLMs*.
3. **A relation-specific screening route (R4)** that improves strong_action positive-F1 on the controlled silver-stage evaluation, at the cost of lower macro-F1 — *as a screening-oriented complement, not a replacement*.
4. **A RIGOURATE-style scalar proxy baseline** showing that a scalar score cannot reliably distinguish mild from strong_action on SimClaim — *as proxy evidence, not official RIGOURATE comparison*.
5. **A pre-registered two-layer gold protocol** (relation + realism) with frozen criteria and frozen realism thresholds — *as a protocol contribution, not a validated result*.

**This minimum contribution is safe because:**
- It does not depend on gold validation succeeding (the silver-stage findings are reported as silver-stage).
- It does not depend on official RIGOURATE being unavailable (the proxy baseline is explicitly a proxy).
- It does not claim to outperform any prior work (the differentiation is positioning-level).
- It does not claim natural prevalence (SimClaim is counterfactual).
- It is falsifiable: gold adjudication can confirm or downgrade each claim via pre-registered criteria.

---

## Q6. If the scalar baseline is not strong, how does CESE-OCN retain value?

**The scalar baseline (§VI.E) is NOT strong on the mild-vs-strong distinction:**
- `rule_scalar_score` ROC-AUC = 0.5062 (chance-level) on mild_vs_strong.
- `llm_scalar_proxy` ROC-AUC = 0.5874 (weak, below 0.70) on mild_vs_strong.
- Both scalar variants are at chance-level (ROC-AUC ≤ 0.52) on strong_vs_nonstrong.

**This weakness IS the value of CESE-OCN.** The scalar baseline's failure to distinguish mild from strong_action is the empirical motivation for the four-class decomposition. If the scalar baseline were strong, CESE-OCN's contribution would be undermined (a scalar would suffice). The scalar's weakness on the high-risk boundary class is exactly the gap CESE-OCN fills.

**CESE-OCN retains value via:**
1. **The four-class decomposition** isolates the high-risk boundary class (`strong_action_overclaim`) that the scalar compresses away.
2. **R4's dedicated escalation route** achieves strong_F1 = 0.3967 vs. scalar best-F1 = 0.3844 on silver 444 (and 0.3000 vs. 0.1364 on matched 100).
3. **R4 captures 8/24 strong_action cases** that all three LLM judges miss on matched 100.
4. **The two-layer gold protocol** provides a falsifiable validation mechanism for the relation-label reliability and claim realism.

**The scalar's strength on the broad supported-vs-overclaim distinction (ROC-AUC = 0.85 for llm_scalar_proxy) is complementary, not competitive:** scalar for broad severity, relation-specific for high-risk action-overclaim screening.

---

## Q7. If the realism audit shows claims are too artificial, how to downgrade?

**The two-layer gold protocol (§VII.J) has pre-registered downgrade thresholds:**

### Class-level threshold (per silver-label class)
- If > 25% of claims in any class have `claim_realism_score_1_to_5 ≤ 2`, that class is flagged for paper-validity review.
- **Downgrade action:** the paper adds an explicit "realism caveat" to the corresponding §VI result and the §VIII screening-utility claim for that class.
- If the flagged class is `strong_action_overclaim`, the §VI.E Q3-Q5 answers and the §VIII.D.B Screening Utility Test result are reported with the caveat that the strong_action claims may not transfer to natural scientific writing.

### Paper-level threshold (all gold-annotated claims)
- If > 25% of all gold-annotated claims have `claim_realism_score_1_to_5 ≤ 2`, the paper's main claims are downgraded from:
  - "controlled silver-stage evidence on a diagnostic set" → "controlled silver-stage evidence on a synthetic diagnostic set with limited natural-claim transferability."
- **Downgrade action:** an additional §IX limitation item is added, explicitly stating that SimClaim claims are too artificial to support the main screening claim without a follow-up natural-claim study.

### Heuristic pre-screen (already conducted, NOT gold)
- 21/444 (4.7%) overall realism risk flag.
- 10/111 (9.0%) for `strong_action_overclaim` class.
- Both are below the 25% pre-registered threshold, but the `strong_action_overclaim` rate is non-trivial.
- This pre-screen is pattern-based and NOT a substitute for human realism annotation; it only informs the gold sampling order (strong_action prioritised).

### Worst-case downgrade scenario
If gold realism annotation reveals > 25% of `strong_action_overclaim` claims are unrealistic:
1. §VI.E Q3-Q5 answers are reported with a realism caveat.
2. §VIII.D.B Screening Utility Test is reported as "on the diagnostic set, with limited natural-claim transferability."
3. §IX adds a limitation: "the strong_action screening claim is diagnostic-stage only; a follow-up natural-claim study is required before deployment-oriented claims."
4. The mainline lock (§II.B) is NOT violated: the paper still studies fine-grained relation diagnosis + strong_action screening, but the screening claim is explicitly diagnostic-stage.

### If realism thresholds are NOT breached
The paper states that SimClaim claims pass the pre-registered realism check and proceeds with the main tables as-is. The two-layer gold protocol is the falsifiable mechanism that addresses the realism risk.

---

## Summary

| Question | Verdict |
| --- | --- |
| Q1. Homogenous with RIGOURATE? | NOT homogenous; overlap is largest but controlled via §VI.E + counterfactual data disclosure |
| Q2. Homogenous with ForceBench? | NOT homogenous; input form (paired vs. single) is structurally different |
| Q3. Homogenous with CLAIM-BENCH? | NOT homogenous; primary question (extraction-validation vs. strength-calibration) is different |
| Q4. Where to avoid "first" claims? | 7 specific "first" claims forbidden; 2 narrow "first" claims allowed with hedging |
| Q5. Minimum safe contribution? | 5 items (taxonomy + diagnostic + screening + proxy baseline + two-layer gold protocol) |
| Q6. Scalar baseline weak → CESE-OCN value? | The scalar's weakness IS the value; it motivates the four-class decomposition |
| Q7. Realism audit shows claims too artificial → downgrade? | Pre-registered 25% class-level and paper-level thresholds with explicit downgrade actions |
