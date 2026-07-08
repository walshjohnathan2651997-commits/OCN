# 语料关联性 Pilot 标注指南 v1

适用于 `audit_packet_alignment_pilot_zh_bilingual.xlsx`（30 条 pilot 样本）。

## 标注者要做的事

**先判断 claim 和 evidence 是否真的有关，再决定要不要做标签判断。**

本轮 pilot 不要求填 `人工标签`。本轮重点是判断 `claim-evidence` 是否可判。

## 标注顺序

1. 先看 `claim_text_原文`（必要时参考 `claim_text_中文对照`）。
2. 再看 `evidence_text_原文`（必要时参考 `evidence_text_中文对照`）。
3. 判断 `claim` 和 `evidence_text` 是否有关 → 填 `语料关联性`。
4. 再看 `selected_evidence_原文`（必要时参考 `selected_evidence_中文对照`）。
5. 判断 `selected_evidence` 是否和 `claim` 有关 → 填 `selected_evidence关联性`。
6. 只有 `claim-evidence` 至少 `明确相关` 或 `弱相关`，才允许把 `是否可进入标签判断` 填 `是`；否则填 `否`，并在 `不可判原因` 里给出原因。

## 字段解释

### 语料关联性

判断 `claim_text` 和 `evidence_text` 的关系。

| 选项 | 含义 |
|---|---|
| 明确相关 | `evidence_text` 直接提供判断 `claim` 所需信息。 |
| 弱相关 | `evidence_text` 有部分信息，但上下文不完整。 |
| 只是同主题 | 主题相似，但无法判断 `claim`。 |
| 基本无关 | `claim` 和 `evidence_text` 看不出实质关系。 |
| 证据不足无法判断 | 文本太短、缺上下文或不可理解。 |

### selected_evidence 关联性

判断 `selected_evidence` 和 `claim` 的关系。

| 选项 | 含义 |
|---|---|
| 和claim明确相关 | `selected_evidence` 直接提供判断 `claim` 所需信息。 |
| 和claim弱相关 | `selected_evidence` 有部分信息，但不够。 |
| 只是同主题 | `selected_evidence` 主题相似，但无法判断 `claim`。 |
| 基本无关 | `selected_evidence` 和 `claim` 看不出实质关系。 |
| 为空或太短 | `selected_evidence` 缺失或信息太少。 |

### 是否可进入标签判断

| 选项 | 含义 |
|---|---|
| 是 | `语料关联性` 为 `明确相关` 或 `弱相关`，且证据足以做初步判断。 |
| 否 | `只是同主题`、`基本无关`、`证据不足`，或 `selected_evidence` 完全不可用。 |

### 不可判原因

当 `是否可进入标签判断 = 否` 时必须填。

| 选项 | 含义 |
|---|---|
| 无 | 可进入标签判断（`是否可进入标签判断 = 是` 时填此项）。 |
| claim-evidence无关 | `claim` 和 `evidence_text` 无实质关系。 |
| selected_evidence无关 | `selected_evidence` 和 `claim` 无实质关系。 |
| 证据太短 | 证据文本太短，信息不足。 |
| 上下文缺失 | 缺少上下文，无法判断。 |
| 术语或对象不一致 | `claim` 和 `evidence` 讨论的对象或术语不匹配。 |
| 其他 | 其他无法判断的原因，在 `备注` 里说明。 |

## 重要规则

### 规则 1：无关 ≠ contradiction

`claim` 和 `evidence` 无关，**不等于** `contradiction`。

- `contradiction` 只能用于 `evidence` 明确反向支持的情况。
- 如果只是看不出关系，应填 `基本无关` 或 `证据不足无法判断`，**不要** 填 `contradiction`。

### 规则 2：本轮不填人工标签

本轮 pilot 重点判断 `语料关联性`。`人工标签`、`证据是否一致`、`系统证据是否足够`、`信心1到5`、`是否二审` 可以留空，留到正式 111 条人审时再填。

### 规则 3：判断必须基于原文

