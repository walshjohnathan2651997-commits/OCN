# Table 4 — Canonicalizer Ablation

| Selector | oracle_recall | mean_overlap | pct_long_gt60 | median_n_words |
|---|---|---|---|---|
| raw_top1_chunk | 0.043 | 0.199 | 0.910 | 70 |
| cleaned_top1_chunk | 0.043 | 0.199 | 0.910 | 70 |
| first_sentence_top1 | 0.027 | 0.086 | 0.059 | 18 |
| best_sentence_top1_overlap | 0.221 | 0.319 | 0.052 | 23 |
| **best_sentence_top5_overlap** | **0.387** | **0.524** | **0.000** | 23 |
| three_sentence_window_top5 | 0.203 | 0.376 | 0.304 | 52 |
| sentence_bm25_top1 | 0.000 | 0.000 | 0.000 | 0 |
| window_bm25_top1 | 0.000 | 0.000 | 0.000 | 0 |

`sentence_bm25_top1` and `window_bm25_top1` are blocked (missing real PDF corpus file); they are not included in the main analysis.

`best_sentence_top5_overlap` achieves 9x oracle_recall improvement over `raw_top1_chunk` (0.043 → 0.387) and produces screening-format-length evidence (0% exceed 60 words).
All canonicalizers are unsupervised, deterministic, and use only `claim_text` and retrieved text — no labels, no oracle, no API calls.

[Source: experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv]
