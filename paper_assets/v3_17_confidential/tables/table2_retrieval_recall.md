# Table 2 — Retrieval Recall

## Chunk-level BM25 (69 PDFs, 4747 chunks)

| Metric | Value |
|---|---|
| n_claims | 444 |
| n_pdfs | 69 |
| n_chunks | 4747 |
| oracle_match_rate | 0.991 |
| recall@1 | 0.716 |
| recall@3 | 0.939 |
| recall@5 | 0.973 |
| recall@10 | 0.980 |
| recall@20 | 0.980 |
| MRR | 0.826 |
| strong_action_recall@10 | 0.991 |

## Sentence-level BM25 (34643 sentences)

| Metric | Value |
|---|---|
| recall@1 | 0.851 |
| recall@5 | 0.932 |
| recall@10 | 0.948 |
| MRR | 0.883 |

## Window-level BM25 (32250 windows)

| Metric | Value |
|---|---|
| recall@10 | 0.396 |
| MRR | 0.324 |

Sentence-level retrieval outperforms window-level on recall@10 (0.948 vs 0.396) and MRR (0.883 vs 0.324). Public artifacts are hash-only (no raw text); BM25 reads from a gitignored private corpus.

[Source: experiments/simclaim_pdf_corpus_retrieval_v1/retrieval_metrics_bm25.json; experiments/bm25_sentence_retrieval_v1/oracle_recall_summary.json; experiments/bm25_sentence_retrieval_v1/leakage_guard_report.json]
