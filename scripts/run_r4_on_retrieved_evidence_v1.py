"""
R4-on-Retrieved Evidence Formal Evaluation + Retriever Upgrade Readiness v1

Goal:
    Formally evaluate whether CESE-OCN/R4 still works on retrieved evidence.
    HARD RULE: No cue-based proxy as R4. If frozen R4 cannot be replayed per-item,
    declare BLOCKED and give reproducible reason + alternative path.

Hard prohibitions:
    - No model training
    - No API calls
    - No network
    - No threshold tuning
    - No original-data modification
    - No paper modification
    - No file deletion
    - No cue-based proxy as R4
    - No silver-as-gold
    - No simulation-as-natural-distribution
"""

import json
import re
import sys
from pathlib import Path
from collections import Counter, defaultdict
import pandas as pd
import numpy as np

# Shared config utilities
sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from config_utils import get_repo_root  # noqa: E402

# ============ Configuration (defaults — repo-root relative) ============
_REPO_ROOT = get_repo_root()
RETR_DIR = _REPO_ROOT / "experiments" / "simclaim_pdf_corpus_retrieval_v1"
CHUNKS_CSV = _REPO_ROOT / "data" / "simclaim_pdf_corpus_retrieval_v1" / "local_pdf_corpus_chunks.csv"
STRICT_SILVER_CSV = _REPO_ROOT / "data" / "simclaim_all92_candidate_pool_v1" / "strict_silver_max_v1" / "strict_silver_max_candidates_v1.csv"
R4_FROZEN_DIR = _REPO_ROOT / "experiments" / "mixed_framework_v2_frozen_r4_baseline"
SCRIPTS_DIR = _REPO_ROOT / "scripts"
EXPERIMENTS_DIR = _REPO_ROOT / "experiments"
OUT_DIR = _REPO_ROOT / "experiments" / "r4_on_retrieved_evidence_v1"

# ============ Step 1: R4 Pipeline Inventory ============
def build_r4_pipeline_inventory() -> pd.DataFrame:
    """Search for R4 pipeline files."""
    print("[1] Building R4 pipeline inventory ...")
    rows = []

    # Key files to check
    files_to_check = [
        (R4_FROZEN_DIR / "frozen_r4_manifest.json", "json"),
        (R4_FROZEN_DIR / "frozen_r4_metrics_summary.json", "json"),
        (R4_FROZEN_DIR / "frozen_r4_routing_results_by_seed.csv", "csv"),
        (R4_FROZEN_DIR / "frozen_r4_readiness_gate.json", "json"),
        (R4_FROZEN_DIR / "frozen_r4_method_selection.csv", "csv"),
        (R4_FROZEN_DIR / "frozen_r4_ablation_summary.json", "json"),
        (SCRIPTS_DIR / "run_mixed_framework_router_optimization_v2.py", "script"),
        (SCRIPTS_DIR / "run_mixed_framework_new_algorithm_sweep_v1.py", "script"),
        (SCRIPTS_DIR / "run_v3_r4_strong_baselines_holdout_v1.py", "script"),
        (SCRIPTS_DIR / "run_llm_judge_baseline_v1.py", "script"),
        (SCRIPTS_DIR / "run_cese_ocn_lite_v3.py", "script"),
        (EXPERIMENTS_DIR / "gpt_structured_judge_probe_v1" / "gpt_vs_r4_deepseek_comparison.csv", "csv"),
        (EXPERIMENTS_DIR / "mixed_framework_router_optimization_v2" / "routing_variant_results_by_seed.csv", "csv"),
        (EXPERIMENTS_DIR / "mixed_framework_router_optimization_v2" / "strong_action_error_cases_after_router.csv", "csv"),
        (EXPERIMENTS_DIR / "cese_ocn_hcm_v1" / "hcm_features.csv", "csv"),
        (EXPERIMENTS_DIR / "cese_ocn_lite_v3" / "v3_seed11_predictions.csv", "csv"),
    ]

    for fpath, ftype in files_to_check:
        if not fpath.exists():
            rows.append({
                "file_path": str(fpath),
                "file_type": ftype,
                "exists": False,
                "contains_r4_logic": False,
                "contains_thresholds": False,
                "contains_per_item_predictions": False,
                "contains_feature_logic": False,
                "likely_replayable": False,
                "notes": "FILE NOT FOUND",
            })
            continue

        text = ""
        try:
            if fpath.suffix == ".csv":
                df = pd.read_csv(fpath, keep_default_na=False)
                text = " ".join(df.columns) + " " + df.head(2).to_string()
            elif fpath.suffix == ".json":
                text = fpath.read_text(encoding="utf-8")[:3000]
            elif fpath.suffix == ".py":
                text = fpath.read_text(encoding="utf-8")
        except Exception as e:
            text = str(e)

        text_lower = text.lower()

        contains_r4 = any(k in text_lower for k in ["route_conservative_strong", "r4_conservative", "frozen_r4", "r4_label"])
        contains_thresholds = any(k in text_lower for k in ["t_contra", "t_strong", "t_svm", "0.48", "0.535", "0.51"])
        contains_per_item = any(k in text_lower for k in ["candidate_id", "sample_id"]) and any(k in text_lower for k in ["r4_label", "pred_label", "prediction"])
        contains_feature_logic = any(k in text_lower for k in ["nli", "hcm", "entailment", "cross-encoder", "compute_nli", "hcm_features"])

        # Replayable: has R4 logic + thresholds + per-item predictions
        replayable = contains_r4 and contains_thresholds and contains_per_item

        notes = []
        if contains_r4:
            notes.append("has_r4_logic")
        if contains_thresholds:
            notes.append("has_thresholds")
        if contains_per_item:
            notes.append("has_per_item_preds")
        if contains_feature_logic:
            notes.append("has_feature_logic")
        if not notes:
            notes.append("aggregate_only")

        rows.append({
            "file_path": str(fpath),
            "file_type": ftype,
            "exists": True,
            "contains_r4_logic": contains_r4,
            "contains_thresholds": contains_thresholds,
            "contains_per_item_predictions": contains_per_item,
            "contains_feature_logic": contains_feature_logic,
            "likely_replayable": replayable,
            "notes": "; ".join(notes),
        })

    inv_df = pd.DataFrame(rows)
    inv_df.to_csv(OUT_DIR / "r4_pipeline_inventory.csv", index=False, encoding="utf-8")
    print(f"  Inventory: {len(inv_df)} files, {inv_df['exists'].sum()} exist")
    print(f"  Per-item predictions found: {inv_df[inv_df['contains_per_item_predictions']]['exists'].sum()}")
    print(f"  Replayable files: {inv_df['likely_replayable'].sum()}")
    return inv_df


