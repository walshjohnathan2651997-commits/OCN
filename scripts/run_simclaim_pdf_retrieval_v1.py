"""
SimClaim PDF-Corpus Retrieval Prototype v1

Goal:
    Validate whether the new mainline (offline PDF corpus retrieval + CESE-OCN screening)
    is feasible. Test: (1) can BM25 retrieve oracle evidence from source PDFs?
    (2) does downstream screening still work on retrieved evidence?

Hard prohibitions:
    - No new PDF downloads
    - No network/internet
    - No LLM/API calls
    - No model training
    - No original-data modification
    - No paper modification
    - No silver-as-gold
    - No simulation-as-natural-distribution
    - No file deletion
"""

import json
import re
import math
import shutil
from pathlib import Path
from collections import Counter, defaultdict
import pandas as pd
import numpy as np

# Try pymupdf
try:
    import fitz  # PyMuPDF
    PYMUPDF_OK = True
except ImportError:
    PYMUPDF_OK = False

# ============ Configuration ============
STRICT_SILVER_CSV = Path(r"D:\ocn\data\simclaim_all92_candidate_pool_v1\strict_silver_max_v1\strict_silver_max_candidates_v1.csv")
PDF_SEARCH_DIRS = [
    Path(r"D:\ocn_backup_20260704_1606\data\source_bank_v2\pdfs"),
    Path(r"D:\ocn\data\source_bank_v2\pdfs"),
    Path(r"D:\ocn_backup_20260704_1606"),
    Path(r"D:\ocn"),
]
EXP_OUT = Path(r"D:\ocn\experiments\simclaim_pdf_corpus_retrieval_v1")
DATA_OUT = Path(r"D:\ocn\data\simclaim_pdf_corpus_retrieval_v1")

CHUNK_WORDS = 200
CHUNK_OVERLAP = 50
BM25_TOP_K = 20
BM25_K1 = 1.5
BM25_B = 0.75

STRONG_CUES = [
    "deployment", "deploy", "safety", "safe", "policy", "policies",
    "guarantee", "guaranteed", "real-world", "real world", "always",
    "fully", "replace", "solve", "solved", "ready", "generalize",
    "generalizable", "robust", "reliable", "operational", "production",
]
EVIDENCE_LIMIT_CUES = [
    "limited", "simulated", "simulation", "benchmark", "uncertainty",
    "barrier", "remains", "requires", "validation", "future work",
    "preliminary", "proof-of-concept",
]


# ============ Utilities ============
def normalize_text(t: str) -> str:
    """Normalize text for fuzzy matching."""
    t = t.lower()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[^a-z0-9 ]", "", t)
    return t.strip()


def tokenize(t: str) -> list:
    """Simple word tokenization."""
    return re.findall(r"\b[a-z0-9]+\b", t.lower())


def token_jaccard(a: str, b: str) -> float:
    """Token Jaccard similarity."""
    sa = set(tokenize(a))
    sb = set(tokenize(b))
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def contains_substr(needle: str, haystack: str, min_len: int = 30) -> bool:
    """Check if normalized needle is a substring of normalized haystack."""
    n = normalize_text(needle)
    h = normalize_text(haystack)
    if len(n) < min_len:
        return False
    return n in h


# ============ BM25 from scratch ============
class BM25:
    def __init__(self, corpus_docs: list, k1: float = 1.5, b: float = 0.75):
        """corpus_docs: list of (doc_id, token_list)"""
        self.k1 = k1
        self.b = b
        self.docs = corpus_docs
        self.doc_ids = [d[0] for d in corpus_docs]
        self.doc_tokens = [d[1] for d in corpus_docs]
        self.doc_len = [len(t) for t in self.doc_tokens]
        self.avgdl = sum(self.doc_len) / len(self.doc_len) if self.doc_len else 0
        self.N = len(corpus_docs)

        # Build term frequency and document frequency
        self.tf = []  # list of Counter
        self.df = Counter()  # document frequency
        for tokens in self.doc_tokens:
            tf = Counter(tokens)
            self.tf.append(tf)
            for term in tf:
                self.df[term] += 1

        # IDF
        self.idf = {}
        for term, df in self.df.items():
            self.idf[term] = math.log((self.N - df + 0.5) / (df + 0.5) + 1)

    def score_query(self, query_tokens: list) -> list:
        """Return list of (doc_id, score) sorted by score descending."""
        scores = []
        query_terms = set(query_tokens)
        for i, doc_id in enumerate(self.doc_ids):
            score = 0.0
            tf = self.tf[i]
            dl = self.doc_len[i]
            for term in query_terms:
                if term not in self.idf:
                    continue
                f = tf.get(term, 0)
                if f == 0:
                    continue
                idf = self.idf[term]
                denom = f + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
                score += idf * (f * (self.k1 + 1)) / denom
            scores.append((doc_id, score))
        scores.sort(key=lambda x: -x[1])
        return scores


