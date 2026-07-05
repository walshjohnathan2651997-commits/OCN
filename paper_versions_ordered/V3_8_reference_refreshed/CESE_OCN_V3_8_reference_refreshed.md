# Evidence Sufficiency Calibration for Scientific Claims: A Mixed Relation-Routing Framework

**Version:** V3.8 (reference refreshed)
**Date:** 2026-07-04
**Changes from V3.7:** Reference refresh pass — added recent 2025–2026 work on scientific claim verification, claim-evidence reasoning, scientific overstatement / evidence-licensed claims, and LLM-as-judge reliability. Citation positions are marked in the Introduction, Related Work, Discussion, and Limitations. No new experiments, no API calls, no new data, no change to numeric results, no change to conclusions.

Author information omitted for review draft

## Abstract

Scientific claim verification is typically framed as deciding whether evidence supports or refutes a claim. We argue this framing is insufficient for scientific writing, where a more frequent failure mode is that evidence is topically relevant but does not justify the *strength* of the claim — particularly when a claim asserts deployment readiness, actionability, safety, or operational conclusions on the basis of limited experimental evidence. We call this task **evidence sufficiency calibration**, formulated as a four-class relation problem: supported, mild_scope_overclaim, strong_action_overclaim, and contradiction_candidate. We present CESE-OCN R4, a mixed relation-routing framework that complements generic LLM/NLI judges via a contradiction detector, a scope-calibration residual classifier, and a conservative strong-action escalation route. On a silver-label pilot of 444 pairs across six domains, R4 improves strong_action positive-F1 from 0.2408 to 0.3967 while preserving contradiction performance. On 200 matched samples, DeepSeek-V3 reaches macro-F1 0.5270 but strong_action-F1 only 0.0769 (recall 0.04). On 100 matched samples, GPT-5.5 standard and structured prompts both yield strong_action-F1 0.0769, while R4 reaches 0.3000 — but with substantially lower overall macro-F1 (0.3280 vs. 0.5523). R4 is positioned as a relation-specific complement, not a replacement. Results are exploratory: labels are silver, not gold; the LLM comparison is prompt/model/sample-specific.

Index Terms — evidence sufficiency, claim calibration, scientific claims, action overclaim, relation-specific routing, LLM-as-judge, natural-language inference, simulation evidence.

## I. Introduction

Scientific claim verification is typically framed as a three-class task: given a claim and evidence, decide whether the evidence *supports* the claim, *refutes* it, or provides *not enough information* (NEI). This framing — established by FEVER [1], SNLI [2], and SciFact [3], and extended by recent scientific claim verification / claim-evidence reasoning benchmarks such as SciClaimHunt and CLAIM-BENCH [27], [28] — is effective for factual correctness, but it is **insufficient** for scientific claim calibration, where the most frequent and consequential failure mode is not outright contradiction but **strength mismatch**: the evidence is topically relevant, directionally consistent, and non-contradictory, yet it does not justify the *strength* of the claim. A benchmark improvement becomes a "deployment-ready system"; a controlled simulated result becomes a "safety guarantee"; a single-domain observation becomes a "generalization claim".

This motivates the **evidence sufficiency calibration** task. Rather than asking only whether evidence supports or refutes a claim, we ask whether the evidence is *sufficient for the strength of the claim* — including its scope, action framing, deployment implications, safety conclusions, and generalization breadth. This framing is aligned with recent work on scientific overstatement, evidence-aligned claim evaluation, and evidence-licensed claims [30], [31]. We formulate this as a four-class relation problem: (i) **supported** — the evidence supports the claim as stated, including its strength; (ii) **mild_scope_overclaim** — the claim mildly over-extends the scope of the evidence, without asserting an action/deployment/safety conclusion; (iii) **strong_action_overclaim** — the claim asserts an action, deployment, safety, policy, generalization, guarantee, or operational conclusion that the evidence does not justify; (iv) **contradiction_candidate** — the evidence contradicts the claim. Class (iii) — strong_action_overclaim — is the most consequential and the hardest to detect, because the evidence is often relevant and the claim is not strictly false; it is simply stronger than the evidence warrants (Figure 2).

A natural hypothesis is that strong LLM judges (GPT-5.5, DeepSeek-V3) should handle this task well, given their broad language understanding. Recent LLM-as-judge work, however, stresses that automatic judges require careful validation against human judgments and may vary substantially by task, domain, prompt, and availability of grounded references [32]–[34]. We test this hypothesis empirically. Under the tested prompts, generic LLM judges are strong on overall support/refutation and contradiction (GPT-5.5 macro-F1 = 0.5523, DeepSeek-V3 macro-F1 = 0.5270 on matched samples), but they **consistently under-detect strong_action_overclaim on the tested samples**: on 100 matched SimClaim samples, both GPT-5.5 with a standard judge prompt and GPT-5.5 with a structured 5-step evidence-sufficiency decomposition prompt achieve strong_action-F1 of only 0.0769 (recall 0.04 = 1/25). DeepSeek-V3 on 200 samples achieves the same strong_action-F1 of 0.0769. The structured prompt design does *not* improve strong_action detection under this single tested prompt setting (Figure 3).

We therefore position CESE-OCN R4 as a **complement** to generic LLM/NLI judges, not a replacement. R4 is a mixed relation-routing framework (Figure 1): a contradiction detector handles the most separable relation first; a scope-calibration residual classifier handles supported vs. mild_scope_overclaim; and a conservative strong-action escalation route targets strong_action_overclaim specifically, under a guarded condition that prevents contradiction cases from being absorbed. On the same 100 matched samples where GPT and DeepSeek achieve strong_action-F1 0.0769, R4 achieves strong_action-F1 0.3000 (absolute gap +0.2231). **R4 is not the strongest model on overall macro-F1 — LLM judges retain that, with GPT-5.5 at 0.5523 vs. R4 at 0.3280 on the matched 100 — but it provides targeted value on the relation that LLM judges miss under the tested prompts.** This positioning as a relation-specific complement, rather than a competitive replacement, is central to the paper's contribution.

This manuscript makes four cautious contributions:

(i) It frames scientific claim calibration as **evidence sufficiency calibration**, a four-class relation task distinguishing strong_action_overclaim from generic support/refutation/NEI, with concrete taxonomy examples (Table 0) and an operational decision tree (Figure 2).

(ii) It constructs a **silver diagnostic set** of 444 claim-evidence pairs across 111 evidence groups and six domains, with AI-preannotated and author-screened labels, and an author sanity audit of 40 silver labels that explicitly flags 25/40 as questionable or unclear.

(iii) It introduces **CESE-OCN R4**, a conservative strong-action router as a mixed relation-routing framework that complements black-box LLM judges, with explicit acknowledgment that R4 sacrifices overall macro-F1 for targeted strong_action recall.

(iv) It reports a **matched-sample LLM judge comparison** (DeepSeek-V3, GPT-5.5 standard, GPT-5.5 structured) showing that under the tested prompts, this structured decomposition design does not improve strong_action detection, while R4 provides complementary value on this relation — bounded by silver-label and single-run limitations.

The remainder of the paper is organized as follows: §II positions the work; §III formulates the task and provides taxonomy examples (Table 0) and the decision tree (Figure 2); §IV describes the CESE-OCN R4 framework (Figure 1); §V describes the data and protocol; §VI reports results (Figure 3, Tables 1-3); §VII discusses implications; §VIII states limitations; §IX concludes. Case studies and detailed tables are in the appendix.

