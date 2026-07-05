# V3.13 Strengthening Plan After Related Work Shift (P0–P4)

**Date:** 2026-07-05
**Paper version:** V3.13 Differentiated Against RIGOURATE / ForceBench / CLAIM-BENCH
**Source paper:** `CESE_OCN_V3_13_differentiated_against_rigourate_forcebench.md`

## Scope

This plan re-orders the V3.13 strengthening roadmap into five priority levels (P0–P4), each specified with five fields: **目的** (purpose), **是否必须** (whether required), **成本** (cost), **能支撑什么结论** (what conclusions it supports), **失败时如何降级** (how to downgrade on failure). Items P2–P4 are **plan-only** in V3.13 (no API calls, no experiments); they specify what would be done in V3.14+ if authorized.

---

## P0 — 叙事差异化和 Related Work 对齐 (Pre-Advisor-Send)

### 目的
Ensure the paper is consistently positioned as a fine-grained relation-type decomposition on the existing scientific overstatement / evidence-force calibration track, with explicit and positive discussion of RIGOURATE [30], ForceBench [35], and CLAIM-BENCH [28]. Eliminate any residual "first to propose / novel task / new field / SOTA" framing in body text.

### 是否必须
**必须 (Required).** Without P0, the paper carries同质化风险 (homogeneity risk) against RIGOURATE / ForceBench / CLAIM-BENCH, and the advisor may reject the positioning.

### 成本
**Low.** Pure narrative work — no experiments, no API calls, no gold annotation. Estimated 4–8 hours of author time for: (i) adding concrete bibliography entries for [30], [35], [28]; (ii) verifying Table X renders readably in docx; (iii) re-reading Abstract + §I + §X for residual "first to propose" phrasing; (iv) confirming §V.A counterfactual transparency statement and §VIII.F fine-grained typing argument are consistent with §II.A.

### 能支撑什么结论
P0 supports the **positioning-level conclusion** that CESE-OCN is complementary to (not competing with) RIGOURATE / ForceBench / CLAIM-BENCH. After P0, the paper can be sent to the advisor with a defensible differentiation narrative. P0 does NOT support any empirical advantage claim — empirical head-to-head is P2.

### 失败时如何降级
- **If RIGOURATE / ForceBench / CLAIM-BENCH concrete references cannot be confirmed:** Downgrade the corresponding §II.A paragraph to "concurrent / unpublished work in progress" and remove the [N] citation; the positioning argument survives conceptually but loses citational grounding.
- **If Table X is too cramped in docx:** Split into two tables (RIGOURATE+ForceBench; CLAIM-BENCH+CESE-OCN) or transpose.
- **If residual "first to propose" phrasing is found:** Rephrase to "fine-grained diagnostic variant of evidence-sufficiency calibration on the existing track."
- **If the advisor rejects the positioning:** Add an explicit §IX item acknowledging the positioning is contested and add a P2 head-to-head comparison as a pre-condition for resubmission.

### P0 Sub-items
- **P0.1** — Add concrete bibliography entry for RIGOURATE [30] (author, year, venue, arXiv ID).
- **P0.2** — Add concrete bibliography entry for ForceBench [35]. If unavailable, downgrade §II.A ForceBench paragraph to "concurrent work in progress" and remove [35].
- **P0.3** — Confirm [28] is CLAIM-BENCH (not SciClaimHunt [27]); add concrete bibliography entry.
- **P0.4** — Verify Table X renders readably in V3.13 docx.
- **P0.5** — Re-read Abstract + §I + §X for residual "first to propose / novel task / new field / SOTA" phrasing.

---

## P1 — 50-Sample Relation + Realism Gold Pilot (Pre-Confirmatory-Submission)

### 目的
Run the pre-registered gold adjudication protocol (§VII) on a 50-case pilot, collecting **both** the relation label (supported / mild_scope_overclaim / strong_action_overclaim / contradiction_candidate) AND the proposed realism fields (`claim_realism_score_1_to_5`, `claim_realism_issue` from §VII.I). This is the protocol-locked mechanism that determines whether the silver-stage patterns are treated as validated.

