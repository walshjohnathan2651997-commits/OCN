# V3.18 Intelligent Upgrade on V3.17 Baseline v1 — Report

**Date:** 2026-07-05T21:01:42
**Output dir:** D:\ocn\experiments\v3_18_intelligent_upgrade_v1
**Baseline frozen:** Yes (V3.17 baseline not modified)

---

## 1. V3.17 baseline 是否冻结？

是。V3.17 baseline 已在 v3_17_frozen_baseline_metrics.json 中冻结，包含全部关键指标（strong_F1=0.4503，strong_recall=0.7064，P@20=0.45，R@100=0.3303，FP/TP@5%=11.24，second_stage_usable=true，standalone_usable=false）。本任务期间未修改 baseline，未修改论文，未调用 API，未联网。

## 2. learned evidence selector 是否超过 best_sentence_top5_overlap？

否。learned evidence selector 的 strong_F1 = 0.4444，相比 baseline 的 0.4503 下降 -0.0059，selector_upgrade_passed=false。最优 sklearn 模型为 rf。该结果作为 negative result 保留，说明在当前 NLI 特征 + BM25 + overlap 标签下，learned selector 暂未超过手工 overlap selector。

**Selector training data:** 444 candidates × ~16.8 sentences = ~7439 candidate sentences; positive/negative pseudo labels via oracle overlap (top 30% = positive, bottom 50% = negative; per-candidate).

**Group-aware split:** train=77 groups, dev=16 groups, test=18 groups; no group leakage.

**Learned selector matches baseline best_sentence_top5_overlap on 285/444 candidates.**

## 3. learned risk ranker 是否提升 review queue？

否/部分。learned risk ranker 的 P@20 = 0.3500（baseline=0.45，gap=-0.1000），R@100 = 0.3303（baseline=0.3303，gap=-0.0000），FP/TP@5% = 2.00（baseline=11.24）。未同时满足 P@20 ≥ 0.50 或 R@100 ≥ 0.40 且 FP/TP@5% ≤ 11.24 的成功判定，ranker_upgrade_passed=false。最优 sklearn 模型为 logreg。该结果作为 negative/partial result 保留。

**Ranker training data:** 436 candidates (canonicalized R4 output + ranking features), label = is_strong_action (109 positive).

**Group-aware split:** train=76 groups, dev=16 groups, test=17 groups; no group leakage.

**Held-out test metrics (best model logreg):**
- AP = 0.3720
- AUC = 0.6740
- P@10 = 0.4000
- P@20 = 0.3500
- P@50 = 0.4000
- P@100 = 0.3600
- R@10 = 0.0367
- R@20 = 0.0642
- R@50 = 0.1835
- R@100 = 0.3303
- FP/TP@1% = 0.33
- FP/TP@5% = 2.00
- FP/TP@10% = 1.69
- Review burden = 0.2294

## 4. 智能化补强是否显著优于规则 baseline？

否。V3.18 智能化补强未显著优于规则 baseline：selector_upgrade_passed=False，ranker_upgrade_passed=False。最优综合方法为 V3.17_baseline（strong_F1=0.4503，P@20=0.4500，R@100=0.3303）。在当前特征空间（NLI + BM25 + action gap + selector/ranker scores）和 sklearn 轻量模型下，learned 模块未稳定超过手工规则。

**Comparison table:**

| Method | Selector | Ranker | strong_F1 | strong_recall | macro_F1 | P@20 | R@100 | FP/TP@5% | 2nd-stage usable |
|---|---|---|---|---|---|---|---|---|---|
| raw_bm25_top1 | raw_top1 | none | 0.1806 | - | - | - | - | - | - |
| V3.17 baseline | best_sentence_top5_overlap | G_conservative_precision | 0.4503 | 0.7064 | - | 0.45 | 0.3303 | 11.24 | True |
| learned_selector_only | learned | G (baseline) | 0.4444 | 0.6972 | 0.3685 | - | - | - | - |
| learned_ranker_only | best_sentence_top5 (baseline) | learned | 0.4503 | 0.7064 | - | 0.3500 | 0.3303 | 2.00 | True |
| learned_selector + learned_ranker | learned | learned | 0.4444 | 0.6972 | 0.3685 | 0.3500 | 0.3303 | 2.00 | True |

