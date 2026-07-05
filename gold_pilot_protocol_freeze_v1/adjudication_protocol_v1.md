# Adjudication Protocol v1 — FROZEN

**Version:** 1.0 (frozen)
**Date:** 2026-07-04
**Status:** FROZEN — do not modify after annotator training begins.
**Audience:** The adjudicator (who is NOT one of the two annotators).

---

## 1. When Adjudication Begins

Adjudication begins **only after** both Annotator A and Annotator B have submitted their filled CSVs:
- `pilot_50_blind_annotation_A_filled.csv`
- `pilot_50_blind_annotation_B_filled.csv`

Do not begin adjudication until both are received. Do not preview one annotator's labels while the other is still annotating.

---

## 2. Adjudicator Qualifications

- The adjudicator must **NOT** be Annotator A or Annotator B.
- The adjudicator should be familiar with the four-class taxonomy and the decision tree (`annotation_decision_tree_v1.md`).
- The adjudicator should have read `boundary_rules_v1.md` and `label_positive_negative_examples.csv`.

---

## 3. Adjudication Workflow

For each of the 50 pairs, the adjudicator:

### Step 1: Load both annotators' labels
- Read `annotator_label` from Annotator A's CSV.
- Read `annotator_label` from Annotator B's CSV.

### Step 2: Classify the pair
- **Agreement case:** A and B assigned the same label (both `supported`, both `mild_scope_overclaim`, etc.).
- **Disagreement case:** A and B assigned different labels.
- **Unsure case (either or both):** A and/or B assigned `unsure`.

### Step 3: Process by case type

#### 3a. Agreement cases (A and B same label)

1. Read the evidence and claim.
2. Apply the decision tree independently.
3. If the adjudicator agrees with A and B → confirm the label as `adjudicated_label`.
4. If the adjudicator disagrees with A and B (both wrong) → override with the correct label. Note the override reason in `adjudication_notes`.
5. Mark `final_use_recommendation`:
   - `usable_for_gold_eval` — if the label is clear and both annotators agreed confidently.
   - `boundary_case_only` — if the label is correct but the case is on a boundary (e.g., both annotators agreed but both marked `confidence_1_to_5 ≤ 3`).
   - `exclude_due_to_unclear_evidence` — if the evidence is too short/truncated to support any label confidently.
   - `taxonomy_revision_needed` — if the adjudicator believes the taxonomy itself is ambiguous for this case (see §6 below).

#### 3b. Disagreement cases (A and B different labels)

1. Read Annotator A's `rationale_one_sentence` and `confusion_if_any`.
2. Read Annotator B's `rationale_one_sentence` and `confusion_if_any`.
3. Read the evidence and claim.
4. Apply the decision tree independently.
5. Assign `adjudicated_label` based on the adjudicator's independent judgment, NOT simply picking A or B.
6. Note in `adjudication_notes`: which annotator was closer, why, and what the key signal was.
7. Mark `final_use_recommendation` (same options as 3a).

#### 3c. Unsure cases (either or both marked `unsure`)

1. Read the rationale(s) for the `unsure` label(s).
2. Read the evidence and claim.
3. Apply the decision tree.
4. If the adjudicator can assign a confident label → assign `adjudicated_label`.
5. If the adjudicator also cannot decide → assign `adjudicated_label = unsure` and mark `final_use_recommendation = exclude_due_to_unclear_evidence` or `taxonomy_revision_needed`.
6. Note in `adjudication_notes`: why the case was unsure, whether it was evidence-quality (too short/truncated) or taxonomy-boundary (genuinely hard).

---

## 4. Silver Label Access Policy

**Default: The adjudicator does NOT look at silver labels during adjudication.**

The silver labels are AI-preannotated and author-screened. They are NOT gold. If the adjudicator looks at silver labels during adjudication, it risks biasing the gold labels toward silver, defeating the purpose of independent gold adjudication.

**Exception:** After all 50 adjudicated labels are finalized, the adjudicator MAY compare gold labels to silver labels **for analysis purposes only** (e.g., computing label distribution shift from silver to gold). This comparison must happen AFTER adjudication is complete, not during.