### 是否必须
**必须 (Required).** The paper's §VII explicitly pre-registers this protocol as the validation mechanism. Without P1, all §VI and §VIII.D results remain "controlled silver-stage evidence" indefinitely, and the paper cannot move to confirmatory submission. The advisor cannot sign off on the screening claim without at least the 50-case pilot.

### 成本
**Medium.** Roughly: 50 cases × 2 annotators × ~10 min/case = ~17 annotator-hours; plus adjudication ~4 hours; plus realism audit training packet preparation ~4 hours; plus analysis + reporting ~6 hours. Total ~30 person-hours. No API cost. No new model training. Annotator compensation per institutional policy.

### 能支撑什么结论
P1 supports:
- **Relation-label agreement:** Cohen's κ or Krippendorff's α between two annotators and against silver, per class and per boundary (esp. mild vs. strong boundary).
- **strong_action retention rate:** Whether the silver-stage R4 > LLM pattern on strong_action survives gold adjudication.
- **Realism distribution:** Per-class mean `claim_realism_score_1_to_5` and % low-realism flags.
- **Realism-conditioned re-evaluation:** Whether the R4 > LLM pattern holds when low-realism claims are excluded.

If P1 succeeds (κ ≥ 0.4 on strong_action boundary; retention rate ≥ 60%; < 25% low-realism in strong_action class), the paper upgrades from "controlled silver-stage evidence" to "gold-pilot-validated evidence on 50 cases, with 300–500-case confirmatory study pending."

### 失败时如何降级
- **If κ < 0.4 on strong_action boundary:** Trigger §VII.G downgrade criterion 1 — the strong_action class is not reliably drawable; downgrade the screening claim to "exploratory" and add a §IX limitation that the strong_action boundary fails the pre-registered κ threshold.
- **If retention rate < 60%:** Trigger §VII.G downgrade criterion 2 — the silver-stage R4 > LLM pattern does not survive gold; replace "R4 improves strong_action recall" with "R4 does not improve strong_action recall under gold adjudication" in §VI and §VIII.A.
- **If > 25% low-realism in strong_action class:** Trigger §VII.I class-level realism threshold — add explicit realism caveat to §VI strong_action result and §VIII.D.B screening-utility claim; bound the screening finding to the diagnostic set.
- **If > 25% low-realism overall:** Trigger §VII.I paper-level realism threshold — downgrade main claims from "controlled silver-stage evidence on a diagnostic set" to "controlled silver-stage evidence on a synthetic diagnostic set with limited natural-claim transferability"; add §IX item.
- **If gold pilot cannot be run at all (e.g., annotator unavailable):** Keep V3.13 as silver-stage-only; explicitly state in §X that gold validation is pending and the paper is a framework-level contribution, not a validated benchmark.

### P1 Sub-items
- **P1.1** — Update `gold_pilot_protocol_freeze_v1/annotator_training_packet.md` to include realism scoring rubric + 5 calibration examples.
- **P1.2** — Generate `pilot_50_blind_annotation_A_realism_template.csv` and `pilot_50_blind_annotation_B_realism_template.csv` (add realism columns; do NOT modify existing CSVs).
- **P1.3** — Update `adjudication_template.csv` (or generate `adjudication_template_realism.csv`) to include final realism columns.
- **P1.4** — Advisor sign-off on 25% class-level and 25% paper-level realism thresholds before pilot starts.
- **P1.5** — Run the 50-case pilot with two independent annotators + adjudication + realism audit.
- **P1.6** — Populate Tables G1–G3; evaluate §VII.G downgrade criteria; evaluate §VII.I realism thresholds; report.

---

## P2 — RIGOURATE-Style Scalar Overstatement Baseline (Plan-Only in V3.13)

### 目的
Add a **scalar overstatement baseline** that produces a continuous overstatement score per claim-evidence pair, then thresholds it into no-overclaim vs. overclaim. This tests whether a RIGOURATE-style scalar alone can separate mild_scope_overclaim from strong_action_overclaim, or whether the four-class relation-type decomposition is operationally necessary. **Plan-only in V3.13 — no API, no model run.**