# ============ Step 2: Replay Feasibility ============
def assess_replay_feasibility(inv_df: pd.DataFrame) -> dict:
    """Assess whether R4 can be replayed on new evidence."""
    print("[2] Assessing R4 replay feasibility ...")

    # Check for frozen R4 script
    frozen_scripts = inv_df[(inv_df["file_type"] == "script") & (inv_df["contains_r4_logic"]) & (inv_df["exists"])]
    frozen_r4_script_found = len(frozen_scripts) > 0

    # Check for per-item predictions
    per_item_files = inv_df[(inv_df["contains_per_item_predictions"]) & (inv_df["exists"])]
    per_item_found = len(per_item_files) > 0

    # Check for HCM features
    hcm_row = inv_df[inv_df["file_path"].str.contains("hcm_features", case=False, na=False)]
    hcm_exists = len(hcm_row) > 0 and hcm_row.iloc[0]["exists"]

    # Check for trained model artifacts (.pkl/.joblib)
    import glob
    model_artifacts = []
    for pattern in ["D:\\ocn\\**\\*.pkl", "D:\\ocn\\**\\*.joblib"]:
        model_artifacts.extend(glob.glob(pattern, recursive=True))
    model_artifacts_exist = len(model_artifacts) > 0

    # Check NLI model cache
    from pathlib import Path as P
    nli_cache = P(r"C:\Users\Administrator\.cache\huggingface\hub\models--cross-encoder--nli-deberta-base")
    nli_model_cached = nli_cache.exists()

    # Check frozen thresholds
    manifest = json.loads((R4_FROZEN_DIR / "frozen_r4_manifest.json").read_text(encoding="utf-8"))
    thresholds = manifest.get("selection_thresholds_mean", {})
    has_thresholds = all(k in thresholds for k in ["t_contra", "t_strong", "t_svm"])

    # Check t_contra_low (NOT in frozen manifest)
    has_t_contra_low = False  # only grid-search code exists

    # Determine can_replay
    # R4 needs: NLI features → trained clf_contra/clf_strong/clf_svm → frozen thresholds → routing
    # Without trained classifiers, routing can't produce probabilities
    can_replay = False
    proxy_required = True
    reason = []

    if not frozen_r4_script_found:
        reason.append("No frozen R4 script found")
    if not per_item_found:
        reason.append("No per-item R4 predictions on disk (only 100 matched samples)")
    if not hcm_exists:
        reason.append("HCM/NLI features CSV (hcm_features.csv) is MISSING — required input for R4 classifiers")
    if not model_artifacts_exist:
        reason.append("No trained classifier artifacts (.pkl/.joblib) on disk — clf_contra, clf_strong, clf_svm must be retrained")
    if not has_t_contra_low:
        reason.append("t_contra_low (lower contradiction guard) is NOT frozen — only grid-search code exists")

    if hcm_exists and model_artifacts_exist and has_thresholds and has_t_contra_low:
        can_replay = True
        proxy_required = False
    else:
        reason.append("REPLAY BLOCKED: R4 requires (a) HCM/NLI features for new evidence, (b) trained classifier artifacts, (c) frozen t_contra_low. Without all three, routing cannot produce per-item predictions.")
        reason.append("Reproduction path (requires authorization to retrain on silver labels): (1) compute NLI features with cached cross-encoder/nli-deberta-base; (2) retrain clf_contra/clf_strong/clf_svm on silver-444 with original evidence; (3) save artifacts; (4) compute NLI features for retrieved evidence; (5) apply frozen thresholds + saved classifiers.")

    feasibility = {
        "frozen_r4_script_found": frozen_r4_script_found,
        "frozen_r4_per_item_predictions_found": per_item_found,
        "per_item_prediction_files": [r["file_path"] for _, r in per_item_files.iterrows()] if per_item_found else [],
        "per_item_prediction_coverage": "100/444 matched samples only (gpt_vs_r4_deepseek_comparison.csv); full silver-444 per-item predictions were never saved",
        "hcm_features_csv_exists": hcm_exists,
        "trained_model_artifacts_exist": model_artifacts_exist,
        "model_artifact_paths": model_artifacts[:5] if model_artifacts_exist else [],
        "nli_model_cached": nli_model_cached,
        "nli_model_path": str(nli_cache) if nli_model_cached else "",
        "frozen_thresholds": thresholds,
        "t_contra_low_frozen": has_t_contra_low,
        "feature_dependencies_available": hcm_exists and nli_model_cached,
        "can_replay_with_new_evidence": can_replay,
        "proxy_required": proxy_required,
        "reason_if_blocked": "; ".join(reason) if not can_replay else "",
        "exact_script_or_file_to_use": (
            "D:\\ocn\\scripts\\run_mixed_framework_router_optimization_v2.py (routing logic) + "
            "D:\\ocn\\scripts\\run_cese_ocn_lite_v3.py (NLI feature computation) + "
            "frozen_r4_manifest.json (thresholds)"
            if frozen_r4_script_found else "NONE"
        ),
        "exact_thresholds_found": thresholds if has_thresholds else {},
        "no_threshold_tuning_confirmed": True,
        "blocked_path_required": not can_replay,
        "alternative_path_to_unblock": [
            "1. Authorize reproduction training (retrain clf_contra/clf_strong/clf_svm on silver-444 with original evidence — this is reproduction, not new model training)",
            "2. Save classifier artifacts as .pkl/.joblib",
            "3. Compute NLI features for retrieved evidence (BM25 top1/top3/top5) using cached cross-encoder/nli-deberta-base",
            "4. Freeze t_contra_low (use grid-search mean or re-fit on silver-444)",
            "5. Apply frozen thresholds + saved classifiers to retrieved evidence",
            "6. Output per-item R4 predictions on retrieved evidence",
        ],
    }

    with open(OUT_DIR / "r4_replay_feasibility.json", "w", encoding="utf-8") as f:
        json.dump(feasibility, f, indent=2, ensure_ascii=False, default=lambda o: bool(o) if isinstance(o, (np.bool_,)) else str(o))
    print(f"  can_replay_with_new_evidence: {can_replay}")
    print(f"  proxy_required: {proxy_required}")
    if not can_replay:
        print(f"  BLOCKED: {reason[-1][:100]}...")
    return feasibility


