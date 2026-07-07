# 05 — Confidentiality Framing Response (Risk E)

**Risk ID:** E
**Reviewer attack:** "Why is 'confidentiality' emphasized throughout the paper? Is this a narrative device to avoid comparing with stronger LLM baselines, or to dress up an engineering constraint as a scientific contribution?"
**Severity:** Medium

---

## 1. Reviewer concern

The reviewer suspects that the repeated emphasis on confidentiality (`no_api`, `no_network`, `no_training`) is a rhetorical move to (a) avoid comparing the pipeline against stronger LLM-based baselines (e.g., GPT-4, DeepSeek-V3, Claude), (b) reframe a deployment-engineering constraint as if it were an empirical contribution, or (c) lower the bar for what counts as a methodological result. The reviewer may ask the authors to either drop the confidentiality framing or to justify why it deserves first-class status in the empirical narrative.

## 2. What we agree with

We agree that confidentiality is a deployment constraint, not the empirical contribution. We agree that emphasizing a deployment constraint as if it were a scientific contribution would be misleading. We agree that the absence of LLM baselines is a limitation of the experimental matrix, not a feature. We do not contest that a reviewer is entitled to ask why LLM baselines are absent and to treat the no-API boundary as a scope restriction rather than a contribution.

## 3. Evidence we have

- **Constraint is real and enforced.** `configs/v3_17_paths.yaml` and `scripts/run_v3_17_confidential_pipeline.py` enforce `no_api`, `no_network`, `no_training` boundaries. The pipeline runner rejects any mode that requires API egress or model training.
- **Constraint is not the contribution.** The manuscript's stated contributions are: (1) quantifying the retrieval-to-screening format shift, (2) deterministic evidence canonicalization as a no-API bridge, (3) a frozen R4 screening router with group-aware bootstrap CIs and a 12-check leakage audit, (4) a complexity-vs-utility Pareto analysis under the confidential constraint set. Confidentiality is the *scope condition* under which these contributions are made, not itself the contribution.
- **Complexity-vs-utility Pareto analysis.** `experiments/complexity_vs_utility_ablation_v1/method_pareto_table.csv` reports that `deterministic_canonicalization`, `conservative_rule_queue`, and `lightweight_smart_queue` are Pareto-optimal; learned alternatives are dominated under the constraint set; `external_llm_baseline` is unavailable (no-API). The Pareto analysis is the empirical treatment of the constraint, not a rhetorical appeal to it.
- **Manuscript framing.** The manuscript states verbatim: "Confidentiality is a deployment constraint, not the empirical contribution." This sentence appears in §5 (Problem Setting) and is repeated in the abstract framing.
- **LLM baseline status.** DeepSeek V3 LLM baseline execution was authorized for a small-sample pilot (N ≤ 200, see project memory) but is not part of this submission; the submission does not claim LLM comparison results.

## 4. Evidence file

- `configs/v3_17_paths.yaml`
- `scripts/run_v3_17_confidential_pipeline.py`
- `experiments/complexity_vs_utility_ablation_v1/method_pareto_table.csv`
- `experiments/complexity_vs_utility_ablation_v1/method_comparison_metrics.csv`
- `paper_assets/v3_17_confidential/submission_manuscript_v1.md` (§5, abstract)

## 5. Safe response

We answer the reviewer as follows: confidentiality is a deployment constraint, not the empirical contribution. The constraint is real and enforced by the pipeline runner; it is the scope condition under which the contributions are made, not the contribution itself. The main empirical contributions are (a) the identification and quantification of the retrieval-to-screening format shift (oracle_recall 0.043 → 0.387 under canonicalization, 9x improvement), (b) deterministic evidence canonicalization as a no-API, no-training bridge, and (c) a complexity-vs-utility Pareto analysis that treats the constraint set empirically rather than rhetorically. The absence of LLM baselines is a stated limitation of the experimental matrix; the Pareto analysis explicitly marks `external_llm_baseline` as unavailable under the no-API boundary.

The safe empirical conclusion is therefore narrow: **the contribution is the retrieval-to-screening format shift and its deterministic bridging under explicit no-API, no-network, no-training boundaries. Confidentiality is the scope condition, not the contribution. The absence of LLM baselines is a limitation, not a feature.**

## 6. Remaining limitation

- No LLM baseline (GPT-4, DeepSeek-V3, Claude, etc.) is included in this submission; the no-API boundary prevents in-pipeline LLM calls.
- A small-sample DeepSeek V3 pilot (N ≤ 200) was authorized separately but is not part of this submission; the submission does not claim LLM comparison results.
- The confidentiality framing is meaningful only for deployments that actually enforce no-API/no-network; readers operating in less restrictive settings may find the Pareto frontier shifts toward learned or LLM-based methods.
- The complexity-vs-utility Pareto analysis is conditional on the silver diagnostic set and on the V3.17 constraint set; it is not a universal ranking of methods.

## 7. Paper text to add

> "We clarify the role of confidentiality in this paper. Confidentiality is a deployment constraint, not the empirical contribution. The constraint is real and enforced by the V3.17 pipeline runner (`no_api`, `no_network`, `no_training`); it is the scope condition under which the contributions are made. The empirical contributions are: (1) quantifying the retrieval-to-screening format shift (oracle_recall 0.043 → 0.387 under canonicalization, 9x improvement), (2) deterministic evidence canonicalization as a no-API, no-training bridge, (3) a frozen R4 screening router with group-aware bootstrap CIs and a 12-check leakage audit, and (4) a complexity-vs-utility Pareto analysis under the confidential constraint set. The Pareto analysis treats the constraint empirically: `external_llm_baseline` is explicitly marked unavailable under the no-API boundary, and learned alternatives are dominated by deterministic methods under the constraint set. The absence of LLM baselines is a limitation of the experimental matrix, not a feature of the system."

## 8. What not to claim

| Unsafe wording (forbidden) | Why forbidden |
|---|---|
| "confidentiality is a contribution" | confidentiality is a deployment constraint, not the empirical contribution |
| "we beat LLM baselines" | no LLM baseline is included; no comparison is possible |
| "LLM baselines are unnecessary" | absence is a limitation, not a finding |
| "the no-API boundary is a strength" | it is a scope condition; whether it is a strength depends on deployment context |
| "the system is the only valid approach under confidentiality" | Pareto analysis is conditional on this silver set and constraint set; not a universal claim |

---

*End of response 05.*
