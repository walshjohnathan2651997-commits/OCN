# 10 — Master Reviewer Response Table

**Purpose.** This table consolidates the 9 reviewer response files into a single index. Each row maps a reviewer attack to its severity, evidence, current status, safe answer, limitation, and the manuscript section where the response is integrated. The table is the single source of truth for rebuttal navigation; the individual response files (01–09) provide the full text.

**Status legend.**
- **PASS** — evidence complete, claim supportable as stated.
- **WARNING** — evidence partial or conditional; claim must be narrowed.
- **BLOCKED** — evidence incomplete due to environmental constraint; metrics not reported.
- **FAIL** — would indicate an unsupported claim; not present in this submission.

**Final gate reference.** `READY_WITH_LIMITATIONS` (PASS=40, WARNING=3, BLOCKED=1, FAIL=0).

---

## Master table

| Risk ID | Reviewer attack | Severity | Evidence | Current status | Safe answer | Limitation | Manuscript section |
|---|---|---|---|---|---|---|---|
| A | 444 candidates are GPT/silver; results may be silver-labeler contingency | High | Dataset lock (SHA256, 444 rows, 111 groups, 4 balanced labels); leakage audit 12/12 PASS; claim-only strong_F1=0.2448 (ratio 0.5436 <0.8); shuffled-evidence 46x collapse; group split integrity | WARNING (silver labels, no human audit) | Results support a retrieval-to-screening diagnostic on this controlled silver set; not general model validation | Silver labels (`human_audited=False`, `gold_label` empty); no human audit; 6 domains only | §6 Dataset and Boundaries; §1 Abstract framing |
| B | R4 may have learned only claim template (claim-only shortcut) | High | Claim-only strong_F1=0.2448 (ratio 0.5436 <0.8); shuffled/title-only/metadata baselines collapse; lexical cue probe ≤ claim-only; leakage audit 12/12 PASS | WARNING (residual claim-only signal) | R4 substantially exceeds claim-only ceiling; not fully shortcut-free; residual signal is a reported limitation | Claim-only signal non-zero (0.2448); format-shift R4 eval blocked; subtle semantic shortcuts not ruled out | §10 Leakage and Shortcut Audits; §13 Limitations |
| C | Format-shift R4 eval is incomplete (hidden negative result?) | High | 8 variants × 444 = 3552 rows constructed; NLI features [3552, 7] complete; R4 prediction blocked (sklearn 1.4.1.post1 vs ≥1.5.0); no-network boundary; blocked report; redacted public variant inputs | BLOCKED (3.4) | Variant construction and NLI features complete; R4 metrics not reported; environmental block, not suppressed negative result | R4 metrics on variants absent; block permanent under no-network; canonicalization gain is on ablation, not on R4 over variants | §7.2 Method; §13 Limitations; Appendix on blocked experiments |
| D | No human audit; how can metrics be trusted? | High | Human audit protocol (`docs/human_audit_protocol_v1.md`); audit template and seed queue prepared; no `audit_agreement_summary.json`; `human_audited=False` for all 444 rows; `gold_label` empty | WARNING (6.4) | Protocol/template/seed queue prepared; audit not executed; all metrics are silver-conditional diagnostics | No human audit; metrics may shift under adjudication; 80–120 candidate sample, not full adjudication | §6 Dataset and Boundaries; §13 Limitations |
| E | Why emphasize confidentiality? Narrative device to avoid LLM baselines? | Medium | `no_api`/`no_network`/`no_training` enforced by pipeline runner; manuscript states "Confidentiality is a deployment constraint, not the empirical contribution"; Pareto analysis marks `external_llm_baseline` unavailable | WARNING (no LLM baseline) | Confidentiality is deployment constraint, not contribution; main contributions are format shift + canonicalization + Pareto analysis | No LLM baseline in submission; DeepSeek V3 pilot authorized separately but not included; Pareto conditional on constraint set | §5 Problem Setting; §1 Abstract; §4 Related Work |
| F | BM25/simple rules have no novelty | Medium | Retrieval-to-screening interface failure (recall@10=0.980 vs oracle_recall=0.043); canonicalization 9x improvement (0.043→0.387); Pareto analysis (deterministic Pareto-optimal, learned dominated); error taxonomy (interface errors dominate) | PASS (interface-level contribution) | Novelty is pipeline interface failure: retrieval success != screening success; canonicalization bridges interface under no-API/local constraints | No novel algorithm; Pareto optimality conditional on silver set and constraint set; interface failure shown on one dataset | §1 Introduction; §7 Method; §9 Results; §12 Complexity vs Utility |
| G | Release safety: internal files contain `true_label`/`oracle_hit` | Medium | Redteam scan finds 3 high-risk `forbidden_sorting_field` in internal scoring files; release safety manifest PASS (bundle-only); artifact ledger marks high-risk files `safe_to_release=false`; public PDF corpus hash-only | WARNING (9.1, internal-only) | Public release bundle clean of forbidden fields; 3 high-risk findings internal-only, excluded from bundle | 3 internal files contain `true_label`/`oracle_hit`; gate is bundle-only scope; repo-wide scan would fail | §14 Ethics/Confidentiality/Release Policy |
| H | Low prevalence queue: precision@20=0.35 is barely better than calibrated prior | Medium | Queue utility gate (`second_stage_viable=true`, `standalone_viable=false`); `G_conservative_precision` precision@20=0.45 vs 0.35 baseline (+0.10); error taxonomy (boundary errors dominate, strong_recall=0.706) | WARNING (modest absolute precision) | Queue provides meaningful precision lift at top (+0.10 at k=20); second-stage viable; not standalone detector | `standalone_viable=false`; absolute precision modest; all 8 variants miss strict targets; silver-conditional | §11 Review Queue Utility; §13 Limitations |
| I | No SOTA comparison, no gold benchmark, not a benchmark paper | High | Silver dataset (`human_audited=False`); no SciFact/VitaminC/FEVER comparison; Pareto analysis marks `external_llm_baseline` unavailable; manuscript states verbatim "not a gold benchmark", "not SOTA" | WARNING (scope restriction) | Paper is controlled silver diagnostic study, not SOTA and not benchmark; contribution is format shift + canonicalization, not benchmark-level performance | No gold-benchmark comparison; no SOTA claim supportable; system not validated as general detector | §1 Abstract; §3 Introduction; §4 Related Work; §13 Limitations |

