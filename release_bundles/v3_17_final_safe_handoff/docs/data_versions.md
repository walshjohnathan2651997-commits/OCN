# Data Versions

This document tracks all data assets used in the ocn project. Each entry
notes the version, status, allowed usage, and whether it may serve as a
paper-ready benchmark.

---

## clean_v2 — pilot gold benchmark (NOT paper-ready)

- **Files**:
  - `data/clean_v2_all.jsonl`
  - `data/all_preannotated_annotations_clean_v2.csv`
  - `data/clean_v2_train.jsonl` / `data/clean_v2_dev.jsonl` / `data/clean_v2_test.jsonl`
- **Status**: pre-annotated + auto-derived, 80 samples (train 48 / dev 16 / test 16)
- **paper_ready**: false
- **Allowed usage**: pilot diagnostics, ablation smoke tests, metric-consistency checks
- **NOT allowed as**: main-paper test set (n_test=16 < 30, no human audit, single domain)

---

## simclaim_candidate_master_588_optimized_v2 — AI-preannotated candidate set

`simclaim_candidate_master_588_optimized_v2.csv` 是 50 篇论文自动生成并优化后的
AI-preannotated candidate set，共 588 条。它不是 human-audited gold benchmark，
不能作为 paper_ready 主实验测试集。它可以用于 weak training、人工审计候选池、
错误分析和后续数据扩展。真正论文主实验仍需人工审计样本。

- **Files**:
  - `data/candidates/simclaim_candidate_master_588_optimized_v2.csv`
  - `data/candidates/simclaim_candidate_master_588_optimized_v2.jsonl`
  - `data/candidates/simclaim_candidate_master_588_optimized_v2.xlsx`
- **Status**: `ai_preannotated_optimized_v2` (annotation_status field)
- **paper_ready**: false
- **human_audited**: false (all 588 rows)
- **Size**: 588 rows, 6 domains, 4 variant types × 147
- **Config**: `configs/data_candidate_588_optimized_v2.yaml`
- **Validation report**: `reports/candidate_optimization/validate_candidate_588_optimized_v2_report.md`
- **Known issues** (from validation):
  - 4 rows with empty `evidence_text` (paper014_packet001, all 4 variants) —
    flagged `evidence_too_short`; must be repaired or excluded before training
  - 20 samples flagged `possible_metadata_leakage` in quality_flags — review
    before using as training signal
  - 94 samples flagged `needs_human_review` (recommended_use)
- **Rule-based audit**: 见 [reports/candidate_optimization/rule_audit_report.md](../reports/candidate_optimization/rule_audit_report.md)
  - 审核输出: `data/candidates/simclaim_candidate_master_588_rule_audited.csv`
  - 结果: 588 条中 576 条 `rule_audited=true` (98%)，12 条 error 被拒绝
  - **rule_audited ≠ human_audited**: 规则审核仅过滤 schema 违规和启发式可疑样本，
    不构成人工标注。不可用于声明标注质量或计算 inter-annotator agreement。
- **Allowed usage**:
  - weak training candidate (建议只用 rule_audited=true 的样本)
  - human audit candidate pool (优先审 warning 样本，尤其 contradiction_candidate)
  - error analysis and data expansion
- **NOT allowed as**: paper-ready test set, gold benchmark, sole training source

### human_audit_round1_150 (priority audit subset)

- **Files**:
  - `data/human_audit/human_audit_round1_150_from_588_optimized_v2.csv`
  - `data/human_audit/human_audit_round1_150_from_588_optimized_v2.jsonl`
- **Status**: priority subset of the 588 candidate set selected for round-1
  human audit (150 samples)
- **paper_ready**: false (pending audit)
- **Allowed usage**: human annotation queue; once audited and adjudicated,
  the audited subset may seed a gold benchmark

---

## Isolation rules

- The 588 candidate set and the clean_v2 pilot set are kept in separate
  directories and must not be merged into a single gold benchmark.
- `clean_v2_*` files are never overwritten by candidate-set ingestion.
- The candidate set must not be used as the test set for any model trained
  on it (would constitute train/test leakage).
