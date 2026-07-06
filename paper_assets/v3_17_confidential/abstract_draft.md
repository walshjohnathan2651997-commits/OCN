# Abstract Draft — V3.17 Confidential Lightweight

**Authority:** This is the frozen abstract draft for V3.17. All
quantitative claims are sourced from `experiments/` files and the
result narrative freeze. Forbidden wording (see
`docs/safe_claims_dictionary_v3_17.md`) is excluded by construction.

**Title candidate (preferred):** Local Evidence Canonicalization for
Confidential Simulation-Claim Review Queues

**Alternative title:** Retrieval-to-Screening Format Shift in Local
PDF Claim Review

---

## Abstract

Simulation-claim review requires screening claims about autonomous
driving, policy simulation, digital twins, cyber defense, multi-agent
reinforcement learning, and robotics against source PDF evidence. In
confidential deployment settings, API egress, network access, and new
model training are prohibited, so all retrieval, screening, and
ranking must run locally and remain auditable.

We study this problem on a 444-candidate controlled silver diagnostic
set (111 groups × 4 labels: supported, mild_scope_overclaim,
strong_action_overclaim, contradiction_candidate). The dataset is
source-traceable but not gold and not human-audited
(`human_audited=False` for all rows); results are diagnostic, not
benchmark-level validation.

We identify a retrieval-to-screening format shift: raw BM25 PDF chunks
are too long and noisy to match screening-format evidence
(oracle_recall = 0.043, 91% of chunks exceed 60 words). To bridge
this gap without API calls or training, we propose deterministic
evidence canonicalization that selects the best sentence from BM25
top-5 chunks by token overlap with the claim. The best canonicalizer
(`best_sentence_top5_overlap`) raises oracle_recall to 0.387 (9x
improvement) and produces screening-format-length evidence (0% of
selected evidence exceeds 60 words).

We then evaluate a frozen R4 screening router (strong_F1 = 0.4503,
95% CI [0.4086, 0.4833]) and a conservative precision-optimized
review queue (`G_conservative_precision`, precision@20 = 0.45). The
queue augments human review; it is not a standalone detector and does
not replace adjudication. A 12-check leakage audit (11 PASS + 1 SKIP)
finds no significant shortcuts or label contingencies: claim-only
strong_F1 = 0.2448 (ratio to R4 = 0.54, below the 0.8 warning
threshold), and shuffled evidence collapses overlap by 46x.

Limitations: silver labels (not gold), no completed human audit, six
domains only, sentence/window BM25 on the real PDF corpus is blocked
(missing corpus file), and the format-shift R4 evaluation is blocked
by a scikit-learn version mismatch. The system is not a validated
general detector, not SOTA, and not an automatic peer reviewer.

---

## Required structure check

| Required element | Present? | Where |
|---|---|---|
| Problem | yes | sentence 1 |
| Confidential / no-API setting | yes | sentence 2 |
| Controlled silver diagnostic | yes | sentence 3 |
| Retrieval-to-screening format shift | yes | sentence 5 |
| Evidence canonicalization | yes | sentence 6 |
| Second-stage review queue | yes | sentence 8 |
| Limitations | yes | final paragraph |

## Forbidden wording check

| Forbidden phrase | Present? |
|---|---|
| gold benchmark | no |
| SOTA / state-of-the-art | no |
| automatic peer review | no |
| general detector (as positive claim) | no |
| human-audited benchmark | no |
| full CESE-OCN validated | no |
| outperforms LLMs | no |

---

## Source file traceability

| Metric | Source file |
|---|---|
| oracle_recall = 0.043 (raw_top1_chunk) | `experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv` |
| oracle_recall = 0.387 (best_sentence_top5_overlap) | `experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv` |
| 91% chunks > 60 words | `experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv` |
| 0% selected evidence > 60 words | `experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv` |
| strong_F1 = 0.4503, CI [0.4086, 0.4833] | `experiments/metric_robustness_v1/classification_metrics_with_ci.csv` |
| precision@20 = 0.45 (G_conservative_precision) | `experiments/canonicalized_risk_ranking_v1/risk_ranking_results_by_variant.csv` |
| 12 checks (11 PASS + 1 SKIP) | `experiments/leakage_audit_v1/audit_summary.md` |
| claim-only strong_F1 = 0.2448 | `experiments/leakage_audit_v1/claim_only_baseline.json` |
| shuffled ratio = 46x | `experiments/leakage_audit_v1/shuffled_evidence_baseline.json` |
