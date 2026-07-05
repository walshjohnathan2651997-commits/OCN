# 导师说明（V3.12.1）

**版本：** V3.12.1 Advisor Send Clean
**日期：** 2026-07-04
**状态：** 可发导师（silver-stage，gold adjudication 未完成）

---

## 一、本次提交版本

V3.12.1 是基于 V3.12 的乱码清理 + 措辞稳健化版本，用于发导师审阅。

**与 V3.12 的差异（仅此两项）：**

1. **乱码扫描：** 对 25 种常见乱码模式（含用户列出的 19 种 + 6 种 Latin-1 误读模式）做全文件扫描，**0 命中**。V3.12 本身已是干净的 UTF-8 编码，使用正确的 Unicode 字符（§ κ Δ ≥ − — –），无需替换。
2. **措辞稳健化：** 摘要和 §I 引言中 2 处 "systematically under-detect" 改为 "consistently under-detect"。两处上下文均已含 "under the tested prompts" 限定词，无需额外添加。**strong_action under-detection 主结论保留不变**（LLM strong-F1=0.0769, recall=0.04；R4 strong-F1=0.3000）。

**未改动：** 实验数字、§VIII.D 三项 credibility checks、non-gold caveat、50% retention caveat、R4 macro-F1 < LLM 事实、gold 未完成事实、§VII gold validation protocol、frozen R4 阈值、taxonomy 边界规则。V3.12 / V3.11 / V3.10.1 / V3.9 原文件全部保留不变。

## 二、论文当前主线（一句话）

在 controlled silver-stage evaluation 上，R4 作为 screening-oriented complement，在 strong_action_overclaim 上提供 LLM judges 所缺乏的 targeted screening signal（R4 strong-F1=0.3000 vs LLM=0.0769），代价是 overall macro-F1 更低（0.3280 vs 0.5523）；gold adjudication（§VII）是 protocol-locked 验证机制，尚未执行。

## 三、V3.12 新增的 §VIII.D 三项非 gold credibility checks

**类型：非 gold 鲁棒性分析，不替代 gold adjudication。**

### A. Evidence Necessity Check（证据必要性检查）
- correct evidence accuracy = 0.4324，empty = 0.2545，shuffled = 0.3851，same-domain wrong = 0.2568
- TF-IDF：correct sim = 0.4131，empty = 0.0000，same-domain wrong = 0.0124
- shuffled TF-IDF 与 correct 相同（bag-of-words 不变性），由 NLI audit（order-sensitive）区分
- TF-IDF/NLI 相关性 r = −0.2736，二者捕捉不同维度（surface overlap vs semantic entailment），互补非冗余
- **结论：** evidence perturbation *suggests* task is evidence-sensitive（不说 proves fully relies on evidence）

### B. Screening Utility Test（筛查实用性测试）
- matched-100：TP=9, FP=26, FN=16, precision=0.257, recall=0.36, positive-F1=0.300
- FP/TP = 2.89（低于预注册阈值 10）
- R4 captures 8 strong_action cases that LLM missed
- 实际 FP 分布：supported→strong=12, mild→strong=13, contradiction→strong=1
- **结论：** R4 provides targeted recall-improving screening signal（不说 high-recall detector without qualification，不说 final automatic labeler）

### C. Label-Shift Stress Test（标签缩水压力测试）
- 1000 次 bootstrap，break-even retention ≈ 0.5
- 60% retention：Δ=+0.1408, CI=[+0.035, +0.28]，98.6% wins → **marginal-positive**（CI 下界刚高于 0）
- 50% retention：Δ=+0.1137, CI=[−0.026, +0.255]，94.2% wins → **positive but statistically weaker / CI crosses zero**（不写稳健通过）
- <50% retention：按 §VII.G 降级
- **结论：** gold retention ≥ 60% → stronger support；50% → point estimate positive but uncertainty crosses zero；<50% → downgrade

## 四、关键数字（全部保留，未改动）

| 指标 | 值 |
|---|---|
| R4 strong_action positive-F1（silver） | 0.3967 |
| LLM strong_action F1（matched） | 0.0769 |
| R4 strong_action F1（matched-100） | 0.3000 |
| R4 macro-F1（matched-100） | 0.3280 |
| GPT-5.5 macro-F1（matched-100） | 0.5523 |
| 绝对差距（R4 - LLM, strong_action） | +0.2231 |
| FP/TP ratio（matched-100） | 2.89 |
| Label-shift break-even retention | ~0.5 |

## 五、请导师关注的关键问题

1. **三项 credibility checks 的定位是否合适？** 当前定位为"非 gold 鲁棒性分析，加强 silver-stage 相对模式，不替代 gold adjudication"。是否需要进一步弱化或加强？
2. **50% retention caveat 措辞是否到位？** 当前明确写 "positive but statistically weaker / CI crosses zero" 和 "must *not* be reported as a robust pass"。是否需要更醒目的提示？
3. **"consistently under-detect" 措辞是否合适？** 从 "systematically" 改为 "consistently"，保留 "under the tested prompts" 限定。主结论不变。
4. **gold pilot 优先级：** label-shift break-even (~50%) 为 gold pilot 设置了量化门槛。是否建议先做 50-sample gold pilot（聚焦 high_risk_sample_bank）？
5. **R4 macro-F1 < LLM 事实：** 论文保留 0.3280 vs 0.5523 的差距，R4 定位为 screening-oriented complement 而非 replacement。这个定位是否需要调整？

## 六、最大剩余风险

§VIII.D 是非 gold 鲁棒性分析，不替代独立 gold adjudication。绝对数字、mild/strong κ、strong_action retention rate 仍需 §VII gold adjudication 确认。50% retention 的 Δ 95% CI 跨越 0（[−0.026, +0.255]），是 directional signal 不是 robust pass。Evidence Necessity 使用同一 SimClaim backbone 但更早数据集版本的预存 NLI audit。在 gold 完成前，所有 §VIII.D 结论均为 directional silver-stage support，不是 validation。

## 七、建议下一步

1. 发导师审阅 V3.12.1（当前最佳 silver-stage 草稿）。
2. 同步启动 50-sample gold pilot（§VII protocol），优先 high_risk_sample_bank 案例。
3. gold pilot 完成后，根据 retention rate 判断：≥70% robust / 60% marginal-positive / 50% CI-crosses-zero / <50% downgrade。
4. 不要在外部沟通中声称 gold validation。
