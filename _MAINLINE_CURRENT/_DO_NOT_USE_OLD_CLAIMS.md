# Do NOT Use Old Claims — 禁用旧结论清单

**Date:** 2026-07-05
**Scope:** 以下旧结论/旧表述已废弃，禁止在论文正文、项目记录、报告、readme 中继续使用

> 任何违反本清单的表述都应被视为 stale，必须立即更正。允许的写法见 `D:\ocn\project_synthesis\mainline_realignment_v1\updated_allowed_forbidden_claims.md`。

---

## 禁用旧结论（共 9 类）

### 1. "R4 beats LLM overall"

**禁用理由：** R4 macro_F1=0.4238（silver 444，historical frozen R4 baseline）< LLM macro_F1=0.5270（DeepSeek-V3 200 samples）/ 0.5523（GPT-5.5 standard 100 samples）。R4 不是 overall beats LLM 的分类器。

**允许的替代写法：** "R4 provides targeted Level-2 strong_action screening signal (strong_recall=0.7064) where LLM judges under-detect (strong_recall=0.04 under tested prompts). This is a controlled silver-stage finding, not a fundamental limit of LLMs."

---

### 2. "Four-class benchmark as main contribution"

**禁用理由：** 当前贡献不是 four-class benchmark。当前贡献是发现 raw PDF chunks 破坏 downstream screening，证明 evidence canonicalization 是 retrieval-to-screening 的关键桥梁，并将 R4 定位为 second-stage screening router。

**允许的替代写法：** "This work contributes an offline PDF-corpus evidence-sufficiency screening framework, demonstrating that evidence canonicalization is the critical bridge between BM25 retrieval and R4 relation-specific screening."

---

### 3. "Standalone detector"

**禁用理由：** R4 standalone_viable=false（FP/TP @ 1% = 66.82）。R4 必须作为 second-stage，不能独立使用。

**允许的替代写法：** "R4 is a second-stage screening router. Standalone viability is false (FP/TP @ 1% = 66.82); second-stage viability is true (FP/TP @ 5% = 11.24, recall ≥ 0.6)."

---

### 4. "Natural distribution" / "Natural prevalence"

**禁用理由：** SimClaim 是 controlled counterfactual diagnostic set（444 pairs, 111 groups, 6 domains, balanced 1:1:1:1）。balanced 设计是为了 diagnostic pressure-testing，不是自然分布估计。

**允许的替代写法：** "SimClaim is a controlled silver diagnostic test set with deliberate balanced four-way label design for diagnostic pressure-testing. It is NOT a natural-prevalence corpus and does not estimate real-world prevalence."

---

### 5. "Gold validated"

**禁用理由：** Gold adjudication 未开始。所有标签为 silver。§VII 50-pair two-layer gold pilot protocol 是 planned/frozen，NOT executed。

**允许的替代写法：** "All labels are silver (AI-preannotated). Gold adjudication is pending (§VII protocol planned, NOT begun). Claims are conditional on silver-stage evidence."

---

### 6. "Full automatic review"

**禁用理由：** R4 是 second-stage screening router，产出 review queue 供人工二审，不是全自动审稿。standalone_viable=false。

**允许的替代写法：** "The pipeline produces a second-stage review queue for human review. R4 is a screening router, not a full automatic review system."

---

### 7. "V3.18 as main method" / "Learned selector/ranker improves main method"

**禁用理由：** V3.18 intelligent upgrade 是 negative ablation。learned selector strong_F1=0.4444 < baseline 0.4503；learned ranker P@20=0.35 < baseline 0.45。`supports_v3_18_intelligent_upgrade=false`；`best_overall_method=V3.17_baseline`。

**允许的替代写法：** "V3.18 intelligent upgrade is an exploratory negative ablation. Learned selector and ranker did not improve over the V3.17 baseline (selector strong_F1 -0.006; ranker P@20 -0.10). V3.17 baseline remains the selected main method. V3.18 is retained for §VIII limitations / §IX future work."

---

### 8. "Raw BM25 chunks directly work" / "BM25 raw chunks alone solve screening"

**禁用理由：** Raw BM25 top1 strong_F1=0.1806，远低于 canonicalized 0.4503。Raw chunks 严重破坏 R4 screening。必须经过 evidence canonicalization。

