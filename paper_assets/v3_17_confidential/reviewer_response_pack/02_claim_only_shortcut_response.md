# 02 — Claim-Only Shortcut Response (Risk B)

**Risk ID:** B
**Reviewer attack:** "R4 may have learned only the claim template (claim-only shortcut). The strong_F1 = 0.4503 may be inflated by lexical cues in `claim_text` rather than by retrieval-to-screening behavior."
**Severity:** High

---

## 1. Reviewer concern

The reviewer suspects that R4's strong_F1 = 0.4503 is driven primarily by surface features of `claim_text` (lexical cues, action verbs, polarity markers) rather than by the retrieved and canonicalized evidence. If true, the entire retrieval-to-screening pipeline would be redundant, and the canonicalization contribution would be cosmetic. The reviewer may ask for claim-only, title-only, metadata-only, and shuffled-evidence baselines to quantify the shortcut risk.

## 2. What we agree with

We agree that claim-only signal exists on this silver set: claim-only strong_F1 = 0.2448 is non-trivial. We agree that any non-zero claim-only signal is a limitation that must be reported transparently, not hidden. We agree that the canonicalization contribution is only meaningful insofar as R4 uses the evidence beyond what is already predictable from the claim alone. We do not claim that R4 is fully shortcut-free.

## 3. Evidence we have

- **Claim-only baseline.** `experiments/leakage_audit_v1/claim_only_baseline.json` reports claim-only strong_F1_mean = 0.2448 across 10 seeds. The ratio claim-only / R4 = 0.5436, which is below the 0.8 warning threshold defined in the leakage audit protocol. R4 therefore substantially exceeds the claim-only ceiling, but the claim-only signal is real.
- **Shuffled-evidence baseline.** When the evidence is shuffled within-label, R4 strong_F1 collapses by roughly 46x, well below the claim-only baseline. This indicates R4 is not ignoring the evidence entirely.
- **Title-only and metadata-only baselines.** Both controls sit well below R4 strong_F1, indicating that document title and metadata fields are not sufficient substitutes for the retrieved evidence.
- **Lexical cue audit.** The leakage audit includes a lexical-cue probe that checks whether high-frequency claim tokens alone predict the label; the probe does not exceed the claim-only baseline.
- **Leakage audit overall.** 12/12 checks PASS with strongest_concern = none; the claim-only ratio is the largest observed shortcut signal and is still below the warning threshold.

## 4. Evidence file

- `experiments/leakage_audit_v1/claim_only_baseline.json`
- `experiments/leakage_audit_v1/audit_summary.md`
- `experiments/metric_robustness_v1/classification_metrics_with_ci.csv`
- `experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv`
- `reports/leakage_quick_scan_v3_17.md`

## 5. Safe response

We answer the reviewer as follows: claim-only signal exists and is reported as a limitation, not hidden. Claim-only strong_F1 = 0.2448 (ratio 0.5436 to R4, below the 0.8 warning threshold). Shuffled-evidence, title-only, and metadata-only controls all collapse well below R4, and the lexical-cue probe does not exceed the claim-only baseline. These results indicate that R4 uses the retrieved and canonicalized evidence beyond what is predictable from the claim alone, but they do not prove that R4 is fully shortcut-free.

The safe empirical conclusion is therefore narrow: **R4 substantially exceeds the claim-only ceiling on this silver set, and the canonicalization contribution (oracle_recall 0.043 → 0.387, 9x improvement) is meaningful at the retrieval-to-screening interface. The residual claim-only signal is a reported limitation and motivates the planned human audit.**

## 6. Remaining limitation

- Claim-only strong_F1 = 0.2448 is non-zero; R4 is not a fully shortcut-free model.
- The claim-only ratio (0.5436) is below the 0.8 warning threshold but is not zero; a stricter reviewer may still consider 0.54 high.
- The claim-only baseline is computed on silver labels; under human adjudication the claim-only signal could rise or fall.
- The leakage audit covers structural shortcuts; subtle semantic shortcuts (e.g., claim phrasing systematically co-occurring with labels) cannot be fully ruled out without human audit.
- Format-shift R4 evaluation (which would directly test whether R4 depends on evidence format) is blocked by sklearn version mismatch (see response 03); this leaves the shortcut analysis incomplete on the format axis.

## 7. Paper text to add

> "We report a claim-only baseline to quantify the shortcut risk. Claim-only strong_F1 = 0.2448 (10-seed mean), with ratio claim-only / R4 = 0.5436, below the 0.8 warning threshold defined in our leakage audit protocol. Shuffled-evidence, title-only, and metadata-only controls all collapse well below R4, and the lexical-cue probe does not exceed the claim-only baseline. These results indicate that R4 uses the retrieved and canonicalized evidence beyond what is predictable from the claim alone, but they do not prove that R4 is fully shortcut-free. The residual claim-only signal is a reported limitation. A direct format-shift R4 evaluation, which would further constrain the shortcut interpretation, is blocked by sklearn version mismatch and is documented as a permanent limitation (see response 03)."

## 8. What not to claim

| Unsafe wording (forbidden) | Why forbidden |
|---|---|
| "R4 is shortcut-free" | claim-only strong_F1 = 0.2448 is non-zero; ratio 0.5436 is below threshold but not zero |
| "claim-only signal is absent" | claim-only strong_F1 = 0.2448 is a real, reported signal |
| "format-shift evaluation proves shortcut absence" | format-shift R4 evaluation is blocked; metrics not reported |
| "human audit confirmed shortcut-free" | human audit is staged, not executed |
| "the evidence is necessary and sufficient" | evidence is helpful (R4 >> claim-only) but not proven necessary in all cases |

---

*End of response 02.*
