# V3.13 Claims Allowed / Forbidden for Paper (RIGOURATE-Differentiated + Realism-Aware)

**Date:** 2026-07-05
**Version:** V3.13 RIGOURATE-Differentiated + Realism-Aware
**Source:** §II.A, §VI.E, §VII.J, §IX, and Appendix B of CESE_OCN_V3_13_rigourate_differentiated_realism_aware.md.

This file lists the claims that are **allowed** and **forbidden** in V3.13 RIGOURATE-Differentiated + Realism-Aware. It is a companion to Appendix B (Language Guardrails) and is intended as a quick-reference checklist for paper text, advisor cover note, and any downstream presentation.

---

## 1. Allowed claims (can be written in the paper)

### Positioning and contribution

- "CESE-OCN is a fine-grained evidence-sufficiency relation diagnosis framework for rare high-risk scientific action overclaims, positioned on the existing scientific overstatement / evidence-force calibration track."
- "This work builds on RIGOURATE [30], the evidence-licensed claims perspective [31], ForceBench [35], and CLAIM-BENCH [28]; it does not introduce scientific overstatement detection or evidence sufficiency calibration as a new field."
- "The contribution is a fine-grained relation-type decomposition with a frozen, protocol-locked validation mechanism — not the introduction of scientific overstatement detection as a new field, and not a claim of state-of-the-art overstatement detection."
- "CESE-OCN outputs a four-class relation label on a single claim and targets the high-risk action-overclaim sub-class as a screening target, complementing continuous overstatement scoring (RIGOURATE), contrastive paired-claim force testing (ForceBench), and full-paper claim-evidence extraction (CLAIM-BENCH)."

### Taxonomy

- "We decompose evidence-sufficiency mismatch into supported, mild_scope_overclaim, strong_action_overclaim, and contradiction_candidate, with an operational decision tree (Figure 2), concrete examples (Table 0), and explicit boundary rules."
- "strong_action_overclaim is the high-risk boundary class: the most consequential for scientific claim calibration and the hardest to detect, because the evidence is often relevant and the claim is not strictly false; it is simply stronger than the evidence warrants."
- "The separability of strong_action_overclaim as a reliably drawable class is a hypothesis tested by the pre-registered gold adjudication (§VII), not an assumption taken as already proven."

### Data (SimClaim)

- "SimClaim is a controlled counterfactual diagnostic benchmark of 444 claim-evidence pairs across 111 evidence groups and six domains, with AI-preannotated and author-screened silver labels."
- "SimClaim is not a natural-prevalence corpus of author-written claims. It is a controlled counterfactual diagnostic set: evidence spans are drawn from real scientific papers, while claim variants are generated to instantiate specific evidence-sufficiency relations."
- "The four-way balanced design (111 per class) is a deliberate construction for pressure-testing boundary recognition under matched evidence, not an estimate of the natural prevalence of these relations in real scientific writing."
- "In natural scientific corpora, we expect contradiction_candidate and strong_action_overclaim to be substantially rarer than supported and mild_scope_overclaim."
- "SimClaim is appropriate for pressure-testing boundary recognition under matched evidence and for controlled comparison of relation-specific routing strategies; it is not appropriate for estimating the real-world prevalence of each evidence-sufficiency relation in scientific papers."

### R4 method and results

- "On the controlled silver-stage evaluation, R4 improves strong-action positive-F1 from 0.2408 to 0.3967 (+0.1559, CI [0.1058, 0.1988], 10/10 seeds positive) while preserving contradiction and escalation performance."
- "R4 is positioned as a screening-oriented complement to black-box LLM judges, not a replacement and not a state-of-the-art overstatement detector."
- "On the controlled silver-stage evaluation, R4's macro-F1 (0.3280) is substantially lower than GPT-5.5 (0.5523) and DeepSeek-V3 (0.5248) on the same 100 matched samples. R4's value is relation-specific: it targets the strong_action_overclaim relation that LLM judges miss under the tested prompts."
- "R4 captures 8/24 strong_action cases that all three LLM judges (GPT standard, GPT structured, DeepSeek) miss on the matched 100."
- "R4 over-routes supported → strong (98 false positives) and mild → strong (24 false positives) — a trade-off for improved strong recall. This is a known trade-off: R4 improves strong recall at the cost of supported/mild → strong false positives."