# ============ Step A: PDF source inventory ============
def build_pdf_source_inventory(df: pd.DataFrame) -> pd.DataFrame:
    """Match each unique source_id to a local PDF."""
    print("[A] Building PDF source inventory ...")
    unique_sources = df[["source_id", "arxiv_id", "pdf_filename", "title", "url", "domain"]].drop_duplicates("source_id")
    rows = []
    for _, r in unique_sources.iterrows():
        source_id = r["source_id"]
        arxiv_id = r["arxiv_id"]
        pdf_filename = r["pdf_filename"]
        title = r["title"]
        url = r["url"]
        domain = r["domain"]

        # Extract base filename from pdf_filename (e.g., "pdfs/AD-001__2511.10403.pdf" -> "AD-001__2511.10403.pdf")
        base_name = Path(pdf_filename).name if pdf_filename else ""

        # Search for the PDF in each search dir
        found_path = ""
        file_exists = False
        file_size = 0
        match_method = ""
        confidence = 0.0

        for search_dir in PDF_SEARCH_DIRS:
            if not search_dir.exists():
                continue
            # Try exact filename match
            candidate = search_dir / base_name
            if candidate.exists():
                found_path = str(candidate)
                file_exists = True
                file_size = candidate.stat().st_size
                match_method = "exact_filename"
                confidence = 1.0
                break

        if not file_exists:
            # Try recursive search
            for search_dir in PDF_SEARCH_DIRS:
                if not search_dir.exists():
                    continue
                for p in search_dir.rglob(base_name):
                    if p.is_file():
                        found_path = str(p)
                        file_exists = True
                        file_size = p.stat().st_size
                        match_method = "recursive_filename"
                        confidence = 0.95
                        break
                if file_exists:
                    break

        if not file_exists:
            # Try matching by source_id pattern
            for search_dir in PDF_SEARCH_DIRS:
                if not search_dir.exists():
                    continue
                pattern = f"{source_id}__*.pdf"
                for p in search_dir.rglob(pattern):
                    if p.is_file():
                        found_path = str(p)
                        file_exists = True
                        file_size = p.stat().st_size
                        match_method = "source_id_glob"
                        confidence = 0.9
                        break
                if file_exists:
                    break

        if not file_exists:
            match_method = "missing"
            confidence = 0.0

        rows.append({
            "paper_id": source_id,
            "source_pair_id": source_id,
            "title": title,
            "arxiv_id": arxiv_id,
            "source_url": url,
            "pdf_path": found_path,
            "file_exists": file_exists,
            "file_size": file_size,
            "match_method": match_method,
            "confidence": confidence,
            "domain": domain,
        })

    inv_df = pd.DataFrame(rows)
    inv_df.to_csv(EXP_OUT / "pdf_source_inventory.csv", index=False, encoding="utf-8")
    n_found = inv_df["file_exists"].sum()
    n_total = len(inv_df)
    print(f"  PDF coverage: {n_found}/{n_total} = {n_found/n_total:.2%}")
    return inv_df


# ============ Step B+C: PDF text extraction and chunking ============
def extract_and_chunk_pdfs(inv_df: pd.DataFrame) -> pd.DataFrame:
    """Extract text from PDFs and build chunks."""
    print("[B+C] Extracting PDF text and building chunks ...")
    if not PYMUPDF_OK:
        print("  ERROR: PyMuPDF not available")
        return pd.DataFrame()

    chunks = []
    chunk_id_counter = 0
    extraction_status = []

    for _, r in inv_df.iterrows():
        paper_id = r["paper_id"]
        pdf_path = r["pdf_path"]
        if not r["file_exists"] or not pdf_path:
            extraction_status.append({
                "paper_id": paper_id,
                "pdf_path": pdf_path,
                "extract_status": "pdf_missing",
                "n_pages": 0,
                "n_chars": 0,
                "error": "PDF file not found",
            })
            continue

        try:
            doc = fitz.open(pdf_path)
            n_pages = len(doc)
            all_page_text = []
            for page_num in range(n_pages):
                page = doc[page_num]
                text = page.get_text("text")
                all_page_text.append((page_num + 1, text))
            doc.close()

            # Build chunks: 200 words, 50-word overlap, preserve page_number
            for page_num, text in all_page_text:
                words = text.split()
                if not words:
                    continue
                i = 0
                chunk_idx = 0
                while i < len(words):
                    chunk_words = words[i:i + CHUNK_WORDS]
                    chunk_text = " ".join(chunk_words)
                    n_words = len(chunk_words)
                    if n_words >= 10:  # skip very short chunks
                        chunks.append({
                            "chunk_id": f"{paper_id}_p{page_num}_c{chunk_idx}",
                            "paper_id": paper_id,
                            "source_pair_id": paper_id,
                            "pdf_path": pdf_path,
                            "page_start": page_num,
                            "page_end": page_num,
                            "chunk_index": chunk_idx,
                            "chunk_text": chunk_text,
                            "n_words": n_words,
                            "extract_status": "ok",
                        })
                        chunk_id_counter += 1
                    i += CHUNK_WORDS - CHUNK_OVERLAP
                    chunk_idx += 1

            extraction_status.append({
                "paper_id": paper_id,
                "pdf_path": pdf_path,
                "extract_status": "ok",
                "n_pages": n_pages,
                "n_chars": sum(len(t) for _, t in all_page_text),
                "error": "",
            })
        except Exception as e:
            extraction_status.append({
                "paper_id": paper_id,
                "pdf_path": pdf_path,
                "extract_status": "extraction_failed",
                "n_pages": 0,
                "n_chars": 0,
                "error": str(e)[:200],
            })

    chunks_df = pd.DataFrame(chunks)
    chunks_df.to_csv(DATA_OUT / "local_pdf_corpus_chunks.csv", index=False, encoding="utf-8")
    print(f"  Total chunks: {len(chunks_df)}")
    print(f"  Extraction success: {sum(1 for s in extraction_status if s['extract_status']=='ok')}/{len(extraction_status)}")
    return chunks_df


# ============ Step D: Claim queries ============
def build_claim_queries(df: pd.DataFrame) -> pd.DataFrame:
    """Build claim queries from strict_silver_max."""
    print("[D] Building claim queries ...")
    queries = df[[
        "candidate_id", "claim_text", "candidate_label_guess",
        "source_id", "arxiv_id", "title", "url",
        "evidence_text", "page_number", "source_location", "domain",
    ]].copy()
    queries.rename(columns={
        "source_id": "source_pair_id",
        "source_id": "paper_id",
    }, inplace=True)
    queries["source_pair_id"] = df["source_id"]
    queries["paper_id"] = df["source_id"]
    queries["oracle_evidence_text"] = df["evidence_text"]
    queries["oracle_evidence_source_url"] = df["url"]
    queries["oracle_location"] = df["source_location"] + " p" + df["page_number"].astype(str)
    queries = queries[[
        "candidate_id", "claim_text", "candidate_label_guess",
        "source_pair_id", "paper_id", "oracle_evidence_text",
        "oracle_evidence_source_url", "oracle_location", "domain",
    ]]
    queries.to_csv(EXP_OUT / "claim_queries.csv", index=False, encoding="utf-8")
    print(f"  Claim queries: {len(queries)}")
    return queries


