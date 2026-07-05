# Next Actions Only — 下一步清单（严格 3-5 个，不扩散）

**Date:** 2026-07-05
**Rule:** 只允许以下 3-5 个下一步。不允许新增。每完成一个，划掉一个，不补充。

---

## 1. 按 V3.17 主线改论文（首要）

**目标：** 将论文正文（Abstract / §I / §IV / §V / §VII / §IX）从 V3.7/V3.15 hierarchical-taxonomy 主线改写为 V3.17 baseline offline PDF-corpus screening 主线。

**输入：**
- `D:\ocn\_MAINLINE_CURRENT\_FINAL_PAPER_OUTLINE_CURRENT.md`（论文骨架）
- `D:\ocn\_MAINLINE_CURRENT\_FINAL_NUMBERS_FOR_PAPER.csv`（最终数字）
- `D:\ocn\_MAINLINE_CURRENT\_DO_NOT_USE_OLD_CLAIMS.md`（禁用旧表述）

**输出：** 更新后的论文 .md（保留版本历史，新增 V3.19 mainline_rewrite 或类似版本）

**验收：**
- Abstract 重写为 offline PDF-corpus screening 框架
- §IV method 描述 V3.17 baseline pipeline
- §V experiments 使用 V3.17 baseline 数字
- §VII limitations 包含 V3.18 negative ablation
- 所有数字可在 `_FINAL_NUMBERS_FOR_PAPER.csv` 找到 source
- 通过 `_DO_NOT_USE_OLD_CLAIMS.md` 检查

---

## 2. 清理论文乱码和引用（与 1 并行）

**目标：** 统一论文中的 stale 表述、修复引用、清理乱码。

**输入：**
- `D:\ocn\_MAINLINE_CURRENT\_DO_NOT_USE_OLD_CLAIMS.md`
- `D:\ocn\project_synthesis\mainline_realignment_v1\stale_claims_audit.csv`

**输出：** 论文 .md 中的 stale 表述全部更正

**验收：**
- grep 论文 .md，无 "R4 beats LLM overall" / "gold validated" / "natural distribution" / "standalone detector" / "full automatic review" / "raw BM25 chunks directly work" / "V3.18 as main method" / "local LLM baseline completed"
- 所有引用可解析

---

## 3.（可选）Local LLM feasibility note

**目标：** 作为 §VIII future work 的预注册 pilot，写一份 local LLM baseline feasibility note（不调 API，不训练模型）。

**输入：**
- `D:\ocn\project_synthesis\local_llm_baseline_feasibility_note_v1\local_llm_feasibility_note.md`（已存在，已对齐）
- `D:\ocn\project_synthesis\local_llm_baseline_feasibility_note_v1\local_llm_future_work_protocol.md`

**输出：** 在论文 §VIII future work 中引用该 note，明确标注 "future work, NOT completed"

**验收：**
- 论文 §VIII 包含 local LLM pilot 预注册
- 明确标注 "future work, NOT completed"
- 不调 API，不训练模型

---

## 4.（可选）Gold / claim extraction demo 后置

**目标：** 将 gold adjudication 与 claim extraction demo 明确后置到论文 revision 之后，不阻塞当前改写。

**输入：**
- `D:\ocn\paper_versions_ordered\V3_4_taxonomy_hardened\high_risk_sample_bank.csv`（参考数据）
- `D:\ocn\paper_versions_ordered\V3_4_taxonomy_hardened\trusted_case_bank.csv`（参考数据）

**输出：** 论文 §VIII future work 明确标注 gold adjudication 为后续步骤

**验收：**
- 论文 §VIII 包含 gold adjudication 未来计划
- 明确标注 "pending, NOT begun"
- 不执行 gold adjudication（当前只规划）

---

## 不允许的下一步（明确禁止扩散）

- ❌ 不允许新增实验
- ❌ 不允许调 API
- ❌ 不允许训练模型
- ❌ 不允许重跑 R4
- ❌ 不允许改 R4 thresholds
- ❌ 不允许改实验原始数据
- ❌ 不允许删除文件
- ❌ 不允许移动文件
- ❌ 不允许新增第 6 个下一步

---

## 完成判定

当 1、2 完成（3、4 可选）时，项目进入 "ready_for_paper_submission" 状态，需要新一轮 gate 检查。
