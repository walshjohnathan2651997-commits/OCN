# Evidence Sufficiency Calibration for Scientific Claims: A Mixed Relation-Routing Framework

**Version:** V3.4 (taxonomy hardened)
**Date:** 2026-07-04
**Changes from V3.3:** Taxonomy boundary hardening — added operational decision tree for the four-class taxonomy, diagnosed root causes of the 25 questionable/unclear audit cases (taxonomy boundary vs. audit too conservative vs. claim too abstract vs. evidence too short), built trusted case bank (18 illustrative cases) and high-risk sample bank (25 boundary cases), added 'Boundary cases are not noise to hide' discussion, strengthened Limitations with boundary challenge. No new experiments, no API calls, no new data.

Author information to be added before submission

## Abstract

Scientific claim verification is typically framed as deciding whether evidence supports or refutes a claim. We argue that this framing is insufficient for scientific writing, where a more frequent failure mode is that the evidence is topically relevant but does not justify the *strength* of the claim — in particular when a claim asserts deployment readiness, actionability, safety, policy relevance, or broad operational conclusions on the basis of limited experimental evidence. We call this task **evidence sufficiency calibration**, and we study it as a four-class relation problem: supported, mild_scope_overclaim, strong_action_overclaim, and contradiction_candidate.

We present CESE-OCN R4, a mixed relation-routing framework that complements generic LLM/NLI judges. R4 routes each claim-evidence pair through a contradiction detector, a scope-calibration residual classifier, and a conservative strong-action escalation route. On a silver-label pilot set of 444 claim-evidence pairs across 111 evidence groups and six domains, R4 improves strong_action_overclaim positive-F1 from 0.2408 (flat baseline) to 0.3967 (+0.1559, bootstrap CI [0.1058, 0.1988], 10/10 seeds positive), while preserving contradiction positive-F1 (0.7296 vs. 0.7308).

We then compare R4 against generic LLM judges. On 200 SimClaim samples, DeepSeek-V3 achieves macro-F1 0.5270 and contradiction-F1 0.8317, but strong_action-F1 only 0.0769 (recall 0.04 = 1/25). On 100 matched samples, GPT-5.5 with a standard judge prompt achieves strong_action-F1 0.0769, and GPT-5.5 with a structured 5-step evidence-sufficiency decomposition prompt still achieves strong_action-F1 0.0769 — this structured prompt design did not improve strong_action detection. On the same 100 samples, R4 achieves strong_action-F1 0.3000 (absolute gap +0.2231), while LLM judges retain substantially higher macro-F1 (GPT-5.5: 0.5523; R4: 0.3280) and contradiction-F1. R4 is therefore positioned as a relation-specific complement, not a replacement: LLM judges are stronger overall, but under the tested prompts they consistently under-detect strong_action_overclaim, and R4 provides targeted value on this specific relation.

Results are exploratory: labels are silver (AI-preannotated, author-screened) rather than fully adjudicated gold, the dataset is small, and the LLM comparison is prompt/model/sample specific (single-run, temperature 0). A small author sanity audit of 40 silver labels (§V.D) flags 25/40 as questionable or unclear, confirming that independent gold adjudication is required before the LLM blind spot finding can be treated as established. External sanity checks on SciFact and VitaminC show R4-compatible methods run on public data but underperform NLI cross-encoders on generic support/refutation; public data cannot test the four-class evidence-sufficiency taxonomy. The contribution is therefore a falsifiable framework and a frozen main method, not a final benchmark claim.

Index Terms — evidence sufficiency, claim calibration, scientific claims, action overclaim, relation-specific routing, LLM-as-judge, natural-language inference, simulation evidence.

## I. Introduction

Scientific claim verification is typically framed as a three-class task: given a claim and evidence, decide whether the evidence *supports* the claim, *refutes* it, or provides *not enough information* (NEI). This framing — established by benchmarks such as FEVER [1], SNLI [2], and SciFact [3] — is effective for factual correctness, but it is **insufficient** for scientific claim calibration, where the most frequent and consequential failure mode is not outright contradiction but **strength mismatch**: the evidence is topically relevant, directionally consistent, and non-contradictory, yet it does not justify the *strength* of the claim. A benchmark improvement becomes a "deployment-ready system"; a controlled simulated result becomes a "safety guarantee"; a single-domain observation becomes a "generalization claim". These cases are not captured by support/refute/NEI labels, because the evidence does support *something* — just not the action, deployment, or operational conclusion asserted by the claim.

This motivates the **evidence sufficiency calibration** task. Rather than asking only whether evidence supports or refutes a claim, we ask whether the evidence is *sufficient for the strength of the claim* — including its scope, action framing, deployment implications, safety conclusions, and generalization breadth. We formulate this as a four-class relation problem: (i) **supported** — the evidence supports the claim as stated, including its strength; (ii) **mild_scope_overclaim** — the claim mildly over-extends the scope of the evidence, without asserting an action/deployment/safety conclusion; (iii) **strong_action_overclaim** — the claim asserts an action, deployment, safety, policy, generalization, guarantee, or operational conclusion that the evidence does not justify; (iv) **contradiction_candidate** — the evidence contradicts the claim. Class (iii) — strong_action_overclaim — is the most consequential and the hardest to detect, because the evidence is often relevant and the claim is not strictly false; it is simply stronger than the evidence warrants.

A natural hypothesis is that strong LLM judges (GPT-5.5, DeepSeek-V3) should handle this task well, given their broad language understanding. We test this hypothesis empirically. We find that under the tested prompts, generic LLM judges are strong on overall support/refutation and contradiction (GPT-5.5 macro-F1 = 0.5523, DeepSeek-V3 macro-F1 = 0.5270 on matched samples), but they **consistently under-detect strong_action_overclaim on the tested samples**: on 100 matched SimClaim samples, both GPT-5.5 with a standard judge prompt and GPT-5.5 with a structured 5-step evidence-sufficiency decomposition prompt achieve strong_action-F1 of only 0.0769 (recall 0.04 = 1/25). DeepSeek-V3 on 200 samples achieves the same strong_action-F1 of 0.0769. The structured prompt — which explicitly asks the model to decompose factual alignment, scope expansion, action/deployment claims, and evidence sufficiency — does *not* improve strong_action detection under this single tested prompt design. This suggests that this prompt-engineering approach alone does not fix the under-detection pattern under the tested setting. We emphasize that this finding is bounded: it is single-run, on 100 matched silver-labeled samples, with one structured prompt design, and we do not claim that LLMs cannot solve strong_action_overclaim — only that under the tested prompts, on the current silver diagnostic set, the pattern is consistent across the two tested models.

We therefore position CESE-OCN R4 as a **complement** to generic LLM/NLI judges, not a replacement. R4 is a mixed relation-routing framework: a contradiction detector handles the most separable relation first; a scope-calibration residual classifier handles supported vs. mild_scope_overclaim; and a conservative strong-action escalation route targets strong_action_overclaim specifically, under a guarded condition that prevents contradiction cases from being absorbed. On the same 100 matched samples where GPT and DeepSeek achieve strong_action-F1 0.0769, R4 achieves strong_action-F1 0.3000 (absolute gap +0.2231). **R4 is not the strongest model on overall macro-F1 — LLM judges retain that, with GPT-5.5 at 0.5523 vs. R4 at 0.3280 on the matched 100 — but it provides targeted value on the relation that LLM judges miss under the tested prompts.** This positioning as a relation-specific complement, rather than a competitive replacement, is central to the paper's contribution.

This manuscript makes four cautious contributions:

(i) It frames scientific claim calibration as **evidence sufficiency calibration**, a four-class relation task distinguishing strong_action_overclaim from generic support/refutation/NEI, with concrete taxonomy examples (Table 0) and an author sanity audit of silver labels (§V.D);

(ii) It constructs a **silver diagnostic set** of 444 claim-evidence pairs across 111 evidence groups and six domains, with AI-preannotated and author-screened labels, and provides taxonomy examples (Table 0) to make the label space concrete and reproducible;

(iii) It introduces **CESE-OCN R4**, a conservative strong-action router as a mixed relation-routing framework that complements black-box LLM judges, with explicit acknowledgment that R4 sacrifices overall macro-F1 for targeted strong_action recall, and with a text Figure 1 describing the routing flow;

(iv) It reports a **matched-sample LLM judge comparison** (DeepSeek-V3, GPT-5.5 standard, GPT-5.5 structured) showing that under the tested prompts, this structured decomposition design does not improve strong_action detection, while R4 provides complementary value on this relation — bounded by silver-label and single-run limitations, and explicitly not a claim that R4 outperforms LLM judges overall.

The remainder of the paper is organized as follows: §II positions the work relative to claim verification, NLI, RAG evaluation, hedging, and calibration; §III formulates the evidence sufficiency calibration task and provides taxonomy examples (Table 0); §IV describes the CESE-OCN R4 mixed relation-routing framework (Figure 1); §V describes the data and experimental protocol, including the author sanity audit; §VI reports results; §VII discusses implications; §VIII states limitations; §IX concludes.

## II. Related Work and Positioning

### A. Claim Verification, NLI, and RAG Evaluation

Generic claim verification and NLI estimate whether evidence supports or contradicts a statement (FEVER [1], SNLI [2], SciFact [3]). RAG evaluation and LLM-as-judge frameworks (RAGAs [12], ARES [13], G-Eval [14], MT-Bench [15]) similarly evaluate faithfulness, context relevance, or answer quality. These frameworks are designed for generic factuality, not for the specific failure mode of evidence-claim *strength* mismatch. CESE-OCN is complementary: it asks whether a scientific claim calibrates its strength to the evidence available, including cases where the claim is topically relevant but over-extends the action implied by the evidence.

