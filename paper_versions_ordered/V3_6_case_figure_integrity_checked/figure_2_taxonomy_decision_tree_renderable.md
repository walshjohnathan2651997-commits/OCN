# Figure 2: Taxonomy Decision Tree (Renderable)

> **V3.6 note:** This is the renderable version. Unlike V3.5 (which used `![Figure](figure_2_taxonomy_decision_tree.md)` markdown links that do not render in docx), this version uses inline ASCII art + a markdown table that can be copied directly into the paper body. No external image dependencies, no broken markdown links.

---

## Figure 2 caption

**Figure 2.** Taxonomy decision tree (simplified). Step 1: directional conflict on the same metric / number / entity → `contradiction_candidate` (including detail-swapping of numbers, names, or metrics). Step 2-3: action / deployment / safety / operational cue present AND evidence insufficient for action strength → `strong_action_overclaim`. Step 4: scope over-extension without action consequences → `mild_scope_overclaim`; otherwise → `supported`. The full operational version with cue lists and boundary-case rules is in `taxonomy_boundary_decision_tree.md` (V3.4).

---

## Figure 2 body (inline ASCII — copy directly into paper)

```
                       +---------------------------+
                       |   Claim-Evidence Pair     |
                       +-------------+-------------+
                                     |
                                     v
              +----------------------------------------+
              | Step 1: Directional Conflict?         |
              | Does the claim point OPPOSITE to      |
              | evidence on the same metric, number,  |
              | entity, or conclusion?                |
              | (includes detail-swapping)            |
              +-----------------+---------------------+
                          YES   |   NO
                +---------------+   +---------------+
                v                               v
        +----------------+        +-----------------------------+
        | contradiction_ |        | Step 2: Action/Deployment/  |
        | candidate      |        | Safety/Operational Cue?     |
        +----------------+        | (deploy, safety, guarantee, |
                                  | operational, policy, broad   |
                                  | generalization, outperforms, |
                                  | suitable for, theoretically  |
                                  | justified, etc.)             |
                                  +--------------+--------------+
                                          YES    |    NO
                                  +--------------+   +--------------+
                                  v                              v
                       +-------------------------+   +-----------------------+
                       | Step 3: Evidence        |   | Step 4: Scope         |
                       | Sufficient for Action   |   | Over-Extension?       |
                       | Strength?               |   | Does the claim expand |
                       | Is evidence limited to  |   | scope/domain/         |
                       | single benchmark /      |   | population/condition/ |
                       | simulation / lab /      |   | temporal range beyond |
                       | limited metric / single |   | evidence, WITHOUT     |
                       | domain, while claim     |   | action consequences?  |
                       | asserts stronger        |   +-------+---------------+
                       | action conclusion?      |    YES    |    NO
                       +-----------+-------------+   +--------+   +--------+
                              YES   |   NO            v           v
                       +------------+   +----------+ +--------+ +--------+
                       v                v          | mild_   | |        |
                +--------------+  +------------+    | scope_  | | sup-   |
                | strong_      |  | Re-examine |    | over-   | | ported |
                | action_      |  | as sup.    |    | claim   | |        |
                | overclaim    |  | or mild    |    +---------+ +--------+
                +--------------+  +------------+
```

## Figure 2 four labels (table form)

| Label | Core Definition |
| --- | --- |
| **supported** | Evidence is sufficient for the claim's stated strength (not "absolutely true"). |
| **mild_scope_overclaim** | Claim mildly over-extends scope / domain / generality, but no action / deployment / safety conclusion asserted. |
| **strong_action_overclaim** | Claim asserts an action / deployment / safety / guarantee / operational / policy conclusion that evidence cannot justify. Direction may be consistent; strength is excessive. |
| **contradiction_candidate** | Evidence contradicts the claim; directions conflict on the same metric or conclusion (including detail-swapping). |

## Figure 2 key distinctions (table form)

| # | Distinction | Operationalized by |
| --- | --- | --- |
| 1 | strong_action_overclaim does NOT require directional conflict | Step 1 routes by direction first; if no conflict, Step 2-3 check action strength |
| 2 | contradiction_candidate IS about directional conflict | Step 1 — including detail-swapping (numbers, names, metrics) |
| 3 | strong_action_overclaim is about strength / action consequences | Step 2-3 — cue list + evidence sufficiency for action strength |
| 4 | mild_scope_overclaim is about scope / generalization over-extension | Step 4 — without action consequences |
| 5 | supported means evidence sufficient for claim's stated strength | Step 4 — default when no conflict, no action cue, no scope over-extension |

## Figure 2 boundary cases (table form)

| Boundary | Hardest cases | Audit count | Decision tree handling |
| --- | --- | --- | --- |
| Mild vs. Strong | 12/25 questionable/unclear | 48% of audit | Step 2 cue list operationalizes action/deployment cue; cases with weak cues remain ambiguous |
| Strong vs. Contradiction | 6/25 questionable/unclear | 24% of audit | Step 1 now treats detail-swapping (number/name/metric swap) as contradiction |
| Supported vs. Mild | weakest boundary (mild-F1 = 0.1266) | — | Step 4 operationalizes scope over-extension; minor scope expansions remain genuinely hard |
| Claim too abstract | 5/25 questionable/unclear | 20% of audit | Decision tree cannot compensate — claim generation issue, not taxonomy issue |

Boundary cases are not noise to hide — they are the cases where evidence sufficiency calibration is hardest and most consequential. They are retained in `high_risk_sample_bank.csv` as future gold adjudication priority.

## What this decision tree is NOT

- **Not a gold standard.** It is a labeling aid.
- **Not validated against gold labels.** No gold labels exist for the four-class taxonomy; the tree has not been tested against external adjudication.
- **Not a replacement for human judgment.** Cases where the tree yields ambiguous results still require human adjudication.