## II. Related Work and Positioning

Generic claim verification and NLI estimate whether evidence supports or contradicts a statement (FEVER [1], SNLI [2], SciFact [3]). Recent scientific claim verification datasets and claim-evidence reasoning benchmarks extend this line to larger scientific-paper settings and full-paper evidence links [27], [28]. Related claim-citation alignment systems also emphasize selective escalation from abstract-level reasoning to passage-level evidence when local evidence is insufficient [29]. These works motivate scientific claim-evidence reasoning but generally do not isolate the particular relation of evidence-to-claim *strength* mismatch.

RAG evaluation and LLM-as-judge frameworks (RAGAs [12], ARES [13], G-Eval [14], MT-Bench [15]) evaluate faithfulness, context relevance, or answer quality for generic factuality, not for the specific failure mode of evidence-claim *strength* mismatch. Recent LLM-as-judge surveys and benchmarks further caution that LLM judges need task-specific validation against human judgments, especially in high-stakes or correctness-sensitive settings [32]–[34]. Hedging detection [25] and NLI calibration [26] are related but do not introduce a strength-calibration taxonomy. CESE-OCN is complementary: it asks whether a scientific claim calibrates its strength to the evidence available, including cases where the claim is topically relevant but over-extends the action implied by the evidence.

The closest recent line to our framing is scientific overstatement and evidence-aligned claim evaluation. RIGOURATE explicitly quantifies scientific exaggeration by aligning paper claims with supporting evidence and predicting overstatement scores [30], while the evidence-licensed claims perspective frames scientific writing as a problem of calibrating assertion rights to available evidence [31]. CESE-OCN differs by operationalizing this idea as a four-class claim-evidence relation taxonomy with a relation-specific router for strong_action_overclaim.

The current results suggest that contradiction, scope shift, and action escalation should not be treated as identical classification errors. Contradiction aligns naturally with NLI-style signals. Mild scope shift remains ambiguous and may require finer annotation. **Strong action overclaim sits between support and contradiction**: the evidence may support a factual finding but not the action, deployment, or generalization asserted by the claim. This is why a single flat four-class classifier under-performs on strong_action_overclaim (baseline strong-F1 0.2408), and why a relation-specific router (R4, strong-F1 0.3967) is needed.

The revised manuscript is a **pilot validation** of an evidence-sufficiency calibration framework with a relation-specific router. It is **not** a final public benchmark, **not** a human-gold evaluation, and **not** a claim that all four classes are solved. All LLM comparison results are labeled as small-sample pilot (N ≤ 200) and are never merged with SimClaim main results or claimed as gold standard.

## III. Task and Problem Formulation

### A. Evidence Sufficiency Calibration Task

Each instance consists of a claim, an evidence span, and a silver candidate label in four relation classes:

- **supported**: the evidence supports the claim as stated, including its strength. This is not "the claim is absolutely true" — it means the evidence is sufficient for the strength of the claim as written.
- **mild_scope_overclaim**: the evidence supports a weaker version of the claim; the claim mildly over-extends the scope (e.g., a single-dataset result is framed as a multi-dataset result), but no action/deployment/safety conclusion is asserted.
- **strong_action_overclaim**: the claim asserts an action, deployment, safety, policy, generalization, guarantee, or operational conclusion that the evidence does not justify. **strong_action_overclaim is not the same as contradiction**: the claim may be directionally consistent with the evidence, but its strength is excessive.
- **contradiction_candidate**: the evidence contradicts the claim; the claim and evidence point in opposite directions on the same metric or conclusion (including detail-swapping of numbers, names, or metrics).

Labels are treated as AI-preannotated development labels (silver), not as gold adjudications.

### B. Taxonomy Decision Tree (Figure 2)

To make the taxonomy operationalizable and reduce the boundary confusion identified in the author sanity audit (§V.D), we introduce a four-step decision tree for label assignment. Figure 2 shows the simplified tree; the full operational version is in `taxonomy_boundary_decision_tree.md`.

```
                       +---------------------------+
                       |   Claim-Evidence Pair     |
                       +-------------+-------------+
                                     |
                                     v
              +----------------------------------------+
              | Step 1: Directional Conflict?         |
              | Does the claim point OPPOSITE to      |
              | evidence on the same metric, number,  |
              | entity, or conclusion?                |
              | (includes detail-swapping)            |
              +-----------------+---------------------+
                          YES   |   NO
                +---------------+   +---------------+
                v                               v
        +----------------+        +-----------------------------+
        | contradiction_ |        | Step 2: Action/Deployment/  |
        | candidate      |        | Safety/Operational Cue?     |
        +----------------+        | (deploy, safety, guarantee, |
                                  | operational, policy, broad   |
                                  | generalization, outperforms, |
                                  | suitable for, theoretically  |
                                  | justified, etc.)             |
                                  +--------------+--------------+
                                          YES    |    NO
                                  +--------------+   +--------------+
                                  v                              v
                       +-------------------------+   +-----------------------+
                       | Step 3: Evidence        |   | Step 4: Scope         |
                       | Sufficient for Action   |   | Over-Extension?       |
                       | Strength?               |   | Does the claim expand |
                       | Is evidence limited to  |   | scope/domain/         |
                       | single benchmark /      |   | population/condition/ |
                       | simulation / lab /      |   | temporal range beyond |
                       | limited metric / single |   | evidence, WITHOUT     |
                       | domain, while claim     |   | action consequences?  |
                       | asserts stronger        |   +-------+---------------+
                       | action conclusion?      |    YES    |    NO
                       +-----------+-------------+   +--------+   +--------+
                              YES   |   NO            v           v
                       +------------+   +----------+ +--------+ +--------+
                       v                v          | mild_   | |        |
                +--------------+  +------------+    | scope_  | | sup-   |
                | strong_      |  | Re-examine |    | over-   | | ported |
                | action_      |  | as sup.    |    | claim   | |        |
                | overclaim    |  | or mild    |    +---------+ +--------+
                +--------------+  +------------+
```

**Figure 2.** Taxonomy decision tree (simplified). Step 1: directional conflict on the same metric/number/entity → `contradiction_candidate` (including detail-swapping). Step 2-3: action/deployment/safety/operational cue present and evidence insufficient for action strength → `strong_action_overclaim`. Step 4: scope over-extension without action consequences → `mild_scope_overclaim`; otherwise → `supported`. The full operational version with cue lists and boundary-case rules is in `taxonomy_boundary_decision_tree.md`.

**Key distinctions operationalized by this tree:**

1. **strong_action_overclaim does not require directional conflict.** The claim may align with evidence direction, but its *strength* (action/deployment/safety assertion) exceeds what the evidence warrants.
2. **contradiction_candidate is about directional conflict** on the same metric/number/entity, including detail-swapping (e.g., evidence says "6 systems", claim says "8 systems").
3. **mild_scope_overclaim is about scope/generalization over-extension** without action/deployment/safety consequences.
4. **supported means evidence is sufficient for the claim's stated strength**, not that the claim is "absolutely true."