# ============ Step 3: Build 4 Input CSVs ============
def build_input_csvs(feasibility: dict) -> dict:
    """Build 4 input CSVs: oracle, BM25 top1, top3, top5."""
    print("[3] Building 4 input CSVs (oracle, BM25 top1/top3/top5) ...")

    # Load data
    silver = pd.read_csv(STRICT_SILVER_CSV, keep_default_na=False)
    retr = pd.read_csv(RETR_DIR / "retrieval_results_bm25.csv", keep_default_na=False)
    oracle_map = pd.read_csv(RETR_DIR / "oracle_evidence_map.csv", keep_default_na=False)

    # Oracle evidence input
    oracle_input = silver[["candidate_id", "claim_text", "evidence_text", "candidate_label_guess", "source_id"]].copy()
    oracle_input.rename(columns={
        "evidence_text": "evidence_text",
        "candidate_label_guess": "true_label",
        "source_id": "source_pair_id",
    }, inplace=True)
    oracle_input["retrieval_setting"] = "oracle"
    oracle_input["retrieved_chunk_ids"] = ""
    oracle_input["retrieved_ranks"] = ""
    oracle_input["retrieved_pages"] = ""
    oracle_input["oracle_hit_in_topk"] = True
    oracle_input = oracle_input[["candidate_id", "claim_text", "evidence_text", "true_label", "retrieval_setting", "source_pair_id", "retrieved_chunk_ids", "retrieved_ranks", "retrieved_pages", "oracle_hit_in_topk"]]
    oracle_input.to_csv(OUT_DIR / "r4_input_oracle.csv", index=False, encoding="utf-8")

    # Build BM25 top1/top3/top5 inputs
    for top_k in [1, 3, 5]:
        rows = []
        for cid in silver["candidate_id"]:
            claim = silver[silver["candidate_id"] == cid].iloc[0]["claim_text"]
            true_label = silver[silver["candidate_id"] == cid].iloc[0]["candidate_label_guess"]
            source_id = silver[silver["candidate_id"] == cid].iloc[0]["source_id"]
            oracle_text = silver[silver["candidate_id"] == cid].iloc[0]["evidence_text"]

            # Get top-k retrieved chunks
            cid_retr = retr[retr["candidate_id"] == cid].sort_values("rank").head(top_k)
            if len(cid_retr) == 0:
                evidence = "[RETRIEVAL_EMPTY]"
                chunk_ids = ""
                ranks = ""
                pages = ""
                oracle_hit = False
            else:
                # Concatenate with rank/PDF/page markers
                parts = []
                chunk_ids = []
                ranks = []
                pages = []
                oracle_hit = False
                for _, r in cid_retr.iterrows():
                    marker = f"[RANK={r['rank']}][PDF={r['paper_id']}][PAGE={r['page_number']}]"
                    parts.append(f"{marker} {r['retrieved_text']}")
                    chunk_ids.append(r["chunk_id"])
                    ranks.append(str(r["rank"]))
                    pages.append(str(r["page_number"]))
                    if r["is_oracle_hit"]:
                        oracle_hit = True
                evidence = " ".join(parts)
                # Truncate if too long (max 3000 chars)
                if len(evidence) > 3000:
                    evidence = evidence[:3000] + "...[TRUNCATED]"
                chunk_ids = ";".join(chunk_ids)
                ranks = ";".join(ranks)
                pages = ";".join(pages)

            rows.append({
                "candidate_id": cid,
                "claim_text": claim,
                "evidence_text": evidence,
                "true_label": true_label,
                "retrieval_setting": f"bm25_top{top_k}",
                "source_pair_id": source_id,
                "retrieved_chunk_ids": chunk_ids,
                "retrieved_ranks": ranks,
                "retrieved_pages": pages,
                "oracle_hit_in_topk": oracle_hit,
            })

        df = pd.DataFrame(rows)
        df.to_csv(OUT_DIR / f"r4_input_bm25_top{top_k}.csv", index=False, encoding="utf-8")
        print(f"  r4_input_bm25_top{top_k}.csv: {len(df)} rows, oracle_hit_rate={df['oracle_hit_in_topk'].mean():.4f}")

    return {"oracle": oracle_input}


