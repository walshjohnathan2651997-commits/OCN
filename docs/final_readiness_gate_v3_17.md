# Final Readiness Gate — V3.17 Confidential Lightweight

**Authority:** This document is the pre-submission readiness gate for the
V3.17 Confidential Lightweight mainline. All items must be satisfied
before declaring the project "near-perfect ready" for submission.

**Scope:** Confidential Lightweight V3.17 mainline only. Does not apply
to legacy V2 pilot or future full CESE-OCN neural architecture work.

---

## Pre-submission requirements

Every item below must be `done` or explicitly `blocked-with-reason`
before the project is declared submission-ready. `blocked-with-reason`
is acceptable for items that are intentionally out of scope for V3.17
(e.g., full human audit), but the blocker must be documented here.

### 1. P0 real experiments complete

- **Requirement:** All P0 real-data experiments have run end-to-end on
  the 444-candidate silver diagnostic set and produced paper-ready
  outputs.
- **P0 stages:** `bm25_real`, `canonicalizer_real`, `format_shift_real`,
  `leakage_real`, `error_taxonomy`, `metric_robustness`.
- **Verification:**
  - `experiments/<stage>_v1/` directories exist with `run_config.json`
    and at least one results file.
  - `reports/current_project_status_v3_17.md` marks each P0 item as
    `done` or `blocked` with a documented reason.
  - `make p0-real --allow_private_data true` runs to completion without
    unexpected failures (blocked-by-missing-data is acceptable if
    documented).
- **Status:** ✅ done (PDF corpus blocked — see item 2 below; all other
  P0 stages ran on real data)

### 2. PDF-start extraction complete or blocked reason documented

- **Requirement:** Either (a) the real PDF sentence corpus has been
  built and verified, or (b) the blocker is explicitly documented
  (e.g., PDFs available locally only, extraction deferred to camera-ready
  phase).
- **Verification:**
  - `data/pdf_corpus_v1/sentences.jsonl` exists, OR
  - `reports/current_project_status_v3_17.md` lists PDF corpus as
    `blocked` with a clear `blocker:` note.
  - The PDF stress test (`experiments/pdf_extraction_stress_test_v1/`)
    must always run on synthetic data to verify extraction robustness.
- **Status:** ✅ blocked-with-reason — real PDFs are confidential and
  not committed to the repo; corpus build runs only on the private
  machine. Stress test on synthetic data passes (12/12 documents).

### 3. Leakage audit (real) complete

- **Requirement:** The 12-rule leakage audit has run on the real
  444-candidate dataset and reports `PASS` (no significant shortcuts or
  leakage).