---

## Severity summary

| Severity | Count | Risk IDs |
|---|---|---|
| High | 5 | A, B, C, D, I |
| Medium | 4 | E, F, G, H |
| Low | 0 | — |

---

## Status summary

| Status | Count | Risk IDs |
|---|---|---|
| PASS | 1 | F |
| WARNING | 7 | A, B, D, E, G, H, I |
| BLOCKED | 1 | C |
| FAIL | 0 | — |

The single BLOCKED item (Risk C, format-shift R4 eval) is an environmental block (sklearn version mismatch under no-network), not an empirical failure. No risk is promoted to PASS without complete evidence; no WARNING or BLOCKED is rewritten as PASS.

---

## Forbidden claim audit

The following claims are forbidden across all response files, the master table, and the rebuttal snippets. They must not appear in any reviewer-facing material:

| Unsafe wording (forbidden) | Why forbidden |
|---|---|
| "gold benchmark" | silver diagnostic only; `human_audited=False`; `gold_label` empty |
| "human-audited dataset" / "human-audited validation" | audit staged, not executed |
| "SOTA" / "state-of-the-art" | no gold comparison; silver labels cannot anchor SOTA |
| "automatic peer reviewer" | queue is second-stage; does not replace adjudication |
| "standalone detector" | `standalone_viable=false`; queue is second-stage only |
| "validated general detector" | silver-conditional diagnostics only; no cross-dataset validation |
| "format-shift R4 evaluation is complete" | R4 metrics on variants not reported; status = partial |
| "R4 is shortcut-free" | claim-only strong_F1=0.2448 is non-zero |
| "we beat LLM baselines" | no LLM baseline included; no comparison possible |
| "the entire repo is leak-free" | 3 high-risk findings exist in internal scoring files |

---

*End of master reviewer response table.*
