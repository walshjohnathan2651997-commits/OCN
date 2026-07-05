import csv
import importlib.util
import sys
from pathlib import Path


ROOT = Path(r"D:\ocn")
LLM_LIB = ROOT / "scripts" / "simclaim_detemplate_v1_150" / "run_llm_small_eval.py"
EXP_ROOT = ROOT / "experiments" / "simclaim_hardpair_v2b_llm_small_eval"


def load_lib():
    spec = importlib.util.spec_from_file_location("llm_eval_lib", LLM_LIB)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def rewrite_dataset_name(path, dataset_name):
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        for row in reader:
            row["dataset"] = dataset_name
            rows.append(row)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    m = load_lib()
    m.SPLIT_ROOT = ROOT / "data" / "simclaim_hardpair_v2b" / "splits_group_stratified"
    m.EXP_ROOT = EXP_ROOT
    m.PRED_DIR = EXP_ROOT / "predictions"
    m.RAW_DIR = EXP_ROOT / "raw_outputs"
    m.METRIC_DIR = EXP_ROOT / "metrics"
    m.REPORT_DIR = EXP_ROOT / "reports"
    m.PRED_CSV = m.PRED_DIR / "hardpair_v2b_llm_small_eval_predictions.csv"
    m.RAW_JSONL = m.RAW_DIR / "hardpair_v2b_llm_small_eval_raw_outputs.jsonl"
    m.METRICS_CSV = m.METRIC_DIR / "hardpair_v2b_llm_small_eval_metrics.csv"
    m.REPORT_MD = m.REPORT_DIR / "hardpair_v2b_llm_small_eval_report.md"
    m.SUMMARY_JSON = m.REPORT_DIR / "hardpair_v2b_llm_small_eval_summary.json"
    sys.argv = [sys.argv[0], "--max-workers", "6"]
    m.main()
    rewrite_dataset_name(m.METRICS_CSV, "simclaim_hardpair_v2b_268_group_stratified")


if __name__ == "__main__":
    main()
