# Canonicalized R4 Risk Ranking Calibration v1

- 审计时间: 2026-07-05T19:27:36
- 评估样本数: 436 (out-of-fold candidates)
- true strong_action 数: 109
- Baseline priority_score: priority_score = p_strong_mean - p_contra_mean + 0.5 * strong_action_flag
- 禁止: 无模型训练, 无API, 无联网, 无阈值修改, 无原数据修改, 无论文修改, 无true_label/oracle_hit参与排序, 无silver写成gold, 无自然分布声明

## 1. 当前 queue 排序为什么弱？

Task J 的 priority_score = p_strong - p_contra + 0.5 * strong_action_flag 存在以下问题：

- **precision@20 = 0.3500** (阈值 0.40): top-20 中只有 7/20 是 true strong_action
- **recall@100 = 0.3394**: top-100 只抓到 37/109 true strong_action
- flag 过于宽松: strong_action_flag=1 的样本过多 (233 个)，其中只有 77 个是 true strong_action
- priority_score 的 +0.5*flag 偏移量不足以区分 flag 内部的真实风险差异
- p_strong 和 p_contra 单独区分力不足: strong_action 和非 strong_action 的 p_strong 分布重叠大

## 2. 哪个 ranking formula 最好？

**G_conservative_precision**

- precision@20 = 0.4500
- precision@50 = 0.3600
- recall@100 = 0.3303
- average_precision = 0.3532
- 是否达到推荐目标: partial (未全部达到)

所有 variant 对比:

| Variant | P@20 | P@50 | R@100 | AP |
|---------|------|------|-------|----|
| A_flag_only | 0.3500 | 0.3600 | 0.3303 | 0.3562 |
| B_p_strong_desc | 0.3500 | 0.3200 | 0.3028 | 0.3318 |
| C_guarded_strong_score | 0.3500 | 0.3400 | 0.3211 | 0.3395 |
| D_confidence_guarded | 0.4000 | 0.3200 | 0.3303 | 0.3539 |
| E_selector_confidence | 0.3500 | 0.3600 | 0.2752 | 0.3349 |
| F_short_span_bonus | 0.4000 | 0.3200 | 0.3303 | 0.3509 |
| G_conservative_precision ** | 0.4500 | 0.3600 | 0.3303 | 0.3532 |
| H_balanced_review_score | 0.2500 | 0.3800 | 0.2752 | 0.3231 |

## 3. precision@20/50 和 recall@100 是否提升？

| 指标 | Baseline | Best | 提升 |
|------|----------|------|------|
| precision@20 | 0.3500 | 0.4500 | +0.1000 |
| precision@50 | (baseline N/A) | 0.3600 | - |
| recall@100 | 0.3394 | 0.3303 | -0.0092 |

ranking_improved = True (precision@20 提升 >= 0.05 或 recall@100 提升 >= 0.05)

## 4. FP 主要来自哪些类？

| 错误类型 | 数量 |
|---------|------|
| false_positive_mild | 0 |
| false_positive_supported | 21 |
| false_positive_contradiction | 13 |
| false_negative_low_pstrong | 16 |
| false_negative_high_entropy | 18 |
| selector_failure | 7 |
| r4_screening_failure | 32 |
| ambiguous_mild_strong | 66 |

FP 主要来源分析:
- false_positive_mild: 0 (0.0%)
- false_positive_supported: 21 (61.8%)
- false_positive_contradiction: 13 (38.2%)
- FN 主要来源: r4_screening_failure=32, false_negative_low_pstrong=16, false_negative_high_entropy=18, selector_failure=7

## 5. 是否仍只能作为 second-stage？

| 判定 | 结果 |
|------|------|
| queue_usable (P@20>=0.40 且 R@100>=0.45) | False |
| standalone_usable (FP/TP@1%<=50 且 P@20>=0.40) | False |
| second_stage_usable (FP/TP@5%<=20 且 recall>=0.60) | True |
| recommended_mode | **second-stage** |

低患病率模拟 (best variant top-100):

| Prevalence | Recall | Precision | F1 | FP/TP | NNR | Review Burden |
|------------|--------|-----------|----|-------|-----|---------------|
| 1% | 0.3303 | 0.0167 | 0.0319 | 58.73 | 59.73 | 0.1973 |
| 3% | 0.3303 | 0.0496 | 0.0863 | 19.17 | 20.17 | 0.1999 |
| 5% | 0.3303 | 0.0818 | 0.1311 | 11.24 | 12.24 | 0.2021 |
| 10% | 0.3303 | 0.1580 | 0.2136 | 5.35 | 6.35 | 0.2097 |
| 15% | 0.3303 | 0.2303 | 0.2711 | 3.36 | 4.36 | 0.2159 |
| 20% | 0.3303 | 0.2989 | 0.3134 | 2.36 | 3.36 | 0.2221 |

## 6. 是否需要 local LLM baseline 或 learned ranker？

**建议: 是，考虑 local LLM baseline 或 learned ranker**。

- 当前 best variant (G_conservative_precision) precision@20=0.4500, recall@100=0.3303
- 虽然比 baseline 有提升, 但仍未达到 standalone 标准
- FP/TP@1%=58.73 (阈值 50), 说明低患病率下 FP 负担仍高
- r4_screening_failure=32 (R4 未 flag 的 true strong_action) 是 FN 主要来源, ranking 无法修复
- learned ranker 可利用更多特征 (如 evidence-claim 语义匹配) 提升排序
- local LLM 可作为补充 screener, 提升 recall

## 输出文件清单

- risk_ranking_features.csv
- risk_ranking_formula_variants.csv
- risk_ranking_results_by_variant.csv
- review_queue_top100_best.csv
- low_prevalence_ranking_results.csv
- risk_ranking_error_analysis.csv
- risk_ranking_gate.json
- risk_ranking_report.md