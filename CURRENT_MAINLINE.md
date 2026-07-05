# Current Mainline

The current empirical mainline is:

## V3.17 Canonicalized R4 Baseline

```text
PDF corpus
→ BM25 top-k retrieval
→ best_sentence_top5_overlap evidence canonicalization
→ frozen R4 OOF screening
→ G_conservative_precision risk ranking
→ second-stage human review queue
```

## What this project currently claims

This project studies retrieval-to-screening format shift in offline simulation claim evidence-sufficiency review. It shows that raw retrieved PDF chunks can harm downstream R4 screening, and that simple unsupervised evidence canonicalization restores strong_action_overclaim screening signal sufficiently for second-stage review queue construction.

## What this project does not claim

- not gold labels
- not human-audited benchmark
- not SOTA
- not natural-distribution prevalence
- not full shared-threshold CESE-OCN validation
- not a standalone classifier
- not automatic peer review
- not a replacement for human judgment

## Current key scripts

- `scripts/run_simclaim_pdf_retrieval_v1.py`
- `scripts/run_r4_evidence_canonicalization_v1.py`
- `scripts/run_canonicalized_review_queue_v1.py`
- `scripts/run_canonicalized_risk_ranking_v1.py`

## Legacy material

Older V2 paper-readiness, simclaim_human_pilot, and full CESE-OCN architecture materials are preserved as development history or future work unless explicitly referenced by this file. See `docs/current_mainline_v3_17.md` for the detailed mainline specification, and the "Historical / development context" section of `README.md` for the legacy architecture description.