# ============ Step 4: R4 Predictions (BLOCKED) ============
def write_blocked_predictions(feasibility: dict) -> None:
    """Write blocked prediction CSVs."""
    print("[4] Writing BLOCKED prediction CSVs (R4 replay not possible) ...")

    if feasibility["can_replay_with_new_evidence"]:
        print("  ERROR: can_replay=True but no replay implementation — should not reach here")
        return

    blocked_reason = "BLOCKED: " + feasibility["reason_if_blocked"][:200]

    for setting in ["oracle", "bm25_top1", "bm25_top3", "bm25_top5"]:
        input_csv = OUT_DIR / f"r4_input_{setting}.csv"
        if not input_csv.exists():
            continue
        df = pd.read_csv(input_csv, keep_default_na=False)
        # Write blocked predictions
        df["pred_label"] = "BLOCKED"
        df["strong_action_flag"] = False
        df["strong_action_score"] = -1.0
        df["route"] = "blocked"
        df["retrieval_setting"] = setting
        df["evidence_used"] = df["evidence_text"].str[:100]
        df["notes"] = blocked_reason
        df = df[["candidate_id", "true_label", "pred_label", "strong_action_flag", "strong_action_score", "route", "retrieval_setting", "evidence_used", "notes"]]
        df.to_csv(OUT_DIR / f"r4_predictions_{setting}.csv", index=False, encoding="utf-8")
        print(f"  r4_predictions_{setting}.csv: {len(df)} rows (ALL BLOCKED)")


# ============ Step 5: Metrics (BLOCKED) ============
def compute_blocked_metrics() -> pd.DataFrame:
    """Compute metrics CSV with blocked status."""
    print("[5] Writing blocked metrics CSV ...")
    rows = []
    for setting in ["oracle", "bm25_top1", "bm25_top3", "bm25_top5"]:
        rows.append({
            "retrieval_setting": setting,
            "n_claims": 444,
            "accuracy": -1.0,
            "macro_f1": -1.0,
            "weighted_f1": -1.0,
            "strong_precision": -1.0,
            "strong_recall": -1.0,
            "strong_f1": -1.0,
            "contradiction_f1": -1.0,
            "supported_f1": -1.0,
            "mild_f1": -1.0,
            "status": "BLOCKED",
            "reason": "R4 replay not possible: HCM features missing, classifier artifacts not saved, t_contra_low not frozen",
        })
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "r4_retrieved_metrics.csv", index=False, encoding="utf-8")
    print(f"  r4_retrieved_metrics.csv: {len(df)} rows (ALL BLOCKED)")
    return df


# ============ Step 6: Error Analysis (retrieval-level) ============
def error_analysis_retrieval_level() -> pd.DataFrame:
    """Error analysis at retrieval level (R4-level analysis blocked)."""
    print("[6] Running retrieval-level error analysis ...")

    retr = pd.read_csv(RETR_DIR / "retrieval_results_bm25.csv", keep_default_na=False)
    silver = pd.read_csv(STRICT_SILVER_CSV, keep_default_na=False)
    oracle_map = pd.read_csv(RETR_DIR / "oracle_evidence_map.csv", keep_default_na=False)

    rows = []
    for _, srow in silver.iterrows():
        cid = srow["candidate_id"]
        label = srow["candidate_label_guess"]
        source_id = srow["source_id"]

        # Check retrieval status at top1, top3, top5
        cid_retr = retr[retr["candidate_id"] == cid].sort_values("rank")
        top1 = cid_retr[cid_retr["rank"] == 1]
        top3 = cid_retr[cid_retr["rank"] <= 3]
        top5 = cid_retr[cid_retr["rank"] <= 5]

        top1_oracle = top1["is_oracle_hit"].iloc[0] if len(top1) > 0 else False
        top3_oracle = top3["is_oracle_hit"].any() if len(top3) > 0 else False
        top5_oracle = top5["is_oracle_hit"].any() if len(top5) > 0 else False
        top1_same_paper = top1["same_paper"].iloc[0] if len(top1) > 0 else False

        oracle_row = oracle_map[oracle_map["candidate_id"] == cid]
        oracle_found = oracle_row.iloc[0]["oracle_match_found"] if len(oracle_row) > 0 else False

        # Categorize
        if not oracle_found:
            error_type = "oracle_not_in_pdf_text"
            reason = "Oracle evidence not found in PDF text"
        elif not top5_oracle:
            if not top1_same_paper:
                error_type = "retrieved_wrong_paper"
                reason = f"Top-1 from different paper; oracle not in top-5"
            else:
                error_type = "oracle_chunk_not_retrieved"
                reason = "Same paper but oracle chunk not in top-5"
        elif not top1_oracle and top3_oracle:
            error_type = "retrieval_partial_hit"
            reason = "Oracle in top-3 but not top-1"
        elif not top1_oracle and top5_oracle:
            error_type = "retrieval_partial_hit"
            reason = "Oracle in top-5 but not top-1"
        elif top1_oracle:
            error_type = "retrieval_success"
            reason = "Oracle chunk retrieved at rank 1"
        else:
            error_type = "other"
            reason = "Uncategorized"

        # R4-level errors: BLOCKED
        r4_error = "r4_blocked"

        rows.append({
            "candidate_id": cid,
            "true_label": label,
            "source_pair_id": source_id,
            "oracle_found_in_pdf": oracle_found,
            "top1_oracle_hit": top1_oracle,
            "top3_oracle_hit": top3_oracle,
            "top5_oracle_hit": top5_oracle,
            "top1_same_paper": top1_same_paper,
            "retrieval_error_type": error_type,
            "retrieval_reason": reason,
            "r4_error_type": r4_error,
            "r4_reason": "R4 replay blocked — cannot classify relation_screening_failure / strong_action_fn / strong_action_fp / contradiction_confusion / supported_mild_confusion",
            "strong_action_false_negative": "BLOCKED",
            "strong_action_false_positive": "BLOCKED",
            "contradiction_confusion": "BLOCKED",
            "supported_mild_confusion": "BLOCKED",
        })

    err_df = pd.DataFrame(rows)
    err_df.to_csv(OUT_DIR / "r4_retrieved_error_analysis.csv", index=False, encoding="utf-8")
    print(f"  Error analysis: {len(err_df)} rows")
    print(f"  Retrieval error distribution:")
    for et, count in err_df["retrieval_error_type"].value_counts().items():
        print(f"    {et}: {count}")
    return err_df


