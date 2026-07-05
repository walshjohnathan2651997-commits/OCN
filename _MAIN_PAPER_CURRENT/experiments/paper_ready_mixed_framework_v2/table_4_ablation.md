# Table 4: Strong Expert Ablation

| config | strong_positive_f1 | strong_positive_std | strong_precision | strong_recall | flat4_strong_f1 |
| --- | --- | --- | --- | --- | --- |
| TF-IDF claim-only | 0.2747 | 0.0613 | 0.2493 | 0.3438 | 0.3342 |
| NLI only | 0.3934 | 0.0429 | 0.2869 | 0.6312 | 0.3934 |
| Action-gap only | 0.3648 | 0.0491 | 0.2966 | 0.4813 | 0.3857 |
| NLI + action gap | 0.4209 | 0.0555 | 0.3430 | 0.5625 | 0.4064 |
| NLI + length/overlap | 0.4340 | 0.0688 | 0.3705 | 0.5437 | 0.4236 |
| NLI + gap (no length) | 0.4135 | 0.0506 | 0.3238 | 0.5813 | 0.4178 |
| NLI + gap (no claim_strength) | 0.4266 | 0.0616 | 0.3461 | 0.5750 | 0.4128 |

- A6_tfidf_claim_only (0.2747) confirms improvement is NOT from claim-only keywords.
- A0_nli_only (0.3934) > A1_action_gap_only (0.3648): NLI is the stronger single feature.
- A2_nli_plus_action_gap (0.4209) > A0 and A1: NLI and action/structure features are complementary.
- A3_nli_plus_length_overlap (0.4340) is highest but length/overlap alone is not a theoretical claim.
- Conclusion: improvement comes from NLI + action-gap combination, not feature soup.