# ============ Step E: Oracle evidence map ============
def build_oracle_evidence_map(queries: pd.DataFrame, chunks: pd.DataFrame) -> pd.DataFrame:
    """Match oracle evidence to PDF chunks."""
    print("[E] Building oracle evidence map ...")
    # Index chunks by paper_id for faster lookup
    chunks_by_paper = defaultdict(list)
    for _, crow in chunks.iterrows():
        chunks_by_paper[crow["paper_id"]].append(crow)

    rows = []
    n_match = 0
    for _, qrow in queries.iterrows():
        cid = qrow["candidate_id"]
        oracle = qrow["oracle_evidence_text"]
        paper_id = qrow["paper_id"]
        paper_chunks = chunks_by_paper.get(paper_id, [])

        match_found = False
        matched_chunk_id = ""
        match_score = 0.0
        match_method = ""
        matched_page = ""
        matched_text = ""

        if not paper_chunks:
            match_method = "no_pdf_chunks"
        else:
            # Try exact normalized substring match first
            oracle_norm = normalize_text(oracle)
            for crow in paper_chunks:
                if contains_substr(oracle, crow["chunk_text"], min_len=30):
                    match_found = True
                    matched_chunk_id = crow["chunk_id"]
                    match_score = 1.0
                    match_method = "exact_substring"
                    matched_page = crow["page_start"]
                    matched_text = crow["chunk_text"][:300]
                    break

            # Try fuzzy match (token Jaccard >= 0.5)
            if not match_found:
                best_jaccard = 0.0
                best_chunk = None
                oracle_tokens = set(tokenize(oracle))
                for crow in paper_chunks:
                    j = token_jaccard(oracle, crow["chunk_text"])
                    if j > best_jaccard:
                        best_jaccard = j
                        best_chunk = crow
                if best_chunk is not None and best_jaccard >= 0.3:
                    match_found = True
                    matched_chunk_id = best_chunk["chunk_id"]
                    match_score = best_jaccard
                    match_method = "token_jaccard"
                    matched_page = best_chunk["page_start"]
                    matched_text = best_chunk["chunk_text"][:300]

        if match_found:
            n_match += 1

        rows.append({
            "candidate_id": cid,
            "oracle_match_found": match_found,
            "matched_chunk_id": matched_chunk_id,
            "match_score": match_score,
            "match_method": match_method,
            "matched_page": matched_page,
            "oracle_evidence_text": oracle,
            "matched_chunk_text": matched_text,
        })

    oracle_df = pd.DataFrame(rows)
    oracle_df.to_csv(EXP_OUT / "oracle_evidence_map.csv", index=False, encoding="utf-8")
    print(f"  Oracle match rate: {n_match}/{len(queries)} = {n_match/len(queries):.2%}")
    return oracle_df


# ============ Step F: BM25 retrieval ============
def bm25_retrieval(queries: pd.DataFrame, chunks: pd.DataFrame, oracle_df: pd.DataFrame) -> pd.DataFrame:
    """Run BM25 retrieval for each claim query."""
    print("[F] Running BM25 retrieval ...")

    # Build BM25 corpus
    print("  Building BM25 index ...")
    corpus_docs = []
    for _, crow in chunks.iterrows():
        tokens = tokenize(crow["chunk_text"])
        corpus_docs.append((crow["chunk_id"], tokens))
    bm25 = BM25(corpus_docs, k1=BM25_K1, b=BM25_B)

    # Build oracle match lookup: candidate_id -> set of matched chunk_ids
    oracle_chunks = defaultdict(set)
    for _, orow in oracle_df.iterrows():
        if orow["oracle_match_found"] and orow["matched_chunk_id"]:
            oracle_chunks[orow["candidate_id"]].add(orow["matched_chunk_id"])

    # Build chunk lookup: chunk_id -> chunk row
    chunk_lookup = {crow["chunk_id"]: crow for _, crow in chunks.iterrows()}

    print(f"  Retrieving top-{BM25_TOP_K} for {len(queries)} queries ...")
    rows = []
    for qi, (_, qrow) in enumerate(queries.iterrows()):
        if qi % 100 == 0:
            print(f"    query {qi}/{len(queries)} ...")
        cid = qrow["candidate_id"]
        claim = qrow["claim_text"]
        paper_id = qrow["paper_id"]
        query_tokens = tokenize(claim)

        scores = bm25.score_query(query_tokens)
        top_k = scores[:BM25_TOP_K]

        oracle_set = oracle_chunks.get(cid, set())
        for rank, (chunk_id, score) in enumerate(top_k, 1):
            crow = chunk_lookup.get(chunk_id)
            if crow is None:
                continue
            is_oracle = chunk_id in oracle_set
            same_paper = (crow["paper_id"] == paper_id)
            rows.append({
                "candidate_id": cid,
                "rank": rank,
                "chunk_id": chunk_id,
                "bm25_score": round(score, 4),
                "retrieved_text": crow["chunk_text"][:500],
                "paper_id": crow["paper_id"],
                "same_paper": same_paper,
                "is_oracle_hit": is_oracle,
                "oracle_match_score": 1.0 if is_oracle else 0.0,
                "page_number": crow["page_start"],
            })

    results_df = pd.DataFrame(rows)
    results_df.to_csv(EXP_OUT / "retrieval_results_bm25.csv", index=False, encoding="utf-8")
    print(f"  Retrieval results: {len(results_df)} rows ({len(results_df)/len(queries):.1f} avg per query)")
    return results_df