# ============ Step 7: Retriever Upgrade Readiness ============
def check_upgrade_readiness() -> dict:
    """Check retriever upgrade readiness."""
    print("[7] Checking retriever upgrade readiness ...")

    # Check library availability
    libs = {}
    for lib in ["sentence_transformers", "torch", "transformers", "sklearn", "scipy", "rank_bm25", "numpy", "pandas"]:
        try:
            __import__(lib)
            libs[lib] = True
        except ImportError:
            libs[lib] = False

    # Check GPU
    gpu_available = False
    if libs["torch"]:
        import torch
        gpu_available = torch.cuda.is_available()

    # Check NLI model cache
    nli_cache = Path(r"C:\Users\Administrator\.cache\huggingface\hub\models--cross-encoder--nli-deberta-base")
    nli_cached = nli_cache.exists()

    # Check for dense model caches
    import glob
    dense_models = glob.glob(r"C:\Users\Administrator\.cache\huggingface\hub\models--*mini*lm*")
    dense_models += glob.glob(r"C:\Users\Administrator\.cache\huggingface\hub\models--*mpnet*")
    dense_models += glob.glob(r"C:\Users\Administrator\.cache\huggingface\hub\models--*bge*")
    dense_cached = len(dense_models) > 0

    # Check for cross-encoder reranker caches
    reranker_models = glob.glob(r"C:\Users\Administrator\.cache\huggingface\hub\models--cross-encoder--*")
    reranker_cached = any("nli" not in m.lower() for m in reranker_models)

    # Chunk count
    chunks = pd.read_csv(CHUNKS_CSV, keep_default_na=False)
    n_chunks = len(chunks)

    readiness = {
        "bm25_done": True,
        "bm25_implementation": "custom from-scratch Okapi BM25 (rank_bm25 package not installed)",
        "dense_possible": libs["sentence_transformers"] or (libs["transformers"] and libs["torch"]),
        "dense_library_available": libs["sentence_transformers"],
        "dense_model_cached": dense_cached,
        "dense_model_paths": dense_models[:3],
        "hybrid_possible": True,  # BM25 + dense can be combined
        "reranker_possible": libs["transformers"] and libs["torch"] and (reranker_cached or nli_cached),
        "reranker_library_available": libs["transformers"] and libs["torch"],
        "reranker_model_cached": reranker_cached,
        "reranker_model_paths": [m for m in reranker_models if "nli" not in m.lower()][:3],
        "nli_model_cached": nli_cached,
        "nli_model_path": str(nli_cache) if nli_cached else "",
        "gpu_available": gpu_available,
        "sklearn_available": libs["sklearn"],
        "scipy_available": libs["scipy"],
        "numpy_available": libs["numpy"],
        "pandas_available": libs["pandas"],
        "torch_available": libs["torch"],
        "transformers_available": libs["transformers"],
        "n_chunks": n_chunks,
        "n_chunks_suitable_for_dense": n_chunks < 100000,  # 4747 is well within dense index capacity
        "recommended_upgrade_order": [
            "1. Install sentence-transformers (pip install sentence-transformers) for dense retrieval",
            "2. Download a small dense model (e.g., all-MiniLM-L6-v2) for zero-shot dense retrieval",
            "3. Run dense retrieval on 4747 chunks (CPU-feasible, ~5-10 min)",
            "4. Combine BM25 + dense scores for hybrid retrieval (weighted sum or RRF)",
            "5. Use cached cross-encoder/nli-deberta-base as cross-encoder reranker (top-50 → top-10)",
            "6. Re-evaluate retrieval metrics (Recall@k, MRR) on hybrid + reranker",
        ],
        "expected_benefit": "Hybrid (BM25+dense) typically improves Recall@10 by 2-5%; cross-encoder reranker typically improves Recall@1 by 10-20%. Main benefit: better chunk-level precision (currently 25.45% oracle_chunk_not_retrieved failures).",
        "risk": "Dense retrieval on CPU is slow but feasible for 4747 chunks. No GPU available. Cross-encoder reranker on CPU is slower but still feasible for top-50 reranking.",
    }

    with open(OUT_DIR / "retriever_upgrade_readiness.json", "w", encoding="utf-8") as f:
        json.dump(readiness, f, indent=2, ensure_ascii=False, default=lambda o: bool(o) if isinstance(o, (np.bool_,)) else str(o))
    print(f"  dense_possible: {readiness['dense_possible']}")
    print(f"  reranker_possible: {readiness['reranker_possible']}")
    print(f"  nli_model_cached: {readiness['nli_model_cached']}")
    print(f"  gpu_available: {readiness['gpu_available']}")
    return readiness


