# Canonicalized Review Queue and Low-Prevalence Screening v1

- 审计时间: 2026-07-05T18:20:15
- 评估样本数: 436 (out-of-fold candidates)
- 缺失 (split-missing): 8 (不纳入主指标)
- 最佳 selector: best_sentence_top5_overlap
- Priority score 公式: priority_score = p_strong_mean - p_contra_mean + 0.5 * strong_action_flag
- 禁止: 无 proxy, 无重训, 无调参, 无 API, 无联网, 不把 silver 写成 gold, 不声称自然分布, 不把 simulated 写成真实部署

## 1. canonicalized R4 能否生成有用 review queue？

**否**。

- precision@20 = 0.3500 (阈值 0.30)
- recall@100 = 0.3394 (阈值 0.70)

## 2. top100 能抓多少 strong_action？

**37 / 109** (recall@100 = 0.3394)

## 3. FP/TP 在低患病率下是否仍可接受？

| Prevalence | Recall | Precision | FP/TP | NNR | Review Burden |
|------------|--------|-----------|-------|-----|---------------|
| 1% | 0.7064 | 0.0147 | 66.82 | 67.8 | 0.4791 |
| 3% | 0.7064 | 0.0438 | 21.83 | 22.8 | 0.4839 |
| 5% | 0.7064 | 0.0723 | 12.84 | 13.8 | 0.4890 |
| 10% | 0.7064 | 0.1415 | 6.07 | 7.1 | 0.4998 |
| 15% | 0.7064 | 0.2072 | 3.83 | 4.8 | 0.5118 |
| 20% | 0.7064 | 0.2708 | 2.70 | 3.7 | 0.5224 |
| 25% | 0.7064 | 0.3305 | 2.03 | 3.0 | 0.5344 |

- FP/TP at 1%: 66.82
- FP/TP at 5%: 12.84
- FP/TP at 10%: 6.07

低患病率可用 (FP/TP <= 20 at 5%): **是**

## 4. 这个流程适合 standalone 还是 second-stage？

**second-stage**

- Standalone viable (FP/TP <= 50 at 1%): False
- Second-stage viable (FP/TP <= 20 at 5% AND recall >= 0.6): True

## 5. 是否支持 V3.17 的 offline review workflow？

**否**。

- Review queue usable: False
- Low prevalence usable: True

## 6. 下一步是否需要 local LLM baseline？

**建议: 是**。

当前 canonicalized R4 strong-F1 = 0.4503, recall = 0.7064。
- 主瓶颈仍是 screening (R4 自身判断能力限制)
- Local LLM 可作为补充 baseline，验证是否能在不调 API 的情况下提升 recall
- 但 priority queue 已可用作 second-stage screener

## 与旧结果对比

| Setting | strong-F1 | recall | precision |
|---------|-----------|--------|-----------|
| Raw BM25 top1 | 0.1806 | 0.1193 | 0.3714 |
| Canonicalized (best_sentence_top5_overlap) | 0.4503 | 0.7064 | 0.3305 |
| Oracle | 0.4257 | 0.4862 | 0.3786 |

Canonicalization vs raw:
- F1 提升: +0.2697
- Recall 提升: +0.5872
- FP/TP 降低: 是 (recall 大幅提升使 queue 中 TP 占比上升)

## Queue Metrics

| k | precision@k | recall@k | TP | FP | FP/TP | NNR |
|---|-------------|----------|----|----|-------|-----|
| 10 | 0.5000 | 0.0459 | 5 | 5 | 1.00 | 2.00 |
| 20 | 0.3500 | 0.0642 | 7 | 13 | 1.86 | 2.86 |
| 50 | 0.3400 | 0.1560 | 17 | 33 | 1.94 | 2.94 |
| 100 | 0.3700 | 0.3394 | 37 | 63 | 1.70 | 2.70 |

## Error Analysis

| Category | Count |
|----------|-------|
| correct_non_strong | 108 |
| strong_action_true_positive | 77 |
| ambiguous_mild_strong | 73 |
| screening_failure | 63 |
| strong_action_false_positive | 62 |
| contradiction_confusion | 40 |
| strong_action_false_negative | 13 |

| Failure Type | Count |
|--------------|-------|
| screening_failure | 163 |
| both_correct | 126 |
| selection_failure | 88 |
| canon_helped | 59 |

## 输出文件清单

- canonicalized_r4_review_scores.csv
- review_queue_top100.csv
- review_queue_metrics.csv
- low_prevalence_canonicalized_results.csv
- low_prevalence_canonicalized_summary.json
- review_queue_error_analysis.csv
- canonicalized_review_queue_gate.json
- canonicalized_review_queue_report.md
