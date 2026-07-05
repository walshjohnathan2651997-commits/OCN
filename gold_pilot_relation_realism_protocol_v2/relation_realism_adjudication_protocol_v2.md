# Adjudication Protocol v2 — Relation + Realism (Two-Layer)

**Version:** 2.0 (DRAFT)
**Date:** 2026-07-05
**Status:** v2 DRAFT. v1 (`adjudication_protocol_v1.md`) is FROZEN and untouched. v2 extends v1 with Layer 2 realism adjudication.
**Predecessor:** `D:\ocn\gold_pilot_protocol_freeze_v1\adjudication_protocol_v1.md`

---

## 0. Adjudicator role

The adjudicator is a third party (not Annotator A, not Annotator B, not the project lead). The adjudicator's job is to:

1. Review disagreements between A and B.
2. Make a final decision on each disputed field.
3. Produce `final_relation_label` and `final_realism_score` for every row.
4. Apply pre-registered decision rules to determine paper-claim fate.

**The adjudicator does NOT re-annotate from scratch.** The adjudicator reviews A's and B's annotations, reads the evidence and claim, and picks the more defensible label/score. The adjudicator may consult the v1 and v2 guidelines and decision trees.

---

## 1. Silver-label access policy (carry over from v1)

- **Default:** The adjudicator does NOT look at silver labels during adjudication.
- **Silver labels** (`silver_label`, `candidate_label_guess`, `final_label`, `gold_label`) are HIDDEN from the adjudicator.
- **Exception:** If the adjudicator explicitly flags a row as "silver comparison required" (with a written justification), the project lead may unlock silver for that row ONLY, post-decision. This exception should be rare (< 5% of rows).
- **Post-adjudication:** After all final labels are set, silver labels may be compared to gold for analysis purposes (label shift, retention rate). This is a research analysis, not part of the adjudication.

---

## 2. Two-layer adjudication order

For each row, the adjudicator works in this order:

### Step 1: Layer 1 relation adjudication (first)

Decide `final_relation_label` BEFORE looking at Layer 2.

- If A and B agree on `annotator_relation_label` → adopt it as `final_relation_label` (no adjudication needed).
- If A and B disagree → review both rationales, read evidence + claim, apply Tree A, pick the more defensible label.
- If either annotator set `needs_relation_adjudication = yes` → review even if A and B agree (the annotator is asking for a sanity check).
- If both marked `unsure` → the adjudicator must make a definitive call (no `unsure` allowed in final gold).

### Step 2: Layer 2 realism adjudication (second, AFTER Layer 1 is decided)

Decide `final_realism_score` and `final_realism_issue` AFTER Layer 1.

- If A and B agree on `claim_realism_score_1_to_5` (exact match or within-1) AND agree on `claim_realism_issue` → adopt as final (no adjudication needed).
- If A and B disagree on score (difference >= 2) OR on issue type → review both rationales, re-read claim text (set evidence aside), apply Tree B, pick the more defensible score and issue.
- If either annotator set `needs_realism_adjudication = yes` → review even if A and B agree.
- The adjudicator's Layer 2 decision is INDEPENDENT of Layer 1. A `strong_action_overclaim` (Layer 1) can have `final_realism_score = 5` (very natural).

### Step 3: Cross-layer high-risk review

After both layers are decided, apply cross-layer rules (see §4 below).

### Step 4: Final fields

For each row, the adjudicator produces:

| Field | Source |
| --- | --- |
| `final_relation_label` | Step 1 |
| `final_relation_confidence` | Adjudicator's confidence 1-5 |
| `final_realism_score` | Step 2 |
| `final_realism_issue` | Step 2 |
| `claim_usable_for_paper_example_final` | "no" if `final_realism_score <= 2`; otherwise adjudicator's judgment |
| `high_risk_flag` | True if cross-layer rules trigger (see §4) |
| `adjudication_notes` | Free-text explanation if adjudicated |

---

## 3. Layer 1 adjudication rules (carry over from v1)

### 3.1 When to adjudicate Layer 1

Adjudicate Layer 1 if ANY of:
- A and B disagree on `annotator_relation_label`.
- Either annotator set `needs_relation_adjudication = yes`.
- Either annotator marked `unsure` (the final gold must have a definitive label).

### 3.2 How to adjudicate Layer 1

1. Read A's `relation_rationale_one_sentence` and B's `relation_rationale_one_sentence`.
2. Read the evidence and claim.
3. Apply Tree A (`relation_realism_decision_tree_v2.md`).
4. Pick the more defensible label. If neither is fully defensible, pick the closest defensible label (no `unsure` in final gold).
5. Record `final_relation_label` and `final_relation_confidence`.
6. If the case is genuinely ambiguous, mark `adjudication_notes` with the ambiguity.

### 3.3 Common Layer 1 adjudication patterns

- **mild_vs_strong disagreement:** Check whether the claim asserts an action/deployment/safety conclusion (→ strong) or only expands scope (→ mild). The cue word "deployment/safety/policy" tips it to strong.
- **strong_vs_contradiction disagreement:** Check whether there's a directional conflict on the same metric/number/entity (→ contradiction) or just strength escalation (→ strong). Number inflation is contradiction.
- **supported_vs_mild disagreement:** Check whether the claim adds scope/precision detail not in evidence (→ mild) or just paraphrases (→ supported).

---

## 4. Layer 2 adjudication rules (NEW in v2)