### B. Overclaiming as Relation-Specific Calibration

The current results suggest that contradiction, scope shift, and action escalation should not be treated as identical classification errors. Contradiction aligns naturally with NLI-style signals. Mild scope shift remains ambiguous and may require finer annotation. **Strong action overclaim sits between support and contradiction**: the evidence may support a factual finding but not the action, deployment, or generalization asserted by the claim. This is why a single flat four-class classifier under-performs on strong_action_overclaim (baseline strong-F1 0.2408), and why a relation-specific router (R4, strong-F1 0.3967) is needed.

### C. LLM-as-Judge and the Action-Overclaim Under-Detection Pattern

A growing body of work uses LLMs as automated judges for evaluation tasks [14, 15]. We test whether strong LLM judges (GPT-5.5, DeepSeek-V3) naturally solve the strong_action_overclaim task, or whether they exhibit a consistent under-detection pattern. Our results show that under the tested prompts, both GPT-5.5 standard and GPT-5.5 structured (5-step evidence-sufficiency decomposition) achieve strong_action-F1 of only 0.0769 on 100 matched samples, while R4 achieves 0.3000 on the same samples. The structured prompt does not hurt macro-F1 or contradiction-F1, but it does not improve strong_action either under this single tested prompt design. This pattern suggests that this prompt-formatting approach alone does not fix the under-detection pattern, and that a relation-specific router provides complementary value. We emphasize that this finding is bounded: it is single-run, on 100 matched silver-labeled samples, with one structured prompt design. We do not claim that LLMs cannot solve strong_action_overclaim — only that under the tested prompts, on the current silver diagnostic set, the pattern is consistent across the two tested models.

### D. Hedging, Certainty, and Claim Strength (Added in V3.2)

Evidence sufficiency calibration is related to but distinct from several existing lines of work. Hedging detection (e.g., Hyland 2005 on metadiscourse) identifies linguistic cues that weaken claims, but does not ask whether the evidence supports the claim's strength. Certainty detection in scientific text identifies confidence levels, but does not compare claim strength to evidence support. NLI calibration work (e.g., Desai & Durrett 2020) calibrates NLI probability outputs, but does not introduce a strength-calibration taxonomy. Evidence sufficiency calibration is distinct: it focuses on the **gap between claim strength and evidence support**, including cases where the claim is unhedged but over-asserts an action that the evidence cannot justify.

### E. Positioning of This Revision

The revised manuscript is a **pilot validation** of an evidence-sufficiency calibration framework with a relation-specific router. It is **not** a final public benchmark, **not** a human-gold evaluation, and **not** a claim that all four classes are solved. The target contribution is a falsifiable framework and a frozen main method whose numeric claims are constrained by the paper-ready result pack. All LLM comparison results are labeled as small-sample pilot (N ≤ 200) and are never merged with SimClaim main results or claimed as gold standard.

## III. Task and Problem Formulation

### A. Evidence Sufficiency Calibration Task

Each instance consists of a claim, an evidence span, and a silver candidate label in four relation classes:

- **supported**: the evidence supports the claim as stated, including its strength. This is not "the claim is absolutely true" — it means the evidence is sufficient for the strength of the claim as written.
- **mild_scope_overclaim**: the evidence supports a weaker version of the claim; the claim mildly over-extends the scope (e.g., a single-dataset result is framed as a multi-dataset result), but no action/deployment/safety conclusion is asserted.
- **strong_action_overclaim**: the claim asserts an action, deployment, safety, policy, generalization, guarantee, or operational conclusion that the evidence does not justify. The evidence typically supports only limited experiments, local observations, or metric improvements — but the claim promotes these into a stronger action framing. **strong_action_overclaim is not the same as contradiction**: the claim may be directionally consistent with the evidence, but its strength is excessive.
- **contradiction_candidate**: the evidence contradicts the claim; the claim and evidence point in opposite directions on the same metric or conclusion.

Labels are treated as AI-preannotated development labels (silver), not as gold adjudications.

### B. Table 0: Taxonomy Examples (Added in V3.2)

To make the taxonomy concrete and reproducible, Table 0 provides 8 examples (2 per class) from the SimClaim silver set. The examples are drawn from two evidence groups (G215 policy_simulation, G175 marl) to illustrate that **the same evidence can yield all four labels depending on claim strength** — the taxonomy is about claim strength relative to evidence, not about evidence content alone.

**Table 0. Taxonomy examples (2 per class, from SimClaim silver set).**

| # | candidate_id | domain | label | claim_text (shortened) | why_this_label |
| --- | --- | --- | --- | --- | --- |
| 1 | SBV2-ALL92-G215-C01 | policy_simulation | supported | "The ABM discussion says decision-support effectiveness remains uncertain because calibration, heterogeneous data integration, and result interpretation require expertise." | Evidence directly supports the claim as stated, including its strength; no over-extension. |
| 2 | SBV2-ALL92-G175-C01 | marl | supported | "The Craftax-Coop evaluation compares MAPPO with IPPO, which trains agents independently, and PQN, a parallel-environment Q-learning algorithm method." | Evidence directly supports the claim as stated; no over-extension. |
| 3 | SBV2-ALL92-G215-C02 | policy_simulation | mild_scope_overclaim | "The ABM discussion says decision-support effectiveness remains uncertain because calibration and heterogeneous data integration require expertise, while interpretation is resolved." | Claim mildly over-extends scope — evidence says interpretation is *uncertain*, claim says it is *resolved*. No action conclusion asserted. |
| 4 | SBV2-ALL92-G175-C02 | marl | mild_scope_overclaim | "The Craftax-Coop evaluation compares MAPPO with IPPO... and PQN, a recurrent value-based Q-learning algorithm." | Claim says PQN is "recurrent value-based" but evidence says PQN is "parallel-environment Q-learning". Scope detail mildly over-extended. |
| 5 | SBV2-ALL92-G215-C03 | policy_simulation | strong_action_overclaim | "The ABM discussion says decision-support effectiveness remains uncertain because calibration, data integration, interpretation, and validation require extensive expertise." | Claim asserts that validation requires extensive expertise and frames this as an operational barrier — a stronger action/deployment conclusion than the evidence supports (evidence says "uncertain", claim asserts "extensive expertise required for validation"). |
| 6 | SBV2-ALL92-G175-C03 | marl | strong_action_overclaim | "The Craftax-Coop evaluation compares MAPPO with IPPO, PQN, and QMIX while treating each method as a parallel-environment Q-learning algorithm." | Claim asserts a broader operational characterization (all methods as "parallel-environment Q-learning") than the evidence supports — evidence only describes IPPO and PQN, not QMIX, and the characterization is the claim's action framing, not the evidence's. |
| 7 | SBV2-ALL92-G215-C04 | policy_simulation | contradiction_candidate | "The ABM discussion says decision-support effectiveness is clear because calibration, heterogeneous data integration, and result interpretation require little expertise." | Claim says effectiveness is "clear" and requires "little expertise"; evidence says effectiveness is "uncertain" and requires "expertise". Directions conflict. |
| 8 | SBV2-ALL92-G175-C04 | marl | contradiction_candidate | "The Craftax-Coop evaluation compares MAPPO with PPO-RNN and SAC rather than IPPO or PQN as companion algorithms." | Claim says comparison is with PPO-RNN and SAC; evidence says comparison is with IPPO and PQN. Directions conflict on the same fact. |

**Key distinctions illustrated by Table 0:**

1. **supported** is not "absolutely true" — it means the evidence is sufficient for the strength of the claim as stated (examples 1-2).
2. **mild_scope_overclaim** is a mild scope/precision over-extension, not an action assertion (examples 3-4).
3. **strong_action_overclaim** asserts an action/deployment/safety/generalization/guarantee/operational conclusion that the evidence does not justify — the claim may be directionally consistent with the evidence, but its strength is excessive (examples 5-6).
4. **contradiction_candidate** is a directional conflict on the same metric or conclusion (examples 7-8).
5. **strong_action_overclaim ≠ contradiction**: in examples 5-6, the claim and evidence point in the same direction (both discuss expertise requirements / method characteristics), but the claim's strength is excessive. In examples 7-8, the claim and evidence point in opposite directions. This distinction is the core of evidence sufficiency calibration.

The full Table 0 with evidence text and rationale is provided in `table_0_taxonomy_examples.csv`.

### C. Taxonomy Decision Tree (Operational, Added in V3.4)

To make the taxonomy operationalizable and reduce the boundary confusion identified in the author sanity audit (§V.D), we introduce a four-step decision tree for label assignment. The full decision tree with operational rules is provided in `taxonomy_boundary_decision_tree.md`; a summary follows.

**Step 1 — Directional conflict?** Does the claim point in the *opposite direction* from the evidence on the same metric, number, entity, or conclusion? If yes → `contradiction_candidate`. (This includes *detail-swapping*: changing specific numbers, names, or metrics — the most common contradiction pattern in SimClaim.)

**Step 2 — Action/deployment/safety/operational cue present?** Does the claim introduce deployment, safety, guarantee, operational, policy, generalization, or action language (e.g., "deployment-ready", "safety guarantee", "theoretically justified", "outperforms", "suitable for")? If yes → Step 3. If no → Step 4.

**Step 3 — Evidence sufficient for action strength?** Is the evidence limited to local/experimental/simulated results, while the claim asserts a stronger action/deployment/safety/generalization conclusion? If yes → `strong_action_overclaim`. If no → re-examine as `supported` or `mild_scope_overclaim`.

