# ForceBench Feasibility Report

**Task:** No-Gold RIGOURATE + Public Benchmark Pipeline Part 2 - Section 2
**Date:** 2026-07-05

## 1. ForceBench description

ForceBench [X et al., 2026] is a contrastive evidence-force calibration benchmark that fixes the cited evidence passage and compares a *calibrated claim* against a *force-raised claim* along five force dimensions:

1. **relation** — the type of evidence-claim relation
2. **modality** — the strength of the claim (e.g., possible vs. certain)
3. **scope** — the breadth of the claim (e.g., specific vs. general)
4. **temporal validity** — the time frame of the claim
5. **numeric specificity** — the precision of quantitative claims

The benchmark supplies a monotonic preference signal: a model should rank the calibrated claim above the force-raised claim.

## 2. Availability check

| Resource | Status |
| --- | --- |
| ForceBench paper | referenced in related work; full text not located in this audit |
| GitHub repository | **not located** |
| HuggingFace dataset | **not located** |
| Downloadable data bundle | **not located** |
| Code/scripts | **not located** |
| Scope/relation axis labels | **not accessible** |
| calibrated vs. force-raised claim pairs | **not accessible** |
| Evidence passages | **not accessible** |
| Offline-readable format | **not accessible** |

## 3. Feasibility conclusion

**Status: blocked**

ForceBench is referenced in related work (V3.13 differentiation) as a contrastive evidence-force calibration benchmark with calibrated vs. force-raised claim pairs along five force dimensions (relation, modality, scope, temporal validity, numeric specificity). However, as of audit date 2026-07-05, no public GitHub repository, HuggingFace dataset, or downloadable data bundle has been located via web search. The ForceBench paper is referenced but the dataset is not publicly accessible. Consequently, no non-API subset analysis could be performed.

## 4. What we would do if ForceBench were available

If ForceBench data became publicly available, the non-API subset analysis would:

1. Extract scope + relation axes (max 80 pairs).
2. Use local scoring methods:
   - TF-IDF similarity between calibrated and force-raised claims.
   - Reuse local NLI features if available (currently blocked).
   - No large model download, no API calls.
3. Compute monotonic violation rate (MVR):
   - For each pair, score calibrated_claim and force_raised_claim.
   - Monotonicity holds if calibrated_claim_score > force_raised_claim_score.
   - MVR = fraction of pairs where monotonicity is violated.
4. Report MVR per force dimension and overall.

## 5. Implications for the main line

ForceBench being blocked means:
- We cannot directly compare CESE-OCN's relation typing to ForceBench's contrastive preference formulation.
- We cannot validate our scope distinction against ForceBench's scope axis.
- The differentiation between CESE-OCN and ForceBench remains at the conceptual level (typing vs. preference), not empirical.

This is not fatal to the main line: ForceBench is a related but different formulation (preference vs. typing), and the core differentiation argument holds without direct empirical comparison. However, the lack of ForceBench data means the "contrastive preference" comparison remains a conceptual positioning argument, not an empirical result.

## 6. Prohibitions enforced

- No paid API calls.
- No gold creation.
- No silver-as-gold.
- No claiming proxy as official ForceBench.
- No fabrication of ForceBench data or results.
- No modification of original data or V3.15 paper.
