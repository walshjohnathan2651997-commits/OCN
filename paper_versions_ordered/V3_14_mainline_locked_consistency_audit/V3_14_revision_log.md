# V3.14 Revision Log — Mainline Locked + Reviewer-Grade Consistency Audit

**From:** V3.13 RIGOURATE-Differentiated + Realism-Aware
**To:** V3.14 Mainline Locked + Reviewer-Grade Consistency Audit
**Date:** 2026-07-05
**Output directory:** `D:\ocn\paper_versions_ordered\V3_14_mainline_locked_consistency_audit\`

---

## 1. Chapters modified

| Section | Change type | Details |
| --- | --- | --- |
| Header (Version/Date) | Updated | Version: V3.13 RIGOURATE-Aware → V3.14 Mainline Locked + Reviewer-Grade Consistency Audit; Date: 2026-07-05 |
| Header (Changes block) | Added | New "Changes from V3.13 RIGOURATE-Differentiated + Realism-Aware (this V3.14 release)" paragraph documenting 7 wording/ordering-level changes |
| Header (Mainline lock) | Added | New "Mainline lock (this version)" paragraph |
| §II.B (NEW) | Added | "Mainline Lock Declaration" subsection before §III, with the required mainline-lock statement and 9 binding commitments for pre-gold revisions |
| §VII.J | Enhanced | Layer 1 now references the frozen `gold_pilot_protocol_freeze_v1` package (2026-07-04, PROTOCOL FROZEN, annotation NOT begun); Layer 2 wording aligned |
| §VIII.D opening | Enhanced | "These checks are non-gold robustness analyses." → "These checks are non-gold robustness analyses that strengthen but do not validate." |

**No other section was modified.** §I, §II.A, §III–§VII (except §VII.J), §VIII.A–§VIII.C, §VIII.E, §IX, §X, Appendix A, Appendix B are byte-identical to V3.13 RIGOURATE-Aware.

---

## 2. Wording down-toned

| Location | Original (V3.13) | Revised (V3.14) | Rationale |
| --- | --- | --- | --- |
| §VIII.D opening | "These checks are non-gold robustness analyses." | "These checks are non-gold robustness analyses that strengthen but do not validate." | Reinforce that non-gold checks do not validate; reviewer-grade consistency |
| §VII.J opening | (no reference to gold_pilot_protocol_freeze_v1) | Added: "Layer 1 (relation label) is operationalised by the frozen `gold_pilot_protocol_freeze_v1` package... (2026-07-04, status: PROTOCOL FROZEN, annotation NOT begun)" | Align §VII.J with the actual frozen protocol package; make "planned, not completed" status explicit |

**No experimental number was changed. No over-strong claim in §VI.A–§VI.D, §VIII.D, §IX was left un-toned.** The V3.13 RIGOURATE-Aware text was already heavily down-toned; V3.14 only adds two reinforcements.

---

## 3. Claims preserved (NOT changed, NOT deleted)

| Claim | Section | Why preserved |
| --- | --- | --- |
| R4 macro-F1 = 0.3280 < LLM 0.5523 | §VI.B, §VIII.A, §IX item 4 | Required by mainline lock; forbidden to delete |
| R4 strong_F1 = 0.3967 (silver 444); 0.3000 (matched 100) | §VI.A, §VI.B | Core result; no number change |
| LLM strong_F1 = 0.0769 (matched 100) | §VI.B | Core result; no number change |
| Gold not done; all labels silver | §VII, §IX item 1-3 | Required by mainline lock; forbidden to delete |
| SimClaim is counterfactual, not natural-prevalence | §V.A, §IX item 10 | Required by mainline lock; forbidden to delete |
| R4 is screening-oriented complement, not replacement | §I, §II.B, §VI.B, §VIII.A, §IX item 4 | Core positioning; no change |
| RIGOURATE-style proxy is NOT official RIGOURATE | §VI.E, §IX item 11 | Required by mainline lock; forbidden to promote |
| nli_scalar_score is BLOCKED with blocked_reason | §VI.E, §IX item 11 | Required by mainline lock; forbidden to promote |
| Three non-gold checks (§VIII.D) do not replace gold | §VIII.D | Required by mainline lock; reinforced in V3.14 |
| Two-layer gold protocol (§VII.J) is planned, not completed | §VII.J | Required by mainline lock; reinforced in V3.14 |
| 62.5% author sanity audit flag rate | §VIII.C | Honest disclosure; no change |
| 25/40 questionable/unclear audit cases | §VIII.C | Honest disclosure; no change |

---

## 4. Claims forbidden (must NOT appear in V3.14 or any future pre-gold revision)

| Forbidden claim | Rationale |
| --- | --- |
| "First scientific overstatement benchmark" | RIGOURATE [30] is prior art |
| "First evidence-force calibration benchmark" | ForceBench [35] is prior art |
| "First scientific claim-evidence extraction benchmark" | CLAIM-BENCH [28] is prior art |
| "First to propose evidence sufficiency calibration" | RIGOURATE [30] and evidence-licensed claims [31] are prior art |
| "We introduce scientific overstatement detection as a new field" | RIGOURATE [30] already does this |
| "SimClaim is a natural-prevalence corpus" | §V.A explicitly states it is counterfactual |
| "SimClaim estimates real-world prevalence" | §V.A explicitly states it does not |
| "SimClaim claims are natural author-written claims" | §V.A explicitly states they are generated variants |
| "Gold validated" / "Validated taxonomy" | Gold annotation has NOT begun |
| "Our labels are gold / human-audited" | All 444 labels are silver |
| "R4 outperforms LLM overall" / "R4 beats LLM" | R4 macro-F1 = 0.3280 < LLM 0.5523 |
| "R4 is the best model" | Misleading; R4 is screening-oriented complement |
| "R4 has high recall on strong_action" | recall = 0.36 is not high in absolute terms |
| "Official RIGOURATE reproduced" | Official code/data/model not publicly available |
| "The RIGOURATE-style proxy is the official RIGOURATE system" | Proxy is explicitly labelled as proxy |
| "The blocked nli_scalar_score baseline was completed" | BLOCKED with blocked_reason |
| "CESE-OCN outperforms RIGOURATE / ForceBench / CLAIM-BENCH" | Differentiation is positioning-level, not head-to-head |
| "The silver-stage screening finding transfers to natural scientific writing" | Realism audit pending; transferability not claimed |
| "Proves LLMs cannot detect strong_action" / "Systematic blind spot" | Finding is prompt/model/sample-specific and silver-stage |
| "Submission-ready / final benchmark complete" | Gold validation pending |

---

## 5. Unresolved risks

| Risk | Severity | Mitigation |
| --- | --- | --- |
| Gold adjudication may reveal mild_vs_strong κ < 0.40 | HIGH | §VII.G pre-registered downgrade criterion: taxonomy revised (strong_action merged with mild) |
| Gold strong_action retention may be < 0.50 | HIGH | §VII.G pre-registered downgrade criterion: screening claim downgraded |
| Realism audit may reveal > 25% of strong_action claims unrealistic | MEDIUM | §VII.J pre-registered realism threshold: realism caveat added; screening claim limited to diagnostic-stage |
| Official RIGOURATE release may weaken §VI.E proxy finding | MEDIUM | Proxy is explicitly labelled; transferability not claimed; §VI.E is on SimClaim, not RIGOURATE's natural-claim corpus |
| R4 over-routing (supported → strong: 98 FP; mild → strong: 24 FP) | MEDIUM | §IX item 5 lists as limitation; R5 future work should target lower FP/TP |
| LLM under-detection is prompt/model/sample-specific | MEDIUM | §IX item 3 lists as limitation; "under tested prompts" qualifier used throughout |
| SimClaim 6 domains may not generalise | LOW | §IX item 7 lists as limitation; cross-domain generalisation not confirmed |
| Single-run LLM comparison (no variance estimate) | LOW | §IX additional practical limitation (b) lists this |

---

## 6. Should the next step be relation+realism gold protocol?

**YES — strongly recommended.**

**Rationale:**
1. The mainline is locked (§II.B). The framework, taxonomy, frozen R4 method, RIGOURATE-style proxy baseline, two-layer gold protocol, and three non-gold credibility checks are all in place. The only remaining validation step is gold adjudication.
2. The gold pilot protocol is frozen (`gold_pilot_protocol_freeze_v1`, 2026-07-04). The annotation guideline, decision tree, boundary rules, 20 worked examples, annotator training packet, two blind annotation templates (A and B with silver excluded), adjudication protocol, and agreement metric plan are all generated and ready to send to two independent annotators.
3. The §VII.J two-layer gold protocol extends Layer 1 with Layer 2 realism fields (`claim_realism_score_1_to_5`, `claim_realism_issue`, `claim_realism_usable_for_paper`). The 25% class-level and 25% paper-level realism thresholds are pre-registered.
4. The §VII.G downgrade criteria are pre-registered and frozen. Gold results will be inserted into Tables G1-G3 without restructuring the paper; if criteria fail, the paper downgrades per the pre-registered mechanism.
5. No further pre-gold revision is needed. V3.14 is the mainline-locked version ready for gold protocol execution.

**Recommended next action (5-step sequence):**
1. Send the frozen `gold_pilot_protocol_freeze_v1` package (plus §VII.J Layer 2 realism fields) to two independent annotators.
2. Run the 50-sample gold pilot under the two-layer protocol (Layer 1 relation label + Layer 2 claim realism).
3. Adjudicate disagreements and compute Cohen's κ / Krippendorff's α per class and per boundary.
4. Insert gold results into Tables G1-G3 and check against §VII.G downgrade criteria and §VII.J realism thresholds.
5. If gold pilot passes (mild_vs_strong κ ≥ 0.40, strong_action retention ≥ 0.50, realism thresholds not breached), prepare V3.15 with gold results and consider submission; if gold pilot fails, downgrade per §VII.G and §VII.J.

---

## 7. Prohibitions verified (all PASS)

| Prohibition | Status |
| --- | --- |
| No new experiments | PASS |
| No API calls | PASS |
| No gold annotation | PASS |
| No original data modification | PASS |
| No V3.13 modification | PASS (V3.13 file untouched) |
| No new research direction | PASS |
| No planned baseline written as completed | PASS |
| No silver written as gold | PASS |
| No synthetic claim written as natural | PASS |
| No advisor note generated | PASS (per task spec §9 禁止) |

---

## 8. File inventory (V3.14 output directory)

| File | Type | Purpose |
| --- | --- | --- |
| CESE_OCN_V3_14_mainline_locked.md | Main draft | V3.14 mainline-locked paper |
| CESE_OCN_V3_14_mainline_locked.docx | Main draft (docx) | Word export |
| claim_validity_matrix.csv | Audit | 10 core claims audited |
| homogenization_risk_audit.md | Audit | 7 reviewer-grade Q&A on RIGOURATE/ForceBench/CLAIM-BENCH overlap |
| dataset_construction_risk_audit.md | Audit | 7 data-construction risks + paste-ready English Data Limitation paragraph |
| r4_method_positioning_audit.md | Audit | 6 reviewer-grade Q&A on R4 method |
| V3_14_mainline_gate.json | Gate | 15 gate fields + prohibitions + quality checks + file inventory |
| V3_14_revision_log.md | Log | This file |
