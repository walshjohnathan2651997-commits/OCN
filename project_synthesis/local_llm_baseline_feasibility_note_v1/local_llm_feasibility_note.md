# Local LLM Baseline Feasibility Note v1

- 审计时间: 2026-07-05
- 任务性质: 可行性分析与论文定位说明（不部署、不运行、不下载模型）
- 禁止: 不下载本地 LLM, 不安装 Ollama/LM Studio, 不联网, 不调 API, 不运行推理, 不训练模型
- 输入: canonicalized_risk_ranking_v1, canonicalized_review_queue_v1, canonical_selector_robustness_v1, r4_evidence_canonicalization_v1, current_project_state_consolidation_clean_v1

---

## 1. 现在是否需要部署本地 LLM？

**否。**

理由：

1. **当前论文主线不是"R4 超过 local LLM"。** 论文的核心贡献是：(a) hierarchical diagnostic taxonomy；(b) retrieval-to-screening interface 的必要性；(c) evidence canonicalization 修复 format shift；(d) R4 作为 Level-2 high-risk strong_action screening complement。这些贡献不依赖 local LLM 对比实验。

2. **已有 LLM baseline（API-based）已覆盖对比需求。** 项目已完成 GPT-5.5 (matched 100, macro_F1=0.5523, strong_recall=0.04) 和 DeepSeek-V3 (200 samples, macro_F1=0.5270, strong_recall=0.04) 的 API-based LLM baseline。结果显示 LLM 在 strong_action 上高度保守（pred_strong_rate=0.04 vs R4=0.36, 9x gap），R4 捕获了 8 个 LLM 漏判的 strong_action 案例。这一对比已足够支撑"R4 是 LLM 的 screening complement"这一论文定位。

3. **部署 local LLM 的成本和风险高于当前收益。** 部署需要：(a) 硬件资源（GPU 内存 ≥16GB for 7B 模型）；(b) 模型来源与版本冻结（需指定具体 model checkpoint）；(c) 安全审批（本地模型部署可能涉及机构审查）；(d) 解析稳定性（structured output 解析失败率需要控制）；(e) 可复现性保障（model version + prompt version + temperature 全部冻结）。在当前 silver-stage，这些成本无法被论文收益覆盖。

4. **当前最关键的 next action 是 gold adjudication，不是 local LLM。** §VII 50-pair two-layer gold pilot（Layer 1 relation + Layer 2 realism）是决定四级分层 taxonomy 是否成立的关键实验。如果 gold adjudication 显示 Level-2 κ < 0.40，论文需 fallback 到三级 + binary screening。这一实验的优先级远高于 local LLM baseline。

---

## 2. 没有 local LLM baseline 是否会致命？

**否。**

理由：

1. **论文已有 API-based LLM baseline。** GPT-5.5 和 DeepSeek-V3 的结果已经建立了"LLM 在 strong_action 上保守"这一发现。审稿人不能说"没有 LLM baseline"——只是没有 local LLM baseline。

2. **Local LLM 和 API-based LLM 的差异是部署方式的差异，不是方法本质的差异。** 在 strong_action screening 任务上，local LLM（如 Qwen-7B、Llama-3-8B）与 API-based LLM（GPT-5.5、DeepSeek-V3）的核心差异在于模型规模和微调程度，而非"是否本地部署"。如果 API-based LLM 已经保守，没有先验理由认为 local LLM 会显著不同。

3. **论文的 contribution structure 不要求 local LLM 对比。** 论文声称的是：
   - R4 是 screening complement（不是 overall-beats-LLM）
   - Retrieval-to-screening interface 需要 canonicalization
   - Hierarchical taxonomy 优于 flat four-class
   
   这些声称都不需要 local LLM baseline 来验证。

4. **潜在风险可控。** 如果审稿人要求 local LLM 对比，可以在 rebuttal 阶段补充 120 条 pilot 实验（见 future_work_protocol）。这不阻塞当前投稿。

---

## 3. 审稿人会如何评价？

审稿人可能会提出以下质疑：

### 质疑 1: "为什么不用 Qwen/Llama/DeepSeek 本地模型？"

**回答策略:** 承认 local LLM 是合理替代方案，但解释当前重点不同。

- Local LLM（Qwen-7B, Llama-3-8B, DeepSeek-V3 local deployment）是合理的 strong_action screening baseline
- 但本文的重点不是证明 R4 超过 local LLM，而是证明 retrieval-to-screening interface 和 evidence canonicalization 的必要性
- API-based LLM baseline (GPT-5.5, DeepSeek-V3 API) 已覆盖 LLM 对比需求
- Local LLM baseline 作为 future work 列出（见 §VIII future work + future_work_protocol）

### 质疑 2: "R4 是否只是 heuristic，不如 learned model？"

**回答策略:** 承认 R4 是 heuristic router，但解释其 screening value。

- R4 是 relation-specific screening router，不是 flat 4-class best classifier
- R4 macro_F1 (0.3280) < LLM (0.5523)，这是已知的
- 但 R4 strong_recall (0.36) >> LLM (0.04)，9x gap
- R4 捕获 8 个 LLM 漏判的 strong_action 案例
- R4 的价值在于 high-recall first-stage screening，不是 overall precision

### 质疑 3: "Silver labels 是否可信？"

**回答策略:** 承认 silver labels 是 limitation，但有 gold protocol。

- 所有实验是 silver-stage evidence
- §VII 50-pair two-layer gold pilot 是 pre-registered protocol
- Gold adjudication 将决定 Level-2 boundary 是否 reliable
- §VII.K fallback rules 提供 graceful-degradation path

### 质疑 4: "SimClaim 是 counterfactual，不是 natural distribution？"

