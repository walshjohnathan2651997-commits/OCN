# Submission Limitations Box — V3.17 Confidential Lightweight

**Manuscript:** Local Evidence Canonicalization for Offline Simulation-Claim Review Queues
**Generated:** 2026-07-07

> This is the frozen limitations box for the V3.17 submission. It must be reproduced verbatim in the manuscript (Section 13) and in any cover note / response to reviewers. No limitation may be removed without an explicit gate rerun and a new manuscript version.

---

## Limitations (verbatim)

1. **Silver labels, not gold.** All 444 candidates have `human_audited=False` and `gold_label` empty. Silver labels (`candidate_label_guess`) are used as `true_label` for metrics only. **This is a controlled silver diagnostic study, not a gold benchmark.**

2. **Human audit staged, not executed.** A small targeted human audit protocol and seed queue are prepared; the audit has not been executed. We do not report human-audited benchmark results. Paper wording: "small targeted human audit protocol and seed queue prepared; audit not yet executed."

3. **Format-shift R4 evaluation completed with environment note.** Variant construction (3552 rows, 8 variants), NLI feature extraction, and frozen R4 prediction were completed using a local scikit-learn 1.9.0 environment (the exact version the frozen R4 artifacts were pickled with), run offline with `HF_HUB_OFFLINE=1`. No network, no API, no retraining, and no model-artifact modification were involved. Canonicalized evidence (`canonicalized_best_sentence_top5`) achieves strong_F1=0.4615, close to the oracle upper bound (0.4627) and substantially above raw BM25 chunks (0.2755). Reproducibility note: reviewers need scikit-learn >= 1.5.0 to re-run the R4 prediction step; the redacted public variant inputs allow independent reproduction. Results are diagnostic (silver labels, frozen R4), not benchmark-level.

4. **Six domains only.** Coverage: autonomous_driving (140), policy_simulation (84), digital_twin (68), cyber_defense (64), marl (52), robotics (36). Not a general scientific claim benchmark.

5. **Deployment-specific Pareto result.** The complexity-vs-utility Pareto result shows deterministic canonicalization is optimal under the confidential / no-API / no-training / silver-diagnostic constraint set. It does **not** prove rules generally beat learned models.

6. **No SOTA claim.** We do not claim SOTA on simulation-claim screening. We do not claim a validated general detector. We do not claim an automatic peer reviewer. We do not claim full CESE-OCN neural architecture validation.

7. **CI reflects controlled pool variability, not natural prevalence.** Bootstrap CIs are group-aware (group-level resampling, 100 bootstrap iterations) over the controlled 444-candidate pool. They do not estimate performance under natural prevalence.

8. **Redteam high-risk findings are internal-only.** 3 high-risk `forbidden_sorting_field` findings exist in internal scoring files. They are excluded from the public release bundle; the release safety gate PASS.

---

## Forbidden rewrites (must not be used to "soften" the limitations)

- Do **not** rewrite limitation 1 as "labels are validated" or "labels are reliable".
- Do **not** rewrite limitation 2 as "human audit completed" or "human-validated dataset".
- Do **not** rewrite limitation 3 as "format-shift metrics are validated" or "benchmark-level format-shift results". (The evaluation is complete, but results are diagnostic, not benchmark-level, due to silver labels and frozen R4.)
- Do **not** rewrite limitation 5 as "rules beat learned models" or "deterministic methods are universally better".
- Do **not** rewrite limitation 6 as "SOTA on simulation-claim screening" or "validated general detector".
- Do **not** rewrite limitation 7 as "CI estimates natural-prevalence performance".
- Do **not** rewrite limitation 8 as "redteam scan clean" or "no internal-only findings".

---

## Source files for each limitation

| # | Limitation | Source file |
|---|---|---|
| 1 | Silver labels, not gold | `docs/dataset_version_lock_v3_17.md`; `data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/strict_silver_max_candidates_v1.csv` |
| 2 | Human audit staged | `docs/human_audit_protocol_v1.md`; `data/audit_templates/human_audit_queue_seed_v1_redacted.csv`; `reports/final_perfect_state_gate_v3_17.md` (check 6.4 WARNING) |
| 3 | Format-shift R4 completed | `experiments/format_shift_ablation_v1/format_shift_metrics.csv`; `reports/sklearn_offline_compatibility_investigation_v3_17.md`; `experiments/format_shift_ablation_v1/r4_eval_blocked.json` (status=resolved) |
| 4 | Six domains only | `docs/dataset_version_lock_v3_17.md` |
| 5 | Deployment-specific Pareto | `experiments/complexity_vs_utility_ablation_v1/method_pareto_table.csv` |
| 6 | No SOTA claim | `paper_assets/v3_17_confidential/paper_claims_checklist.md` |
| 7 | CI is controlled-pool | `experiments/metric_robustness_v1/classification_metrics_with_ci.csv` |
| 8 | Redteam internal-only | `reports/redteam_release_reconciliation_v3_17.md`; `reports/release_safety_manifest_v3_17.json` |

---

*End of limitations box.*
