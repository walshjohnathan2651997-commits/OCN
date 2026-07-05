# Final Paper Outline (Current Mainline) — 论文最终骨架

**Date:** 2026-07-05
**Selected main method:** V3.17 baseline (offline PDF-corpus evidence-sufficiency screening)
**V3.18:** negative ablation (§VIII limitations)
**Note:** This is the outline skeleton only. The paper body itself was NOT modified in this task.

---

## §I Introduction

**应放内容：**
- 问题动机：科学论文中的 evidence-sufficiency 判断（claim 与 evidence 是否匹配）是科研审稿与可信度评估的核心环节
- 当前缺口：LLM judges 整体 macro_F1 高，但在 Level-2 strong_action overclaim 上严重 under-detect（strong_recall=0.04 under tested prompts）；raw PDF retrieval 直接喂给 downstream screening 会严重破坏性能
- 本文贡献（三点）：
  1. 发现 raw PDF chunks 破坏 downstream strong_action screening（raw BM25 top1 strong_F1=0.1806 vs oracle 0.4257）
  2. 证明 evidence canonicalization 是 retrieval-to-screening 的关键桥梁（canonicalized strong_F1=0.4503，+0.2697 gain，仅 -0.0246 below oracle）
  3. 将 R4 定位为离线、可审计、second-stage strong_action screening router（standalone_viable=false, second_stage_viable=true）
- 明确范围：本项目不是通用 LLM 审稿器、不是自然分布 benchmark、不是 R4 overall beats LLM

**关键数字：** raw BM25 top1 strong_F1=0.1806; canonicalized strong_F1=0.4503; canonicalization gain +0.2697; R4 strong_recall=0.7064 vs LLM strong_recall=0.04

**禁止表述：** "R4 beats LLM overall"; "first scientific overstatement benchmark"; "full automatic review"; "standalone detector"

---

## §II Related Work

**应放内容：**
- Scientific overstatement detection track：RIGOURATE（官方不可复现，scalar proxy only）、ForceBench、CLAIM-BENCH
- LLM-as-judge：GPT-5.5 / DeepSeek-V3 整体 macro_F1 高（0.55 / 0.53），但 strong_action under-detect
- Evidence retrieval for scientific claims：BM25 / dense retrieval；raw chunks 与 downstream screening 的 gap
- Hierarchical / multi-level claim taxonomy（作为 paper-level interpretation，不是 empirical mainline）

**关键区分：** 本文不是第一个 benchmark，而是 offline PDF-corpus evidence-sufficiency screening framework，贡献在 canonicalization bridge + second-stage positioning

---

## §III Task and Dataset

**应放内容：**
- Task definition：offline PDF-corpus evidence-sufficiency screening；输出是 second-stage review queue，不是 final adjudication
- SimClaim dataset：
  - 444 claim-evidence pairs, 111 evidence groups, 6 domains
  - Balanced 1:1:1:1 across supported / mild_scope_overclaim / strong_action_overclaim / contradiction_candidate
  - Controlled counterfactual diagnostic set（NOT natural-prevalence）
  - Silver labels（AI-preannotated）；gold adjudication pending（§VII protocol planned, NOT begun）
  - Real evidence spans + generated claim variants
- 操作流程：PDF corpus → BM25 top-k → canonicalization → R4 → ranking → review queue

**关键数字：** n=444; n_groups=111; n_domains=6; balance=1:1:1:1; safe_as_diagnostic_set=true; safe_as_naturalistic=false

**禁止表述：** "natural prevalence"; "gold validated"; "natural distribution"

---

## §IV Method

**应放内容：**
- §IV.1 PDF corpus & BM25 retrieval
  - PDF corpus 构建与清洗
  - BM25 top-k retrieval（top-5 chunks per claim）
- §IV.2 Evidence canonicalization
  - `best_sentence_top5_overlap` selector：从 top-5 BM25 chunks 选最佳句子（简单 overlap-based）
  - 为什么需要 canonicalization：raw chunks 包含 metadata + 多句拼接，破坏 R4 screening
  - Canonicalization 是 retrieval-to-screening 的关键桥梁
- §IV.3 R4 relation-specific screening router
  - 4 个 operational labels：supported / mild_scope_overclaim / strong_action_overclaim / contradiction_candidate
  - Route function `route_conservative_strong(p_contra, p_strong, p_svm, t_contra, t_contra_low, t_strong, t_svm, n)`
  - 10 seeds [11,22,33,44,55,66,77,88,99,111]，per-seed thresholds，majority-vote aggregation，prefer test split with dev fallback
  - NLI features (7) + action-gap features (9) = 16 expert_features；svm_features = NLI (7) + scope_gap = 8
  - R4 定位为 second-stage screening router（NOT standalone, NOT LLM-replacement）
- §IV.4 Risk ranking
  - 8 个 ranking formula variants（A_flag_only through H_balanced_review_score）
  - Selected: `G_conservative_precision`（P@20=0.45，最佳）
  - `priority_score = p_strong_mean - p_contra_mean + 0.5 * strong_action_flag`
- §IV.5 Second-stage review queue
  - Top-100 prioritized candidates
  - 设计为 human-in-the-loop，不是 final adjudication

**关键数字：** BM25 top-k=5; 10 seeds; per-seed thresholds (seed_11: t_contra=0.4, t_contra_low=0.35, t_strong=0.55, t_svm=0.55); G_conservative_precision P@20=0.45