### LLM judge comparison

- "Under the tested prompts, generic LLM judges (GPT-5.5, DeepSeek-V3) consistently under-detect strong_action_overclaim on the controlled silver-stage evaluation — a validation-pending finding."
- "On the controlled silver-stage evaluation, both GPT-5.5 standard and structured achieve strong_action-F1 of 0.0769 (recall 0.04 = 1/25). This structured 5-step evidence-sufficiency decomposition prompt design did not improve strong_action detection under the tested setting."
- "LLM judge results are labeled 'small-sample controlled evaluation, N ≤ 200' and are never merged with SimClaim main results or claimed as gold standard."
- "We do not claim that 'LLMs cannot solve strong_action_overclaim' — only that under the tested prompts, on the current silver diagnostic set, the pattern is observed across the two tested models."

### RIGOURATE-style proxy baseline (§VI.E)

- "As of 2026-07-05, the official RIGOURATE code, data, and fine-tuned model weights are not publicly available. A full official reproduction was therefore not possible from public resources."
- "We construct a RIGOURATE-style scalar overstatement proxy baseline and explicitly label it as a proxy, NOT as the official RIGOURATE system."
- "On the controlled silver-stage evaluation, a scalar score (whether cue-based or LLM-derived) cannot reliably distinguish mild_scope_overclaim from strong_action_overclaim (ROC-AUC ≤ 0.59)."
- "On the controlled silver-stage evaluation, a scalar score cannot match R4's strong_action screening F1 (R4 strong_F1 = 0.3967 vs. rule_scalar best-F1 = 0.3844 on silver 444; R4 strong_F1 = 0.3000 vs. rule_scalar = 0.1364 on matched 100)."
- "Scalar overstatement scoring and relation-specific screening are complementary: scalar for broad severity ranking, relation-specific for high-risk action-overclaim screening."
- "The nli_scalar_score baseline is BLOCKED with `blocked_reason` recorded (HCM/NLI features not present in the active repository); no result is fabricated for this baseline."

### Gold validation (two-layer protocol)

- "Gold validation is two-layer: Layer 1 relation label agreement, Layer 2 claim realism / plausibility audit."
- "The pre-registered realism thresholds are: 25% class-level (if > 25% of claims in any class have realism_score ≤ 2, that class is flagged for paper-validity review) and 25% paper-level (if > 25% of all claims have realism_score ≤ 2, the paper's main claims are downgraded)."
- "Gold does not verify that synthetic claims naturally occur; it verifies relation-label reliability and claim plausibility."
- "A heuristic pattern-based realism pre-screen flagged 21/444 (4.7%) of SimClaim silver claims overall and 10/111 (9.0%) for the strong_action_overclaim class. Both are below the 25% pre-registered threshold, but the strong_action_overclaim rate is non-trivial and motivates prioritising that class in gold sampling. This heuristic pre-screen is NOT gold and does NOT pre-judge the gold result."

### Non-gold credibility checks (§VIII.D)

- "The three credibility checks in §VIII.D are non-gold robustness analyses and do not replace independent gold adjudication."
- "Evidence Necessity Check (§VIII.D.A): the task is evidence-sensitive, not a claim-only shortcut."
- "Screening Utility Test (§VIII.D.B): R4 provides targeted recall-improving screening signal for strong_action_overclaim at an operationally acceptable FP/TP ratio."
- "Label-Shift Stress Test (§VIII.D.C): the silver-stage screening claim has quantified robustness to simulated strong-label shift, with a pre-registered break-even threshold (~50% retention) that ties directly to the §VII.G downgrade criteria."

### Limitations and validation-pending status

