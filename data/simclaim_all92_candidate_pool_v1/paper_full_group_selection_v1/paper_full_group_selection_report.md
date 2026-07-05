# Paper-full v1 Group-level Selection Report

Group-complete selection: each group retains all 4 claims.

NOT gold, NOT final, NOT human audited.


## 1. Strict core groups selected

- strict eligible groups: **111**
- core groups selected: **50** (target 50)
- core claims total: **200** (= groups × 4)

## 2. Label distribution (must be balanced)

| label | count |
|---|---|
| contradiction_candidate | 50 |
| mild_scope_overclaim | 50 |
| strong_action_overclaim | 50 |
| supported | 50 |

## 3. Domain distribution

| domain | groups | claims |
|---|---|---|
| autonomous_driving | 27 | 108 |
| cyber_defense | 9 | 36 |
| policy_simulation | 6 | 24 |
| digital_twin | 5 | 20 |
| robotics | 2 | 8 |
| marl | 1 | 4 |

## 4. Group composition

- groups with n_B >= 1 (evidence gain): **21**
- groups with n_A > 0 (lexical leakage flag): **37**
- groups with only C (no A, no B): **5**

### Tier distribution

| tier | count |
|---|---|
| tier1_B_no_A | 8 |
| tier2_B_has_A | 13 |
| tier3_no_B_no_A | 5 |
| tier4_no_B_has_A | 24 |

## 5. Excluded groups

- groups with n_D > 0 (exclude recommended): **47**
- groups with cue risk: **3**
- review queue groups: **64**

## 6. Why this is NOT gold / final

- **Not gold**: no human adjudication, no double-annotation, no agreement metrics.
- **Not final**: candidate_label_guess is AI preannotation; final_label and gold_label absent; human_audited not written.
- Group-level selection ensures structural completeness, not semantic validity.

## 7. Next step

1. Human review of group-complete core (50 groups × 4 = 200 claims).
2. Review tier1_B_no_A groups first (B evidence gain, no lexical leakage).
3. After human adjudication, run model experiments on adjudicated subset.

## Output files

- `data\simclaim_all92_candidate_pool_v1\paper_full_group_selection_v1\paper_full_core_candidates_group_complete_v1.csv`
- `data\simclaim_all92_candidate_pool_v1\paper_full_group_selection_v1\paper_full_core_groups_v1.csv`
- `data\simclaim_all92_candidate_pool_v1\paper_full_group_selection_v1\paper_full_group_review_queue_v1.csv`
- `data\simclaim_all92_candidate_pool_v1\paper_full_group_selection_v1\paper_full_group_exclude_recommended_v1.csv`
- `data\simclaim_all92_candidate_pool_v1\paper_full_group_selection_v1\paper_full_group_selection_summary.json`
- `data\simclaim_all92_candidate_pool_v1\paper_full_group_selection_v1\paper_full_group_selection_report.md`