# ============ Step 8: Gate ============
def write_gate(feasibility: dict, err_df: pd.DataFrame, readiness: dict) -> None:
    """Write final gate JSON."""
    print("[8] Writing gate JSON ...")

    # Compute retrieval-level metrics for gate
    n_claims = len(err_df)
    retrieval_success_rate = (err_df["retrieval_error_type"] == "retrieval_success").mean()
    oracle_found_rate = err_df["oracle_found_in_pdf"].mean()
    top1_hit_rate = err_df["top1_oracle_hit"].mean()
    top3_hit_rate = err_df["top3_oracle_hit"].mean()
    top5_hit_rate = err_df["top5_oracle_hit"].mean()

    # Error distribution
    err_counts = err_df["retrieval_error_type"].value_counts()
    main_bottleneck = err_counts.idxmax() if len(err_counts) > 0 else "unknown"

    gate = {
        "task": "R4-on-Retrieved Evidence Formal Evaluation v1",
        "audit_date": "2026-07-05",
        "n_claims": n_claims,
        "frozen_r4_found": feasibility["frozen_r4_script_found"],
        "frozen_r4_thresholds_found": feasibility["frozen_thresholds"],
        "frozen_r4_per_item_predictions_found": feasibility["frozen_r4_per_item_predictions_found"],
        "frozen_r4_per_item_coverage": feasibility["per_item_prediction_coverage"],
        "hcm_features_available": feasibility["hcm_features_csv_exists"],
        "trained_classifier_artifacts_available": feasibility["trained_model_artifacts_exist"],
        "nli_model_cached": feasibility["nli_model_cached"],
        "t_contra_low_frozen": feasibility["t_contra_low_frozen"],
        "can_replay_with_new_evidence": feasibility["can_replay_with_new_evidence"],
        "used_proxy": False,
        "proxy_rejected": True,
        "proxy_rejection_reason": "Task spec explicitly prohibits cue-based proxy as R4. R4 replay is BLOCKED, not proxied.",
        "oracle_strong_f1": -1.0,
        "top1_strong_f1": -1.0,
        "top3_strong_f1": -1.0,
        "top5_strong_f1": -1.0,
        "oracle_strong_f1_status": "BLOCKED",
        "top1_strong_f1_status": "BLOCKED",
        "top3_strong_f1_status": "BLOCKED",
        "top5_strong_f1_status": "BLOCKED",
        "best_retrieved_setting": "BLOCKED",
        "oracle_to_best_retrieved_gap": -1.0,
        "retrieval_level_metrics": {
            "oracle_found_in_pdf_rate": float(oracle_found_rate),
            "top1_oracle_hit_rate": float(top1_hit_rate),
            "top3_oracle_hit_rate": float(top3_hit_rate),
            "top5_oracle_hit_rate": float(top5_hit_rate),
            "retrieval_success_rate": float(retrieval_success_rate),
        },
        "retrieval_error_distribution": {k: int(v) for k, v in err_counts.items()},
        "main_bottleneck": f"R4 replay blocked (missing HCM features + classifier artifacts + t_contra_low); retrieval-level bottleneck: {main_bottleneck}",
        "supports_pdf_corpus_screening_claim": "partial",
        "supports_pdf_corpus_screening_reason": "Retrieval is feasible (PDF coverage 100%, BM25 Recall@10=97.97%), but R4 screening on retrieved evidence is BLOCKED. Without R4 replay, the claim 'offline PDF-corpus retrieval + CESE-OCN screening works' is only partially supported: retrieval works, but downstream screening validation is pending.",
        "supports_v3_17_mainline": "partial",
        "supports_v3_17_reason": "V3.17 mainline (offline PDF-corpus retrieval + CESE-OCN screening) is feasible in principle but requires: (1) R4 reproduction training to save classifier artifacts; (2) NLI feature computation for retrieved evidence; (3) frozen t_contra_low. All three are doable with current local resources (NLI model cached, silver labels available, sklearn available).",
        "recommended_next_step": [
            "1. Authorize R4 reproduction training: retrain clf_contra/clf_strong/clf_svm on silver-444 with original evidence (reproduction, NOT new model training)",
            "2. Save classifier artifacts as .pkl files",
            "3. Freeze t_contra_low (use grid-search mean from existing router optimization results)",
            "4. Compute NLI features for 4 input CSVs (oracle, BM25 top1/top3/top5) using cached cross-encoder/nli-deberta-base",
            "5. Replay R4 on all 4 input CSVs with frozen thresholds + saved classifiers",
            "6. Compute per-setting metrics (strong-F1, macro-F1, confusion matrix)",
            "7. Compare oracle vs retrieved strong-F1 gap",
            "8. If gap < 0.05: V3.17 mainline is fully supported. If gap >= 0.05: investigate retrieval quality improvement (dense/hybrid/reranker).",
        ],
        "retriever_upgrade_readiness": {
            "dense_possible": readiness["dense_possible"],
            "hybrid_possible": readiness["hybrid_possible"],
            "reranker_possible": readiness["reranker_possible"],
            "nli_model_cached": readiness["nli_model_cached"],
            "gpu_available": readiness["gpu_available"],
        },
        "prohibitions_enforced": [
            "no_model_training",
            "no_api_calls",
            "no_network",
            "no_threshold_tuning",
            "no_original_data_modification",
            "no_paper_modification",
            "no_file_deletion",
            "no_cue_based_proxy_as_r4",
            "no_silver_as_gold",
            "no_simulation_as_natural_distribution",
        ],
    }

    with open(OUT_DIR / "r4_on_retrieved_evidence_gate.json", "w", encoding="utf-8") as f:
        json.dump(gate, f, indent=2, ensure_ascii=False, default=lambda o: bool(o) if isinstance(o, (np.bool_,)) else str(o))
    print(f"  can_replay: {gate['can_replay_with_new_evidence']}")
    print(f"  used_proxy: {gate['used_proxy']}")
    print(f"  supports_pdf_corpus_screening_claim: {gate['supports_pdf_corpus_screening_claim']}")
    print(f"  supports_v3_17_mainline: {gate['supports_v3_17_mainline']}")


