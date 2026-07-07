# 01 — Dataset Silver Risk Response (Risk A)

**Risk ID:** A
**Reviewer attack:** "The 444-candidate dataset is GPT/silver labeled; the reported results may be a contingency artifact of the silver labeler rather than evidence of pipeline behavior."
**Severity:** High

---

## 1. Reviewer concern

The reviewer suspects that because all 444 candidates carry silver labels produced by a candidate-label-guess procedure (rather than human adjudication), the empirical results (BM25 retrieval, canonicalization gain, R4 strong_F1 = 0.4503, G_conservative_precision precision@20 = 0.45) may be an artifact of labeler regularities rather than a property of the retrieval-to-screening pipeline. The reviewer may ask whether the dataset lock, leakage audit, and group-split integrity are sufficient to defend against this risk.

## 2. What we agree with

We agree that the dataset is a **controlled silver diagnostic set**, not a gold benchmark. We agree that silver labels carry labeler-imposed regularities that could, in principle, inflate metrics or produce spurious shortcuts. We agree that no silver diagnostic can substitute for a human-audited gold benchmark when claiming general model validation. We do not contest that the silver label source (`candidate_label_guess`) is a structural limitation of every metric reported on this set.

## 3. Evidence we have

- **Dataset lock.** The SimClaim Strict Silver Diagnostic Set v1 is locked at SHA256 `13d6c66171cf54e1a456d5ef8674f00f91939aa79a60f0c65066f2a3ebe0a812` (448144 bytes, 444 rows, 36 columns, 111 groups). The lock document fixes row count, group count, label balance, `human_audited=False`, `gold_label` empty, `silver_label_source=candidate_label_guess`, and domain distribution.
- **Leakage audit.** A 12-check leakage audit (`experiments/leakage_audit_v1/audit_summary.md`) reports 12/12 PASS with strongest_concern=none. The audit covers train/test overlap, group leakage, label-prior shortcuts, and feature leakage.
- **Claim-only baseline.** `experiments/leakage_audit_v1/claim_only_baseline.json` reports claim-only strong_F1 = 0.2448, ratio to R4 = 0.5436, which is below the 0.8 warning threshold. This indicates R4 does not reduce to a claim-only shortcut on the silver labels.
- **Shuffled/title-only/metadata baselines.** The leakage audit additionally includes shuffled-evidence (46x collapse), title-only, and metadata-only controls, all of which fail to reproduce R4 performance.
- **Group split integrity.** All triples sharing a `logical_sample_id` are kept in the same split; no group straddles train/dev/test. The split uses the CSV `split` column, not random assignment.
- **Label balance.** Each of the 4 labels has exactly 111 candidates (one per group), preventing label-prior shortcuts from dominating metrics.

## 4. Evidence file

- `docs/dataset_version_lock_v3_17.md`
- `data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/strict_silver_max_candidates_v1.csv`
- `experiments/leakage_audit_v1/audit_summary.md`
- `experiments/leakage_audit_v1/claim_only_baseline.json`
- `experiments/metric_robustness_v1/classification_metrics_with_ci.csv`
- `reports/current_project_status_v3_17.md`

## 5. Safe response

We answer the reviewer as follows: the dataset is explicitly a controlled silver diagnostic set, not a gold benchmark. The dataset is locked (SHA256, row/group/label balance, `human_audited=False`, `gold_label` empty), the leakage audit passes 12/12 checks, the claim-only baseline sits at ratio 0.5436 (below the 0.8 warning threshold), and group-split integrity is enforced. These controls reduce — but do not eliminate — the risk that silver-labeler regularities inflate the metrics.

The safe empirical conclusion is therefore narrow: **the reported results support a retrieval-to-screening diagnostic on this controlled silver set, and do not support general model validation, gold-level performance claims, or claims that the system would transfer to human-adjudicated labels.** The human audit protocol is staged but not executed; until it is run, all silver-label metrics remain diagnostic-only.

## 6. Remaining limitation

- Silver labels are produced by `candidate_label_guess`; no human adjudication has been performed (`human_audited=False` for all 444 rows, `gold_label` empty for all 444 rows).
- The leakage audit checks structural shortcuts (overlap, group leakage, claim-only collapse, shuffled-evidence collapse) but cannot rule out subtle semantic regularities introduced by the silver labeler.
- All quantitative results (BM25 recall, canonicalizer oracle_recall, R4 strong_F1, queue precision) are conditional on the silver labels and may shift under human adjudication.
- The dataset covers only 6 domains with imbalanced counts (autonomous_driving=140 vs robotics=36); silver-labeler behavior may differ across domains.

## 7. Paper text to add

> "We emphasize that the SimClaim Strict Silver Diagnostic Set v1 is a controlled silver diagnostic set, not a gold benchmark. All 444 candidates carry `silver_label_source = candidate_label_guess`; `human_audited = False` for every row and `gold_label` is empty. We lock the dataset (SHA256 `13d6c66171cf54e1a456d5ef8674f00f91939aa79a60f0c65066f2a3ebe0a812`, 444 rows, 111 groups, 4 balanced labels) to prevent runtime modification. A 12-check leakage audit passes 12/12, and the claim-only baseline achieves strong_F1 = 0.2448 (ratio 0.5436 to R4, below the 0.8 warning threshold), indicating that R4 does not reduce to a claim-only shortcut on this silver set. These controls reduce but do not eliminate silver-labeler regularity risk. All quantitative results are therefore diagnostic, not benchmark-level, and may shift under human adjudication. The human audit protocol is staged but not executed (see response 04)."

## 8. What not to claim

| Unsafe wording (forbidden) | Why forbidden |
|---|---|
| "gold benchmark" | labels are silver (`candidate_label_guess`), `human_audited=False`, `gold_label` empty |
| "human-audited dataset" | human audit protocol staged, not executed; no `audit_agreement_summary.json` |
| "validated general detector" | silver diagnostic only; no cross-dataset or human-audited validation |
| "SOTA on simulation-claim screening" | no gold comparison; silver labels cannot anchor a SOTA claim |
| "the silver labels are correct" | silver labels are unverified guesses; correctness is not asserted |

---

*End of response 01.*
