# Current Mainline

## Confidential Lightweight V3.17

The current empirical mainline is **Confidential Lightweight V3.17: Local Evidence Canonicalization and Review Queueing for Simulation Claim Escalation Screening**.

```text
private/local PDFs
→ local PDF text extraction
→ BM25 sentence/window retrieval
→ best_sentence_top5_overlap evidence canonicalization
→ frozen R4 out-of-fold screening
→ conservative/SmartQueue ranking
→ human review queue
```

## Safe claims

- local / no-API / no-cloud / no-training pipeline
- controlled silver diagnostic setting
- retrieval-to-screening format shift analysis
- evidence canonicalization restores strong_action_overclaim screening signal
- second-stage review queue support

## Not safe claims (do NOT make)

- no gold benchmark claim
- no human-audited dataset claim
- no SOTA claim
- no natural-prevalence claim
- no full shared-threshold CESE-OCN validation claim
- no automatic peer review claim
- no standalone detector claim

## Current key scripts

- `scripts/run_simclaim_pdf_retrieval_v1.py` — local PDF text extraction + BM25 retrieval
- `scripts/run_r4_evidence_canonicalization_v1.py` — evidence canonicalization (best_sentence_top5_overlap)
- `scripts/run_canonicalized_review_queue_v1.py` — frozen R4 OOF screening + review queue
- `scripts/run_canonicalized_risk_ranking_v1.py` — conservative/SmartQueue ranking

## Legacy / future materials

- **V2 evidence-aware hierarchical pilot** = legacy pilot (superseded)
- **simclaim_human_pilot** = legacy workflow (superseded)
- **full shared-threshold CESE-OCN neural architecture** = future architecture, not current empirical claim

See `docs/current_mainline_v3_17_confidential.md` for the detailed mainline specification, `docs/data_release_policy.md` for confidentiality, and `docs/leakage_and_confidentiality_policy.md` for forbidden-field rules.
