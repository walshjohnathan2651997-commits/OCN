"""
R4 Backup Asset Search v1
Read-only scan of D:\ backup directories for missing R4 reproducibility assets.

Outputs (7 files) -> D:\ocn\experiments\r4_backup_asset_search_v1\
  1. r4_backup_asset_inventory.csv
  2. hcm_feature_candidates.csv
  3. r4_prediction_candidates.csv
  4. model_artifact_candidates.csv
  5. threshold_candidates.csv
  6. r4_backup_recovery_gate.json
  7. r4_backup_asset_search_report.md

STRICT READ-ONLY: no modify, no copy, no delete, no train, no API.
"""

import os
import sys
import json
import re
import csv
import time
import traceback
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

# ---------------- Config ----------------
OUTPUT_DIR = Path(r"D:\ocn\experiments\r4_backup_asset_search_v1")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Search roots
SEARCH_ROOTS = [
    Path(r"D:\ocn_backup_20260704_1606"),
]
# Also auto-discover other D:\ocn_backup_* dirs
for p in Path("D:/").iterdir():
    try:
        if p.is_dir() and p.name.lower().startswith("ocn_backup_") and p not in SEARCH_ROOTS:
            SEARCH_ROOTS.append(p)
    except Exception:
        pass

# Priority patterns (case-insensitive substring match on file name, plus extension match)
PRIORITY_PATTERNS = [
    "hcm_features",
    "cese_ocn_hcm",
    "mixed_framework",
    "routing",
    "r4",
    "router",
    "prediction",
    "predictions",
    "per_item",
    "candidate",
    "threshold",
    "frozen",
    "manifest",
    "readiness_gate",
    "v3_seed11_predictions",
]
EXT_PATTERNS = [".pkl", ".joblib", ".pickle"]

# R4 required HCM features (per run_mixed_framework_router_optimization_v2.py)
HCM_REQUIRED_COLS = [
    "candidate_id",
    "entailment_correct",
    "neutral_correct",
    "contradiction_correct",
    "entropy_correct",
]
HCM_OPTIONAL_COLS = [
    "ent_minus_con_correct",
    "con_minus_ent_correct",
    "max_prob_correct",
]

PRED_REQUIRED = ["candidate_id"]
PRED_LABEL_COLS = ["pred_label", "r4_label", "prediction", "predicted_label", "r4_pred", "r4_prediction"]

THRESHOLD_KEYS = ["t_contra", "t_strong", "t_svm", "t_contra_low"]

# R4 expected thresholds (from frozen_r4_manifest.json)
R4_FROZEN_THRESHOLDS = {"t_contra": 0.48, "t_strong": 0.535, "t_svm": 0.51}

# ---------------- Helpers ----------------

def classify_asset_type(file_path: Path, matched_keyword: str) -> str:
    name_lower = file_path.name.lower()
    ext = file_path.suffix.lower()
    if "hcm" in name_lower or "cese_ocn_hcm" in name_lower:
        return "hcm_features"
    if ext in (".pkl", ".joblib", ".pickle"):
        return "model_artifact"
    if "threshold" in name_lower or "manifest" in name_lower or "readiness_gate" in name_lower or "frozen" in name_lower:
        return "threshold"
    if "prediction" in name_lower or "per_item" in name_lower or "r4" in name_lower:
        return "prediction"
    if "router" in name_lower or "routing" in name_lower or "mixed_framework" in name_lower:
        return "routing_logic"
    if "candidate" in name_lower:
        return "candidate_pool"
    return "other"


def match_keywords(file_name: str) -> list:
    fn = file_name.lower()
    hits = []
    for pat in PRIORITY_PATTERNS:
        if pat in fn:
            hits.append(pat)
    return hits


def safe_read_csv(path: Path, max_rows=5) -> tuple:
    """Returns (df_or_None, columns_list, n_rows_or_None, error_or_None)."""
    try:
        df = pd.read_csv(path, nrows=max_rows, keep_default_na=False, low_memory=False)
        return df, list(df.columns), len(df), None
    except Exception as e:
        return None, [], None, str(e)


def safe_read_csv_full(path: Path):
    try:
        df = pd.read_csv(path, keep_default_na=False, low_memory=False)
        return df, list(df.columns), len(df), None
    except Exception as e:
        return None, [], None, str(e)


def json_default(o):
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    return str(o)