**回答策略:** 承认这是设计属性，不是缺陷。

- SimClaim 是 controlled counterfactual diagnostic set，不是 natural-prevalence corpus
- Balanced four-way design 是 deliberate for diagnostic pressure-testing
- §VII.J Layer 2 realism audit 将评估 natural-claim transferability
- Low-prevalence simulation (1%-25%) 已模拟 natural deployment scenario

---

## 4. 现在怎么回应最稳？

**推荐策略: 列为 future work + optional baseline，不阻塞当前投稿。**

具体操作：

1. **在 §VIII Limitations 中新增一段:**
   > "本研究的 LLM baseline 基于 API-based models (GPT-5.5, DeepSeek-V3)。Local LLM models (如 Qwen, Llama) 作为替代部署方案尚未测试。由于 API-based LLM 已显示 strong_action 保守倾向 (pred_strong_rate=0.04)，且 R4 的定位是 screening complement 而非 LLM 替代品，local LLM baseline 不影响本文核心结论。未来工作将测试 local LLM 在 canonicalized evidence 上的 strong_action screening 表现（见 Appendix X future work protocol）。"

2. **在 §VIII Future Work 中新增一段:**
   > "Future work will evaluate local LLM models (Qwen-7B, Llama-3-8B) as alternative strong_action screeners using the canonicalized evidence pipeline. The experiment protocol is pre-registered in Appendix X, including zero-shot structured prompting, temperature=0, JSON output, and 120-pair pilot on SimClaim. The comparison will focus on: (a) strong_action recall/F1 vs R4; (b) R4 captured LLM-missed cases; (c) deployment cost-precision tradeoff."

3. **不修改任何实验结果或表格。** 所有现有数字保持 byte-identical。

4. **在 rebuttal 准备中，预备 120-pair pilot 的执行计划。** 如果审稿人明确要求，可以在 rebuttal 阶段执行。

---

## 5. 未来如果做，最小实验怎么做？

**最小实验协议（120 条 pilot，不要求现在执行）:**

### 实验设计

| 项目 | 规格 |
|------|------|
| 模型 | Qwen-7B-Chat 或 Llama-3-8B-Instruct（选一个，冻结版本） |
| 数据 | SimClaim 120 条 pilot（从 444 中分层抽样，保持 4-class balance） |
| Evidence | Canonicalized evidence (best_sentence_from_top5_overlap，与 R4 相同输入) |
| Prompt | Zero-shot, structured, relation-typed screening prompt |
| Temperature | 0 (greedy decoding) |
| Output format | JSON: `{label: supported/mild_scope_overclaim/strong_action_overclaim/contradiction_candidate, confidence: 0-1, reasoning: text}` |
| 解析失败处理 | Retry once with repair prompt; if still fails, mark as `parse_failure` |

### 比较指标

1. **Strong_action recall/F1:** Local LLM vs R4 (silver 444) vs API-based LLM (matched 100)
2. **R4 captured LLM-missed:** 统计 R4 正确但 local LLM 漏判的 strong_action 数量
3. **LLM captured R4-missed:** 统计 local LLM 正确但 R4 漏判的 strong_action 数量
4. **Complementarity:** 50/100 matched samples 是否仍有 R4-LLM 互补模式
5. **Deployment cost:** Latency per sample, GPU memory, parse failure rate

### 判定标准

- 如果 local LLM strong_recall > 0.20（远高于 API-based LLM 的 0.04），则 local LLM 可能是 R4 的有效补充
- 如果 local LLM strong_recall ≤ 0.10（与 API-based LLM 相似），则确认 LLM conservatism 是任务固有难度，不是 API 限制
- 无论结果如何，不影响"R4 是 screening complement"的定位

### 注意事项

- 不要求 gold labels（silver-stage pilot）
- 不要求大规模实验（120 条足够评估趋势）
- 不要求多模型对比（选一个代表性模型即可）
- 结果必须标注"small-sample pilot, N=120, silver labels"
- 不与 SimClaim main results 合并

---

## 6. 是否影响当前 V3.17 主线？

**否。**

V3.17 主线的核心证据链已经完整：

| 环节 | 实验 | 结果 | Gate |
|------|------|------|------|
| PDF retrieval feasible | simclaim_pdf_corpus_retrieval_v1 | BM25 retrieval successful | PASS |
| Raw chunk degrades screening | r4_retrieved_replay_v1 | oracle F1=0.3969, top1 F1=0.2166, gap=0.1803 | CONFIRMED |
| Canonicalization restores screening | r4_evidence_canonicalization_v1 | best_sentence_from_top5 F1=0.4503 > oracle 0.4257 | PASSED |
| Selector robust | canonical_selector_robustness_v1 | 6/9 selectors above 0.40, robustness_passed=True | PASSED |
| Review queue second-stage | canonicalized_review_queue_v1 | FP/TP@5%=12.84, second_stage_viable=True | PASSED |
| Ranking calibration | canonicalized_risk_ranking_v1 | P@20 0.35→0.45, FP/TP@5%=11.24, second_stage_usable=True | PASSED |
| R4 not standalone | canonicalized_risk_ranking_v1 | FP/TP@1%=58.73>50, standalone_usable=False | CONFIRMED |
| Local LLM comparison | (future work) | Not executed | FUTURE WORK |

**结论:** V3.17 主线可以不依赖 local LLM baseline 继续推进。Local LLM baseline 列为 future work / optional baseline，不影响核心证据链。

---

## 输出文件清单

- local_llm_feasibility_note.md (本文件)
- local_llm_alternative_risk_table.csv
- local_llm_future_work_protocol.md
- local_llm_gate.json