### 4.1 When to adjudicate Layer 2

Adjudicate Layer 2 if ANY of:
- |A.realism_score - B.realism_score| >= 2.
- A.realism_issue != B.realism_issue.
- Either annotator set `needs_realism_adjudication = yes`.
- Either annotator marked `claim_realism_score_1_to_5 <= 2` (low-realism claims must be reviewed).

### 4.2 How to adjudicate Layer 2

1. Read A's `realism_rationale_one_sentence` and B's `realism_rationale_one_sentence`.
2. Re-read the **claim text alone** (set the evidence aside — Layer 2 is about the claim as a sentence).
3. Apply Tree B (`relation_realism_decision_tree_v2.md`).
4. Pick the more defensible score (1-5) and issue type.
5. Record `final_realism_score` and `final_realism_issue`.
6. Set `claim_usable_for_paper_example_final`:
   - If `final_realism_score <= 2` → "no" (MANDATORY, no exception).
   - If `final_realism_score >= 4` AND `final_realism_issue == none` → "yes" (default).
   - If `final_realism_score == 3` → adjudicator's judgment, default "no".

### 4.3 Cross-layer high-risk rules (NEW in v2)

After deciding both layers, the adjudicator MUST apply these cross-layer rules:

| # | Condition | Action |
| --- | --- | --- |
| 1 | `final_relation_label == strong_action_overclaim` AND `final_realism_issue == strong_action_too_forced` AND `final_realism_score <= 2` | Set `high_risk_flag = True`. This claim is a forced overclaim — exclude from paper examples. Flag for taxonomy review: is the strong_action category capturing realistic overclaims or just AI-generated forced ones? |
| 2 | `final_relation_label == contradiction_candidate` AND `final_realism_issue == contradiction_too_mechanical` AND `final_realism_score <= 2` | Set `high_risk_flag = True`. This contradiction is mechanical — exclude from paper examples. Flag for data construction review: are contradictions being generated as simple negation/number swaps? |
| 3 | `final_realism_score <= 2` (regardless of relation label) | Set `claim_usable_for_paper_example_final = "no"` (MANDATORY). |
| 4 | `final_relation_label == unsure` (post-adjudication, should not happen) | Set `high_risk_flag = True`. The adjudicator must make a definitive call (no `unsure` in final gold). |

### 4.4 What `high_risk_flag` triggers

- High-risk claims are **excluded from paper illustrative examples** (regardless of relation label).
- High-risk claims are **counted in the class-level realism downgrade trigger** (see §5).
- If > 25% of claims in any relation label are high-risk → paper claim downgrade (class-level).
- If > 25% of all 50 claims are high-risk → major paper downgrade (paper-level).

---

## 5. Pre-registered downgrade triggers (summary)

After all 50 rows are adjudicated, compute:

| Trigger | Threshold | Action |
| --- | --- | --- |
| `mild_vs_strong` κ < 0.40 | κ < 0.40 | Taxonomy revision required; re-pilot. |
| Strong-action retention < 0.40 | retention < 0.40 | Paper claim downgrade. |
| >= 5/50 `taxonomy_revision_needed` | >= 5 rows | Taxonomy revision required. |
| Class-level realism: any label with > 25% `realism_score <= 2` | > 25% per label | Paper claim downgrade (class-level). |
| Paper-level realism: > 25% of all 50 with `realism_score <= 2` | > 25% overall | Major paper downgrade. |
| Layer 2 Pearson r < 0.40 | r < 0.40 | Realism annotation unreliable; retraining required. |

---

## 6. Final gold output

The adjudicator produces `adjudication_results_v2.csv` with 50 rows and these columns:

| Field | Description |
| --- | --- |
| `pilot_id` | P001-P050 |
| `candidate_id` | Original candidate ID |
| `domain` | Domain |
| `final_relation_label` | One of 4 labels (no `unsure`) |
| `final_relation_confidence` | Adjudicator's confidence 1-5 |
| `final_realism_score` | 1-5 |
| `final_realism_issue` | One of 9 issue types |
| `claim_usable_for_paper_example_final` | yes / no |
| `high_risk_flag` | True / False |
| `annotator_a_relation_label` | A's original label (for traceability) |
| `annotator_b_relation_label` | B's original label |
| `annotator_a_realism_score` | A's original score |
| `annotator_b_realism_score` | B's original score |
| `adjudication_notes` | Free text |

---

## 7. What the adjudicator does NOT do

- Does NOT re-annotate from scratch (only reviews disagreements).
- Does NOT look at silver labels (default).
- Does NOT modify the original SimClaim data.
- Does NOT modify v1 protocol files.
- Does NOT decide whether to publish the paper (only produces gold + triggers; project lead decides publication).
- Does NOT skip Layer 2 because Layer 1 was easy. Both layers must have final values for every row.
- Does NOT mark `final_realism_score <= 2` claims as `claim_usable_for_paper_example_final = "yes"` (this is forbidden; the rule is mandatory).

---

## 8. Relationship to v1

- v1 (`adjudication_protocol_v1.md`): FROZEN, Layer 1 only. **Not modified by v2.**
- v2 (this protocol): DRAFT, Layer 1 + Layer 2.
- v2's Layer 1 adjudication rules are consistent with v1 (no conflict).
- v2 adds Layer 2 adjudication rules (NEW) and cross-layer high-risk rules (NEW).
- If v1 and v2 ever conflict on Layer 1, v1 wins (FROZEN).