### 是否必须
**Strongly recommended but not strictly required for the V3.13 advisor send.** Required for confirmatory submission (P2-tier). Without P2, the §II.A claim that "RIGOURATE does not isolate mild scope from high-risk action overclaim" remains a conceptual argument, not an empirically demonstrated one (§IX item 9 acknowledges this).

### 成本
**Medium-High.** Two branches (see `rigourate_style_baseline_plan.md` for full plan):
- **Branch A (preferred):** If RIGOURATE public model / code / checkpoint is available, run it on all 444 SimClaim pairs. Cost: engineering time to integrate (~1–2 days) + inference compute (modest if CPU-compatible).
- **Branch B (fallback):** If RIGOURATE is not available, construct a RIGOURATE-style scalar baseline using a comparable scoring approach (e.g., a fine-tuned regressor on SimClaim silver labels producing a 0–3 or 0–1 score, OR a prompt-based LLM scalar overstatement rater). Cost: ~2–3 days engineering + LLM API cost (~$5–$20 for 444 pairs at current DeepSeek/GPT rates).

### 能支撑什么结论
P2 supports:
- **Scalar-vs-relation-type comparison:** Can a scalar score alone distinguish mild_scope_overclaim from strong_action_overclaim? If yes, the four-class decomposition is operationally redundant; if no, the decomposition is necessary.
- **R4 strong_action screening recall / FP/TP vs. scalar baseline:** Does R4's relation-specific routing add value over a thresholded scalar score for high-risk action-overclaim screening?
- **Empirical differentiation against RIGOURATE:** Converts §II.A from "conceptual complementarity" to "empirically demonstrated complementarity" (resolves §IX item 9).

If P2 succeeds (scalar score cannot distinguish mild from strong at pre-registered threshold; R4 strong_action recall > scalar-baseline strong_action recall by a significant margin), the paper's central differentiation claim becomes empirically grounded.

### 失败时如何降级
- **If scalar score CAN distinguish mild from strong:** The four-class decomposition loses its operational-necessity argument. Downgrade §VIII.F from "fine-grained typing is operationally valuable" to "fine-grained typing is a complementary diagnostic perspective"; add §IX item acknowledging that scalar scoring may suffice for some screening applications.
- **If R4 strong_action recall is NOT significantly higher than scalar baseline:** The screening-method contribution weakens. Add §IX item: "R4's relation-specific routing does not significantly outperform a thresholded scalar baseline on strong_action screening under this comparison."
- **If RIGOURATE public model is unavailable AND the fallback scalar baseline is also unconvincing (e.g., LLM scalar rater has near-100% accuracy trivially because it sees silver labels in prompt):** Drop P2 entirely; keep §II.A as conceptual positioning; add §IX item that empirical head-to-head is left for future work.
- **If P2 cannot be run at all:** Keep §IX item 9 as-is; the paper remains positioning-level, not empirical-head-to-head.

### P2 Sub-items
- **P2.1** — Confirm whether RIGOURATE public model / code / checkpoint is available (search arXiv, GitHub, Hugging Face).
- **P2.2** — If available (Branch A): integrate, run on 444 SimClaim pairs, save predictions.
- **P2.3** — If unavailable (Branch B): construct RIGOURATE-style scalar baseline per `rigourate_style_baseline_plan.md`.
- **P2.4** — Evaluate scalar baseline: (a) can it distinguish mild vs. strong at any threshold? (b) R4 strong_action recall / FP/TP vs. scalar-baseline-thresholded-as-strong_action-screen.
- **P2.5** — Report results in new §VI.D "Scalar Overstatement Baseline Comparison"; update §II.A and Table X with empirical column; update §IX item 9.

---

## P3 — Few-Shot / CoT LLM Prompt Baseline (Plan-Only in V3.13)

### 目的
Test whether the LLM strong_action under-detection pattern (§VI.B: GPT-5.5 / DeepSeek-V3 strong-F1 = 0.0769) is robust to prompt design, by running additional prompt conditions: **few-shot** (with 4–8 labeled examples in the prompt) and **chain-of-thought (CoT)** (with explicit reasoning steps before the label). **Plan-only in V3.13 — no API calls.**

