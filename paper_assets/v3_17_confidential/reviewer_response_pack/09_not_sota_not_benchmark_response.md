# 09 — Not SOTA, Not Benchmark Response (Risk I)

**Risk ID:** I
**Reviewer attack:** "You do not compare against SOTA on any gold benchmark, you do not report results on SciFact/VitaminC/FEVER, and you do not establish that the system is competitive with prior work. This is not a benchmark paper."
**Severity:** High

---

## 1. Reviewer concern

The reviewer notes that the paper reports no comparison against SOTA on any gold benchmark, no results on standard claim-verification benchmarks (SciFact, VitaminC, FEVER), and no head-to-head comparison with prior retrieval-augmented screening systems. The reviewer may suspect that the authors are avoiding comparison because the system is not competitive, or that the paper is being mis-positioned as a benchmark paper without benchmark-level evidence.

## 2. What we agree with

We agree that the paper is not a SOTA claim on any gold benchmark. We agree that no comparison is reported against SciFact, VitaminC, FEVER, or any other standard claim-verification benchmark. We agree that the system is not validated as a general detector and is not competitive with gold-benchmark-trained systems. We do not contest that a reviewer is entitled to ask why no gold-benchmark comparison is reported and to treat the absence as a scope restriction.

## 3. Evidence we have

- **Dataset is silver, not gold.** `docs/dataset_version_lock_v3_17.md` records `human_audited = False` for all 444 rows, `gold_label` empty, `silver_label_source = candidate_label_guess`. The dataset is a controlled silver diagnostic set, not a gold benchmark.
- **No gold-benchmark comparison.** The experimental matrix does not include SciFact, VitaminC, FEVER, or any other gold-labeled claim-verification benchmark. The complexity-vs-utility ablation (`experiments/complexity_vs_utility_ablation_v1/method_pareto_table.csv`) explicitly marks `external_llm_baseline` as unavailable under the no-API boundary.
- **Manuscript framing.** The manuscript states verbatim: "This is a controlled silver diagnostic study, not a gold benchmark." and "We explicitly do not claim a gold benchmark, a human-audited dataset, SOTA on simulation-claim screening, an automatic peer reviewer, a validated general detector, or full CESE-OCN neural architecture validation."
- **Pipeline scope.** The system is a second-stage review queue generator, not a standalone detector (`standalone_viable = false`). The empirical contribution is the retrieval-to-screening format shift and its deterministic bridging, not benchmark-level performance.
- **Leakage audit.** The 12-check leakage audit is structural (overlap, group leakage, claim-only collapse, shuffled-evidence collapse), not a benchmark comparison. It establishes that the silver-label results are not trivial shortcuts, not that they are SOTA.
- **Final gate status.** The Final Perfect State Gate does not include any SOTA or benchmark-comparison check; the gate is READY_WITH_LIMITATIONS (PASS=40, WARNING=3, BLOCKED=1, FAIL=0), not a benchmark-validation gate.

## 4. Evidence file

- `docs/dataset_version_lock_v3_17.md`
- `experiments/complexity_vs_utility_ablation_v1/method_pareto_table.csv`
- `experiments/leakage_audit_v1/audit_summary.md`
- `paper_assets/v3_17_confidential/submission_manuscript_v1.md` (§3, §4)
- `reports/final_perfect_state_gate_v3_17.json`

## 5. Safe response

We answer the reviewer as follows: this paper is not a SOTA claim on any gold benchmark and is not positioned as one. The dataset is a controlled silver diagnostic set (`human_audited = False`, `gold_label` empty), not a gold benchmark. No comparison is reported against SciFact, VitaminC, FEVER, or any other gold-labeled claim-verification benchmark, because the system is not trained or evaluated on gold labels and the no-API/no-network boundary prevents in-pipeline LLM baselines. The empirical contribution is the identification and bridging of the retrieval-to-screening format shift (oracle_recall 0.043 → 0.387, 9x improvement) under explicit constraints, not benchmark-level performance. The manuscript states this verbatim and does not claim SOTA, gold benchmark, or validated general detector status.

The safe empirical conclusion is therefore narrow: **the paper is a controlled silver diagnostic study of retrieval-to-screening format shift, not a SOTA paper and not a benchmark paper. We do not claim SOTA on any benchmark, we do not claim the system is competitive with gold-benchmark-trained systems, and we do not claim the system is a validated general detector. The contribution is the interface-level finding and the deterministic bridge, conditional on the silver diagnostic set and the no-API/no-network/no-training constraint set.**

## 6. Remaining limitation

- No gold-benchmark comparison (SciFact, VitaminC, FEVER, etc.) is reported; the system is not validated against gold labels.
- No SOTA claim is supportable; the silver-label metrics (strong_F1 = 0.4503) are not comparable to gold-benchmark metrics in the literature.
- The system is not a validated general detector; results are conditional on the 6-domain silver diagnostic set.
- The no-API/no-network boundary prevents LLM baselines; a less restrictive setting might allow stronger baselines that dominate the deterministic pipeline.
- The paper is scope-restricted to the retrieval-to-screening format shift; it does not claim coverage of the full claim-verification problem space.

## 7. Paper text to add

> "We clarify the scope of this paper. This is a controlled silver diagnostic study, not a gold benchmark, not a SOTA claim, and not a benchmark paper. The dataset is silver (`human_audited = False`, `gold_label` empty, `silver_label_source = candidate_label_guess`); no comparison is reported against SciFact, VitaminC, FEVER, or any other gold-labeled claim-verification benchmark. The no-API/no-network boundary prevents in-pipeline LLM baselines; the complexity-vs-utility Pareto analysis explicitly marks `external_llm_baseline` as unavailable. We do not claim SOTA on simulation-claim screening, do not claim the system is competitive with gold-benchmark-trained systems, and do not claim the system is a validated general detector. The empirical contribution is the identification and bridging of the retrieval-to-screening format shift (oracle_recall 0.043 → 0.387, 9x improvement) under explicit constraints, conditional on the silver diagnostic set. Readers seeking benchmark-level performance or SOTA comparison should treat this paper as out-of-scope."

## 8. What not to claim

| Unsafe wording (forbidden) | Why forbidden |
|---|---|
| "SOTA on simulation-claim screening" | no gold comparison; silver labels; no SOTA claim is supportable |
| "state-of-the-art" | no gold-benchmark comparison; not a SOTA paper |
| "gold benchmark" | silver diagnostic only; `human_audited=False`; `gold_label` empty |
| "validated general detector" | silver-conditional diagnostics only; no cross-dataset validation |
| "competitive with prior work on SciFact/VitaminC/FEVER" | no comparison is reported; not a benchmark paper |
| "automatic peer reviewer" | queue is second-stage; does not replace human adjudication |

---

*End of response 09.*