**Step 4 — Scope over-extension?** Does the claim expand scope, domain, population, condition, or temporal range beyond what the evidence supports, *without* asserting action/deployment/safety consequences? If yes → `mild_scope_overclaim`. If no → `supported`.

**Key distinctions operationalized by this tree:**

1. **strong_action_overclaim does not require directional conflict.** The claim may align with evidence direction, but its *strength* (action/deployment/safety assertion) exceeds what the evidence warrants.
2. **contradiction_candidate is about directional conflict** on the same metric/number/entity, including detail-swapping (e.g., evidence says "6 systems", claim says "8 systems").
3. **strong_action_overclaim is about strength/action consequences**, not scope breadth alone.
4. **mild_scope_overclaim is about scope/generalization over-extension** without action/deployment/safety consequences.
5. **supported means evidence is sufficient for the claim's stated strength**, not that the claim is "absolutely true."

The decision tree is a *labeling aid*, not a gold standard. Cases where the tree yields ambiguous results are flagged as boundary cases for future gold adjudication (§V.D, `high_risk_sample_bank.csv`).

### D. Why strong_action_overclaim Is the Core Hard Case

strong_action_overclaim is the most consequential class for scientific claim calibration, because it corresponds to cases where a claim is *actionable* (deployment, policy, safety) but the evidence is *insufficient* for that action. It is also the hardest to detect, because:

1. The evidence is often relevant and non-contradictory.
2. The claim is not strictly false — it over-extends rather than fabricates.
3. Generic NLI signals (entailment/contradiction) do not separate "supports a finding" from "supports the action claimed".
4. Under the tested prompts, LLM judges tend to map these cases to supported, mild_scope_overclaim, or contradiction_candidate, missing the action-escalation signal.

The primary success criterion for R4 is therefore **strong_action_overclaim positive-F1**, while requiring that flat4 macro-F1, contradiction positive-F1, and escalation macro-F1 are not damaged.

### E. Binary Projections

We also evaluate binary projections that are more stable under the current dataset:

- **escalation_binary**: supported is negative; all overclaim/contradiction classes are positive.
- **contradiction_binary**: contradiction_candidate is positive; all others are negative.
- **strong_action_binary**: strong_action_overclaim is positive; all others are negative.

## IV. CESE-OCN R4: A Mixed Relation-Routing Framework

### A. Framework Overview — Why Relation-Specific Routing

The central design principle of R4 is that **different evidence relations require different signals and should not be handled by a single flat classifier**. The pilot results support this: contradiction is comparatively well captured by NLI-style evidence signals (NLI-only strong-F1 = 0.3934), while strong_action_overclaim requires action-aware features that NLI does not provide (action-gap-only strong-F1 = 0.3648; NLI + action-gap = 0.4209, see Table 4). A single flat four-class classifier conflates these signals and under-performs on the most consequential class (baseline strong-F1 = 0.2408).

R4 is therefore designed as a **relation-specific diagnostic routing framework**, not a threshold-tuned heuristic. The routing order reflects a theoretical principle: handle the most separable relation first (contradiction), then the most consequential relation under a conservative guard (strong_action), then the residual scope calibration (supported vs. mild). The thresholds are frozen operationalizations of this principle, not tuned parameters — they are selected on train/dev under pre-specified constraints (§IV.D) and then frozen.

R4 is explicitly designed as a **complement** to generic LLM/NLI judges, not a replacement. LLM judges handle overall support/refutation and contradiction well; R4 targets the strong_action_overclaim relation that LLM judges miss under the tested prompts. R4 is **not** optimized to maximize overall macro-F1 — it is optimized to reduce under-detection of action/deployment overclaims while preserving contradiction performance. This means R4 accepts a lower macro-F1 than LLM judges in exchange for higher strong_action recall (see §VI.C and §VII.C for the explicit macro-F1 gap discussion).

### B. Routing Flow (Text Figure 1)

The R4 routing flow is:

```
claim-evidence pair
        |
        v
[NLI relation features] ---> p_contra (contradiction score)
        |                    p_strong (strong-action score)
        v                    p_svm (supported/mild score)
[scope/action/deployment cues]
        |
        v
+-----------------------------+
| Conservative strong router |
|                             |
| Route 1 (contradiction):   |
|   if p_contra >= t_contra  |
|   -> contradiction_candidate|
|                             |
| Route 2 (strong-action):    |
|   if p_strong >= t_strong   |
|      AND p_contra < t_low   |
|   -> strong_action_overclaim|
|                             |
| Route 3 (scope residual):   |
|   if p_svm >= t_svm         |
|   -> supported              |
|   else                      |
|   -> mild_scope_overclaim   |
+-----------------------------+
        |
        v
    final label
```

**Figure 1 (text).** R4 routing flow. The router applies three routes in order: contradiction first (the most separable relation), then strong-action escalation under a conservative contradiction guard (to prevent contradiction cases from being absorbed into strong_action), then a supported/mild residual classifier. Frozen mean thresholds: `t_contra = 0.48`, `t_strong = 0.535`, `t_svm = 0.51`, `t_low` = lower contradiction guard. *A standalone text version of Figure 1 with full routing rationale is provided in `V3_3_method_flow_figure_text.md`.*

### C. Why This Order — Theoretical Motivation

**Route 1 (Contradiction first).** Contradiction is the strongest and most separable relation in the pilot data. NLI-style signals capture it well (NLI-only achieves strong-F1 0.3934 on the strong-action expert, but contradiction-F1 is preserved at 0.7296). Handling contradiction first prevents downstream routes from absorbing contradiction cases into strong_action or mild.

**Route 2 (Strong-action escalation under a conservative guard).** strong_action_overclaim is the most consequential relation but the hardest to detect. The strong-action expert uses action-gap features (the gap between the action implied by the claim and the action supported by the evidence) in addition to NLI signals. The conservative guard (`p_contra < t_low`) prevents contradiction cases from being absorbed into strong_action — this is critical because strong_action and contradiction can look similar to a strong-action expert (both involve a claim-evidence mismatch), but they require different handling.

**Route 3 (Scope-calibration residual).** Supported vs. mild_scope_overclaim is the residual scope-calibration problem. This is handled last because it is the least separable boundary (supported-F1 = 0.4424, mild-F1 = 0.1266 — the weakest boundary in the taxonomy). An SVM residual classifier handles this, acknowledging that the supported/mild boundary remains an open problem.

### D. R4 Is Intentionally Conservative

R4 is intentionally conservative: it is **not** optimized to maximize overall macro-F1, but to reduce under-detection of action/deployment overclaims while preserving contradiction performance. This means:

- R4 accepts a lower macro-F1 than a flat classifier or LLM judge (R4 macro-F1 = 0.4238 on 444 samples, 0.3280 on matched 100; GPT-5.5 = 0.5523 on matched 100).
- R4 accepts supported/mild → strong false positives (98 supported → strong, 24 mild → strong in Table 6) in exchange for higher strong recall (0.4562 vs. baseline 0.2062).
- R4 is selected against 5 router variants (Table 3) under 5 pre-specified constraints: strong_positive_delta ≥ +0.05, flat4_macro_delta ≥ -0.02, contradiction_positive_delta ≥ -0.03, escalation_macro_delta ≥ -0.03, positive_delta_seed_count ≥ 7. R4 is the only router meeting all 5 constraints simultaneously.

This conservative design is the right trade-off for a **diagnostic complement** to LLM judges: R4 flags potential action overclaims that LLM judges miss, accepting false positives that a human reviewer (or an LLM judge on a second pass) can filter. R4 is not designed to be a standalone classifier.

### E. Auxiliary Cost-Sensitive Variant

A cost-sensitive strong expert with class weight 4.0 (B_cost_sensitive_cw4.0) gives a small additional improvement over R4 on strong positive-F1 (+0.0254), but the gain does not meet the replacement threshold (+0.03) and its confidence interval crosses zero. It is therefore retained only as an auxiliary sensitivity analysis, **not** as the main method.

### F. Why a Mixed Router, Not a Single Stronger Classifier

R5 (a strong-recall router) achieves higher strong_action-F1 (0.4399) but damages flat4 macro-F1 (-0.0284 vs. baseline, exceeding the -0.02 constraint). R3 (a margin router) similarly damages flat4 macro-F1. A single stronger classifier that maximizes strong_action-F1 tends to absorb supported/mild cases into strong_action, producing unacceptable false positives. R4 is the only router that meets all five pre-specified constraints simultaneously. This is not "tuning until it works" — it is selecting the router that satisfies the pre-registered trade-off constraints.

## V. Data and Experimental Protocol

### A. SimClaim Silver-Label Pilot Set

The current study uses a paper-only strict silver set containing 444 claim-evidence pairs, 111 evidence groups, six domains (policy_simulation, marl, digital_twin, robotics, autonomous_driving, cyber_defense), and balanced four-way silver labels (111 per class). Source traceability is complete in the current dataset audit. These labels are AI-preannotated and author-screened; they should not be described as human-gold. The `human_audited` field is `False` for all 444 rows; `gold_label` and `final_label` fields are empty.

All experiments use group-aware splits so that claims derived from the same evidence group do not cross train/dev/test boundaries. Router thresholds and hyperparameters are selected on train/dev only. The reported R4 result is frozen in `D:\ocn\experiments\mixed_framework_v2_frozen_r4_baseline` and should be treated as the current main baseline for this manuscript version.

### B. LLM Judge Comparison Protocol