- "All numeric results in §VI are computed on the controlled silver-stage evaluation against AI-preannotated, author-screened silver labels. The pre-registered gold adjudication (§VII) is the protocol-locked mechanism that determines whether these patterns are treated as validated."
- "The author sanity audit flags 62.5% of silver labels as questionable or unclear; the pre-registered gold adjudication (§VII) is the protocol-locked validation mechanism."
- "The framework is positioned as a controlled silver-stage action-overclaim diagnostic with a protocol-locked validation mechanism."
- "The controlled silver-stage evidence motivates the protocol-locked gold validation rather than replacing it."
- "R4's macro-F1 is substantially lower than LLM judges (0.3280 vs. 0.5523 on matched 100); R4 is a screening-oriented complement, not a general-purpose classifier."
- "Validation-pending; gold validation is planned but not completed."

---

## 2. Forbidden claims (must NOT appear in the paper)

### Field-claim forbidden

- "We introduce scientific overstatement detection / evidence sufficiency calibration as a new field." (This work builds on RIGOURATE [30], evidence-licensed claims [31], ForceBench [35], and CLAIM-BENCH [28]; it is a fine-grained relation-type decomposition on the existing track, not a new field.)
- "First work / first benchmark / first to propose evidence sufficiency calibration." (Use "fine-grained diagnostic variant of evidence-sufficiency calibration" instead.)
- "We open a new research direction."

### Data forbidden

