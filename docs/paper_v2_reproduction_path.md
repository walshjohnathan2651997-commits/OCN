# Paper V2 Reproduction Path

This file defines the current authoritative reproduction path for the V2 manuscript:

`paper_versions_ordered/V2_evidence_aware_hierarchical/V2_CESE_OCN_evidence_aware_hierarchical_pilot.docx`

## Current paper position

The V2 manuscript is a silver-label pilot paper. It is **not** a gold benchmark, **not** a human-audited dataset paper, and **not** a completed full CESE-OCN neural architecture paper.

The current empirical mainline is:

```text
strict_silver_max_v1
→ frozen encoder baselines
→ cross_encoder_nli_pair escalation_binary result
→ evidence sanity check: correct evidence > shuffled / empty / title-only
→ paper_readiness_v2_evidence_aware
```

## Main dataset

```text
data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/strict_silver_max_candidates_v1.csv
```

Current status:

- 111 evidence groups
- 444 claim candidates
- 6 domains
- 4 labels per group
- source trace complete
- label source: `candidate_label_guess`
- silver only; not gold; not human-audited

## Main scripts

Run these in order from `D:\ocn`:

```powershell
python scripts/build_strict_silver_max_v1.py
python scripts/run_frozen_encoder_v1.py
python scripts/run_evidence_sanity_check_v1.py
python scripts/run_paper_v2_bootstrap_ci.py
python scripts/run_paper_v2_domain_holdout.py
python scripts/build_paper_readiness_v2.py
python scripts/build_cese_ocn_v2_docx.py
```

## Main output folders

```text
data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/
experiments/evidence_aware_frozen_encoder_v1/
experiments/evidence_aware_sanity_check_v1/
experiments/paper_v2_bootstrap_ci/
experiments/paper_v2_domain_holdout_v1/
experiments/paper_readiness_v2_evidence_aware/
paper_versions_ordered/V2_evidence_aware_hierarchical/
```

## Main results to cite

| Claim | Supported by |
|---|---|
| Strict silver data has 111 groups / 444 claims | `strict_silver_max_summary.json` |
| TF-IDF does not reliably use evidence | `frozen_encoder_summary.json`, `table_key_results.csv` |
| Cross-encoder NLI pair is strongest on escalation_binary | `frozen_encoder_summary.json` |
| Correct evidence beats shuffled and empty evidence | `evidence_sanity_decision_gate.json` |
| Flat 4-class remains exploratory | `frozen_encoder_decision_gate.json` |
| Cross-encoder improvement has positive 10-seed bootstrap CI | `paper_v2_bootstrap_ci/bootstrap_ci_summary.json` |
| Cross-encoder generalizes in leave-one-domain-out pilot | `paper_v2_domain_holdout_v1/domain_holdout_summary.json` |

## Current safe claims

Safe:

- Source-traceable silver pipeline is operational.
- Hierarchical escalation detection is more viable than flat four-class detection under current data.
- Frozen NLI cross-encoder features provide stable evidence-specific signal on escalation_binary.
- Correct evidence outperforms shuffled, empty, and title-only controls.

Not safe:

- Do not claim gold benchmark.
- Do not claim human-audited dataset.
- Do not claim SOTA.
- Do not claim the full CESE-OCN shared-threshold network has been empirically validated.
- Do not claim flat four-class ordinal calibration is solved.

## Relationship to older code

Older CESE-OCN architecture, human-pilot, hardpair, LLM, and release-pipeline code remains useful as development history and future work. It is not the current V2 manuscript reproduction path unless explicitly referenced above.