For the LLM judge comparison, we use two matched-sample subsets:

- **DeepSeek-V3 baseline (200 samples)**: a label-balanced 200-sample subset of SimClaim, with 50 samples per class. DeepSeek-V3 is queried via the OpenAI-compatible DeepSeek API (model: `deepseek-chat`), temperature 0, single run. Output is parsed into the same four-class label space. Results are labeled "small-sample pilot, N ≤ 200" and are never merged with SimClaim main results.
- **GPT-5.5 standard vs. structured (100 samples)**: a label-balanced 100-sample subset (25 per class), selected to overlap with the DeepSeek 200-sample set and to cover all six domains. GPT-5.5 is queried via a third-party proxy (temperature 0, single run). Two prompt strategies are compared:
  - **Standard**: a direct judge prompt asking for a four-class label.
  - **Structured**: a 5-step evidence-sufficiency decomposition prompt that explicitly asks the model to (1) check factual alignment, (2) check scope expansion, (3) check whether the claim contains an action/deployment/safety/generalization assertion, (4) check whether the evidence is sufficient for that action, and (5) produce a final label.

R4 predictions on the same 100/200 samples are computed for matched-sample comparison. API keys are held in environment variables only and are never logged. The LLM comparison is **single-run, temperature 0, no variance estimate** — this is an explicit limitation (§VIII).

### C. External Public Dataset Sanity Check

To test whether the evidence-relation approach transfers to public claim-verification data, we run a small gold-derived subset evaluation on **SciFact** [3] and **VitaminC** (dev/test). Public gold labels are preserved as original (SUPPORT / CONTRADICT-REFUTES / NEI), with a conservative derived mapping (SUPPORT → supported, CONTRADICT/REFUTES → contradiction_candidate, NEI → unsupported_or_insufficient). **No mapping to strong/mild labels is performed**, because public datasets do not contain the action-overclaim taxonomy. We evaluate four methods: TF-IDF claim+evidence, TF-IDF claim-only (leakage probe), NLI cross-encoder (`cross-encoder/nli-deberta-base`), and an R4-compatible heuristic. Five seeds are used, with ≤300 eval samples per dataset.

This external evaluation is a **sanity check** for generic support/refutation transfer. It cannot replace SimClaim gold evaluation, because public datasets do not contain action-overclaim labels and cannot test the four-class evidence-sufficiency taxonomy.

### D. Author Sanity Audit of Silver Labels (Added in V3.2)

To check whether the silver labels are prima facie plausible, we conducted a small author sanity audit of 40 silver labels. **This audit is not a substitute for independent human adjudication.** It is a qualitative sanity check by the authors to flag labels that may be questionable or unclear before independent gold validation.

**Audit protocol:** We sampled 40 cases from the 444-row silver set, oversampling strong_action_overclaim (20 cases) since it is the central class of the paper, plus 7 supported, 7 mild_scope_overclaim, and 6 contradiction_candidate. For each case, the authors assessed whether the silver label is prima facie plausible based on the claim text, evidence text, and taxonomy definition (Table 0). Each case was assigned:

- `author_sanity_decision`: reasonable / questionable / unclear
- `possible_confusion`: none / supported_vs_mild / mild_vs_strong / strong_vs_contradiction

**Audit results:**

| Label | Reasonable | Questionable | Unclear | Total |
| --- | --- | --- | --- | --- |
| supported | 7 | 0 | 0 | 7 |
| mild_scope_overclaim | 3 | 0 | 4 | 7 |
| strong_action_overclaim | 5 | 5 | 10 | 20 |
| contradiction_candidate | 0 | 0 | 6 | 6 |
| **Total** | **15** | **5** | **20** | **40** |

**Key findings:**

1. **25/40 (62.5%) of silver labels are flagged as questionable or unclear.** This is a real signal that silver labels require independent gold validation before the LLM blind spot finding can be treated as established. However, root cause analysis (below) shows that the 25 cases are *not* all label noise — they reflect a mix of taxonomy boundary issues, audit heuristic limitations, and genuinely hard cases.

2. **Root cause distribution of the 25 questionable/unclear cases** (full diagnosis in `sanity_audit_error_diagnosis.csv`):
   - **mild_vs_strong_boundary_unclear (12 cases, 48%):** The claim has some scope-expansion or strength cue, but the boundary between mild_scope_overclaim and strong_action_overclaim is genuinely fuzzy. These are the core taxonomy challenge cases.
   - **strong_vs_contradiction_boundary_unclear (6 cases, 24%):** The claim swaps specific details (numbers, metrics, entity names) relative to evidence. The audit heuristic looked for explicit "contradicts" language and missed the detail-swap pattern. The decision tree (§III.C, Step 1) now operationalizes detail-swapping as contradiction.
   - **claim_too_abstract (5 cases, 20%):** The claim describes what the paper does ("presents", "evaluates", "reports") without explicit action/deployment language. The silver label strong_action may be too strong, but the claim's framing still over-extends relative to evidence.
   - **audit_heuristic_too_conservative (2 cases, 8%):** The audit keyword heuristic missed action/strength cues that are present but implicit. The silver label is likely defensible.

3. **strong_action_overclaim has the highest confusion rate** (15/20 = 75% flagged), mostly mild_vs_strong confusion. This is expected: strong_action is the most subtle class, and the boundary between mild and strong is the hardest to operationalize. The decision tree (§III.C) provides a clearer operationalization, but 12 cases remain genuinely ambiguous.

4. **All 6 contradiction_candidate cases are flagged unclear**, mostly strong_vs_contradiction confusion. Root cause analysis shows these are genuine contradiction cases (detail-swapping) that the audit heuristic missed — not label noise. The decision tree (§III.C, Step 1) now operationalizes detail-swapping as contradiction, which should reduce this confusion in future annotation.

5. **supported is the most stable class** (7/7 reasonable), which is expected since supported is the easiest class to identify.

**Interpretation:** This audit confirms that the silver labels are not ready to be treated as gold. However, the root cause analysis shows that the 25 questionable/unclear cases are *not* evidence of systematic label failure — they are concentrated at the two hardest taxonomy boundaries (mild-vs-strong and strong-vs-contradiction), which is expected for an evidence-sufficiency task. The LLM blind spot finding (§VI.C) is computed against these silver labels, and the high questionable/unclear rate means the finding must be interpreted as **diagnostic evidence against silver labels, pending independent gold adjudication** — not as an established property of LLM judges. The audit does not invalidate the framework (the relative pattern — R4 > LLM on strong_action — may hold under gold), but it bounds the strength of the claim.

The 25 questionable/unclear cases are retained in `high_risk_sample_bank.csv` as boundary cases for future gold adjudication priority. They are not deleted or hidden. A separate `trusted_case_bank.csv` (18 cases, ≥4 per class) provides clear illustrative cases for paper examples — none of which are claimed as gold.

The full audit is in `author_sanity_audit_40.csv`. This audit is **not** independent human adjudication, **not** gold labeling, and **not** a basis for treating silver labels as gold.

### E. Exploratory Framing

Because the dataset is small, silver-labeled, and the author sanity audit flags substantial label uncertainty, all results are framed as **exploratory pilot validation**. A higher-tier confirmatory submission would require 300–500 independently adjudicated claim-evidence pairs, inter-annotator agreement statistics, significance tests against stronger external baselines, and external validation.

## VI. Results

### A. Internal Silver Diagnostic Results (Group A)

The strongest supported result is that R4 improves strong-action positive-F1 while preserving contradiction and escalation. Table 1 reports the main comparison among the flat baseline, frozen R4 router, and the auxiliary cost-sensitive variant.

**Table 1. Main results for the frozen mixed framework (silver-label pilot, 444 claims, 10 seeds).**

| Method | Flat4 F1 | Strong F1 | Contra F1 | Escal. F1 | Strong Prec. | Strong Recall | Use |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_flat4 | 0.3963 | 0.2408 | 0.7308 | 0.5723 | 0.3097 | 0.2062 | baseline |
| R4_conservative_strong_router (MAIN) | 0.4238 | 0.3967 | 0.7296 | 0.6143 | 0.3791 | 0.4562 | main_method |
| B_cost_sensitive_cw4.0 (AUXILIARY) | 0.4365 | 0.4221 | 0.7296 | 0.6262 | 0.4109 | 0.4625 | auxiliary_module |

- Values are means over 10 seeds (group-aware 70/15/15 split).
- R4 is the frozen main method (immutable).
- B_cost_sensitive_cw4.0 is auxiliary: delta vs R4 = +0.0254 (below +0.03 threshold, CI crosses zero).
- All metrics computed on silver-label pilot data, NOT gold/human-audited.

**Table 2. Per-class F1 comparison.**

| Class | Baseline F1 | R4 F1 | Delta |
| --- | --- | --- | --- |
| supported | 0.4492 | 0.4424 | -0.0069 |
| mild_scope_overclaim | 0.1644 | 0.1266 | -0.0378 |
| strong_action_overclaim | 0.2408 | 0.3967 | +0.1559 |
| contradiction_candidate | 0.7308 | 0.7296 | -0.0012 |

- The key improvement is in **strong_action_overclaim** (+0.1559).
- Supported/mild remains weak and should be treated as an open boundary problem rather than a solved subtask.
- Contradiction is preserved (-0.0012, well within the -0.03 constraint).

The bootstrap confidence interval for the strong-positive delta is [0.1058, 0.1988], which does not cross zero, and the delta is positive in 10/10 random seeds. This supports the claim that the strong-action improvement is not a seed artifact, on the current silver diagnostic set.

