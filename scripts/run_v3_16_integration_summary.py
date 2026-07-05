# -*- coding: utf-8 -*-
"""
V3.16 Integration Summary + Revision Plan generator.

Reads the 5 task gates + V3.12 readiness gate + related-work insert,
produces 6 synthesis outputs in
D:\\ocn\\project_synthesis\\v3_16_integration_summary_and_revision_plan\\

NO experiments. NO API calls. NO gold. NO paper modification.
NO original data modification. NO submission draft.
NO planned-as-completed. NO silver-as-gold. NO proxy-as-official-RIGOURATE.
"""

import json
import os
import csv
from datetime import date

OUT_DIR = r"D:\ocn\project_synthesis\v3_16_integration_summary_and_revision_plan"
os.makedirs(OUT_DIR, exist_ok=True)

GATE_PATHS = {
    "T1_rigourate": r"D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1\rigourate_reproduction_readiness_gate.json",
    "T2_low_prev": r"D:\ocn\experiments\v3_15_low_prevalence_screening_simulation\low_prevalence_screening_gate.json",
    "T3_realism": r"D:\ocn\experiments\v3_15_claim_realism_audit\claim_realism_audit_gate.json",
    "T4_gold_v2": r"D:\ocn\gold_pilot_relation_realism_protocol_v2\relation_realism_protocol_v2_gate.json",
    "T5_scalar": r"D:\ocn\experiments\v3_15_scalar_vs_relation_screening_deep_test\scalar_vs_relation_deep_test_gate.json",
    "V3_12": r"D:\ocn\paper_versions_ordered\V3_12_with_three_credibility_checks\V3_12_readiness_gate.json",
}

def load_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

gates = {k: load_json(v) for k, v in GATE_PATHS.items()}

TODAY = date.today().isoformat()

# -----------------------------------------------------------------
# Section 1: five_task_status_matrix.csv
# -----------------------------------------------------------------
matrix_rows = [
    {
        "task_id": "T1",
        "task_name": "RIGOURATE reproduction / proxy baseline",
        "completed": "true",
        "main_output_dir": "D:\\ocn\\experiments\\rigourate_reproduction_and_simclaim_baseline_v1\\",
        "main_result": (
            "Official RIGOURATE code/data/model UNAVAILABLE (blocked); "
            "3 proxy baselines built (rule_scalar=N444, nli_scalar=blocked, llm_scalar=N200); "
            "scalar cannot distinguish mild vs strong (rule ROC-AUC=0.5062, llm ROC-AUC=0.5874); "
            "R4 strong_F1=0.3967 > scalar best-F1=0.3844 on 444 silver; "
            "R4 captures 8/24 LLM-missed strong_action."
        ),
        "supports_mainline": "true",
        "weakens_mainline": "true",
        "requires_revision": "true",
        "blocking_issue": "Official RIGOURATE artifacts unavailable; proxy results cannot be claimed as official.",
        "recommended_use": (
            "Cite as PROXY baseline labelled 'rule_scalar_score / llm_scalar_score', NOT 'RIGOURATE'. "
            "State official reproduction blocked. Use as complementary reference supporting four-class decomposition."
        ),
    },
    {
        "task_id": "T2",
        "task_name": "Low-prevalence screening simulation",
        "completed": "true",
        "main_output_dir": "D:\\ocn\\experiments\\v3_15_low_prevalence_screening_simulation\\",
        "main_result": (
            "R4 recall stable ~0.36 across 1%-25% prevalence; "
            "R4 NOT viable as standalone screener <10% (FP/TP=25-121, NNR=27-159); "
            "R4 marginal at 10% (FP/TP=12), viable at 25% (FP/TP=3.8); "
            "LLM shows high-accuracy/low-recall failure mode (99% acc, 4.3% recall at 1%); "
            "R4 captures 3.19-80.04 LLM-missed strong per 1000 samples."
        ),
        "supports_mainline": "true",
        "weakens_mainline": "true",
        "requires_revision": "true",
        "blocking_issue": "Two-stage pipeline (R4 -> LLM/human) proposed but NOT empirically evaluated.",
        "recommended_use": (
            "Frame R4 as first-stage high-recall filter in two-stage pipeline (NOT standalone). "
            "Report FP/TP, NNR, review burden alongside F1. State simulation uses heuristic 80/15/5 non-strong composition."
        ),
    },
    {
        "task_id": "T3",
        "task_name": "Claim realism audit",
        "completed": "true",
        "main_output_dir": "D:\\ocn\\experiments\\v3_15_claim_realism_audit\\",
        "main_result": (
            "0% high-risk claims; 4.7% overall realism risk; 9.0% strong_action risk; "
            "52.3% contradiction_mechanical; 76.6% group_template_risk; 0.9% strong_forced; "
            "safe_to_use_as_diagnostic_set=true; safe_to_claim_naturalistic=false."
        ),
        "supports_mainline": "true",
        "weakens_mainline": "true",
        "requires_revision": "true",
        "blocking_issue": "Audit is heuristic/automatic; NOT human gold; cannot validate realism without Layer-2 gold annotation.",
        "recommended_use": (
            "Include realism audit in Limitations as author-side automatic audit awaiting human validation. "
            "Feed high-risk claims into v2 gold pilot. Exclude extreme/templated cases from paper illustrative examples."
        ),
    },
    {
        "task_id": "T4",
        "task_name": "Relation+realism gold protocol v2",
        "completed": "true",
        "main_output_dir": "D:\\ocn\\gold_pilot_relation_realism_protocol_v2\\",
        "main_result": (
            "v2 two-layer protocol DRAFTED (Layer 1 relation + Layer 2 realism, independent); "
            "50-row A/B templates silver-leakage-free; "
            "9 realism_issue types + 5-point scale; 6 pre-registered decision rules; "
            "ready_for_blind_annotation=true; does_not_modify_v1=true; "
            "ANNOTATION NOT BEGUN (protocol-only deliverable)."
        ),
        "supports_mainline": "true",
        "weakens_mainline": "false",
        "requires_revision": "true",
        "blocking_issue": "v2 is DRAFT; not piloted; annotators untrained on Layer 2; realism agreement untested.",
        "recommended_use": (
            "Identify 2 annotators + 1 adjudicator; train on v2 guideline; run 50-pair pilot; "
            "apply pre-registered thresholds (kappa<0.40 -> taxonomy revision; realism_score<=2 rate>25% -> downgrade)."
        ),
    },
    {
        "task_id": "T5",
        "task_name": "Scalar vs relation screening deep test",
        "completed": "true",
        "main_output_dir": "D:\\ocn\\experiments\\v3_15_scalar_vs_relation_screening_deep_test\\",
        "main_result": (
            "Scalar CANNOT separate mild/strong (rule ROC-AUC=0.5062, llm ROC-AUC=0.5874); "
            "Score collapse confirmed (4 indicators: overlap=1.02, contra/strong within 15pp, "
            "supported high=54.1%, strong var/overall=0.94); "
            "R4 retains advantage (F1=0.30 vs 0.14; recall=0.36 vs 0.12; LLM-missed captured 8 vs 3); "
            "scalar CANNOT replace R4."
        ),
        "supports_mainline": "true",
        "weakens_mainline": "false",
        "requires_revision": "true",
        "blocking_issue": "All results on silver labels (pre-gold); gold may shift comparison.",
        "recommended_use": (
            "Cite as core empirical support for four-class decomposition. "
            "Position scalar as complementary severity signal, NOT replacement for relation-specific screening."
        ),
    },
]