The decision tree is a *labeling aid*, not a gold standard. Cases where the tree yields ambiguous results are flagged as boundary cases for future gold adjudication (§V.D, `high_risk_sample_bank.csv`). Table 0 (below) provides 8 illustrative examples (2 per class) from the SimClaim silver set, all traceable to `strict_silver_max_candidates_v1.csv`; full versions are in `table_taxonomy_examples_v3_6_clean.csv`. The V3.6 case integrity audit replaced the V3.5 T2 mild case (TCB_008, number inflation that a reviewer would judge as contradiction) with a clean scope-expansion case (SBV2-ALL92-G170-C02, numbers match exactly, only scope adjective added) — see `case_integrity_audit.csv` for the full audit.

**Table 0. Taxonomy examples (8 cases, 2 per class, silver-label SimClaim).** See `table_taxonomy_examples_v3_6_clean.csv` for full text.

| Class | case_id | candidate_id | domain | claim (short) |
| --- | --- | --- | --- | --- |
| supported | TCB_001 | SBV2-ALL92-G215-C01 | policy_simulation | ABM discussion says decision-support effectiveness remains uncertain because calibration, data integration, and interpretation require expertise. |
| supported | TCB_004 | SBV2-ALL92-G067-C01 | cyber_defense | AgentCyberRange study evaluates six frontier AI systems under matched prompts and budgets. |
| mild_scope_overclaim | TCB_007 | SBV2-ALL92-G002-MILD | autonomous_driving | nuPlan-R adds Success Rate and All-Core Pass Rate metrics to assess planner robustness and performance balance as the main comparison basis. |
| mild_scope_overclaim | TCB_NEW_MILD_2 | SBV2-ALL92-G170-C02 | robotics | In simulation, GRaD-Nav++ reports success rates of 83% on trained tasks and 75% on unseen multi-stage tasks during evaluation. |
| strong_action_overclaim | TCB_009 | SBV2-ALL92-G215-C03 | policy_simulation | ABM discussion says decision-support effectiveness remains uncertain because calibration, data integration, interpretation, and validation require extensive expertise. |
| strong_action_overclaim | TCB_012 | SBV2-ALL92-G107-C03 | digital_twin | Approach jointly calibrates digital twin and searches for optimal control rule, outperforming existing methods in numerical biopharmaceutical experiments and direct physical plant trials. |
| contradiction_candidate | TCB_015 | SBV2-ALL92-G215-C04 | policy_simulation | ABM discussion says decision-support effectiveness is clear because calibration, data integration, and interpretation require little expertise. |
| contradiction_candidate | TCB_018 | SBV2-ALL92-G036-C04 | autonomous_driving | Bench2Drive describes official training data as already available, making method comparisons operate at algorithm level rather than system level. |

### C. Why strong_action_overclaim Is the Core Hard Case

strong_action_overclaim is the most consequential class for scientific claim calibration, because it corresponds to cases where a claim is *actionable* (deployment, policy, safety) but the evidence is *insufficient* for that action. It is also the hardest to detect, because: (1) the evidence is often relevant and non-contradictory; (2) the claim is not strictly false — it over-extends rather than fabricates; (3) generic NLI signals (entailment/contradiction) do not separate "supports a finding" from "supports the action claimed"; (4) under the tested prompts, LLM judges tend to map these cases to supported, mild_scope_overclaim, or contradiction_candidate, missing the action-escalation signal. The primary success criterion for R4 is therefore **strong_action_overclaim positive-F1**, while requiring that flat4 macro-F1, contradiction positive-F1, and escalation macro-F1 are not damaged.

## IV. CESE-OCN R4: A Mixed Relation-Routing Framework

### A. Framework Overview — Why Relation-Specific Routing

The central design principle of R4 is that **different evidence relations require different signals and should not be handled by a single flat classifier**. The pilot results support this: contradiction is comparatively well captured by NLI-style evidence signals (NLI-only strong-F1 = 0.3934), while strong_action_overclaim requires action-aware features that NLI does not provide (action-gap-only strong-F1 = 0.3648; NLI + action-gap = 0.4209). A single flat four-class classifier conflates these signals and under-performs on the most consequential class (baseline strong-F1 = 0.2408).

R4 is therefore designed as a **relation-specific diagnostic routing framework**, not a threshold-tuned heuristic. The routing order reflects a theoretical principle: handle the most separable relation first (contradiction), then the most consequential relation under a conservative guard (strong_action), then the residual scope calibration (supported vs. mild). Thresholds are frozen operationalizations of this principle, selected on train/dev under pre-specified constraints (§IV.D) and then frozen. R4 is explicitly a **complement** to generic LLM/NLI judges, not a replacement — it is optimized to reduce under-detection of action/deployment overclaims while preserving contradiction performance, accepting a lower macro-F1 in exchange for higher strong_action recall.

### B. Routing Flow (Figure 1)

```
                    +-------------------------------+
                    |     Claim-Evidence Pair       |
                    +---------------+---------------+
                                    |
                                    v
              +-----------------------------------------+
              |  NLI relation features                  |
              |  + scope / action / deployment cues     |
              +-----------------------------------------+
                                    |
              +------------+--------+--------+------------+
              |                     |                    |
              v                     v                    v
         p_contra              p_strong               p_svm
       (contradiction)      (strong-action)       (supported/mild)
              |                     |                    |
              v                     v                    v
    +----------------+    +--------------------+    +---------------+
    | Route 1:       |    | Route 2:           |    | Route 3:      |
    | if p_contra    |    | if p_strong>=t_str |    | if p_svm>=tvm |
    |   >= t_contra  |    | AND p_contra<t_low |    |   supported   |
    |   -> contra    |    |   -> strong_action |    | else          |
    |                |    |                    |    |   mild_scope  |
    +-------+--------+    +---------+----------+    +-------+-------+
            |                       |                      |
            +------+-------+--------+------+-------+-------+
                   |       |        |      |
                   v       v        v      v
              +-------------------------------------+
              |              Final Label            |
              +-------------------------------------+
```

| Route | Order | Decision | Threshold (mean, 10 seeds) | Rationale |
| --- | --- | --- | --- | --- |
| Route 1 — Contradiction | 1st | if `p_contra >= t_contra` → `contradiction_candidate` | `t_contra = 0.48` | Most separable; handling first prevents absorption into strong_action or mild. |
| Route 2 — Strong-action escalation | 2nd | if `p_strong >= t_strong` AND `p_contra < t_low` → `strong_action_overclaim` | `t_strong = 0.535`, `t_low` = lower guard | Most consequential; action-gap + NLI features. Conservative guard prevents contradiction absorption. |
| Route 3 — Scope residual | 3rd | if `p_svm >= t_svm` → `supported`; else → `mild_scope_overclaim` | `t_svm = 0.51` | Least separable boundary (mild-F1 = 0.1266). SVM residual handles it last. |

**Figure 1.** R4 routing flow. The router applies three routes in order: contradiction first (the most separable relation), then strong-action escalation under a conservative contradiction guard (to prevent contradiction cases from being absorbed into strong_action), then a supported/mild residual classifier. Frozen mean thresholds: `t_contra = 0.48`, `t_strong = 0.535`, `t_svm = 0.51`, `t_low` = lower contradiction guard.

### C. Why This Order — Theoretical Motivation

**Route 1 (Contradiction first).** Contradiction is the strongest and most separable relation in the pilot data. NLI-style signals capture it well. Handling contradiction first prevents downstream routes from absorbing contradiction cases into strong_action or mild.

