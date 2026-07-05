# Retrieved Evidence Canonicalization for R4 v1

- 审计时间: 2026-07-05T16:36:21
- 评估样本数: 436 (out-of-fold candidates)
- 缺失 (split-missing): 8 (不纳入主指标)
- 禁止: 无 proxy, 无重训, 无调参, 无 API, 无联网, 不使用 true_label/oracle_hit 选 evidence

## 1. Evidence 格式长度统计 (words)

| Setting | Mean | Median |
|---------|------|--------|
| oracle_span | 26.7 | 26 |
| raw_bm25_top1_chunk | 71.1 | 70 |
| cleaned_top1_chunk | 69.8 | 69 |
| best_sentence_from_top1 | 28.3 | 24 |
| three_sentence_window_from_top1 | 60.8 | 61 |
| best_sentence_from_top5 | 23.2 | 22 |
| three_sentence_window_from_top5 | 62.8 | 62 |

## 2. R4 strong_action F1 by evidence format

| Setting | strong-F1 | strong-recall | macro-F1 |
|---------|-----------|---------------|----------|
| oracle_span | 0.4257 | 0.4862 | 0.4571 |
| raw_bm25_top1_chunk | 0.1806 | 0.1193 | 0.3551 |
| cleaned_top1_chunk | 0.2282 | 0.1560 | 0.3576 |
| best_sentence_from_top1 | 0.4110 | 0.6147 | 0.3505 |
| three_sentence_window_from_top1 | 0.2688 | 0.2294 | 0.3514 |
| best_sentence_from_top5 | 0.4503 | 0.7064 | 0.3847 |
| three_sentence_window_from_top5 | 0.2561 | 0.1927 | 0.3569 |

## 3. 格式偏移消融 (Format Ablation)

将 oracle span 人为加 metadata / 拉长，测试 R4 是否也下降：

| Ablation | strong-F1 | drop vs clean oracle |
|----------|-----------|----------------------|
| oracle_span_clean | 0.4257 | 0.0000 (baseline) |
| oracle_with_metadata | 0.4156 | 0.0101 |
| oracle_lengthened | 0.0938 | 0.3320 |

**Format shift confirmed**: 是 (阈值: 任一 ablation drop >= 0.05)

## 4. Canonicalization vs Raw BM25

| 指标 | 值 |
|------|----|
| Raw BM25 top1 strong-F1 | 0.1806 |
| Best canonicalized format | best_sentence_from_top5 |
| Best canonicalized strong-F1 | 0.4503 |
| Canonicalization gain vs raw | +0.2697 |
| Oracle strong-F1 | 0.4257 |
| Oracle-to-best gap | -0.0246 |

## 5. 错误归因 (best canonicalized vs raw)

- Canon helped (raw 错, canon 对): 129
- Canon harmed (raw 对, canon 错): 3
- Both correct: 163
- Both failed: 141

## 6. 是否确认格式偏移是主要原因？

**是**。

- Metadata 注入 drop: 0.0101
- Length 拉长 drop: 0.3320
- 阈值: 0.05

## 7. 是否支持 V3.17 主线 (offline PDF-corpus retrieval + R4 screening)？

**是**。

- Retrieved replay passed (gap <= 0.05): True
- Canonicalization improves over raw: True
- Oracle-to-best gap: -0.0246

## 8. 主瓶颈 & 下一步

主瓶颈: **format_shift**

下一步建议: Format shift confirmed as major cause. Re-test R4 with canonicalized spans (best_sentence/three_sentence_window) on dense retrieval / reranker outputs.

## 输出文件清单

- canonicalized_evidence_spans.csv
- format_ablation_inputs.csv
- r4_predictions_by_format.csv
- r4_metrics_by_format.csv
- canonicalization_error_analysis.csv
- r4_confusion_matrices_by_format.json
- evidence_canonicalization_gate.json
- evidence_canonicalization_report.md