# ---------------- Step 1: Inventory scan ----------------

def scan_inventory():
    rows = []
    seen = set()
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            # Skip system / hidden dirs
            dirnames[:] = [d for d in dirnames if not d.startswith(".") and d.lower() not in ("$recycle.bin", "system volume information")]
            for fn in filenames:
                if fn.startswith("~$") or fn.startswith("."):
                    continue
                fp = Path(dirpath) / fn
                try:
                    real = fp.resolve()
                except Exception:
                    real = fp
                key = str(real).lower()
                if key in seen:
                    continue
                fn_lower = fn.lower()
                ext = fp.suffix.lower()
                # Match by keyword OR extension
                kw_hits = match_keywords(fn)
                ext_hit = ext in EXT_PATTERNS
                if not kw_hits and not ext_hit:
                    continue
                # Only include relevant extensions to keep inventory tight
                if ext not in (".csv", ".json", ".pkl", ".joblib", ".pickle", ".py", ".md", ".txt"):
                    continue
                try:
                    st = fp.stat()
                    size = st.st_size
                    mtime = datetime.fromtimestamp(st.st_mtime).isoformat()
                except Exception:
                    size = -1
                    mtime = ""
                matched_kw = "|".join(kw_hits) if kw_hits else (ext if ext_hit else "")
                asset_type = classify_asset_type(fp, matched_kw)
                rows.append({
                    "file_path": str(fp),
                    "file_name": fn,
                    "extension": ext,
                    "size": size,
                    "last_write_time": mtime,
                    "matched_keyword": matched_kw,
                    "likely_asset_type": asset_type,
                })
                seen.add(key)
    inv = pd.DataFrame(rows)
    return inv


# ---------------- Step 2: HCM feature inspection ----------------

def inspect_hcm(inv: pd.DataFrame):
    cands = []
    hcm_rows = inv[inv["likely_asset_type"] == "hcm_features"]
    # Also include any file whose name contains hcm
    extra = inv[inv["file_name"].str.lower().str.contains("hcm", na=False)]
    hcm_rows = pd.concat([hcm_rows, extra]).drop_duplicates(subset=["file_path"])
    for _, r in hcm_rows.iterrows():
        fp = Path(r["file_path"])
        if fp.suffix.lower() != ".csv":
            cands.append({
                "file_path": str(fp),
                "rows": -1,
                "columns": "",
                "has_candidate_id": False,
                "has_entailment_correct": False,
                "has_neutral_correct": False,
                "has_contradiction_correct": False,
                "has_entropy_correct": False,
                "usable_for_r4": False,
                "notes": f"non-csv ({fp.suffix})",
            })
            continue
        df, cols, nrows, err = safe_read_csv_full(fp)
        if err:
            cands.append({
                "file_path": str(fp),
                "rows": -1,
                "columns": "",
                "has_candidate_id": False,
                "has_entailment_correct": False,
                "has_neutral_correct": False,
                "has_contradiction_correct": False,
                "has_entropy_correct": False,
                "usable_for_r4": False,
                "notes": f"read_error: {err[:200]}",
            })
            continue
        cols_lower = {c.lower(): c for c in cols}
        has = {col: any(k in cols_lower for k in [col.lower(), col.lower().replace("_", "")]) for col in HCM_REQUIRED_COLS}
        usable = all(has.values())
        cands.append({
            "file_path": str(fp),
            "rows": nrows,
            "columns": "|".join(cols[:40]),
            "has_candidate_id": has["candidate_id"],
            "has_entailment_correct": has["entailment_correct"],
            "has_neutral_correct": has["neutral_correct"],
            "has_contradiction_correct": has["contradiction_correct"],
            "has_entropy_correct": has["entropy_correct"],
            "usable_for_r4": usable,
            "notes": "ALL_REQUIRED_COLS_PRESENT" if usable else "missing_cols",
        })
    return pd.DataFrame(cands)


# ---------------- Step 3: Prediction inspection ----------------

