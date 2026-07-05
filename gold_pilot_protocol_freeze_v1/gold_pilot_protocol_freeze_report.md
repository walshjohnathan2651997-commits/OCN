# Gold Pilot Protocol Freeze Report v1

**Date:** 2026-07-04
**Status:** PROTOCOL FROZEN. Annotation has NOT begun.
**Output directory:** `D:\ocn\gold_pilot_protocol_freeze_v1\`

---

## 0. Summary

The gold pilot annotation protocol is now **frozen**. All 10 required output files have been generated. The protocol is ready to be sent to two independent annotators. **No actual annotation has been performed.** No `gold_label`, `final_label`, or `human_audited` fields have been filled. No models have been run. No APIs have been called. No original data has been modified.

---

## 1. Can This Be Sent to Two Annotators?

**Yes.** The protocol is self-contained and includes:
- Frozen label definitions (`annotation_guideline_v1_frozen.md`)
- Frozen decision tree (`annotation_decision_tree_v1.md`)
- 20 worked positive/negative examples (`label_positive_negative_examples.csv`)
- 6 boundary rules (`boundary_rules_v1.md`)
- Annotator training packet (`annotator_training_packet.md`)
- Blind annotation templates A and B (`pilot_50_blind_annotation_A.csv`, `pilot_50_blind_annotation_B.csv`)
- Adjudication protocol (`adjudication_protocol_v1.md`)
- Agreement metric plan (`agreement_metric_plan_v1.md`)

Annotator A receives: training packet + guideline + decision tree + boundary rules + examples + blind template A.
Annotator B receives: the same materials + blind template B.
The adjudicator receives: adjudication protocol + agreement metric plan (after both annotators submit).

---

## 2. Are Silver Labels Hidden?

**Yes.** The blind annotation templates (`pilot_50_blind_annotation_A.csv` and `pilot_50_blind_annotation_B.csv`) contain ONLY these columns:
- `pilot_id`, `candidate_id`, `domain`, `evidence_text`, `claim_text`
- `annotator_label` (empty), `confidence_1_to_5` (empty), `rationale_one_sentence` (empty), `confusion_if_any` (empty), `needs_adjudication` (empty)

The following columns from the original `gold_pilot_candidate_50.csv` have been **excluded** from the blind templates:
- `silver_label_hidden_or_visible` — EXCLUDED
- `sample_source` — EXCLUDED
- `boundary_type` — EXCLUDED
- `why_selected` — EXCLUDED
- `do_not_use_as_gold_yet` — EXCLUDED

Verification: The generation script (`build_gold_pilot_protocol_freeze_v1.py`) explicitly checks that no excluded field leaks into the blind template headers. Output: "Header OK" for both A and B, 0 silver_leaked.

The adjudicator's default policy is also to NOT look at silver labels during adjudication (see `adjudication_protocol_v1.md` §4). Silver labels may only be compared to gold AFTER adjudication is complete, for analysis purposes.

---

## 3. Are Positive/Negative Examples Included?

**Yes.** `label_positive_negative_examples.csv` contains 20 worked examples:
- 3 positive + 2 negative/near-miss per class × 4 classes = 20 examples.
- All examples are from **real candidates** in the project's dataset (traceable to `strict_silver_max_candidates_v1.csv` via `candidate_id`).
- No examples are fabricated.

Distribution:

| Class | Positive examples | Negative/near-miss examples |
|---|---|---|
| `supported` | EX-S-POS-1 (SBV2-ALL92-G215-C01), EX-S-POS-2 (SBV2-ALL92-G067-C01), EX-S-POS-3 (SBV2-ALL92-G175-C01) | EX-S-NEG-1 (SBV2-ALL92-G002-MILD, near-miss mild), EX-S-NEG-2 (SBV2-ALL92-G170-C02, near-miss mild) |
| `mild_scope_overclaim` | EX-M-POS-1 (SBV2-ALL92-G002-MILD), EX-M-POS-2 (SBV2-ALL92-G170-C02), EX-M-POS-3 (SBV2-ALL92-G215-C02) | EX-M-NEG-1 (SBV2-ALL92-G215-C01, near-miss supported), EX-M-NEG-2 (SBV2-ALL92-G215-C03, near-miss strong) |
| `strong_action_overclaim` | EX-ST-POS-1 (SBV2-ALL92-G215-C03), EX-ST-POS-2 (SBV2-ALL92-G107-C03), EX-ST-POS-3 (SBV2-ALL92-G003-STRONG) | EX-ST-NEG-1 (SBV2-ALL92-G067-C02, near-miss mild), EX-ST-NEG-2 (SBV2-ALL92-G002-CONTRA, near-miss contradiction) |
| `contradiction_candidate` | EX-C-POS-1 (SBV2-ALL92-G215-C04), EX-C-POS-2 (SBV2-ALL92-G036-C04), EX-C-POS-3 (SBV2-ALL92-G002-CONTRA) | EX-C-NEG-1 (SBV2-ALL92-G107-C03, near-miss strong), EX-C-NEG-2 (SBV2-ALL92-G215-C03, near-miss strong) |

Each example includes: `example_id`, `label`, `example_type`, `candidate_id`, `evidence_text`, `claim_text`, `why_this_label`, `why_not_other_label`, `notes`.

---

## 4. Are Boundary Rules Included?

**Yes.** `boundary_rules_v1.md` covers all 6 required boundaries:
1. `supported` vs `mild_scope_overclaim` — decision rule, signal words, common mistake, example, what to write in rationale.
2. `mild_scope_overclaim` vs `strong_action_overclaim` — the hardest boundary (12/25 audit cases); includes the key action-vs-scope distinction.
3. `strong_action_overclaim` vs `contradiction_candidate` — includes the number-inflation-is-contradiction rule.
4. `contradiction_candidate` vs `mild_scope_overclaim` — includes the detail-swap-is-contradiction rule.
5. Evidence too short / context missing — when to mark `unsure` with `evidence_insufficient_context`.
6. When to use `unsure` — last resort; pick a leaning label with confusion note when possible.

Each boundary rule includes: decision rule, signal words, common mistake, example, and what the annotator should write in `rationale_one_sentence`.

---

## 5. Is `unsure` Allowed?

**Yes.** `unsure` is one of the five labels. Annotators are instructed:
- `unsure` is allowed and will be analyzed separately.
- Do not force a label if genuinely uncertain.
- However, if you can narrow it to two adjacent classes, **pick the one you lean toward** and note the confusion in `confusion_if_any` — this is more informative than `unsure`.
- If you mark `unsure`, you **must** explain what makes the case hard in `rationale_one_sentence` and note which two classes you are choosing between in `confusion_if_any`. Blank `unsure` without explanation is invalid.

The `unsure` rate will be tracked as a pilot metric (target: < 20%; < 10% is ideal).

---

## 6. Can Cohen's Kappa Be Computed?

**Yes.** The agreement metric plan (`agreement_metric_plan_v1.md`) defines:
- Overall agreement rate (A vs B, before adjudication).
- Cohen's kappa (A vs B, 4-class, excluding `unsure` for primary κ).
- Krippendorff's alpha (optional, ordinal).
- Per-boundary kappa: `supported_vs_mild`, `mild_vs_strong`, `strong_vs_contradiction`.
- Unsure rate.
- Label distribution shift (silver → gold).
- Strong-action retention rate.

All metrics are computable once both annotators submit their filled CSVs. The kappa computation requires:
- Annotator A's labels (from `pilot_50_blind_annotation_A_filled.csv`).
- Annotator B's labels (from `pilot_50_blind_annotation_B_filled.csv`).
- Both in the same 50-row order (matched by `pilot_id`).

---

## 7. Has Actual Annotation Been Performed?

**No.** This is a protocol freeze only. Specifically:
- `annotator_label` is empty in both blind templates (A and B).
- `confidence_1_to_5` is empty.
- `rationale_one_sentence` is empty.
- `confusion_if_any` is empty.
- `needs_adjudication` is empty.
- `adjudicated_label` has NOT been filled (adjudication template not yet created in this freeze).
- `gold_label` has NOT been filled anywhere.
- `final_label` has NOT been filled anywhere.
- `human_audited` has NOT been set to `true` anywhere.

Verification: The blind template generation script confirmed 50 rows with all 5 label-related fields empty for both A and B.

---

## 8. What Is the Next Step?

### Immediate next step (human action required)
1. **Identify two annotators** (Annotator A and Annotator B). They must be independent — not the project lead, not each other, not the adjudicator.
2. **Identify one adjudicator.** Must not be Annotator A or B.
3. **Send each annotator their materials:**
   - `annotator_training_packet.md`
   - `annotation_guideline_v1_frozen.md`
   - `annotation_decision_tree_v1.md`
   - `boundary_rules_v1.md`
   - `label_positive_negative_examples.csv`
   - `pilot_50_blind_annotation_A.csv` (for A) or `pilot_50_blind_annotation_B.csv` (for B)
4. **Annotators work independently** (no communication between them). Estimated time: ~4 hours each, spread over multiple days if needed.
5. **Annotators submit filled CSVs** (`_filled.csv`).

### After both annotators submit
6. **Adjudicator performs adjudication** per `adjudication_protocol_v1.md`. Output: `adjudication_results_v1.csv`.
7. **Compute agreement metrics** per `agreement_metric_plan_v1.md`. Output: agreement results JSON, label shift matrix, strong-action retention, taxonomy revision decision.
8. **Apply pre-registered decision rules:**
   - If `mild_vs_strong` κ < 0.4 → taxonomy MUST be revised.
   - If strong-action retention < 0.40 → paper claim降级.
   - If ≥ 5/50 `taxonomy_revision_needed` → taxonomy revision required.
9. **Decide next steps** based on pilot results:
   - If taxonomy is validated (κ ≥ 0.60, retention ≥ 0.40, < 5 revision-needed cases): proceed to full gold annotation of the 444-pair dataset, then re-evaluate R4/LLM against gold.
   - If taxonomy needs revision: revise taxonomy, re-pilot, then proceed.
   - If paper claim needs降级: revise V3.7 paper to reflect downgraded claim.

### What does NOT happen next
- No new algorithms.
- No new LLM comparisons.
- No new ablations.
- No code refactoring.
- No paper publication until the pilot is adjudicated and pre-registered rules are applied.

---

## 9. File Manifest

All 10 required output files are in `D:\ocn\gold_pilot_protocol_freeze_v1\`:

| # | File | Size | Purpose |
|---|---|---|---|
| 1 | `annotation_guideline_v1_frozen.md` | ~10 KB | Frozen 4+1 label definitions with definition/when to use/when not to use/common confusion/example/warning per label. |
| 2 | `annotation_decision_tree_v1.md` | ~8 KB | Frozen 6-step decision tree (directional conflict → action cue → action strength → scope → evidence-too-short → still-unsure). |
| 3 | `label_positive_negative_examples.csv` | ~12 KB | 20 worked examples (3 pos + 2 neg per class × 4 classes), all from real candidates. |
| 4 | `boundary_rules_v1.md` | ~9 KB | 6 boundary rules (supported/mild, mild/strong, strong/contradiction, contradiction/mild, evidence-too-short, unsure). |
| 5 | `annotator_training_packet.md` | ~9 KB | Self-contained training packet for non-project-member annotators. |
| 6 | `pilot_50_blind_annotation_A.csv` | ~22 KB | Blind template A (50 rows, 5 fields to fill, silver label hidden). |
| 7 | `pilot_50_blind_annotation_B.csv` | ~22 KB | Blind template B (50 rows, 5 fields to fill, silver label hidden). |
| 8 | `adjudication_protocol_v1.md` | ~8 KB | Adjudicator workflow, silver-label access policy, taxonomy_revision_needed triggers. |
| 9 | `agreement_metric_plan_v1.md` | ~9 KB | Overall agreement, Cohen's kappa, per-boundary kappa, unsure rate, label shift, strong-action retention, pre-registered decision rules. |
| 10 | `gold_pilot_protocol_freeze_report.md` | (this file) | Freeze report answering 8 questions. |

Supporting script: `D:\ocn\_PROJECT_INDEX\tools\build_gold_pilot_protocol_freeze_v1.py` (generates blind templates A and B; CSV transformation only, no models/APIs).

---

## 10. Prohibitions Honored

- No actual annotation performed.
- No `gold_label` filled.
- No `final_label` filled.
- No `human_audited = true` written.
- No original CSV modified (`gold_pilot_candidate_50.csv` is read-only; blind templates are new files).
- No models run.
- No APIs called.
- No V3.8 paper text modified.
- No experiment results generated.
- No silver-as-gold (silver labels are hidden from blind templates and from adjudicator by default).

---

## 11. Conclusion

The gold pilot protocol is frozen and ready for annotation. The next step is human: identify two annotators and one adjudicator, distribute the materials, and wait for independent annotation. The project's scientific credibility depends on this pilot — do not skip it, do not shortcut it, and do not begin any new algorithm or model work until the pilot is adjudicated and the pre-registered decision rules are applied.