### B. strong_action_overclaim Detection (Group B)

R4 is not the highest strong_action-F1 among router variants (R5 achieves 0.4399), but it is the only router that meets all five pre-specified constraints simultaneously. Table 3 summarizes the router selection.

**Table 3. Router variants and selection rationale.**

| Router | Strong F1 | Flat4 F1 | Contra F1 | Escal. F1 | Selected |
| --- | --- | --- | --- | --- | --- |
| baseline_flat4 | 0.2408 | 0.3963 | 0.7308 | 0.5723 |  |
| R1_contra_first | 0.3467 | 0.4124 | 0.7344 | 0.5955 |  |
| R2_strong_first | 0.3400 | 0.3925 | 0.6755 | 0.5947 |  |
| R3_margin_router | 0.4047 | 0.3565 | 0.7308 | 0.5488 |  |
| **R4_conservative_strong (SELECTED)** | **0.3967** | **0.4238** | **0.7296** | **0.6143** | **YES** |
| R5_strong_recall_router | 0.4399 | 0.3680 | 0.7363 | 0.4878 |  |

**Table 4. Strong-expert ablation.**

| Config | Strong F1 | Strong Prec. | Strong Recall | Flat4 Strong F1 |
| --- | --- | --- | --- | --- |
| TF-IDF claim-only | 0.2747 | 0.2493 | 0.3438 | 0.3342 |
| NLI only | 0.3934 | 0.2869 | 0.6312 | 0.3934 |
| Action-gap only | 0.3648 | 0.2966 | 0.4813 | 0.3857 |
| NLI + action gap | 0.4209 | 0.3430 | 0.5625 | 0.4064 |
| NLI + length/overlap | 0.4340 | 0.3705 | 0.5437 | 0.4236 |

- TF-IDF claim-only (0.2747) confirms the improvement is NOT from claim-only keywords.
- NLI is the stronger single feature (0.3934 > 0.3648 action-gap-only).
- NLI + action-gap (0.4209) > either alone: NLI and action/structure features are complementary.

**Table 5. New algorithm sweep vs. frozen R4.**

| Method | Strong F1 | Delta Strong | Delta Flat4 | CI crosses 0 | Use |
| --- | --- | --- | --- | --- | --- |
| B_cost_sensitive_cw4.0 | 0.4221 | +0.0254 | +0.0127 | YES | auxiliary_module |
| B_cost_sensitive_cw1.5 | 0.4136 | +0.0169 | +0.0030 | YES | auxiliary_module |
| A1_temp_scaled_router | 0.4076 | +0.0109 | +0.0100 | YES | auxiliary_module |
| C_ordinal_severity | 0.3685 | -0.0282 | -0.0455 | YES | diagnostic_only |
| F_recall_balance_router | 0.3185 | -0.0782 | -0.0049 | NO | reject |
| D1_ovr_contra_priority | 0.3141 | -0.0826 | -0.0384 | NO | reject |
| A3_platt_router | 0.2540 | -0.1427 | -0.0091 | NO | reject |

(Full 13-row table in `V3_1_result_tables.csv`; abbreviated here for space.)

**Table 6. Error transition pattern after R4 routing (true → predicted, counts).**

| True class | Predicted class | Count |
| --- | --- | --- |
| strong_action_overclaim | strong_action_overclaim | 64 |
| strong_action_overclaim | mild_scope_overclaim | 27 |
| strong_action_overclaim | contradiction_candidate | 14 |
| strong_action_overclaim | supported | 12 |
| supported | supported | 156 |
| supported | strong_action_overclaim | 98 |
| supported | mild_scope_overclaim | 43 |
| mild_scope_overclaim | mild_scope_overclaim | 25 |
| mild_scope_overclaim | strong_action_overclaim | 24 |
| mild_scope_overclaim | supported | 17 |
| contradiction_candidate | contradiction_candidate | 159 |
| contradiction_candidate | strong_action_overclaim | 1 |

- supported → strong = 98: R4 aggressively routes supported to strong (false positives).
- strong → strong = 64 (recall improved vs. baseline).
- This is a LIMITATION: R4 improves strong recall at the cost of supported/mild → strong false positives.

### C. LLM Judge Comparison (Group C)

This is the central new analysis of V3.1/V3.2. We compare R4 against generic LLM judges on matched SimClaim samples.

#### C.1 DeepSeek-V3 Baseline (200 samples)

DeepSeek-V3 (`deepseek-chat`) is queried on a 200-sample label-balanced subset of SimClaim (50 per class), temperature 0, single run. 100% parse rate. Results:

- **Macro-F1: 0.5270** — DeepSeek is strong on overall four-class classification.
- **Contradiction-F1: 0.8317** — DeepSeek is a strong contradiction detector.
- **strong_action-F1: 0.0769** (precision 1.0, recall 0.04 = 1/25) — DeepSeek misses strong_action_overclaim on 200 samples under the tested prompt.

DeepSeek is stronger than R4 on overall macro-F1 (0.5270 vs. 0.4238 on the full 444 set) and on contradiction-F1, but it misses almost all strong_action_overclaim cases under the tested prompt. On the same 200 samples, R4 achieves strong_action-F1 0.3158 (absolute gap +0.2389 over DeepSeek).

#### C.2 GPT-5.5 Standard vs. Structured (100 matched samples)

This is the key probe for whether this prompt-engineering approach can fix the strong_action under-detection pattern. We query GPT-5.5 on a 100-sample label-balanced subset (25 per class), with two prompt strategies, temperature 0, single run. 100% parse rate on both strategies.

**Table 7. LLM judge comparison on 100 matched SimClaim samples (Group C).**

| Method | Macro-F1 | Strong F1 | Strong Recall | Contradiction F1 |
| --- | --- | --- | --- | --- |
| GPT-5.5 standard | 0.5523 | 0.0769 | 0.04 | 0.6857 |
| GPT-5.5 structured (5-step) | 0.5543 | 0.0769 | 0.04 | 0.6857 |
| DeepSeek-V3 (same 100 samples) | 0.5248 | 0.0769 | 0.04 | 0.8317 |
| R4 (same 100 samples) | 0.3280 | 0.3000 | — | — |

- **Both GPT-5.5 standard and structured achieve strong_action-F1 of 0.0769 (recall 0.04 = 1/25).**
- This structured 5-step evidence-sufficiency decomposition prompt design **did not improve** strong_action detection.
- The structured prompt does not hurt macro-F1 (0.5543 vs. 0.5523) or contradiction-F1 (both 0.6857), but it does not improve strong_action either.
- GPT only flagged 7/100 samples as containing an action/deployment/safety claim in structured mode, despite 25/100 being strong_action_overclaim by silver label.
- On the same 100 samples, R4 achieves strong_action-F1 0.3000 (absolute gap +0.2231 over LLM judges), while LLM judges retain substantially higher macro-F1 and contradiction-F1.

#### C.3 Explicit Discussion: R4 Macro-F1 Gap (Added in V3.2)

**We explicitly acknowledge that R4's overall macro-F1 is substantially lower than LLM judges on matched samples.** On the 100 matched samples:

- GPT-5.5 standard macro-F1 = 0.5523
- GPT-5.5 structured macro-F1 = 0.5543
- DeepSeek-V3 (same 100) macro-F1 = 0.5248
- **R4 (same 100) macro-F1 = 0.3280**

The gap is approximately 0.22 (R4 is ~40% lower than GPT-5.5 on macro-F1). This is not a hidden weakness — it is a **design choice**. R4 is intentionally conservative (§IV.D): it is not optimized to maximize overall macro-F1, but to reduce under-detection of action/deployment overclaims while preserving contradiction performance. R4 sacrifices macro-F1 to gain strong_action recall.

**The complement framing depends on this gap being acceptable.** R4 is not a general-purpose LLM judge replacement. It is a relation-specific diagnostic that flags potential action overclaims. A practical deployment would use an LLM judge for supported/mild/contradiction (where LLM judges are strong) and R4 as a second-pass flag for strong_action (where LLM judges under-detect). The macro-F1 gap is the cost of this specialization; the strong_action recall gain is the benefit. Whether this trade-off is worthwhile depends on the downstream use case — for scientific writing quality monitoring where missing an action overclaim is costly, the trade-off may be favorable; for generic claim verification where overall accuracy matters most, an LLM judge alone is preferable.

We do not claim R4 is better than LLM judges overall. We claim R4 provides **targeted value on strong_action_overclaim** that LLM judges miss under the tested prompts, at the cost of lower overall macro-F1.

**This result should not be interpreted as R4 outperforming LLM judges overall.** R4's macro-F1 (0.3280) is substantially lower than GPT-5.5 (0.5523) and DeepSeek-V3 (0.5248) on the same 100 matched samples. R4's value is relation-specific: it targets the strong_action_overclaim relation that LLM judges miss under the tested prompts. The complement framing depends on this gap being acceptable for the downstream use case (§VII.C). We do not claim R4 is better than LLM judges overall — we claim R4 provides targeted value on strong_action_overclaim, at the cost of lower overall macro-F1.

#### C.4 Interpretation

The interpretation rule triggered is **Rule C: both standard and structured GPT strong_F1 < R4 strong_F1**. The recommended paper positioning is `llm_blindspot_supported` — bounded by silver-label and single-run limitations.

The key interpretation:

1. **Under the tested prompts, generic LLM judges (GPT-5.5, DeepSeek-V3) consistently under-detect strong_action_overclaim on the tested samples.** This is not a single-model issue: both GPT and DeepSeek converge on the same strong_F1 (0.0769) and the same recall (0.04 = 1/25) on matched samples.
2. **This structured evidence-sufficiency prompt design does not improve strong_action detection** under the tested setting. A 5-step decomposition that explicitly asks the model to check for action/deployment/safety claims and evidence sufficiency does not improve strong_action detection. This suggests that this prompt-formatting approach alone does not fix the under-detection pattern — but other prompt designs (few-shot, chain-of-thought, tool-augmented) remain untested.
3. **R4 provides targeted complementary value.** On the same 100 samples where GPT and DeepSeek achieve strong_F1 0.0769, R4 achieves strong_F1 0.3000 (absolute gap +0.2231). R4 is not stronger overall — LLM judges retain substantially higher macro-F1 (0.5523 vs. 0.3280) and contradiction-F1 — but it targets the specific relation that LLM judges miss under the tested prompts.
4. **This is not a claim that LLMs cannot solve the task.** The result is prompt/model/sample specific, single-run, and computed against silver labels (which the author sanity audit flags as 62.5% questionable/unclear). A different model, prompt, sample, or gold label set may behave differently. The claim is narrower: under the tested prompts, on the current silver diagnostic set, the pattern is consistent across the two tested models and suggests a relation-specific under-detection pattern that a relation-specific router can complement — pending independent gold validation.

#### C.5 Error Pattern on strong_action_overclaim

Out of 25 strong_action_overclaim cases in the 100-sample probe:

- GPT-5.5 standard correctly identifies 1/25.
- GPT-5.5 structured correctly identifies 1/25 (the same case).
- DeepSeek-V3 correctly identifies 1/25 (on the matched 100).
- R4 correctly identifies more (strong_F1 0.3000 corresponds to ~4-5/25 on the matched 100).

The dominant LLM error modes on strong_action_overclaim are:

- **Over-contradiction**: mapping strong_action_overclaim to contradiction_candidate (the LLM treats the action over-extension as a factual mismatch).
- **Over-milding**: mapping strong_action_overclaim to mild_scope_overclaim (the LLM recognizes scope expansion but misses the action escalation).
- **Over-supporting**: mapping strong_action_overclaim to supported (the LLM treats the relevant-but-insufficient evidence as full support).

R4's error mode is different: it tends to over-route supported → strong (98 cases in Table 6), producing false positives rather than false negatives on strong_action. This is a complementary error profile: LLM judges miss strong_action (false negatives), R4 over-flags strong_action (false positives). A combined system could potentially exploit this complementarity, though we leave that to future work.

### D. External Public Dataset Sanity Check (Group D)

To test whether the evidence-relation approach transfers to public claim-verification data, we run a small gold-derived subset evaluation on SciFact and VitaminC. **Public gold labels are preserved as original; the mapping to supported/contradiction_candidate/unsupported_or_insufficient is derived and does not map to strong/mild labels.**

**Table 8. External public dataset sanity check (5 seeds, ≤300 eval per dataset).**

| Dataset | Method | E1 Macro-F1 | E2 Macro-F1 | Best task |
| --- | --- | --- | --- | --- |
| SciFact | TF-IDF claim+evidence | 0.3350 | 0.5111 |  |
| SciFact | TF-IDF claim-only (leakage) | 0.3170 | 0.4629 |  |
| SciFact | NLI cross-encoder | **0.6895** | 0.6034 | E1/C (best) |
| SciFact | R4-compatible | 0.3549 | 0.5166 |  |
| VitaminC | TF-IDF claim+evidence | 0.4277 | 0.5184 |  |
| VitaminC | TF-IDF claim-only (leakage) | 0.3976 | 0.5013 |  |
| VitaminC | NLI cross-encoder | **0.6686** | 0.5691 | E1/C (best) |
| VitaminC | R4-compatible | 0.4568 | 0.5197 |  |

- **SciFact best E1 macro-F1: 0.6895** (NLI cross-encoder, N=271 per seed).
- **VitaminC best E1 macro-F1: 0.6686** (NLI cross-encoder, N=300 per seed).
- **R4-compatible underperforms NLI cross-encoder on external data** (SciFact E1: 0.3549 vs. 0.6895; VitaminC: 0.4568 vs. 0.6686). This is expected because (a) public datasets have no action-overclaim labels, so the strong-action route is inactive and R4 reduces to its contradiction + scope components; (b) R4 was not retrained on public data. The external check validates that the contradiction + scope components run without crash on public data, **not** that the full R4 framework transfers competitively. The strong-action component is SimClaim-specific by design.
- **Claim-only leakage is HIGH**: claim-only TF-IDF is within 0.018–0.030 of claim+evidence TF-IDF, indicating that public data rewards claim-only shortcuts.

**Evidence sensitivity (E3).** On VitaminC official contrastive pairs (300 per seed), the support-score delta between correct and wrong evidence is 0.0226 ± 0.007, with a sensitivity rate of 46.9%. On SciFact synthetic perturbation (209 per seed), the delta is 0.0056 ± 0.014, with a sensitivity rate of 45.5%. The evidence sensitivity is **weak but positive** on VitaminC and **near zero** on SciFact (as expected, since SciFact perturbations are synthetic and not designed as contrastive pairs).

**What this external check does and does not show:**

- ✅ R4-compatible methods run on public data without crash (contradiction + scope components transfer).
- ✅ NLI cross-encoder is a strong generic support/refutation baseline on public data.
- ✅ Evidence sensitivity is positive on VitaminC official contrastive pairs.
- ❌ Public datasets **cannot** test the four-class evidence-sufficiency taxonomy (no action-overclaim labels).
- ❌ Public datasets **cannot** replace SimClaim gold evaluation.
- ❌ Public results are **sanity checks**, not benchmark superiority claims. R4-compatible underperforms NLI on public data because the strong-action route is inactive by design.

## VII. Discussion

### A. Why LLM Macro-F1 High but Strong-F1 Low Still Matters

A natural objection to the under-detection finding is: "LLMs have higher macro-F1, so they are better overall." This objection is correct — LLM judges **are** better overall (GPT-5.5 macro-F1 = 0.5523 vs. R4 = 0.3280 on matched 100 samples, a 0.22 gap). We do not dispute this. The point is that macro-F1 averages over four classes, three of which (supported, mild_scope_overclaim, contradiction_candidate) are well-handled by LLM judges. The fourth class — strong_action_overclaim — is the most consequential for scientific claim calibration, because it corresponds to cases where a claim is *actionable* but the evidence is *insufficient* for that action. A model that misses strong_action_overclaim fails on cases that are consequential for scientific writing quality, even if its overall macro-F1 is high.

The pattern is also consistent across the two tested models. Both GPT-5.5 and DeepSeek-V3 converge on strong_F1 = 0.0769 (recall = 0.04 = 1/25), and this structured 5-step decomposition prompt design does not change this. This suggests a consistent under-detection pattern under the tested prompts, not a single-model quirk. We do not claim this is a fundamental limit of LLMs — it is prompt/model/sample specific and computed against silver labels (which the author sanity audit flags as 62.5% questionable/unclear) — but under the tested prompts, the pattern is consistent across the two tested models and suggests that a relation-specific router can complement black-box LLM judges. Independent gold validation is required before this pattern can be treated as established.

### B. Why Action-Overclaim Is the Core Hard Case

Action-overclaim is the core hard case because it sits between support and contradiction. The evidence is relevant and non-contradictory, but it does not justify the action, deployment, safety, or generalization asserted by the claim. Generic NLI signals do not separate "supports a finding" from "supports the action claimed", because both are entailment-like at the factual level. LLM judges, trained on generic factuality, tend to map these cases to supported, mild_scope_overclaim, or contradiction_candidate — all of which miss the action-escalation signal.

R4's design directly addresses this. The strong-action escalation route uses action-gap features (the gap between the action implied by the claim and the action supported by the evidence) in addition to NLI signals. The ablation (Table 4) confirms that NLI and action-gap features are complementary: combining them improves strong expert F1 over either alone (0.4209 vs. 0.3934 NLI-only, 0.3648 action-gap-only). This is consistent with R4 achieving strong_F1 0.3000 on the matched 100 samples where LLM judges achieve 0.0769 — though the absolute numbers are moderate on both sides, and the gap is computed against silver labels.

### C. Why R4's Value Is Relation-Specific Complement — And Why The Macro-F1 Gap Is Acceptable

**R4 is not the strongest model on overall macro-F1, and we explicitly acknowledge this.** LLM judges (GPT-5.5 0.5523, DeepSeek 0.5248) retain substantially higher macro-F1 and contradiction-F1 on the matched 100 samples. R4's macro-F1 on the matched 100 is 0.3280 — a 0.22 gap below GPT-5.5. This is not a hidden weakness; it is the cost of R4's conservative design (§IV.D).

R4's value is **relation-specific**: it targets the strong_action_overclaim relation that LLM judges miss under the tested prompts. This is a complementary positioning, not a competitive one. A combined system — LLM judge for supported/mild/contradiction, R4 for strong_action — could potentially exploit this complementarity, though we leave that to future work.

This positioning is also honest about R4's limitations. R4 over-routes supported → strong (98 false positives in Table 6), producing a different error profile from LLM judges. R4 is not a replacement for LLM judges on the relations they handle well; it is a complement on the relation they miss. Whether the macro-F1 gap is an acceptable trade-off depends on the downstream use case — for action-overclaim monitoring where missing a strong_action case is costly, the trade-off may be favorable; for generic claim verification, an LLM judge alone is preferable.

### D. Why Silver-Label Limitations Must Be Frank — And What the Author Sanity Audit Shows

