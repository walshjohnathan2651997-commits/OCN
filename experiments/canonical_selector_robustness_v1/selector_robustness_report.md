# Canonical Evidence Selector Robustness v1

- 审计时间: 2026-07-05T17:54:49
- 评估样本数: 436 (out-of-fold candidates)
- 缺失 (split-missing): 8 (不纳入主指标)
- 测试 selector 数: 11
- 禁止: 无 proxy, 无重训, 无调参, 无 API, 无联网, 不使用 true_label/oracle_hit 选 evidence

## 1. best_sentence_from_top5 是否稳健？

**是**。

best_sentence_from_top5_overlap strong-F1 = 0.4503

最佳 selector: **best_sentence_top5_overlap** (strong-F1 = 0.4503)

判定: 至少 3 个 selector strong-F1 >= 0.40 (实际 6), 至少 2 个 selector gap <= 0.05 (实际 6)。

## 2. 有多少 selector 超过 raw top1？

**9 / 9** (排除 oracle 和 raw_top1 本身)

raw top1 strong-F1 = 0.1806

## 3. 有多少 selector 接近 oracle (gap <= 0.05)？

**6 / 9**

oracle strong-F1 = 0.4257

selectors 接近 oracle:
- best_sentence_top3_overlap: strong-F1=0.4345, gap=-0.0088
- best_sentence_top5_overlap: strong-F1=0.4503, gap=-0.0246
- best_sentence_top10_overlap: strong-F1=0.4419, gap=-0.0162
- best_sentence_top5_bm25weighted: strong-F1=0.4159, gap=+0.0098
- best_sentence_top5_nli_low_entropy: strong-F1=0.4289, gap=-0.0032
- length_limited_top5: strong-F1=0.4464, gap=-0.0207

## 4. NLI selector 是否优于 overlap selector？

**否**。

- Best NLI selector strong-F1: 0.4289
- Best overlap selector strong-F1: 0.4503

## 5. 失败主要来自选错句子还是 R4 判断失败？

主瓶颈: **screening**

- Selection failure (best_sel 错, oracle 对): 88
- Both wrong (best_sel 错, oracle 也错): 163  → R4 screening 失败
- Canon helped (best_sel 对, oracle 错): 59

## 6. 是否值得继续 hybrid/dense retrieval？

**否**。

判定依据:
- selectors >= 0.40: 6
- best selector vs oracle gap: -0.0246

## 7. 是否支持主线：retrieval → canonicalization → R4 screening？

**是**。

- Robustness passed: True
- 多个 selector 稳定接近 oracle, 证明 canonicalization 是稳健策略, 不是偶然

## 完整 metrics 表

| Selector | strong-F1 | recall | macro-F1 | gap | improvement vs raw |
|----------|-----------|--------|----------|-----|--------------------|
| best_sentence_top5_overlap | 0.4503 | 0.7064 | 0.3847 | -0.0246 | +0.2697 |
| length_limited_top5 | 0.4464 | 0.7064 | 0.3729 | -0.0207 | +0.2658 |
| best_sentence_top10_overlap | 0.4419 | 0.6972 | 0.3731 | -0.0162 | +0.2613 |
| best_sentence_top3_overlap | 0.4345 | 0.6697 | 0.3837 | -0.0088 | +0.2540 |
| best_sentence_top5_nli_low_entropy | 0.4289 | 0.8991 | 0.2870 | -0.0032 | +0.2483 |
| oracle_span | 0.4257 | 0.4862 | 0.4571 | +0.0000 | +0.2451 |
| best_sentence_top5_bm25weighted | 0.4159 | 0.6239 | 0.3569 | +0.0098 | +0.2353 |
| two_sentence_window_top5 | 0.3660 | 0.3945 | 0.3772 | +0.0597 | +0.1854 |
| best_sentence_top5_nli_entailment | 0.3345 | 0.4220 | 0.3262 | +0.0912 | +0.1540 |
| best_sentence_top5_margin | 0.1867 | 0.1284 | 0.2573 | +0.2390 | +0.0061 |
| bm25_top1_raw | 0.1806 | 0.1193 | 0.3551 | +0.2451 | +0.0000 |

## 输出文件清单

- selector_variant_definitions.csv
- selector_variant_evidence.csv
- selector_variant_predictions.csv
- selector_variant_metrics.csv
- selector_stability_by_label.csv
- selector_error_overlap.csv
- selector_robustness_gate.json
- selector_robustness_report.md
