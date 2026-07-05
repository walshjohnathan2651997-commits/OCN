# Reviewer Risk Brief — CESE-OCN V3.7

**Purpose:** One-page summary of the top reviewer risks for the evidence-sufficiency calibration paper. Each risk lists what it is, the current mitigation in the manuscript, and what would fully resolve it. Current version: advisor-review draft, not final submission.

---

## Risk 1: Silver labels are not gold.

**Risk.** All 444 SimClaim labels are AI-preannotated + author-screened silver, not independently adjudicated gold. The author sanity audit flags 25/40 (62.5%) as questionable/unclear. A reviewer can reject any quantitative finding (R4 strong_action-F1, LLM under-detection) as "computed against unvalidated labels."

**Current mitigation.** Manuscript explicitly labels all results as silver-label pilot, never as gold. Limitations section (§VIII) states silver labels are not ready to be treated as gold. LLM under-detection finding is framed as "diagnostic evidence against silver labels, pending independent gold adjudication — not as an established property of LLM judges." `high_risk_sample_bank.csv` prioritizes 25 questionable cases for future gold adjudication. No claim of "established" or "validated" anywhere in the paper.

**What would fully solve it.** Independent two-annotator gold adjudication on at least 50-100 pairs (suggested: 25 questionable cases + randomly sampled clear cases), with inter-annotator agreement reported per class (especially κ on the mild/strong boundary). If κ ≥ 0.4 on the mild/strong boundary, the taxonomy holds and findings can be re-computed against gold. If κ < 0.4, the `strong_action_overclaim` class may need to be merged with `mild`.

---

## Risk 2: LLM comparison is prompt/model/sample-specific.

**Risk.** The LLM under-detection finding (GPT-5.5, DeepSeek-V3 all converge on strong_action-F1 0.0769, recall 0.04) is based on a single standard judge prompt and a single structured 5-step decomposition prompt, on 100-200 matched samples. A reviewer can argue that a different prompt, a different model (Claude, Gemini, Llama), few-shot examples, or chain-of-thought would fix the blind spot, making the finding an artifact of the tested prompts.

**Current mitigation.** Manuscript explicitly bounds the claim: "under the tested prompts," "on the tested samples," "this single tested prompt setting." The structured-prompt experiment is included specifically to show that one obvious fix (5-step decomposition) did not work under this setting. All LLM results are labeled "small-sample pilot, N ≤ 200," never merged with SimClaim main results, never claimed as gold standard. No claim of "LLMs systematically fail" — only "consistent under-detection pattern under the tested prompts."

**What would fully solve it.** A sweep over (a) multiple models (GPT, Claude, Gemini, open-source), (b) multiple prompt variants (standard, structured, few-shot, chain-of-thought, retrieval-augmented), (c) larger sample size (≥ 500), with the strong_action-F1 reported per condition. If the under-detection pattern holds across models/prompts/samples, the finding is established; if it disappears under some condition, the manuscript would report the boundary.

---

## Risk 3: R4 macro-F1 is lower than GPT/DeepSeek.

**Risk.** R4's overall macro-F1 (0.3280 on matched 100) is substantially lower than GPT-5.5 (0.5523) and DeepSeek-V3 (0.5248). A reviewer can argue R4 is simply a weaker model that happens to score higher on one class, and that the "complement not replacement" framing is a hedge to avoid admitting R4 is worse overall.

**Current mitigation.** Manuscript explicitly states "R4 is not the strongest model on overall macro-F1 — LLM judges retain that" in the introduction, results, and discussion. R4 is positioned as a relation-specific complement targeting `strong_action_overclaim`, with explicit acknowledgment that R4 sacrifices overall macro-F1 for targeted strong_action recall. The contribution claim is "targeted value on a relation LLM judges miss," not "R4 is better." Forbidden-claims list (Appendix B) explicitly forbids "R4 outperforms GPT overall" / "R4 is stronger than LLMs on all metrics."

**What would fully solve it.** Two paths: (a) strengthen R4's overall macro-F1 via better routing/features (would require new experiments, currently out of scope), or (b) accept the complement framing and validate it via a combined system (LLM judge + R4 escalation) that outperforms either alone on both macro-F1 and strong_action-F1. The combined-system experiment is a natural next step but is not in the current draft.

---

## Risk 4: Mild/strong boundary remains difficult.

**Risk.** The author sanity audit shows 12/25 questionable/unclear cases are mild-vs-strong boundary cases. Even with the four-step decision tree (Figure 2), 12 cases remain ambiguous. A reviewer can argue the `strong_action_overclaim` class is not reliably drawable, and that the high R4 strong_action-F1 is an artifact of silver labels that happen to be separable but would not be separable under gold.

**Current mitigation.** Decision tree (Figure 2) operationalizes the boundary with explicit cue lists (deploy, safety, guarantee, operational, policy, broad generalization, outperforms, suitable for, theoretically justified). Boundary cases are flagged in `high_risk_sample_bank.csv` for future gold priority. Limitations section explicitly states "12 cases remain ambiguous even with the decision tree" and "if gold adjudication reveals that the mild/strong boundary is not reliably drawable (κ < 0.4 on this boundary), the `strong_action_overclaim` class itself may need to be merged with `mild`." Manuscript does not claim the boundary is solved.

**What would fully solve it.** Gold adjudication with per-boundary κ on the mild/strong boundary specifically. If gold annotators can reliably distinguish mild from strong (κ ≥ 0.4), the class is defensible. If not, the taxonomy collapses to three classes (supported / scope_overclaim / contradiction) and the paper's central contribution weakens — but the broader evidence-sufficiency framing still holds.

---

## Risk 5: No independent adjudication yet.

**Risk.** The author sanity audit was conducted by the author, not by independent annotators. A reviewer can argue the 25/40 questionable/unclear rate is itself biased (author may over- or under-flag), and that no claim about label quality — including the claim that labels are "silver not gold" — is itself trustworthy without independent review.

**Current mitigation.** Manuscript explicitly states the audit is an "author sanity audit," not an independent adjudication. Limitations section lists "no independent adjudication" as a separate item from "silver not gold." The 40-case audit is positioned as a *lower bound* on label quality issues (the real rate under independent review could be higher or lower). No claim that the audit establishes gold-readiness.

**What would fully solve it.** Independent two-annotator adjudication on the 40 audit cases (plus additional randomly sampled cases), with κ reported between (a) the two independent annotators, (b) independent annotators vs. silver labels, (c) independent annotators vs. author audit. This would establish whether the author audit is calibrated and whether the silver labels are recoverable under independent review.

---

## Summary

| # | Risk | Current mitigation | Full solution |
|---|---|---|---|
| 1 | Silver labels not gold | Explicit silver labeling; framing as diagnostic | 50-100 pair gold adjudication |
| 2 | LLM comparison prompt/model/sample-specific | "Under the tested prompts" bounding | Multi-model multi-prompt sweep, N ≥ 500 |
| 3 | R4 macro-F1 lower than GPT | "Complement not replacement" framing | Combined LLM+R4 system experiment |
| 4 | Mild/strong boundary difficult | Decision tree + boundary case bank | Gold κ on mild/strong boundary |
| 5 | No independent adjudication | Author audit labeled as such | Independent two-annotator adjudication |

**Bottom line:** The single highest-value next step is the gold pilot (50-100 pairs, two-annotator independent review + adjudication). It addresses risks 1, 4, and 5 directly, and provides a stronger foundation for risks 2 and 3. Without the gold pilot, the paper remains a silver-label pilot validation, suitable for diagnostic-paper venues but not for claims of established findings.
