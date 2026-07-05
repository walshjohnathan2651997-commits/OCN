# V3.13 RIGOURATE-Differentiated + Realism-Aware — 导师 cover note（中文）

**日期：** 2026-07-05
**版本：** V3.13 RIGOURATE-Differentiated + Realism-Aware
**输出目录：** `D:\ocn\paper_versions_ordered\V3_13_rigourate_differentiated_realism_aware\`
**前置工作：** RIGOURATE Reproduction + SimClaim Differentiation v1（`D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1\`）

---

尊敬的导师：

附件是 V3.13 RIGOURATE-Differentiated + Realism-Aware 版本，基于 V3.12 + V3.13 (prior) 进一步整合 RIGOURATE 复现 / proxy baseline / realism audit 的结果。这一版没有跑新实验、没有调付费 API、没有做 gold、没有改原始数据、没有改 V3.12 原文件。所有禁令均已遵守。

## 1. 这一版做了什么

V3.13 RIGOURATE-Differentiated + Realism-Aware 在 V3.13 (prior) 的 positioning 基础上做了两件事：

1. **新增 §VI.E：RIGOURATE-style scalar proxy baseline 结果**。基于 RIGOURATE Reproduction + SimClaim Differentiation v1 任务，构建三个 RIGOURATE-style scalar overstatement proxy baseline（A=rule_scalar_score 完成 444 对；B=nli_scalar_score BLOCKED 因为 HCM/NLI features 不在 repo 中，已记录 blocked_reason；C=llm_scalar_proxy 完成 200/444 匹配对），在 SimClaim silver 444 上评估 4 个 binary task，并与 R4 frozen、GPT standard、GPT structured、DeepSeek-V3 在 100 matched samples 上做 head-to-head 比较。proxy baseline 明确标注为 proxy，**不是**官方 RIGOURATE 系统。

2. **新增 §VII.J：两层 gold protocol（relation + realism）**。把 V3.13 (prior) 的 §VII.I gold-realism audit 提议升级为完整的两层协议：Layer 1 relation label（沿用 §VII），Layer 2 claim realism（`claim_realism_score_1_to_5` + `claim_realism_issue` + `claim_realism_usable_for_paper`），并预注册 25% class-level 和 25% paper-level realism thresholds。这是 protocol-level 升级，**没有**做 gold，**没有**改 silver CSV，**没有**改 §VII.G 的 downgrade criteria。

此外，标题改为 **"Fine-Grained Evidence-Sufficiency Relation Diagnosis for Rare High-Risk Scientific Action Overclaims"**，副标题 "A Controlled Counterfactual Diagnostic Study of LLM Under-Detection and Screening-Oriented Routing"。Abstract、§X Conclusion 同步更新引用 §VI.E 和 §VII.J。§IX Limitations 新增第 11 条（RIGOURATE-style proxy baseline caveat）。

## 2. 关键结论（controlled silver-stage，validation-pending）

### 2.1 RIGOURATE 官方复现状态：BLOCKED

截至 2026-07-05，RIGOURATE 官方代码 / 数据 / 模型权重均未公开发布。arXiv v2 (12 Jan 2026) 中的 `[Github/HF Link]` 仍是占位符；web search 未找到任何 GitHub repo、HuggingFace model、dataset release 或 supplementary material。**官方复现目前不可行**。所有 blocked 项均已记录 `blocked_reason`。

### 2.2 RIGOURATE-style proxy baseline 主要发现

- **scalar score 能识别 overclaim 吗？** 仅当 scalar 来自强 LLM 时可以（llm_scalar_proxy ROC-AUC=0.85）；纯 cue-based scalar 不行（rule_scalar_score ROC-AUC=0.51，chance-level）。
- **scalar score 能区分 mild vs. strong_action 吗？** **不能**。rule_scalar ROC-AUC=0.51（chance），llm_scalar ROC-AUC=0.59（弱，低于 0.70 阈值）。这是四类 taxonomy 的关键动机——scalar 压缩了 action-vs-scope 区分。
- **scalar score 能替代 R4 strong_action route 吗？** **不能**。silver 444 上 R4 strong_F1=0.3967 > rule_scalar best-F1=0.3844；matched 100 上 R4 strong_F1=0.3000 >> rule_scalar=0.1364。llm_scalar 看似与 R4 持平（0.3974 vs. 0.3967），但其 ROC-AUC=0.52（chance-level），apparent F1 是 threshold artefact。
- **R4 在 strong_action 筛查上仍有独立价值吗？** **是**。R4 在 matched 100 上抓回 8/24 LLM 全部漏报的 strong_action 案例；R4 strong_F1 是 LLM judges 的 3-5 倍。代价是 macro-F1 更低（0.3280 vs. 0.5523）和 review burden 更高（35% vs. 1%），但这是 screening-oriented complement 的设计权衡。
- **scalar 与 relation-specific screening 互补吗？** **是**。scalar 擅长 broad supported-vs-overclaim 区分（ROC-AUC=0.85）；R4 擅长 high-risk action-overclaim 识别。两者覆盖不同 sub-problem，互补性是 CESE-OCN 四类分解的经验依据。

### 2.3 Case-level 分析（100 matched cases）

- both_wrong: 49/100（dominant — 两种方法都 struggle）
- r4_right_scalar_wrong: 24/100
- scalar_right_r4_wrong: 17/100
- both_right: 10/100
- mild/strong confusion: 35/100（确认 mild-vs-strong 边界是 taxonomy 最不稳定的点）

### 2.4 Claim realism audit（heuristic pre-screen，NOT gold）

- 21/444 (4.7%) 总体 realism risk flag；strong_action_overclaim 类 10/111 (9.0%)。
- 均低于 25% 预注册阈值，但 strong_action 类的 9.0% 不算小，需在 gold sampling 中优先处理。
- 这是 heuristic pattern-based pre-screen，**不是** gold，**不**预判 gold 结果，只决定 sampling 顺序。

## 3. 这一版没有做什么（禁令遵守）

| 禁令 | 状态 |
| --- | --- |
| 不要跑新实验 | PASS（proxy baseline 仅基于已有 silver data + 已有 LLM parsed outputs） |
| 不要调 API | PASS（无付费 API 调用） |
| 不要做 gold | PASS（无 gold annotation） |
| 不要改原始数据 | PASS（strict_silver_max_v1 CSV 只读） |
| 不要修改 V3.12 原文件 | PASS（V3.12 文件未触碰） |
| 不要把 proxy baseline 写成官方 RIGOURATE | PASS（所有 proxy 输出明确标注为 proxy） |
| 不要把 blocked plan 写成 completed result | PASS（nli_scalar_score BLOCKED with blocked_reason；无伪造结果） |
| 不要把 silver 写成 gold | PASS（所有输出标注 silver） |
| 不要声称本文首次提出 scientific overstatement / evidence-force calibration | PASS（明确写"builds on RIGOURATE / ForceBench / CLAIM-BENCH"） |
| 不要删除 R4 macro-F1 低于 LLM 的事实 | PASS（§VI.B、§VIII.A、§IX item 4 均保留 0.3280 vs 0.5523 事实） |
| 不要删除 gold 未完成的事实 | PASS（§VII 明确 "No gold annotation has been performed"；Tables G1-G3 全部 `TO_BE_FILLED_AFTER_GOLD`） |

## 4. 文件清单

- `CESE_OCN_V3_13_rigourate_differentiated_realism_aware.md` — 主稿（基于 V3.13 prior + §VI.E + §VII.J + §IX item 11 + 标题/Abstract/Conclusion 更新）
- `CESE_OCN_V3_13_rigourate_differentiated_realism_aware.docx` — docx 导出
- `V3_13_positioning_change_log.md` — 从 V3.12 到 V3.13 RIGOURATE-Aware 的 positioning 变化日志
- `V3_13_related_work_diff_table.md` — RIGOURATE / ForceBench / CLAIM-BENCH / CESE-OCN 对比表（standalone）
- `V3_13_claims_allowed_for_paper.md` — 允许和禁止的主张清单
- `V3_13_advisor_cover_note_cn.md` — 本文件

## 5. 主要 risk 与下一步

**主要 risk：**

1. **官方 RIGOURATE artifacts 不可用** — proxy baseline 不是官方 RIGOURATE，结论可能在官方系统发布后 shift。建议联系 RIGOURATE 通讯作者（jhfjames1@sheffield.ac.uk）询问 code/data release 状态。
2. **Silver-only evaluation** — 所有结论都是 pre-gold，gold adjudication 后可能 shift。
3. **SimClaim realism risk** — 4.7% 总体、9.0% strong_action 类，非平凡；需 gold realism annotation 确认 SimClaim claims 是否足够 naturalistic 支撑 paper tables。

**建议下一步（不在本任务范围内，待您指示）：**

1. 跑 §VII 的 50-sample gold pilot（两层 protocol），填 Tables G1-G3。
2. 联系 RIGOURATE 通讯作者询问 code/data release。
3. 若 gold pilot 通过，准备 confirmatory submission（300-500 pairs）。
4. 若 gold pilot 失败（mild_vs_strong κ < 0.40），按 §VII.G downgrade criteria 修订 taxonomy。

## 6. 一句话总结

V3.13 RIGOURATE-Differentiated + Realism-Aware 在 V3.13 prior 的 positioning 基础上，整合了 RIGOURATE-style proxy baseline 的 silver-stage 经验证据（scalar 不能区分 mild vs. strong，R4 保留 strong_action 筛查价值，两者互补）和两层 gold protocol（relation + realism），所有禁令遵守，所有 blocked 项有 `blocked_reason`，所有数字 validation-pending。这一版**没有**声称复现官方 RIGOURATE，**没有**声称 R4 整体优于 LLM，**没有**声称 gold 完成，**没有**声称 SimClaim 是 natural-prevalence corpus。

敬祝

教安

学生
2026-07-05
