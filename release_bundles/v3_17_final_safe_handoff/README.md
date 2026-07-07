# V3.17 Final Safe Handoff Bundle

This bundle is the **final delivery pack** for the V3.17 Confidential Lightweight
mainline. It lets a reviewer understand the project state, contributions,
limitations, what is public, and what is private — without exposing any
confidential content.

## What this bundle IS

- One-page status card and final delivery manifest
- Submission manuscript (v2 Final Freeze), 8 result tables, result source map
- Final perfect-state gate, artifact ledger, release safety manifest
- Reviewer response playbook and risk register
- Dataset version lock and safe-claims dictionary
- Aggregate experiment summaries (metric CSVs, summary JSON/MD)
- Redacted audit summaries and redteam reconciliation
- Public release bundle MANIFEST + REDACTION_REPORT (for traceability)

## What this bundle is NOT

- It is NOT the code pack (code lives in `v3_17_confidential_public`).
- It is NOT the toy-data pack (toy data lives in `v3_17_confidential_public`).
- It does NOT contain any private/raw content (see hard boundaries below).

## Hard boundaries (enforced by the builder + redteam scan)

- No private audit CSV (`data/private_audit/`).
- No PDFs (`*.pdf`).
- No raw claim/evidence text (`claim_text`, `evidence_text`, `selected_evidence`, `raw_text`).
- No pkl/joblib/model artifacts (`*.pkl`, `*.joblib`, `*.npz`).
- No `data/private/`, no `data/private_audit/`.
- No `*.docx`, `*.xlsx`.
- No unredacted CSV with text columns.

## Mandatory framing

This is a **controlled silver diagnostic study**, not a gold benchmark.
**Not SOTA. Not an automatic peer reviewer. Not a validated general detector.**
The system is a second-stage review queue generator, not a standalone detector.
