# 人工审计标注指南 v2（双语下拉版）

适用于 `audit_packet_simple_zh_bilingual.xlsx`。

## 标注者要做的事

**读证据 → 读 claim → 从下拉列表选标签。**

## 标注顺序

1. 先看 `selected_evidence_原文` / `selected_evidence_中文对照`。
2. 再看 `evidence_text_原文` / `evidence_text_中文对照`。
3. 判断 `selected_evidence` 和 `evidence_text` 是否一致 → 填 `证据是否一致`。
4. 判断 `selected_evidence` 是否足够支持你做标签判断 → 填 `系统证据是否足够`。
5. 最后给 `claim_text` 选 `人工标签`。

## 字段解释

### 证据是否一致

| 选项 | 含义 |
|---|---|
| 一致 | selected_evidence 和 evidence_text 表达基本相同。 |
| 部分一致 | selected_evidence 只覆盖 evidence_text 的一部分。 |
| 不一致 | selected_evidence 选偏，和 evidence_text 重点不同。 |
| selected为空或太短 | selected_evidence 缺失或信息太少。 |

### 系统证据是否足够

| 选项 | 含义 |
|---|---|
| 足够 | 只看 selected_evidence 就能判断 claim。 |
| 部分足够 | selected_evidence 有帮助，但还要看 evidence_text。 |
| 不足 | selected_evidence 不够，主要靠 evidence_text 判断。 |
| 无法判断 | 两个证据都不够或看不懂。 |

### 人工标签

| 选项 | 含义 |
|---|---|
| 支持 | 证据基本支持 claim。 |
| 轻微过度 | claim 比证据说得更宽、更确定。 |
| 强行动过度 | claim 加入部署、真实应用、自动决策、安全保证、政策行动、工程落地等证据未支持的含义。 |
| 矛盾 | claim 和证据方向相反。 |
| 不确定 | 证据不足或难判断。 |

### 信心1到5

- 1 = 非常不确定
- 5 = 非常确定

### 是否二审

- `是` / `否`（从下拉选）

## 重要规则

### 规则 1：selected 不足但 evidence 可判

如果 `selected_evidence` 不足，但 `evidence_text` 能判断：
- `人工标签` 可以根据 `evidence_text` 填；
- `系统证据是否足够` 填 `不足`；
- `备注` 写「原始证据可判，系统选证据不足」。

### 规则 2：selected 和 evidence 差距大

如果 `selected_evidence` 和 `evidence_text` 差距很大：
- `证据是否一致` 填 `不一致`；
- `是否二审` 填 `是`。

### 规则 3：信心低必须二审

当 `信心1到5` ≤ 2，`是否二审` **必须**填 `是`。

### 规则 4：支持 vs 强行动过度不一致必须二审

当你的 `人工标签` 和 `silver标签` 在「支持 vs 强行动过度」轴上不一致，`是否二审` **必须**填 `是`。

## 关于中文对照字段

`claim_text_中文对照` / `evidence_text_中文对照` / `selected_evidence_中文对照` 初始为 `待人工确认`。
如果你在阅读时写了中文理解，可以替换进去，但这不是必须的——这些字段只是辅助。
**判断必须基于原文，不要只看中文对照。**

## 数量要求

- 最少 **80 条**。
- 最好 **100–120 条**（共 111 条，尽量全做）。

## 严禁事项

- **严禁**自动填写或让模型代替填写 `人工标签`。必须由真人判断。
- **严禁**修改原文列（`*_原文`）。
- **严禁**把填好的 xlsx/csv 提交到 git（该目录已 gitignore）。
- **严禁**在公开报告里输出 claim/evidence 原文。
- **严禁**把 silver 当 gold。

## 这份审计不是什么

- 不是 gold benchmark。
- 不是 human-validated dataset。
- 不会用来修改原 CSV 的 silver 标签。
- 不会用来填充 gold_label。
- 不覆盖全部 444 条候选。

## 公开报告里允许/禁止的措辞

**Safe wording (允许)**:
- 「small targeted audit, not a gold benchmark」
- 「directional reliability check on the top of the review queue」
- 「auditor agreement with silver on the audited subset was X%」

### Forbidden wording (禁止的措辞)

| Unsafe wording (forbidden) | Why forbidden |
|---|---|
| 「human-validated dataset」 | audit not executed |
| 「gold benchmark」 | silver diagnostic; not gold |
| 「the silver labels are correct」 | no audit has verified them |
| 「SOTA」 | no gold comparison; silver diagnostic only |
| 「automatic peer reviewer」 | not an automatic peer reviewer |
| 「general detector」 | not a validated general detector |
