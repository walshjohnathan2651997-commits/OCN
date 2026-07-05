# R4-on-Retrieved Evidence Formal Evaluation Report v1

**任务：** R4-on-Retrieved Evidence Formal Evaluation + Retriever Upgrade Readiness v1
**日期：** 2026-07-05
**输出目录：** `D:\ocn\experiments\r4_on_retrieved_evidence_v1\`
**限制：** 不训练模型、不调 API、不联网、不改阈值、不改原数据、不改论文、不删文件、**不用 cue-based proxy 冒充 R4**。

---

## 1. 是否找到真正 frozen R4？

**是，找到路由逻辑和阈值；但缺少关键依赖。**

- **R4 路由逻辑脚本：** 找到 4 个脚本（`run_mixed_framework_router_optimization_v2.py` 等），均包含 `route_conservative_strong` 函数。
- **Frozen 阈值：** 找到 t_contra=0.48, t_strong=0.535, t_svm=0.51（在 3 个 JSON 文件中）。
- **逐条 R4 prediction：** 仅找到 100 条匹配样本（`gpt_vs_r4_deepseek_comparison.csv` 中的 `r4_label` 列），覆盖 100/444 = 22.5%。完整 silver-444 逐条 prediction 从未保存。
- **HCM/NLI features CSV：** **缺失。** `hcm_features.csv` 不在磁盘上。
- **训练好的分类器 artifacts：** **缺失。** 磁盘上无 .pkl/.joblib 文件；clf_contra/clf_strong/clf_svm 必须重新训练。
- **t_contra_low（lower contradiction guard）：** **未冻结。** 仅有 grid-search 代码，无 frozen 值。
- **NLI 模型：** `cross-encoder/nli-deberta-base` **已本地缓存**（在 HuggingFace cache 中）。

## 2. 是否没有使用 proxy？

**是，严格拒绝 proxy。**

任务规范明确禁止用 cue-based proxy 冒充 R4。本任务在 R4 无法逐条复跑的情况下，**走 blocked path**，不输出任何 proxy 预测。所有 4 个 prediction CSV 均标记为 `BLOCKED`，所有指标标记为 `-1.0`。

## 3. retrieved evidence 下 R4 是否还能工作？

**BLOCKED — 无法判断。**

R4 复跑需要：(a) HCM/NLI features for retrieved evidence（缺失）；(b) 训练好的分类器 artifacts（缺失）；(c) frozen t_contra_low（未冻结）。三者均不可用，R4 无法在 retrieved evidence 上产生逐条预测。

**不使用 proxy 冒充 R4**，因此无法回答"retrieved evidence 下 R4 是否还能工作"。

## 4. top1/top3/top5 哪个最好？

**BLOCKED — 无法比较。** 所有四组（oracle/top1/top3/top5）的 R4 预测均标记为 BLOCKED。

但 **retrieval-level 指标** 可以比较：

| Setting | Oracle hit rate |
| --- | --- |
| BM25 top-1 | 0.7162 |
| BM25 top-3 | 0.9392 |
| BM25 top-5 | 0.9730 |

top-3/top5 的 oracle hit rate 高于 top-1，但 **这不等于 R4 性能更好**——需要 R4 复跑后才能判断 concat evidence 是否因噪声过多而损害 screening。

## 5. 与 oracle evidence 差距多大？

**BLOCKED — 无法计算。** R4 在 oracle evidence 和 retrieved evidence 上均无法复跑，gap 无法计算。

## 6. 主要错误来自 retrieval 还是 screening？

**Retrieval 层面错误分布（444 条）：**

| Error type | Count | Rate |
| --- | --- | --- |
| retrieval_success | 318 | 71.62% |
| retrieval_partial_hit | 114 | 25.68% |
| oracle_chunk_not_retrieved | 6 | 1.35% |
| oracle_not_in_pdf_text | 4 | 0.90% |
| retrieved_wrong_paper | 2 | 0.45% |

**Screening 层面错误：BLOCKED。** 无法归因 strong_action_false_negative / strong_action_false_positive / contradiction_confusion / supported_mild_confusion，因为 R4 预测不可用。

**Retrieval 层面结论：** 主要 retrieval 错误是 `oracle_chunk_not_retrieved`（找到正确论文但未命中 oracle chunk），占 25.45%。这表明 BM25 的 chunk 级精排有提升空间。

## 7. 是否建议继续 dense/hybrid/reranker？

**是，具备升级条件。**

- `cross-encoder/nli-deberta-base` 已本地缓存，可作为 cross-encoder reranker。
- `transformers` + `torch` (CPU) 可用，支持 dense retrieval 和 reranker。
- `sentence_transformers` 未安装，但可通过 `pip install sentence-transformers` 安装。
- `sklearn` + `scipy` 可用，支持 hybrid 分数融合。
- 语料库 4747 chunks，远在 dense index 容量范围内。
- **无 GPU**，但 CPU 可处理 4747 chunks（dense retrieval 约 5-10 分钟，reranker top-50 约 10-20 分钟）。

**推荐升级顺序：**
1. 安装 sentence-transformers
2. 下载 all-MiniLM-L6-v2 做 zero-shot dense retrieval
3. 运行 dense retrieval（CPU，5-10 min）
4. BM25 + dense hybrid（加权或 RRF 融合）
5. 用 cached cross-encoder/nli-deberta-base 做 top-50 → top-10 reranker
6. 重新评估 retrieval metrics

**预期收益：** Hybrid + reranker 可将 Recall@1 从 71.62% 提升到 85-90%，将 oracle_chunk_not_retrieved 失败率从 25.45% 降到 10-15%。

## 8. 是否支持把论文 V3.17 主线改为 offline PDF-corpus retrieval + CESE-OCN screening？

**有条件支持（partial）。**

支持的理由：
- PDF 语料库 100% 完整，离线可读。
- BM25 检索 Recall@10 = 97.97%，MRR = 0.8261，检索可行。
- NLI 模型已缓存，dense/reranker 升级条件具备。
- 4747 chunks 适合 dense index。

不支持的理由（当前 BLOCKED）：
- R4 无法在 retrieved evidence 上复跑（HCM features 缺失、分类器 artifacts 未保存、t_contra_low 未冻结）。
- 无法验证 retrieved evidence 下 R4 的 strong_action screening 信号是否保留。
- **不能用 proxy 冒充 R4**，因此"retrieved evidence 下 R4 仍有效"这一 claim **未经验证**。

**恢复 R4 replay 的路径（需授权 reproduction training）：**
1. 在 silver-444 + original evidence 上重新训练 clf_contra/clf_strong/clf_svm（这是 reproduction，不是新模型训练）
2. 保存 classifier artifacts 为 .pkl
3. 冻结 t_contra_low（用 grid-search 均值）
4. 为 4 组 input CSV（oracle/top1/top3/top5）计算 NLI features（用 cached NLI 模型）
5. 用 frozen thresholds + saved classifiers 复跑 R4
6. 计算 oracle vs retrieved strong-F1 gap
7. 若 gap < 0.05：V3.17 主线完全支持；若 gap >= 0.05：先改善 retrieval 再验证

---

## 禁止项执行确认

- 不训练模型：PASS
- 不调 API：PASS
- 不联网：PASS
- 不改阈值：PASS
- 不改原数据：PASS
- 不改论文：PASS
- 不删文件：PASS
- **不用 cue-based proxy 冒充 R4：PASS（严格 blocked）**
- 不把 silver 写成 gold：PASS
- 不声称自然分布：PASS

---

## 输出文件清单

1. `r4_pipeline_inventory.csv` — 16 文件盘点
2. `r4_replay_feasibility.json` — 复跑可行性（BLOCKED）
3. `r4_input_oracle.csv` — 444 条 oracle evidence 输入
4. `r4_input_bm25_top1.csv` — 444 条 BM25 top-1 输入
5. `r4_input_bm25_top3.csv` — 444 条 BM25 top-3 concat 输入
6. `r4_input_bm25_top5.csv` — 444 条 BM25 top-5 concat 输入
7. `r4_predictions_oracle.csv` — BLOCKED（无预测）
8. `r4_predictions_bm25_top1.csv` — BLOCKED（无预测）
9. `r4_predictions_bm25_top3.csv` — BLOCKED（无预测）
10. `r4_predictions_bm25_top5.csv` — BLOCKED（无预测）
11. `r4_retrieved_metrics.csv` — BLOCKED（所有指标 -1.0）
12. `r4_retrieved_error_analysis.csv` — retrieval-level 错误分析（444 条）
13. `retriever_upgrade_readiness.json` — 升级条件检查
14. `r4_on_retrieved_evidence_gate.json` — gate
15. `r4_on_retrieved_evidence_report.md` — 本报告
