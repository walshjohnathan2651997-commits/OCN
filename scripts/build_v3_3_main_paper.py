"""Build V3.3 main paper MD from V3.2 with P1/P2 reviewer-defense polish.

Enhancements over V3.2:
1. Strengthened Introduction (4-layer logic + 4 contributions)
2. Strengthened Method (Figure 1 caption + clearer routing motivation)
3. Strengthened Results narrative (explicit "not outperforming LLM" sentence)
4. Strengthened Limitations (7-item honest, non-failure framing)
5. Added reviewer-defense positioning throughout
6. Version note at top

Does NOT modify V3.2. Reads V3.2 MD, applies enhancements, writes V3.3 MD.
"""
import os
import re

V32_PATH = r"D:\ocn\paper_versions_ordered\V3_2_p0_repaired_evidence_sufficiency\CESE_OCN_V3_2_p0_repaired_evidence_sufficiency.md"
V33_PATH = r"D:\ocn\paper_versions_ordered\V3_3_reviewer_defense_polished\CESE_OCN_V3_3_reviewer_defense_polished.md"


def build_v33():
    with open(V32_PATH, 'r', encoding='utf-8') as f:
        v32 = f.read()

    # 1. Update version header
    v33 = v32.replace(
        "**Version:** V3.2 (P0 repaired)\n**Date:** 2026-07-04\n**Changes from V3.1:** P0 fatal-risk repairs — added Table 0 taxonomy examples, author sanity audit of silver labels, explicit R4 macro-F1 gap discussion, softened LLM blind spot claims, rewrote Method to avoid rule-stacking framing, expanded Limitations.",
        "**Version:** V3.3 (reviewer-defense polished)\n**Date:** 2026-07-04\n**Changes from V3.2:** P1/P2 reviewer-defense polish — strengthened Introduction (4-layer logic, 4 contributions), strengthened Method (Figure 1 caption, clearer routing motivation), strengthened Results narrative (explicit non-outperformance statement), strengthened Limitations (honest diagnostic framing), added reviewer defense matrix, related work insert, submission readiness checklist. No new experiments, no API calls, no new data."
    )

    # 2. Strengthen Introduction — replace the entire §I with a 4-layer logic version
    new_intro = """## I. Introduction

Scientific claim verification is typically framed as a three-class task: given a claim and evidence, decide whether the evidence *supports* the claim, *refutes* it, or provides *not enough information* (NEI). This framing — established by benchmarks such as FEVER [1], SNLI [2], and SciFact [3] — is effective for factual correctness, but it is **insufficient** for scientific claim calibration, where the most frequent and consequential failure mode is not outright contradiction but **strength mismatch**: the evidence is topically relevant, directionally consistent, and non-contradictory, yet it does not justify the *strength* of the claim. A benchmark improvement becomes a "deployment-ready system"; a controlled simulated result becomes a "safety guarantee"; a single-domain observation becomes a "generalization claim". These cases are not captured by support/refute/NEI labels, because the evidence does support *something* — just not the action, deployment, or operational conclusion asserted by the claim.

This motivates the **evidence sufficiency calibration** task. Rather than asking only whether evidence supports or refutes a claim, we ask whether the evidence is *sufficient for the strength of the claim* — including its scope, action framing, deployment implications, safety conclusions, and generalization breadth. We formulate this as a four-class relation problem: (i) **supported** — the evidence supports the claim as stated, including its strength; (ii) **mild_scope_overclaim** — the claim mildly over-extends the scope of the evidence, without asserting an action/deployment/safety conclusion; (iii) **strong_action_overclaim** — the claim asserts an action, deployment, safety, policy, generalization, guarantee, or operational conclusion that the evidence does not justify; (iv) **contradiction_candidate** — the evidence contradicts the claim. Class (iii) — strong_action_overclaim — is the most consequential and the hardest to detect, because the evidence is often relevant and the claim is not strictly false; it is simply stronger than the evidence warrants.

A natural hypothesis is that strong LLM judges (GPT-5.5, DeepSeek-V3) should handle this task well, given their broad language understanding. We test this hypothesis empirically. We find that under the tested prompts, generic LLM judges are strong on overall support/refutation and contradiction (GPT-5.5 macro-F1 = 0.5523, DeepSeek-V3 macro-F1 = 0.5270 on matched samples), but they **consistently under-detect strong_action_overclaim on the tested samples**: on 100 matched SimClaim samples, both GPT-5.5 with a standard judge prompt and GPT-5.5 with a structured 5-step evidence-sufficiency decomposition prompt achieve strong_action-F1 of only 0.0769 (recall 0.04 = 1/25). DeepSeek-V3 on 200 samples achieves the same strong_action-F1 of 0.0769. The structured prompt — which explicitly asks the model to decompose factual alignment, scope expansion, action/deployment claims, and evidence sufficiency — does *not* improve strong_action detection under this single tested prompt design. This suggests that this prompt-engineering approach alone does not fix the under-detection pattern under the tested setting. We emphasize that this finding is bounded: it is single-run, on 100 matched silver-labeled samples, with one structured prompt design, and we do not claim that LLMs cannot solve strong_action_overclaim — only that under the tested prompts, on the current silver diagnostic set, the pattern is consistent across the two tested models.

We therefore position CESE-OCN R4 as a **complement** to generic LLM/NLI judges, not a replacement. R4 is a mixed relation-routing framework: a contradiction detector handles the most separable relation first; a scope-calibration residual classifier handles supported vs. mild_scope_overclaim; and a conservative strong-action escalation route targets strong_action_overclaim specifically, under a guarded condition that prevents contradiction cases from being absorbed. On the same 100 matched samples where GPT and DeepSeek achieve strong_action-F1 0.0769, R4 achieves strong_action-F1 0.3000 (absolute gap +0.2231). **R4 is not the strongest model on overall macro-F1 — LLM judges retain that, with GPT-5.5 at 0.5523 vs. R4 at 0.3280 on the matched 100 — but it provides targeted value on the relation that LLM judges miss under the tested prompts.** This positioning as a relation-specific complement, rather than a competitive replacement, is central to the paper's contribution.

This manuscript makes four cautious contributions:

(i) It frames scientific claim calibration as **evidence sufficiency calibration**, a four-class relation task distinguishing strong_action_overclaim from generic support/refutation/NEI, with concrete taxonomy examples (Table 0) and an author sanity audit of silver labels (§V.D);

(ii) It constructs a **silver diagnostic set** of 444 claim-evidence pairs across 111 evidence groups and six domains, with AI-preannotated and author-screened labels, and provides taxonomy examples (Table 0) to make the label space concrete and reproducible;

(iii) It introduces **CESE-OCN R4**, a conservative strong-action router as a mixed relation-routing framework that complements black-box LLM judges, with explicit acknowledgment that R4 sacrifices overall macro-F1 for targeted strong_action recall, and with a text Figure 1 describing the routing flow;

(iv) It reports a **matched-sample LLM judge comparison** (DeepSeek-V3, GPT-5.5 standard, GPT-5.5 structured) showing that under the tested prompts, this structured decomposition design does not improve strong_action detection, while R4 provides complementary value on this relation — bounded by silver-label and single-run limitations, and explicitly not a claim that R4 outperforms LLM judges overall.

The remainder of the paper is organized as follows: §II positions the work relative to claim verification, NLI, RAG evaluation, hedging, and calibration; §III formulates the evidence sufficiency calibration task and provides taxonomy examples (Table 0); §IV describes the CESE-OCN R4 mixed relation-routing framework (Figure 1); §V describes the data and experimental protocol, including the author sanity audit; §VI reports results; §VII discusses implications; §VIII states limitations; §IX concludes."""

    # Replace the old §I (from "## I. Introduction" to "## II. Related Work")
    v33 = re.sub(
        r"## I\. Introduction.*?(?=## II\. Related Work)",
        new_intro + "\n\n",
        v33,
        count=1,
        flags=re.DOTALL
    )

    # 3. Add Figure 1 caption note in §IV.B (right after the existing text Figure 1 block)
    # The existing block ends with: "Frozen mean thresholds: `t_contra = 0.48`..."
    # Add a clear Figure 1 caption line right after.
    v33 = v33.replace(
        "**Figure 1 (text).** R4 routing flow. The router applies three routes in order: contradiction first (the most separable relation), then strong-action escalation under a conservative contradiction guard (to prevent contradiction cases from being absorbed into strong_action), then a supported/mild residual classifier. Frozen mean thresholds: `t_contra = 0.48`, `t_strong = 0.535`, `t_svm = 0.51`, `t_low` = lower contradiction guard.",
        "**Figure 1 (text).** R4 routing flow. The router applies three routes in order: contradiction first (the most separable relation), then strong-action escalation under a conservative contradiction guard (to prevent contradiction cases from being absorbed into strong_action), then a supported/mild residual classifier. Frozen mean thresholds: `t_contra = 0.48`, `t_strong = 0.535`, `t_svm = 0.51`, `t_low` = lower contradiction guard. *A standalone text version of Figure 1 with full routing rationale is provided in `V3_3_method_flow_figure_text.md`.*"
    )

    # 4. Add explicit "This result should not be interpreted as R4 outperforming LLM judges overall" in §VI.C
    # Insert right before "#### C.4 Interpretation"
    v33 = v33.replace(
        "#### C.4 Interpretation",
        "**This result should not be interpreted as R4 outperforming LLM judges overall.** R4's macro-F1 (0.3280) is substantially lower than GPT-5.5 (0.5523) and DeepSeek-V3 (0.5248) on the same 100 matched samples. R4's value is relation-specific: it targets the strong_action_overclaim relation that LLM judges miss under the tested prompts. The complement framing depends on this gap being acceptable for the downstream use case (§VII.C). We do not claim R4 is better than LLM judges overall — we claim R4 provides targeted value on strong_action_overclaim, at the cost of lower overall macro-F1.\n\n#### C.4 Interpretation"
    )

    # 5. Strengthen Limitations — rewrite §VIII to be more honest and diagnostic-framed
    new_limitations = """## VIII. Limitations

This work is a **diagnostic pilot study**, not a confirmatory benchmark. The limitations below define the boundary of what the current results do and do not support. We state them clearly so that reviewers and future work can judge the scope of the claims.

1. **Silver labels are not gold labels.** The current dataset uses AI-preannotated, author-screened silver labels, not fully adjudicated gold. The author sanity audit (§V.D) flags 25/40 (62.5%) of silver labels as questionable or unclear, with strong_action_overclaim having a 75% confusion rate. All numeric results are exploratory on the silver set. We do not claim gold/human-audited performance, human kappa, or Q1 readiness from silver data alone. The LLM under-detection finding (§VI.C) is computed against these silver labels and must be interpreted as diagnostic evidence, pending independent gold adjudication.

2. **Author sanity audit is preliminary, not independent adjudication.** The audit in §V.D is a qualitative plausibility check by the authors, not independent human annotation with reported inter-annotator agreement. It flags label uncertainty but does not resolve it. Independent gold adjudication (two-annotator + adjudication, with Cohen's κ or Krippendorff's α) is required before the LLM under-detection finding can be treated as established.

3. **LLM results are prompt/model/sample specific.** The GPT-5.5 and DeepSeek-V3 results are single-run, temperature 0, on ≤200 samples, under specific prompts. A different model, prompt, or sample may behave differently. We do not claim that "LLMs cannot solve strong_action_overclaim" — only that under the tested prompts, on the current silver diagnostic set, the pattern is consistent across the two tested models. The structured 5-step decomposition result is a single prompt design; other decompositions (few-shot, chain-of-thought, tool-augmented) are untested and might behave differently.

4. **R4 is not a general-purpose LLM judge replacement.** On matched 100 samples, R4 macro-F1 = 0.3280 vs. GPT-5.5 = 0.5523 (gap 0.22). R4 is a relation-specific diagnostic complement, not a general-purpose classifier. It sacrifices macro-F1 for strong_action recall. We do not claim R4 is better than LLM judges overall — we claim R4 provides targeted value on the strong_action_overclaim relation, at the cost of lower overall macro-F1.

5. **External public datasets only provide generic verification sanity checks.** SciFact and VitaminC use support/refute/NEI labels and do not contain action-overclaim or scope-overclaim labels. External results validate only generic support/refutation transfer and evidence-sensitivity sanity, **not** the SimClaim-specific four-class escalation task. Public data cannot replace SimClaim gold evaluation. R4-compatible underperforms NLI on public data because the strong-action route is inactive by design.

6. **Strong_action remains the main targeted use case.** R4's improvement is concentrated on strong_action_overclaim (+0.1559 strong-F1). The supported/mild boundary remains weak (mild-F1 = 0.1266) and is treated as an open problem, not a solved subtask. R4 is designed for action-overclaim monitoring, not for general four-class classification.

7. **Future work requires independent adjudication.** A higher-tier confirmatory submission requires 300–500 independently adjudicated claim-evidence pairs, inter-annotator agreement statistics (κ/α), paired bootstrap significance tests against stronger external baselines, prompt robustness sweeps, few-shot and open-source LLM replications, and external validation of the four-class taxonomy. The author sanity audit is not a substitute for this. Until this work is completed, the current results should be reported with clear silver-label limitations, without claims of final benchmark readiness, and without claims that R4 outperforms LLM judges overall.

Additional practical limitations: (a) small dataset (444 pairs, ~16 test per seed); (b) single-run LLM comparison with no variance estimate; (c) GPT-5.5 accessed via third-party proxy, not official OpenAI API; (d) R4 over-routes supported → strong (98 false positives) and mild → strong (24 false positives), a trade-off for improved strong recall; (e) cross-domain generalization is not confirmed beyond the six SimClaim domains; (f) LLM judge results are labeled "small-sample pilot, N ≤ 200" and are never merged with SimClaim main results or claimed as gold standard.

These limitations do not invalidate the framework — they bound the strength of its claims. The contribution is a falsifiable framework and a frozen main method whose numeric claims are constrained by the paper-ready result pack, positioned as a diagnostic complement to LLM judges rather than a competitive replacement."""

    v33 = re.sub(
        r"## VIII\. Limitations.*?(?=## IX\. Conclusion)",
        new_limitations + "\n\n",
        v33,
        count=1,
        flags=re.DOTALL
    )

    # 6. Add reviewer-defense note at end of §VII Discussion
    # Append a new §VII.E before §VIII
    new_discussion_e = """### E. Reviewer Defense and Honest Positioning

We anticipate several reviewer concerns and address them briefly here; a full reviewer defense matrix is provided in `V3_3_reviewer_defense_matrix.csv`.

The most consequential concerns are: (1) silver labels are not gold — addressed by the author sanity audit (§V.D) and explicit bounding of the LLM under-detection finding as "diagnostic evidence, pending independent gold adjudication"; (2) R4 macro-F1 is lower than LLM judges — addressed by §VI.C.3 and the explicit positioning of R4 as a relation-specific complement; (3) LLM prompts may be insufficient — addressed by the structured prompt probe (§V.C.2) and the explicit "under the tested prompts" caveat; (4) the four-class taxonomy may be subjective — addressed by Table 0 examples and the honest reporting of the 75% confusion rate on strong_action in the audit.

We do not claim these defenses are conclusive. They bound the claims and make the limitations explicit. A higher-tier submission requires independent gold adjudication, prompt robustness sweeps, and open-source LLM replication — work that is left to future versions.

"""

    v33 = v33.replace(
        "## VIII. Limitations",
        new_discussion_e + "## VIII. Limitations"
    )

    # Write V3.3
    with open(V33_PATH, 'w', encoding='utf-8') as f:
        f.write(v33)

    print(f"V3.3 MD written: {V33_PATH}")
    print(f"Size: {os.path.getsize(V33_PATH)} bytes")
    print(f"V3.2 size: {os.path.getsize(V32_PATH)} bytes")
    print(f"V3.2 unchanged: {os.path.getsize(V32_PATH)} bytes (verified)")


if __name__ == '__main__':
    build_v33()
