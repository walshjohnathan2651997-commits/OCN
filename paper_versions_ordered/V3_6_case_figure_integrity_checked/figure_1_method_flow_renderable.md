# Figure 1: CESE-OCN R4 Method Flow (Renderable)

> **V3.6 note:** This is the renderable version. Unlike V3.5 (which used `![Figure](figure_1_method_flow.md)` markdown links that do not render in docx), this version uses inline ASCII art + a markdown table that can be copied directly into the paper body. No external image dependencies, no broken markdown links.

---

## Figure 1 caption

**Figure 1.** CESE-OCN R4 routing flow. The router applies three routes in order: contradiction first (the most separable relation), then strong-action escalation under a conservative contradiction guard (to prevent contradiction cases from being absorbed into strong_action), then a supported/mild residual classifier. Frozen mean thresholds: `t_contra = 0.48`, `t_strong = 0.535`, `t_svm = 0.51`, `t_low` = lower contradiction guard.

---

## Figure 1 body (inline ASCII — copy directly into paper)

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

## Figure 1 routing order rationale (table form)

| Route | Order | Decision | Threshold (mean over 10 seeds) | Rationale |
| --- | --- | --- | --- | --- |
| Route 1 — Contradiction | 1st | if `p_contra >= t_contra` → `contradiction_candidate` | `t_contra = 0.48` | Most separable relation; NLI signals capture it well. Handling it first prevents downstream routes from absorbing contradiction cases into strong_action or mild. |
| Route 2 — Strong-action escalation | 2nd | if `p_strong >= t_strong` AND `p_contra < t_low` → `strong_action_overclaim` | `t_strong = 0.535`, `t_low` = lower guard | Most consequential but hardest to detect. Action-gap features (in addition to NLI) target this class. Conservative guard prevents contradiction absorption. |
| Route 3 — Scope residual | 3rd | if `p_svm >= t_svm` → `supported`; else → `mild_scope_overclaim` | `t_svm = 0.51` | Least separable boundary (supported-F1 = 0.4424, mild-F1 = 0.1266). SVM residual classifier handles it last, acknowledging the boundary remains open. |

## Design choice

The pilot results show that a single flat four-class classifier conflates these signals and under-performs on the most consequential class (baseline strong-F1 = 0.2408). R4 routes each pair through the most separable relation first, then the most consequential under a conservative guard, then the residual scope calibration — meeting all 5 pre-specified constraints simultaneously (strong_positive_delta ≥ +0.05, flat4_macro_delta ≥ -0.02, contradiction_positive_delta ≥ -0.03, escalation_macro_delta ≥ -0.03, positive_delta_seed_count ≥ 7).