**Route 2 (Strong-action escalation under a conservative guard).** strong_action_overclaim is the most consequential relation but the hardest to detect. The strong-action expert uses action-gap features (the gap between the action implied by the claim and the action supported by the evidence) in addition to NLI signals. The conservative guard (`p_contra < t_low`) prevents contradiction cases from being absorbed into strong_action — critical because strong_action and contradiction can look similar to a strong-action expert.

**Route 3 (Scope-calibration residual).** Supported vs. mild_scope_overclaim is the residual scope-calibration problem, handled last because it is the least separable boundary (supported-F1 = 0.4424, mild-F1 = 0.1266 — the weakest boundary in the taxonomy). An SVM residual classifier handles this, acknowledging that the supported/mild boundary remains an open problem.

### D. R4 Is Intentionally Conservative

R4 is **not** optimized to maximize overall macro-F1, but to reduce under-detection of action/deployment overclaims while preserving contradiction performance. R4 accepts a lower macro-F1 than a flat classifier or LLM judge (R4 macro-F1 = 0.4238 on 444 samples, 0.3280 on matched 100; GPT-5.5 = 0.5523 on matched 100). R4 accepts supported/mild → strong false positives (98 supported → strong, 24 mild → strong) in exchange for higher strong recall (0.4562 vs. baseline 0.2062). R4 is selected against 5 router variants under 5 pre-specified constraints: strong_positive_delta ≥ +0.05, flat4_macro_delta ≥ -0.02, contradiction_positive_delta ≥ -0.03, escalation_macro_delta ≥ -0.03, positive_delta_seed_count ≥ 7. R4 is the only router meeting all 5 constraints simultaneously. This conservative design is the right trade-off for a **diagnostic complement** to LLM judges: R4 flags potential action overclaims that LLM judges miss, accepting false positives that a human reviewer (or an LLM judge on a second pass) can filter. A cost-sensitive variant (cw4.0) gives a small additional improvement (+0.0254 strong-F1) but does not meet the replacement threshold (+0.03) and is retained only as an auxiliary sensitivity analysis.

## V. Data and Experimental Protocol

### A. SimClaim Silver-Label Pilot Set

The current study uses a paper-only strict silver set containing 444 claim-evidence pairs, 111 evidence groups, six domains (policy_simulation, marl, digital_twin, robotics, autonomous_driving, cyber_defense), and balanced four-way silver labels (111 per class). These labels are AI-preannotated and author-screened; they should not be described as human-gold. All experiments use group-aware splits so that claims derived from the same evidence group do not cross train/dev/test boundaries. Router thresholds and hyperparameters are selected on train/dev only. The reported R4 result is frozen in `D:\ocn\experiments\mixed_framework_v2_frozen_r4_baseline` and is the current main baseline for this manuscript version.

### B. LLM Judge Comparison Protocol

For the LLM judge comparison, we use two matched-sample subsets:

- **DeepSeek-V3 baseline (200 samples)**: a label-balanced 200-sample subset (50 per class). DeepSeek-V3 is queried via the OpenAI-compatible DeepSeek API (model: `deepseek-chat`), temperature 0, single run. Output is parsed into the same four-class label space. Results are labeled "small-sample pilot, N ≤ 200" and are never merged with SimClaim main results.
- **GPT-5.5 standard vs. structured (100 samples)**: a label-balanced 100-sample subset (25 per class), selected to overlap with the DeepSeek 200-sample set and to cover all six domains. GPT-5.5 is queried via a third-party proxy (temperature 0, single run). Two prompt strategies are compared: **Standard** (a direct judge prompt asking for a four-class label) and **Structured** (a 5-step evidence-sufficiency decomposition prompt that explicitly asks the model to check factual alignment, scope expansion, action/deployment claims, evidence sufficiency, and a final label).

R4 predictions on the same 100/200 samples are computed for matched-sample comparison. The LLM comparison is **single-run, temperature 0, no variance estimate** — an explicit limitation (§VIII).

### C. External Public Dataset Sanity Check

To test whether the evidence-relation approach transfers to public claim-verification data, we run a small gold-derived subset evaluation on **SciFact** [3] and **VitaminC** (dev/test). Public gold labels are preserved as original (SUPPORT / CONTRADICT-REFUTES / NEI), with a conservative derived mapping (SUPPORT → supported, CONTRADICT/REFUTES → contradiction_candidate, NEI → unsupported_or_insufficient). **No mapping to strong/mild labels is performed**, because public datasets do not contain the action-overclaim taxonomy. We evaluate four methods: TF-IDF claim+evidence, TF-IDF claim-only (leakage probe), NLI cross-encoder (`cross-encoder/nli-deberta-base`), and an R4-compatible heuristic. Five seeds are used, with ≤300 eval samples per dataset. This is a **sanity check** for generic support/refutation transfer; it cannot replace SimClaim gold evaluation.

### D. Author Sanity Audit of Silver Labels

To check whether the silver labels are prima facie plausible, we conducted a small author sanity audit of 40 silver labels. **This audit is not a substitute for independent human adjudication.** It is a qualitative sanity check by the authors to flag labels that may be questionable or unclear before independent gold validation.

**Audit protocol:** We sampled 40 cases from the 444-row silver set, oversampling strong_action_overclaim (20 cases) since it is the central class, plus 7 supported, 7 mild_scope_overclaim, and 6 contradiction_candidate. For each case, the authors assigned `author_sanity_decision` (reasonable / questionable / unclear) and `possible_confusion` (none / supported_vs_mild / mild_vs_strong / strong_vs_contradiction).

**Audit results:** 15 reasonable, 5 questionable, 20 unclear (25/40 = 62.5% flagged). strong_action_overclaim has the highest confusion rate (15/20 = 75%), mostly mild_vs_strong confusion. All 6 contradiction_candidate cases are flagged unclear, mostly strong_vs_contradiction confusion (detail-swapping missed by the audit heuristic). supported is the most stable class (7/7 reasonable).

**Root cause distribution of the 25 questionable/unclear cases:**

- mild_vs_strong_boundary_unclear: 12 cases (48%) — the core taxonomy challenge.
- strong_vs_contradiction_boundary_unclear: 6 cases (24%) — the audit heuristic missed detail-swapping; the decision tree (Figure 2, Step 1) now operationalizes detail-swapping as contradiction.
- claim_too_abstract: 5 cases (20%) — a claim generation issue, not a taxonomy issue.
- audit_heuristic_too_conservative: 2 cases (8%) — the audit was too strict, not the labels too weak.

**Interpretation:** This audit confirms that the silver labels are not ready to be treated as gold. The 25 questionable/unclear cases are concentrated at the two hardest taxonomy boundaries (mild-vs-strong and strong-vs-contradiction), which is expected for an evidence-sufficiency task. The LLM under-detection finding (§VI.C) is computed against these silver labels, and the high questionable/unclear rate means the finding must be interpreted as **diagnostic evidence against silver labels, pending independent gold adjudication** — not as an established property of LLM judges. The audit does not invalidate the framework (the relative pattern — R4 > LLM on strong_action — may hold under gold), but it bounds the strength of the claim. The 25 questionable/unclear cases are retained in `high_risk_sample_bank.csv` as boundary cases for future gold adjudication priority; `trusted_case_bank.csv` (18 cases, ≥4 per class) provides clear illustrative cases for paper examples — none of which are claimed as gold. The full audit is in `author_sanity_audit_40.csv`.

### E. Exploratory Framing