All SimClaim results are on silver-label pilot data (AI-preannotated, author-screened), not fully adjudicated gold. The author sanity audit (§V.D) flags 25/40 (62.5%) of silver labels as questionable or unclear, with strong_action_overclaim having the highest confusion rate (15/20 = 75%). This has three implications:

1. **Numeric claims are bounded.** The strong-F1 improvement (0.2408 → 0.3967) is real on the silver set, but the absolute numbers may shift under gold adjudication. We report the delta and CI rather than treating the absolute numbers as final.
2. **LLM comparison is silver-vs-silver.** The LLM under-detection finding (strong_F1 = 0.0769 for GPT/DeepSeek vs. 0.3000 for R4 on matched samples) is computed against silver labels. If the silver labels themselves systematically mis-label strong_action_overclaim (which the audit suggests is plausible, given the 75% confusion rate), the under-detection pattern could be partly a label-noise artifact. The consistency across GPT, DeepSeek, and the structured prompt does not rule this out — consistency could reflect shared LLM bias or shared silver-label bias. **The LLM under-detection finding must be interpreted as diagnostic evidence against silver labels, pending independent gold adjudication.**
3. **No gold/human-audited performance is claimed.** A higher-tier confirmatory submission requires 300–500 independently adjudicated claim-evidence pairs, inter-annotator agreement statistics, and significance tests. The author sanity audit is not a substitute for this.

### E. Reviewer Defense and Honest Positioning

We anticipate several reviewer concerns and address them briefly here; a full reviewer defense matrix is provided in `V3_3_reviewer_defense_matrix.csv`.

The most consequential concerns are: (1) silver labels are not gold — addressed by the author sanity audit (§V.D) and explicit bounding of the LLM under-detection finding as "diagnostic evidence, pending independent gold adjudication"; (2) R4 macro-F1 is lower than LLM judges — addressed by §VI.C.3 and the explicit positioning of R4 as a relation-specific complement; (3) LLM prompts may be insufficient — addressed by the structured prompt probe (§V.C.2) and the explicit "under the tested prompts" caveat; (4) the four-class taxonomy may be subjective — addressed by Table 0 examples and the honest reporting of the 75% confusion rate on strong_action in the audit.

We do not claim these defenses are conclusive. They bound the claims and make the limitations explicit. A higher-tier submission requires independent gold adjudication, prompt robustness sweeps, and open-source LLM replication — work that is left to future versions.

### F. Boundary Cases Are Not Noise to Hide (Added in V3.4)

A reviewer might argue that the 25/40 questionable/unclear audit rate means the taxonomy is too subjective to be useful. We disagree, but we state the argument carefully.

Evidence sufficiency calibration is *inherently a boundary task*. The four classes are not disjoint categories with sharp edges — they are regions on a continuous space of claim-evidence strength mismatch. The hardest boundaries (mild-vs-strong, strong-vs-contradiction) are where the taxonomy is most useful *and* most uncertain. A 62.5% questionable/unclear rate on an audit that *deliberately oversampled* strong_action_overclaim (20/40 = 50% of the audit sample, vs. 25% in the balanced set) is not evidence that the taxonomy is broken — it is evidence that the taxonomy surfaces the cases where human judgment is most needed.

The root cause analysis (§V.D) supports this interpretation:
- 12/25 (48%) are *mild_vs_strong_boundary_unclear* — the core taxonomy challenge, expected to be hard.
- 6/25 (24%) are *strong_vs_contradiction_boundary_unclear* — the audit heuristic missed detail-swapping; the decision tree (§III.C) now operationalizes this.
- 5/25 (20%) are *claim_too_abstract* — a claim generation issue, not a taxonomy issue.
- 2/25 (8%) are *audit_heuristic_too_conservative* — the audit was too strict, not the labels too weak.

Only a small fraction of the 25 cases are candidates for *likely label noise*. The majority are genuinely hard boundary cases that any annotation scheme would struggle with. This means:

1. **The aggregate diagnostic pattern (R4 > LLM on strong_action) may hold even if individual labels shift under gold adjudication.** The pattern is computed over 100-200 samples, not on individual cases. If 60% of strong_action labels are stable and 40% shift, the relative ordering of R4 vs. LLM may persist — but this is not guaranteed.

2. **The paper's claims must be limited to aggregate diagnostic patterns, not individual case correctness.** We do not claim that any individual silver label is correct. We claim that the *pattern* (R4 detects more strong_action than LLM under tested prompts) is consistent across models and prompts, on the silver set.

3. **Trusted cases (§V.D, `trusted_case_bank.csv`) are used for paper examples; high-risk cases (`high_risk_sample_bank.csv`) are used for risk disclosure.** The paper does not hide the 25 questionable/unclear cases — it reports them, diagnoses their root causes, and flags them as future gold adjudication priority.

The boundary cases are not noise to hide. They are the cases where evidence sufficiency calibration is hardest and most consequential. Future gold annotation should prioritize these boundary cases, and the decision tree (§III.C) provides a starting operationalization for that work.

## VIII. Limitations

This work is a **diagnostic pilot study**, not a confirmatory benchmark. The limitations below define the boundary of what the current results do and do not support. We state them clearly so that reviewers and future work can judge the scope of the claims.

1. **Silver labels are not gold labels.** The current dataset uses AI-preannotated, author-screened silver labels, not fully adjudicated gold. The author sanity audit (§V.D) flags 25/40 (62.5%) of silver labels as questionable or unclear, with strong_action_overclaim having a 75% confusion rate. All numeric results are exploratory on the silver set. We do not claim gold/human-audited performance, human kappa, or Q1 readiness from silver data alone. The LLM under-detection finding (§VI.C) is computed against these silver labels and must be interpreted as diagnostic evidence, pending independent gold adjudication.

2. **Author sanity audit is preliminary, not independent adjudication.** The audit in §V.D is a qualitative plausibility check by the authors, not independent human annotation with reported inter-annotator agreement. It flags label uncertainty but does not resolve it. Independent gold adjudication (two-annotator + adjudication, with Cohen's κ or Krippendorff's α) is required before the LLM under-detection finding can be treated as established. The root cause analysis (§V.D) shows that the 25 questionable/unclear cases are concentrated at the mild-vs-strong (12 cases) and strong-vs-contradiction (6 cases) boundaries — the two hardest taxonomy boundaries. Future gold annotation should prioritize these boundary cases, using the decision tree (§III.C) as a starting operationalization. The `high_risk_sample_bank.csv` file lists all 25 cases with recommended handling.

3. **LLM results are prompt/model/sample specific.** The GPT-5.5 and DeepSeek-V3 results are single-run, temperature 0, on ≤200 samples, under specific prompts. A different model, prompt, or sample may behave differently. We do not claim that "LLMs cannot solve strong_action_overclaim" — only that under the tested prompts, on the current silver diagnostic set, the pattern is consistent across the two tested models. The structured 5-step decomposition result is a single prompt design; other decompositions (few-shot, chain-of-thought, tool-augmented) are untested and might behave differently.

4. **R4 is not a general-purpose LLM judge replacement.** On matched 100 samples, R4 macro-F1 = 0.3280 vs. GPT-5.5 = 0.5523 (gap 0.22). R4 is a relation-specific diagnostic complement, not a general-purpose classifier. It sacrifices macro-F1 for strong_action recall. We do not claim R4 is better than LLM judges overall — we claim R4 provides targeted value on the strong_action_overclaim relation, at the cost of lower overall macro-F1.

5. **External public datasets only provide generic verification sanity checks.** SciFact and VitaminC use support/refute/NEI labels and do not contain action-overclaim or scope-overclaim labels. External results validate only generic support/refutation transfer and evidence-sensitivity sanity, **not** the SimClaim-specific four-class escalation task. Public data cannot replace SimClaim gold evaluation. R4-compatible underperforms NLI on public data because the strong-action route is inactive by design.

6. **Strong_action remains the main targeted use case.** R4's improvement is concentrated on strong_action_overclaim (+0.1559 strong-F1). The supported/mild boundary remains weak (mild-F1 = 0.1266) and is treated as an open problem, not a solved subtask. R4 is designed for action-overclaim monitoring, not for general four-class classification.

7. **Future work requires independent adjudication.** A higher-tier confirmatory submission requires 300–500 independently adjudicated claim-evidence pairs, inter-annotator agreement statistics (κ/α), paired bootstrap significance tests against stronger external baselines, prompt robustness sweeps, few-shot and open-source LLM replications, and external validation of the four-class taxonomy. The author sanity audit is not a substitute for this. Until this work is completed, the current results should be reported with clear silver-label limitations, without claims of final benchmark readiness, and without claims that R4 outperforms LLM judges overall.

Additional practical limitations: (a) small dataset (444 pairs, ~16 test per seed); (b) single-run LLM comparison with no variance estimate; (c) GPT-5.5 accessed via third-party proxy, not official OpenAI API; (d) R4 over-routes supported → strong (98 false positives) and mild → strong (24 false positives), a trade-off for improved strong recall; (e) cross-domain generalization is not confirmed beyond the six SimClaim domains; (f) LLM judge results are labeled "small-sample pilot, N ≤ 200" and are never merged with SimClaim main results or claimed as gold standard.

