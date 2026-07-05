# 导师审阅说明（V3.10.1 Advisor-Ready Silver-Stage, Encoding-Verified Clean）

**稿件版本：** CESE-OCN V3.10.1 Advisor-Ready Silver-Stage (Encoding-Verified Clean)
**日期：** 2026-07-04
**附件：**
- `CESE_OCN_V3_10_1_advisor_send_clean.md` / `.docx`（主稿）
- `V3_10_1_cleaning_log.md`（编码清理与格式核查日志）
- `V3_10_1_readiness_gate.json`（机器可读就绪门）

---

## 一、这是一版 silver-stage 完整稿

这一版是基于 V3.9 经过一轮"提交导师前的严苛一致性审计"后的小修版（V3.10）。审计结论是 **B 档**（小修后可发导师），全部问题都是表达和框架问题，不需要补实验。

所谓 **silver-stage**，是指：数据集的标签是 AI 预标注 + 作者人工筛查的 silver 标签，**不是** 经过两人独立标注 + 裁决的 gold 标签。所有 §VI 里的数字（R4 strong-F1 0.3967、LLM strong-F1 0.0769、macro-F1 差距、bootstrap CI 等）都是 silver 标签上的 pilot 结果。

这一点在主稿标题页、Abstract、§VI 开头、§VII 开头和 §X 结论里都明确写出了，没有任何地方把 silver 写成 gold。

---

## 二、主线已经定型

这版的主线是：

1. **任务定义**：科学声明验证不应只问 evidence 是否支持 claim，还应问 evidence 是否**足以支撑 claim 的强度**——尤其是当 claim 断言部署、行动、安全、泛化结论时。我们把它形式化为四类关系：supported / mild_scope_overclaim / strong_action_overclaim / contradiction_candidate。

2. **方法**：CESE-OCN R4，一个混合关系路由框架——先检矛盾，再升级 strong_action，最后用 SVM 残差分类 supported vs mild。阈值已冻结（t_contra=0.48, t_strong=0.535, t_svm=0.51）。

3. **核心发现（silver-stage）**：在受测的 prompt 下，通用 LLM judge（GPT-5.5、DeepSeek-V3）在 strong_action_overclaim 上明显欠检（strong_F1=0.0769，recall=0.04），而 R4 在同一批样本上 strong_F1=0.3000。R4 的整体 macro-F1 比 LLM 低（0.3280 vs 0.5523），所以 R4 定位为**关系级补充**而非替代。

4. **Gold 验证协议**：已冻结在 §VII 和独立的 `gold_validation_protocol_section.md`，50 条 blind gold pilot（25 高风险 + 16 可信 + 9 随机），Cohen's κ per-boundary，预注册的降级标准。Tables G1-G3 全部标记 `TO_BE_FILLED_AFTER_GOLD`，没有编造任何数字。

5. **诚实的局限**：作者 sanity audit 标记 40 条 silver 标签里 25 条（62.5%）为 questionable/unclear；R4 的 FP/TP 约 4.9（122 误报 / ~25 真实 strong_action），只能做 high-recall 筛选层，不能做最终自动标注器。

主线结构（Abstract → §I Introduction → §II Related Work → §III Task → §IV Framework → §V Data → §VI Results → §VII Planned Gold → §VIII Discussion → §IX Limitations → §X Conclusion）已经稳定，gold 结果回来后只需要填表 + 调限定语，不需要重写。

---

## 三、当前不请求导师判断实验是否最终成立

**这一版请导师判断的不是"实验是否成立"**，而是：

- **这个 taxonomy（四类 evidence sufficiency calibration）作为科学声明验证的新框架，是否值得做下去？**
- **R4 作为"关系级补充而非替代"的 positioning，是否站得住？**
- **strong_action_overclaim 作为一个独立类别，是否值得单独建模（而不是合并进 mild 或 contradiction）？**
- **§VII 的 gold 验证协议（50 条、κ 阈值、降级标准）是否合理，是否需要调整？**

