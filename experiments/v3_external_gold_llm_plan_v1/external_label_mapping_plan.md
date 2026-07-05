# External Label Mapping Plan (Conservative)

> **Critical constraint**: Public datasets use support/refute/NEI-style labels. 
> They CANNOT be mapped to `strong_action_overclaim` or `mild_scope_overclaim` 
> because no public dataset annotates action/deployment/safety overclaim. 
> Public data tests binary support-vs-contradiction and support-vs-non-support only.

> A third bucket `unsupported_or_insufficient` is introduced for external-only use. 
> It is NOT a V3 label and must not be merged into SimClaim gold.

## Mapping Table

| Dataset | Source Label | V3 External Label | Confidence | Rationale |
|---|---|---|---|---|
| SciFact | SUPPORT | supported | high | Direct support relation maps cleanly to V3 supported. |
| SciFact | CONTRADICT | contradiction_candidate | high | Direct contradiction relation maps cleanly to V3 contradiction_candidate. |
| SciFact | NEI / NOT_ENOUGH_INFO | unsupported_or_insufficient | high | Insufficient evidence is a distinct bucket; maps to a 3rd external-only class. |
| VitaminC | SUPPORTS | supported | high | Direct support. |
| VitaminC | REFUTES | contradiction_candidate | high | Direct refutation. |
| VitaminC | NOT_ENOUGH_INFO | unsupported_or_insufficient | high | Insufficient evidence. |
| FEVER | SUPPORTED | supported | high | Direct support. |
| FEVER | REFUTED | contradiction_candidate | high | Direct refutation. |
| FEVER | NOT ENOUGH INFO | unsupported_or_insufficient | high | Insufficient evidence. |
| PubHealth | true | supported | high | Claim is true given evidence. |
| PubHealth | false | contradiction_candidate | medium | Claim is false; approximately maps to contradiction but is truth-value based, not evidence-relation based. |
| PubHealth | mixture | unsupported_or_insufficient | medium | Mixed support; treated as insufficient for a single clean verdict. |
| PubHealth | unproven | unsupported_or_insufficient | high | No sufficient evidence. |
| AVeriTeC | Supported | supported | high | Direct support. |
| AVeriTeC | Refuted | contradiction_candidate | high | Direct refutation. |
| AVeriTeC | Not Enough Evidence | unsupported_or_insufficient | high | Insufficient evidence. |
| AVeriTeC | Conflicting | unsupported_or_insufficient | medium | Conflicting evidence; not a clean contradiction, bucketed as insufficient. |
| AVeriTeC | Cherry-picking | unsupported_or_insufficient | low | Cherry-picking weakly resembles mild_scope_overclaim but is NOT equivalent. Conservatively bucketed as insufficient rather than mapped to overclaim. |

## Per-Dataset Recommended Use

- **SciFact**: scientific-domain contradiction/support external test (Task E1, E2).
- **VitaminC**: evidence sensitivity / contrastive evidence test (Task E3).
- **FEVER**: optional general fact-verification sanity check; not a primary result.
- **PubHealth**: health-domain support vs non-support external test (Task E2).
- **AVeriTeC**: complex fact-checking support vs non-support sanity check (Task E2).

## Forbidden Mappings

- NEVER map any public label to `strong_action_overclaim`.
- NEVER map any public label to `mild_scope_overclaim`.
- NEVER treat `unsupported_or_insufficient` as a SimClaim gold label.
- NEVER average public-dataset F1 with SimClaim F1 in the main results table.
