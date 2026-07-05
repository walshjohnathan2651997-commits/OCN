# R4 Backup Asset Search Report v1

- 审计时间: 2026-07-05 14:48:25
- 搜索根目录: D:\ocn_backup_20260704_1606
- 只读模式: 是 (无修改/无复制/无删除/无训练/无 API)

## 1. 备份里是否找到 hcm_features？

找到 3 个候选文件。

至少一个文件包含 R4 所需全部列 (candidate_id, entailment_correct, neutral_correct, contradiction_correct, entropy_correct)，**可用**于 R4 复现。

候选清单：

| file_path | rows | usable_for_r4 | notes |
|-----------|-------|---------------|-------|
| D:\ocn_backup_20260704_1606\experiments\cese_ocn_hcm_v1\hcm_features.csv | 444 | True | ALL_REQUIRED_COLS_PRESENT |
| D:\ocn_backup_20260704_1606\experiments\cese_ocn_hcm_v1\hcm_readiness_gate.json | -1 | False | non-csv (.json) |
| D:\ocn_backup_20260704_1606\scripts\run_cese_ocn_hcm_v1.py | -1 | False | non-csv (.py) |

## 2. 是否找到完整 444 per-item R4 predictions？

**未找到**完整 444 per-item R4 predictions。

但找到 **partial** R4 per-item 预测，最大 200 行 (覆盖 45.0%)。
这些 partial 预测可用于子集评估，但不足以恢复完整 444 R4 结果。

R4-specific 预测候选文件：

| file_path | rows | has_candidate_id | has_r4_label | coverage_444 | usable_for_444 |
|-----------|-------|------------------|--------------|--------------|----------------|
| D:\ocn_backup_20260704_1606\data\simclaim_eval_v1\round2_candidates\batch01\raw_sources\ceur_ws_paper42_cyber_exercises.txt | -1 | False | False | 0.0 | False |
| D:\ocn_backup_20260704_1606\experiments\gpt_structured_judge_probe_v1\gpt_vs_r4_deepseek_comparison.csv | 100 | True | True | 0.2252 | False |
| D:\ocn_backup_20260704_1606\experiments\llm_judge_baseline_v1\llm_vs_r4_100.csv | 100 | True | True | 0.2252 | False |
| D:\ocn_backup_20260704_1606\experiments\llm_judge_baseline_v1\llm_vs_r4_200.csv | 200 | True | True | 0.4505 | False |
| D:\ocn_backup_20260704_1606\experiments\mixed_framework_new_algorithm_sweep_v1\new_algorithm_vs_r4_table.csv | 13 | False | False | 0.0 | False |
| D:\ocn_backup_20260704_1606\experiments\v3_r4_strong_baselines_holdout_v1\r4_vs_strong_baselines.csv | 7 | False | False | 0.0 | False |
| D:\ocn_backup_20260704_1606\paper_versions_ordered\V3_5_presentation_ready\figure_3_llm_vs_r4_strong_gap.md | -1 | False | False | 0.0 | False |
| D:\ocn_backup_20260704_1606\paper_versions_ordered\V3_6_case_figure_integrity_checked\figure_3_llm_vs_r4_strong_gap_renderable.md | -1 | False | False | 0.0 | False |
| D:\ocn_backup_20260704_1606\paper_versions_ordered\V3_mixed_framework_v2_R4\CESE_OCN_mixed_framework_v2_R4_manuscript.md | -1 | False | False | 0.0 | False |
| D:\ocn_backup_20260704_1606\paper_versions_ordered\V3_mixed_framework_v2_R4\V3_R4_change_log.md | -1 | False | False | 0.0 | False |
| D:\ocn_backup_20260704_1606\scripts\run_v3_r4_strong_baselines_holdout_v1.py | -1 | False | False | 0.0 | False |

## 3. 是否找到 pkl/joblib 模型 artifacts？

**未找到** .pkl/.joblib/.pickle 模型 artifact。

## 4. 是否找到 t_contra_low？

**未找到** t_contra_low 在任何 threshold/manifest/readiness_gate/frozen 文件中。

这与之前 Task D 的判断一致：t_contra_low 从未被冻结。

t_contra: True, t_strong: True, t_svm: True, t_contra_low: False

## 5. 是否可以不用重训恢复 R4？

**不可以**。原因：

- 模型 artifact 缺失（.pkl/.joblib/.pickle 没有）→ 必须重训 SVM 分类器

- t_contra_low 未冻结 → 必须在 dev split 上重新拟合（小成本，但属于阈值调整）

- 也没有现成 444 行 per-item 预测可复用

## 6. 如果可以，需要复制哪些文件到当前项目？

不适用（无法仅靠复制恢复）。

## 7. 如果不可以，下一步是否必须 reproduction training？

**是**，但成本显著降低，因为 HCM features 已在备份中找到（最昂贵的 NLI 重算步骤可跳过）：

1. **复制**备份中的 HCM features CSV: `D:\ocn_backup_20260704_1606\experiments\cese_ocn_hcm_v1\hcm_features.csv` (444 行, 5 个必需列齐全) → 无需重算 NLI 特征
2. **重训** SVM 分类器（小成本，CPU 秒级，使用现有 HCM features）
3. **重新拟合** t_contra_low 阈值（在 dev split 上，小成本）
4. **复跑** R4 routing 逻辑 (`route_conservative_strong`) 逐条预测
5. **输出** 444 行 per-item R4 预测 CSV

**关键节省**：因 HCM features 已找到，无需调用 `cross-encoder/nli-deberta-base` 重算 7 个 NLI 特征（这原本是最耗时的步骤）。

**仍需的小成本训练**：SVM 分类器重训 + t_contra_low 拟合。这两步在 CPU 上秒级完成，不属于 'full retraining'。

**替代方案**：如果只想恢复 per-item 预测而不重训，可考虑：
- 在 200 行已存预测 (`gpt_vs_r4_deepseek_comparison.csv` / `llm_vs_r4_*.csv`) 上做 partial evaluation
- 但这无法覆盖完整 444，论文必须明确标注 partial-only

## Inventory 统计

- 总文件数: 318

按 likely_asset_type 分类：

| asset_type | count |
|------------|-------|
| threshold | 146 |
| candidate_pool | 119 |
| prediction | 39 |
| routing_logic | 11 |
| hcm_features | 3 |

## 输出文件清单

- `r4_backup_asset_inventory.csv`
- `hcm_feature_candidates.csv`
- `r4_prediction_candidates.csv`
- `model_artifact_candidates.csv`
- `threshold_candidates.csv`
- `r4_backup_recovery_gate.json`
- `r4_backup_asset_search_report.md`