- **Verification:**
  - `experiments/leakage_audit_v1/audit_summary.json` exists with
    `overall_result: PASS`.
  - `experiments/leakage_audit_v1/audit_summary.md` lists every rule
    and its verdict.
  - Claim-only baseline and shuffled-evidence baseline are both
    reported (claim-only must be substantially below R4's strong_F1).
- **Status:** ✅ done — 7/7 (now 12/12) checks PASS, claim-only
  strong_F1 = 0.2448 (54% of R4's 0.4503), correct/shuffled evidence
  ratio = 46x.

### 4. Format-shift ablation (real) complete

- **Requirement:** The format-shift ablation has run on real data and
  documents the retrieval-to-screening signal change across at least
  four input formats (raw chunks, sentences, windows, oracle-best).
- **Verification:**
  - `experiments/format_shift_ablation_v1/` exists with per-format
    results.
  - The summary table shows that best_sentence_top5_overlap restores
    strong_action screening signal relative to raw_top1_chunk.
  - R4 evaluation may be blocked by sklearn version mismatch (1.9.0 vs
    1.4.1) — acceptable if documented.
- **Status:** ✅ done (R4 eval partial — sklearn version blocker
  documented in schema validation report)

### 5. Human audit (optional but protocol exists)

- **Requirement:** A human audit protocol exists. A full human audit is
  optional for V3.17 (which is a silver diagnostic, not a gold
  benchmark), but the protocol must be in place so a future audit can
  run without redesigning the pipeline.
- **Verification:**
  - `docs/human_audit_protocol_v1.md` exists.
  - `data/audit_templates/human_audit_template.csv` exists with the
    required fields.
  - `scripts/build_human_audit_queue_v1.py` runs and produces a
    redacted audit queue.
  - `scripts/summarize_human_audit_v1.py` exists (runs only after
    annotation returns).
- **Status:** ✅ done — protocol exists, queue builder runs, summary
  script in place. Full audit deferred (silver diagnostic, not gold).

### 6. Redteam scan: high risk = 0

- **Requirement:** The confidentiality red-team scanner reports
  `high_risk_count == 0` across the full scan (or any HIGH findings are
  explicitly downgraded via the `--private_allowlist` mechanism with a
  documented justification).
- **Verification:**
  - `experiments/confidentiality_redteam_scan_v1/redteam_summary.json`
    reports `high_risk_count: 0` and `pass_public_release_gate: true`.
  - `experiments/confidentiality_redteam_scan_v1/private_intermediate_allowlist.json`
    exists and documents any downgraded findings with justifications.
  - `make redteam` runs to completion with `high_risk=0`.
- **Status:** ✅ done — high_risk=0, two private intermediate scoring
  files downgraded to LOW via allowlist with justifications.

### 7. Paper assets generated

- **Requirement:** All paper-ready tables, figures, and checklists are
  generated under `paper_assets/v3_17_confidential/`.
- **Verification:**
  - 8 tables (table1–table8) with `.md` and `.tex` versions.
  - `paper_results_summary.md` organized by RQ1–RQ8.
  - `paper_claims_checklist.md` with safe-claim / unsafe-claim sections
    and evidence file pointers.
  - `run_config.json` records the generation timestamp and guards.
- **Status:** ✅ done — 8 tables, RQ1–RQ8 summary, claims checklist
  with C1–C8 caveats.

### 8. README current line clean

- **Requirement:** `README.md` and `CURRENT_MAINLINE.md` declare
  Confidential Lightweight V3.17 as the current mainline and do NOT
  mark V2 (or any older line) as current.
- **Verification:**
  - `tests/test_current_mainline_docs.py` passes.
  - Both files contain "V3.17", "confidential", and "lightweight".
  - Neither file frames V2 as the current empirical mainline.
- **Status:** ✅ done — both files declare V3.17 confidential
  lightweight as current; V2 is explicitly listed under "legacy /
  future materials".

### 9. Release bundle sanitized

- **Requirement:** The public sanitized release bundle exists under
  `release_bundles/v3_17_confidential_public/` and contains no PDFs,
  no raw claim/evidence text, and no forbidden binary types.
- **Verification:**
  - `release_bundles/v3_17_confidential_public/REDACTION_REPORT.json`
    certifies `contains_real_pdf: false`,
    `contains_raw_evidence_text: false`,
    `contains_real_claim_text: false`.
  - `tests/test_release_bundle_safety.py` passes.
  - Bundle redteam scan reports `high_risk_count: 0`.
  - Bundle includes `MANIFEST.json`, `README.md`, `CURRENT_MAINLINE.md`,
    `LICENSE_NOTICE.md`.
- **Status:** ✅ done — 221 files included, 12 excluded, redteam PASS,
  no PDFs, no raw text fields.

---

## Acceptance commands

The following commands must all succeed (or skip gracefully with a
documented reason) before submission:

```bash
# CI-safe quick check
make toy

# Full readiness gate (status + redteam + schema + tests + summary)
make final-check

# Targeted test subset
pytest -q \
  tests/test_current_mainline_docs.py \
  tests/test_no_private_text_in_public_outputs.py \
  tests/test_pipeline_runner_toy.py \
  tests/test_release_bundle_safety.py \
  tests/test_redteam_scan_toy_passes.py \
  tests/test_paper_assets_no_private_text.py
```

The following commands require explicit private-data authorization and
must NOT be triggered by CI:

```bash
# Real-data P0 (requires --allow_private_data true)
make p0-real

# Full pipeline on real data
python scripts/run_v3_17_confidential_pipeline.py \
  --mode real --allow_private_data true
```

---

## Hard boundaries (always enforced)

- No LLM / API / cloud calls in the mainline pipeline
- No new model training
- No original data modification
- No silver-as-gold claim
- No automatic peer-review claim
- No standalone-detector claim
- No real PDFs committed to the repo
- No real claim/evidence text in public artifacts
- Real-mode runs require `--allow_private_data true`
- CI runs only toy / synthetic data

---

## Sign-off

When all nine items above are `done` or `blocked-with-reason` and the
acceptance commands pass, the V3.17 Confidential Lightweight mainline
is ready for submission as a controlled silver-diagnostic paper.
