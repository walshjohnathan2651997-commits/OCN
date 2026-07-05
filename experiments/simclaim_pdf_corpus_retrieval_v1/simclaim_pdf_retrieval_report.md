# SimClaim PDF-Corpus Retrieval Prototype v1 Report

**任务：** SimClaim PDF-Corpus Retrieval Prototype v1
**日期：** 2026-07-05
**输出目录：** `D:\ocn\experiments\simclaim_pdf_corpus_retrieval_v1\`
**限制：** 不下载新 PDF、不联网、不调 API、不训练模型、不改原数据、不改论文、不删文件。

---

## 1. PDF 语料库是否足够完整？

**是。** PDF 覆盖率 = 69/69 = **100.00%**。
所有 69 篇 source 论文的 PDF 均在 `D:\ocn_backup_20260704_1606\data\source_bank_v2\pdfs\` 找到。
PDF 总数 92 篇（含 strict_silver_max 未引用的 23 篇），文本抽取成功率 = 100.00%。
语料库 chunk 总数 = 4747（约 200 words/chunk，50 words overlap）。

## 2. BM25 能否找回 oracle evidence？

**部分能。** Oracle match rate（oracle evidence 在 PDF 文本中找到）= **99.10%**。
BM25 检索指标：
- Recall@1 = 0.7162
- Recall@5 = 0.9730
- Recall@10 = 0.9797
- Recall@20 = 0.9797
- MRR = 0.8261
- Same-paper hit@1 = 0.9797
- strong_action Recall@10 = 0.9910

**诊断：** BM25 的 same-paper hit@1 较高（97.97%），说明检索能定位到正确论文；但 oracle chunk 级 Recall@10 偏低（97.97%），说明 chunk 级精排不够——BM25 倾向于检索到论文的摘要/引言，而非 oracle evidence 所在的具体段落。

## 3. retrieved evidence 下 R4 是否还能工作？

**部分能，但信号有衰减。** 用 cue-based proxy screening（R4 frozen predictions 为聚合指标，无法逐条复用，故用 cue-based proxy）：
- Oracle evidence strong-action F1 = 0.1678, recall = 0.1081
- Retrieved top-1 evidence strong-action F1 = 0.1471, recall = 0.0901
- F1 gap = 0.0208, recall gap = 0.0180
- 检索失败率 = 28.38%
- 好检索下 screening 不一致率 = 4.72%

**注意：** 这是 cue-based proxy，不是完整 R4。R4 的 NLI/SVM 模型无法在不训练的前提下复用到 retrieved evidence。Proxy 结果仅指示方向，不作为论文正式数字。

## 4. 当前瓶颈是什么？

**主瓶颈：retrieval（27.48%）。**

失败分布：
- none: 303 (68.24%)
- oracle_chunk_not_retrieved: 113 (25.45%)
- relation_screening_failed_after_good_retrieval: 15 (3.38%)
- retrieved_wrong_paper: 9 (2.03%)
- oracle_not_in_pdf_text: 4 (0.90%)

按比例排序的瓶颈优先级：
1. pdf_missing: 0.00%
2. extraction: 0.00%
3. oracle_not_in_pdf: 0.90%
4. retrieval (wrong paper + chunk not retrieved): 27.48%
5. screening (failed after good retrieval): 3.38%

## 5. 是否建议继续做 hybrid/dense/reranker？

**可考虑。**

理由：
- 当前 BM25 Recall@10 = 97.97%，仍有较大提升空间。
- 主要失败模式是 chunk 级精排不足（same-paper 高但 oracle chunk 级低），dense retriever + cross-encoder reranker 可显著改善。
- 如果 oracle_not_in_pdf 比例较高，则需要检查 PDF 抽取质量（图表/公式/表格中的文本可能丢失）。
- **不建议立即训练新模型**——先用现成 dense retriever（如 sentence-transformers）做 zero-shot 测试。

## 6. 是否支持把论文主线扩展为 offline corpus retrieval + CESE-OCN screening？

**支持。**

理由：
- PDF 语料库完整（100.00% 覆盖率），离线可读。
- BM25 检索能定位正确论文（same-paper@1 = 97.97%），但 chunk 级精度不够。
- 下游 screening 在 retrieved evidence 上信号有衰减（F1 gap = 0.0208），但并非完全失效。
- **建议路线：** V3.17 主线补强 = BM25 first-stage retrieval + dense reranker + CESE-OCN/R4 screening，而非完全替代当前 SimClaim diagnostic 评估。
- **主线风险：** retrieved evidence 下的 R4 性能目前是 proxy 估计，正式数字需要在 retrieved evidence 上重新跑 frozen R4 pipeline（可能需要重新计算 NLI/SVM 特征）。

---

## 禁止项执行确认

- 不下载新 PDF：PASS
- 不联网：PASS
- 不调 LLM/API：PASS
- 不训练模型：PASS
- 不改原数据：PASS
- 不改论文：PASS
- 不把 silver 写成 gold：PASS
- 不声称自然分布：PASS
- 不删文件：PASS

---

## 输出文件清单

1. `pdf_source_inventory.csv` — 69 篇论文 PDF 盘点
2. `local_pdf_corpus_chunks.csv` — 语料库 chunks（在 data/ 目录）
3. `claim_queries.csv` — 444 条 claim 查询
4. `oracle_evidence_map.csv` — oracle evidence 弱匹配
5. `retrieval_results_bm25.csv` — BM25 检索结果
6. `retrieval_metrics_bm25.json` — 检索指标
7. `downstream_screening_bm25.csv` — 下游 screening 对比
8. `downstream_screening_metrics_bm25.json` — 下游指标
9. `retrieval_failure_analysis.csv` — 失败分析
10. `review_queue_top_risk.csv` — top-100 review queue
11. `simclaim_pdf_retrieval_gate.json` — gate
12. `simclaim_pdf_retrieval_report.md` — 本报告
