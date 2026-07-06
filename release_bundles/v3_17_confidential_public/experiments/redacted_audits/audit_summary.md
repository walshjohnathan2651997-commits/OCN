# Leakage Audit Summary

Generated: 2026-07-06T05:32:46.122336+00:00

## Check Results

| # | Check | Status | Key Metric |
|---|-------|--------|------------|
| 1 | Claim-only baseline | pass | ratio=0.720156 |
| 2 | Title-only retrieval | pass | mean_overlap=0.023932 |
| 3 | Metadata-only retrieval | pass | purity=0 |
| 4 | Label lexical cues | pass | max_cues=0 |
| 5 | Group split integrity | pass | cross_groups=0 |
| 6 | No oracle in selector | pass |  |
| 7 | No label in queue sorting | pass |  |

## Forbidden Fields (selector)

- candidate_label_guess
- final_label
- gold_label
- human_audited
- oracle_hit
- true_label

## Forbidden Fields (queue sorting)

- candidate_label_guess
- evidence_text
- evidence_text_sha256
- final_label
- gold_label
- human_audited
- is_strong_action
- oracle_hit
- true_label