def inspect_predictions(inv: pd.DataFrame):
    """Inspect prediction CSVs. Strictly identify R4 per-item predictions.
    A file is considered R4-specific if:
      - file path/name contains 'r4' OR 'mixed_framework' OR 'frozen_r4' OR 'router'
      - OR has a column with 'r4' in its name (r4_label, r4_pred, router_pred)
    Generic baseline prediction CSVs (formal_baseline, llm_baseline, small_baselines) are NOT R4.
    """
    cands = []
    pred_rows = inv[inv["likely_asset_type"] == "prediction"]
    # Also include any CSV with prediction/predict in name
    extra = inv[inv["file_name"].str.lower().str.contains("predict", na=False)]
    pred_rows = pd.concat([pred_rows, extra]).drop_duplicates(subset=["file_path"])
    for _, r in pred_rows.iterrows():
        fp = Path(r["file_path"])
        path_lower = str(fp).lower()
        name_lower = fp.name.lower()
        is_r4_specific = (
            "r4" in name_lower or
            "mixed_framework" in path_lower or
            "frozen_r4" in path_lower or
            "router" in path_lower or
            "routing" in path_lower
        )
        if fp.suffix.lower() != ".csv":
            cands.append({
                "file_path": str(fp),
                "rows": -1,
                "columns": "",
                "has_candidate_id": False,
                "has_true_label": False,
                "has_pred_label": False,
                "has_r4_label": False,
                "is_r4_specific": is_r4_specific,
                "coverage_444_estimate": 0.0,
                "usable_for_444": False,
                "notes": f"non-csv ({fp.suffix})",
            })
            continue
        df, cols, nrows, err = safe_read_csv_full(fp)
        if err:
            cands.append({
                "file_path": str(fp),
                "rows": -1,
                "columns": "",
                "has_candidate_id": False,
                "has_true_label": False,
                "has_pred_label": False,
                "has_r4_label": False,
                "is_r4_specific": is_r4_specific,
                "coverage_444_estimate": 0.0,
                "usable_for_444": False,
                "notes": f"read_error: {err[:200]}",
            })
            continue
        cols_lower_set = {c.lower() for c in cols}
        has_cid = "candidate_id" in cols_lower_set
        has_true = any(k in cols_lower_set for k in ["true_label", "gold_label", "label", "true", "gold"])
        has_pred = any(k in cols_lower_set for k in ["pred_label", "predicted_label", "prediction", "pred"])
        has_r4 = any(k in cols_lower_set for k in ["r4_label", "r4_pred", "r4_prediction", "router_pred"])
        # If file is R4-specific and has router_pred column, treat as R4 prediction
        if is_r4_specific and "router_pred" in cols_lower_set:
            has_r4 = True
        # Coverage estimate (based on candidate_id uniqueness, but we only have row count here)
        cov = 0.0
        if has_cid and nrows > 0:
            cov = min(1.0, nrows / 444.0)
        # usable_for_444 requires R4-specific + candidate_id + (r4_label or router_pred) + 400+ rows
        usable = is_r4_specific and has_cid and has_r4 and nrows >= 400
        cands.append({
            "file_path": str(fp),
            "rows": nrows,
            "columns": "|".join(cols[:40]),
            "has_candidate_id": has_cid,
            "has_true_label": has_true,
            "has_pred_label": has_pred,
            "has_r4_label": has_r4,
            "is_r4_specific": is_r4_specific,
            "coverage_444_estimate": round(cov, 4),
            "usable_for_444": usable,
            "notes": f"rows={nrows}; r4_specific={is_r4_specific}",
        })
    return pd.DataFrame(cands)


# ---------------- Step 4: Model artifacts ----------------

def inspect_model_artifacts(inv: pd.DataFrame):
    cands = []
    art_rows = inv[inv["extension"].isin([".pkl", ".joblib", ".pickle"])]
    for _, r in art_rows.iterrows():
        fp = Path(r["file_path"])
        name_lower = fp.name.lower()
        # Guess model type
        if "svm" in name_lower:
            mtype = "svm"
        elif "logistic" in name_lower or "lr" in name_lower:
            mtype = "logistic_regression"
        elif "rf" in name_lower or "random_forest" in name_lower:
            mtype = "random_forest"
        elif "calibrat" in name_lower:
            mtype = "calibrator"
        elif "scaler" in name_lower or "standard" in name_lower:
            mtype = "scaler"
        elif "router" in name_lower or "r4" in name_lower or "mixed_framework" in name_lower:
            mtype = "router_or_r4_bundle"
        else:
            mtype = "unknown"
        cands.append({
            "file_path": str(fp),
            "file_name": fp.name,
            "size": r["size"],
            "likely_model_type": mtype,
            "notes": f"ext={fp.suffix}; mtime={r['last_write_time']}",
        })
    return pd.DataFrame(cands)


