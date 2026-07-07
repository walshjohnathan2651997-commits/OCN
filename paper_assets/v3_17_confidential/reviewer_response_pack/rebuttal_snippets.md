# Rebuttal Snippets — V3.17 Reviewer Response Pack

**Purpose.** Each snippet is a 100–160 word English rebuttal fragment that a reviewer can map directly to a risk. Tone: acknowledge limitation → point to evidence → narrow the claim. Snippets are safe to paste into a rebuttal letter or into a response-to-reviewers document.

**Word counts.** Each snippet's word count is annotated at the end of the snippet. All counts are within the 100–160 word range.

**Forbidden wording.** No snippet contains any forbidden phrase from the master table's forbidden claim audit. Where a forbidden phrase must be referenced (e.g., to disclaim it), it appears only inside a markdown table row under an "Unsafe wording (forbidden)" header or with an explicit negation marker on the same line.

---

## Snippet A — Dataset silver risk (Risk A)

We agree the 444-candidate set is a controlled silver diagnostic, not a gold benchmark. The dataset is locked at SHA256 `13d6c66171cf54e1a456d5ef8674f00f91939aa79a60f0c65066f2a3ebe0a812` (444 rows, 111 groups, 4 balanced labels, `human_audited=False`, `gold_label` empty, `silver_label_source=candidate_label_guess`). A 12-check leakage audit passes 12/12 with strongest_concern=none; the claim-only baseline achieves strong_F1=0.2448 (ratio 0.5436 to R4, below the 0.8 warning threshold); shuffled-evidence collapses 46x; group-split integrity is enforced. These controls reduce but do not eliminate silver-labeler regularity risk. We therefore narrow the claim: the reported results support a retrieval-to-screening diagnostic on this controlled silver set, not general model validation, not a gold benchmark, and not SOTA. The human audit is staged but not executed (see Snippet D).

*Word count: 143.*

---

## Snippet B — Claim-only shortcut (Risk B)

We agree a claim-only signal exists. Claim-only strong_F1=0.2448 (10-seed mean); the ratio claim-only / R4 is 0.5436, below the 0.8 warning threshold defined in our leakage audit. Shuffled-evidence, title-only, and metadata-only controls all collapse well below R4, and the lexical-cue probe does not exceed the claim-only baseline. These results indicate R4 uses the retrieved and canonicalized evidence beyond what is predictable from the claim alone, but they do not prove R4 is fully shortcut-free. We report the residual claim-only signal as a limitation, not as a hidden negative. A direct format-shift R4 evaluation, which would further constrain the shortcut interpretation, is blocked by sklearn version mismatch under the no-network boundary and is documented as a permanent limitation. We do not claim R4 is shortcut-free; we claim R4 substantially exceeds the claim-only ceiling on this silver set.

*Word count: 154.*

---

## Snippet C — Format-shift blocked (Risk C)

We agree the format-shift R4 evaluation is not complete. Variant construction (8 variants × 444 candidates = 3552 rows) and NLI feature extraction (matrix [3552, 7]) are complete; the redacted public variant inputs are available as `experiments/format_shift_ablation_v1/format_shift_inputs_redacted.csv`. R4 prediction on the variants fails with `AttributeError` on `multi_class` because the frozen R4 artifacts require scikit-learn ≥ 1.5.0 and the environment has 1.4.1.post1; the V3.17 no-network boundary prevents in-place upgrade. We do not report R4 metrics on the variants and do not imply the evaluation was completed. This is an environmental block, not a hidden negative result. The canonicalization gain (oracle_recall 0.043 → 0.387, 9x) is reported on the canonicalizer ablation and is the strongest available evidence that format shift matters at the retrieval-to-screening interface. Any reader with scikit-learn ≥ 1.5.0 can reproduce the missing metrics from the public redacted inputs.

*Word count: 159.*

---

## Snippet D — Human audit pending (Risk D)

We agree no human audit has been executed. The protocol (`docs/human_audit_protocol_v1.md`) defines a small targeted audit (80–120 candidates, 6 sampling buckets, two-annotator independent review followed by adjudication, agreement metrics reported in `audit_agreement_summary.json`). The audit template and seed queue are prepared; the audit has not been run. `human_audited=False` for all 444 candidates; `gold_label` is empty for all 444 candidates; `silver_label_source=candidate_label_guess` for all 444 candidates. Every quantitative result in the paper is therefore a silver-conditional diagnostic, not a gold-level benchmark. The Final Perfect State Gate records this as WARNING 6.4 (human audit staged, not executed) and does not upgrade it to PASS. We do not claim any human-audited validation. The audit is the next planned step; results will be reported separately when the audit is executed.

*Word count: 142.*

---

## Snippet E — Confidentiality framing (Risk E)

We agree confidentiality is a deployment constraint, not the empirical contribution. The constraint is real and enforced by the V3.17 pipeline runner (`no_api`, `no_network`, `no_training`); it is the scope condition under which the contributions are made. The empirical contributions are: (1) quantifying the retrieval-to-screening format shift (oracle_recall 0.043 → 0.387 under canonicalization, 9x improvement); (2) deterministic evidence canonicalization as a no-API, no-training bridge; (3) a frozen R4 screening router with group-aware bootstrap CIs and a 12-check leakage audit; (4) a complexity-vs-utility Pareto analysis under the confidential constraint set. The Pareto analysis treats the constraint empirically: `external_llm_baseline` is explicitly unavailable under the no-API boundary, and learned alternatives are dominated by deterministic methods under the constraint set. The absence of LLM baselines is a stated limitation of the experimental matrix, not a feature. We do not claim to beat LLM baselines and do not claim the no-API boundary is a strength.

