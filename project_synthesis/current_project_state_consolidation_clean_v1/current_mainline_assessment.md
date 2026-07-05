# Current Mainline Assessment

> **REALIGNMENT BANNER (2026-07-05):** This assessment has been superseded by `D:\ocn\project_synthesis\mainline_realignment_v1\updated_project_mainline_summary.md`. The current mainline is the **V3.17 baseline offline PDF-corpus evidence-sufficiency screening framework**: PDF corpus → BM25 top-k → `best_sentence_top5_overlap` canonicalization → restored R4 (10 seeds, per-seed thresholds) → `G_conservative_precision` ranking → second-stage review queue. V3.15 hierarchical taxonomy is retained as paper-level interpretation only. V3.18 intelligent upgrade is an exploratory negative ablation (not selected). The V3.15-era content below is retained for traceability.

**Date:** 2026-07-05
**Assessment based on (historical):** V3.15 hierarchical taxonomy revision + V3.16 integration gate + overnight pipeline + all recent task gates
**Superseded by (current):** V3.17 baseline + V3.18 intelligent upgrade negative result; see `mainline_realignment_v1/`

## 1. What is the current mainline? (UPDATED)

The current mainline is the **offline PDF-corpus evidence-sufficiency screening framework**:

```
PDF corpus → BM25 top-k retrieval → evidence canonicalization (best_sentence_top5_overlap)
  → CESE-OCN / R4 relation-specific screening (restored R4, 10 seeds, per-seed thresholds, majority vote)
  → risk ranking (G_conservative_precision) → second-stage human review queue
```

This mainline is offline, auditable, and second-stage. V3.17 baseline is the selected method (strong_F1=0.4503, P@20=0.45, R@100=0.3303, FP/TP@5%=11.24). V3.18 intelligent upgrade attempted learned selector + ranker and did NOT improve (negative ablation). The hierarchical diagnostic taxonomy (V3.15) is retained as paper-level interpretation; it is NOT the empirical mainline. The original V3.15-era content follows below.

---

## Historical V3.15-era Assessment (Retained for Traceability)

The current mainline is **CESE-OCN R4**: a relation-specific screening router under the hierarchical diagnostic taxonomy, targeting Level-2 high-risk strong_action overclaim screening as a complement to LLM judges. The mainline is anchored on the SimClaim controlled counterfactual diagnostic set (444 silver pairs, 111 groups, 6 domains) and the pre-registered §VII gold adjudication protocol (Layer 1 relation + Layer 2 realism, DRAFT, annotation NOT begun).

## 2. Is the mainline still flat 4-class?

**No.** As of V3.15, the mainline has transitioned from a flat four-class taxonomy to a **hierarchical diagnostic taxonomy**:
- **Level 1:** supported / overclaim / contradiction
- **Level 2 (under overclaim):** scope_expansion (= mild_scope_overclaim) / strong_action (= strong_action_overclaim)

The four operational labels (supported, mild_scope_overclaim, strong_action_overclaim, contradiction_candidate) remain the experimental label space, but their interpretation is hierarchical. `mild_scope_overclaim` is explicitly a boundary-sensitive buffer subtype, NOT a naturally stable discrete class.

## 3. Has it transitioned to hierarchical diagnostic taxonomy?

**Yes.** V3.15 (the current recommended paper version) implements the hierarchical taxonomy via 18 targeted string replacements across 9 sections. Key markers:
- Abstract reframed ("we operationalize a hierarchical diagnostic taxonomy")
- §I contribution 1 reframed as "Hierarchical diagnostic taxonomy"
- §III.A adds Table 0a (Level 1 / Level 2 mapping)
- §IV.A reframes R4 as "relation-specific screening router under the hierarchical taxonomy"
- §VIII.G (NEW) "Why the Taxonomy Is Hierarchical Rather Than Flat"
- §VII.K (NEW) hierarchical gold validation plan with pre-registered fallback rules
- §X Conclusion reframed hierarchically

The readiness gate confirms: `hierarchical_taxonomy_inserted=true`, `flat_four_class_deemphasized=true`, `fallback_to_3class_plus_binary_defined=true`.

## 4. Is three-class + strong_action binary the mainline or fallback?

**It is the FALLBACK, not the primary mainline.** The primary mainline is the hierarchical taxonomy (Level 1 + Level 2). The three-class + binary strong_action screening is the pre-registered fallback (§VII.K rule 3.1) that activates IF gold adjudication shows Level-2 κ < 0.40 (mild_vs_strong boundary not reliably drawable). This fallback design is what reduces the "forced four-class" reviewer risk: the paper does not force four classes; it has a graceful-degradation path to three classes + binary screening.

## 5. How should SimClaim be defined currently?

SimClaim is a **controlled counterfactual diagnostic set**:
- 444 silver claim-evidence pairs, 111 groups, 6 domains, balanced 1:1:1:1 across the four operational labels
- Uses real evidence spans and generated claim variants to pressure-test boundary recognition under matched evidence
- **NOT a natural-prevalence corpus** — the balanced design is deliberate for diagnostic pressure-testing, not an estimate of real-world prevalence
- **NOT a naturalistic corpus** — generated claim variants have template risk (76/111 groups high-risk tier, design attribute); realism audit (§VII.J Layer 2) pending
- Silver labels pending §VII gold adjudication
- `safe_as_diagnostic_set=true`, `safe_as_naturalistic=false`