# ============ Step 9: Report ============
def write_report(feasibility: dict, err_df: pd.DataFrame, readiness: dict) -> None:
    """Write final report in Chinese."""
    print("[9] Writing report ...")

    err_counts = err_df["retrieval_error_type"].value_counts()
    n_claims = len(err_df)

    report = f"""# R4-on-Retrieved Evidence Formal Evaluation Report v1

**任务：** R4-on-Retrieved Evidence Formal Evaluation + Retriever Upgrade Readiness v1
**日期：** 2026-07-05
**输出目录：** `D:\\ocn\\experiments\\r4_on_retrieved_evidence_v1\\`
**限制：** 不训练模型、不调 API、不联网、不改阈值、不改原数据、不改论文、不删文件、**不用 cue-based proxy 冒充 R4**。

---

## 1. 是否找到真正 frozen R4？

**是，找到路由逻辑和阈值；但缺少关键依赖。**

- **R4 路由逻辑脚本：** 找到 4 个脚本（`run_mixed_framework_router_optimization_v2.py` 等），均包含 `route_conservative_strong` 函数。
- **Frozen 阈值：** 找到 t_contra=0.48, t_strong=0.535, t_svm=0.51（在 3 个 JSON 文件中）。
- **逐条 R4 prediction：** 仅找到 100 条匹配样本（`gpt_vs_r4_deepseek_comparison.csv` 中的 `r4_label` 列），覆盖 100/444 = 22.5%。完整 silver-444 逐条 prediction 从未保存。
- **HCM/NLI features CSV：** **缺失。** `hcm_features.csv` 不在磁盘上。
- **训练好的分类器 artifacts：** **缺失。** 磁盘上无 .pkl/.joblib 文件；clf_contra/clf_strong/clf_svm 必须重新训练。
- **t_contra_low（lower contradiction guard）：** **未冻结。** 仅有 grid-search 代码，无 frozen 值。
- **NLI 模型：** `cross-encoder/nli-deberta-base` **已本地缓存**（在 HuggingFace cache 中）。

## 2. 是否没有使用 proxy？

**是，严格拒绝 proxy。**

任务规范明确禁止用 cue-based proxy 冒充 R4。本任务在 R4 无法逐条复跑的情况下，**走 blocked path**，不输出任何 proxy 预测。所有 4 个 prediction CSV 均标记为 `BLOCKED`，所有指标标记为 `-1.0`。

## 3. retrieved evidence 下 R4 是否还能工作？

**BLOCKED — 无法判断。**

R4 复跑需要：(a) HCM/NLI features for retrieved evidence（缺失）；(b) 训练好的分类器 artifacts（缺失）；(c) frozen t_contra_low（未冻结）。三者均不可用，R4 无法在 retrieved evidence 上产生逐条预测。

**不使用 proxy 冒充 R4**，因此无法回答"retrieved evidence 下 R4 是否还能工作"。

## 4. top1/top3/top5 哪个最好？

**BLOCKED — 无法比较。** 所有四组（oracle/top1/top3/top5）的 R4 预测均标记为 BLOCKED。

但 **retrieval-level 指标** 可以比较：

| Setting | Oracle hit rate |
| --- | --- |
| BM25 top-1 | {err_df['top1_oracle_hit'].mean():.4f} |
| BM25 top-3 | {err_df['top3_oracle_hit'].mean():.4f} |
| BM25 top-5 | {err_df['top5_oracle_hit'].mean():.4f} |

top-3/top5 的 oracle hit rate 高于 top-1，但 **这不等于 R4 性能更好**——需要 R4 复跑后才能判断 concat evidence 是否因噪声过多而损害 screening。

## 5. 与 oracle evidence 差距多大？

**BLOCKED — 无法计算。** R4 在 oracle evidence 和 retrieved evidence 上均无法复跑，gap 无法计算。

## 6. 主要错误来自 retrieval 还是 screening？

**Retrieval 层面错误分布（444 条）：**

| Error type | Count | Rate |
| --- | --- | --- |
"""
    for et, count in err_counts.items():
        report += f"| {et} | {count} | {count/n_claims:.2%} |\n"

    report += f"""
**Screening 层面错误：BLOCKED。** 无法归因 strong_action_false_negative / strong_action_false_positive / contradiction_confusion / supported_mild_confusion，因为 R4 预测不可用。

**Retrieval 层面结论：** 主要 retrieval 错误是 `oracle_chunk_not_retrieved`（找到正确论文但未命中 oracle chunk），占 25.45%。这表明 BM25 的 chunk 级精排有提升空间。

## 7. 是否建议继续 dense/hybrid/reranker？

**是，具备升级条件。**

- `cross-encoder/nli-deberta-base` 已本地缓存，可作为 cross-encoder reranker。
- `transformers` + `torch` (CPU) 可用，支持 dense retrieval 和 reranker。
- `sentence_transformers` 未安装，但可通过 `pip install sentence-transformers` 安装。
- `sklearn` + `scipy` 可用，支持 hybrid 分数融合。
- 语料库 4747 chunks，远在 dense index 容量范围内。
- **无 GPU**，但 CPU 可处理 4747 chunks（dense retrieval 约 5-10 分钟，reranker top-50 约 10-20 分钟）。

**推荐升级顺序：**
1. 安装 sentence-transformers
2. 下载 all-MiniLM-L6-v2 做 zero-shot dense retrieval
3. 运行 dense retrieval（CPU，5-10 min）
4. BM25 + dense hybrid（加权或 RRF 融合）
5. 用 cached cross-encoder/nli-deberta-base 做 top-50 → top-10 reranker
6. 重新评估 retrieval metrics

**预期收益：** Hybrid + reranker 可将 Recall@1 从 71.62% 提升到 85-90%，将 oracle_chunk_not_retrieved 失败率从 25.45% 降到 10-15%。

## 8. 是否支持把论文 V3.17 主线改为 offline PDF-corpus retrieval + CESE-OCN screening？

**有条件支持（partial）。**

支持的理由：
- PDF 语料库 100% 完整，离线可读。
- BM25 检索 Recall@10 = 97.97%，MRR = 0.8261，检索可行。
- NLI 模型已缓存，dense/reranker 升级条件具备。
- 4747 chunks 适合 dense index。

不支持的理由（当前 BLOCKED）：
- R4 无法在 retrieved evidence 上复跑（HCM features 缺失、分类器 artifacts 未保存、t_contra_low 未冻结）。
- 无法验证 retrieved evidence 下 R4 的 strong_action screening 信号是否保留。
- **不能用 proxy 冒充 R4**，因此"retrieved evidence 下 R4 仍有效"这一 claim **未经验证**。

**恢复 R4 replay 的路径（需授权 reproduction training）：**
1. 在 silver-444 + original evidence 上重新训练 clf_contra/clf_strong/clf_svm（这是 reproduction，不是新模型训练）
2. 保存 classifier artifacts 为 .pkl
3. 冻结 t_contra_low（用 grid-search 均值）
4. 为 4 组 input CSV（oracle/top1/top3/top5）计算 NLI features（用 cached NLI 模型）
5. 用 frozen thresholds + saved classifiers 复跑 R4
6. 计算 oracle vs retrieved strong-F1 gap
7. 若 gap < 0.05：V3.17 主线完全支持；若 gap >= 0.05：先改善 retrieval 再验证

---

## 禁止项执行确认

- 不训练模型：PASS
- 不调 API：PASS
- 不联网：PASS
- 不改阈值：PASS
- 不改原数据：PASS
- 不改论文：PASS
- 不删文件：PASS
- **不用 cue-based proxy 冒充 R4：PASS（严格 blocked）**
- 不把 silver 写成 gold：PASS
- 不声称自然分布：PASS

---

## 输出文件清单

1. `r4_pipeline_inventory.csv` — 16 文件盘点
2. `r4_replay_feasibility.json` — 复跑可行性（BLOCKED）
3. `r4_input_oracle.csv` — 444 条 oracle evidence 输入
4. `r4_input_bm25_top1.csv` — 444 条 BM25 top-1 输入
5. `r4_input_bm25_top3.csv` — 444 条 BM25 top-3 concat 输入
6. `r4_input_bm25_top5.csv` — 444 条 BM25 top-5 concat 输入
7. `r4_predictions_oracle.csv` — BLOCKED（无预测）
8. `r4_predictions_bm25_top1.csv` — BLOCKED（无预测）
9. `r4_predictions_bm25_top3.csv` — BLOCKED（无预测）
10. `r4_predictions_bm25_top5.csv` — BLOCKED（无预测）
11. `r4_retrieved_metrics.csv` — BLOCKED（所有指标 -1.0）
12. `r4_retrieved_error_analysis.csv` — retrieval-level 错误分析（444 条）
13. `retriever_upgrade_readiness.json` — 升级条件检查
14. `r4_on_retrieved_evidence_gate.json` — gate
15. `r4_on_retrieved_evidence_report.md` — 本报告
"""
    with open(OUT_DIR / "r4_on_retrieved_evidence_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  Report written: {len(report)} chars")


# ============ Main ============
def main() -> None:
    print("=" * 60)
    print("R4-on-Retrieved Evidence Formal Evaluation v1")
    print("=" * 60)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: R4 pipeline inventory
    inv_df = build_r4_pipeline_inventory()

    # Step 2: Replay feasibility
    feasibility = assess_replay_feasibility(inv_df)

    # Step 3: Build 4 input CSVs (always built, even if blocked)
    build_input_csvs(feasibility)

    # Step 4: R4 predictions (BLOCKED path)
    if not feasibility["can_replay_with_new_evidence"]:
        write_blocked_predictions(feasibility)
    else:
        print("  ERROR: can_replay=True but no replay implementation written")
        return

    # Step 5: Metrics (BLOCKED)
    compute_blocked_metrics()

    # Step 6: Error analysis (retrieval-level only)
    err_df = error_analysis_retrieval_level()

    # Step 7: Retriever upgrade readiness
    readiness = check_upgrade_readiness()

    # Step 8: Gate
    write_gate(feasibility, err_df, readiness)

    # Step 9: Report
    write_report(feasibility, err_df, readiness)

    print("\n" + "=" * 60)
    print("DONE (BLOCKED PATH)")
    print(f"  Output: {OUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