### 是否必须
**Strongly recommended for confirmatory submission.** Without P3, the §VI.B / §VIII.B claim that "LLM judges under-detect strong_action under the tested prompts" may be dismissed as a prompt-engineering artifact. The §IX item 3 already acknowledges this limitation explicitly.

### 成本
**Medium.** LLM API cost: 2 models (GPT-5.5, DeepSeek-V3) × 3 prompt designs (standard, few-shot, CoT) × 200 samples = 1200 LLM calls. At current DeepSeek rates (~$0.01–$0.05 per call depending on context), total ~$12–$60. Engineering time: ~2 days to design few-shot example selection and CoT templates.

### 能支撑什么结论
P3 supports:
- **Prompt-robustness of the under-detection pattern:** Does any prompt design (few-shot or CoT) lift LLM strong_action-F1 from 0.0769 to a competitive level?
- **If yes:** The under-detection is a prompt artifact; downgrade §VIII.B claim and reposition R4 as "useful when prompt engineering budget is limited."
- **If no:** The under-detection is prompt-robust across {standard, structured 5-step, few-shot, CoT}; strengthen §VIII.B claim.

If P3 succeeds in showing prompt-robustness (no prompt design lifts strong_action-F1 above, say, 0.20), the paper's diagnostic contribution is significantly strengthened.

### 失败时如何降级
- **If few-shot or CoT lifts strong_action-F1 above 0.30:** The under-detection is a prompt artifact. Downgrade §VIII.B from "LLM judges consistently under-detect" to "LLM judges under-detect under zero-shot and structured prompts, but few-shot / CoT can recover much of the gap." Reposition R4 as a "prompt-budget-free screening complement."
- **If results are mixed (one prompt works for one model but not the other):** Add §IX item specifying the prompt-dependence; report per-prompt-per-model results in §VI.B.
- **If P3 cannot be run (API unavailable or cost-prohibitive):** Keep §IX item 3 as-is; the under-detection claim remains bounded to "under the tested prompts" (standard + structured 5-step).

### P3 Sub-items
- **P3.1** — Design few-shot example selection (4–8 labeled SimClaim examples per class, sampled from train split only).
- **P3.2** — Design CoT template (explicit reasoning steps: evidence summary → claim strength assessment → relation label).
- **P3.3** — Run 2 models × 3 prompts × 200 samples; save predictions.
- **P3.4** — Evaluate per-prompt per-model strong_action-F1, macro-F1, recall.
- **P3.5** — Report in §VI.B prompt-robustness table; update §VIII.B; update §IX item 3.

---

## P4 — Low-Prevalence Screening Simulation (Plan-Only in V3.13)

### 目的
SimClaim's four-way balanced design (111 per class) inflates the base rate of strong_action_overclaim relative to natural scientific corpora. P4 simulates a **low-prevalence screening setting** by downsampling strong_action_overclaim to a realistic base rate (e.g., 2%, 5%, 10%) and re-evaluating R4's screening utility (FP/TP, recall, precision) at each prevalence level. **Plan-only in V3.13 — no experiments.**

### 是否必须
**Recommended for confirmatory submission, but not strictly required.** Without P4, the §VIII.D.B screening utility claim (FP/TP = 2.89, recall = 0.36) is bounded to the balanced diagnostic set; downstream deployment on natural corpora would need to re-calibrate the operating threshold.

### 成本
**Low.** Pure simulation on existing predictions and silver labels — no API, no new model training. Engineering time: ~1 day to implement prevalence downsampling + bootstrap CI; compute: minutes on a laptop.

### 能支撑什么结论
P4 supports:
- **Prevalence-conditional screening utility:** How do R4's FP/TP, recall, and precision change as strong_action_overclaim prevalence drops from 25% (balanced) to 2% (realistic)?
- **Operating-threshold recommendation:** At what prevalence level should the R4 strong-action threshold be tightened to maintain a target FP/TP ratio?
- **Deployment guidance:** If R4's recall drops below 0.10 at 2% prevalence, the screening claim is bounded to high-prevalence settings; if it stays above 0.20, R4 is deployable as a low-prevalence screen.

