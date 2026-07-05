# V3.4 Remaining Risks

**Date:** 2026-07-04
**Manuscript:** V3.4 Taxonomy Hardened — Evidence Sufficiency Calibration
**Stance:** Honest, conservative. V3.4 is more defensible than V3.3 on taxonomy subjectivity, but is **not** Q1-ready.

---

## 1. Bottom Line

V3.4 is **not Q1-ready**. The largest remaining risk remains the **lack of independent gold adjudication**. V3.4 has *reduced* the taxonomy subjectivity risk (the second-largest risk) by providing an operational decision tree and root cause analysis, but has not *eliminated* it.

V3.4 is suitable as a **Q2/Q3-tier diagnostic paper雏形**, more defensible than V3.3 because:
- The 25 questionable/unclear audit cases now have *identifiable root causes* (not a black box).
- The taxonomy is now *operationalizable* via a 4-step decision tree.
- The paper *does not hide* the 25/40 rate — it reports, diagnoses, and discloses it.
- Trusted illustrative cases are separated from high-risk boundary cases.

---

## 2. Largest Remaining Risk

### R-1 (largest, unchanged from V3.3): Lack of Independent Gold Adjudication

**Why this remains the largest risk:** All 444 SimClaim labels are still silver. The V3.4 root cause analysis shows that 12/25 questionable/unclear cases are *genuinely hard boundary cases* (mild_vs_strong), which means even independent annotators may disagree on these cases. The decision tree (§III.C) operationalizes the boundary but does not resolve it — 12 cases remain ambiguous even with the decision tree.

**What is needed:** Independent two-annotator adjudication of 300–500 pairs, with inter-annotator agreement reported *separately for each boundary* (mild_vs_strong, strong_vs_contradiction, supported_vs_mild). The high-risk sample bank (`high_risk_sample_bank.csv`) provides the 25 priority cases for this adjudication.

**Impact on the paper's central claim:** If gold adjudication reveals that the mild/strong boundary is not reliably drawable (κ < 0.4 on this boundary), the strong_action_overclaim class itself may need to be merged with mild, which would weaken the paper's central contribution. V3.4's decision tree is a starting operationalization, but it is not validated against gold.

---

## 3. Other Remaining Risks

### R-2: Mild/Strong Boundary Is the Central Annotation Challenge

**Status:** Partially addressed in V3.4, but not resolved.

The audit shows 12/25 questionable/unclear cases are mild_vs_strong_boundary_unclear, and strong_action has a 75% confusion rate. The decision tree (§III.C) operationalizes the boundary, but 12 cases remain genuinely ambiguous. This means:
- The strong_action_overclaim class is the hardest to annotate reliably.
- Any gold annotation effort must invest disproportionate effort in this boundary.
- The strong_action numeric results (R4 strong-F1 = 0.3967, LLM strong-F1 = 0.0769) should be read as diagnostic evidence on a hard boundary, not as stable benchmark numbers.

**What is needed:** Two-annotator pilot on the 25 high-risk cases, with adjudication and κ reported separately for mild_vs_strong. If κ on this boundary is acceptable (>0.4), the taxonomy is defensible. If not, the boundary may need to be redrawn.

### R-3: Decision Tree Is Not Validated Against Gold

**Status:** New risk identified in V3.4.

The 4-step decision tree (§III.C) is a *labeling aid*, not a validated annotation scheme. It has not been tested against gold labels (because no gold labels exist). It may:
- Misclassify cases that the decision tree's steps yield ambiguous results for.
- Over-operationalize boundaries that are actually more nuanced.
- Introduce new biases (e.g., treating all detail-swapping as contradiction, when some detail-swapping may be mild or strong).

**What is needed:** Validate the decision tree against gold annotation. If the decision tree's labels match gold labels on >80% of cases, it is a useful aid. If not, it needs revision.

### R-4: Trusted Case Bank Is Not Gold

**Status:** Disclosed, but still a risk.

The 18 trusted illustrative cases (`trusted_case_bank.csv`) are *not* gold. They are cases where the audit rated "reasonable" or where evidence/claim clarity is high. But "reasonable" by author audit is not the same as "correct" by independent adjudication. A reviewer may ask: "How do you know your trusted cases are actually correctly labeled?"

**What is needed:** Independent adjudication of the 18 trusted cases. If most are confirmed, the paper's examples are defensible. If many are overturned, the paper's examples need revision.

### R-5: Claim Generation May Introduce Bias (5/25 claim_too_abstract)

**Status:** Partially addressed.

