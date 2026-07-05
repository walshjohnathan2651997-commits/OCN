# V3.13 导师审稿封面说明（中文）

**版本：** V3.13 Differentiated Against RIGOURATE / ForceBench / CLAIM-BENCH
**日期：** 2026-07-05
**源版本：** V3.12.1（已清理版）
**输出目录：** `D:\ocn\paper_versions_ordered\V3_13_differentiated_against_rigourate_forcebench\`

---

## 一、本次提交版本的核心变化

V3.13 是一次"同质化风险规避 + 高标准差异化重写"。基于 V3.12.1，**不跑实验、不调 API、不做 gold、不改任何数字**，只做定位和叙事层面的差异化重写。

主要变化：

1. **定位从"开创新大方向"改为"在已有赛道做细粒度关系拆解"。** 不再声称本文首次提出 scientific overstatement detection 或 evidence sufficiency calibration；而是明确建立在 RIGOURATE、evidence-licensed claims、ForceBench、CLAIM-BENCH 之上，做关系类型拆解和高风险 action-overclaim 筛查。
2. **§II 新增 §II.A "Relation to Scientific Overstatement and Evidence-Force Calibration"**：三段分别对照 RIGOURATE（连续分数 vs 关系类型）、ForceBench（配对比对 vs 单样本分类）、CLAIM-BENCH（抽取验证 vs 强度校准），并新增 Table X 定位对照表。
3. **贡献列表从 5 项压缩到 3 项**：taxonomy contribution / diagnostic contribution / screening-method contribution，每项都明确标注与已有工作的互补关系，删除 "novel task / first work / new field / SOTA" 等表述。
4. **Abstract 和 §I Introduction 调整**：开头先承认 recent work 已开始量化 scientific overstatement 和 evidence-force mismatch；不再写"该问题空白"。
5. **§V.A 增加 synthetic/counterfactual 透明度声明**：明确 SimClaim 不是 natural-prevalence corpus，而是 controlled counterfactual diagnostic set；四类均衡是设计目的，不是自然比例；本数据用于 pressure-test boundary recognition，不用于估计真实比例。
6. **§VIII 新增 §VIII.F "Why Fine-Grained Relation Typing Is Valuable"**：论证不同 overclaim 关系有不同风险语义和筛查需求，strong_action_overclaim 不只是"分数更高的 mild"。
7. **§VII 新增 §VII.I "Proposed Gold-Realism Audit Extension"**：在 gold pilot 中并行评估 claim_realism_score_1_to_5 和 claim_realism_issue，预注册 25% 类级和 25% 论文级 realism 阈值。
8. **§IX Limitations 新增第 9 项和第 10 项**：第 9 项明确与 RIGOURATE/ForceBench/CLAIM-BENCH 的差异化是 positioning-level，不是 empirical head-to-head；第 10 项明确 SimClaim 是 controlled counterfactual diagnostic set，realism audit 尚未运行。
9. **附录 B Language Guardrails 新增 5 条 forbidden claims**：包括"我们首次提出 scientific overstatement detection 作为新领域"、"SimClaim 是 natural-prevalence corpus"、"CESE-OCN 在实证 head-to-head 中超越 RIGOURATE/ForceBench/CLAIM-BENCH"等。

## 二、主论点

**本文不声称首次提出 scientific overstatement detection 或 evidence sufficiency calibration 作为新领域。** 本文建立在 RIGOURATE [30]、evidence-licensed claims [31]、ForceBench [35]、CLAIM-BENCH [28] 之上，做的是**细粒度关系类型拆解和高风险 action-overclaim 筛查**。

具体而言：

- RIGOURATE 输出**连续 overstatement 分数**；CESE-OCN 输出**四类关系标签**。RIGOURATE 不区分 mild scope expansion 和 high-risk action/deployment overclaim；CESE-OCN 通过 strong_action_overclaim 类做这种区分。
- ForceBench 做**配对 claim 的单调偏好测试**（calibrated vs. force-raised）；CESE-OCN 做**单样本关系类型分类和筛查**。ForceBench 不直接输出四类关系标签，也不以 action-overclaim 为筛查目标。
- CLAIM-BENCH 做**全文 claim-evidence 抽取和验证**（支持/反驳/NEI 风格）；CESE-OCN 做**claim 强度与证据充分性的校准**。CLAIM-BENCH 不引入强度不匹配的分类法。
- 三者与 CESE-OCN 是**互补关系**，不是竞争关系。

## 三、与 V3.12.1 的对照

| 项目 | V3.12.1 | V3.13 |
| --- | --- | --- |
| 定位 | "evidence sufficiency calibration framework" | "fine-grained relation-type decomposition on the existing track" |
| Related Work | RIGOURATE 一段简述 | §II.A 新增三段（RIGOURATE / ForceBench / CLAIM-BENCH）+ Table X |
| 贡献数 | 5 项 | 3 项（taxonomy / diagnostic / screening-method） |
| Abstract 开头 | 不提 recent work | "Building on recent work on scientific overstatement scoring and evidence-force calibration..." |
| §I Introduction 开头 | "Scientific claim verification is typically framed as a three-class task..." | 先承认 recent work，再写"However, less attention has been paid to whether different overclaim relations require different diagnostic treatment..." |
| §V.A SimClaim | 仅描述数据规模 | 新增 synthetic/counterfactual 透明度声明 |
| §VIII | A-E（含 §VIII.D 三项非 gold 可信度检查） | A-F（新增 §VIII.F "Why Fine-Grained Relation Typing Is Valuable"） |
| §VII | A-H | A-I（新增 §VII.I "Proposed Gold-Realism Audit Extension"） |
| §IX Limitations | 1-8 项 | 1-10 项（新增第 9 项差异化定位、第 10 项 SimClaim 反事实声明） |
| 所有实验数字 | — | **字节级不变**（R4 strong-F1 0.3967、LLM strong-F1 0.0769、macro-F1 0.3280/0.5523、bootstrap CI [0.1058, 0.1988]、FP/TP 2.89、retention break-even ~0.5、50% CI [-0.026, +0.255] 全部保留） |

## 四、关键数字（与 V3.12.1 完全一致）

- R4 strong-F1 = **0.3967**（silver 444）；LLM strong-F1 = **0.0769**（matched 100/200）
- R4 macro-F1 = **0.3280**（matched 100）；GPT-5.5 macro-F1 = **0.5523**（matched 100）；DeepSeek-V3 macro-F1 = **0.5270**（matched 200）
- R4 在 matched 100 上 strong-F1 = **0.3000**（绝对差距 +0.2231）
- Bootstrap CI for strong-positive delta = **[0.1058, 0.1988]**，10/10 seeds positive
- §VIII.D.B Screening Utility：FP/TP = **2.89**，recall = **0.360**，R4 captures **8** LLM-missed cases
- §VIII.D.C Label-Shift：50% retention Δ 95% CI = **[-0.026, +0.255]**（CI crosses zero，positive but statistically weaker）；60% retention = **+0.1408 [+0.035, +0.280]**（marginal-positive）；70% retention = **+0.1692 [+0.083, +0.264]**（robust）
- §V.A SimClaim：**444** claim-evidence pairs，**111** evidence groups，**6** domains，**111 per class**
- §V.D Author Sanity Audit：**25/40 (62.5%)** questionable/unclear；strong_action confusion rate **75%**

## 五、请导师重点审阅的几个问题

1. **差异化定位是否到位**：§II.A + Table X 是否足以说明 CESE-OCN 与 RIGOURATE / ForceBench / CLAIM-BENCH 的关系？是否有需要进一步强调或弱化的地方？
2. **3 项贡献列表是否准确**：taxonomy / diagnostic / screening-method 三项贡献的边界是否清晰？是否还有遗漏或重叠？
3. **§V.A synthetic/counterfactual 透明度声明是否足够**：是否需要进一步明确 SimClaim 不能做什么？是否需要在 Abstract 中也加一句 realism caveat？
4. **§VII.I gold-realism audit 提案**：`claim_realism_score_1_to_5` 和 `claim_realism_issue` 字段设计是否合理？25% 类级和 25% 论文级 realism 阈值是否合适？是否需要在 gold pilot 之前调整？
5. **§VIII.F "Why Fine-Grained Relation Typing Is Valuable"**：论证是否说服力足够？是否需要补充更多例子？
6. **RIGOURATE / ForceBench / CLAIM-BENCH 的引用**：目前 [30] [35] [28] 的引用是 informal 的，是否需要补充完整的 bibliography 条目？（V3.13 strengthening plan P0.1–P0.3 已记录此问题）

## 六、剩余风险

1. **差异化是 positioning-level，不是 empirical head-to-head**（§IX 第 9 项已明确声明）。如果导师要求 empirical head-to-head，需要在 V3.14+ 增加 RIGOURATE / ForceBench / CLAIM-BENCH 在 SimClaim 上的实际比对实验。
2. **SimClaim 的 natural-claim transferability 尚未验证**（§IX 第 10 项已明确声明）。realism audit 是 proxy，但尚未运行；如果 realism audit 显示 >25% 的 strong_action_overclaim 案例为 low-realism，screening 主张需要降级。
3. **所有 silver-stage 数字仍然 pending gold adjudication**（§VII 已明确）。gold pilot 尚未运行；所有 §VI 数字可能在 gold 后变动。
4. **ForceBench [35] 引用**：如果 ForceBench 实际上是 concurrent work 或不能确认具体引用，需要将 §II.A 中 ForceBench 段降级为 "concurrent work in progress" 并移除 [35] 引用。

## 七、下一步（按优先级）

- **P0（导师发送前）**：补全 RIGOURATE / ForceBench / CLAIM-BENCH 的具体引用条目（strengthening plan P0.1–P0.3）；重读 Abstract 和 §I 确认无残留 "first to propose" 措辞（P0.5）。
- **P1（gold pilot 前）**：更新 annotator training packet 加入 realism scoring guidance（P1.1）；生成 realism template CSV（P1.2）；导师对 realism 阈值签字确认（P1.4）。
- **P2（confirmatory submission 前）**：运行 gold pilot + realism audit（P2.1）；扩展到 300–500 gold cases（P2.2）；prompt robustness sweep（P2.3）；open-source LLM replication（P2.4）；RIGOURATE/ForceBench/CLAIM-BENCH head-to-head（P2.5）；natural-claim transferability probe（P2.6）。

详细计划见 `V3_13_strengthening_plan_after_related_work_shift.md`。

## 八、文件清单

V3.13 输出目录共 7 个文件：

1. `CESE_OCN_V3_13_differentiated_against_rigourate_forcebench.md` — 主论文（V3.13）
2. `CESE_OCN_V3_13_differentiated_against_rigourate_forcebench.docx` — 主论文 docx
3. `proposed_gold_realism_extension.md` — gold-realism audit 字段和协议规范（独立文件，§VII.I 引用）
4. `V3_13_strengthening_plan_after_related_work_shift.md` — P0/P1/P2/P3 优先级路线图
5. `V3_13_revision_log.md` — 修订日志（11 项变更 + 10 项质量验证 + 11 项禁止动作检查）
6. `V3_13_readiness_gate.json` — 机器可读 readiness gate
7. `advisor_cover_note_cn_v3_13.md` — 本文件（中文导师封面说明）

---

**本版本可发导师审阅。** 所有实验数字与 V3.12.1 字节级一致；所有 non-gold caveat 保留；gold pilot 尚未运行；与 RIGOURATE / ForceBench / CLAIM-BENCH 的差异化是 positioning-level，不是 empirical head-to-head（已在 §IX 第 9 项明确声明）。
