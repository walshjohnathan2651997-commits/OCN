# Table 6: Error Transition Matrix (baseline -> R4 predictions)

| source_class | predicted_class | count |
| --- | --- | --- |
| strong_action_overclaim | strong_action_overclaim | 64 |
| strong_action_overclaim | mild_scope_overclaim | 27 |
| strong_action_overclaim | contradiction_candidate | 14 |
| strong_action_overclaim | supported | 12 |
| supported | supported | 156 |
| supported | strong_action_overclaim | 98 |
| supported | mild_scope_overclaim | 43 |
| mild_scope_overclaim | mild_scope_overclaim | 25 |
| mild_scope_overclaim | strong_action_overclaim | 24 |
| mild_scope_overclaim | supported | 17 |
| contradiction_candidate | contradiction_candidate | 159 |
| contradiction_candidate | strong_action_overclaim | 1 |

- Read as: TRUE source_class was predicted as predicted_class by R4.
- supported->strong = 98: R4 aggressively routes supported to strong (false positives).
- mild->strong = 24: R4 also confuses mild with strong.
- strong->strong = 64 (recall improved vs baseline's 64 total strong predictions).
- strong->supported = 12, strong->mild = 27: residual strong under-detection.
- This is a LIMITATION: R4 improves strong recall at the cost of supported/mild->strong false positives.