**允许的替代写法：** "Raw BM25 retrieved chunks degrade R4 screening (strong_F1=0.1806). Evidence canonicalization (best_sentence_top5_overlap) restores strong_F1 to 0.4503, a +0.2697 gain. Canonicalization is the critical bridge between retrieval and screening."

---

### 9. "Local LLM baseline completed"

**禁用理由：** Local LLM baseline 是 future work，未完成。当前只有 DeepSeek-V3 API baseline（200 samples）和 GPT-5.5 API probe（100 samples），都是 API-based，不是 local LLM。

**允许的替代写法：** "Local LLM baseline is future work (see `project_synthesis/local_llm_baseline_feasibility_note_v1/`). Current LLM comparison uses API-based DeepSeek-V3 (200 samples) and GPT-5.5 (100 samples). A local-LLM pilot is a candidate next step but has not been executed."

---

## 补充禁用（次要但需注意）

### 10. "Official RIGOURATE reproduced"

**禁用理由：** 官方 RIGOURATE 代码/数据/模型未公开。scalar baseline 是显式 proxy，不是官方复现。

**允许的替代写法：** "Official RIGOURATE is not publicly available. We use a scalar proxy baseline inspired by RIGOURATE's design; this is NOT an official reproduction."

---

### 11. "First scientific overstatement benchmark"

**禁用理由：** Scientific overstatement detection 是已有方向（RIGOURATE, ForceBench, CLAIM-BENCH）。CESE-OCN 不是第一个。

**允许的替代写法：** "CESE-OCN contributes an offline PDF-corpus evidence-sufficiency screening framework to the existing scientific overstatement detection track."

---

### 12. "The model fully understands scientific language"

**禁用理由：** R4 是 feature-based relation-specific screening router（NLI + action-gap features），不是语言理解系统。

**允许的替代写法：** "R4 is a feature-based screening router using NLI and action-gap features. It does not perform language understanding in the LLM sense."

---

### 13. "V3.7 is the current paper" / "V3.7 is the current selected method"

**禁用理由：** V3.7 是历史 advisor-handoff 草稿。当前 selected method 是 V3.17 baseline。

**允许的替代写法：** "V3.7 is a historical advisor-handoff paper draft. The current selected main method is V3.17 baseline (offline PDF-corpus evidence-sufficiency screening)."

---

### 14. "Hierarchical taxonomy is the empirical mainline"

**禁用理由：** Hierarchical taxonomy 是 paper-level interpretation，不是 empirical mainline。Empirical mainline 是 offline PDF-corpus screening pipeline。

**允许的替代写法：** "The hierarchical diagnostic taxonomy is a paper-level interpretation framework. The empirical mainline is the offline PDF-corpus evidence-sufficiency screening pipeline (V3.17 baseline)."

---

### 15. "Gold pilot is the single most decisive next action"

**禁用理由：** Gold pilot 仍是未来可信度步骤，但当前主线方向是 offline PDF-corpus screening 框架。Gold 不是唯一决定性下一步。

**允许的替代写法：** "Gold adjudication is a future credibility step. The current mainline direction is the offline PDF-corpus evidence-sufficiency screening framework with V3.17 baseline selected. Candidate next steps include paper rewrite per V3.17 mainline, evidence-force contrastive features, and optional local LLM pilot."

---

## 检测与更正流程

1. 在论文或项目记录中发现上述任何表述 → 标记为 stale
2. 查阅 `D:\ocn\project_synthesis\mainline_realignment_v1\updated_allowed_forbidden_claims.md` 找到允许的替代写法
3. 更正表述，保留原文备查（如有历史价值）
4. 在 `D:\ocn\project_synthesis\mainline_realignment_v1\mainline_realignment_change_log.md` 中记录更正

---

## Cross-reference

- 允许的写法（A1-A9）：`D:\ocn\project_synthesis\mainline_realignment_v1\updated_allowed_forbidden_claims.md`
- 主线证据地图：`D:\ocn\_MAINLINE_CURRENT\_MAINLINE_EVIDENCE_MAP.md`
- 最终数字表：`D:\ocn\_MAINLINE_CURRENT\_FINAL_NUMBERS_FOR_PAPER.csv`
- Realignment change log：`D:\ocn\project_synthesis\mainline_realignment_v1\mainline_realignment_change_log.md`