Because the dataset is small, silver-labeled, and the author sanity audit flags substantial label uncertainty, all results are framed as **exploratory pilot validation**. A higher-tier confirmatory submission would require 300–500 independently adjudicated claim-evidence pairs, inter-annotator agreement statistics, significance tests against stronger external baselines, and external validation.

## VI. Results

### A. Internal Silver Diagnostic Results (Table 1)

The strongest supported result is that R4 improves strong-action positive-F1 while preserving contradiction and escalation. Table 1 reports the main comparison among the flat baseline, frozen R4 router, and the auxiliary cost-sensitive variant. Per-class F1 and the router-selection table (R4 vs. R1/R2/R3/R5) are in `V3_1_result_tables.csv`; the bootstrap confidence interval for the strong-positive delta is [0.1058, 0.1988], positive in 10/10 random seeds.

**Table 1. Internal R4 targeted result (silver-label pilot, 444 claims, 10 seeds).** See `table_main_results_clean.csv`.

| Method | Strong F1 | Strong Recall | Contra F1 | Flat4 F1 | Use |
| --- | --- | --- | --- | --- | --- |
| baseline_flat4 | 0.2408 | 0.2062 | 0.7308 | 0.3963 | baseline |
| **R4_conservative_strong_router (MAIN)** | **0.3967** | **0.4562** | **0.7296** | **0.4238** | **main_method** |
| B_cost_sensitive_cw4.0 (AUX) | 0.4221 | 0.4625 | 0.7296 | 0.4365 | auxiliary |

- R4 is the frozen main method (immutable). The cost-sensitive variant is auxiliary (delta vs R4 = +0.0254, below the +0.03 threshold, CI crosses zero).
- The key improvement is in **strong_action_overclaim** (+0.1559 strong-F1 over baseline), with contradiction preserved (-0.0012, well within the -0.03 constraint).
- R4 over-routes supported → strong (98 false positives) and mild → strong (24 false positives) — a trade-off for improved strong recall. This is a LIMITATION, not a feature: R4 improves strong recall at the cost of supported/mild → strong false positives.

### B. LLM Judge Comparison (Table 2, Figure 3)

This is the central new analysis. We compare R4 against generic LLM judges on matched SimClaim samples.

**Table 2. LLM judge comparison on matched SimClaim samples (Group C).** See `table_main_results_clean.csv`.

| Method | N | Macro-F1 | Strong F1 | Strong Recall | Contra F1 |
| --- | --- | --- | --- | --- | --- |
| GPT-5.5 standard | 100 | 0.5523 | 0.0769 | 0.04 | 0.6857 |
| GPT-5.5 structured (5-step) | 100 | 0.5543 | 0.0769 | 0.04 | 0.6857 |
| DeepSeek-V3 (matched 100) | 100 | 0.5248 | 0.0769 | 0.04 | 0.8317 |
| DeepSeek-V3 (full 200) | 200 | 0.5270 | 0.0769 | 0.04 | 0.8317 |
| R4 (matched 100) | 100 | 0.3280 | 0.3000 | — | — |
| R4 (full 200) | 200 | — | 0.3158 | — | — |

**Overall Macro-F1 (higher is better):**

```
GPT-5.5 structured  | ████████████████████████████████████████████████  0.5543
GPT-5.5 standard    | ████████████████████████████████████████████████  0.5523
DeepSeek-V3 (200)   | ██████████████████████████████████████████████   0.5270
DeepSeek-V3 (100)   | ██████████████████████████████████████████████   0.5248
R4 (matched 100)    | ██████████████████████████████                   0.3280
                    +------+------+------+------+------+------+------+--+
                    0.0   0.1   0.2   0.3   0.4   0.5   0.6   0.7
```

**Strong-Action F1 (higher is better):**

```
R4 (matched 200)    | ████████████████████████████                     0.3158
R4 (matched 100)    | ███████████████████████████                      0.3000
GPT-5.5 structured  | █                                                 0.0769
GPT-5.5 standard    | █                                                 0.0769
DeepSeek-V3 (200)   | █                                                 0.0769
DeepSeek-V3 (100)   | █                                                 0.0769
                    +------+------+------+------+------+------+------+--+
                    0.0   0.1   0.2   0.3   0.4   0.5   0.6   0.7
```

**Figure 3.** LLM vs. R4 strong_action gap on matched SimClaim samples. LLMs (GPT-5.5 standard, GPT-5.5 structured, DeepSeek-V3) all converge on strong_action-F1 = 0.0769 (recall 0.04 = 1/25). R4 reaches strong_F1 = 0.3000 on the matched 100 and 0.3158 on the matched 200. LLMs retain substantially higher overall macro-F1 (0.5248-0.5543 vs. R4 0.3280). Interpretation: **LLMs are stronger overall, but R4 targets the strong_action gap.**

**Key findings:**

1. **Both GPT-5.5 standard and structured achieve strong_action-F1 of 0.0769 (recall 0.04 = 1/25).** This structured 5-step evidence-sufficiency decomposition prompt design **did not improve** strong_action detection under the tested setting. The structured prompt does not hurt macro-F1 (0.5543 vs. 0.5523) or contradiction-F1 (both 0.6857), but it does not improve strong_action either. GPT only flagged 7/100 samples as containing an action/deployment/safety claim in structured mode, despite 25/100 being strong_action_overclaim by silver label.
2. **DeepSeek-V3 on 200 samples also achieves strong_action-F1 0.0769** (precision 1.0, recall 0.04 = 1/25), while reaching macro-F1 0.5270 and contradiction-F1 0.8317 — strong overall, missing strong_action.
3. **R4 provides targeted complementary value.** On the same 100 samples where GPT and DeepSeek achieve strong_F1 0.0769, R4 achieves strong_F1 0.3000 (absolute gap +0.2231). On the 200-sample set, R4 achieves strong_F1 0.3158 (absolute gap +0.2389 over DeepSeek). R4 is not stronger overall — LLM judges retain substantially higher macro-F1 (0.5523 vs. 0.3280) and contradiction-F1 — but it targets the specific relation that LLM judges miss under the tested prompts.
4. **The dominant LLM error modes on strong_action_overclaim** are over-contradiction (mapping strong_action to contradiction_candidate — the LLM treats the action over-extension as a factual mismatch), over-milding (mapping strong_action to mild_scope_overclaim — the LLM recognizes scope expansion but misses the action escalation), and over-supporting (mapping strong_action to supported — the LLM treats the relevant-but-insufficient evidence as full support). R4's error mode is different: it tends to over-route supported → strong, producing false positives rather than false negatives on strong_action. This is a complementary error profile.

**This result should not be interpreted as R4 outperforming LLM judges overall.** R4's macro-F1 (0.3280) is substantially lower than GPT-5.5 (0.5523) and DeepSeek-V3 (0.5248) on the same 100 matched samples. R4's value is relation-specific: it targets the strong_action_overclaim relation that LLM judges miss under the tested prompts. We do not claim R4 is better than LLM judges overall — we claim R4 provides targeted value on strong_action_overclaim, at the cost of lower overall macro-F1.

### C. Boundary Audit Summary (Table 3)

**Table 3. Boundary audit summary (40-case author sanity audit, §V.D).** See `table_main_results_clean.csv`.