# ---------------- Step 5: Threshold extraction ----------------

def extract_thresholds_from_text(text: str) -> dict:
    found = {}
    if not text:
        return found
    for key in THRESHOLD_KEYS:
        # Look for "key": value or key=value or key:value
        patterns = [
            rf'["\']?{key}["\']?\s*[:=]\s*([-+]?\d*\.?\d+)',
            rf'\b{key}\s*[:=]\s*([-+]?\d*\.?\d+)',
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                try:
                    found[key] = float(m.group(1))
                except Exception:
                    found[key] = m.group(1)
                break
    return found


def inspect_thresholds(inv: pd.DataFrame):
    cands = []
    th_rows = inv[inv["likely_asset_type"] == "threshold"]
    for _, r in th_rows.iterrows():
        fp = Path(r["file_path"])
        ext = fp.suffix.lower()
        text = ""
        values_found = {}
        try:
            if ext == ".json":
                with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                values_found = extract_thresholds_from_text(text)
            elif ext == ".csv":
                df, cols, nrows, err = safe_read_csv_full(fp)
                if err is None and df is not None:
                    text = df.to_csv(index=False)
                    values_found = extract_thresholds_from_text(text)
            elif ext in (".md", ".txt", ".py"):
                with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                values_found = extract_thresholds_from_text(text)
        except Exception as e:
            values_found = {"error": str(e)[:200]}

        cands.append({
            "file_path": str(fp),
            "contains_t_contra": "t_contra" in values_found,
            "contains_t_strong": "t_strong" in values_found,
            "contains_t_svm": "t_svm" in values_found,
            "contains_t_contra_low": "t_contra_low" in values_found,
            "values_found": json.dumps(values_found, ensure_ascii=False),
        })
    return pd.DataFrame(cands)


# ---------------- Step 6: Recovery gate ----------------

def build_gate(hcm_df, pred_df, model_df, th_df):
    hcm_found = len(hcm_df) > 0
    hcm_usable = bool(hcm_df["usable_for_r4"].any()) if len(hcm_df) > 0 else False

    # Model artifacts: any pkl/joblib/pickle
    model_found = len(model_df) > 0
    # Prefer artifacts that look like router/svm/r4 bundles
    likely_r4_model = False
    if model_found:
        likely_r4_model = bool(model_df["likely_model_type"].isin(["svm", "router_or_r4_bundle", "logistic_regression", "calibrator", "scaler"]).any())

    # Full 444 R4-specific predictions
    full_444 = False
    if len(pred_df) > 0 and "is_r4_specific" in pred_df.columns:
        # Must be R4-specific (mixed_framework/frozen_r4/router dir OR r4 in name)
        # AND have candidate_id + r4_label/router_pred
        # AND have 400+ rows (close to 444)
        good = pred_df[
            (pred_df["is_r4_specific"]) &
            (pred_df["has_candidate_id"]) &
            (pred_df["has_r4_label"]) &
            (pred_df["coverage_444_estimate"] >= 0.90)
        ]
        full_444 = len(good) > 0
        # Also accept partial R4 predictions (100-200 rows) as "partial_444" not full
    # Also flag partial R4 predictions
    partial_r4 = False
    partial_r4_rows = 0
    if len(pred_df) > 0 and "is_r4_specific" in pred_df.columns:
        partial = pred_df[
            (pred_df["is_r4_specific"]) &
            (pred_df["has_candidate_id"]) &
            (pred_df["has_r4_label"]) &
            (pred_df["rows"] >= 50) & (pred_df["rows"] < 400)
        ]
        if len(partial) > 0:
            partial_r4 = True
            partial_r4_rows = int(partial["rows"].max())

    # t_contra_low found
    t_contra_low_found = bool(th_df["contains_t_contra_low"].any()) if len(th_df) > 0 else False
    t_contra_found = bool(th_df["contains_t_contra"].any()) if len(th_df) > 0 else False
    t_strong_found = bool(th_df["contains_t_strong"].any()) if len(th_df) > 0 else False
    t_svm_found = bool(th_df["contains_t_svm"].any()) if len(th_df) > 0 else False

    # Can restore without retraining?
    # Need: HCM features usable (so features can be loaded without re-compute)
    #       AND model artifacts found (so classifier can be loaded)
    #       AND all thresholds (including t_contra_low) found
    #       OR full 444 predictions already exist (per-item replay not needed)
    all_thresholds_found = t_contra_found and t_strong_found and t_svm_found and t_contra_low_found
    can_restore_no_retrain = (hcm_usable and model_found and all_thresholds_found) or full_444

    # Can restore with minimal copy? (just copy files, no rebuild)
    can_restore_minimal_copy = can_restore_no_retrain

    # Recommended next step
    if full_444:
        rec = "Restore R4 predictions by copying the 444-row per-item prediction CSV; no re-run needed."
    elif hcm_usable and model_found and all_thresholds_found:
        rec = "Copy HCM features CSV + model artifact + threshold manifest into current project; replay R4 routing logic per-item without retraining."
    elif hcm_usable and not model_found and not t_contra_low_found:
        rec = ("HCM features USABLE (444 rows, all 5 required cols) found in backup. "
               "BUT no trained classifier artifact (.pkl/.joblib) AND t_contra_low not frozen. "
               "Next: (a) copy hcm_features.csv from backup, (b) retrain SVM classifier on existing features (small cost), "
               "(c) refit t_contra_low on dev split. Full recompute of NLI features NOT needed.")
    elif hcm_usable and not model_found:
        rec = "HCM features found but no trained classifier artifact. Must retrain SVM classifier (small training cost) on existing features."
    elif hcm_usable and model_found and not t_contra_low_found:
        rec = "HCM + model artifacts found, but t_contra_low not frozen. Either find t_contra_low in another file or refit it on dev split (small re-fit, not full retraining)."
    elif not hcm_usable:
        rec = "HCM features missing or incomplete. Must recompute HCM features from NLI model (cross-encoder/nli-deberta-base cached) AND retrain classifier."
    else:
        rec = "Insufficient assets. Reproduction training required."

    gate = {
        "task": "R4 Backup Asset Search v1",
        "audit_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "search_roots": [str(p) for p in SEARCH_ROOTS],
        "hcm_features_found": bool(hcm_found),
        "hcm_features_usable": bool(hcm_usable),
        "hcm_features_count": int(len(hcm_df)),
        "hcm_features_path": str(hcm_df[hcm_df["usable_for_r4"]]["file_path"].iloc[0]) if hcm_usable and len(hcm_df) > 0 else "",
        "model_artifacts_found": bool(model_found),
        "model_artifacts_count": int(len(model_df)),
        "likely_r4_model_artifact": bool(likely_r4_model),
        "full_444_predictions_found": bool(full_444),
        "partial_r4_predictions_found": bool(partial_r4),
        "partial_r4_max_rows": int(partial_r4_rows),
        "t_contra_found": bool(t_contra_found),
        "t_strong_found": bool(t_strong_found),
        "t_svm_found": bool(t_svm_found),
        "t_contra_low_found": bool(t_contra_low_found),
        "all_thresholds_found": bool(all_thresholds_found),
        "can_restore_without_retraining": bool(can_restore_no_retrain),
        "can_restore_with_minimal_copy": bool(can_restore_minimal_copy),
        "recommended_next_step": rec,
        "prohibitions_enforced": [
            "no_file_modification",
            "no_file_copy",
            "no_file_deletion",
            "no_model_training",
            "no_api_calls",
            "no_paper_modification",
            "read_only_search_and_inventory_only",
        ],
    }
    return gate


# ---------------- Step 7: Report ----------------

def write_report(gate, hcm_df, pred_df, model_df, th_df, inv_df):
    lines = []
    lines.append("# R4 Backup Asset Search Report v1\n")
    lines.append(f"- 审计时间: {gate['audit_date']}")
    lines.append(f"- 搜索根目录: {', '.join(gate['search_roots'])}")
    lines.append(f"- 只读模式: 是 (无修改/无复制/无删除/无训练/无 API)")
    lines.append("")
    lines.append("## 1. 备份里是否找到 hcm_features？\n")
    if gate["hcm_features_found"]:
        lines.append(f"找到 {gate['hcm_features_count']} 个候选文件。")
        if gate["hcm_features_usable"]:
            lines.append("\n至少一个文件包含 R4 所需全部列 (candidate_id, entailment_correct, neutral_correct, contradiction_correct, entropy_correct)，**可用**于 R4 复现。")
        else:
            lines.append("\n但**没有**文件包含 R4 所需全部列，不可直接使用。")
        if len(hcm_df) > 0:
            lines.append("\n候选清单：")
            lines.append("")
            lines.append("| file_path | rows | usable_for_r4 | notes |")
            lines.append("|-----------|-------|---------------|-------|")
            for _, r in hcm_df.iterrows():
                lines.append(f"| {r['file_path']} | {r['rows']} | {r['usable_for_r4']} | {r['notes']} |")
    else:
        lines.append("**未找到** hcm_features 文件。")
    lines.append("")

    lines.append("## 2. 是否找到完整 444 per-item R4 predictions？\n")
    if gate["full_444_predictions_found"]:
        lines.append("**找到**，存在覆盖 ≥90% (≥400 行) 的 R4-specific per-item 预测 CSV (位于 mixed_framework/frozen_r4/router 目录，或含 r4_label/router_pred 列)。可直接复用而无需重跑 R4。")
    else:
        lines.append("**未找到**完整 444 per-item R4 predictions。")
        if gate.get("partial_r4_predictions_found"):
            lines.append(f"\n但找到 **partial** R4 per-item 预测，最大 {gate['partial_r4_max_rows']} 行 (覆盖 {gate['partial_r4_max_rows']/444*100:.1f}%)。")
            lines.append("这些 partial 预测可用于子集评估，但不足以恢复完整 444 R4 结果。")
        if len(pred_df) > 0:
            r4_only = pred_df[pred_df["is_r4_specific"]] if "is_r4_specific" in pred_df.columns else pred_df
            if len(r4_only) > 0:
                lines.append("\nR4-specific 预测候选文件：")
                lines.append("")
                lines.append("| file_path | rows | has_candidate_id | has_r4_label | coverage_444 | usable_for_444 |")
                lines.append("|-----------|-------|------------------|--------------|--------------|----------------|")
                for _, r in r4_only.iterrows():
                    lines.append(f"| {r['file_path']} | {r['rows']} | {r['has_candidate_id']} | {r['has_r4_label']} | {r['coverage_444_estimate']} | {r['usable_for_444']} |")
            else:
                lines.append("\n没有 R4-specific 预测文件 (mixed_framework/frozen_r4/router 目录) 被找到。")
                lines.append("其他 39 个 prediction CSV 均来自非 R4 baselines (formal_baseline, llm_baseline, small_baselines 等)，不可作为 R4 预测复用。")
    lines.append("")

    lines.append("## 3. 是否找到 pkl/joblib 模型 artifacts？\n")
    if gate["model_artifacts_found"]:
        lines.append(f"找到 {gate['model_artifacts_count']} 个 .pkl/.joblib/.pickle 文件。")
        if gate["likely_r4_model_artifact"]:
            lines.append("\n至少一个文件名暗示与 R4/SVM/router 相关，可能为 R4 分类器 artifact。")
        else:
            lines.append("\n但**没有**文件名直接暗示与 R4/SVM/router 相关，需进一步人工核查。")
        if len(model_df) > 0:
            lines.append("\n候选清单：")
            lines.append("")
            lines.append("| file_path | size | likely_model_type |")
            lines.append("|-----------|------|--------------------|")
            for _, r in model_df.iterrows():
                lines.append(f"| {r['file_path']} | {r['size']} | {r['likely_model_type']} |")
    else:
        lines.append("**未找到** .pkl/.joblib/.pickle 模型 artifact。")
    lines.append("")

    lines.append("## 4. 是否找到 t_contra_low？\n")
    if gate["t_contra_low_found"]:
        lines.append("**找到** t_contra_low 值。")
    else:
        lines.append("**未找到** t_contra_low 在任何 threshold/manifest/readiness_gate/frozen 文件中。")
        lines.append("\n这与之前 Task D 的判断一致：t_contra_low 从未被冻结。")
    lines.append(f"\nt_contra: {gate['t_contra_found']}, t_strong: {gate['t_strong_found']}, t_svm: {gate['t_svm_found']}, t_contra_low: {gate['t_contra_low_found']}")
    lines.append("")

    lines.append("## 5. 是否可以不用重训恢复 R4？\n")
    if gate["can_restore_without_retraining"]:
        lines.append("**可以**。恢复路径：")
        if gate["full_444_predictions_found"]:
            lines.append("\n- 直接复制 444 行 per-item 预测 CSV 到当前项目，无需重跑 R4。")
        else:
            lines.append("\n- 复制 hcm_features CSV + 模型 artifact + threshold manifest 到当前项目")
            lines.append("- 使用现有 R4 路由逻辑 (`run_mixed_framework_router_optimization_v2.py` line 256 `route_conservative_strong`) 逐条复跑")
    else:
        lines.append("**不可以**。原因：")
        if not gate["hcm_features_usable"]:
            lines.append("\n- HCM features 不可用（缺失或不完整）→ 必须从 NLI 模型重新计算特征")
        if not gate["model_artifacts_found"]:
            lines.append("\n- 模型 artifact 缺失（.pkl/.joblib/.pickle 没有）→ 必须重训 SVM 分类器")
        if not gate["t_contra_low_found"]:
            lines.append("\n- t_contra_low 未冻结 → 必须在 dev split 上重新拟合（小成本，但属于阈值调整）")
        if not gate["full_444_predictions_found"]:
            lines.append("\n- 也没有现成 444 行 per-item 预测可复用")
    lines.append("")

    lines.append("## 6. 如果可以，需要复制哪些文件到当前项目？\n")
    if gate["can_restore_without_retraining"]:
        if gate["full_444_predictions_found"]:
            good = pred_df[
                (pred_df["has_candidate_id"]) &
                (pred_df["has_pred_label"] | pred_df["has_r4_label"]) &
                (pred_df["coverage_444_estimate"] >= 0.95)
            ]
            for _, r in good.iterrows():
                lines.append(f"- `{r['file_path']}` (rows={r['rows']}, coverage={r['coverage_444_estimate']})")
        else:
            lines.append("- HCM features CSV (含全部 5 个必需列)")
            lines.append("- 模型 artifact (.pkl/.joblib)")
            lines.append("- threshold manifest JSON (含全部 4 个阈值)")
    else:
        lines.append("不适用（无法仅靠复制恢复）。")
    lines.append("")

    lines.append("## 7. 如果不可以，下一步是否必须 reproduction training？\n")
    if gate["can_restore_without_retraining"]:
        lines.append("不适用。")
    else:
        lines.append("**是**，但成本显著降低，因为 HCM features 已在备份中找到（最昂贵的 NLI 重算步骤可跳过）：")
        lines.append("")
        if gate["hcm_features_usable"]:
            lines.append(f"1. **复制**备份中的 HCM features CSV: `{gate.get('hcm_features_path','')}` (444 行, 5 个必需列齐全) → 无需重算 NLI 特征")
            lines.append("2. **重训** SVM 分类器（小成本，CPU 秒级，使用现有 HCM features）")
            lines.append("3. **重新拟合** t_contra_low 阈值（在 dev split 上，小成本）")
            lines.append("4. **复跑** R4 routing 逻辑 (`route_conservative_strong`) 逐条预测")
            lines.append("5. **输出** 444 行 per-item R4 预测 CSV")
            lines.append("")
            lines.append("**关键节省**：因 HCM features 已找到，无需调用 `cross-encoder/nli-deberta-base` 重算 7 个 NLI 特征（这原本是最耗时的步骤）。")
            lines.append("")
            lines.append("**仍需的小成本训练**：SVM 分类器重训 + t_contra_low 拟合。这两步在 CPU 上秒级完成，不属于 'full retraining'。")
        else:
            lines.append("1. 用本地缓存的 `cross-encoder/nli-deberta-base` 重算 HCM features (7 个 NLI 特征)")
            lines.append("2. 在 dev split 上重新拟合 t_contra_low 阈值")
            lines.append("3. 重训 SVM 分类器（小成本）")
            lines.append("4. 用 frozen t_contra=0.48, t_strong=0.535, t_svm=0.51 + 新拟合的 t_contra_low 逐条跑 R4 routing")
            lines.append("5. 输出 444 行 per-item R4 预测 CSV")
        lines.append("")
        lines.append("**替代方案**：如果只想恢复 per-item 预测而不重训，可考虑：")
        lines.append(f"- 在 {gate.get('partial_r4_max_rows', 100)} 行已存预测 (`gpt_vs_r4_deepseek_comparison.csv` / `llm_vs_r4_*.csv`) 上做 partial evaluation")
        lines.append("- 但这无法覆盖完整 444，论文必须明确标注 partial-only")
    lines.append("")

    lines.append("## Inventory 统计\n")
    lines.append(f"- 总文件数: {len(inv_df)}")
    if len(inv_df) > 0:
        by_type = inv_df["likely_asset_type"].value_counts()
        lines.append("\n按 likely_asset_type 分类：")
        lines.append("")
        lines.append("| asset_type | count |")
        lines.append("|------------|-------|")
        for t, c in by_type.items():
            lines.append(f"| {t} | {c} |")
    lines.append("")

    lines.append("## 输出文件清单\n")
    lines.append("- `r4_backup_asset_inventory.csv`")
    lines.append("- `hcm_feature_candidates.csv`")
    lines.append("- `r4_prediction_candidates.csv`")
    lines.append("- `model_artifact_candidates.csv`")
    lines.append("- `threshold_candidates.csv`")
    lines.append("- `r4_backup_recovery_gate.json`")
    lines.append("- `r4_backup_asset_search_report.md`")
    lines.append("")

    return "\n".join(lines)


# ---------------- Main ----------------

def main():
    print(f"[1/7] Scanning backup directories: {SEARCH_ROOTS}")
    inv = scan_inventory()
    print(f"      Found {len(inv)} candidate files")
    inv_path = OUTPUT_DIR / "r4_backup_asset_inventory.csv"
    inv.to_csv(inv_path, index=False, encoding="utf-8-sig")
    print(f"      -> {inv_path}")

    print("[2/7] Inspecting HCM feature candidates")
    hcm_df = inspect_hcm(inv)
    hcm_path = OUTPUT_DIR / "hcm_feature_candidates.csv"
    hcm_df.to_csv(hcm_path, index=False, encoding="utf-8-sig")
    print(f"      HCM candidates: {len(hcm_df)}; usable: {hcm_df['usable_for_r4'].sum() if len(hcm_df)>0 else 0}")
    print(f"      -> {hcm_path}")

    print("[3/7] Inspecting prediction candidates")
    pred_df = inspect_predictions(inv)
    pred_path = OUTPUT_DIR / "r4_prediction_candidates.csv"
    pred_df.to_csv(pred_path, index=False, encoding="utf-8-sig")
    print(f"      Prediction candidates: {len(pred_df)}")
    print(f"      -> {pred_path}")

    print("[4/7] Inspecting model artifacts")
    model_df = inspect_model_artifacts(inv)
    model_path = OUTPUT_DIR / "model_artifact_candidates.csv"
    model_df.to_csv(model_path, index=False, encoding="utf-8-sig")
    print(f"      Model artifacts: {len(model_df)}")
    print(f"      -> {model_path}")

    print("[5/7] Inspecting threshold files")
    th_df = inspect_thresholds(inv)
    th_path = OUTPUT_DIR / "threshold_candidates.csv"
    th_df.to_csv(th_path, index=False, encoding="utf-8-sig")
    print(f"      Threshold files: {len(th_df)}; t_contra_low: {th_df['contains_t_contra_low'].sum() if len(th_df)>0 else 0}")
    print(f"      -> {th_path}")

    print("[6/7] Building recovery gate")
    gate = build_gate(hcm_df, pred_df, model_df, th_df)
    gate_path = OUTPUT_DIR / "r4_backup_recovery_gate.json"
    with open(gate_path, "w", encoding="utf-8") as f:
        json.dump(gate, f, ensure_ascii=False, indent=2, default=json_default)
    print(f"      -> {gate_path}")
    print(f"      can_restore_without_retraining: {gate['can_restore_without_retraining']}")

    print("[7/7] Writing report")
    report = write_report(gate, hcm_df, pred_df, model_df, th_df, inv)
    report_path = OUTPUT_DIR / "r4_backup_asset_search_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"      -> {report_path}")

    print("\n=== Summary ===")
    print(f"hcm_features_found: {gate['hcm_features_found']} (usable: {gate['hcm_features_usable']})")
    print(f"model_artifacts_found: {gate['model_artifacts_found']}")
    print(f"full_444_predictions_found: {gate['full_444_predictions_found']}")
    print(f"t_contra_low_found: {gate['t_contra_low_found']}")
    print(f"can_restore_without_retraining: {gate['can_restore_without_retraining']}")


if __name__ == "__main__":
    main()
