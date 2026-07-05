# Local LLM Baseline Future Work Protocol v1

- 创建时间: 2026-07-05
- 状态: PROTOCOL ONLY — 不要求现在执行
- 禁止: 当前不下载模型, 不部署, 不运行推理

---

## 1. 实验目标

在 SimClaim canonicalized evidence pipeline 上测试 local LLM 的 strong_action screening 表现，与 R4 和 API-based LLM (GPT-5.5, DeepSeek-V3) 进行对比。

**核心问题:** Local LLM (Qwen-7B / Llama-3-8B) 在 strong_action screening 上是否比 API-based LLM 更激进（更高 recall），从而可能替代或补充 R4？

---

## 2. 实验设计

### 2.1 模型选择

| 候选模型 | 参数量 | 推荐度 | 理由 |
|---------|--------|--------|------|
| Qwen-7B-Chat | 7B | 推荐 | 中文支持好, structured output 稳定 |
| Llama-3-8B-Instruct | 8B | 备选 | 英文强, 通用 instruction following 好 |
| DeepSeek-V3 (local) | 671B | 不推荐 | 参数过大, 部署成本高, API 版本已测试 |

**选择规则:** 选一个 7B-8B 模型即可，不需要多模型对比。冻结 model checkpoint 和 tokenizer 版本。

### 2.2 数据

- **来源:** SimClaim 444 silver pairs
- **Pilot 样本:** 120 条（从 444 中分层抽样，保持 4-class balance: 30 supported + 30 mild + 30 strong + 30 contradiction）
- **Evidence:** Canonicalized evidence (best_sentence_from_top5_overlap，与 R4 Task I/K 相同输入)
- **注意:** 120 条 pilot 必须标记 `paper_ready=false, diagnostic_only=true`

### 2.3 Prompt 设计

**Zero-shot, structured, relation-typed screening prompt:**

```
You are a claim verification expert. Given a claim and evidence from a scientific paper, classify the claim-evidence relationship into one of four categories:

1. supported: The evidence directly supports the claim.
2. mild_scope_overclaim: The claim slightly overstates what the evidence shows (scope expansion).
3. strong_action_overclaim: The claim substantially overstates the evidence, attributing actions, results, or capabilities not present in the evidence.
4. contradiction_candidate: The evidence contradicts the claim.

Claim: {claim_text}
Evidence: {evidence_text}

Respond in JSON format:
{
  "label": "supported|mild_scope_overclaim|strong_action_overclaim|contradiction_candidate",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}
```

### 2.4 推理参数

| 参数 | 值 | 理由 |
|------|----|------|
| Temperature | 0 | Greedy decoding, 确保可复现 |
| Max tokens | 512 | 足够覆盖 JSON + reasoning |
| Top-p | 1.0 | 不截断 |
| Seed | 42 | 固定随机种子 |
| Repetition penalty | 1.0 | 不惩罚 |

### 2.5 输出解析

- 期望输出: JSON object with `label`, `confidence`, `reasoning`
- 解析规则:
  1. 尝试 `json.loads()` 直接解析
  2. 如果失败, 尝试提取 `{...}` 子串后解析
  3. 如果仍失败, retry once with repair prompt: "Your previous response was not valid JSON. Please respond with ONLY a JSON object."
  4. 如果 retry 仍失败, 标记为 `parse_failure`, 不参与指标计算但记录数量

---

## 3. 比较指标

### 3.1 主指标

| 指标 | R4 (silver 444) | API LLM (matched 100) | Local LLM (pilot 120) |
|------|-----------------|----------------------|----------------------|
| strong_action F1 | 0.3967 | 0.0769 | TBD |
| strong_action recall | 0.4562 | 0.04 | TBD |
| strong_action precision | 0.3791 | 1.0 (1/1) | TBD |
| macro_F1 | 0.4238 | 0.5523 | TBD |
| pred_strong_rate | 0.36 | 0.04 | TBD |

### 3.2 互补性分析

- **R4 captured LLM-missed:** R4 正确但 local LLM 漏判的 strong_action 数量
- **LLM captured R4-missed:** local LLM 正确但 R4 漏判的 strong_action 数量
- **Both correct / both wrong:** 统计四种组合
- **Complementarity score:** (R4-only-correct + LLM-only-correct) / total

### 3.3 部署成本

| 指标 | 说明 |
|------|------|
| Latency per sample | 平均推理时间 (秒) |
| GPU memory peak | 峰值显存 (GB) |
| Parse failure rate | JSON 解析失败比例 |
| Model size on disk | 模型文件大小 (GB) |

---

## 4. 判定标准

| 场景 | 条件 | 结论 |
|------|------|------|
| Local LLM 有价值 | strong_recall > 0.20 AND macro_F1 > 0.40 | Local LLM 是 R4 的有效补充, 值得扩大实验 |
| Local LLM 与 API LLM 相似 | strong_recall ≤ 0.10 | LLM conservatism 是任务固有难度, 不是 API 限制 |
| Local LLM 优于 R4 | strong_F1 > 0.45 AND strong_recall > 0.50 | Local LLM 可能替代 R4 作为 screener (需 gold 验证) |
| 无论如何 | - | 不影响"R4 是 screening complement"的论文定位 |

---

## 5. 注意事项

1. **不要求 gold labels。** 这是 silver-stage pilot, 结果必须标注 "small-sample pilot, N=120, silver labels"。
2. **不与 SimClaim main results 合并。** Pilot 结果独立报告。
3. **不声称 natural distribution。** SimClaim 是 counterfactual diagnostic set。
4. **不修改 R4 thresholds。** R4 使用 frozen thresholds (t_contra=0.48, t_strong=0.535, t_svm=0.51)。
5. **不修改论文。** Pilot 结果如果执行, 在 rebuttal 或 future version 中报告。
6. **模型版本必须冻结。** 记录 model checkpoint, tokenizer version, prompt version, temperature, seed。
7. **解析失败必须记录。** 不能静默丢弃 parse_failure 样本。

---

## 6. 执行前检查清单

- [ ] 获得硬件资源（GPU ≥ 16GB VRAM）
- [ ] 获得模型部署安全审批（如需要）
- [ ] 冻结 model checkpoint 版本
- [ ] 准备 120 条 pilot 样本（分层抽样）
- [ ] 准备 canonicalized evidence（从 Task I/K 复用）
- [ ] 测试 prompt 的 JSON output 稳定性（先跑 5 条）
- [ ] 确认 temperature=0 的可复现性
- [ ] 记录所有版本信息（model, prompt, code commit hash）

---

## 7. 预期输出（如果执行）

| 文件 | 内容 |
|------|------|
| local_llm_pilot_predictions.csv | 120 条预测结果 (candidate_id, true_label, pred_label, confidence, reasoning, parse_status) |
| local_llm_pilot_metrics.json | 主指标 (strong_F1, strong_recall, macro_F1, pred_strong_rate) |
| local_llm_complementarity.csv | R4 vs local LLM 互补性分析 |
| local_llm_pilot_gate.json | Gate (pilot_completed, local_llm_value, recommended_next_step) |
| local_llm_pilot_report.md | 中文报告 |

**注意:** 以上文件仅在实际执行后生成。当前只提供 protocol, 不生成任何结果文件。
