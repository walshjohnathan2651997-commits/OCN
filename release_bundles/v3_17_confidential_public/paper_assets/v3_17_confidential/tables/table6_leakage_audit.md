# Table 6 — Leakage Audit

**Overall status: PASS.** Strongest leakage concern: none.

| # | Check | Status | Key metric |
|---|---|---|---|
| 1 | Claim-only baseline (TF-IDF+LR, GroupKFold) | pass | strong_F1=0.2448 (ratio to R4=0.5436, below 0.8 warning) |
| 2 | Empty evidence baseline | pass | correct_overlap=0.361 |
| 3 | Shuffled evidence baseline | pass | correct=0.361, shuffled=0.008 (46x collapse) |
| 4 | Title-only retrieval | pass | mean_overlap=0.043 |
| 5 | Metadata-only retrieval | pass | purity=0.25 |
| 6 | Lexical overlap by label | pass | overlap_ratio=1.344 |
| 7 | Cue words by label | pass | max_cue_ratio=1.608 |
| 8 | Label lexical cues | pass | max_cues=0 |
| 9 | Group split integrity | pass | cross_groups=0 |
| 10 | Generation policy distribution | pass | max_concentration=0.25 |
| 11 | No oracle in selector | pass | — |
| 12 | No label in queue sorting | pass | — |

**Forbidden fields (selector):** `candidate_label_guess`, `final_label`, `gold_label`, `human_audited`, `oracle_hit`, `true_label`.

**Forbidden fields (queue sorting):** the same plus `evidence_text`, `evidence_text_sha256`, `is_strong_action`.

Silver labels (`candidate_label_guess`) are used as `true_label` for audit metrics only; the audit checks for shortcuts and label contingencies, not for gold-level validity.

[Source: experiments/leakage_audit_v1/audit_summary.md; experiments/leakage_audit_v1/claim_only_baseline.json]
