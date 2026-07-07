# 06 — Simple Method Novelty Response (Risk F)

**Risk ID:** F
**Reviewer attack:** "BM25, token-overlap sentence selection, and rule-based ranking are well-known methods. Where is the novelty? This looks like a re-packaging of off-the-shelf components."
**Severity:** Medium

---

## 1. Reviewer concern

The reviewer notes that every individual component in the pipeline (BM25 retrieval, best-sentence selection by token overlap, frozen R4 cascade, rule-based risk ranking) is individually well-known. The reviewer may suspect that the paper repackages off-the-shelf components without a novel algorithm and asks the authors to either identify a concrete novel algorithm or to retract novelty claims.

## 2. What we agree with

We agree that BM25 is not a novel algorithm. We agree that token-overlap sentence selection is a standard technique. We agree that the frozen R4 cascade is a previously existing artifact, not a novel architecture. We agree that rule-based ranking variants are individually well-known. We do not claim that any single component is a novel algorithm.

## 3. Evidence we have

- **Pipeline interface failure.** The empirical novelty is not a new algorithm but a pipeline interface failure that we identify and bridge: retrieval success (BM25 recall@10 = 0.980) does not imply screening success (raw_top1_chunk oracle_recall = 0.043). The retrieval stage returns long chunks (91% exceed 60 words) that the screening stage cannot consume.
- **Canonicalization bridges the interface.** The deterministic canonicalizer `best_sentence_top5_overlap` raises oracle_recall from 0.043 to 0.387 (9x improvement) and produces screening-format-length evidence (0% exceed 60 words). The contribution is the identification of the interface failure and the demonstration that a deterministic, no-API, no-training bridge closes most of the gap.
- **Complexity-vs-utility Pareto analysis.** `experiments/complexity_vs_utility_ablation_v1/method_pareto_table.csv` reports that under the confidential constraint set, `deterministic_canonicalization`, `conservative_rule_queue`, and `lightweight_smart_queue` are Pareto-optimal; learned alternatives are dominated; `external_llm_baseline` is unavailable. The novelty is in the empirical finding that simple deterministic methods are Pareto-optimal under this constraint set, not in the methods themselves.
- **Component-level transparency.** The manuscript explicitly states that all canonicalizers are unsupervised, deterministic, and use only `claim_text` and the retrieved text — no labels, no oracle, no API calls. No component is presented as a novel algorithm.
- **Error taxonomy.** `experiments/error_taxonomy_v1/error_taxonomy_summary.csv` shows that the dominant error types are boundary errors (mild_vs_strong_boundary = 38.83%, weak_selector_overlap = 34.57%), not failures of any individual method; this further supports that the contribution is at the interface, not inside any single component.

## 4. Evidence file

- `experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv`
- `experiments/complexity_vs_utility_ablation_v1/method_pareto_table.csv`
- `experiments/complexity_vs_utility_ablation_v1/method_comparison_metrics.csv`
- `experiments/error_taxonomy_v1/error_taxonomy_summary.csv`
- `experiments/simclaim_pdf_corpus_retrieval_v1/retrieval_metrics_bm25.json`

## 5. Safe response

We answer the reviewer as follows: BM25 is not the novelty. The novelty is the identification of a pipeline interface failure (retrieval success does not imply screening success) and the demonstration that deterministic evidence canonicalization bridges this interface under the no-API, no-training, no-network constraint set. The contribution is therefore empirical and interface-level, not algorithmic. The complexity-vs-utility Pareto analysis treats this empirically: simple deterministic methods are Pareto-optimal under the constraint set, learned alternatives are dominated, and external LLM baselines are unavailable.

The safe empirical conclusion is therefore narrow: **the contribution is the identification and bridging of the retrieval-to-screening interface failure, not any novel component algorithm. We do not claim a novel retrieval algorithm, a novel ranking algorithm, or a novel classifier. We claim an empirical interface-level finding and a deterministic bridge that is Pareto-optimal under the stated constraints.**

## 6. Remaining limitation

- No component is a novel algorithm; the contribution is interface-level and empirical.
- The Pareto-optimality of deterministic methods is conditional on the V3.17 silver diagnostic set and the no-API/no-network/no-training constraint set; in less restrictive settings, learned or LLM-based methods may dominate.
- The canonicalizer is unsupervised and uses token overlap; more sophisticated canonicalizers (e.g., supervised sentence selection, neural extractive summarization) are not tested because they require training or API access.
- The interface failure is identified on one dataset (444 candidates, 6 domains); generalization to other retrieval-to-screening settings is not established.

## 7. Paper text to add

> "We clarify the novelty claim. BM25, token-overlap sentence selection, the frozen R4 cascade, and rule-based ranking are individually well-known; we do not claim any of them as a novel algorithm. The novelty is the identification of a pipeline interface failure — retrieval success (BM25 recall@10 = 0.980) does not imply screening success (raw_top1_chunk oracle_recall = 0.043, 91% of chunks exceed 60 words) — and the demonstration that deterministic evidence canonicalization bridges this interface (oracle_recall 0.043 → 0.387, 9x improvement; 0% of canonicalized evidence exceeds 60 words) under the no-API, no-training, no-network constraint set. The complexity-vs-utility Pareto analysis treats this empirically: deterministic canonicalization, conservative rule queue, and lightweight smart queue are Pareto-optimal under the constraint set; learned alternatives are dominated; external LLM baseline is unavailable. The contribution is interface-level and empirical, not algorithmic."

## 8. What not to claim

| Unsafe wording (forbidden) | Why forbidden |
|---|---|
| "we propose a novel BM25 variant" | BM25 (k1=1.5, b=0.75) is standard; no variant is proposed |
| "we propose a novel ranking algorithm" | ranking variants (A–H) are rule-based combinations of existing signals |
| "the canonicalizer is a novel algorithm" | token-overlap sentence selection is a standard technique |
| "R4 is a novel classifier" | R4 is a frozen pre-existing cascade; not proposed as novel |
| "the methods are universally optimal" | Pareto-optimality is conditional on the silver set and constraint set |

---

*End of response 06.*
