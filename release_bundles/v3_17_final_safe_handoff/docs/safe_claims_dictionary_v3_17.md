# Safe Claims Dictionary — V3.17 Confidential Lightweight

**Authority:** This dictionary standardizes the wording used in V3.17
Confidential Lightweight paper assets, docs, and reports. Use the Safe
wording column. Never use the Unsafe wording column. If an existing
document uses unsafe wording, replace it with the Safe replacement.

**Scope:** V3.17 Confidential Lightweight mainline only.

---

## Core positioning

| Concept | Safe wording | Unsafe wording | Replacement |
|---|---|---|---|
| Project type | controlled silver diagnostic study | gold benchmark study / validated detector study | "This work is a controlled silver diagnostic study of retrieval-to-screening format shift for confidential local PDF review." |
| Dataset | source-traceable silver set | gold-standard dataset / human-verified benchmark | "The 444-candidate dataset is a source-traceable silver diagnostic with `human_audited=False`; it is not a gold benchmark." |
| Pipeline output | second-stage review queue | automatic detector / standalone detector | "The pipeline produces a second-stage review queue that augments human review; it is not a standalone automatic detector." |
| Research contribution | retrieval-to-screening format shift analysis | SOTA claim / SOTA retrieval / SOTA screening / state-of-the-art system | "We analyze retrieval-to-screening format shift and show that evidence canonicalization restores screening signal." |
| Method | evidence canonicalization (unsupervised, local) | learned canonicalizer / trained evidence selector | "Evidence canonicalization selects the best sentence from BM25 top-5 chunks by token overlap; it is unsupervised and local." |
| Deployment setting | local / no-API / confidential review | cloud-based / API-dependent / web-scale system | "The pipeline runs locally with no API calls, no cloud dependency, and no new training, suitable for confidential PDF review." |

---

## Safe one-sentence positioning

> This work is a controlled silver diagnostic study of
> retrieval-to-screening format shift for confidential local PDF
> review. It is not a gold benchmark, SOTA detector, or automatic
> peer reviewer.

This sentence MUST appear (or be paraphrased with equivalent meaning)
in the README first screen and in the paper abstract / introduction.

---

## Allowed safe claims

### S1: Controlled silver diagnostic
- **Safe**: "On the controlled silver diagnostic, [result]."
- **Unsafe**: "On gold-standard data, [result]." / "In production, [result]."
- **Bound**: All quantitative results must be qualified as
  silver-label diagnostic, limited to the 444-candidate pool.

### S2: Source-traceable silver set
- **Safe**: "The 444-candidate dataset is a source-traceable silver
  diagnostic with `human_audited=False`."
- **Unsafe**: "Gold-standard evaluation set." / "Human-verified benchmark."
- **Bound**: All rows have `human_audited=False`; `gold_label` is empty.

### S3: Second-stage review queue only
- **Safe**: "The pipeline produces a second-stage review queue that
  augments human review; it is not a standalone automatic detector."
- **Unsafe**: "The system detects simulation claim overclaims
  automatically." / "The pipeline replaces human review."
- **Bound**: Human adjudication remains the gold standard; the queue
  only prioritizes cases for review.

### S4: Retrieval-to-screening format shift
- **Safe**: "We analyze retrieval-to-screening format shift: raw BM25
  chunks collapse R4 screening signal, and evidence canonicalization
  restores it."
- **Unsafe**: "We solve the retrieval problem." / "BM25 is SOTA for
  scientific claim retrieval."
- **Bound**: Limited to BM25 with the current PDF corpus; the format
  shift finding is specific to the R4 downstream classifier.

### S5: Evidence canonicalization (unsupervised, local)
- **Safe**: "Evidence canonicalization (best_sentence_top5_overlap)
  yields higher oracle recall than raw_top1_chunk, supporting
  canonicalization as a recovery step."
- **Unsafe**: "Canonicalization always improves retrieval." /
  "Canonicalization is necessary for all datasets."
- **Bound**: Limited to silver diagnostic data; not generalizable to
  gold-standard.

### S6: Local / no-API / confidential review
- **Safe**: "The pipeline runs locally with no API calls, no cloud
  dependency, and no new training, suitable for confidential PDF
  review."
- **Unsafe**: "The system uses LLM APIs for screening." / "The system
  requires cloud infrastructure."
