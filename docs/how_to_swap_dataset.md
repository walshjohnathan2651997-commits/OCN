# 如何更换数据集（How to Swap a Dataset）

本指南说明：以后换成更好的正式数据集（例如 `simclaim_paper_full`）时，
**只需要新增一个 dataset config 并重跑 pipeline，不需要改任何模型/baseline 代码**。

## 一、前提

新数据集必须满足以下条件：

1. **字段符合 schema**：参考 `schemas/simclaim_eval_schema.json` 与
   `cese/data/loaders.py` 中的 `STANDARD_FIELDS`。统一加载器会把
   JSONL/CSV 标准化为以下字段（节选）：
   - `sample_id`、`logical_sample_id`、`paper_id`、`source_id`、`domain`
   - `claim_text`、`evidence_text`
   - `claim_scope_tier`、`claim_causal_tier`、`claim_action_tier`、`claim_certainty_tier`
   - `support_scope_tier`、`support_causal_tier`、`support_action_tier`、`support_certainty_tier`
   - `escalation_label`、`escalation_type`、`source_type`、`human_audited`、`split`
2. **train/dev/test 切分**：正式数据集必须是已经切分好的 JSONL，且每条
   记录带 `split` 字段（或使用三个独立文件）。
3. **不允许在 test split 上选阈值**：`threshold_source` 必须是 `dev`。

## 二、步骤

### 1. 准备数据文件

把新数据放到 `data/<role>/` 下，例如：

```
data/paper_full/
    splits/train.jsonl
    splits/dev.jsonl
    splits/test.jsonl
```

### 2. 新增 dataset config

复制 `configs/dataset_simclaim_paper_full_future.yaml` 为正式配置，例如
`configs/dataset_simclaim_paper_full.yaml`，并填写全部必填字段：

```yaml
dataset_name: simclaim_paper_full
dataset_version: v1
dataset_role: paper_benchmark
dataset_status: paper_full
human_audited: true
multi_annotator: true
num_annotators: 2
adjudicated: true
source_type_modes: ["oracle"]
schema_path: schemas/simclaim_eval_schema.json

train_path: data/paper_full/splits/train.jsonl
dev_path:   data/paper_full/splits/dev.jsonl
test_path:  data/paper_full/splits/test.jsonl
candidate_path: null
weak_train_path: null

output_release_dir: release_simclaim_paper_full
result_scope: paper_full
paper_valid_default: true        # 仅当 readiness gate 通过后才允许 true
threshold_source: dev
forbid_test_threshold_tuning: true
```

### 3. 校验数据契约

```bash
python scripts/validate_dataset_contract.py \
    --config configs/dataset_simclaim_paper_full.yaml
```

必须全部通过后再继续。

### 4. 运行统一 pipeline

```bash
python scripts/run_dataset_pipeline.py \
    --config configs/dataset_simclaim_paper_full.yaml
```

该命令会按顺序执行 12 步：
`validate_dataset_contract` → `run_train_eval` → `run_baselines` →
`run_ablations` → `run_adversarial_eval` → `run_oracle_extracted_confidence` →
`bootstrap_metrics` → `paired_significance_tests` → `generate_tables` →
`update_results_manifest` → `validate_pipeline_outputs` → `export_paper_tables`。

任一步失败会被记录到 `release_simclaim_paper_full/pipeline_summary.json`，
不会 silent pass。

### 5. 导出论文表格

```bash
python scripts/export_paper_tables.py \
    --release-dir release_simclaim_paper_full \
    --out paper_assets/simclaim_paper_full
```

输出：

```
paper_assets/simclaim_paper_full/
    tables/main_results_table.csv
    tables/calibration_ablation_table.csv
    tables/constraint_ablation_table.csv
    tables/adversarial_results_table.csv
    figures/
    export_manifest.json
```

每张表都附带 `source_release` 和 `generated_at` 列，**数字全部来自
release，不是手工写死**。

## 三、paper_ready 规则

只有 `simclaim_paper_full` 才可能 `paper_ready=true`，且必须同时满足：

- readiness gate 通过（`scripts/check_paper_readiness.py`）
- `n_test >= 100`
- `threshold_source != test` 且 `test_threshold_tuning_detected=false`
- 全部 completion flag 为 true：
  - `strong_baselines_complete`
  - `calibration_ablation_complete`
  - `constraint_ablation_complete`
  - `adversarial_eval_complete`
  - `oracle_extracted_confidence_complete`
  - `bootstrap_ci_available`
  - `paired_significance_available`

其余数据集（`legacy_dev` / `human_pilot` / `candidate_pool` / `weak_train`）
**永远是 `paper_ready=false`**，`export_paper_tables.py` 会把它们的
`main_results` 导出为 `diagnostic_table.csv`（而不是 `main_results_table.csv`）。

## 四、禁止事项

以下行为严格禁止：

- ❌ 为换数据改模型代码（`cese/model/` 下的训练/评估代码）
- ❌ 在 baseline 脚本里写死数据路径
- ❌ 手工修改 `release_*/RESULTS_MANIFEST.json` 或 `release_*/tables/*.csv` 中的数字
- ❌ 手工把 `paper_ready` 改成 `true`
- ❌ 在 test split 上选阈值

## 五、常见问题

**Q：换数据后某一步失败怎么办？**
A：查看 `release_<dataset>/pipeline_summary.json` 中对应 stage 的
`stderr_tail`，修好数据/配置后重跑 pipeline。失败步不会阻止其它步生成
中间结果。

**Q：旧数据集的 release 还能用吗？**
A：可以。每个数据集有独立的 `release_simclaim_<dataset>/` 目录，互不覆盖。

**Q：如何只重跑某一步？**
A：直接调用对应的脚本并传 `--config`，例如：
```bash
python scripts/run_baselines.py --config configs/dataset_simclaim_human_pilot.yaml --fair-only
```