之所以这样限定请求范围，是因为：silver 标签上的数字会因为 gold 标注而变化，现在请导师判断 silver 数字"是否成立"为时过早；但 taxonomy 和 positioning 是结构性判断，gold 之前就可以请导师把关。如果结构本身有问题，gold 做完也救不回来。

---

## 四、如果导师认可结构，下一步做 50 条 blind gold pilot

如果导师认为 taxonomy + positioning 值得继续，下一步是：

1. 按已冻结协议做 **50 条 blind gold pilot**（25 高风险 + 16 可信 + 9 随机）。
2. 两位标注者独立标注，裁决生成 gold 标签，计算 per-boundary Cohen's κ。
3. 填写 Tables G1-G3，对照预注册标准判断：
   - mild_vs_strong κ ≥ 0.40 → taxonomy 结构成立；
   - strong_action 保留率 ≥ 0.50 → strong_action 发现不降级；
   - R4 gold FP/TP ≤ 10 → 筛选定位成立；
   - 其余降级标准见 §VII.G。
4. 根据 gold 结果，把 §VI 的 silver 限定语升级为 gold 验证后的措辞，或按预注册标准降级相关声明。
5. 生成 V3.11 gold-validated 版（届时才考虑投稿判断）。

这一步预计 1-2 周（标注 + 裁决 + 填表 + 改稿）。

---

## 五、如果导师认为 taxonomy 不合适，先改结构再 gold

如果导师认为：

- 四类分法不合适（例如 strong_action 不该独立，或 mild_scope 不该单独成类）；
- 或 R4 的 screening 定位不成立（FP/TP 太高、macro-F1 太低，不值得做）；
- 或 evidence sufficiency calibration 这个 framing 本身有问题；

那么**先改结构，再 gold**。在错误的 taxonomy 上做 gold 是浪费标注成本。

可能的调整方向（仅供导师参考，不是预设结论）：
- 合并 mild_scope 和 strong_action 为单一 overclaim 类（降为三类）；
- 或保留四类但重新定义 strong_action 的边界（收紧或放宽）；
- 或把 R4 从"独立框架"降级为"LLM + 规则的混合后处理"。

这些调整都会触发 §VII 协议的相应修订（κ 阈值、降级标准、pilot 样本配比）。

---

## 附：本版做了什么 / 没做什么

**做了（纯表达层）：**
1. 标题页从"Not submission-ready"改为"Silver-stage pilot manuscript with a pre-registered gold validation protocol"。
2. §VI 开头加条件框架句（silver 结果 + gold 后降级预案）。
3. §VI 所有关键数字加"on silver labels"限定。
4. "pre-gold"从 ~19 次减到 4 次（Abstract / §VI / §VII / §X）。
5. 贡献改写为 pilot contribution（"We propose a pilot taxonomy..."）。
6. §VIII.A 补 R4 screening 合理性 + FP/TP ≈ 4.9。
7. §III.C 明确 strong_action 可分性是待验证假设。
8. §VI.D 外部数据集改为"External Transferability Probe"，不再说验证 taxonomy。
9. 清理所有乱码（§, ≥, κ, — 均为正常 UTF-8）。
10. 生成 .docx + 修订日志 + 本说明 + 就绪门 JSON。

**没做：**
- 没改 V3.9 原文件。
- 没跑新实验 / 没调 API / 没做 gold 标注。
- 没改任何实验数字。
- 没把 silver 写成 gold。
- 没填 gold_label / final_label / human_audited。

---

## 请导师反馈的 4 个具体问题

1. **Taxonomy**：四类（supported / mild_scope / strong_action / contradiction）是否值得做？strong_action 是否该独立？
2. **Positioning**：R4 作为"关系级补充"（不争 macro-F1，只补 strong_action）是否站得住？
3. **Gold 协议**：50 条 pilot、κ ≥ 0.40、降级标准是否合理？
4. **下一步**：认可结构 → 做 gold；不认可 → 先改结构。哪种？

---

*本说明为 V3.10 Advisor-Ready Silver-Stage 配套文件，不作为独立发表材料。*