## 5. 如果没有明显提升，说明什么？

可能的原因：（1）特征空间已饱和——V3.17 baseline 的 NLI + BM25 + action gap 特征已被手工规则充分利用，learned 模型在相同特征上难以提取额外信号；（2）标签质量限制——selector 训练标签为 oracle overlap pseudo label，并非真实 evidence 标注，可能引入噪声；（3）样本规模小——436 candidates、7439 sentences 不足以训练复杂 learned 模型；（4）R4 routing 是 hard threshold 决策，learned selector 即使选出更好的 evidence，也受限于 R4 三路由分类器的判别能力；（5）ranker 受限于 R4 输出的 p_strong/p_contra/p_svm，无法恢复被 R4 漏掉的 true strong_action（32 个 r4_screening_failure）；（6）strong_action 边界本身在 silver label 上有 75% confusion（§V.D audit），learned 模型无法在 silver 噪声上突破。这说明当前提升空间不在 selector/ranker 的 learned 化，而在于：(a) 引入新的特征（如 evidence-force contrastive），(b) 引入更强的语义模型（local LLM），或 (c) 通过 gold adjudication 修正标签噪声。

## 6. 当前最佳方法应写成 V3.17 baseline 还是 V3.18 intelligent upgrade？

当前最佳方法应写成 V3.17 baseline。V3.18 intelligent upgrade 作为 exploratory negative result 保留，可用于 §VIII limitations 或 §IX future work，说明 attempted learned upgrade 在当前特征空间下未显著超过规则 baseline。论文主线保持 V3.17，不改写为 V3.18。

## 7. 下一步是否需要 local LLM baseline 或 evidence-force contrastive？

建议优先级：（1）evidence-force contrastive——当前 selector 受限于 NLI + overlap 特征，evidence-force contrastive（在同一 claim 上强制错误 evidence vs 正确 evidence 的 NLI 差异作为新特征）可能为 selector 提供更强信号，且无需 API/网络；（2）local LLM baseline——如 Qwen-7B / Llama-3-8B，可作为 §VII future work 的预注册 120-pair pilot（参见 local_llm_baseline_feasibility_note_v1）；（3）gold adjudication——修正 silver label 噪声后再评估 learned 模块，避免噪声标签低估 learned 模型潜力。如果 V3.18 整体未通过，建议先做 evidence-force contrastive（成本最低），再做 local LLM pilot，最后做 gold。

---

## Error analysis summary

{
  "selector_helped": 26,
  "selector_harmed": 26,
  "selector_neutral": 384,
  "ranker_helped": 39,
  "ranker_harmed": 39,
  "ranker_neutral": 358,
  "both_helped": 0,
  "both_failed": 1,
  "partial_help": 65,
  "no_change": 370,
  "strong_action_false_negative": 33,
  "strong_action_false_positive": 157,
  "screening_recovery": 9,
  "screening_loss": 0,
  "screening_neutral": 237,
  "ambiguous_mild_strong": 72,
  "evidence_selection_failure": 25
}

---

## Prohibitions enforced

- no V3.17 baseline modification
- no paper modification
- no API calls
- no network
- no gold labels for selector (oracle overlap pseudo-label only)
- no test-set strong-F1 reverse tuning
- no R4 retraining / threshold change
- no proxy
- no silver-as-gold
- no natural-distribution claim
- sklearn only (no new packages)
- group-aware split mandatory (no test leakage)

## Output files

1. v3_17_frozen_baseline_metrics.json
2. learned_selector_training_data.csv
3. learned_selector_predictions.csv
4. learned_selector_metrics.csv
5. learned_ranker_training_data.csv
6. learned_ranker_results.csv
7. intelligent_upgrade_comparison_table.csv
8. intelligent_upgrade_error_analysis.csv
9. v3_18_intelligent_upgrade_gate.json
10. v3_18_intelligent_upgrade_report.md