**The mild/strong boundary remains the central annotation challenge.** The audit shows 12/25 questionable/unclear cases are mild_vs_strong_boundary_unclear, and strong_action has a 75% confusion rate. The decision tree (§III.C) operationalizes the boundary, but 12 cases remain genuinely ambiguous. This means: (a) the strong_action_overclaim class is the hardest to annotate reliably; (b) any gold annotation effort must invest disproportionate effort in this boundary; (c) the strong_action numeric results (R4 strong-F1 = 0.3967, LLM strong-F1 = 0.0769) should be read as diagnostic evidence on a hard boundary, not as stable benchmark numbers. Future gold annotation should use two annotators with adjudication specifically on mild-vs-strong cases, and report inter-annotator agreement separately for this boundary.

These limitations do not invalidate the framework — they bound the strength of its claims. The contribution is a falsifiable framework and a frozen main method whose numeric claims are constrained by the paper-ready result pack, positioned as a diagnostic complement to LLM judges rather than a competitive replacement. The contribution is a falsifiable framework and a frozen main method whose numeric claims are constrained by the paper-ready result pack, positioned as a diagnostic complement to LLM judges rather than a competitive replacement.

## IX. Conclusion

This revision reframes CESE-OCN as an **evidence sufficiency calibration** framework, rather than a generic claim verification system. The core thesis is that scientific claim verification should not only ask whether evidence is related to a claim, but whether the evidence is *sufficient for the strength of the claim* — in particular when the claim asserts action, deployment, safety, or generalization conclusions.

The frozen R4 conservative strong router provides targeted value for **strong_action_overclaim**: it improves strong-action positive-F1 from 0.2408 to 0.3967 (+0.1559, CI [0.1058, 0.1988], 10/10 seeds positive) on the silver-label pilot set, while preserving contradiction and escalation performance. On matched-sample LLM judge comparisons, under the tested prompts, both GPT-5.5 (standard and structured) and DeepSeek-V3 consistently under-detect strong_action_overclaim (strong_F1 = 0.0769, recall 0.04 = 1/25), while R4 achieves strong_F1 = 0.3000 (absolute gap +0.2231) on the same samples. This structured 5-step decomposition prompt design does not improve strong_action detection, suggesting that this prompt-engineering approach alone does not fix the under-detection pattern under the tested setting.

**R4 is positioned as a complement to black-box LLM judges, not a replacement.** LLM judges retain substantially higher overall macro-F1 (GPT-5.5: 0.5523 vs. R4: 0.3280 on matched 100) and contradiction-F1; R4 targets the specific relation they miss under the tested prompts, at the cost of lower macro-F1. External sanity checks on SciFact and VitaminC show R4-compatible methods run on public data but underperform NLI cross-encoders on generic support/refutation; public data cannot test the four-class evidence-sufficiency taxonomy.

The result is promising but exploratory. The author sanity audit flags 62.5% of silver labels as questionable or unclear, confirming that independent gold adjudication is required before the LLM under-detection finding can be treated as established. The paper should be reported with clear silver-label limitations, without claims of final benchmark readiness, and without claims that R4 outperforms LLM judges overall. The contribution is a falsifiable framework and a frozen main method whose numeric claims are constrained by the paper-ready result pack. R4 provides targeted value for strong_action_overclaim detection and evidence sufficiency calibration — as a complement to LLM judges, not a replacement.

## Appendix A. Language Guardrails

### Safe claims (allowed in the paper):

- "R4 improves strong-action positive-F1 from 0.2408 to 0.3967 while preserving contradiction and escalation performance, on the current silver diagnostic set."
- "Results support a mixed evidence-relation framework rather than a single flat classifier."
- "On silver-label pilot data, the conservative-strong router yields a strong-action positive-F1 delta of +0.1559 (CI [0.1058, 0.1988], 10/10 seeds positive)."
- "Under the tested prompts, generic LLM judges (GPT-5.5, DeepSeek-V3) consistently under-detect strong_action_overclaim on the tested samples, suggesting a consistent under-detection pattern under the tested setting."
- "This structured evidence-sufficiency prompt design did not improve strong_action detection under the tested setting; other prompt designs remain untested."
- "R4 complements black-box LLM judges on the strong_action_overclaim relation, rather than replacing them."
- "R4's macro-F1 is substantially lower than LLM judges (0.3280 vs. 0.5523 on matched 100); R4 is a relation-specific complement, not a general-purpose classifier."
- "Evidence sufficiency rather than generic factuality is the target of this framework."
- "The author sanity audit flags 62.5% of silver labels as questionable or unclear; independent gold adjudication is required."
- "The cost-sensitive variant (cw4.0) provides a small auxiliary improvement (+0.0254) but does not meet the pre-registered replacement threshold."
- "NLI and action-gap features are complementary: combining them improves strong expert F1 over either alone."
- "The mixed framework is positioned as an action-overclaim diagnostic, not a final calibrated benchmark."

### Forbidden claims (must NOT appear in the paper):

- "We solve scientific claim calibration."
- "Our model fully handles strong action overclaims."
- "Our labels are gold / human-audited."
- "Proves LLMs cannot detect strong_action_overclaim."
- "All LLMs are bad at this task."
- "R4 outperforms GPT overall." / "R4全面超过 LLM."
- "R4 is stronger than LLMs on all metrics."
- "GPT can be used as gold label."
- "Cost-sensitive cw4.0 is the new main method."
- "CESE-OCN outperforms strong baselines on a final benchmark."
- "The framework is validated for deployment."
- "All four classes are well-calibrated."
- "supported_vs_mild boundary is resolved."
- "Results are confirmatory (they are exploratory on silver data)."
- "Cross-domain generalization is confirmed."
- "SOTA / state-of-the-art."
- "Fully solved."
- "Systematic blind spot" (use "consistent under-detection pattern under the tested prompts" instead).

### Cautious language (preferred):

- "under the tested prompts"
- "under this tested setting"
- "on the current silver diagnostic set"
- "on the 100 matched samples"
- "single-run, temperature 0, no variance estimate"
- "prompt/model/sample specific"
- "consistent under-detection pattern" (NOT "systematic blind spot")
- "on silver-label pilot data"
- "AI-preannotated, author-screened labels"
- "exploratory pilot validation"
- "not fully adjudicated gold"
- "suggests"
- "supports"
- "is consistent with"
- "does not support"
- "complements black-box LLM judges"
- "evidence sufficiency rather than generic factuality"
- "relation-specific complement"
- "diagnostic, not benchmark"
- "pending independent gold validation"

## References

[1] J. Thorne, A. Vlachos, C. Christodoulopoulos, and A. Mittal. 2018. FEVER: a Large-scale Dataset for Fact Extraction and VERification. NAACL-HLT.

[2] S. R. Bowman, G. Angeli, C. Potts, and C. D. Manning. 2015. A large annotated corpus for learning natural language inference. EMNLP.

[3] A. Wadden et al. 2020. Fact or Fiction: Verifying Scientific Claims. EMNLP.

[4] P. McCullagh. 1980. Regression models for ordinal data. Journal of the Royal Statistical Society: Series B, 42(2):109-142.

[5] F. Samejima. 1969. Estimation of latent ability using a response pattern of graded scores. Psychometrika Monograph Supplement, No. 17.

[6] W. Cao, V. Mirjalili, and S. Raschka. 2020. Rank consistent ordinal regression for neural networks. Pattern Recognition Letters / arXiv:1901.07884.

[7] X. Shi, W. Cao, and S. Raschka. 2021. Deep Neural Networks for Rank-Consistent Ordinal Regression Based on Conditional Probabilities. arXiv:2111.08851.

[8] M. Schlichtkrull et al. 2018. Modeling Relational Data with Graph Convolutional Networks. ESWC.

[9] R. G. Sargent. 2013. Verification and validation of simulation models. Journal of Simulation, 7(1):12-24.

[10] J. Pearl. 2009. Causality: Models, Reasoning, and Inference, 2nd ed. Cambridge University Press.

[11] R. L. Keeney and H. Raiffa. 1976. Decisions with Multiple Objectives: Preferences and Value Tradeoffs. Wiley.

[12] S. Es, J. James, L. Espinosa-Anke, and S. Schockaert. 2024. RAGAs: Automated Evaluation of Retrieval Augmented Generation. EACL Demo.

[13] J. Saad-Falcon, O. Khattab, C. Potts, and M. Zaharia. 2024. ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems. NAACL.

[14] Y. Liu et al. 2023. G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment. EMNLP.

[15] L. Zheng et al. 2023. Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. NeurIPS.

[16] S. S. Stevens. 1946. On the theory of scales of measurement. Science, 103(2684):677-680.

[17] S. Messick. 1995. Validity of psychological assessment. American Psychologist, 50(9):741-749.

[18] K. Krippendorff. 2018. Content Analysis: An Introduction to Its Methodology, 4th ed. SAGE.

[19] J. Cohen. 1960. A coefficient of agreement for nominal scales. Educational and Psychological Measurement, 20(1):37-46.

[20] B. Ellis et al. 2023. SMACv2: An Improved Benchmark for Cooperative Multi-Agent Reinforcement Learning. arXiv.

[21] C. Baillie et al. 2020. CybORG: An Autonomous Cyber Operations Research Gym. arXiv:2002.10667.

[22] J. K. Terry et al. 2021. PettingZoo: Gym for Multi-Agent Reinforcement Learning. NeurIPS.

[23] J. Z. Leibo et al. 2021. Scalable Evaluation of Multi-Agent Reinforcement Learning with Melting Pot. ICML.

[24] DeepSeek-AI. 2024. DeepSeek-V3 Technical Report. arXiv:2412.19437.

[25] K. Hyland. 2005. Metadiscourse: Exploring Interaction in Writing. Continuum.

[26] S. Desai and G. Durrett. 2020. Calibration of Pre-trained Transformers. EMNLP.
