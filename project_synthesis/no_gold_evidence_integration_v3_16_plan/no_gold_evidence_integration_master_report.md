# No-Gold Evidence Integration Master Report (V3.16 Plan)

**Task:** No-Gold Evidence Integration Plan for V3.16
**Date:** 2026-07-05
**Output directory:** `D:\ocn\project_synthesis\no_gold_evidence_integration_v3_16_plan\`
**Base paper version:** V3.15 (hierarchical taxonomy revision)
**Scope:** Integration only. No gold, no API, no paper modification, no original-data modification.

---

## 1. Section summary

| # | Section | Source | Status |
| --- | --- | --- | --- |
| 1 | RIGOURATE-style scalar baseline | Part 1 (reused) | completed (proxy; NLI blocked) |
| 2 | Scalar vs R4 / LLM comparison | Part 2 (reused) | completed |
| 3 | Claim realism auto audit | Part 2 (reused) | completed (heuristic, not gold) |
| 4 | Low-prevalence screening simulation | v3_15 (reused) | completed (simulation, not natural distribution) |
| 5 | ForceBench feasibility | Part 2 (reused) | blocked (no public data) |
| 6 | Public dataset positioning insert | Part 2 (reused) | ready |
| 7 | V3.16 revision plan | new | ready (plan only; no paper modification) |
| 8 | Master report and gate | new | this file |

---

## 2. Headline findings

### 2.1 Scalar baseline (Section 1)
- rule_scalar_score: 444 candidates, cue-based 0-3 scoring.
- nli_scalar_score: **blocked** (no HCM/NLI features in repo).
- llm_scalar_proxy: 200/444 candidates (LLM-label-derived 0-3).
- **Scalar cannot distinguish mild vs strong_action** (rule_scalar ROC-AUC ~0.5054; llm_scalar_proxy ROC-AUC ~0.5874; threshold 0.60 -> False).
- Scalar *can* detect strong_action vs non-strong, but at much lower F1 than R4.

### 2.2 Scalar vs R4 vs LLM on strong_action (Section 2)
- R4 strong-F1 = **0.3967** (silver 444) vs rule_scalar = 0.2996 vs DeepSeek LLM = 0.0769.
- R4 captures **8/24 (33.3%)** of LLM-missed strong_action cases on 100 matched subset.
- LLM is 9x more conservative than R4 on strong_action prediction rate.
- **R4 retains independent value as a strong_action screening complement.**

### 2.3 Claim realism auto audit (Section 3)
- 444 claims audited; 0.2% high-risk, 2.0% medium-risk, 97.7% no-risk.
- strong_action forced rate = 0.0%; contradiction mechanical rate = 0.9%.
- **SimClaim remains suitable as a controlled diagnostic set, NOT as a natural-prevalence corpus.**
- Realism risk is NOT high; paper must still disclose the controlled-counterfactual design.

### 2.4 Low-prevalence screening simulation (Section 4)
- R4 recall stable at ~0.36 across 1-25% prevalence.
- R4 FP/TP ratio: **158 @1%**, ~25 @5%, **11.7 @10%**.
- R4 standalone-usable only at prevalence >= 10%; two-stage-usable below.
- LLM accuracy is misleading at low prevalence (~0.99 @1% but recall ~0.04).
- **R4 screening positioning is partially supported: second-stage router, not standalone screen.**

### 2.5 ForceBench feasibility (Section 5)
- **Blocked.** No public GitHub, HuggingFace, or downloadable data located.
- No empirical comparison reported; positioning paragraph only.

### 2.6 Public dataset positioning (Section 6)
- Insert paragraphs ready for RIGOURATE, ForceBench, SciFact, CLAIM-BENCH, VitaminC.
- All paragraphs enforce: SimClaim is a controlled counterfactual diagnostic set, not a natural-prevalence corpus; public datasets do not label high-risk action/deployment overclaim.

---

## 3. Main-line judgment (no-gold conditions)

**Question: Is the main line supported without gold?**

**Answer: YES, with caveats.**

The hierarchical taxonomy survives without gold on the strength of three no-gold findings:
1. Scalar overstatement scores cannot replace relation typing (ROC-AUC < 0.60 on mild_vs_strong).
2. R4 retains independent value as a strong_action screening complement (captures LLM-missed cases; F1 advantage ~0.10 over scalar).
3. SimClaim is a controlled counterfactual diagnostic set, suitable for relation-type separability diagnosis.

**Caveats:**
- Level-2 mild_vs_strong boundary is *not* validated without gold; the pre-registered fallback (three-class + binary strong_action) must be retained.
- All quantitative results are on silver labels; gold adjudication may shift conclusions.
- ForceBench and RIGOURATE official comparisons are blocked; positioning only.

---

## 4. V3.16 revision readiness

**Question: Can V3.16 be written?**

**Answer: YES, as a no-gold revision.**

The V3.16 revision plan (Section 7) is ready. The revision:
- Adds 3 new result subsections (scalar baseline, scalar vs R4/LLM, low-prevalence simulation).
- Adds 5 explicit limitations (silver-only, RIGOURATE-proxy, ForceBench-blocked, simulation-not-natural, realism-risk).
- Adds a two-stage deployment recommendation.
- Down-tones 5 phrasings ("detects high-risk" -> "screening-oriented complement", etc.).
- Does NOT change any existing experiment number.
- Does NOT trigger the pre-registered fallback (pending gold).

---

## 5. Biggest remaining risks

1. **Silver-only evaluation.** Gold adjudication may shift the mild_vs_strong boundary conclusion; if κ < 0.40, the Level-2 decomposition must be downgraded.
2. **RIGOURATE official artifacts unavailable.** The proxy baseline is the best available substitute; reviewers may argue the proxy is too weak.
3. **ForceBench blocked.** No empirical comparison; positioning only.
4. **Simulation, not natural distribution.** The low-prevalence numbers must be carefully labelled to avoid being misread as real-world performance.
5. **Realism risk non-zero.** 2.0% medium-risk claims require disclosure; the gold realism layer is required to validate.

---

## 6. Recommended next action

1. **Apply V3.16 revision plan** (Section 7) in a separate revision pass after advisor sign-off.
2. **Execute the 50-pair two-layer relation+realism gold pilot** (pre-registered protocol v2) to validate the Level-2 mild_vs_strong boundary.
3. If gold κ >= 0.40 on mild_vs_strong: retain Level-2 decomposition in V3.17.
4. If gold κ < 0.40: trigger the pre-registered fallback (three-class + binary strong_action).
5. Monitor RIGOURATE and ForceBench artifact releases; re-run comparisons if artifacts become available.

---

## 7. Prohibitions enforced

- No gold annotation — PASS.
- No human annotation — PASS.
- No API calls — PASS.
- No model training — PASS.
- No paper main-text modification — PASS (this is a plan; revision is a separate pass).
- No original-data modification — PASS.
- No silver-as-gold — PASS.
- No proxy-as-official-RIGOURATE — PASS.
- No simulation-as-natural-distribution — PASS.

---

## 8. Output files

1. `rigourate_style_scalar_scores.csv` (reused from Part 1)
2. `scalar_baseline_report.md` (reused from Part 1)
3. `scalar_baseline_gate.json` (adapted from Part 1)
4. `scalar_vs_r4_llm_results.csv` (reused from Part 2)
5. `scalar_vs_r4_llm_cases.csv` (reused from Part 2)
6. `scalar_vs_r4_llm_report.md` (reused from Part 2)
7. `claim_realism_auto_audit.csv` (reused from Part 2)
8. `claim_realism_auto_summary.md` (reused from Part 2)
9. `low_prevalence_screening_results.csv` (reused from v3_15)
10. `low_prevalence_screening_report.md` (new, adapted)
11. `forcebench_feasibility_report.md` (reused from Part 2)
12. `forcebench_gate.json` (reused from Part 2)
13. `public_dataset_positioning_insert.md` (reused from Part 2)
14. `V3_16_no_gold_revision_plan.md` (new)
15. `no_gold_evidence_integration_master_report.md` (this file)
16. `no_gold_evidence_integration_gate.json` (new)
