# Advisor Cover Note — CESE-OCN V3.7

**To:** Advisor / Collaborator
**From:** Author
**Date:** 2026-07-04
**Re:** Review draft for evidence-sufficiency calibration paper (advisor-review draft, not final submission)
**Enclosed:** `CESE_OCN_V3_7_advisor_handoff_clean.md` (+ `.docx`), `one_page_project_summary.md`, `reviewer_risk_brief.md`, `V3_7_cleanup_log.md`, `V3_7_file_manifest.csv`

---

## 1. What this paper is about (current main line)

The paper is about **evidence sufficiency calibration for scientific claims**. The core observation is that scientific claim verification is usually framed as a three-class support/refute/NEI task (FEVER, SNLI, SciFact), but this framing misses the most frequent and consequential failure mode in scientific writing: the evidence is topically relevant and directionally consistent, yet it does not justify the *strength* of the claim — particularly when a claim asserts deployment readiness, actionability, safety, policy, or broad generalization on the basis of limited experimental evidence.

We formulate this as a four-class relation problem: **supported**, **mild_scope_overclaim**, **strong_action_overclaim**, and **contradiction_candidate**. The central class is `strong_action_overclaim` — claims that assert an action/deployment/safety/operational conclusion the evidence does not justify. The claim is not strictly false; it is simply stronger than the evidence warrants.

We propose **CESE-OCN R4**, a mixed relation-routing framework that handles the three separable relations in order: contradiction first (most separable via NLI signals), strong-action escalation under a conservative contradiction guard, then a supported/mild residual classifier. R4 is explicitly positioned as a **complement** to generic LLM/NLI judges, not a replacement.

## 2. Current strongest result

On a silver-label pilot of 444 claim-evidence pairs across 111 evidence groups and six domains:

- **R4 improves strong_action positive-F1 from 0.2408 (flat baseline) to 0.3967** (+0.1559), with bootstrap CI [0.1058, 0.1988] positive in 10/10 seeds, while preserving contradiction performance.
- On 200 matched samples, **DeepSeek-V3** reaches macro-F1 0.5270 but strong_action-F1 only **0.0769** (recall 0.04 = 1/25).
- On 100 matched samples, **GPT-5.5** with both a standard judge prompt and a structured 5-step evidence-sufficiency decomposition prompt yields strong_action-F1 **0.0769** (identical — structured prompting did not fix the blind spot under the tested prompt).
- On the same 100 matched samples, **R4 reaches strong_action-F1 0.3000** (absolute gap +0.2231 over LLM judges), with macro-F1 0.3280 (substantially lower than GPT-5.5's 0.5523).

External sanity checks on SciFact and VitaminC confirm that R4-compatible methods transfer to public data (best E1 macro-F1 0.6895 on SciFact, 0.6686 on VitaminC via NLI cross-encoder), but cannot replace SimClaim gold due to limited taxonomy coverage.

## 3. Why R4 is positioned as a complement, not a replacement

The honest framing is that **R4 is not the strongest model on overall macro-F1** — GPT-5.5 and DeepSeek-V3 both retain that. R4's value is relation-specific: it targets the `strong_action_overclaim` relation that LLM judges miss under the tested prompts. The structured-prompt experiment (GPT-5.5 standard vs. structured) was specifically designed to test whether a 5-step evidence-sufficiency decomposition would fix the LLM blind spot — it did not, under this single tested prompt setting. We do not claim this is a permanent property of LLM judges; we claim it holds under the tested prompts and samples, and R4 provides targeted value in that regime.

This positioning matters: the paper does **not** claim "R4 beats LLMs" overall. It claims "ordinary LLM judges under-detect strong_action_overclaim on the tested samples, and R4 provides complementary value on that specific relation, at the cost of lower overall macro-F1."

## 4. Current biggest risk: gold labels are missing

The largest unresolved risk is that **all 444 SimClaim labels are silver, not gold**. They are AI-preannotated and author-screened, but not independently adjudicated. The author sanity audit of 40 silver labels flags **25/40 (62.5%) as questionable or unclear**, concentrated at the mild-vs-strong and strong-vs-contradiction boundaries.

This means:
- The LLM under-detection finding is computed against silver labels, so it must be interpreted as **diagnostic evidence against silver labels, pending independent gold adjudication** — not as an established property of LLM judges.
- If gold adjudication reveals that the mild/strong boundary is not reliably drawable (κ < 0.4 on this boundary), the `strong_action_overclaim` class itself may need to be merged with `mild`, which would weaken the paper's central contribution.
- A small gold pilot (suggested: 50-100 pairs, two-annotator independent review + adjudication) is the single highest-value next step. The `high_risk_sample_bank.csv` already prioritizes the 25 questionable cases.

Other risks (LLM comparison is prompt/model/sample-specific, R4 macro-F1 lower than GPT, mild/strong boundary remains difficult, no independent adjudication) are documented in `reviewer_risk_brief.md`.

## 5. What I would most value your feedback on

1. **Is the taxonomy (four classes, especially `strong_action_overclaim`) conceptually sound?** Does the boundary between `mild_scope_overclaim` and `strong_action_overclaim` correspond to a real distinction in scientific writing, or is it an artifact of the silver-labeling process?

2. **Is `strong_action_overclaim` valuable as a target class?** Even if the gold pilot shows the boundary is hard, is the *concept* of "evidence sufficient for the claim's strength, including its action framing" worth formalizing, or should it collapse into a weaker "scope overclaim" category?

3. **Is this suitable as a diagnostic paper submission?** The current positioning is a pilot validation of an evidence-sufficiency calibration framework with a relation-specific router, explicitly bounded by silver labels and small-sample LLM comparison. Would you recommend targeting a diagnostic-paper venue (e.g., EMNLP findings, NAACL findings, a workshop, or a domain journal), or do you think the framing needs to be strengthened (e.g., full gold adjudication) before any submission?

4. **Is a gold pilot worth doing before submission?** My current inclination is yes — a 50-100 pair gold adjudication would substantially strengthen (or falsify) the central claim. But it requires annotator time and may take 2-4 weeks. Do you agree this is the right priority, or would you recommend a different next step (e.g., larger LLM comparison, more domains, a different ablation)?

5. **Target journal/conference suggestions?** Given the current state — silver labels, small-sample LLM comparison, R4 as complement not replacement — which venues would you consider realistic, and which would you recommend I avoid until the gold pilot is done?

## 6. Honest summary

This is an advisor-review draft, not a final submission. The strongest finding (R4 targets the strong_action gap that LLM judges miss) is real and reproducible on the silver-label pilot, but its strength as a *scientific* claim depends on the gold pilot. The writing has been cleaned up (V3.7 fixes the `EMNAACP` typo, unifies table/figure numbering, removes placeholder author info, generates this cover note and a one-page summary), but the substantive content has not changed since V3.6 — no new experiments, no new data, no new API calls.

I am not asking you to endorse the paper for submission. I am asking for your read on (a) whether the taxonomy is worth formalizing, (b) whether the strong_action class is worth defending, (c) whether a gold pilot is the right next step, and (d) where you would target this if the gold pilot confirms the pattern.

Thank you for your time.