If P4 succeeds (R4 recall ≥ 0.20 at 5% prevalence with FP/TP ≤ 5), the screening claim generalizes to low-prevalence deployment settings.

### 失败时如何降级
- **If R4 recall drops below 0.10 at 5% prevalence:** The screening claim is bounded to high-prevalence settings. Add §IX item: "R4's screening utility is prevalence-dependent; at < 5% strong_action prevalence, recall drops below 0.10, limiting deployment to high-prevalence screening contexts."
- **If FP/TP explodes (> 20) at low prevalence:** Add §IX item specifying that R4 requires threshold re-calibration for low-prevalence deployment; provide a prevalence-to-threshold lookup table as a deployment aid.
- **If P4 cannot be run:** Keep §V.A counterfactual transparency statement as the only caveat; note in §IX that prevalence-conditional screening utility is left for future work.

### P4 Sub-items
- **P4.1** — Implement prevalence downsampling: at each target prevalence {2%, 5%, 10%, 15%, 20%, 25% (balanced)}, downsample strong_action_overclaim cases (with replacement) and re-compute R4 screening metrics.
- **P4.2** — Bootstrap CI (1000 resamples) for FP/TP, recall, precision at each prevalence.
- **P4.3** — Generate prevalence-vs-metric curves; identify the prevalence floor below which R4 is no longer useful.
- **P4.4** — Report in new §VIII.G "Prevalence-Conditional Screening Utility"; update §VIII.D.B; update §IX.

---

## Priority Order Summary

| Priority | Item | 是否必须 | 成本 | When |
| --- | --- | --- | --- | --- |
| **P0** | 叙事差异化和 Related Work 对齐 | 必须 | Low (4–8h, no API) | Pre-advisor-send |
| **P1** | 50-sample relation + realism gold pilot | 必须 | Medium (~30 person-hours, no API) | Pre-confirmatory-submission |
| **P2** | RIGOURATE-style scalar overstatement baseline | 强烈推荐 | Medium-High (1–3 days + ~$5–$60 API) | Pre-confirmatory-submission (Plan-only in V3.13) |
| **P3** | Few-shot / CoT LLM prompt baseline | 强烈推荐 | Medium (~2 days + ~$12–$60 API) | Pre-confirmatory-submission (Plan-only in V3.13) |
| **P4** | Low-prevalence screening simulation | 推荐 | Low (~1 day, no API) | Pre-confirmatory-submission (Plan-only in V3.13) |

## What This Plan Does NOT Do

- **Does not change any V3.13 numeric result.** All items are forward-looking.
- **Does not run any new experiment in V3.13.** P0 is polish; P1 is gold pilot (forward); P2–P4 are plan-only specifications for V3.14+.
- **Does not modify V3.12.1, V3.12, V3.11, V3.10.1, or V3.9.** All prior versions preserved unchanged.
- **Does not replace §VII.G.** All downgrade routes specified above are *additional* to the existing §VII.G criteria.
- **Does not claim P2–P4 results.** `rigourate_style_baseline_plan.md` is explicitly marked as plan-only; §IX item 9 retains "positioning-level, not empirical head-to-head" until P2 is actually run.

## Cross-References

- §V.A (SimClaim synthetic/counterfactual transparency)
- §VII.G (downgrade criteria)
- §VII.I (proposed gold-realism audit extension)
- §VIII.D.B (screening utility)
- §VIII.F (why fine-grained relation typing is valuable)
- §IX item 9 (differentiation is positioning-level)
- §IX item 10 (SimClaim is a controlled counterfactual diagnostic set)
- `proposed_gold_realism_extension.md` (standalone realism audit specification)
- `rigourate_style_baseline_plan.md` (standalone P2 plan)
- `related_work_differentiation_table.md` (standalone Table X)
- `V3_13_positioning_change_log.md` (positioning change log from V3.12.1 → V3.13)
