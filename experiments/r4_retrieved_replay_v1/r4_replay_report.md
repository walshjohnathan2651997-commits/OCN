# Formal R4 Replay on PDF-Retrieved Evidence v1

- 审计时间: 2026-07-05 15:54:57
- 评估样本数: 436 (out-of-fold candidates)
- 缺失 (split-missing): 8 (不纳入主指标)
- 禁止: 无 proxy, 无重训, 无调参, 无 API, 无联网

## 1. 是否成功加载 recovered R4 artifacts？

**是**。10 个 seed 的 artifacts 全部加载成功 (clf_contra/clf_strong/clf_svm + scaler + thresholds + feature_columns + label_mapping)。
路径: `D:\ocn\experiments\r4_minimal_recovery_v1\artifacts\seed_<N>\`

## 2. 是否没有使用 proxy？

**是**。所有预测均来自 R4_conservative_strong 路由 (clf_contra + clf_strong + clf_svm + route_conservative_strong)，无 cue-based proxy。

## 3. 是否没有重新训练/调参？

**是**。使用 r4_minimal_recovery_v1 已保存的 classifiers 和 thresholds，未重新训练，未调整阈值。
thresholds 来源: routing_variant_results_by_seed.csv (historical per-seed values)

## 4. retrieved evidence 下 R4 strong_action 是否保留？

| Setting | n_eval | strong-F1 | macro-F1 | strong-precision | strong-recall |
|---------|--------|-----------|----------|------------------|---------------|
| oracle | 436 | 0.3969 | 0.4356 | 0.3446 | 0.4679 |
| bm25_top1 | 436 | 0.2166 | 0.3521 | 0.3542 | 0.1560 |
| bm25_top3 | 436 | 0.0000 | 0.3113 | 0.0000 | 0.0000 |
| bm25_top5 | 436 | 0.0000 | 0.2810 | 0.0000 | 0.0000 |

**retrieved replay 未通过** (oracle-to-best gap = 0.1803, 阈值 0.05)

## 5. top1/top3/top5 哪个最好？

**bm25_top1** (strong-F1 = 0.2166)

| Setting | strong-F1 | gap vs oracle |
|---------|-----------|---------------|
| bm25_top1 | 0.2166 | 0.1803 |
| bm25_top3 | 0.0000 | 0.3969 |
| bm25_top5 | 0.0000 | 0.3969 |

## 6. oracle-to-best gap 多大？

**0.1803** (oracle strong-F1 = 0.3969, best retrieved = 0.2166)

判定: gap <= 0.05 → 未通过

## 7. 主要错误来自 retrieval 还是 screening？

主瓶颈: **screening**

错误分布 (best retrieved = bm25_top1):
- Correct: 103
- Retrieval harmed screening: 99
- Both failed: 175
- Retrieval helped: 59
- Strong action false negative: 92
- Strong action false positive: 31

## 8. 是否支持 V3.17 主线：offline PDF-corpus retrieval + CESE-OCN/R4 screening？

**否**。oracle-to-best gap = 0.1803 > 0.05，retrieved evidence 损害 R4 strong_action screening。

V3.17 主线需要 retrieval 升级 (dense/reranker) 后才能成立。

## 输出文件清单

- `hcm_features_replay_oracle.csv`
- `hcm_features_replay_bm25_top1.csv`
- `hcm_features_replay_bm25_top3.csv`
- `hcm_features_replay_bm25_top5.csv`
- `r4_replay_predictions_oracle.csv`
- `r4_replay_predictions_bm25_top1.csv`
- `r4_replay_predictions_bm25_top3.csv`
- `r4_replay_predictions_bm25_top5.csv`
- `r4_replay_metrics_by_setting.csv`
- `r4_replay_confusion_matrices.json`
- `r4_replay_error_analysis.csv`
- `r4_replay_gate.json`
- `r4_replay_report.md`
