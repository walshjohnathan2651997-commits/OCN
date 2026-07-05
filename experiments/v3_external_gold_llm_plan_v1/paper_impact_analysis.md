# Paper Impact Analysis: External Gold + LLM Baseline

## Context

V3/R4 was validated on SimClaim silver labels (444 pairs, 4-class balanced, 6 technical domains).
Task P confirmed R4 retains main-method status under 10-seed group-aware split and domain/source
holdout. This task (Task Q) plans external gold and LLM baseline extensions WITHOUT executing them.

## Scenario-Based Writing Guidance

### Scenario 1: R4 performs well on public gold (SciFact/VitaminC E1+E2)

**Suggested writing**:
> "As an external sanity check, we evaluated the R4 router's contradiction-detection component
> on SciFact and VitaminC. R4 achieved competitive binary support-vs-contradiction F1 without
> retraining, supporting the generality of the evidence-relation routing framework beyond the
> SimClaim annotation. We emphasize that public datasets test support/refute relations and do
> not include action-overclaim labels; therefore they validate generalization of the
> contradiction-detection module, not the strong-action-overclaim detector."

### Scenario 2: R4 performs mediocre on public gold

**Suggested writing**:
> "Public fact-verification datasets (SciFact, VitaminC, FEVER) test binary support/refute
> relations and do not annotate action-overclaim. R4's design prioritizes the
> strong-action-overclaim vs supported/mild distinction, which has no analogue in these
> datasets. Modest performance on public data therefore does not contradict R4's value on
> SimClaim: SimClaim remains the needed benchmark for action-overclaim detection."

### Scenario 3: LLM judge is clearly stronger than R4

**Suggested writing**:
> "A small-sample LLM judge baseline (N=200, GPT-4o-mini) outperformed R4 on overall macro-F1.
> This is expected: the LLM has broader world knowledge and can detect semantic contradictions
> the linear router misses. However, R4 provides three advantages the LLM cannot: (1) transparent
> and auditable routing decisions; (2) per-component threshold control; (3) no API cost or data
> egress. We therefore position R4 as an interpretable and deployable pilot baseline, with the
> LLM as a strong black-box reference."

### Scenario 4: LLM judge is comparable to R4

**Suggested writing**:
> "On 200 SimClaim pairs, the LLM judge achieved competitive but not superior performance to R4
> (delta within bootstrap CI). This suggests action-overclaim detection is difficult even for
> large language models, and that R4's transparent routing captures most of the achievable signal
> at this sample size. R4 thus offers a competitive pilot baseline with the added benefit of
> interpretability."

### Scenario 5: LLM judge is weaker than R4

**Suggested writing**:
> "The LLM judge underperformed R4 on strong-action-overclaim F1, primarily due to over-reliance
> on world knowledge and difficulty following the conservative evidence-only constraint. This
> suggests action-overclaim detection requires the structured evidence-relation decomposition
> provided by R4, rather than end-to-end LLM judgment."

## Cross-Cutting Reporting Rules

1. Public gold results MUST be in a separate table (Table 7+), never merged with SimClaim main results.
2. LLM baseline MUST be labeled as "small-sample pilot baseline, N<=200, not full-dataset".
3. MUST disclose which LLM model and which API was used (or "local model" if applicable).
4. MUST NOT claim public gold validates strong_action_overclaim detection.
5. MUST NOT claim LLM is the gold standard; it is one baseline among several.
6. All R4 vs LLM comparisons MUST report bootstrap CI and seed stability.

## Risk Notes

- If public gold results are very poor (e.g., R4 macro-F1 < 0.50 on SciFact E1), this is a
  red flag for the contradiction-detection module's transferability and should be discussed
  transparently in the paper.
- If LLM is dramatically better (delta > 0.10 strong-F1), this challenges R4's value and
  the paper must reframe R4 as "transparent baseline" rather than "best method".
- The external + LLM extensions are PILOT only; they do not substitute for the 300-500
  human-audited gold pairs recommended in Task N.
