# 03 — Format-Shift Blocked Response (Risk C)

**Risk ID:** C
**Reviewer attack:** "The format-shift R4 evaluation is incomplete. You constructed 8 variants × 444 = 3552 rows and NLI features [3552, 7], but did not report R4 metrics on the variants. This looks like a hidden negative result."
**Severity:** High

---

## 1. Reviewer concern

The reviewer notes that the format-shift ablation is described as partial: variant construction and NLI feature extraction are complete, but R4 metrics on the variants are not reported. The reviewer may suspect that the metrics were computed, found to be unfavorable, and suppressed, or that the experiment was abandoned to avoid reporting a negative result. The reviewer may demand either the missing metrics or a transparent explanation of why the metrics cannot be reported.

## 2. What we agree with

We agree that the format-shift R4 evaluation is not complete. We agree that R4 metrics on the 8 variants are not reported. We agree that the partial state of this experiment is a limitation that must be stated explicitly rather than hidden. We do not contest that a reviewer is entitled to a transparent explanation of the block and to the artifacts that *were* produced (variant rows, NLI features).

## 3. Evidence we have

- **Variant construction complete.** `experiments/format_shift_ablation_v1/format_shift_summary.json` reports `n_variants = 8`, `n_variant_rows = 3552`, `status = partial`. The 8 variants are constructed over 444 candidates.
- **NLI feature extraction complete.** The NLI feature matrix has shape [3552, 7], indicating features are computed for all variant rows.
- **R4 prediction blocked.** R4 prediction on the variants fails with `AttributeError` on `multi_class` argument. The frozen R4 artifacts require scikit-learn ≥ 1.5.0; the current environment has scikit-learn 1.4.1.post1.
- **No-network boundary.** The V3.17 confidential pipeline runs under a strict `no_api`, `no_network`, `no_training` boundary. Upgrading scikit-learn requires either network access (pip install) or a pre-staged wheel; neither is available inside the boundary.
- **Blocked report.** `reports/format_shift_r4_eval_blocked_v3_17.md` documents the block, the version mismatch, the no-network constraint, and the partial artifacts that *are* available.
- **Public artifact.** `experiments/format_shift_ablation_v1/format_shift_inputs_redacted.csv` is the public redacted variant-input file (oracle variant rows stripped) so that downstream consumers can reproduce R4 prediction if their environment has scikit-learn ≥ 1.5.0.
- **Schema validation.** `validate_experiment_outputs_v1.py` reports 2 schema failures, both on `format_shift_metrics.csv` (one in the real experiment dir, one in the toy experiment dir), confirming the metrics file is absent in both real and toy modes.

## 4. Evidence file

- `experiments/format_shift_ablation_v1/format_shift_summary.json`
- `experiments/format_shift_ablation_v1/format_shift_inputs_redacted.csv`
- `reports/format_shift_r4_eval_blocked_v3_17.md`
- `reports/final_perfect_state_gate_v3_17.json` (BLOCKED item 3.4)
- `reports/current_project_status_v3_17.md`

## 5. Safe response

We answer the reviewer as follows: the format-shift R4 evaluation is blocked by a scikit-learn version mismatch, not abandoned and not suppressed. Variant construction (8 variants × 444 = 3552 rows) and NLI feature extraction ([3552, 7]) are complete and available as redacted public artifacts. R4 prediction on the variants fails because the frozen R4 artifacts require scikit-learn ≥ 1.5.0 and the environment has 1.4.1.post1; the V3.17 no-network boundary prevents in-place upgrade. We do not report R4 metrics on the variants and we do not imply that the evaluation was completed.

The safe empirical conclusion is therefore narrow: **variant construction and NLI feature extraction are complete; R4 metrics on the variants are not reported because frozen R4 prediction is blocked by sklearn version mismatch under the no-network boundary. This is a documented permanent limitation, not a hidden negative result.** Any future re-run in an environment with scikit-learn ≥ 1.5.0 can produce the missing metrics from the public redacted variant inputs.

## 6. Remaining limitation

- R4 metrics on the 8 format-shift variants are absent; no precision, recall, F1, or macro_F1 is reported for the variants.
- The block is environmental (sklearn version mismatch under no-network), not a defect in the variant construction or NLI features.
- The canonicalization gain (oracle_recall 0.043 → 0.387) is reported on the canonicalizer ablation, not on R4 over variants; the link between canonicalization gain and R4 behavior under format shift is therefore inferred, not directly measured.
- The block is permanent under the V3.17 no-network boundary; lifting it requires either an offline wheel of scikit-learn ≥ 1.5.0 or relaxing the no-network constraint.
- The schema validation failures (WARNING 10.2) on `format_shift_metrics.csv` are a direct consequence of this block and are documented as such.

## 7. Paper text to add

> "We constructed 8 format-shift variants over the 444 candidates (3552 variant rows) and extracted NLI features for every row (feature matrix [3552, 7]). R4 prediction on the variants is blocked because the frozen R4 artifacts require scikit-learn ≥ 1.5.0 and the deployment environment has scikit-learn 1.4.1.post1; the V3.17 no-network boundary prevents in-place upgrade. We therefore do not report R4 metrics on the variants. This is a documented permanent limitation (`reports/format_shift_r4_eval_blocked_v3_17.md`), not a hidden negative result. The redacted public variant inputs (`experiments/format_shift_ablation_v1/format_shift_inputs_redacted.csv`) allow any reader with scikit-learn ≥ 1.5.0 to reproduce the missing metrics. The canonicalization gain (oracle_recall 0.043 → 0.387, 9x) is reported on the canonicalizer ablation and is the strongest available evidence that format shift matters at the retrieval-to-screening interface."

## 8. What not to claim

| Unsafe wording (forbidden) | Why forbidden |
|---|---|
| "format-shift R4 evaluation is complete" | R4 metrics on variants are not reported; status = partial |
| "R4 is robust to format shift" | metrics not computed; no robustness claim is supportable |
| "R4 is fragile to format shift" | metrics not computed; no fragility claim is supportable either |
| "the blocked evaluation is a negative result" | block is environmental (sklearn version, no-network), not empirical |
| "format_shift_metrics.csv exists" | the file is absent in both real and toy experiment dirs; schema validation fails on both |

---

*End of response 03.*