## 6. How should R4 be defined currently?

R4 is a **relation-specific screening router under the hierarchical taxonomy**:
- Three routes map onto hierarchical levels: contradiction gate (Level 1), scope residual classifier (Level 1 supported vs. Level 2 scope_expansion), strong_action route (Level 2 high-risk screening)
- **NOT a flat 4-class best classifier** — R4's macro_F1 (0.3280) is lower than LLM (0.5523)
- **Core value: Level-2 high-risk strong_action screening** — R4 strong_F1=0.3967 (silver 444), 0.3000 (matched 100); strong_recall=0.4562 (silver), 0.36 (matched); R4 captures 8 LLM-missed strong cases
- Positioned as a screening-oriented complement to LLM judges, NOT a competitive replacement
- Frozen thresholds: t_contra=0.48, t_strong=0.535, t_svm=0.51
- High false positive rate (26 FP / 35 strong predictions, fp_rate=0.7429) concentrated in mild→strong boundary — R4 is a high-recall first-stage filter, not a precision classifier

## 7. Is the RIGOURATE/ForceBench/CLAIM-BENCH homogenization risk controllable?

**Yes, controllable.** The V3.16 integration gate confirms `rigourate_overlap_fatal=false`. Key differentiators:
- **vs. RIGOURATE:** RIGOURATE uses scalar overstatement scoring on natural author-written claims; CESE-OCN uses hierarchical relation-typed screening on controlled counterfactual claim variants. Official RIGOURATE code/data/model NOT available (blocked); proxy scalar baseline cannot distinguish mild vs strong (ROC-AUC=0.5062).
- **vs. ForceBench:** ForceBench uses contrastive paired-claim force testing; CESE-OCN uses single-claim evidence-sufficiency calibration with relation typing.
- **vs. CLAIM-BENCH:** CLAIM-BENCH does full-paper claim-evidence extraction; CESE-OCN focuses on evidence-sufficiency calibration at the span level.
- §II.A positioning paragraph + Table X explicitly differentiate CESE-OCN from all three.

## 8. Biggest data credibility risk

**SimClaim is counterfactual, not natural-prevalence.** The balanced four-way design (111 per class) is a deliberate construction for diagnostic pressure-testing, NOT an estimate of real-world prevalence. In natural scientific corpora, `contradiction_candidate` and `strong_action_overclaim` are expected to be substantially rarer. Template risk is high (76/111 groups) but is a design attribute, not a defect. The §VII.J two-layer gold protocol includes a realism audit (Layer 2: `claim_realism_score_1_to_5`) to assess natural-claim transferability, but this has NOT been executed yet.

**Secondary data risk:** All labels are silver (AI-preannotated development labels). The §V.D author sanity audit flagged 25/40 (62.5%) of audited silver labels as questionable or unclear, with strong_action at 75% confusion. Gold adjudication is the only mechanism that can resolve this.

## 9. Biggest method credibility risk

**R4 macro_F1 < LLM.** R4's overall macro_F1 (0.3280) is substantially lower than GPT-5.5 (0.5523) and DeepSeek-V3 (0.5270) on matched 100 samples. The paper does NOT claim R4 overall beats LLM — it claims R4 provides targeted Level-2 strong_action screening signal at the cost of lower overall macro_F1. This is a defensible but narrow claim: if gold adjudication shows strong_action is not reliably drawable (Level-2 κ < 0.40), R4's screening value downgrades to exploratory status per §VII.K fallback rule 3.3.

**Secondary method risk:** R4 high false positive rate (fp_rate=0.7429). R4 over-routes mild→strong and contradiction→strong. This is the cost of higher recall (0.36 vs LLM 0.04); the two-stage pipeline (R4 first-stage + LLM second-stage) is motivated but NOT evaluated end-to-end.

## 10. What is the most necessary next action?

**Execute the §VII 50-pair two-layer gold pilot** (Layer 1 relation label + Layer 2 realism score) using the frozen `gold_pilot_protocol_freeze_v1` package and the v2 relation+realism protocol (`gold_pilot_relation_realism_protocol_v2`). Specifically:
1. Execute blind annotation A and B (50 pairs each)
2. Adjudicate disagreements
3. Compute Level-1 κ (supported / overclaim / contradiction) — threshold ≥ 0.50
4. Compute Level-2 κ (scope_expansion vs. strong_action, conditional on overclaim) — threshold ≥ 0.40
5. Compute strong_action retention rate — threshold ≥ 0.60 (retain) / < 0.50 (exploratory)
6. Apply §VII.K fallback rules to determine whether to retain hierarchical taxonomy or fall back to Level-1 three-class + binary strong_action screening
7. Insert gold results into Tables G1–G3 without restructuring the paper

This is the single most decisive action for the project: it determines whether the four-class hierarchical taxonomy is validated, downgraded to three-class + binary screening, or downgraded to exploratory status.
