# Leakage and Confidentiality Policy

**Date:** 2026-07-06
**Scope:** This policy defines which fields are forbidden in retrieval selection, evidence selection, ranking, and queue routing to prevent label leakage and protect confidentiality.

---

## Forbidden fields (must NOT be used in retrieval / evidence selection / ranking / queue routing)

The following fields are evaluation/audit-only. They must never be read by any component that selects, ranks, filters, or routes candidates:

| Field | Why forbidden |
|---|---|
| `true_label` | Ground-truth label. Using it in selection/ranking is label leakage. |
| `is_strong_action` | Derived from true_label. Label leakage. |
| `oracle_hit` | Indicates whether the selected evidence matches the oracle span. Using it in evidence selection defeats the purpose of unsupervised canonicalization. |
| `candidate_label_guess` | Silver label guess. Using it in selection/ranking is label leakage. |
| `final_label` | Adjudicated or derived final label. Label leakage. |
| `gold_label` | Gold adjudicated label (if/when available). Label leakage. |
| `human_audited` | Indicates whether a human reviewed this candidate. Using it in routing leaks audit status into the pipeline. |
| `evidence_text_sha256` | Hash of the real evidence text. Using it in selection enables fingerprinting and indirect label leakage (hashes may correlate with label distributions). |

## Allowed fields (may be used in retrieval / evidence selection / ranking / queue routing)

The following fields are safe to use in the pipeline:

- `claim_text` — the claim string (input to BM25 query and NLI pair)
- `candidate_id` — opaque identifier (no label information)
- `target_candidate_group_id` — for group-aware splitting only (no label information)
- `bm25_rank`, `bm25_score` — retrieval outputs (no label information)
- `chunk_text` — retrieved PDF chunk text (no label information)
- `sentence_text` — individual sentence from a chunk (no label information)
- NLI features (entailment / neutral / contradiction probabilities and derivatives) — model outputs, not labels
- Action-gap features (lexicon counts, TF-IDF overlap) — computed features, not labels
- `p_contra`, `p_strong`, `p_svm` — R4 classifier probability outputs (model outputs, not ground truth)
- `strong_action_flag` — derived from R4 prediction (not from true_label)
- `priority_score` — computed from R4 probabilities (not from true_label)
- `selector_score` — overlap score from canonicalization (not from labels)

## Enforcement rules

1. **Evidence canonicalization (`run_r4_evidence_canonicalization_v1.py`) must NOT read** `true_label`, `is_strong_action`, `oracle_hit`, `candidate_label_guess`, `final_label`, `gold_label`, `human_audited`, or `evidence_text_sha256`. The selector uses only `claim_text` and `sentence_text` token overlap.

2. **R4 screening (`run_canonicalized_review_queue_v1.py`) must NOT read** `true_label`, `is_strong_action`, `oracle_hit`, `candidate_label_guess`, `final_label`, `gold_label`, `human_audited`, or `evidence_text_sha256` for routing. R4 reads only NLI features and action-gap features. `true_label` is read ONLY in the final evaluation block for metric computation, never in the routing block.

3. **Risk ranking (`run_canonicalized_risk_ranking_v1.py`) must NOT read** `true_label`, `is_strong_action`, `oracle_hit`, `candidate_label_guess`, `final_label`, `gold_label`, `human_audited`, or `evidence_text_sha256` for ranking. The ranking formula uses only `p_strong`, `p_contra`, `entropy`, `strong_action_flag`, `selector_score`, and `selected_rank`.

4. **Review queue routing must NOT read** any forbidden field. Queue ordering uses only `priority_score` or the selected ranking variant's score.

5. **Evaluation/audit block** may read all fields, including forbidden fields, because it computes metrics against ground truth. The evaluation block must be physically separated from the selection/ranking/routing blocks in the code (separate functions, separate code paths).

## Confidentiality addendum

In addition to leakage prevention, the forbidden fields `evidence_text_sha256` and any field containing raw evidence text must not be exposed in released review queues. Review queues released to human reviewers may contain `candidate_id`, `selected_evidence` (the canonicalized sentence — but see `data_release_policy.md` for confidentiality constraints on real text), `priority_score`, and `pred_label`. They must NOT contain `true_label`, `oracle_hit`, or `human_audited` in the version given to reviewers (to avoid biasing the review).

## Audit

Any script that touches retrieval, evidence selection, R4 screening, ranking, or queue routing should be auditable for forbidden-field usage. A simple grep for forbidden field names in the selection/ranking/routing code paths should return no matches outside the evaluation block.