`claim_text_中文对照` / `evidence_text_中文对照` / `selected_evidence_中文对照` 初始为 `待人工确认`。如果你在阅读时写了中文理解，可以替换进去，但这不是必须的。

**判断必须基于 `*_原文`，不要只看中文对照。**

### 规则 4：中文对照不要脚本伪译

不要用脚本或外部 API 翻译原文。中文对照字段保持 `待人工确认` 或由真人手动填写理解。

## 数量要求

- 共 30 条 pilot 样本。
- **全部 30 条都要填** `语料关联性`、`selected_evidence关联性`、`是否可进入标签判断`。
- `不可判原因` 在 `是否可进入标签判断 = 否` 时必填。
- `备注` 可选。

## 判定规则（汇总脚本使用）

pilot 完成后，`scripts/summarize_corpus_alignment_pilot_v1.py` 会计算 **两个独立的 eligibility rate**。不要把它们混成一个指标——claim-evidence 可判性和系统 selected_evidence 可用性是两件事。

### Part 1 — claim-evidence 标签审计（claim_evidence_label_eligible_rate）

定义：`语料关联性 in [明确相关, 弱相关]` 且 `是否可进入标签判断 == 是`。

| claim_evidence_label_eligible_rate | 建议 |
|---|---|
| >= 0.85 | 可以继续正式 111 条 human label audit。 |
| 0.70 ~ 0.85 | 只对 eligible subset 做标签审计；其余作为语料噪声分析。 |
| < 0.70 | 停止正式标签审计；项目改为 corpus alignment / silver diagnostic failure analysis。 |

### Part 2 — selected_evidence 系统评价（selected_evidence_system_eval_eligible_rate）

定义：`selected_evidence关联性 in [和claim明确相关, 和claim弱相关]`（即 selected_evidence 非空且可用）。

| selected_evidence_system_eval_eligible_rate | 建议 |
|---|---|
| >= 0.50 | 系统选证据可用于评价 review queue / screening pipeline。 |
| < 0.50 | **不要**说模型标签评价失败；应写 `selected_evidence coverage/alignment insufficient`，作为 evidence-selection failure 单独分析。 |

另外报告 `selected_evidence_missing_or_short_rate`（`selected_evidence关联性 == 为空或太短` 的比例），单独量化系统选证据的覆盖问题。

### Legacy 指标

`label_eligible_rate`（`是否可进入标签判断 == 是` 的比例）保留用于向后兼容，但**不再作为唯一决策指标**。

## 严禁事项

- **严禁**自动填写或让模型代替填写任何标注字段。必须由真人判断。
- **严禁**修改 `*_原文` 列。
- **严禁**把填好的 xlsx/csv 提交到 git（该目录已 gitignore）。
- **严禁**在公开报告里输出 claim/evidence 原文。
- **严禁**把 silver 当 gold。

## 这份 pilot 不是什么

- 不是 gold benchmark。
- 不是 human-validated dataset。
- 不会用来修改原 CSV 的 silver 标签。
- 不会用来填充 gold_label。
- 不覆盖全部 444 条候选。
- 不是正式人审标签审计（只是前置语料关联性检查）。

## 公开报告里允许/禁止的措辞

**Safe wording (允许)**:

- 「corpus alignment pilot, N=30」
- 「claim_evidence_label_eligible_rate = X on the pilot subset」
- 「selected_evidence_system_eval_eligible_rate = X (evidence-selection coverage)」
- 「selected_evidence coverage/alignment insufficient — evidence-selection failure to analyze separately」
- 「pilot suggests the audit packet is / is not ready for formal human label audit」
- 「small targeted alignment check, not a gold benchmark」

### Forbidden wording (禁止的措辞)

| Unsafe wording (forbidden) | Why forbidden |
|---|---|
| 「human-validated dataset」 | audit not executed |
| 「gold benchmark」 | silver diagnostic; not gold |
| 「the silver labels are correct」 | no audit has verified them |
| 「SOTA」 | no gold comparison; silver diagnostic only |
| 「automatic peer reviewer」 | not an automatic peer reviewer |
| 「general detector」 | not a validated general detector |
| 「human-audited validation」 | only alignment pilot, not label audit |
