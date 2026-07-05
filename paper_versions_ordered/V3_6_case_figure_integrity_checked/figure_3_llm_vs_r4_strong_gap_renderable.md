# Figure 3: LLM vs. R4 Strong-Action Gap (Renderable)

> **V3.6 note:** This is the renderable version. Unlike V3.5 (which used `![Figure](figure_3_llm_vs_r4_strong_gap.md)` markdown links that do not render in docx), this version uses inline ASCII bar charts + a markdown table that can be copied directly into the paper body. No external image dependencies, no broken markdown links.

---

## Figure 3 caption

**Figure 3.** LLM vs. R4 strong-action gap on matched SimClaim samples. LLMs (GPT-5.5 standard, GPT-5.5 structured, DeepSeek-V3) all converge on strong_action-F1 = 0.0769 (recall 0.04 = 1/25). R4 reaches strong_F1 = 0.3000 on the matched 100 and 0.3158 on the matched 200. LLMs retain substantially higher overall macro-F1 (0.5248-0.5543 vs. R4 0.3280). Interpretation: **LLMs are stronger overall, but R4 targets the strong_action gap.**

---

## Figure 3 data table (Table 2 in the paper)

| Method | N | Overall Macro-F1 | Strong F1 | Strong Recall | Strong Precision | Contra F1 |
| --- | --- | --- | --- | --- | --- | --- |
| GPT-5.5 standard | 100 | 0.5523 | 0.0769 | 0.04 | 1.0 | 0.6857 |
| GPT-5.5 structured (5-step) | 100 | 0.5543 | 0.0769 | 0.04 | 1.0 | 0.6857 |
| DeepSeek-V3 (matched 100) | 100 | 0.5248 | 0.0769 | 0.04 | 1.0 | 0.8317 |
| DeepSeek-V3 (full 200) | 200 | 0.5270 | 0.0769 | 0.04 | 1.0 | 0.8317 |
| R4 (matched 100) | 100 | 0.3280 | 0.3000 | — | — | — |
| R4 (full 200) | 200 | — | 0.3158 | — | — | — |

---

## Figure 3 body — Overall Macro-F1 (higher is better)

```
GPT-5.5 structured  | ████████████████████████████████████████████████  0.5543
GPT-5.5 standard    | ████████████████████████████████████████████████  0.5523
DeepSeek-V3 (200)   | ██████████████████████████████████████████████   0.5270
DeepSeek-V3 (100)   | ██████████████████████████████████████████████   0.5248
R4 (matched 100)    | ██████████████████████████████                   0.3280
                    +------+------+------+------+------+------+------+--+
                    0.0   0.1   0.2   0.3   0.4   0.5   0.6   0.7
```

**Reading:** LLM judges (GPT-5.5, DeepSeek-V3) retain substantially higher overall macro-F1 than R4 on matched samples. R4 is NOT a general-purpose replacement.

---

## Figure 3 body — Strong-Action F1 (higher is better)

```
R4 (matched 200)    | ████████████████████████████                     0.3158
R4 (matched 100)    | ███████████████████████████                      0.3000
GPT-5.5 structured  | █                                                 0.0769
GPT-5.5 standard    | █                                                 0.0769
DeepSeek-V3 (200)   | █                                                 0.0769
DeepSeek-V3 (100)   | █                                                 0.0769
                    +------+------+------+------+------+------+------+--+
                    0.0   0.1   0.2   0.3   0.4   0.5   0.6   0.7
```

**Reading:** All three LLM judges converge on strong_action-F1 = 0.0769 (recall 0.04 = 1/25) on matched samples. R4 reaches 0.3000 (matched 100) and 0.3158 (matched 200) — absolute gap +0.22 to +0.24. R4 targets the specific relation LLMs miss under tested prompts.

---

## Figure 3 body — Strong-Action Recall (higher is better)

```
R4 (444-set)        | ████████████████████████████████                 0.4562
GPT-5.5 standard    | █                                                 0.04 (1/25)
GPT-5.5 structured  | █                                                 0.04 (1/25)
DeepSeek-V3         | █                                                 0.04 (1/25)
                    +------+------+------+------+------+------+------+--+
                    0.0   0.1   0.2   0.3   0.4   0.5   0.6   0.7
```

**Note:** R4 strong_recall on the matched 100 is not directly reported; the bar above uses the 444-set R4 recall (0.4562) for context only. The LLM recall of 0.04 = 1/25 is on the matched 100.

---

## Figure 3 interpretation (inline text)

**LLMs are stronger overall, but R4 targets the strong_action gap.**

- The three LLM judges (GPT-5.5 standard, GPT-5.5 structured, DeepSeek-V3) all converge on strong_action-F1 = 0.0769 (recall 0.04 = 1/25) on matched samples. This is a consistent under-detection pattern under the tested prompts, not a single-model quirk.
- The structured 5-step evidence-sufficiency decomposition prompt does NOT improve strong_action detection under this tested setting. GPT-5.5 only flagged 7/100 samples as containing an action/deployment/safety claim in structured mode, despite 25/100 being strong_action_overclaim by silver label.
- R4 reaches strong_action-F1 = 0.3000 on the matched 100 (absolute gap +0.2231 over LLM judges) and 0.3158 on the matched 200 (absolute gap +0.2389 over DeepSeek-V3). This is the relation-specific value R4 adds.
- But R4's overall macro-F1 is substantially lower (0.3280 vs. 0.5523-0.5543 on matched 100). R4 is a relation-specific complement, not a general-purpose replacement.

## Complementary error profiles

| Method | Dominant error mode on strong_action | Profile |
| --- | --- | --- |
| GPT-5.5 standard / structured | over-contradiction (strong_action → contradiction), over-milding (strong_action → mild), over-supporting (strong_action → supported) | False negatives on strong_action |
| DeepSeek-V3 | same as GPT — over-contradiction, over-milding, over-supporting | False negatives on strong_action |
| R4 | over-routing supported → strong (98 FP), mild → strong (24 FP) | False positives on strong_action |

These error profiles are complementary: LLMs miss strong_action (false negatives); R4 over-flags strong_action (false positives). A combined system — LLM judge for supported/mild/contradiction, R4 for strong_action — could potentially exploit this complementarity, though we leave that to future work.

## Bounded claim

This finding is bounded by:

1. **Silver labels** (62.5% questionable/unclear in the author sanity audit, 75% confusion on strong_action).
2. **Single-run, temperature 0, no variance estimate.**
3. **One structured prompt design** (other decompositions untested).
4. **Two tested models** (GPT-5.5 via third-party proxy, DeepSeek-V3 via official API).

The claim is NOT that "LLMs cannot solve strong_action_overclaim." The claim is that under the tested prompts, on the current silver diagnostic set, the pattern is consistent across the two tested models and suggests that a relation-specific router can complement black-box LLM judges — pending independent gold validation.