| Silver label | Reasonable | Questionable | Unclear | Total | Confusion type |
| --- | --- | --- | --- | --- | --- |
| supported | 7 | 0 | 0 | 7 | none |
| mild_scope_overclaim | 3 | 0 | 4 | 7 | mild_vs_strong |
| strong_action_overclaim | 5 | 5 | 10 | 20 | mild_vs_strong |
| contradiction_candidate | 0 | 0 | 6 | 6 | strong_vs_contradiction |
| **Total** | **15** | **5** | **20** | **40** | — |

**Root causes (25 questionable/unclear cases):**

| Root cause | Cases | % | Implication |
| --- | --- | --- | --- |
| mild_vs_strong_boundary_unclear | 12 | 48% | core taxonomy challenge; needs gold adjudication |
| strong_vs_contradiction_boundary_unclear | 6 | 24% | audit missed detail-swapping; decision tree fixes this |
| claim_too_abstract | 5 | 20% | claim generation issue, not taxonomy issue |
| audit_heuristic_too_conservative | 2 | 8% | audit too strict; silver label likely defensible |

- 25/40 (62.5%) of silver labels are flagged as questionable or unclear — a real signal that silver labels require independent gold validation before the LLM blind spot finding can be treated as established.
- The 25 cases are *not* all label noise — they reflect a mix of taxonomy boundary issues, audit heuristic limitations, and genuinely hard cases.
- strong_action_overclaim has the highest confusion rate (15/20 = 75%), mostly mild_vs_strong confusion. This is expected: strong_action is the most subtle class, and the boundary between mild and strong is the hardest to operationalize.
- The 25 questionable/unclear cases are retained in `high_risk_sample_bank.csv` as boundary cases for future gold adjudication priority; `trusted_case_bank.csv` (18 cases, ≥4 per class) provides clear illustrative cases for paper examples — none claimed as gold.

### D. External Public Dataset Sanity Check

We run a small gold-derived subset evaluation on SciFact and VitaminC. **Public gold labels are preserved as original; the mapping to supported/contradiction_candidate/unsupported_or_insufficient is derived and does not map to strong/mild labels.**

| Dataset | Method | E1 Macro-F1 | E2 Macro-F1 |
| --- | --- | --- | --- |
| SciFact | TF-IDF claim+evidence | 0.3350 | 0.5111 |
| SciFact | NLI cross-encoder | **0.6895** | 0.6034 |
| SciFact | R4-compatible | 0.3549 | 0.5166 |
| VitaminC | TF-IDF claim+evidence | 0.4277 | 0.5184 |
| VitaminC | NLI cross-encoder | **0.6686** | 0.5691 |
| VitaminC | R4-compatible | 0.4568 | 0.5197 |

- SciFact best E1 macro-F1: 0.6895 (NLI cross-encoder, N=271 per seed). VitaminC best E1: 0.6686 (NLI cross-encoder, N=300 per seed).
- R4-compatible underperforms NLI on public data because (a) public datasets have no action-overclaim labels, so the strong-action route is inactive and R4 reduces to its contradiction + scope components; (b) R4 was not retrained on public data. The external check validates that the contradiction + scope components run without crash on public data, **not** that the full R4 framework transfers competitively.
- Claim-only leakage is HIGH: claim-only TF-IDF is within 0.018-0.030 of claim+evidence TF-IDF, indicating that public data rewards claim-only shortcuts.
- Evidence sensitivity (E3) on VitaminC official contrastive pairs (300 per seed): support-score delta = 0.0226 ± 0.007, sensitivity rate 46.9%. On SciFact synthetic perturbation (209 per seed): delta = 0.0056 ± 0.014, sensitivity rate 45.5% (near zero, as expected for synthetic perturbations).

**What this external check does and does not show:**

- ✅ R4-compatible methods run on public data without crash (contradiction + scope components transfer).
- ✅ NLI cross-encoder is a strong generic support/refutation baseline on public data.
- ❌ Public datasets **cannot** test the four-class evidence-sufficiency taxonomy (no action-overclaim labels).
- ❌ Public datasets **cannot** replace SimClaim gold evaluation.
- ❌ Public results are **sanity checks**, not benchmark superiority claims.

## VII. Discussion

### A. What R4 Adds Despite Lower Macro-F1

A natural objection to the under-detection finding is: "LLMs have higher macro-F1, so they are better overall." This objection is correct — LLM judges **are** better overall (GPT-5.5 macro-F1 = 0.5523 vs. R4 = 0.3280 on matched 100 samples, a 0.22 gap). We do not dispute this. The point is that macro-F1 averages over four classes, three of which (supported, mild_scope_overclaim, contradiction_candidate) are well-handled by LLM judges. The fourth class — strong_action_overclaim — is the most consequential for scientific claim calibration, because it corresponds to cases where a claim is *actionable* but the evidence is *insufficient* for that action. A model that misses strong_action_overclaim fails on cases that are consequential for scientific writing quality, even if its overall macro-F1 is high.

R4's value is **relation-specific**: it targets the strong_action_overclaim relation that LLM judges miss under the tested prompts. This is a complementary positioning, not a competitive one. A combined system — LLM judge for supported/mild/contradiction, R4 for strong_action — could potentially exploit this complementarity, though we leave that to future work. Whether the macro-F1 gap is an acceptable trade-off depends on the downstream use case — for action-overclaim monitoring where missing a strong_action case is costly, the trade-off may be favorable; for generic claim verification, an LLM judge alone is preferable.

### B. Why strong_action Is Difficult for LLM Judges

Action-overclaim is the core hard case because it sits between support and contradiction. The evidence is relevant and non-contradictory, but it does not justify the action, deployment, safety, or generalization asserted by the claim. Generic NLI signals do not separate "supports a finding" from "supports the action claimed", because both are entailment-like at the factual level. LLM judges, trained on generic factuality, tend to map these cases to supported, mild_scope_overclaim, or contradiction_candidate — all of which miss the action-escalation signal.

The pattern is consistent across the two tested models. Both GPT-5.5 and DeepSeek-V3 converge on strong_F1 = 0.0769 (recall = 0.04 = 1/25), and this structured 5-step decomposition prompt design does not change this. This suggests a consistent under-detection pattern under the tested prompts, not a single-model quirk. We do not claim this is a fundamental limit of LLMs — it is prompt/model/sample specific and computed against silver labels (which the author sanity audit flags as 62.5% questionable/unclear) — but under the tested prompts, the pattern is consistent across the two tested models and suggests that a relation-specific router can complement black-box LLM judges. R4's design directly addresses this: the strong-action escalation route uses action-gap features (the gap between the action implied by the claim and the action supported by the evidence) in addition to NLI signals. The ablation confirms that NLI and action-gap features are complementary: combining them improves strong expert F1 over either alone (0.4209 vs. 0.3934 NLI-only, 0.3648 action-gap-only). Other prompt designs (few-shot, chain-of-thought, tool-augmented) remain untested and might behave differently. Independent gold validation is required before this pattern can be treated as established.

### C. Boundary Cases Are Part of Evidence Sufficiency

A reviewer might argue that the 25/40 questionable/unclear audit rate means the taxonomy is too subjective to be useful. We disagree, but we state the argument carefully.

Evidence sufficiency calibration is *inherently a boundary task*. The four classes are not disjoint categories with sharp edges — they are regions on a continuous space of claim-evidence strength mismatch. The hardest boundaries (mild-vs-strong, strong-vs-contradiction) are where the taxonomy is most useful *and* most uncertain. A 62.5% questionable/unclear rate on an audit that *deliberately oversampled* strong_action_overclaim (20/40 = 50% of the audit sample, vs. 25% in the balanced set) is not evidence that the taxonomy is broken — it is evidence that the taxonomy surfaces the cases where human judgment is most needed.

