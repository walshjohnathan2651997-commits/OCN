"""Build V3.4 main paper MD from V3.3 with taxonomy hardening revisions.

Enhancements over V3.3:
1. Add taxonomy decision tree summary in §III (Problem Definition)
2. Rewrite §V.D audit results with root cause analysis (not just 25/40 number)
3. Add §VII.F "Boundary cases are not noise to hide"
4. Strengthen §VIII Limitations with boundary challenge
5. Cross-reference trusted_case_bank.csv and high_risk_sample_bank.csv

Does NOT modify V3.3. Reads V3.3 MD, applies enhancements, writes V3.4 MD.
"""
import os
import re

V33_PATH = r"D:\ocn\paper_versions_ordered\V3_3_reviewer_defense_polished\CESE_OCN_V3_3_reviewer_defense_polished.md"
V34_PATH = r"D:\ocn\paper_versions_ordered\V3_4_taxonomy_hardened\CESE_OCN_V3_4_taxonomy_hardened.md"


def build_v34():
    with open(V33_PATH, 'r', encoding='utf-8') as f:
        v33 = f.read()

    v34 = v33.replace(
        "**Version:** V3.3 (reviewer-defense polished)\n**Date:** 2026-07-04\n**Changes from V3.2:** P1/P2 reviewer-defense polish — strengthened Introduction (4-layer logic, 4 contributions), strengthened Method (Figure 1 caption, clearer routing motivation), strengthened Results narrative (explicit non-outperformance statement), strengthened Limitations (honest diagnostic framing), added reviewer defense matrix, related work insert, submission readiness checklist. No new experiments, no API calls, no new data.",
        "**Version:** V3.4 (taxonomy hardened)\n**Date:** 2026-07-04\n**Changes from V3.3:** Taxonomy boundary hardening — added operational decision tree for the four-class taxonomy, diagnosed root causes of the 25 questionable/unclear audit cases (taxonomy boundary vs. audit too conservative vs. claim too abstract vs. evidence too short), built trusted case bank (18 illustrative cases) and high-risk sample bank (25 boundary cases), added 'Boundary cases are not noise to hide' discussion, strengthened Limitations with boundary challenge. No new experiments, no API calls, no new data."
    )

    # 1. Add taxonomy decision tree summary in §III after §III.B (Table 0)
    # Insert §III.C "Taxonomy Decision Tree (Operational)" before the existing §III.C "Why strong_action_overclaim Is the Core Hard Case"
    decision_tree_section = """### C. Taxonomy Decision Tree (Operational, Added in V3.4)

To make the taxonomy operationalizable and reduce the boundary confusion identified in the author sanity audit (§V.D), we introduce a four-step decision tree for label assignment. The full decision tree with operational rules is provided in `taxonomy_boundary_decision_tree.md`; a summary follows.

**Step 1 — Directional conflict?** Does the claim point in the *opposite direction* from the evidence on the same metric, number, entity, or conclusion? If yes → `contradiction_candidate`. (This includes *detail-swapping*: changing specific numbers, names, or metrics — the most common contradiction pattern in SimClaim.)

**Step 2 — Action/deployment/safety/operational cue present?** Does the claim introduce deployment, safety, guarantee, operational, policy, generalization, or action language (e.g., "deployment-ready", "safety guarantee", "theoretically justified", "outperforms", "suitable for")? If yes → Step 3. If no → Step 4.

**Step 3 — Evidence sufficient for action strength?** Is the evidence limited to local/experimental/simulated results, while the claim asserts a stronger action/deployment/safety/generalization conclusion? If yes → `strong_action_overclaim`. If no → re-examine as `supported` or `mild_scope_overclaim`.

**Step 4 — Scope over-extension?** Does the claim expand scope, domain, population, condition, or temporal range beyond what the evidence supports, *without* asserting action/deployment/safety consequences? If yes → `mild_scope_overclaim`. If no → `supported`.

**Key distinctions operationalized by this tree:**

1. **strong_action_overclaim does not require directional conflict.** The claim may align with evidence direction, but its *strength* (action/deployment/safety assertion) exceeds what the evidence warrants.
2. **contradiction_candidate is about directional conflict** on the same metric/number/entity, including detail-swapping (e.g., evidence says "6 systems", claim says "8 systems").
3. **strong_action_overclaim is about strength/action consequences**, not scope breadth alone.
4. **mild_scope_overclaim is about scope/generalization over-extension** without action/deployment/safety consequences.
5. **supported means evidence is sufficient for the claim's stated strength**, not that the claim is "absolutely true."

The decision tree is a *labeling aid*, not a gold standard. Cases where the tree yields ambiguous results are flagged as boundary cases for future gold adjudication (§V.D, `high_risk_sample_bank.csv`).

"""

    # Insert before the existing §III.C "Why strong_action_overclaim Is the Core Hard Case"
    # Re-letter: existing C→D, D→E
    v34 = v34.replace(
        "### C. Why strong_action_overclaim Is the Core Hard Case",
        decision_tree_section + "### D. Why strong_action_overclaim Is the Core Hard Case"
    )
    v34 = v34.replace(
        "### D. Binary Projections",
        "### E. Binary Projections"
    )

    # 2. Rewrite §V.D audit results to include root cause analysis
    # Find the existing audit results paragraph and enhance it
    old_audit_findings = """**Key findings:**

1. **25/40 (62.5%) of silver labels are flagged as questionable or unclear.** This is a real signal that silver labels require independent gold validation before the LLM blind spot finding can be treated as established.
2. **strong_action_overclaim has the highest confusion rate** (15/20 = 75% flagged), mostly mild_vs_strong confusion. This is expected: strong_action is the most subtle class, and the boundary between mild and strong is the hardest to operationalize.
3. **All 6 contradiction_candidate cases are flagged unclear**, mostly strong_vs_contradiction confusion. This suggests the contradiction vs strong_action boundary needs clearer operationalization in future gold annotation.
4. **supported is the most stable class** (7/7 reasonable), which is expected since supported is the easiest class to identify.

**Interpretation:** This audit confirms that the silver labels are not ready to be treated as gold. The LLM blind spot finding (§VI.C) is computed against these silver labels, and the high questionable/unclear rate means the finding must be interpreted as **diagnostic evidence against silver labels, pending independent gold adjudication** — not as an established property of LLM judges. The audit does not invalidate the framework (the relative pattern — R4 > LLM on strong_action — may hold under gold), but it bounds the strength of the claim."""

    new_audit_findings = """**Key findings:**

1. **25/40 (62.5%) of silver labels are flagged as questionable or unclear.** This is a real signal that silver labels require independent gold validation before the LLM blind spot finding can be treated as established. However, root cause analysis (below) shows that the 25 cases are *not* all label noise — they reflect a mix of taxonomy boundary issues, audit heuristic limitations, and genuinely hard cases.

2. **Root cause distribution of the 25 questionable/unclear cases** (full diagnosis in `sanity_audit_error_diagnosis.csv`):
   - **mild_vs_strong_boundary_unclear (12 cases, 48%):** The claim has some scope-expansion or strength cue, but the boundary between mild_scope_overclaim and strong_action_overclaim is genuinely fuzzy. These are the core taxonomy challenge cases.
   - **strong_vs_contradiction_boundary_unclear (6 cases, 24%):** The claim swaps specific details (numbers, metrics, entity names) relative to evidence. The audit heuristic looked for explicit "contradicts" language and missed the detail-swap pattern. The decision tree (§III.C, Step 1) now operationalizes detail-swapping as contradiction.
   - **claim_too_abstract (5 cases, 20%):** The claim describes what the paper does ("presents", "evaluates", "reports") without explicit action/deployment language. The silver label strong_action may be too strong, but the claim's framing still over-extends relative to evidence.
   - **audit_heuristic_too_conservative (2 cases, 8%):** The audit keyword heuristic missed action/strength cues that are present but implicit. The silver label is likely defensible.

3. **strong_action_overclaim has the highest confusion rate** (15/20 = 75% flagged), mostly mild_vs_strong confusion. This is expected: strong_action is the most subtle class, and the boundary between mild and strong is the hardest to operationalize. The decision tree (§III.C) provides a clearer operationalization, but 12 cases remain genuinely ambiguous.

4. **All 6 contradiction_candidate cases are flagged unclear**, mostly strong_vs_contradiction confusion. Root cause analysis shows these are genuine contradiction cases (detail-swapping) that the audit heuristic missed — not label noise. The decision tree (§III.C, Step 1) now operationalizes detail-swapping as contradiction, which should reduce this confusion in future annotation.

5. **supported is the most stable class** (7/7 reasonable), which is expected since supported is the easiest class to identify.

**Interpretation:** This audit confirms that the silver labels are not ready to be treated as gold. However, the root cause analysis shows that the 25 questionable/unclear cases are *not* evidence of systematic label failure — they are concentrated at the two hardest taxonomy boundaries (mild-vs-strong and strong-vs-contradiction), which is expected for an evidence-sufficiency task. The LLM blind spot finding (§VI.C) is computed against these silver labels, and the high questionable/unclear rate means the finding must be interpreted as **diagnostic evidence against silver labels, pending independent gold adjudication** — not as an established property of LLM judges. The audit does not invalidate the framework (the relative pattern — R4 > LLM on strong_action — may hold under gold), but it bounds the strength of the claim.

The 25 questionable/unclear cases are retained in `high_risk_sample_bank.csv` as boundary cases for future gold adjudication priority. They are not deleted or hidden. A separate `trusted_case_bank.csv` (18 cases, ≥4 per class) provides clear illustrative cases for paper examples — none of which are claimed as gold."""

    v34 = v34.replace(old_audit_findings, new_audit_findings)

    # 3. Add §VII.F "Boundary cases are not noise to hide" before §VIII
    boundary_discussion = """### F. Boundary Cases Are Not Noise to Hide (Added in V3.4)

A reviewer might argue that the 25/40 questionable/unclear audit rate means the taxonomy is too subjective to be useful. We disagree, but we state the argument carefully.

Evidence sufficiency calibration is *inherently a boundary task*. The four classes are not disjoint categories with sharp edges — they are regions on a continuous space of claim-evidence strength mismatch. The hardest boundaries (mild-vs-strong, strong-vs-contradiction) are where the taxonomy is most useful *and* most uncertain. A 62.5% questionable/unclear rate on an audit that *deliberately oversampled* strong_action_overclaim (20/40 = 50% of the audit sample, vs. 25% in the balanced set) is not evidence that the taxonomy is broken — it is evidence that the taxonomy surfaces the cases where human judgment is most needed.

The root cause analysis (§V.D) supports this interpretation:
- 12/25 (48%) are *mild_vs_strong_boundary_unclear* — the core taxonomy challenge, expected to be hard.
- 6/25 (24%) are *strong_vs_contradiction_boundary_unclear* — the audit heuristic missed detail-swapping; the decision tree (§III.C) now operationalizes this.
- 5/25 (20%) are *claim_too_abstract* — a claim generation issue, not a taxonomy issue.
- 2/25 (8%) are *audit_heuristic_too_conservative* — the audit was too strict, not the labels too weak.

Only a small fraction of the 25 cases are candidates for *likely label noise*. The majority are genuinely hard boundary cases that any annotation scheme would struggle with. This means:

1. **The aggregate diagnostic pattern (R4 > LLM on strong_action) may hold even if individual labels shift under gold adjudication.** The pattern is computed over 100-200 samples, not on individual cases. If 60% of strong_action labels are stable and 40% shift, the relative ordering of R4 vs. LLM may persist — but this is not guaranteed.

2. **The paper's claims must be limited to aggregate diagnostic patterns, not individual case correctness.** We do not claim that any individual silver label is correct. We claim that the *pattern* (R4 detects more strong_action than LLM under tested prompts) is consistent across models and prompts, on the silver set.

3. **Trusted cases (§V.D, `trusted_case_bank.csv`) are used for paper examples; high-risk cases (`high_risk_sample_bank.csv`) are used for risk disclosure.** The paper does not hide the 25 questionable/unclear cases — it reports them, diagnoses their root causes, and flags them as future gold adjudication priority.

The boundary cases are not noise to hide. They are the cases where evidence sufficiency calibration is hardest and most consequential. Future gold annotation should prioritize these boundary cases, and the decision tree (§III.C) provides a starting operationalization for that work.

"""

    v34 = v34.replace(
        "## VIII. Limitations",
        boundary_discussion + "## VIII. Limitations"
    )

    # 4. Strengthen §VIII Limitations — add boundary challenge as a key limitation
    # Add after limitation 2 (author sanity audit is preliminary)
    old_l2_end = "Independent gold adjudication (two-annotator + adjudication, with Cohen's κ or Krippendorff's α) is required before the LLM under-detection finding can be treated as established."
    new_l2_end = old_l2_end + """ The root cause analysis (§V.D) shows that the 25 questionable/unclear cases are concentrated at the mild-vs-strong (12 cases) and strong-vs-contradiction (6 cases) boundaries — the two hardest taxonomy boundaries. Future gold annotation should prioritize these boundary cases, using the decision tree (§III.C) as a starting operationalization. The `high_risk_sample_bank.csv` file lists all 25 cases with recommended handling."""

    v34 = v34.replace(old_l2_end, new_l2_end)

    # Add a new limitation about mild/strong boundary being the central challenge
    # Find the practical limitations paragraph and add to it
    old_practical = "These limitations do not invalidate the framework — they bound the strength of its claims."
    new_practical = """**The mild/strong boundary remains the central annotation challenge.** The audit shows 12/25 questionable/unclear cases are mild_vs_strong_boundary_unclear, and strong_action has a 75% confusion rate. The decision tree (§III.C) operationalizes the boundary, but 12 cases remain genuinely ambiguous. This means: (a) the strong_action_overclaim class is the hardest to annotate reliably; (b) any gold annotation effort must invest disproportionate effort in this boundary; (c) the strong_action numeric results (R4 strong-F1 = 0.3967, LLM strong-F1 = 0.0769) should be read as diagnostic evidence on a hard boundary, not as stable benchmark numbers. Future gold annotation should use two annotators with adjudication specifically on mild-vs-strong cases, and report inter-annotator agreement separately for this boundary.

These limitations do not invalidate the framework — they bound the strength of its claims. The contribution is a falsifiable framework and a frozen main method whose numeric claims are constrained by the paper-ready result pack, positioned as a diagnostic complement to LLM judges rather than a competitive replacement."""

    v34 = v34.replace(old_practical, new_practical)

    with open(V34_PATH, 'w', encoding='utf-8') as f:
        f.write(v34)

    print(f"V3.4 MD written: {V34_PATH}")
    print(f"Size: {os.path.getsize(V34_PATH)} bytes")
    print(f"V3.3 size: {os.path.getsize(V33_PATH)} bytes (unchanged)")


if __name__ == '__main__':
    build_v34()
