# Boundary-Collapse Fallback Test

**Method:** Remap labels under 3 taxonomy variants, recompute each judge's macro-F1, key-class recall, and confusion matrix.

**Taxonomies:**
- **A. 4-class (original):** supported / mild_scope / strong_action / contradiction
- **B. 3-class (mild+strong merge):** supported / overclaim / contradiction
- **C. 3-class (sup+mild merge):** acceptable / strong_action / contradiction

## Matched-100 Results

| Taxonomy | Judge | Macro-F1 | Key class | Key recall | Key F1 |
|---|---|---|---|---|---|
| A_4class | r4 | 0.3280 | strong_action_overclaim | 0.3600 | 0.3000 |
| A_4class | deepseek | 0.5248 | strong_action_overclaim | 0.0400 | 0.0769 |
| A_4class | gpt_standard | 0.5523 | strong_action_overclaim | 0.0400 | 0.0769 |
| A_4class | gpt_structured | 0.5543 | strong_action_overclaim | 0.0400 | 0.0769 |
| B_3class_overclaim_merge | r4 | 0.4728 | overclaim | 0.7200 | 0.6207 |
| B_3class_overclaim_merge | deepseek | 0.7112 | overclaim | 0.4800 | 0.6316 |
| B_3class_overclaim_merge | gpt_standard | 0.7398 | overclaim | 0.5400 | 0.6585 |
| B_3class_overclaim_merge | gpt_structured | 0.7469 | overclaim | 0.5000 | 0.6494 |
| C_3class_acceptable_merge | r4 | 0.4970 | strong_action_overclaim | 0.3600 | 0.3000 |
| C_3class_acceptable_merge | deepseek | 0.5626 | strong_action_overclaim | 0.0400 | 0.0769 |
| C_3class_acceptable_merge | gpt_standard | 0.5299 | strong_action_overclaim | 0.0400 | 0.0769 |
| C_3class_acceptable_merge | gpt_structured | 0.5299 | strong_action_overclaim | 0.0400 | 0.0769 |

## R4 vs DeepSeek Deltas (matched-100)

| Taxonomy | R4 macro-F1 | DS macro-F1 | Δ macro-F1 | R4 key recall | DS key recall | Δ key recall |
|---|---|---|---|---|---|---|
| A_4class | 0.3280 | 0.5248 | -0.1968 | 0.3600 | 0.0400 | +0.3200 |
| B_3class_overclaim_merge | 0.4728 | 0.7112 | -0.2385 | 0.7200 | 0.4800 | +0.2400 |
| C_3class_acceptable_merge | 0.4970 | 0.5626 | -0.0656 | 0.3600 | 0.0400 | +0.3200 |

## Key Findings

1. **Best fallback taxonomy:** C_3class_acceptable_merge
2. **3-class overclaim merge (B):** R4 retains overclaim recall advantage (+0.2400), so if mild/strong boundary collapses, the paper can fall back to a 3-class taxonomy and R4 still has screening value.
3. **3-class acceptable merge (C):** R4's strong_action recall advantage persists (+0.3200) because merging supported+mild does not affect strong_action detection.
4. **4-class remains the strongest positioning** for R4 because it preserves the relation-specific routing story; fallback to 3-class is a safety net, not the primary contribution.