The root cause analysis supports this interpretation: 12/25 (48%) are mild_vs_strong_boundary_unclear (the core taxonomy challenge, expected to be hard); 6/25 (24%) are strong_vs_contradiction_boundary_unclear (the audit heuristic missed detail-swapping; the decision tree now operationalizes this); 5/25 (20%) are claim_too_abstract (a claim generation issue, not a taxonomy issue); 2/25 (8%) are audit_heuristic_too_conservative (the audit was too strict, not the labels too weak). Only a small fraction are candidates for *likely label noise*. The majority are genuinely hard boundary cases that any annotation scheme would struggle with. This means: (1) the aggregate diagnostic pattern (R4 > LLM on strong_action) may hold even if individual labels shift under gold adjudication — but this is not guaranteed; (2) the paper's claims are limited to aggregate diagnostic patterns, not individual case correctness; (3) trusted cases (`trusted_case_bank.csv`) are used for paper examples; high-risk cases (`high_risk_sample_bank.csv`) are used for risk disclosure. The paper does not hide the 25 questionable/unclear cases — it reports them, diagnoses their root causes, and flags them as future gold adjudication priority.

### D. What Remains Unresolved

The most consequential unresolved issue is **independent gold adjudication**. All 444 SimClaim labels are still silver. The V3.5 root cause analysis shows that 12/25 questionable/unclear cases are *genuinely hard boundary cases* (mild_vs_strong), which means even independent annotators may disagree on these cases. The decision tree (Figure 2) operationalizes the boundary but does not resolve it — 12 cases remain ambiguous even with the decision tree. If gold adjudication reveals that the mild/strong boundary is not reliably drawable (κ < 0.4 on this boundary), the strong_action_overclaim class itself may need to be merged with mild, which would weaken the paper's central contribution.

The decision tree is a *labeling aid*, not a validated annotation scheme. It has not been tested against gold labels (because no gold labels exist). It may misclassify cases that the decision tree's steps yield ambiguous results for, over-operationalize boundaries that are actually more nuanced, or introduce new biases (e.g., treating all detail-swapping as contradiction, when some detail-swapping may be mild or strong). The 18 trusted illustrative cases are *not* gold — "reasonable" by author audit is not the same as "correct" by independent adjudication. A small fraction of questionable/unclear cases (5/25) are `claim_too_abstract`, indicating that the claim generation process sometimes produces claims too abstract to clearly map to the taxonomy. These are claim generation problems, not taxonomy problems, but they affect label quality. Until gold adjudication, decision-tree validation, prompt robustness sweeps, and open-source LLM replications are completed, the current results should be reported with clear silver-label limitations, without claims of final benchmark readiness, and without claims that R4 outperforms LLM judges overall.

## VIII. Limitations

This work is a **diagnostic pilot study**, not a confirmatory benchmark. The limitations below define the boundary of what the current results do and do not support.

1. **Silver labels are not gold labels.** The current dataset uses AI-preannotated, author-screened silver labels, not fully adjudicated gold. The author sanity audit (§V.D) flags 25/40 (62.5%) of silver labels as questionable or unclear, with strong_action_overclaim having a 75% confusion rate. All numeric results are exploratory on the silver set. We do not claim gold/human-audited performance, human kappa, or Q1 readiness from silver data alone. The LLM under-detection finding (§VI.B) is computed against these silver labels and must be interpreted as diagnostic evidence, pending independent gold adjudication.

2. **Author sanity audit is preliminary, not independent adjudication.** The audit in §V.D is a qualitative plausibility check by the authors, not independent human annotation with reported inter-annotator agreement. It flags label uncertainty but does not resolve it. Independent gold adjudication (two-annotator + adjudication, with Cohen's κ or Krippendorff's α) is required before the LLM under-detection finding can be treated as established. Future gold annotation should prioritize the boundary cases in `high_risk_sample_bank.csv`, using the decision tree (Figure 2) as a starting operationalization.

3. **LLM results are prompt/model/sample specific.** The GPT-5.5 and DeepSeek-V3 results are single-run, temperature 0, on ≤200 samples, under specific prompts. A different model, prompt, or sample may behave differently. We do not claim that "LLMs cannot solve strong_action_overclaim" — only that under the tested prompts, on the current silver diagnostic set, the pattern is consistent across the two tested models. The structured 5-step decomposition result is a single prompt design; other decompositions (few-shot, chain-of-thought, tool-augmented) are untested and might behave differently.

4. **R4 is not a general-purpose LLM judge replacement.** On matched 100 samples, R4 macro-F1 = 0.3280 vs. GPT-5.5 = 0.5523 (gap 0.22). R4 is a relation-specific diagnostic complement, not a general-purpose classifier. It sacrifices macro-F1 for strong_action recall. We do not claim R4 is better than LLM judges overall — we claim R4 provides targeted value on the strong_action_overclaim relation, at the cost of lower overall macro-F1. R4 over-routes supported → strong (98 false positives) and mild → strong (24 false positives), a trade-off for improved strong recall.

5. **Taxonomy boundary remains challenging.** The mild/strong boundary remains the central annotation challenge. The audit shows 12/25 questionable/unclear cases are mild_vs_strong_boundary_unclear, and strong_action has a 75% confusion rate. The decision tree (Figure 2) operationalizes the boundary, but 12 cases remain genuinely ambiguous. The strong_action numeric results (R4 strong-F1 = 0.3967, LLM strong-F1 = 0.0769) should be read as diagnostic evidence on a hard boundary, not as stable benchmark numbers. Future gold annotation should use two annotators with adjudication specifically on mild-vs-strong cases, and report inter-annotator agreement separately for this boundary.

6. **External datasets do not validate the four-class taxonomy.** SciFact and VitaminC use support/refute/NEI labels and do not contain action-overclaim or scope-overclaim labels. External results validate only generic support/refutation transfer and evidence-sensitivity sanity, **not** the SimClaim-specific four-class escalation task. Public data cannot replace SimClaim gold evaluation. R4-compatible underperforms NLI on public data because the strong-action route is inactive by design.

Additional practical limitations: (a) small dataset (444 pairs, ~16 test per seed); (b) single-run LLM comparison with no variance estimate; (c) GPT-5.5 accessed via third-party proxy, not official OpenAI API; (d) cross-domain generalization is not confirmed beyond the six SimClaim domains; (e) LLM judge results are labeled "small-sample pilot, N ≤ 200" and are never merged with SimClaim main results or claimed as gold standard.

These limitations do not invalidate the framework — they bound the strength of its claims. The contribution is a falsifiable framework and a frozen main method whose numeric claims are constrained by the paper-ready result pack, positioned as a diagnostic complement to LLM judges rather than a competitive replacement.

## IX. Conclusion

This revision reframes CESE-OCN as an **evidence sufficiency calibration** framework, rather than a generic claim verification system. The core thesis is that scientific claim verification should not only ask whether evidence is related to a claim, but whether the evidence is *sufficient for the strength of the claim* — in particular when the claim asserts action, deployment, safety, or generalization conclusions.

