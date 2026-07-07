# Data Release Policy

**Date:** 2026-07-06
**Scope:** This policy governs what data is released and what is withheld for the Confidential Lightweight V3.17 mainline.

---

## Released

The following are safe to release alongside source code:

- **Source code.** All pipeline scripts (`scripts/run_*.py`), classifier code, and reproduction entry points.
- **Schemas.** Data schemas (`cese/data/schema.py`), label mappings, feature column definitions, and threshold configurations.
- **Toy synthetic fixtures.** `data/toy/*.jsonl`, `data/pilot_template.jsonl`, and any synthetic data explicitly marked `paper_valid=False` / `result_scope="pilot_diagnostic"`. These pass schema validation but are NOT human-audited and NOT paper-ready.
- **Aggregate metrics.** Frozen metric tables (strong_F1, P@k, R@k, FP/TP, macro_F1) in `_MAINLINE_CURRENT/_FINAL_NUMBERS_FOR_PAPER.csv` and experiment gate JSONs. These contain only aggregate numbers, no raw text.
- **Hash manifest format.** The structure of hash manifests (field names, hash algorithm) is documented. Actual hashes of confidential content are NOT released if they could enable fingerprinting of source documents.
- **Redacted examples.** Synthetic or heavily redacted example pairs that do not reveal source document content, clearly labeled as illustrative and not from the real corpus.

## Not released

The following are NOT released because they would reveal confidential source documents:

- **Raw PDFs.** The original private/local PDF corpus is not released.
- **Raw evidence text.** Actual evidence spans extracted from source PDFs are not released.
- **Real claim text.** Real claim strings from the SimClaim candidate pool are not released in raw form.
- **Source document excerpts.** Any text excerpt that could be traced back to a specific source document is not released.
- **Real review queues.** Review queue outputs containing real claim/evidence text are not released. Only aggregate queue statistics (e.g., P@20, R@100) are released.
- **Anything that reveals confidential source documents.** This includes, but is not limited to: PDF filenames of real source documents, page numbers paired with real text, BM25 chunk text, NLI cache contents (which contain real sentence text), and canonicalization selector outputs on real data.

## Boundary cases

- **SimClaim candidate pool CSV (`strict_silver_max_candidates_v1.csv`).** This file contains real claim text and real evidence text. It is NOT released externally. It is used internally for evaluation only.
- **NLI cache (`nli_top5_cache.npz`).** Contains real sentence text. NOT released.
- **R4 artifacts.** Classifier weights, scalers, and thresholds do not contain raw text. They ARE released (they are model parameters, not data).
- **Experiment gate JSONs.** Contain only aggregate metrics and pass/fail flags. Released.
- **Per-candidate prediction CSVs.** Contain candidate IDs and predicted labels but may join to real text. Released only if candidate IDs are anonymized and cannot be joined to raw text by an external party.

## Enforcement

- `.gitignore` excludes raw PDFs, real evidence text files, and NLI caches from the repository.
- Release packaging scripts must run a confidentiality check before zipping: no file in the release may contain raw evidence text or real claim text.
- Any uncertainty about whether a file is releasable should default to NOT released.