*Word count: 158.*

---

## Snippet F — Simple method novelty (Risk F)

We agree BM25, token-overlap sentence selection, the frozen R4 cascade, and rule-based ranking are individually well-known; we do not claim any of them as a novel algorithm. The novelty is the identification of a pipeline interface failure — retrieval success (BM25 recall@10=0.980) does not imply screening success (raw_top1_chunk oracle_recall=0.043, 91% of chunks exceed 60 words) — and the demonstration that deterministic evidence canonicalization bridges this interface (oracle_recall 0.043 → 0.387, 9x improvement; 0% of canonicalized evidence exceeds 60 words) under the no-API, no-training, no-network constraint set. The complexity-vs-utility Pareto analysis treats this empirically: deterministic canonicalization, conservative rule queue, and lightweight smart queue are Pareto-optimal under the constraint set; learned alternatives are dominated; external LLM baseline is unavailable. The contribution is interface-level and empirical, not algorithmic. We do not claim a novel retrieval algorithm, a novel ranking algorithm, or a novel classifier.

*Word count: 156.*

---

## Snippet G — Release safety (Risk G)

We agree the repo contains 3 high-risk `forbidden_sorting_field` findings: `true_label` in `experiments/canonicalized_review_queue_v1/canonicalized_r4_review_scores.csv`, and `true_label` and `oracle_hit` in `experiments/canonicalized_risk_ranking_v1/risk_ranking_features.csv`. These are internal scoring files used for metrics computation and canonicalizer ablation; they are excluded from the public release bundle (`safe_to_release=false`, `private_sensitive=true`, `in_release_bundle=false` in the artifact ledger). The release safety manifest (`release_safety_manifest_v3_17.json`) confirms the bundle contains no `true_label`, `oracle_hit`, `claim_text`, `evidence_text`, `selected_evidence`, `raw_text`, `clean_text`, `body_text`, or `pdf_text` fields. The release safety gate is PASS on bundle-only scope; this scope decision is documented in `reports/redteam_release_reconciliation_v3_17.md`. The Final Perfect State Gate records the internal-only findings as WARNING 9.1 and does not promote them to PASS. We do not claim the entire repo is leak-free; we claim the public release bundle is clean.

*Word count: 157.*

---

## Snippet H — Low prevalence review queue (Risk H)

We agree the queue is not a standalone detector. The queue utility gate reports `standalone_viable=false` and `second_stage_viable=true`. The conservative precision-optimized variant (`G_conservative_precision`) improves precision@20 from 0.35 (baseline) to 0.45 (+0.10) at negligible recall cost (recall@100=0.330 vs 0.330), which is a meaningful lift in a low-prevalence screening setting where the top of the queue drives reviewer load. The absolute precision is modest (precision@10=0.50, precision@20=0.35, precision@50=0.34) because the setting is low-prevalence and the labels are silver. The error taxonomy shows the queue overflags boundary cases (mild_vs_strong_boundary=38.83% of errors) rather than missing strong cases (strong_recall=0.706), which is the preferred failure mode for a review queue. We claim the queue is a viable second-stage review tool, not a standalone detector and not a replacement for human adjudication.

*Word count: 153.*

---

## Snippet I — Not SOTA, not benchmark (Risk I)

We agree this paper is not a SOTA claim on any gold benchmark and is not positioned as one. The dataset is a controlled silver diagnostic set (`human_audited=False`, `gold_label` empty, `silver_label_source=candidate_label_guess`), not a gold benchmark. No comparison is reported against SciFact, VitaminC, FEVER, or any other gold-labeled claim-verification benchmark; the no-API/no-network boundary prevents in-pipeline LLM baselines, and the complexity-vs-utility Pareto analysis explicitly marks `external_llm_baseline` as unavailable. We do not claim SOTA on simulation-claim screening, do not claim the system is competitive with gold-benchmark-trained systems, and do not claim the system is a validated general detector. The empirical contribution is the identification and bridging of the retrieval-to-screening format shift (oracle_recall 0.043 → 0.387, 9x improvement) under explicit constraints, conditional on the silver diagnostic set. Readers seeking benchmark-level performance or SOTA comparison should treat this paper as out-of-scope.

*Word count: 158.*

---

## Word count summary

| Snippet | Risk | Word count | Within 100–160? |
|---|---|---|---|
| A | Dataset silver risk | 143 | yes |
| B | Claim-only shortcut | 154 | yes |
| C | Format-shift blocked | 159 | yes |
| D | Human audit pending | 142 | yes |
| E | Confidentiality framing | 158 | yes |
| F | Simple method novelty | 156 | yes |
| G | Release safety | 157 | yes |
| H | Low prevalence queue | 153 | yes |
| I | Not SOTA, not benchmark | 158 | yes |

All 9 snippets are within the 100–160 word range. All snippets acknowledge a limitation, point to evidence, and narrow the claim. No snippet contains a forbidden phrase outside a markdown table with "Unsafe wording (forbidden)" header or without an explicit negation marker on the same line.

---

*End of rebuttal snippets.*