**禁止表述：** "standalone detector"; "raw BM25 chunks directly work"; "full automatic review"

---

## §V Experiments

**应放内容：**
- §V.1 Main result: V3.17 baseline
  - strong_F1=0.4503, strong_recall=0.7064, strong_precision=0.3305, macro_F1=0.3847
  - P@20=0.45, R@100=0.3303, FP/TP@5%=11.24
  - standalone_viable=false, second_stage_viable=true
- §V.2 Evidence canonicalization ablation
  - raw_bm25_top1 strong_F1=0.1806 vs best_sentence_top5_overlap strong_F1=0.4503（gain +0.2697）
  - oracle_span strong_F1=0.4257（上界）
  - oracle_to_best_gap=-0.0246（canonicalization near oracle）
  - Format shift ablation：metadata drop=0.0101, lengthening drop=0.3320（lengthening 是主因）
  - 9 个 canonicalization formats 中 6/9 above 0.40（robustness）
  - Canon helped 129/436, canon harmed 3/436
- §V.3 R4 vs LLM comparison
  - R4 macro_F1=0.4238（historical frozen R4 baseline, silver 444）
  - DeepSeek-V3 macro_F1=0.5270（200 samples），strong_recall=0.04
  - GPT-5.5 standard macro_F1=0.5523（100 samples），strong_recall=0.04
  - GPT-5.5 structured macro_F1=0.5543（100 samples），strong_recall=0.04
  - R4 V3.17 strong_recall=0.7064 vs LLM strong_recall=0.04（controlled silver-stage finding, NOT fundamental LLM limit）
- §V.4 Risk ranking variant comparison
  - 8 variants；G_conservative_precision 最佳（P@20=0.45）
- §V.5 Second-stage viability analysis
  - FP/TP @ 1% = 66.82（standalone not viable）
  - FP/TP @ 5% = 11.24 / 12.84（second-stage viable）
  - FP/TP @ 10% = 6.07

**关键数字：** 见 `_FINAL_NUMBERS_FOR_PAPER.csv`

**禁止表述：** "R4 beats LLM overall"; "gold validated"; "natural distribution"

---

## §VI Discussion

**应放内容：**
- 为什么 canonicalization 是关键：format shift（metadata + lengthening）破坏 R4 的 NLI + action-gap features；canonicalization 恢复 sentence-level 单句格式
- 为什么 R4 是 second-stage：strong_precision 低（0.3305），standalone FP/TP 不可接受；但 strong_recall 高（0.7064），second-stage 价值大
- R4 vs LLM 互补性：R4 高 strong_recall，LLM 高 macro_F1；两者互补，不是替代关系
- SimClaim 作为 controlled diagnostic set 的局限：balanced 设计不能估计自然分布；silver 标签噪声

---

## §VII Limitations（含 V3.18 negative ablation）

**应放内容：**
- §VII.1 Silver labels
  - 所有标签为 silver；gold adjudication 未开始
  - Silver 标签噪声可能影响 selector/ranker 训练
- §VII.2 V3.18 intelligent upgrade negative ablation
  - Learned selector strong_F1=0.4444 < baseline 0.4503（gap -0.006）
  - Learned ranker P@20=0.35 < baseline 0.45（gap -0.10）
  - Learned ranker FP/TP@5%=2.00（partial improvement，但 P@20 未通过）
  - `supports_v3_18_intelligent_upgrade=false`
  - 可能原因：feature space saturation, silver label noise, small sample size, R4 hard threshold limitations
  - 32 r4_screening_failure candidates 无法通过 ranking 恢复
- §VII.3 Controlled diagnostic set
  - SimClaim 不是自然分布；结果不能外推到真实患病率
- §VII.4 R4 hard thresholds
  - Per-seed thresholds frozen；不能自适应
- §VII.5 LLM comparison scope
  - LLM strong_recall=0.04 是 controlled silver-stage finding under tested prompts，NOT fundamental LLM limit

---

## §VIII Future Work

**应放内容：**
- Gold adjudication（§VII protocol, 50-pair two-layer）
- Evidence-force contrastive features（lowest cost, no API）
- Local LLM baseline pilot（medium cost, no API；pre-registered 120-pair）
- Adaptive thresholds / learned routing（future, after gold）
- Natural-prevalence corpus extension（future, separate from diagnostic set）

---

## §IX Conclusion

**应放内容：**
- 重申三点贡献：raw chunks degrade；canonicalization restores；R4 is second-stage
- V3.17 baseline 是 selected main method
- V3.18 negative ablation 确认 simple overlap-based canonicalization is robust
- 局限：silver labels, controlled diagnostic set, R4 second-stage only

---

## Appendix

- §A R4 per-seed thresholds
- §B Canonicalization format ablation full table
- §C Risk ranking 8-variant full table
- §D V3.18 5-method comparison table
- §E SimClaim dataset statistics

---

## 写作纪律

1. 每个数字必须可在 `_FINAL_NUMBERS_FOR_PAPER.csv` 中找到 source_file
2. 每个表述必须通过 `_DO_NOT_USE_OLD_CLAIMS.md` 检查
3. 每个实验引用必须标注 status（mainline / supporting / negative_ablation / historical）
4. V3.18 只出现在 §VII limitations，不作为 main method
5. R4 vs LLM 必须标注 "controlled silver-stage finding under tested prompts"
6. SimClaim 必须标注 "controlled silver diagnostic test set, NOT natural-prevalence"