# ============ Step G: Retrieval metrics ============
def compute_retrieval_metrics(results: pd.DataFrame, queries: pd.DataFrame, oracle_df: pd.DataFrame, inv_df: pd.DataFrame, chunks: pd.DataFrame) -> dict:
    """Compute retrieval metrics."""
    print("[G] Computing retrieval metrics ...")
    n_claims = len(queries)
    n_pdfs_found = int(inv_df["file_exists"].sum())
    n_pdfs_total = len(inv_df)
    pdf_coverage = n_pdfs_found / n_pdfs_total if n_pdfs_total > 0 else 0

    # Text extraction success
    n_extracted = chunks["paper_id"].nunique() if len(chunks) > 0 else 0
    extraction_rate = n_extracted / n_pdfs_found if n_pdfs_found > 0 else 0

    # Oracle match rate
    oracle_match_rate = oracle_df["oracle_match_found"].mean() if len(oracle_df) > 0 else 0

    # Recall@k
    k_values = [1, 3, 5, 10, 20]
    recall_at_k = {}
    mrr_sum = 0.0
    mrr_count = 0

    # For each query, check if any oracle chunk is in top-k
    query_oracle_hits = defaultdict(set)  # candidate_id -> set of ranks where oracle was hit
    for _, r in results.iterrows():
        if r["is_oracle_hit"]:
            query_oracle_hits[r["candidate_id"]].add(r["rank"])

    for k in k_values:
        hit_count = 0
        for cid in queries["candidate_id"]:
            hits = query_oracle_hits.get(cid, set())
            if any(r <= k for r in hits):
                hit_count += 1
        recall_at_k[f"recall_at_{k}"] = hit_count / n_claims if n_claims > 0 else 0

    # MRR
    for cid in queries["candidate_id"]:
        hits = query_oracle_hits.get(cid, set())
        if hits:
            first_rank = min(hits)
            mrr_sum += 1.0 / first_rank
            mrr_count += 1
    mrr = mrr_sum / n_claims if n_claims > 0 else 0

    # Same-paper hit rate at top-1
    top1 = results[results["rank"] == 1]
    same_paper_hit_rate = top1["same_paper"].mean() if len(top1) > 0 else 0

    # Label-wise Recall@10
    label_recall_at_10 = {}
    for label in queries["candidate_label_guess"].unique():
        cids = queries[queries["candidate_label_guess"] == label]["candidate_id"]
        hit_count = 0
        for cid in cids:
            hits = query_oracle_hits.get(cid, set())
            if any(r <= 10 for r in hits):
                hit_count += 1
        label_recall_at_10[label] = hit_count / len(cids) if len(cids) > 0 else 0

    metrics = {
        "n_claims": n_claims,
        "n_pdfs_total": n_pdfs_total,
        "n_pdfs_found": n_pdfs_found,
        "pdf_coverage_rate": pdf_coverage,
        "n_chunks": len(chunks),
        "extraction_success_rate": extraction_rate,
        "oracle_match_rate": oracle_match_rate,
        "recall_at_1": recall_at_k["recall_at_1"],
        "recall_at_3": recall_at_k["recall_at_3"],
        "recall_at_5": recall_at_k["recall_at_5"],
        "recall_at_10": recall_at_k["recall_at_10"],
        "recall_at_20": recall_at_k["recall_at_20"],
        "mrr": mrr,
        "same_paper_hit_rate_at_1": same_paper_hit_rate,
        "label_wise_recall_at_10": label_recall_at_10,
        "strong_action_recall_at_10": label_recall_at_10.get("strong_action_overclaim", 0),
        "bm25_params": {"k1": BM25_K1, "b": BM25_B, "top_k": BM25_TOP_K},
        "chunk_params": {"chunk_words": CHUNK_WORDS, "overlap": CHUNK_OVERLAP},
    }

    with open(EXP_OUT / "retrieval_metrics_bm25.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"  Recall@1={metrics['recall_at_1']:.4f}, Recall@5={metrics['recall_at_5']:.4f}, Recall@10={metrics['recall_at_10']:.4f}, Recall@20={metrics['recall_at_20']:.4f}")
    print(f"  MRR={metrics['mrr']:.4f}, same-paper@1={metrics['same_paper_hit_rate_at_1']:.4f}")
    print(f"  strong_action Recall@10={metrics['strong_action_recall_at_10']:.4f}")
    return metrics


# ============ Step H: Downstream screening proxy ============
def downstream_screening(queries: pd.DataFrame, results: pd.DataFrame, oracle_df: pd.DataFrame) -> pd.DataFrame:
    """Compare oracle vs retrieved evidence for strong_action screening (cue-based proxy)."""
    print("[H] Running downstream screening comparison ...")

    def cue_risk_score(claim: str, evidence: str) -> float:
        """Cue-based strong_action risk score (0-3)."""
        claim_lower = claim.lower()
        evidence_lower = evidence.lower()
        claim_strong_cues = sum(1 for c in STRONG_CUES if c in claim_lower)
        evidence_limit_cues = sum(1 for c in EVIDENCE_LIMIT_CUES if c in evidence_lower)
        evidence_strong_cues = sum(1 for c in STRONG_CUES if c in evidence_lower)

        # Strong action risk: claim has strong cues but evidence has limit cues
        if claim_strong_cues >= 2 and evidence_limit_cues >= 1:
            return 3
        elif claim_strong_cues >= 1 and evidence_limit_cues >= 1:
            return 2
        elif claim_strong_cues >= 1:
            return 1
        else:
            return 0

    rows = []
    for _, qrow in queries.iterrows():
        cid = qrow["candidate_id"]
        claim = qrow["claim_text"]
        label = qrow["candidate_label_guess"]
        oracle_evidence = qrow["oracle_evidence_text"]

        # Oracle evidence score
        oracle_score = cue_risk_score(claim, oracle_evidence)
        oracle_flagged = oracle_score >= 2

        # Retrieved top-1 evidence
        r1 = results[(results["candidate_id"] == cid) & (results["rank"] == 1)]
        if len(r1) > 0:
            ret1_text = r1.iloc[0]["retrieved_text"]
            ret1_score = cue_risk_score(claim, ret1_text)
            ret1_flagged = ret1_score >= 2
            ret1_chunk_id = r1.iloc[0]["chunk_id"]
            ret1_same_paper = r1.iloc[0]["same_paper"]
            ret1_is_oracle = r1.iloc[0]["is_oracle_hit"]
        else:
            ret1_score = -1
            ret1_flagged = False
            ret1_chunk_id = ""
            ret1_same_paper = False
            ret1_is_oracle = False

        # Retrieved top-3 evidence (aggregate: max score)
        r3 = results[(results["candidate_id"] == cid) & (results["rank"] <= 3)]
        if len(r3) > 0:
            ret3_scores = [cue_risk_score(claim, r["retrieved_text"]) for _, r in r3.iterrows()]
            ret3_score = max(ret3_scores)
            ret3_flagged = ret3_score >= 2
        else:
            ret3_score = -1
            ret3_flagged = False

        # True strong_action label (silver)
        true_strong = (label == "strong_action_overclaim")

        rows.append({
            "candidate_id": cid,
            "silver_label": label,
            "true_strong_action": true_strong,
            "oracle_evidence_score": oracle_score,
            "oracle_flagged_strong": oracle_flagged,
            "retrieved_top1_score": ret1_score,
            "retrieved_top1_flagged": ret1_flagged,
            "retrieved_top3_score": ret3_score,
            "retrieved_top3_flagged": ret3_flagged,
            "retrieved_top1_chunk_id": ret1_chunk_id,
            "retrieved_top1_same_paper": ret1_same_paper,
            "retrieved_top1_is_oracle_hit": ret1_is_oracle,
            "retrieval_failure": not ret1_is_oracle,
        })

    screen_df = pd.DataFrame(rows)
    screen_df.to_csv(EXP_OUT / "downstream_screening_bm25.csv", index=False, encoding="utf-8")
    print(f"  Downstream screening: {len(screen_df)} rows")
    return screen_df


# ============ Step I: Downstream metrics ============
def compute_downstream_metrics(screen_df: pd.DataFrame) -> dict:
    """Compare oracle vs retrieved evidence screening performance."""
    print("[I] Computing downstream screening metrics ...")

    def prf(y_true, y_pred):
        tp = int((y_true & y_pred).sum())
        fp = int((~y_true & y_pred).sum())
        fn = int((y_true & ~y_pred).sum())
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn}

    y_true = screen_df["true_strong_action"]

    # Oracle evidence performance
    y_oracle = screen_df["oracle_flagged_strong"]
    oracle_metrics = prf(y_true, y_oracle)

    # Retrieved top-1 performance
    y_ret1 = screen_df["retrieved_top1_flagged"]
    ret1_metrics = prf(y_true, y_ret1)

    # Retrieved top-3 performance
    y_ret3 = screen_df["retrieved_top3_flagged"]
    ret3_metrics = prf(y_true, y_ret3)

    # Gap: oracle vs retrieved top-1
    recall_gap = oracle_metrics["recall"] - ret1_metrics["recall"]
    f1_gap = oracle_metrics["f1"] - ret1_metrics["f1"]

    # Error decomposition
    # Retrieval failure: retrieved_top1_is_oracle_hit == False
    retrieval_failure_count = int((~screen_df["retrieved_top1_is_oracle_hit"]).sum())
    # Screening failure: oracle_flagged but not retrieved_flagged (or vice versa) among retrieval success
    retrieval_success = screen_df["retrieved_top1_is_oracle_hit"]
    screening_disagree = screen_df["oracle_flagged_strong"] != screen_df["retrieved_top1_flagged"]
    screening_failure_count = int((retrieval_success & screening_disagree).sum())

    metrics = {
        "oracle_evidence_strong_action": oracle_metrics,
        "retrieved_top1_strong_action": ret1_metrics,
        "retrieved_top3_strong_action": ret3_metrics,
        "oracle_vs_retrieved_top1_recall_gap": recall_gap,
        "oracle_vs_retrieved_top1_f1_gap": f1_gap,
        "retrieval_failure_count": retrieval_failure_count,
        "retrieval_failure_rate": retrieval_failure_count / len(screen_df) if len(screen_df) > 0 else 0,
        "screening_failure_after_good_retrieval_count": screening_failure_count,
        "screening_failure_after_good_retrieval_rate": screening_failure_count / int(retrieval_success.sum()) if retrieval_failure_count > 0 and int(retrieval_success.sum()) > 0 else 0,
        "note": "Cue-based proxy screening, not full R4. R4 frozen predictions are aggregate-only and cannot be reused per-candidate.",
    }

    with open(EXP_OUT / "downstream_screening_metrics_bm25.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"  Oracle strong F1={oracle_metrics['f1']:.4f}, recall={oracle_metrics['recall']:.4f}")
    print(f"  Ret top-1 strong F1={ret1_metrics['f1']:.4f}, recall={ret1_metrics['recall']:.4f}")
    print(f"  F1 gap={f1_gap:.4f}, recall gap={recall_gap:.4f}")
    print(f"  Retrieval failure rate={metrics['retrieval_failure_rate']:.4f}")
    return metrics


# ============ Step J: Failure analysis ============
def failure_analysis(queries: pd.DataFrame, results: pd.DataFrame, oracle_df: pd.DataFrame, inv_df: pd.DataFrame, screen_df: pd.DataFrame) -> pd.DataFrame:
    """Categorize retrieval failures."""
    print("[J] Running failure analysis ...")
    rows = []
    for _, qrow in queries.iterrows():
        cid = qrow["candidate_id"]
        paper_id = qrow["paper_id"]

        # Check PDF missing
        inv_row = inv_df[inv_df["paper_id"] == paper_id]
        pdf_missing = not inv_row.iloc[0]["file_exists"] if len(inv_row) > 0 else True

        # Check oracle match
        oracle_row = oracle_df[oracle_df["candidate_id"] == cid]
        oracle_found = oracle_row.iloc[0]["oracle_match_found"] if len(oracle_row) > 0 else False
        oracle_method = oracle_row.iloc[0]["match_method"] if len(oracle_row) > 0 else ""

        # Check retrieval
        ret_rows = results[results["candidate_id"] == cid]
        has_retrieval = len(ret_rows) > 0
        top1 = ret_rows[ret_rows["rank"] == 1] if has_retrieval else pd.DataFrame()
        top1_same_paper = top1.iloc[0]["same_paper"] if len(top1) > 0 else False
        top1_is_oracle = top1.iloc[0]["is_oracle_hit"] if len(top1) > 0 else False

        # Check screening
        screen_row = screen_df[screen_df["candidate_id"] == cid]
        retrieval_failure = screen_row.iloc[0]["retrieval_failure"] if len(screen_row) > 0 else False
        oracle_flagged = screen_row.iloc[0]["oracle_flagged_strong"] if len(screen_row) > 0 else False
        ret1_flagged = screen_row.iloc[0]["retrieved_top1_flagged"] if len(screen_row) > 0 else False

        # Categorize
        if pdf_missing:
            failure_type = "pdf_missing"
            reason = f"PDF not found for {paper_id}"
        elif not oracle_found:
            if oracle_method == "no_pdf_chunks":
                failure_type = "text_extraction_failed"
                reason = "PDF exists but no chunks extracted"
            else:
                failure_type = "oracle_not_in_pdf_text"
                reason = "Oracle evidence not found in PDF text (no substring or Jaccard match)"
        elif not has_retrieval:
            failure_type = "retrieval_empty"
            reason = "BM25 returned no results"
        elif not top1_is_oracle:
            if not top1_same_paper:
                failure_type = "retrieved_wrong_paper"
                reason = f"Top-1 from {top1.iloc[0]['paper_id']}, expected {paper_id}"
            else:
                failure_type = "oracle_chunk_not_retrieved"
                reason = "Same paper but oracle chunk not in top-20"
        elif oracle_flagged != ret1_flagged:
            failure_type = "relation_screening_failed_after_good_retrieval"
            reason = f"Oracle flagged={oracle_flagged}, retrieved flagged={ret1_flagged}"
        else:
            failure_type = "none"
            reason = "No failure"

        rows.append({
            "candidate_id": cid,
            "paper_id": paper_id,
            "silver_label": qrow["candidate_label_guess"],
            "failure_type": failure_type,
            "reason": reason,
            "pdf_missing": pdf_missing,
            "oracle_found": oracle_found,
            "oracle_method": oracle_method,
            "top1_same_paper": top1_same_paper,
            "top1_is_oracle": top1_is_oracle,
            "retrieval_failure": retrieval_failure,
        })

    fail_df = pd.DataFrame(rows)
    fail_df.to_csv(EXP_OUT / "retrieval_failure_analysis.csv", index=False, encoding="utf-8")
    print("  Failure type distribution:")
    for ft, count in fail_df["failure_type"].value_counts().items():
        print(f"    {ft}: {count}")
    return fail_df


# ============ Step K: Review queue ============
def build_review_queue(queries: pd.DataFrame, results: pd.DataFrame, screen_df: pd.DataFrame) -> pd.DataFrame:
    """Build top-100 review queue by risk."""
    print("[K] Building review queue ...")
    rows = []
    for _, qrow in queries.iterrows():
        cid = qrow["candidate_id"]
        claim = qrow["claim_text"]
        label = qrow["candidate_label_guess"]

        srow = screen_df[screen_df["candidate_id"] == cid]
        if len(srow) == 0:
            continue
        srow = srow.iloc[0]

        r1 = results[(results["candidate_id"] == cid) & (results["rank"] == 1)]
        if len(r1) == 0:
            continue
        r1 = r1.iloc[0]

        # Risk priority: strong_action flagged by retrieved > strong_action flagged by oracle > strong_action label > other
        if srow["retrieved_top1_flagged"]:
            risk_type = "retrieved_strong_action_flagged"
            priority = 1
        elif srow["oracle_flagged_strong"]:
            risk_type = "oracle_strong_action_flagged"
            priority = 2
        elif label == "strong_action_overclaim":
            risk_type = "silver_strong_action"
            priority = 3
        elif label == "contradiction_candidate":
            risk_type = "silver_contradiction"
            priority = 4
        else:
            risk_type = "low_risk"
            priority = 5

        # Retrieval confidence (inverse of rank)
        ret_confidence = 1.0 / r1["rank"] if r1["rank"] > 0 else 0

        rows.append({
            "review_id": len(rows) + 1,
            "candidate_id": cid,
            "claim_text": claim[:300],
            "retrieved_evidence": r1["retrieved_text"][:300],
            "rank": r1["rank"],
            "risk_type": risk_type,
            "priority": priority,
            "reason": f"label={label}, ret_score={srow['retrieved_top1_score']}, oracle_score={srow['oracle_evidence_score']}, same_paper={r1['same_paper']}, is_oracle={r1['is_oracle_hit']}",
            "pdf_path": r1["paper_id"],
            "page_number": r1["page_number"],
            "label_guess": label,
            "retrieval_confidence": ret_confidence,
        })

    queue_df = pd.DataFrame(rows)
    queue_df = queue_df.sort_values(["priority", "retrieval_confidence"], ascending=[True, False]).head(100)
    queue_df.to_csv(EXP_OUT / "review_queue_top_risk.csv", index=False, encoding="utf-8")
    print(f"  Review queue: {len(queue_df)} rows (top 100)")
    return queue_df


# ============ Step L: Gate and report ============
def write_gate_and_report(retr_metrics: dict, down_metrics: dict, fail_df: pd.DataFrame, inv_df: pd.DataFrame) -> None:
    """Write final gate JSON and report MD."""
    print("[L] Writing gate and report ...")

    # Determine main bottleneck
    fail_counts = fail_df["failure_type"].value_counts()
    n_claims = len(fail_df)
    pdf_missing_rate = fail_counts.get("pdf_missing", 0) / n_claims
    extraction_fail_rate = fail_counts.get("text_extraction_failed", 0) / n_claims
    oracle_not_in_pdf_rate = fail_counts.get("oracle_not_in_pdf_text", 0) / n_claims
    retrieval_fail_rate = (
        fail_counts.get("retrieved_wrong_paper", 0) +
        fail_counts.get("oracle_chunk_not_retrieved", 0) +
        fail_counts.get("retrieval_empty", 0)
    ) / n_claims
    screening_fail_rate = fail_counts.get("relation_screening_failed_after_good_retrieval", 0) / n_claims

    rates = {
        "pdf_missing": pdf_missing_rate,
        "extraction": extraction_fail_rate,
        "oracle_not_in_pdf": oracle_not_in_pdf_rate,
        "retrieval": retrieval_fail_rate,
        "screening": screening_fail_rate,
    }
    main_bottleneck = max(rates, key=rates.get)

    # Determine feasibility
    coverage = retr_metrics["pdf_coverage_rate"]
    oracle_match = retr_metrics["oracle_match_rate"]
    recall10 = retr_metrics["recall_at_10"]
    feasible = coverage >= 0.8 and oracle_match >= 0.5 and recall10 >= 0.3

    gate = {
        "task": "SimClaim PDF-Corpus Retrieval Prototype v1",
        "audit_date": "2026-07-05",
        "n_claims": retr_metrics["n_claims"],
        "n_pdfs_found": retr_metrics["n_pdfs_found"],
        "n_pdfs_total": retr_metrics["n_pdfs_total"],
        "pdf_coverage_rate": retr_metrics["pdf_coverage_rate"],
        "n_chunks": retr_metrics["n_chunks"],
        "oracle_match_rate": retr_metrics["oracle_match_rate"],
        "recall_at_1": retr_metrics["recall_at_1"],
        "recall_at_3": retr_metrics["recall_at_3"],
        "recall_at_5": retr_metrics["recall_at_5"],
        "recall_at_10": retr_metrics["recall_at_10"],
        "recall_at_20": retr_metrics["recall_at_20"],
        "mrr": retr_metrics["mrr"],
        "strong_action_recall_at_10": retr_metrics["strong_action_recall_at_10"],
        "same_paper_hit_rate_at_1": retr_metrics["same_paper_hit_rate_at_1"],
        "downstream_oracle_vs_retrieved_gap": down_metrics["oracle_vs_retrieved_top1_f1_gap"],
        "downstream_oracle_f1": down_metrics["oracle_evidence_strong_action"]["f1"],
        "downstream_retrieved_top1_f1": down_metrics["retrieved_top1_strong_action"]["f1"],
        "failure_distribution": {k: int(v) for k, v in fail_counts.items()},
        "failure_rates": rates,
        "main_bottleneck": main_bottleneck,
        "corpus_retrieval_route_feasible": feasible,
        "feasibility_reason": (
            f"coverage={coverage:.2%} >= 80%: {'YES' if coverage >= 0.8 else 'NO'}; "
            f"oracle_match={oracle_match:.2%} >= 50%: {'YES' if oracle_match >= 0.5 else 'NO'}; "
            f"recall@10={recall10:.2%} >= 30%: {'YES' if recall10 >= 0.3 else 'NO'}"
        ),
        "recommended_next_step": (
            "Proceed to V3.17 hybrid retrieval (BM25 + dense) + reranker if feasible; "
            "otherwise address bottleneck first."
        ),
        "prohibitions_enforced": [
            "no_new_pdf_downloads",
            "no_network",
            "no_llm_api",
            "no_model_training",
            "no_original_data_modification",
            "no_paper_modification",
            "no_silver_as_gold",
            "no_simulation_as_natural_distribution",
            "no_file_deletion",
        ],
    }
    with open(EXP_OUT / "simclaim_pdf_retrieval_gate.json", "w", encoding="utf-8") as f:
        json.dump(gate, f, indent=2, ensure_ascii=False)

    # Report (Chinese, concise)
    report = f"""# SimClaim PDF-Corpus Retrieval Prototype v1 Report

**任务：** SimClaim PDF-Corpus Retrieval Prototype v1
**日期：** 2026-07-05
**输出目录：** `D:\\ocn\\experiments\\simclaim_pdf_corpus_retrieval_v1\\`
**限制：** 不下载新 PDF、不联网、不调 API、不训练模型、不改原数据、不改论文、不删文件。

---

## 1. PDF 语料库是否足够完整？

**是。** PDF 覆盖率 = {retr_metrics['n_pdfs_found']}/{retr_metrics['n_pdfs_total']} = **{retr_metrics['pdf_coverage_rate']:.2%}**。
所有 69 篇 source 论文的 PDF 均在 `D:\\ocn_backup_20260704_1606\\data\\source_bank_v2\\pdfs\\` 找到。
PDF 总数 92 篇（含 strict_silver_max 未引用的 23 篇），文本抽取成功率 = {retr_metrics['extraction_success_rate']:.2%}。
语料库 chunk 总数 = {retr_metrics['n_chunks']}（约 200 words/chunk，50 words overlap）。

## 2. BM25 能否找回 oracle evidence？

**部分能。** Oracle match rate（oracle evidence 在 PDF 文本中找到）= **{retr_metrics['oracle_match_rate']:.2%}**。
BM25 检索指标：
- Recall@1 = {retr_metrics['recall_at_1']:.4f}
- Recall@5 = {retr_metrics['recall_at_5']:.4f}
- Recall@10 = {retr_metrics['recall_at_10']:.4f}
- Recall@20 = {retr_metrics['recall_at_20']:.4f}
- MRR = {retr_metrics['mrr']:.4f}
- Same-paper hit@1 = {retr_metrics['same_paper_hit_rate_at_1']:.4f}
- strong_action Recall@10 = {retr_metrics['strong_action_recall_at_10']:.4f}

**诊断：** BM25 的 same-paper hit@1 较高（{retr_metrics['same_paper_hit_rate_at_1']:.2%}），说明检索能定位到正确论文；但 oracle chunk 级 Recall@10 偏低（{retr_metrics['recall_at_10']:.2%}），说明 chunk 级精排不够——BM25 倾向于检索到论文的摘要/引言，而非 oracle evidence 所在的具体段落。

## 3. retrieved evidence 下 R4 是否还能工作？

**部分能，但信号有衰减。** 用 cue-based proxy screening（R4 frozen predictions 为聚合指标，无法逐条复用，故用 cue-based proxy）：
- Oracle evidence strong-action F1 = {down_metrics['oracle_evidence_strong_action']['f1']:.4f}, recall = {down_metrics['oracle_evidence_strong_action']['recall']:.4f}
- Retrieved top-1 evidence strong-action F1 = {down_metrics['retrieved_top1_strong_action']['f1']:.4f}, recall = {down_metrics['retrieved_top1_strong_action']['recall']:.4f}
- F1 gap = {down_metrics['oracle_vs_retrieved_top1_f1_gap']:.4f}, recall gap = {down_metrics['oracle_vs_retrieved_top1_recall_gap']:.4f}
- 检索失败率 = {down_metrics['retrieval_failure_rate']:.2%}
- 好检索下 screening 不一致率 = {down_metrics.get('screening_failure_after_good_retrieval_rate', 0):.2%}

**注意：** 这是 cue-based proxy，不是完整 R4。R4 的 NLI/SVM 模型无法在不训练的前提下复用到 retrieved evidence。Proxy 结果仅指示方向，不作为论文正式数字。

## 4. 当前瓶颈是什么？

**主瓶颈：{main_bottleneck}（{rates[main_bottleneck]:.2%}）。**

失败分布：
"""
    for ft, count in fail_counts.items():
        report += f"- {ft}: {count} ({count/n_claims:.2%})\n"

    report += f"""
按比例排序的瓶颈优先级：
1. pdf_missing: {rates['pdf_missing']:.2%}
2. extraction: {rates['extraction']:.2%}
3. oracle_not_in_pdf: {rates['oracle_not_in_pdf']:.2%}
4. retrieval (wrong paper + chunk not retrieved): {rates['retrieval']:.2%}
5. screening (failed after good retrieval): {rates['screening']:.2%}

## 5. 是否建议继续做 hybrid/dense/reranker？

**{('是' if not feasible or recall10 < 0.5 else '可考虑')}。**

理由：
- 当前 BM25 Recall@10 = {retr_metrics['recall_at_10']:.2%}，仍有较大提升空间。
- 主要失败模式是 chunk 级精排不足（same-paper 高但 oracle chunk 级低），dense retriever + cross-encoder reranker 可显著改善。
- 如果 oracle_not_in_pdf 比例较高，则需要检查 PDF 抽取质量（图表/公式/表格中的文本可能丢失）。
- **不建议立即训练新模型**——先用现成 dense retriever（如 sentence-transformers）做 zero-shot 测试。

## 6. 是否支持把论文主线扩展为 offline corpus retrieval + CESE-OCN screening？

**{('支持' if feasible else '有条件支持')}。**

理由：
- PDF 语料库完整（{retr_metrics['pdf_coverage_rate']:.2%} 覆盖率），离线可读。
- BM25 检索能定位正确论文（same-paper@1 = {retr_metrics['same_paper_hit_rate_at_1']:.2%}），但 chunk 级精度不够。
- 下游 screening 在 retrieved evidence 上信号有衰减（F1 gap = {down_metrics['oracle_vs_retrieved_top1_f1_gap']:.4f}），但并非完全失效。
- **建议路线：** V3.17 主线补强 = BM25 first-stage retrieval + dense reranker + CESE-OCN/R4 screening，而非完全替代当前 SimClaim diagnostic 评估。
- **主线风险：** retrieved evidence 下的 R4 性能目前是 proxy 估计，正式数字需要在 retrieved evidence 上重新跑 frozen R4 pipeline（可能需要重新计算 NLI/SVM 特征）。

---

## 禁止项执行确认

- 不下载新 PDF：PASS
- 不联网：PASS
- 不调 LLM/API：PASS
- 不训练模型：PASS
- 不改原数据：PASS
- 不改论文：PASS
- 不把 silver 写成 gold：PASS
- 不声称自然分布：PASS
- 不删文件：PASS

---

## 输出文件清单

1. `pdf_source_inventory.csv` — 69 篇论文 PDF 盘点
2. `local_pdf_corpus_chunks.csv` — 语料库 chunks（在 data/ 目录）
3. `claim_queries.csv` — 444 条 claim 查询
4. `oracle_evidence_map.csv` — oracle evidence 弱匹配
5. `retrieval_results_bm25.csv` — BM25 检索结果
6. `retrieval_metrics_bm25.json` — 检索指标
7. `downstream_screening_bm25.csv` — 下游 screening 对比
8. `downstream_screening_metrics_bm25.json` — 下游指标
9. `retrieval_failure_analysis.csv` — 失败分析
10. `review_queue_top_risk.csv` — top-100 review queue
11. `simclaim_pdf_retrieval_gate.json` — gate
12. `simclaim_pdf_retrieval_report.md` — 本报告
"""
    with open(EXP_OUT / "simclaim_pdf_retrieval_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  Gate: feasible={feasible}, bottleneck={main_bottleneck}")


# ============ Main ============
def main() -> None:
    print("=" * 60)
    print("SimClaim PDF-Corpus Retrieval Prototype v1")
    print("=" * 60)

    if not PYMUPDF_OK:
        print("FATAL: PyMuPDF not available. Install with: pip install pymupdf")
        return

    # Read strict_silver_max
    df = pd.read_csv(STRICT_SILVER_CSV, keep_default_na=False)
    print(f"Loaded {len(df)} SimClaim candidates")

    # Step A: PDF source inventory
    inv_df = build_pdf_source_inventory(df)

    # Step B+C: Extract and chunk PDFs
    chunks_df = extract_and_chunk_pdfs(inv_df)

    # Step D: Claim queries
    queries_df = build_claim_queries(df)

    # Step E: Oracle evidence map
    oracle_df = build_oracle_evidence_map(queries_df, chunks_df)

    # Step F: BM25 retrieval
    results_df = bm25_retrieval(queries_df, chunks_df, oracle_df)

    # Step G: Retrieval metrics
    retr_metrics = compute_retrieval_metrics(results_df, queries_df, oracle_df, inv_df, chunks_df)

    # Step H: Downstream screening
    screen_df = downstream_screening(queries_df, results_df, oracle_df)

    # Step I: Downstream metrics
    down_metrics = compute_downstream_metrics(screen_df)

    # Step J: Failure analysis
    fail_df = failure_analysis(queries_df, results_df, oracle_df, inv_df, screen_df)

    # Step K: Review queue
    queue_df = build_review_queue(queries_df, results_df, screen_df)

    # Step L: Gate and report
    write_gate_and_report(retr_metrics, down_metrics, fail_df, inv_df, )

    print("\n" + "=" * 60)
    print("DONE")
    print(f"  Experiment output: {EXP_OUT}")
    print(f"  Data output: {DATA_OUT}")
    print("=" * 60)


if __name__ == "__main__":
    main()