The frozen R4 conservative strong router provides targeted value for **strong_action_overclaim**: it improves strong-action positive-F1 from 0.2408 to 0.3967 (+0.1559, CI [0.1058, 0.1988], 10/10 seeds positive) on the silver-label pilot set, while preserving contradiction and escalation performance. On matched-sample LLM judge comparisons, under the tested prompts, both GPT-5.5 (standard and structured) and DeepSeek-V3 consistently under-detect strong_action_overclaim (strong_F1 = 0.0769, recall 0.04 = 1/25), while R4 achieves strong_F1 = 0.3000 (absolute gap +0.2231) on the same samples. This structured 5-step decomposition prompt design does not improve strong_action detection, suggesting that this prompt-engineering approach alone does not fix the under-detection pattern under the tested setting.

**R4 is positioned as a complement to black-box LLM judges, not a replacement.** LLM judges retain substantially higher overall macro-F1 (GPT-5.5: 0.5523 vs. R4: 0.3280 on matched 100) and contradiction-F1; R4 targets the specific relation they miss under the tested prompts, at the cost of lower macro-F1. External sanity checks on SciFact and VitaminC show R4-compatible methods run on public data but underperform NLI cross-encoders on generic support/refutation; public data cannot test the four-class evidence-sufficiency taxonomy.

The result is promising but exploratory. The author sanity audit flags 62.5% of silver labels as questionable or unclear, confirming that independent gold adjudication is required before the LLM under-detection finding can be treated as established. The paper should be reported with clear silver-label limitations, without claims of final benchmark readiness, and without claims that R4 outperforms LLM judges overall. R4 provides targeted value for strong_action_overclaim detection and evidence sufficiency calibration — as a complement to LLM judges, not a replacement.

## Appendix A. Case Studies

See `appendix_case_studies_v3_6_clean.md` for 8 detailed case studies: 4 trusted cases (one per class) and 4 boundary cases (mild vs. strong, strong vs. contradiction, supported vs. mild / evidence-context-missing, claim-too-abstract). All 8 cases have traceable candidate_ids in `strict_silver_max_candidates_v1.csv`. Boundary cases are used to illustrate task difficulty, not to support strong claims. The V3.6 appendix replaced V3.5 T2 (TCB_008, problematic number inflation) with SBV2-ALL92-G170-C02 (clean scope expansion), and replaced V3.5 B4 (placeholder with no real candidate_id) with HRC_001 = SBV2-ALL92-G003-STRONG (real case, claim_too_abstract root_cause) — see `case_integrity_audit.csv` for the full audit.

## Appendix B. Language Guardrails

### Safe claims (allowed in the paper):

- "R4 improves strong-action positive-F1 from 0.2408 to 0.3967 while preserving contradiction and escalation performance, on the current silver diagnostic set."
- "On silver-label pilot data, the conservative-strong router yields a strong-action positive-F1 delta of +0.1559 (CI [0.1058, 0.1988], 10/10 seeds positive)."
- "Under the tested prompts, generic LLM judges (GPT-5.5, DeepSeek-V3) consistently under-detect strong_action_overclaim on the tested samples, suggesting a consistent under-detection pattern under the tested setting."
- "This structured evidence-sufficiency prompt design did not improve strong_action detection under the tested setting; other prompt designs remain untested."
- "R4 complements black-box LLM judges on the strong_action_overclaim relation, rather than replacing them."
- "R4's macro-F1 is substantially lower than LLM judges (0.3280 vs. 0.5523 on matched 100); R4 is a relation-specific complement, not a general-purpose classifier."
- "Evidence sufficiency rather than generic factuality is the target of this framework."
- "The author sanity audit flags 62.5% of silver labels as questionable or unclear; independent gold adjudication is required."
- "The mixed framework is positioned as an action-overclaim diagnostic, not a final calibrated benchmark."

### Forbidden claims (must NOT appear in the paper):

- "We solve scientific claim calibration." / "Our model fully handles strong action overclaims."
- "Our labels are gold / human-audited." / "GPT can be used as gold label."
- "Proves LLMs cannot detect strong_action_overclaim." / "All LLMs are bad at this task."
- "R4 outperforms GPT overall." / "R4 is stronger than LLMs on all metrics."
- "Cost-sensitive cw4.0 is the new main method."
- "CESE-OCN outperforms strong baselines on a final benchmark."
- "The framework is validated for deployment." / "All four classes are well-calibrated."
- "supported_vs_mild boundary is resolved." / "Cross-domain generalization is confirmed."
- "SOTA / state-of-the-art." / "Fully solved."
- "Systematic blind spot" (use "consistent under-detection pattern under the tested prompts" instead).

### Cautious language (preferred):

- "under the tested prompts" / "under this tested setting"
- "on the current silver diagnostic set" / "on the 100 matched samples"
- "single-run, temperature 0, no variance estimate"
- "prompt/model/sample specific"
- "consistent under-detection pattern" (NOT "systematic blind spot")
- "on silver-label pilot data" / "AI-preannotated, author-screened labels"
- "exploratory pilot validation" / "not fully adjudicated gold"
- "suggests" / "supports" / "is consistent with" / "does not support"
- "complements black-box LLM judges"
- "evidence sufficiency rather than generic factuality"
- "relation-specific complement" / "diagnostic, not benchmark"
- "pending independent gold validation"

## References

[1] J. Thorne, A. Vlachos, C. Christodoulopoulos, and A. Mittal. 2018. FEVER: a Large-scale Dataset for Fact Extraction and VERification. NAACL-HLT.

[2] S. R. Bowman, G. Angeli, C. Potts, and C. D. Manning. 2015. A large annotated corpus for learning natural language inference. EMNLP.

[3] A. Wadden et al. 2020. Fact or Fiction: Verifying Scientific Claims. EMNLP.

[4] P. McCullagh. 1980. Regression models for ordinal data. JRSS Series B, 42(2):109-142.

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

[27] S. Kumar, A. Sharma, S. H. Khincha, G. Shroff, S. R. Singh, and R. Mishra. 2025. SciClaimHunt: A Large Dataset for Evidence-based Scientific Claim Verification. arXiv:2502.10003.

[28] S. R. Javaji, Y. Cao, H. Li, Y. Yu, N. Muralidhar, and Z. Zhu. 2025. Can AI Validate Science? Benchmarking LLMs on Claim-Evidence Reasoning in AI Papers. IJCNLP-AACL.

[29] S. Sadeghi, K. Khajavi, R. Adhikari, and A. Tessier. 2026. DeepSciVerify: Verifying Scientific Claim-Citation Alignment via LLM-Driven Evidence Escalation. arXiv:2605.27710.

[30] J. James, C. Xiao, Y. Li, N. S. Moosavi, and C. Lin. 2026. RIGOURATE: Quantifying Scientific Exaggeration with Evidence-Aligned Claim Evaluation. arXiv:2601.04350.

[31] H. Li. 2026. The Calibration Turn in AI-Assisted Research: A Conceptual and Methodological Framework for Evidence-Licensed Claims. arXiv:2606.31273.

[32] J. Gu et al. 2024. A Survey on LLM-as-a-Judge. arXiv:2411.15594.

[33] A. Bavaresco et al. 2025. LLMs instead of Human Judges? A Large Scale Empirical Study across 20 NLP Evaluation Tasks. ACL.

[34] M. Krumdick, C. Lovering, V. Reddy, S. Ebner, and C. Tanner. 2025. No Free Labels: Limitations of LLM-as-a-Judge Without Human Grounding. arXiv:2503.05061.
