# Archive — Legacy and Future-Work Material

**Date:** 2026-07-06

## Purpose

This directory (and any subdirectories) contains **legacy and future-work material**. None of the material here represents the current empirical claim of the repository.

## Current mainline

The current mainline is **Confidential Lightweight V3.17**. See `CURRENT_MAINLINE.md` and `docs/current_mainline_v3_17_confidential.md` for the authoritative current specification.

## What is in this archive

Material in this archive falls into three categories:

### 1. Legacy pilot (superseded)

- **V2 evidence-aware hierarchical pilot.** The V2 paper-readiness pilot (`paper_versions_ordered/V2_evidence_aware_hierarchical/`, `experiments/paper_readiness_v2_evidence_aware/`) is a legacy pilot. It is superseded by the V3.17 mainline. Do not cite V2 as the current manuscript.

- **simclaim_human_pilot workflow.** The `simclaim_human_pilot` → `release_simclaim_human_pilot` → `paper_assets/simclaim_human_pilot` workflow is a legacy workflow. It is superseded by the V3.17 mainline. Do not cite it as the current paper mainline.

### 2. Future architecture (not current empirical claim)

- **Full shared-threshold CESE-OCN neural architecture.** The dual-branch ordinal calibration network with shared thresholds (`cese/models/`, `cese/losses/`, `cese/calibrator/`) is a future architecture candidate. It is NOT the current empirical claim. The current V3.17 mainline uses R4 (a feature-based screening router), not the full CESE-OCN neural architecture. Do not cite the full architecture as validated.

### 3. Historical diagnostics (superseded)

- Older experiment directories marked `historical` or `superseded` in `_MAINLINE_CURRENT/_EXPERIMENT_STATUS_REGISTRY.csv` are historical diagnostics. They may contain useful methodology or negative results, but their metrics are superseded by the V3.17 frozen reference.

## How to use this archive

- **Read for context.** Understanding the project's evolution is valid. Reading legacy code for design lessons is valid.
- **Do not cite as current.** Any claim from this archive must be labeled as "legacy," "historical," "superseded," or "future architecture."
- **Do not re-run as mainline.** Legacy experiments should not be re-run as if they produce current mainline results. The V3.17 mainline is the only current empirical claim.
- **Do not delete.** Legacy material is preserved for provenance and future reference. It is not deleted.

## Cross-reference

- Current mainline: `CURRENT_MAINLINE.md`
- Detailed mainline spec: `docs/current_mainline_v3_17_confidential.md`
- Experiment status registry: `_MAINLINE_CURRENT/_EXPERIMENT_STATUS_REGISTRY.csv`
- Stale claims audit: `project_synthesis/mainline_realignment_v1/stale_claims_audit.csv`
- Forbidden old claims: `_MAINLINE_CURRENT/_DO_NOT_USE_OLD_CLAIMS.md`