- **Bound**: All stages (extraction, retrieval, canonicalization,
  screening, ranking) run on local compute.

---

## Forbidden unsafe claims

| # | Unsafe claim | Why unsafe | Safe replacement |
|---|---|---|---|
| U1 | "This is a gold benchmark." | All rows have `human_audited=False`; `gold_label` is empty. Silver diagnostic only. | "This is a controlled silver diagnostic, not a gold benchmark." |
| U2 | "This is a human-audited dataset." | No full human audit has been completed. Only a small targeted audit protocol exists. | "The dataset is silver-label; a small targeted human audit protocol exists but has not been completed." |
| U3 | "The pipeline achieves SOTA on simulation claim overclaim detection." | No comparison to other systems on a shared benchmark; silver diagnostic, not gold. | "On the controlled silver diagnostic, the pipeline achieves strong_F1 ≈ 0.45; no SOTA claim is made." |
| U4 | "The pipeline performs automatic peer review." | Pipeline produces a review queue for human reviewers; it does not perform peer review automatically. | "The pipeline produces a second-stage review queue that augments human review; it is not an automatic peer reviewer." |
| U5 | "This constitutes full CESE-OCN validation." | V3.17 confidential lightweight is a scoped subset; full CESE-OCN validation requires additional stages, gold labels, and human adjudication. | "V3.17 confidential lightweight is a scoped subset of CESE-OCN, not a full validation of the CESE-OCN neural architecture." |
| U6 | "The system is a standalone detector." | At realistic prevalence (1%), FP/TP = 66.82 — unusable as a standalone detector. | "The system is a second-stage review queue generator, not a standalone detector." |
| U7 | "The system is a general scientific overstatement detector." | The system is specific to simulation claims in the silver diagnostic domain, not a general-purpose detector. | "The system addresses simulation claim overclaim screening in a controlled silver diagnostic setting, not general scientific overstatement detection." |
| U8 | "Rules generally beat learned models." | Pareto analysis is deployment-specific (confidential/no-API/no-training/silver diagnostic). | "Under confidential/no-API/no-training/silver-diagnostic constraints, deterministic canonicalization has a favorable tradeoff; this does not generalize to all settings." |
| U9 | "This is a validated general detector." | No general-domain validation has been performed; the system is scoped to simulation claim escalation screening on a silver diagnostic set. | "The system is a scoped second-stage review queue for simulation claim escalation, not a validated general detector." |

---

## Legacy and future-work framing

When referring to V2, full CESE-OCN, or other non-V3.17 work, use
explicit legacy or future-work framing:

| Topic | Safe framing | Unsafe framing |
|---|---|---|
| V2 pilot | "V2 evidence-aware hierarchical pilot (legacy / superseded)" | "The current paper is V2." |
| Full CESE-OCN | "Full shared-threshold CESE-OCN neural architecture (future work, not current empirical claim)" | "Full CESE-OCN is validated." |
| Human audit | "A small targeted human audit protocol exists (future work, not yet completed)" | "The dataset is human-audited." |
| Gold labels | "Gold labels are future work; current labels are silver (`human_audited=False`)" | "Gold benchmark." |
| LLM baselines | "LLM baselines require API access and are out of scope for the local/no-API mainline (future work)" | "LLM baselines are the current mainline." |

---

## README first-screen requirement

The README.md first screen (above the fold, first ~30 lines) MUST
contain:

1. **"V3.17 Confidential Lightweight Local Review Queue"** as the
   current mainline name.
2. The **safe one-sentence positioning** (or equivalent paraphrase).
3. A clear statement that V2 / full CESE-OCN / gold / human-audited /
   SOTA / automatic peer review are **not** claimed.

The README MUST NOT contain "current paper V2" or "current manuscript
is V2" or any framing that presents V2 as the current mainline.

---

## Enforcement

This dictionary is enforced by:

- `scripts/clean_legacy_narrative_scan_v1.py` — scans README.md,
  CURRENT_MAINLINE.md, docs/, paper_assets/, reports/ for unsafe
  narrative and produces `reports/legacy_narrative_scan_v3_17.md`.
- `tests/test_legacy_narrative_cleanup.py` — verifies README first
  screen, CURRENT_MAINLINE content, and absence of unsafe current
  claims.
- `tests/test_current_mainline_docs.py` — verifies README and
  CURRENT_MAINLINE declare V3.17 Confidential Lightweight as current.
