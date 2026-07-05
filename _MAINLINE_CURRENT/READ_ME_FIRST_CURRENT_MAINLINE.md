# READ ME FIRST — 当前主线入口（Current Mainline）

**日期：** 2026-07-05
**版本：** V3.17 baseline selected；V3.18 negative ablation
**读者：** 任何打开 D:\ocn 项目的人（包括未来的你自己）

> 这是本项目的**唯一入口文档**。在阅读任何其他项目记录、实验报告、论文草稿之前，请先读完本文件。本文件 ≤ 2 页。

---

## 1. 当前主线是什么

本项目当前主线是 **离线 PDF 语料证据充分性筛查框架（offline PDF-corpus evidence-sufficiency screening framework）**：

```
PDF corpus
  → BM25 top-k 检索
  → evidence canonicalization (best_sentence_top5_overlap)
  → CESE-OCN / R4 relation-specific screening（restored R4，10 seeds，per-seed thresholds，多数投票）
  → risk ranking (G_conservative_precision)
  → second-stage human review queue
```

**本项目不是：** 通用 LLM 审稿器、自然分布 benchmark、"R4 overall beats LLM" 的主张、独立 standalone detector、全自动审稿系统。

**当前贡献定位：**
1. 发现 raw PDF chunks 会破坏 downstream strong_action screening（raw BM25 top1 strong_F1=0.1806）
2. 证明 evidence canonicalization 是 retrieval-to-screening 的关键桥梁（canonicalized strong_F1=0.4503，+0.2697）
3. 将 R4 定位为离线、可审计、second-stage strong_action screening router（standalone_viable=false，second_stage_viable=true）

---

## 2. 当前最佳方法是什么

**Selected: V3.17 baseline**

- BM25 top-k retrieval over SimClaim PDF corpus
- `best_sentence_top5_overlap` evidence canonicalization（简单 overlap-based selector，从 top-5 BM25 chunks 选最佳句子）
- Restored R4 screening router（10 seeds [11,22,33,44,55,66,77,88,99,111]，per-seed thresholds，majority-vote aggregation，prefer test split with dev fallback）
- `G_conservative_precision` risk ranking variant（8 个公式变体中最佳）
- Second-stage review queue（top-100 prioritized candidates）

---

## 3. 当前核心数字（436 eval candidates）

| 指标 | 值 | 说明 |
|---|---|---|
| strong_F1 | **0.4503** | V3.17 baseline 主指标 |
| strong_recall | 0.7064 | 高召回，二阶段筛查关键 |
| strong_precision | 0.3305 | 低精度，需 second-stage |
| macro_F1 | 0.3847 | 整体低于 LLM |
| precision@20 | **0.45** | review queue 顶部精度 |
| recall@100 | 0.3303 | review queue top-100 覆盖 |
| FP/TP @ 5% prevalence | 11.24 | 低患病率下可接受（second-stage） |
| standalone viable | false | 不能独立使用 |
| second-stage viable | **true** | 必须作为 second-stage |
| raw BM25 top1 strong_F1 | 0.1806 | 对照：raw chunks 严重破坏筛查 |
| oracle span strong_F1 | 0.4257 | 对照：oracle 上界 |
| canonicalization gain | **+0.2697** | canonicalization 的核心贡献 |

---

## 4. V3.18 为什么不作为主方法

V3.18 intelligent upgrade 尝试用 sklearn learned selector + learned ranker 替换 V3.17 的手工规则：

| 模块 | V3.17 baseline | V3.18 learned | 差距 | 通过？ |
|---|---|---|---|---|
| Evidence selector (strong_F1) | 0.4503 | 0.4444 | -0.006 | false |
| Risk ranker (P@20) | 0.45 | 0.35 | -0.10 | false |
| Risk ranker (FP/TP@5%) | 11.24 | 2.00 | -9.24（更好） | partial |

**结论：** `supports_v3_18_intelligent_upgrade=false`；`best_overall_method=V3.17_baseline`。V3.18 作为 **exploratory negative ablation** 保留，写入 §VIII limitations / §IX future work，**不替换 V3.17**。可能原因：特征空间饱和、silver 标签噪声、样本规模小、R4 hard threshold 限制。

---

## 5. 旧方向哪些不要再用

以下旧表述/旧方向**已废弃**，不要在论文或项目记录中继续使用：

- **V3.7 作为当前论文版本** → V3.7 是历史 advisor-handoff 草稿，不是当前 selected method
- **V3.15 hierarchical taxonomy 作为 empirical mainline** → 保留为 paper-level interpretation，不是 empirical mainline
- **"R4 beats LLM overall"** → R4 macro_F1=0.3280 < LLM=0.5523，禁止
- **"gold validated"** → gold adjudication 未开始，所有标签为 silver
- **"natural distribution / natural prevalence"** → SimClaim 是 controlled counterfactual diagnostic set
- **"standalone detector" / "full automatic review"** → R4 是 second-stage，standalone_viable=false
- **"raw BM25 chunks directly work"** → raw BM25 top1 strong_F1=0.1806，必须 canonicalization
- **"V3.18 as main method" / "learned upgrade improves"** → V3.18 negative，未超过 V3.17
- **"local LLM baseline completed"** → local LLM baseline 是 future work，未完成
- **gold pilot 作为"唯一决定性下一步"** → gold 仍是未来可信度步骤，但当前主线方向是 offline PDF-corpus screening

完整禁用清单见 `_DO_NOT_USE_OLD_CLAIMS.md`。

---

## 6. 下一步只做什么（3-5 个，不扩散）

1. **按 V3.17 主线改论文**：Abstract / §I / §IV / §V 重写为 offline PDF-corpus screening 框架，V3.18 写入 §VIII limitations
2. **清理乱码和引用**：统一论文中的 stale 表述（见 `_DO_NOT_USE_OLD_CLAIMS.md`）
3. **（可选）local LLM feasibility note**：作为 §IX future work 的预注册 pilot，不调 API
4. **（可选）gold/claim extraction demo 后置**：gold adjudication 仍是未来步骤，不阻塞当前论文改写

详见 `_NEXT_ACTIONS_ONLY.md`。

---

## 7. 关键文件导航

| 需要什么 | 看哪里 |
|---|---|
| 主线证据地图 | `_MAINLINE_EVIDENCE_MAP.md` |
| 论文最终数字 | `_FINAL_NUMBERS_FOR_PAPER.csv` |
| 版本决策记录 | `_PAPER_VERSION_DECISION_LOG.md` |
| 实验状态注册表 | `_EXPERIMENT_STATUS_REGISTRY.csv` |
| 禁用旧结论 | `_DO_NOT_USE_OLD_CLAIMS.md` |
| 论文最终骨架 | `_FINAL_PAPER_OUTLINE_CURRENT.md` |
| 下一步清单 | `_NEXT_ACTIONS_ONLY.md` |
| Realignment 详情 | `D:\ocn\project_synthesis\mainline_realignment_v1\` |
| V3.17 baseline 冻结指标 | `D:\ocn\experiments\v3_18_intelligent_upgrade_v1\v3_17_frozen_baseline_metrics.json` |
| V3.18 negative gate | `D:\ocn\experiments\v3_18_intelligent_upgrade_v1\v3_18_intelligent_upgrade_gate.json` |

**违反本文件的任何表述都应被视为 stale，按 `_DO_NOT_USE_OLD_CLAIMS.md` 处理。**