5/25 questionable/unclear cases are classified as `claim_too_abstract` — the claim describes what the paper does rather than making an explicit action/deployment assertion. This may indicate that the claim generation process (which produced the claims from evidence) sometimes produces claims that are too abstract to clearly map to the taxonomy. This is a *claim generation problem*, not a taxonomy problem, but it affects label quality.

**What is needed:** Review the claim generation policy. If claims are too abstract, the policy may need revision to produce more concrete action/deployment assertions for strong_action cases.

### R-6: Audit Heuristic Was Too Conservative (2/25 cases)

**Status:** Disclosed.

2/25 questionable/unclear cases are classified as `audit_heuristic_too_conservative` — the audit keyword heuristic missed action/strength cues that are present but implicit. This means the audit's 62.5% questionable/unclear rate may be *slightly inflated* — a more nuanced audit might rate these 2 cases as reasonable. However, this is a small fraction (8%) and does not change the overall picture.

### R-7: Small Dataset, Single-Run LLM, No Variance Estimate (unchanged from V3.3)

These risks remain:
- 444 pairs, ~16 test per seed.
- LLM comparison is single-run, temperature 0, no variance estimate.
- No prompt robustness sweep.
- No open-source LLM replication.
- GPT-5.5 accessed via third-party proxy.

See V3.3's `V3_3_submission_readiness_checklist.md` for details.

---

## 4. What V3.4 Does NOT Claim

1. **Not** claiming the taxonomy is "fully solved" or "validated."
2. **Not** claiming the decision tree is a gold standard.
3. **Not** claiming the 25 questionable/unclear cases are label noise (most are boundary cases).
4. **Not** claiming the trusted case bank cases are gold.
5. **Not** claiming the mild/strong boundary is resolved.
6. **Not** claiming R4 outperforms LLM judges overall.
7. **Not** claiming the LLM blind spot is established (still silver-vs-silver).
8. **Not** hiding or deleting any of the 25 questionable/unclear cases.

---

## 5. Path to Q1 (Updated from V3.3)

The path to Q1 now includes a V3.4-specific item:

1. **Independent gold adjudication of 300-500 pairs** with κ/α reported *separately for each boundary* (mild_vs_strong, strong_vs_contradiction, supported_vs_mild). Priority: the 25 cases in `high_risk_sample_bank.csv`.
2. **Validate the decision tree** against gold labels. If match rate >80%, the decision tree is a useful aid.
3. **Re-run all R4 and LLM comparisons on gold subset.**
4. **Case study on gold subset** (10-20 cases where LLM disagrees with gold).
5. **Few-shot and open-source LLM baselines.**
6. **Prompt robustness sweep.**
7. **Paired bootstrap significance** for all comparisons.

Item 1 (gold adjudication) and item 2 (decision tree validation) are V3.4-specific. Items 3-7 are unchanged from V3.3.

---

## 6. V3.4 vs V3.3: Risk Reduction Summary

| Risk | V3.3 Status | V3.4 Status | Reduced? |
|---|---|---|---|
| Lack of gold adjudication (R-1) | Largest risk | Still largest risk | No (cannot be resolved without new annotation) |
| Taxonomy subjectivity (R-2) | Major risk | Partially addressed (decision tree + root cause) | Yes |
| Decision tree not validated (R-3) | N/A | New risk | No (new risk, but bounded) |
| Trusted cases not gold (R-4) | N/A | Disclosed | Partially |
| Claim generation bias (R-5) | Not identified | Identified (5/25) | Partially (identified, not resolved) |
| Audit too conservative (R-6) | Not identified | Identified (2/25) | Yes (disclosed) |
| Small dataset / single-run LLM (R-7) | Major risk | Unchanged | No |

**Net effect:** V3.4 reduces the taxonomy subjectivity risk (the second-largest risk) and identifies new risks (decision tree validation, claim generation bias) that were previously hidden. The largest risk (lack of gold adjudication) remains unchanged.

---

## 7. Final Honest Statement

V3.4 is an honest, conservative revision of V3.3 that addresses the taxonomy boundary problem head-on. It does not hide the 25/40 questionable/unclear rate — it diagnoses the root causes, provides an operational decision tree, separates trusted cases from high-risk cases, and argues that boundary cases are expected for a boundary task.

The remaining risks are real and disclosed. The largest risk — lack of independent gold adjudication — is acknowledged in the abstract, §V.D, §VII.F, §VIII, and this file. The decision tree is a starting operationalization, not a validated scheme. The trusted case bank is illustrative, not gold.

**V3.4 is suitable for submission to Q2/Q3-tier venues. It is not suitable for Q1 submission without independent gold adjudication and decision tree validation.**