- "SimClaim is a natural-prevalence corpus." (SimClaim is a controlled counterfactual diagnostic set; §V.A.)
- "SimClaim estimates the real-world prevalence of strong_action_overclaim / contradiction_candidate." (SimClaim's balanced design is a deliberate construction; §V.A.)
- "The silver-stage screening finding transfers to natural scientific writing." (The proposed two-layer gold realism audit §VII.J has not yet been run; natural-claim transferability is not established.)
- "SimClaim claims are natural author-written claims." (SimClaim claims are generated counterfactual variants; §V.A.)

### Gold / silver forbidden

- "Our labels are gold / human-audited." (All 444 SimClaim labels are AI-preannotated, author-screened silver; §VII.)
- "GPT can be used as gold label." (LLM judge results are small-sample controlled evaluation, never gold; §V.B.)
- "Gold benchmark." (Use "controlled silver-stage diagnostic" instead.)
- "Gold validated." (Gold validation is planned but not completed; §VII.)
- "Validated taxonomy." (Use "frozen taxonomy pending protocol-locked gold validation" instead.)

### R4 vs LLM forbidden

- "R4 outperforms GPT overall." / "R4 is stronger than LLMs on all metrics." (R4's macro-F1 is lower than LLM judges; R4 is a screening-oriented complement, not a replacement.)
- "R4 beats LLM overall." / "R4 is the best model." (R4 targets strong_action only, at the cost of lower macro-F1.)
- "Cost-sensitive cw4.0 is the new main method." (R4 frozen is the main method; cw4.0 is auxiliary.)
- "CESE-OCN outperforms strong baselines on a final benchmark." (This is a framework-level contribution with controlled silver-stage evidence, not a benchmark victory.)

### RIGOURATE / ForceBench / CLAIM-BENCH forbidden

- "CESE-OCN outperforms RIGOURATE / ForceBench / CLAIM-BENCH." (The differentiation is positioning-level, not a head-to-head empirical benchmark; §II.A, Table X, §IX item 9.)
- "Official RIGOURATE reproduced." (Official RIGOURATE code/data/model are not publicly available as of 2026-07-05; §VI.E; §IX item 11.)
- "The RIGOURATE-style proxy baseline is the official RIGOURATE system." (The proxy is explicitly labelled as proxy, NOT official RIGOURATE; §VI.E; §IX item 11.)
- "R4 outperforms the official RIGOURATE system." (Official RIGOURATE is not available for head-to-head comparison; §VI.E; §IX item 11.)
- "The blocked nli_scalar_score baseline was completed." (nli_scalar_score is BLOCKED with `blocked_reason` recorded; no result is fabricated; §VI.E; §IX item 11.)

### LLM under-detection forbidden

- "Proves LLMs cannot detect strong_action_overclaim." / "All LLMs are bad at this task." (The finding is prompt/model/sample specific and silver-stage; §VI.B; §IX item 3.)
- "Established LLM blind spot." (Use "under-detection pattern observed under the tested prompts, validation-pending" instead.)
- "Systematic blind spot." (Use "under-detection pattern observed under the tested prompts" instead.)
- "Fundamental limit of LLMs." (The finding is prompt/model/sample specific; §VI.B; §IX item 3.)

### General forbidden

- "We solve scientific claim calibration." / "Our model fully handles strong action overclaims."
- "Final proof." (Use "controlled silver-stage evidence" instead.)
- "SOTA / state-of-the-art." / "Fully solved."
- "The framework is validated for deployment." / "All four classes are well-calibrated."
- "supported_vs_mild boundary is resolved." / "Cross-domain generalization is confirmed."
- "Submission-ready / final benchmark complete." (This is a framework-level contribution with a protocol-locked validation mechanism; gold validation is planned but not completed.)
- "Workshop / pilot-only / low-config positioning." (This is a high-standard framework contribution.)

---

## 3. Preferred language (use these instead of forbidden variants)

- "under the tested prompts" / "under this tested setting"
- "on the controlled silver-stage evaluation" / "on the 100 matched samples"
- "single-run, temperature 0, no variance estimate"
- "prompt/model/sample specific"
- "under-detection pattern observed under the tested prompts" (NOT "systematic blind spot", NOT "established")
- "on the controlled silver-stage evaluation" / "AI-preannotated, author-screened labels"
- "framework-level contribution" / "validation-pending"
- "suggests" / "is consistent with" / "does not support"
- "screening-oriented complement to black-box LLM judges"
- "protocol-locked validation mechanism" / "pre-registered adjudication"
- "high-risk boundary class" / "controlled silver-stage evidence"
- "RIGOURATE-style scalar proxy baseline" (NOT "official RIGOURATE")
- "BLOCKED with `blocked_reason` recorded" (for nli_scalar_score)
- "controlled counterfactual diagnostic set" (NOT "natural-prevalence corpus")
- "two-layer gold protocol" (Layer 1 relation + Layer 2 realism)
- "validation-pending" (NOT "gold validated")

---

## 4. Verification checklist (for any new text added to the paper)

Before adding any new sentence to V3.13 RIGOURATE-Differentiated + Realism-Aware, verify:

- [ ] Does it claim to open a new field? If yes, REMOVE.
- [ ] Does it claim to be the first to propose scientific overstatement / evidence-force calibration? If yes, REMOVE.
- [ ] Does it claim R4 outperforms LLM judges overall? If yes, REMOVE.
- [ ] Does it claim gold validation is complete? If yes, REMOVE.
- [ ] Does it claim SimClaim is a natural-prevalence corpus? If yes, REMOVE.
- [ ] Does it claim the RIGOURATE-style proxy is the official RIGOURATE system? If yes, REMOVE.
- [ ] Does it claim the nli_scalar_score baseline was completed? If yes, REMOVE.
- [ ] Does it claim CESE-OCN outperforms RIGOURATE / ForceBench / CLAIM-BENCH? If yes, REMOVE.
- [ ] Does it claim the silver-stage finding transfers to natural scientific writing? If yes, REMOVE.
- [ ] Does it delete or weaken the R4 macro-F1 < LLM fact? If yes, REMOVE.
- [ ] Does it delete or weaken the gold-not-done fact? If yes, REMOVE.
- [ ] Does it delete or weaken the silver-not-gold fact? If yes, REMOVE.
- [ ] Does it delete or weaken the SimClaim-is-counterfactual fact? If yes, REMOVE.

If all checks pass, the sentence is safe to add.