with open(os.path.join(OUT_DIR, "five_task_status_matrix.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(matrix_rows[0].keys()))
    w.writeheader()
    w.writerows(matrix_rows)

# -----------------------------------------------------------------
# Section 2: mainline_impact_summary.md
# -----------------------------------------------------------------
mainline_md = f"""# V3.16 Mainline Impact Summary

**Date:** {TODAY}
**Status:** Synthesis only. NO experiments, NO API calls, NO gold, NO paper modification, NO original data modification.
**Scope:** Five-task integration judgment based on T1-T5 gate files + V3.12 readiness gate.

---

## Q1. Is the current mainline still valid?

**Verdict: YES — the mainline survives, but with mandatory revisions.**

The mainline — *CESE-OCN as a four-class relation-typing framework with R4 as a screening-oriented complement to LLM judges, targeting high-risk strong_action_overclaim* — is supported by all five tasks:

- T1 (RIGOURATE proxy): scalar cannot replace R4; R4 retains strong_F1 advantage.
- T2 (low-prevalence sim): R4 recall stable ~0.36 across prevalences; captures LLM-missed strong.
- T3 (realism audit): realism risk is non-trivial but below 25% threshold; SimClaim usable as diagnostic set.
- T4 (gold v2): two-layer protocol drafted; path to gold defined.
- T5 (scalar deep test): scalar cannot separate mild/strong; score collapse confirmed; R4 retains advantage.

**Mandatory revisions:** (a) qualify R4 as first-stage filter in two-stage pipeline (not standalone below 10% prevalence); (b) add realism caveat to Limitations; (c) clearly distinguish silver-stage from gold-validated claims; (d) label scalar baseline as PROXY, not official RIGOURATE.

---

## Q2. Should the paper still position strong_action as a rare high-risk screening target?

**Verdict: YES — but with explicit two-stage deployment framing.**

- T2 simulation confirms R4 has *stable recall* (~0.36) regardless of prevalence, which is the screening-oriented property the paper claims.
- T2 also confirms R4 is NOT viable as a *standalone* screener below 10% prevalence (FP/TP=25-121, NNR=27-159).
- The screening positioning must therefore be reframed: R4 is a *first-stage high-recall filter* in a two-stage pipeline (R4 -> LLM/human second-stage). The two-stage pipeline is PROPOSED but NOT evaluated in this paper.

**Implication:** keep the screening positioning, but downgrade from "deployment-ready screener" to "first-stage filter candidate; deployment requires two-stage evaluation, which is future work."

---

## Q3. Does RIGOURATE constitute fatal overlap / homogenisation?

**Verdict: NO.**

Three reasons:

1. **Output representation differs.** RIGOURATE produces a continuous scalar overstatement score in [0,1]; CESE-OCN produces a four-class relation label. These are not interchangeable (T5 confirms scalar cannot replace the four-class decomposition).
2. **Empirical complementarity.** T5 shows scalar score collapse (mild/strong overlap=1.02) and ROC-AUC near chance for mild/strong boundary. R4 retains F1=0.30 vs scalar F1=0.14 on matched-100.
3. **Reproducibility blocker.** Official RIGOURATE code/data/model are unavailable as of 2026-07-05; the proxy baseline is explicitly labelled, and the paper must state this clearly.

**Implication:** RIGOURATE is a *complementary related work*, not a fatal overlap. The paper should position scalar severity (RIGOURATE) and relation typing (CESE-OCN) as addressing different facets of evidential proportionality.

---

## Q4. Does the scalar baseline weaken R4?

**Verdict: NO.** The scalar baseline *strengthens* the case for R4 by providing a controlled comparison.

- T5: R4 strong_F1=0.30 vs scalar F1=0.14 (matched-100); R4 recall=0.36 vs scalar 0.12.
- T5: R4 captures 8 LLM-missed strong_action; scalar captures only 3.
- T1: R4 strong_F1=0.3967 vs scalar best-F1=0.3844 (444 silver); R4 captures 8/24 LLM-missed strong.
- T5: score collapse (4 indicators) shows scalar compression loses the action-vs-scope distinction that R4's routing preserves.

**Implication:** the scalar baseline is empirical support for the four-class decomposition, not a threat to R4.

---

## Q5. Does the low-prevalence simulation support deployment-style screening?

**Verdict: PARTIAL — supports first-stage filter role; does NOT support standalone deployment.**

- R4 NOT viable standalone below 10% prevalence (FP/TP=25-121).
- R4 marginal at 10% (FP/TP=12), viable at 25% (FP/TP=3.8) — matches balanced SimClaim prevalence.
- LLM judges exhibit a high-accuracy/low-recall failure mode (99% accuracy but 4.3% recall at 1% prevalence), making accuracy a misleading deployment metric.
- Two-stage pipeline (R4 -> LLM/human) is PROPOSED but NOT evaluated.

**Implication:** the paper must (a) NOT claim R4 is a deployment-ready standalone screener; (b) explicitly state that balanced SimClaim macro-F1 cannot be extrapolated to deployment; (c) propose the two-stage pipeline as future work; (d) report prevalence-aware metrics (FP/TP, NNR, review burden) alongside F1.

---

## Q6. Is the claim realism risk severe?

**Verdict: NO — non-trivial but below pre-registered thresholds.**

- T3: 0% high-risk claims; 4.7% overall realism risk; 9.0% for strong_action.
- All below the 25% pre-registered class-level threshold.
- Dominant risks are *design attributes* (templating 92.8%, mechanical-contradiction 52.3%, narrow-boundary 33.3%) rather than quality defects (extreme 7.0%, forced 0.9%, unnatural 0.2%).
- SimClaim is safe as a *controlled diagnostic set*, NOT as a *naturalistic corpus*.

**Implication:** SimClaim retains diagnostic value; the paper must state "controlled counterfactual diagnostic set, not naturalistic corpus" in Data and Limitations.

---

## Q7. Is relation+realism gold mandatory?

**Verdict: YES.**

- T3 realism audit is heuristic/automatic; cannot validate realism without human gold.
- T4 v2 protocol is drafted but NOT annotated.
- T1 recommends gold realism extension (Layer 2).
- V3.12 gold protocol (Layer 1 only) does not cover realism.
- Realism risk is concentrated in strong_action (9.0%), which is the high-risk class the paper claims to screen for.

**Implication:** the v2 two-layer gold pilot must be run before any external claim of "validated strong_action screening." Until gold is complete, all results are silver-stage directional support.

---

## Q8. Does the dataset need redesign?

**Verdict: NO.** SimClaim retains its diagnostic value.

- T3: realism risk below 25% threshold; safe as diagnostic set.
- T5: score collapse confirms the four-class design captures distinctions scalar loses.
- T2: low-prevalence simulation works on the existing 100 matched samples.
- T1: RIGOURATE proxy results align with V3.12 R4 results.

**Implication:** do NOT redesign SimClaim. Instead, (a) add realism gold validation; (b) state design attributes (templating, mechanical contradiction) as deliberate diagnostic design, not defects; (c) exclude extreme/templated cases from paper illustrative examples.

---

## Q9. Is downgrade to three-class fallback necessary?

**Verdict: NO — not at this stage.** Reserve as contingency.

- T5: scalar cannot separate mild/strong; this is evidence FOR the four-class decomposition, not against.
- T4 v2 pre-registered rule: "mild_vs_strong kappa < 0.40 -> taxonomy revision required." This rule has not fired; annotation has not begun.
- Three-class fallback (supported / overclaim / contradiction) would lose the high-risk strong_action class, which is the paper's central screening target.

**Implication:** keep four-class. If gold pilot returns mild_vs_strong kappa < 0.40 OR strong_action retention < 0.40 (T4 pre-registered rules), trigger taxonomy revision. Until then, three-class fallback is a documented contingency, not an active path.

---

## Summary table

| Question | Verdict | Revision required |
|---|---|---|
| Q1 Mainline valid? | YES | Mandatory qualifications (silver/gold, two-stage, proxy) |
| Q2 Strong_action screening positioning? | YES (first-stage filter, not standalone) | Reframe deployment claim |
| Q3 RIGOURATE fatal overlap? | NO | Position as complementary |
| Q4 Scalar weakens R4? | NO | Scalar strengthens four-class case |
| Q5 Low-prev supports deployment? | PARTIAL | Two-stage pipeline as future work |
| Q6 Realism risk severe? | NO (below 25%) | Realism gold needed; naturalistic caveat |
| Q7 Relation+realism gold mandatory? | YES | Run v2 pilot before external claims |
| Q8 Dataset redesign needed? | NO | Add realism gold; document design attributes |
| Q9 Three-class fallback? | NO (contingency only) | Reserve; trigger on kappa<0.40 |
"""

with open(os.path.join(OUT_DIR, "mainline_impact_summary.md"), "w", encoding="utf-8") as f:
    f.write(mainline_md)

# -----------------------------------------------------------------
# Section 3: evidence_strength_table.csv
# -----------------------------------------------------------------
evidence_rows = [
    {
        "paper_claim": "Fine-grained four-class relation typing captures distinctions lost by scalar severity.",
        "supporting_tasks": "T1; T5",
        "evidence_level": "strong",
        "safe_wording": "On silver SimClaim, the four-class decomposition isolates the mild-vs-strong boundary that scalar overstatement scores cannot recover (rule ROC-AUC=0.5062, llm ROC-AUC=0.5874).",
        "unsafe_wording": "Four-class typing is strictly superior to scalar severity (overgeneralised; gold pending).",
        "needs_gold": "true",
        "needs_revision": "true",
    },
    {
        "paper_claim": "strong_action_overclaim is a high-risk subclass worth isolating.",
        "supporting_tasks": "T1; T5",
        "evidence_level": "medium",
        "safe_wording": "On silver labels, strong_action_overclaim has measurable screening signal under R4 (strong_F1=0.3967 vs LLM 0.0769) and is the class scalar compression loses most.",
        "unsafe_wording": "strong_action_overclaim is conclusively the highest-risk class (gold validation pending).",
        "needs_gold": "true",
        "needs_revision": "true",
    },
    {
        "paper_claim": "R4 is a screening-oriented complement to LLM/NLI judges.",
        "supporting_tasks": "T1; T2; T5; V3_12",
        "evidence_level": "medium",
        "safe_wording": "R4 trades overall macro-F1 for targeted strong_action positive-F1 (silver: R4 strong_F1=0.3967 vs LLM 0.0769). R4 captures 8/24 LLM-missed strong_action on matched-100.",
        "unsafe_wording": "R4 is a deployment-ready screener (low-prevalence sim shows FP/TP=25-121 below 10%).",
        "needs_gold": "true",
        "needs_revision": "true",
    },
    {
        "paper_claim": "LLM judges under-detect strong_action under tested prompts.",
        "supporting_tasks": "T1; T2; V3_12",
        "evidence_level": "strong",
        "safe_wording": "Across three LLM judge variants on matched-100, strong_recall=0.04 and strong_F1=0.0769. At 1% prevalence LLMs show 99% accuracy but 4.3% recall (high-accuracy/low-recall failure mode).",
        "unsafe_wording": "LLMs cannot detect strong_action under any prompt (only tested prompts covered).",
        "needs_gold": "true",
        "needs_revision": "false",
    },
    {
        "paper_claim": "Scalar overstatement score is insufficient for strong_action screening.",
        "supporting_tasks": "T1; T5",
        "evidence_level": "strong",
        "safe_wording": "Rule_scalar ROC-AUC=0.5062 and llm_scalar ROC-AUC=0.5874 on mild-vs-strong; 4 score-collapse indicators; R4 F1=0.30 vs scalar F1=0.14 on matched-100. Scalar is a rule-based proxy; official RIGOURATE artifacts unavailable.",
        "unsafe_wording": "RIGOURATE is insufficient (proxy only; official system not tested).",
        "needs_gold": "true",
        "needs_revision": "true",
    },
    {
        "paper_claim": "SimClaim is a controlled counterfactual diagnostic set.",
        "supporting_tasks": "T3; V3_12",
        "evidence_level": "medium",
        "safe_wording": "444 pairs across 111 evidence groups and 6 domains; realism audit finds 4.7% overall risk, 9.0% for strong_action (below 25% threshold). Safe as diagnostic set; not naturalistic.",
        "unsafe_wording": "SimClaim is a representative scientific-claim benchmark (controlled counterfactual design).",
        "needs_gold": "true",
        "needs_revision": "true",
    },
    {
        "paper_claim": "SimClaim prevalence (25% strong_action) is non-natural.",
        "supporting_tasks": "T2; V3_12",
        "evidence_level": "strong",
        "safe_wording": "SimClaim's 25% strong_action prevalence is a deliberate design choice for diagnostic separability; natural-prevalence deployment requires prevalence-aware metrics.",
        "unsafe_wording": "SimClaim prevalence reflects natural scientific writing.",
        "needs_gold": "false",
        "needs_revision": "false",
    },
    {
        "paper_claim": "Realism validation is required before naturalistic claims.",
        "supporting_tasks": "T3; T4",
        "evidence_level": "medium",
        "safe_wording": "Automatic realism audit (4.7% overall, 9.0% strong_action) is heuristic; v2 two-layer gold protocol adds Layer 2 realism annotation. Gold realism pending.",
        "unsafe_wording": "Realism has been validated (only automatic audit done; human gold pending).",
        "needs_gold": "true",
        "needs_revision": "true",
    },
    {
        "paper_claim": "Low-prevalence screening utility justifies two-stage pipeline.",
        "supporting_tasks": "T2",
        "evidence_level": "planned",
        "safe_wording": "Low-prevalence simulation suggests R4 retains recall (~0.36) as first-stage filter; a two-stage pipeline (R4 -> LLM/human) is PROPOSED as future work and not evaluated in this paper.",
        "unsafe_wording": "Two-stage pipeline is validated (proposed only; not evaluated).",
        "needs_gold": "true",
        "needs_revision": "true",
    },
    {
        "paper_claim": "R4 macro-F1 < LLM macro-F1 is a deliberate trade-off.",
        "supporting_tasks": "V3_12; T1; T5",
        "evidence_level": "strong",
        "safe_wording": "On matched-100, R4 macro-F1=0.3280 < LLM 0.5523; R4 strong_F1=0.3967 > LLM 0.0769. The trade is intentional: R4 prioritises strong_action screening over overall accuracy.",
        "unsafe_wording": "R4 is overall better than LLM (only on strong_action, not macro).",
        "needs_gold": "true",
        "needs_revision": "false",
    },
]

with open(os.path.join(OUT_DIR, "evidence_strength_table.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(evidence_rows[0].keys()))
    w.writeheader()
    w.writerows(evidence_rows)

# -----------------------------------------------------------------
# Section 4: V3_16_revision_plan.md
# -----------------------------------------------------------------
revision_plan = f"""# V3.16 Revision Plan

**Date:** {TODAY}
**Status:** Plan only. NO paper modification. NO submission draft. NO experiments.
**Base version:** V3.12 With Three Credibility Checks (silver-stage draft).
**Synthesis inputs:** T1-T5 gates + V3.12 readiness gate + RIGOURATE related-work insert.

> This document specifies *what to change* in V3.16; it does NOT change the paper.
> All wording directions are advisory; final phrasing is the author's responsibility.

---

## 1. Abstract

**Current issue:** V3.12 abstract mentions three non-gold credibility checks but does not mention the RIGOURATE-style proxy baseline, the low-prevalence simulation, or the realism audit. The screening positioning implies standalone deployment.

**Needed change:**
- Add one sentence on RIGOURATE-style scalar proxy baseline (labelled as proxy).
- Add one sentence on low-prevalence screening simulation (frame R4 as first-stage filter).
- Add one sentence on realism audit + gold protocol v2.
- Replace any "screener" wording with "first-stage filter in a two-stage pipeline."

**Source evidence:** T1 gate (proxy); T2 gate (low-prev); T3 gate (realism); T4 gate (gold v2).

**Exact wording direction:**
> "We further construct a RIGOURATE-style scalar overstatement proxy baseline (official RIGOURATE artifacts unavailable as of 2026-07-05), and show that scalar severity cannot recover the mild-vs-strong_action boundary (ROC-AUC <= 0.59). A low-prevalence screening simulation (1%-25%) shows R4 retains stable recall (~0.36) but is not viable as a standalone screener below 10% prevalence; we propose a two-stage pipeline (R4 -> LLM/human) as future work. An automatic realism audit (4.7% overall risk, 9.0% for strong_action) motivates a two-layer gold protocol (relation + realism), pre-registered and pending annotation."

---

## 2. Introduction

**Current issue:** V3.12 introduction positions CESE-OCN as a four-class relation-typing framework with screening orientation, but does not explicitly contrast with scalar severity (RIGOURATE) or address the low-prevalence deployment gap.

**Needed change:**
- Add a paragraph explicitly contrasting relation typing (CESE-OCN) vs. scalar severity (RIGOURATE), citing T5 score-collapse findings.
- Reframe screening orientation as "first-stage high-recall filter" rather than "standalone screener."
- Mention that SimClaim is a controlled counterfactual diagnostic set, not a naturalistic corpus.

**Source evidence:** T5 gate (score collapse); T2 gate (low-prevalence); T3 gate (realism); RIGOURATE related-work insert (Section 4).

**Exact wording direction:**
> "Where RIGOURATE-style approaches produce a continuous scalar overstatement score, we decompose the same underlying phenomenon into a four-class relation taxonomy that isolates strong_action_overclaim as a separate high-risk boundary class. We show empirically (Section X) that scalar compression cannot recover this boundary (rule ROC-AUC = 0.5062; LLM-derived scalar ROC-AUC = 0.5874; mild/strong score-overlap ratio = 1.02). R4, our mixed relation-routing framework, is positioned as a first-stage high-recall filter in a two-stage pipeline, not a standalone deployment-ready screener."

---

## 3. Related Work

**Current issue:** V3.12 related work may not include RIGOURATE, ForceBench, CLAIM-BENCH (these were drafted in T1 docs but not yet inserted into the paper).

**Needed change:**
- Insert the four prepared paragraphs from `docs/rigourate_reproduction_and_simclaim_baseline_v1/rigourate_forcebench_claimbench_related_work_insert.md` (RIGOURATE, ForceBench, CLAIM-BENCH, CESE-OCN differentiation).
- Insert the comparison table (Section 5 of the insert).
- Cross-check against existing Related Work to avoid duplication.

**Source evidence:** T1 docs (paste-ready paragraphs); T5 results (scalar insufficiency).

**Exact wording direction:** Use the prepared paragraphs verbatim, with the placeholder citations [RIGOURATE: James et al., 2026], [ForceBench: ref 35], [CLAIM-BENCH: ref 28]. Add the reproducibility note about official RIGOURATE artifacts being unavailable.

---

## 4. Data

**Current issue:** V3.12 Data section describes SimClaim but does not include the realism audit results or the controlled-counterfactual design caveats.

**Needed change:**
- Add a paragraph on SimClaim as a controlled counterfactual diagnostic set (Section 6 of the related-work insert).
- Report realism audit headline numbers (0% high-risk; 4.7% overall; 9.0% strong_action).
- State explicitly that SimClaim is NOT a naturalistic corpus.
- Note that realism gold validation is part of the v2 gold protocol (pending).

**Source evidence:** T3 gate (realism audit); T4 gate (gold v2 Layer 2); RIGOURATE insert Section 6.

**Exact wording direction:**
> "SimClaim is a controlled counterfactual diagnostic set: 444 claim-evidence pairs across 111 evidence groups and 6 domains, with four generated claim variants per evidence group instantiating the four evidence-sufficiency relations. An automatic author-side realism audit (Section X) finds 4.7% overall realism risk and 9.0% for strong_action_overclaim — below the pre-registered 25% class-level threshold, but non-trivial. SimClaim is therefore safe as a diagnostic set but is NOT a naturalistic corpus. Human realism validation is included in the v2 gold protocol (Section VII) and is pending annotation."

---

## 5. Method

**Current issue:** V3.12 Method section describes R4 routing but does not explicitly state the screening-oriented trade-off (R4 macro-F1 < LLM macro-F1) or the two-stage pipeline framing.

**Needed change:**
- Add a paragraph stating the screening trade-off: R4 trades macro-F1 for strong_action positive-F1.
- Add a paragraph on the proposed two-stage pipeline (R4 -> LLM/human) as future deployment configuration.
- State frozen R4 thresholds (t_contra=0.48, t_strong=0.535, t_svm=0.51) explicitly.

**Source evidence:** V3.12 gate (numbers preserved); T2 gate (two-stage pipeline); T1 gate (R4 strong_F1 advantage).

**Exact wording direction:**
> "R4's routing is designed as a screening-oriented complement to LLM/NLI judges: it trades overall macro-F1 (R4 = 0.3280 vs LLM = 0.5523 on matched-100) for targeted strong_action positive-F1 (R4 = 0.3967 vs LLM = 0.0769). The frozen thresholds (t_contra=0.48, t_strong=0.535, t_svm=0.51) are not prevalence-aware; we therefore propose a two-stage deployment pipeline (R4 as first-stage high-recall filter, followed by LLM or human second-stage confirmation) as future work. This pipeline is not evaluated in the present paper."

---

## 6. Results

**Current issue:** V3.12 Results report R4/LLM numbers on SimClaim but do not include the RIGOURATE-style scalar baseline, the low-prevalence simulation, or the score-collapse analysis.

**Needed change:**
- Add a new subsection §VI.B (RIGOURATE-style scalar baseline results): 3 baselines, 4 binary tasks, 5-method comparison, case analysis.
- Add a new subsection §VI.C (Low-prevalence screening simulation): 7 prevalence levels, FP/TP, NNR, review burden, LLM high-accuracy/low-recall failure mode.
- Add a new subsection §VI.D (Scalar score-collapse analysis): 4 indicators, mild/strong overlap, contradiction vs strong mixing, supported false-positive rate.
- Preserve all V3.12 numbers byte-identical (0.3967, 0.0769, 0.3280, 0.5523, 0.2408, 0.2231).

**Source evidence:** T1 (baseline results); T2 (low-prev sim); T5 (score collapse).

**Exact wording direction:** Use the experimental numbers from T1/T2/T5 gates verbatim. Label scalar as "rule_scalar_score / llm_scalar_score", NOT "RIGOURATE". Mark all new results as "silver-stage, pre-gold."

---

## 7. Discussion

**Current issue:** V3.12 Discussion §VIII.A discusses R4 vs LLM macro-F1 trade-off and §VIII.D adds three credibility checks, but does not discuss the scalar-baseline complementarity or the low-prevalence deployment implication.

**Needed change:**
- Add a paragraph on scalar vs relation-specific screening complementarity (Section 7 of the related-work insert).
- Add a paragraph on the prevalence-dependence of R4's screening value (T2 findings).
- Add a paragraph on realism risk and the need for Layer-2 gold (T3 + T4).

**Source evidence:** T5 (scalar complementarity); T2 (prevalence dependence); T3+T4 (realism gold).

**Exact wording direction:**
> "The scalar-baseline comparison (Section VI.B) shows that continuous overstatement scores and four-class relation typing are complementary: scalar severity provides broad-coverage ranking, while relation typing isolates the action-vs-scope boundary that scalar compression loses. R4's screening value is prevalence-dependent: stable recall (~0.36) across 1%-25%, but precision drops sharply at low prevalence. Realism risk is non-trivial (9.0% for strong_action) and requires Layer-2 human gold validation before any naturalistic claim."

---

## 8. Limitations

**Current issue:** V3.12 Limitations has 8 items, including the non-gold caveat. It does not include the RIGOURATE proxy caveat, the low-prevalence simulation caveat, or the realism-audit-as-heuristic caveat.

**Needed change:** Add at least four new limitations items:
- §IX.9: RIGOURATE-style scalar baseline is a rule-based / LLM-label-derived proxy. Official RIGOURATE artifacts unavailable. Conclusions may shift if official system is released.
- §IX.10: Low-prevalence simulation uses heuristic 80/15/5 non-strong composition and 100 matched base samples. Absolute FP/TP values may shift with real natural-prevalence corpus.
- §IX.11: Two-stage pipeline (R4 -> LLM/human) is proposed but not evaluated.
- §IX.12: Realism audit is automatic/heuristic; not human gold. SimClaim is a controlled counterfactual diagnostic set, not a naturalistic corpus.

**Source evidence:** T1 (proxy caveat); T2 (simulation caveat + two-stage caveat); T3 (realism heuristic caveat).

**Exact wording direction:**
> "9. The RIGOURATE-style scalar baseline is a rule-based / LLM-label-derived proxy. Official RIGOURATE code, data, and model are unavailable as of 2026-07-05. Conclusions about scalar insufficiency may shift if the official system provides a stronger continuous score. 10. The low-prevalence simulation uses a heuristic 80/15/5 non-strong composition and 100 matched base samples; absolute FP/TP values may shift with a real natural-prevalence corpus. 11. The two-stage pipeline (R4 -> LLM/human) is proposed as future work and is not evaluated in this paper. 12. The realism audit is automatic and heuristic; it is not human gold. SimClaim is a controlled counterfactual diagnostic set, not a naturalistic corpus; naturalistic claims require a separate natural-prevalence corpus study."

---

## 9. Gold Protocol

**Current issue:** V3.12 §VII Pre-Registered Gold Validation Protocol is the v1 Layer-1-only protocol (FROZEN). The v2 two-layer protocol (relation + realism) has been drafted but is not yet reflected in the paper.

**Needed change:**
- DO NOT modify §VII (it is FROZEN as v1).
- Add a new §VII.G or §VII-bis: "Gold Protocol v2 (Relation + Realism) — DRAFT."
- Describe the two-layer independence (Layer 1 relation, Layer 2 realism).
- List the 9 realism_issue types and 5-point realism scale.
- List the 6 pre-registered decision rules (kappa<0.40, retention<0.40, realism_score<=2 rate>25%, etc.).
- State clearly that v2 is DRAFT, annotation NOT begun, and v1 remains FROZEN.

**Source evidence:** T4 gate (v2 protocol details, pre-registered rules, template details).

**Exact wording direction:**
> "Gold Protocol v2 extends v1 with an independent Layer 2 (realism) annotation: claim_realism_score_1_to_5, claim_realism_issue (9 types), realism_rationale_one_sentence, claim_usable_for_paper_example, needs_realism_adjudication. Layer 1 (relation) is carried over from v1 (FROZEN). Six pre-registered decision rules govern taxonomy revision, paper-claim downgrade, and realism downgrade. v2 is DRAFT; annotation has not begun. v1 remains FROZEN and is not modified. The 50-pair v2 pilot will determine whether the four-class taxonomy survives human annotation and whether SimClaim's realism is acceptable for paper use."

---

## Cross-cutting prohibitions for V3.16 drafting

- Do NOT write proxy as official RIGOURATE.
- Do NOT write silver as gold.
- Do NOT write planned two-stage pipeline as evaluated.
- Do NOT write simulation as natural-prevalence corpus study.
- Do NOT write realism audit as human gold.
- Do NOT modify V3.12 source files (create V3.16 as a new file).
- Do NOT change any experimental number from V3.12 (0.3967, 0.0769, 0.3280, 0.5523, 0.2408, 0.2231).
- Do NOT delete the "R4 macro-F1 < LLM macro-F1" fact.
- Do NOT delete the "gold not yet performed" fact.
"""

with open(os.path.join(OUT_DIR, "V3_16_revision_plan.md"), "w", encoding="utf-8") as f:
    f.write(revision_plan)

# -----------------------------------------------------------------
# Section 5: next_route_decision.md
# -----------------------------------------------------------------
route_md = f"""# Next Route Decision

**Date:** {TODAY}
**Status:** Decision support document. NO commitment. NO paper modification. NO experiments.

Three routes are evaluated. Each is scored on: applicable conditions, evidence needed, risks, pros, cons, recommended priority.

---

## Route A — Continue four-class + relation+realism gold

**Description:** Keep the four-class taxonomy (supported / mild_scope_overclaim / strong_action_overclaim / contradiction_candidate) as the central CESE-OCN claim. Run the v2 two-layer gold pilot (50 pairs). Apply pre-registered decision rules. Proceed to full 444-pair gold if pilot passes.

**Applicable conditions:**
- Gold pilot mild_vs_strong kappa >= 0.40.
- Strong_action retention >= 0.40.
- Class-level realism_score<=2 rate <= 25%.
- Paper-level realism_score<=2 rate <= 25%.
- Layer-2 Pearson r >= 0.40.

**Evidence needed:**
- v2 50-pair gold pilot results (Layer 1 + Layer 2 agreement).
- Re-evaluation of R4 / LLM / scalar on gold-validated subset.
- Re-run of low-prevalence simulation with gold labels.

**Risks:**
- If kappa < 0.40, taxonomy revision triggers; four-class claim collapses; paper must be substantially rewritten.
- If realism_score<=2 rate > 25% for strong_action, paper-claim downgrade triggers; strong_action screening positioning weakened.
- Time and annotator cost (estimated 4h per annotator + adjudication).
- v2 protocol is DRAFT; annotators untrained on Layer 2; agreement untested.

**Pros:**
- Maintains the strongest paper claim (four-class + strong_action isolation).
- T5 already shows scalar cannot replace four-class; gold validation locks in this finding.
- T4 v2 protocol is drafted, silver-leakage-free, ready for annotation.
- Most aligned with V3.12's existing structure; minimal rewriting.

**Cons:**
- Highest annotation cost.
- Highest risk of pre-registered downgrade triggers.
- Longest timeline to advisor-ready draft.

**Recommended priority: 1 (PRIMARY).** The evidence from T1-T5 supports the four-class claim; the pre-registered rules provide a graceful degradation path; the v2 protocol is ready. This is the highest-expected-value route.

---

## Route B — Keep four-class diagnostic set, but main paper focus on strong_action screening

**Description:** Retain the four-class SimClaim design (for diagnostic separability) but reframe the paper's central claim around strong_action screening specifically. Mild vs strong becomes a *secondary* diagnostic axis, not the primary paper claim. Gold pilot still runs Layer 1 + Layer 2 but the paper's headline metric is strong_action screening (F1, FP/TP, NNR).

**Applicable conditions:**
- Gold pilot shows strong_action retention >= 0.40 (strong label reliable).
- Mild vs strong kappa is borderline (0.30-0.40) — taxonomy revision triggers but strong_action is salvageable as a binary high-risk class.
- Author wants a tighter, more defensible paper claim.

**Evidence needed:**
- v2 50-pair gold pilot results.
- Re-evaluation of R4 / LLM / scalar on strong-vs-non-strong binary task.
- Low-prevalence simulation on gold-validated strong_action labels.

**Risks:**
- Loses the fine-grained four-class typing claim — weakens differentiation from RIGOURATE / ForceBench.
- May complicate §VII gold protocol (Layer 1 becomes secondary).
- Risks reviewer pushback ("why four classes if you only use strong_action?").

**Pros:**
- Stronger paper claim (binary strong_action screening is more defensible than four-class typing).
- Lower annotation cost (gold pilot can focus on strong_action reliability).
- Better aligned with T2 low-prevalence findings (screening is the practical value).
- Faster path to advisor-ready draft.

**Cons:**
- Wastes the four-class diagnostic design (T5 score-collapse evidence becomes secondary).
- Reduces paper novelty vs. RIGOURATE (which already covers severity screening).
- May require SimClaim redesign to add more strong_action variants.

**Recommended priority: 2 (FALLBACK).** Adopt if Route A's gold pilot returns borderline kappa (0.30-0.40) or strong_action retention >= 0.40 but mild-strong is unstable.

---

## Route C — Downgrade to three-class (supported / overclaim / contradiction), strong_action as overclaim subtype

**Description:** Collapse mild_scope_overclaim and strong_action_overclaim into a single "overclaim" class. strong_action becomes a *subtype tag* within overclaim, not a separate class. Reduces the taxonomy to three classes plus a subtype annotation.

**Applicable conditions:**
- Gold pilot returns mild_vs_strong kappa < 0.40 (taxonomy revision triggers per T4 pre-registered rule).
- Strong_action retention < 0.40 (paper-claim downgrade triggers).
- Author accepts loss of strong_action as a first-class label.

**Evidence needed:**
- v2 gold pilot results showing kappa < 0.40.
- Re-tagging of SimClaim with three-class labels + strong_action subtype.
- Re-evaluation of R4 / LLM / scalar on three-class task.

**Risks:**
- Loses the central paper claim (strong_action isolation).
- T5 evidence (scalar cannot separate mild/strong) becomes a *limitation*, not a *contribution*.
- Substantial paper rewrite required.
- Reviewer pushback ("why did you build a four-class set if you downgraded to three?").
- May invalidate the RIGOURATE differentiation argument (T1, T5).

**Pros:**
- Lower annotation cost (three-class is easier).
- Cleaner agreement statistics (fewer boundary classes).
- More defensible if kappa is genuinely too low.

**Cons:**
- Contradicts T5 empirical evidence (four-class captures distinctions scalar loses).
- Wastes the entire V3.12 / SimClaim design effort.
- Loses the screening-oriented positioning (no separate strong_action class to screen for).
- Reduces paper to a less novel three-class overclaim detector.

**Recommended priority: 3 (CONTINGENCY).** Adopt ONLY if Route A's gold pilot triggers both taxonomy-revision AND paper-claim-downgrade rules. Do NOT pre-emptively choose this route.

---

## Summary recommendation

| Route | Priority | Trigger condition | Expected timeline | Risk |
|---|---|---|---|---|
| A (four-class + gold) | PRIMARY | default | longest | highest (kappa, realism) |
| B (strong_action focus) | FALLBACK | borderline kappa, strong retention OK | medium | medium |
| C (three-class) | CONTINGENCY | kappa<0.40 AND retention<0.40 | shortest (rewrite) | highest (loses main claim) |

**Default action:** Proceed with Route A. Run v2 50-pair gold pilot. Apply pre-registered decision rules. Reassess at pilot completion.
"""

with open(os.path.join(OUT_DIR, "next_route_decision.md"), "w", encoding="utf-8") as f:
    f.write(route_md)

# -----------------------------------------------------------------
# Section 6: v3_16_integration_gate.json
# -----------------------------------------------------------------
gate = {
    "gate_name": "v3_16_integration_gate",
    "task": "V3.16 Five-Task Integration Summary + Revision Plan",
    "date": TODAY,
    "output_directory": "D:\\ocn\\project_synthesis\\v3_16_integration_summary_and_revision_plan\\",
    "mainline_survives": True,
    "needs_dataset_redesign": False,
    "needs_relation_realism_gold": True,
    "rigourate_overlap_fatal": False,
    "scalar_baseline_weakens_r4": False,
    "r4_retains_strong_action_advantage": True,
    "low_prevalence_supports_standalone_deployment": False,
    "low_prevalence_supports_first_stage_filter": True,
    "realism_risk_severe": False,
    "three_class_fallback_needed_now": False,
    "v3_16_revision_required": True,
    "v3_16_revision_scope": "Insertion-only on top of V3.12; preserve all V3.12 numbers; add RIGOURATE proxy baseline section, low-prevalence simulation section, realism audit + gold v2 protocol; reframe R4 as first-stage filter; add 4 new Limitations items.",
    "default_route": "A (four-class + relation+realism gold)",
    "fallback_route": "B (strong_action screening focus) if gold kappa borderline",
    "contingency_route": "C (three-class downgrade) if kappa<0.40 AND retention<0.40",
    "supporting_evidence": {
        "t1_rigourate_proxy": {
            "scalar_cannot_replace_r4": True,
            "official_rigourate_available": False,
            "r4_strong_f1_silver": 0.3967,
            "scalar_best_f1_silver": 0.3844,
            "llm_missed_strong_captured_by_r4": 8,
        },
        "t2_low_prevalence": {
            "r4_recall_stable_across_prevalences": True,
            "r4_recall_mean": 0.36,
            "r4_viable_standalone_below_10pct": False,
            "r4_viable_standalone_at_25pct": True,
            "fp_tp_at_1pct": 121.0,
            "fp_tp_at_10pct": 11.5,
            "fp_tp_at_25pct": 3.8,
            "two_stage_pipeline_evaluated": False,
        },
        "t3_realism_audit": {
            "high_risk_claim_rate": 0.0,
            "overall_realism_risk": 0.047,
            "strong_action_realism_risk": 0.09,
            "safe_as_diagnostic_set": True,
            "safe_as_naturalistic": False,
            "audit_is_human_gold": False,
        },
        "t4_gold_v2_protocol": {
            "protocol_drafted": True,
            "annotation_begun": False,
            "v1_modified": False,
            "silver_leakage_free": True,
            "pre_registered_rules_count": 6,
            "ready_for_blind_annotation": True,
        },
        "t5_scalar_deep_test": {
            "scalar_can_separate_mild_strong": False,
            "rule_scalar_roc_auc": 0.5062,
            "llm_scalar_roc_auc": 0.5874,
            "score_collapse_observed": True,
            "score_collapse_indicators_count": 4,
            "r4_strong_f1_matched_100": 0.30,
            "scalar_strong_f1_matched_100": 0.1364,
            "r4_llm_missed_captured": 8,
            "scalar_llm_missed_captured": 3,
        },
    },
    "revision_plan_sections": [
        "Abstract", "Introduction", "Related Work", "Data", "Method",
        "Results", "Discussion", "Limitations", "Gold Protocol"
    ],
    "prohibitions_enforced": {
        "no_experiments": True,
        "no_api_calls": True,
        "no_gold_annotation": True,
        "no_paper_modification": True,
        "no_original_data_modification": True,
        "no_submission_draft": True,
        "no_planned_as_completed": True,
        "no_silver_as_gold": True,
        "no_proxy_as_official_rigourate": True,
    },
    "audit_disclaimer": (
        "This is an integration summary and revision plan only. "
        "It does NOT modify the paper, does NOT generate a submission draft, "
        "does NOT run experiments, and does NOT create gold. "
        "All evidence is drawn from existing T1-T5 gate files and V3.12 readiness gate. "
        "All scalar baseline results are PROXY (rule-based / LLM-label-derived), NOT official RIGOURATE. "
        "All R4 / LLM / scalar results are on SILVER labels (pre-gold). "
        "The two-stage pipeline (R4 -> LLM/human) is PROPOSED, not evaluated."
    ),
}

with open(os.path.join(OUT_DIR, "v3_16_integration_gate.json"), "w", encoding="utf-8") as f:
    json.dump(gate, f, indent=2, ensure_ascii=False)

# -----------------------------------------------------------------
# Done.
# -----------------------------------------------------------------
print("=== V3.16 Integration Summary generated ===")
print(f"Output directory: {OUT_DIR}")
print("Files generated:")
for fn in [
    "five_task_status_matrix.csv",
    "mainline_impact_summary.md",
    "evidence_strength_table.csv",
    "V3_16_revision_plan.md",
    "next_route_decision.md",
    "v3_16_integration_gate.json",
]:
    p = os.path.join(OUT_DIR, fn)
    print(f"  - {fn} ({os.path.getsize(p)} bytes)")
