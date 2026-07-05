# Advisor Package Recommendation — V3.9

**Audit date:** 2026-07-04
**Auditor:** Pre-advisor critical audit
**Target:** V3.9 Pre-Gold Complete Manuscript + 5 supporting files

## Verdict: B — Minor Revision Before Advisor

**The paper can be sent to the advisor after minor revisions.** No new experiments are needed. No gold annotation is needed before advisor review. The revisions are wording/framing fixes that take 1-2 hours of editing.

## Why Not A (Send Directly)?

Two fatal framing issues (see `reviewer_attack_report_v3_9.md` F1, F2) would make a bad first impression on the advisor:

1. **F1 — "Pre-gold complete draft" reads as apologetic.** The title page leads with what the paper *isn't* ("not submission-ready") rather than what it *is* ("silver-stage pilot with pre-registered gold validation"). This signals weakness before the advisor reads a single result.

2. **F2 — Results section uses present tense ("R4 improves," "LLM under-detects") without conditional framing.** The paper says all results are pre-gold in the Limitations, but the Results section itself doesn't say "if gold supports silver labels, this pattern holds." The advisor will notice this asymmetry.

Both are fixable in 30 minutes of editing.

## Why Not C (Do Not Send)?

The data is sound. All numbers are traceable to frozen experiment files (verified during this audit). The gold validation protocol is genuinely pre-registered and well-designed. The paper's structure is complete. The advisor's feedback should focus on whether the *positioning* is right, not whether the *data* is right. Sending the paper now (after minor fixes) lets the advisor weigh in before the gold annotation effort begins — which is exactly the right sequencing.

## Maximum 10 Minor Revisions (All Wording/Framing, No New Experiments)

1. **Reframe title page.** Remove "Not submission-ready until gold validation is completed" from the prominent position; move to a footnote. Lead with "Silver-stage pilot with pre-registered gold validation protocol (§VII)."

2. **Add conditional framing to §VI Results opener.** After "All numeric results in this section are computed against silver labels," add: "If gold adjudication (§VII) supports the silver labels, these patterns hold; if not, the paper is downgraded per §VII.G."

3. **Reduce "pre-gold" repetition from 14 to 4 occurrences.** Keep in: Abstract, §VI opener, §VII opener, §X closer. Replace elsewhere with "silver-stage" or "pilot."

4. **Add "on silver labels" qualifier to every §VI numeric claim.** "R4 improves strong-action positive-F1 from 0.2408 to 0.3967" → "On silver labels, R4 improves..."

5. **Reframe the 4 contributions (§I) as "pilot contributions."** "(i) We propose a framework..." rather than "(i) It frames..." Add "pilot" or "framework" modifier to each.

6. **Add FP/TP ratio to §VIII.A.** From existing data: R4 produces 122 false positives (98 supported→strong + 24 mild→strong). On the 100-sample set with ~25 true strong_action cases, FP/TP ≈ 4.9. State this explicitly.

7. **Add forward-reference to §VII in §VI.B.** After "other prompt designs remain untested," add: "Two additional prompt designs (decision-tree, few-shot) are pre-registered for gold-subset evaluation (Table G3); if either closes the gap, the claim is downgraded per §VII.G criterion 3."

8. **Move external validation (§VI.D) to appendix or reframe as "transferability probe."** The current "external sanity check" framing takes main-text space but doesn't test the taxonomy.

9. **Add "hypothesis" label to the four-class taxonomy in §III.C.** "The existence of strong_action_overclaim as a reliably drawable class is itself a hypothesis; §VII pre-registers the test of this hypothesis."

10. **Remove "The current silver-stage evidence motivates gold validation rather than replacing it" from §VII.H and §IX.** Keep only in §X closer. Replace §VII.H with: "The downgrade criteria in §VII.G specify what happens if gold does not support the silver-stage findings." Replace §IX reference with: "See §VII for the gold validation protocol and §IX Limitation 7 for the pre-gold draft statement."

## 发给导师的中文说明

导师您好：

附件是 CESE-OCN 项目的 V3.9 版本论文，请审阅。这一版是 **silver-stage pilot + 预注册 gold validation protocol**，不是投稿终稿。

**论文当前状态：**
- 框架完整：四类标签体系（supported / mild_scope_overclaim / strong_action_overclaim / contradiction_candidate）、R4 路由框架、决策树、444 条 silver 标注、LLM 对比实验（GPT-5.5 + DeepSeek-V3）、外部数据 sanity check 均已完成。
- 数字已冻结：所有 §VI 结果可在 `D:\ocn\experiments\` 下复现，R4 strong-F1=0.3967，LLM strong-F1=0.0769，bootstrap CI=[0.1058, 0.1988]，10/10 seeds positive。
- Gold 未做：§VII 设计了完整的 gold validation protocol（50 样本 pilot，2 标注员 + adjudication，6 条成功标准 + 6 条降级触发），全部 pre-registered，但尚未执行。

**希望您判断的核心问题：**
1. 四类标签体系是否值得继续做 gold？如果 strong_action_overclaim 这个类本身不可靠（author audit 75% confusion rate），整个论文的核心贡献就垮了。Gold pilot 的 mild_vs_strong κ≥0.40 是预注册的生死线。
2. R4 macro-F1 比 LLM 低 0.22（0.3280 vs 0.5523），但 strong_action-F1 比 LLM 高 0.22（0.3000 vs 0.0769）。这个"互补定位"是否能支撑一篇论文？还是 macro-F1 太低直接被拒？
3. LLM under-detection 是在 silver label 上算的，62.5% silver label 被作者自己标为 questionable/unclear。这个 finding 是否值得做 gold 验证？还是 silver 太不可靠就不该写论文？

**如果您的判断是"结构可以，做 gold"**，我会按 §VII 的 protocol 执行 50 样本 gold pilot，结果填入 Tables G1-G3。
**如果您的判断是"结构需要改"**（比如四类改三类、或者重新定位），我先改结构再做 gold，不浪费 gold 标注成本。
**如果您的判断是"pivot"**（比如框架方向不对），现在改方向比做完 gold 再改便宜得多。

附带的审计文件（`V3_9_pre_gold_complete_audit/`）是我自己做的提交前严苛审计，包含模拟审稿人攻击、claim-evidence 对齐、语言审计、gold protocol 压力测试。您可以参考，也可以忽略。

谢谢您的时间。

## Files For Advisor Review

- `D:\ocn\paper_versions_ordered\V3_9_pre_gold_complete\CESE_OCN_V3_9_pre_gold_complete.md` — main manuscript
- `D:\ocn\paper_versions_ordered\V3_9_pre_gold_complete\CESE_OCN_V3_9_pre_gold_complete.docx` — DOCX
- `D:\ocn\paper_versions_ordered\V3_9_pre_gold_complete\gold_validation_placeholder_tables.csv` — Tables G1-G3
- `D:\ocn\paper_versions_ordered\V3_9_pre_gold_complete\gold_validation_protocol_section.md` — pre-registered criteria
- `D:\ocn\paper_versions_ordered\V3_9_pre_gold_complete\pre_gold_completion_log.md` — V3.8 → V3.9 changes
- `D:\ocn\paper_versions_ordered\V3_9_pre_gold_complete\advisor_note_v3_9.md` — original advisor note
- `D:\ocn\paper_versions_ordered\V3_9_pre_gold_complete_audit\` — this audit pack (6 files)