If the adjudicator accidentally sees a silver label before finalizing an adjudicated label, that pair must be re-adjudicated by a different adjudicator or flagged as `silver_contaminated = true`.

---

## 5. When `adjudicated_label` Is Filled

`adjudicated_label` is filled **during** adjudication, after reading both annotators' labels and rationales and independently applying the decision tree. It is the adjudicator's final label for the pair.

**Do not fill `adjudicated_label` before reading both annotators' submissions.**

---

## 6. When to Mark `taxonomy_revision_needed`

Mark `final_use_recommendation = taxonomy_revision_needed` when **the taxonomy itself is ambiguous** for this case, not just the annotators. Signals:

1. **Both annotators picked different labels with high confidence** (both `confidence_1_to_5 ≥ 4`), and the adjudicator also cannot confidently pick one. This suggests the taxonomy does not clearly distinguish the classes for this case.

2. **The decision tree yields ambiguous results** — e.g., Step 2 (action cue) is genuinely ambiguous because the claim describes methodology with implicit action framing.

3. **The case is on a known hard boundary** (mild_vs_strong or strong_vs_contradiction) AND both annotators marked `confusion_if_any` matching that boundary AND the adjudicator agrees the boundary is genuinely unclear.

4. **The four-class taxonomy itself may need revision** — e.g., the case suggests a fifth class is needed, or the mild/strong split should be redefined.

`taxonomy_revision_needed` cases will be aggregated and reviewed after the pilot. If ≥5/50 cases are marked `taxonomy_revision_needed`, the taxonomy should be revised before any further annotation or model training.

---

## 7. Adjudicator Output

The adjudicator fills `adjudication_template.csv` (already exists in `D:\ocn\gold_pilot_preparation_v1\`) with these columns:

| Column | Description |
|---|---|
| `pilot_id` | From the candidate CSV. |
| `candidate_id` | From the candidate CSV. |
| `annotator_A_label` | From Annotator A's filled CSV. |
| `annotator_B_label` | From Annotator B's filled CSV. |
| `agreement_status` | `agree` / `disagree` / `either_unsure` / `both_unsure`. |
| `adjudicated_label` | The adjudicator's final label. |
| `adjudication_notes` | Why this label; which annotator was closer; key signal. |
| `final_use_recommendation` | `usable_for_gold_eval` / `boundary_case_only` / `exclude_due_to_unclear_evidence` / `taxonomy_revision_needed`. |
| `silver_contaminated` | `false` by default; `true` if adjudicator accidentally saw silver before finalizing. |

Save the filled adjudication file as:
`D:\ocn\gold_pilot_protocol_freeze_v1\adjudication_results_v1.csv`

---

## 8. Post-Adjudication Analysis

After adjudication is complete, the adjudicator (or a separate analyst) computes:

1. **Overall agreement rate** (A vs B, before adjudication).
2. **Cohen's kappa** (A vs B).
3. **Per-boundary agreement** (supported_vs_mild, mild_vs_strong, strong_vs_contradiction).
4. **Unsure rate** (how often A and/or B marked `unsure`).
5. **Label distribution shift** from silver to gold (after adjudication, compare silver labels to adjudicated labels).
6. **Strong_action retention rate** (how many silver `strong_action_overclaim` cases survived as `strong_action_overclaim` in gold).

See `agreement_metric_plan_v1.md` for the full statistics plan.

---

## 9. What Adjudication Does NOT Do

1. **Does not re-run models.** Adjudication is human judgment only.
2. **Does not call APIs.** No LLM judgments during adjudication.
3. **Does not modify original data.** The 50 candidate pairs are read-only.
4. **Does not fill `gold_label` in the original CSV.** Gold labels live in `adjudication_results_v1.csv`, not in `strict_silver_max_candidates_v1.csv`.
5. **Does not decide taxonomy revisions.** Adjudication flags `taxonomy_revision_needed` cases; the actual revision decision is a separate project step after the pilot.
