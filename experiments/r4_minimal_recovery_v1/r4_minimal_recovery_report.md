# Minimal R4 Recovery from Backup HCM Features v1

- 审计时间: 2026-07-05 15:14:37
- 模式: reproduction recovery (不是新方法)
- 只读原数据，禁止调 API/联网/改论文/用 test 调参

## 1. hcm_features 是否可用？

**是**。备份中的 `hcm_features.csv` 成功加载并合并到主数据。
- 行数: 444 ✓
- candidate_id 唯一: 444 ✓
- 7 个 NLI 特征列齐全 ✓
- 与 strict_silver_max join 后无缺失: True ✓
- 输出: `D:\ocn\experiments\r4_minimal_recovery_v1\recovered_hcm_features.csv`

## 2. 是否恢复了完整 444 条 R4 predictions？

**是**。436/444 candidate_ids 有至少一次 out-of-fold 预测。

覆盖率分解:
- Test split 覆盖: 356 candidates (primary, out-of-fold, never in train)
- Dev split 额外覆盖: 80 candidates (secondary, out-of-fold, never in train)
- 总覆盖: 436 / 444

WARNING: 8 个 candidate 从未出现在任何 seed 的 test 或 dev split (always in train):
- SBV2-ALL92-G055-C01
- SBV2-ALL92-G055-C02
- SBV2-ALL92-G055-C03
- SBV2-ALL92-G055-C04
- SBV2-ALL92-G108-C01
- SBV2-ALL92-G108-C02
- SBV2-ALL92-G108-C03
- SBV2-ALL92-G108-C04

- 总预测行数 (10 seeds × test+dev splits): 1320
- 聚合方式: 优先 test 多数投票，回退 dev 多数投票
- 输出: `D:\ocn\experiments\r4_minimal_recovery_v1\r4_recovered_predictions_444.csv`
- 原始 per-seed 预测: `D:\ocn\experiments\r4_minimal_recovery_v1\r4_recovered_predictions_per_seed.csv`

## 3. t_contra_low 是否恢复？

**是**。从 `routing_variant_results_by_seed.csv` 解析出每个 seed 的历史 R4 阈值 (t_contra, t_contra_low, t_strong, t_svm)。

Per-seed t_contra_low 值:

| seed | t_contra | t_contra_low | t_strong | t_svm |
|------|----------|--------------|----------|-------|
| 11 | 0.4 | 0.35 | 0.55 | 0.55 |
| 22 | 0.5 | 0.4 | 0.55 | 0.5 |
| 33 | 0.35 | 0.35 | 0.4 | 0.45 |
| 44 | 0.4 | 0.4 | 0.4 | 0.45 |
| 55 | 0.5 | 0.4 | 0.4 | 0.55 |
| 66 | 0.55 | 0.35 | 0.5 | 0.6 |
| 77 | 0.45 | 0.3 | 0.55 | 0.55 |
| 88 | 0.35 | 0.3 | 0.5 | 0.5 |
| 99 | 0.55 | 0.4 | 0.55 | 0.55 |
| 111 | 0.6 | 0.35 | 0.5 | 0.55 |

t_contra_low 均值: 0.3600

**同时**也用 frozen 阈值 (t_contra=0.48, t_strong=0.535, t_svm=0.51) + dev grid search 恢复了 t_contra_low，作为对比。

## 4. artifacts 是否保存？

**是**。每个 seed 目录保存了 10 个 artifact 文件 (3 clf + 1 flat4 + 3 scaler + 3 json)。
- 目录: `D:\ocn\experiments\r4_minimal_recovery_v1\artifacts\seed_<N>\`
- 总 artifact 数: 100
- 文件: clf_contra.pkl, clf_strong.pkl, clf_svm.pkl, clf_flat4.pkl, scaler_contra.pkl, scaler_strong.pkl, scaler_svm.pkl, thresholds.json, feature_columns.json, label_mapping.json
- 清单: `D:\ocn\experiments\r4_minimal_recovery_v1\r4_recovery_artifacts_inventory.csv`

## 5. recovered 指标是否接近 frozen R4？

**是** (gap <= 0.05 判定)。

### Exact reproduction mode (per-seed historical thresholds)

| 指标 | Frozen | Recovered | Gap | Pass |
|------|--------|-----------|-----|------|
| strong-F1 | 0.3967 | 0.3967 | 0.0000 | ✓ |
| macro-F1 | 0.4238 | 0.4238 | 0.0000 | ✓ |

### Frozen thresholds mode (t_contra=0.48, t_strong=0.535, t_svm=0.51 + dev-tuned t_contra_low)

| 指标 | Frozen | Recovered | Gap |
|------|--------|-----------|-----|
| strong-F1 | 0.3967 | 0.3906 | 0.0061 |
| macro-F1 | 0.4238 | 0.4438 | 0.0200 |

**判定**: recovery_passed = True (基于 exact reproduction mode)

## 6. 是否可以进入 retrieved evidence replay？

**是**。R4 recovery 通过 (gap <= 0.05)。

下一步: 使用保存的 artifacts (clf_*.pkl, scaler_*.pkl, thresholds.json) 和 `route_conservative_strong` 函数，对 retrieved evidence 的 HCM features 复跑 R4。

具体流程:
1. 对 retrieved evidence 用 `cross-encoder/nli-deberta-base` 计算 HCM features
2. 用保存的 scaler 标准化特征
3. 用保存的 clf_contra/clf_strong/clf_svm 计算 p_contra/p_strong/p_svm
4. 用保存的 thresholds (per-seed) 应用 route_conservative_strong
5. 聚合 10 seeds 的预测 (majority vote)

## 7. 如果不可以，卡在哪里？

不适用 (recovery 通过)。

## 输出文件清单

- `recovered_hcm_features.csv`
- `r4_recovery_split_manifest.csv`
- `r4_recovered_predictions_444.csv`
- `r4_recovery_metrics_by_seed.csv`
- `r4_recovery_metrics_summary.json`
- `r4_recovery_confusion_matrices.json`
- `r4_recovery_artifacts_inventory.csv`
- `r4_recovery_gate.json`
- `r4_minimal_recovery_report.md`
