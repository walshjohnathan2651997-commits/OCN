# 导师审阅说明（V3.11 High-Standard Framework）

**稿件版本：** CESE-OCN V3.11 High-Standard Framework (validation-pending, protocol-locked)
**日期：** 2026-07-04
**附件：**
- `CESE_OCN_V3_11_high_standard_framework.md` / `.docx`（主稿）
- `V3_11_strengthening_roadmap.md`（三层补强路线：立即可做 / 50 gold pilot / Q1 冲刺）
- `reviewer_risk_to_evidence_map.csv`（审稿风险-证据映射，12 条）
- `project_next_30_days_plan.md`（30 天项目计划）
- `V3_11_readiness_gate.json`（机器可读就绪门）

---

老师您好，这版我把论文重新整理为 **evidence sufficiency calibration** 的高标准框架稿。当前希望您主要判断三个问题：

1. **这个问题定义是否值得做。** 现有 scientific claim verification 只问 support/refute/NEI，但科学写作和 AI 辅助科研里更危险的是 overclaim——evidence 相关但不足以支撑 claim 的强度（部署、安全、泛化、行动结论）。我把它形式化为一个独立任务：evidence sufficiency calibration。

2. **四分类 taxonomy 是否值得保留。** 我定义了四个类：supported / mild_scope_overclaim / strong_action_overclaim / contradiction_candidate。其中 strong_action_overclaim 是高风险边界类，也是 LLM judge 系统性欠检的类。这个类的可分性是一个假设，不是已证明的事实——我已预注册 gold adjudication 来检验它（mild_vs_strong κ ≥ 0.40）。

3. **R4 作为 LLM strong_action screening complement 的定位是否成立。** 在受测 prompt 下，GPT-5.5 和 DeepSeek-V3 在 strong_action 上 strong-F1 都只有 0.0769（recall 0.04），而 R4 在同样样本上达到 0.3000。R4 的整体 macro-F1（0.3280）远低于 LLM（0.5523），所以 R4 不替代 LLM，而是作为 high-recall screening 层补充 LLM 漏检的 strong_action。

如果这三个方向认可，我再按已冻结协议做 50 条 blind gold pilot。

---

## 这版做了什么

V3.11 是在 V3.10.1 基础上的**叙事和框架重构**，没有跑新实验、没有调 API、没有做 gold、没有改任何实验数字。主要改动：

1. **主定位升级**：从"silver-stage pilot manuscript"改为"high-standard framework (validation-pending, protocol-locked)"。删除了"not submission-ready"、"workshop"、"pilot only"等低配表达。
2. **贡献从 4 条扩到 5 条**：(1) 问题形式化；(2) 四分类 taxonomy；(3) SimClaim controlled diagnostic benchmark；(4) CESE-OCN/R4 structured screening framework；(5) controlled silver-stage evidence + pre-registered validation。
3. **Gold validation 重新定位**：从"我们还没做 gold"的自我否定，改为"protocol-locked validation mechanism"——gold 是验证机制，不是 pending apology。预注册的降级标准是安全机制，不是弱点暴露。
4. **Results 表达**：所有关键数字用"on the controlled silver-stage evaluation"限定，不再反复求饶。
5. **补强路线**：三层（立即 / 50 gold / Q1 冲刺），每一项写清目的、输入、输出、能支撑的结论、失败时如何降级。
6. **审稿风险映射**：12 条 reviewer attack → current evidence → missing evidence → strengthening action。

---

## 当前不是什么

- 不是 gold-validated benchmark（gold pilot 是下一步，不是当前状态）。
- 不是 R4 全面超过 LLM（R4 macro-F1 0.3280 远低于 LLM 0.5523；R4 是 screening complement，不是 replacement）。
- 不是 workshop / pilot-only 定位（这是高标准框架稿，validation-pending）。
- 不是所有四类都已解决（strong_action 可分性是假设，gold 来检验）。

这些事实在主稿里都明确写出了，没有隐藏。

---

## 三个判断 + 下一步

| 导师判断 | 如果认可 | 如果不认可 |
| --- | --- | --- |
| 1. 问题定义值得做 | 进入 gold pilot | 重新找问题 |
| 2. 四分类 taxonomy 值得保留 | 50 gold pilot 检验 mild_vs_strong κ | 改为三类或重新定义边界 |
| 3. R4 screening complement 定位成立 | 50 gold pilot 检验 FP/TP 和 hybrid gain | 改为其他定位（如 LLM 后处理规则） |

**如果三个方向都认可**：按已冻结协议做 50 条 blind gold pilot（25 高风险 + 16 可信 + 9 随机），两人独立标注 + 裁决，计算 per-boundary κ 和 strong_action retention，填写 Tables G1–G3。预计 1–2 周。

**如果某个方向不认可**：先改结构再 gold。在错误的 taxonomy 或定位上做 gold 是浪费标注成本。

---

## 最大剩余风险

**silver 标签 62.5% questionable/unclear**（作者 sanity audit）。这意味着所有 silver-stage 数字（R4 strong-F1 0.3967、LLM strong-F1 0.0769、gap +0.2231）都可能因为 gold 而变化。但：

- 25/40 questionable/unclear 里，48% 是 mild_vs_strong 边界本来就难的 case，24% 是 audit heuristic 问题（decision tree 已修），20% 是 claim 生成问题，8% 是 audit 太严。只有很小一部分是 label noise。
- 相对模式（R4 > LLM on strong_action）可能在 gold 下仍然成立，即使个别 label 变化。
- 如果 gold 不支持，§VII.G 预注册了降级标准——paper 会降级但不会崩盘。

这个风险是已知的、已披露的、有预案的。它不构成压稿理由，但构成了"必须做 gold pilot"的理由。

---

## 请导师反馈

1. **问题定义**：evidence sufficiency calibration 作为独立任务，是否值得做？
2. **Taxonomy**：四分类（尤其 strong_action 独立成类）是否值得保留？
3. **R4 定位**：screening complement（不争 macro-F1，补 strong_action）是否成立？
4. **下一步**：认可 → 50 gold pilot；不认可 → 先改结构。哪种？

---

*本说明为 V3.11 High-Standard Framework 配套文件。主稿、补强路线、审稿风险映射、30 天计划、就绪门 JSON 均在同级目录。*
