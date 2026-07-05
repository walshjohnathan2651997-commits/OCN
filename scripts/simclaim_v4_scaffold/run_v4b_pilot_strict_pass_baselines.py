import csv
import importlib.util
from pathlib import Path


ROOT = Path(r"D:\ocn")
BASE_SCRIPT = ROOT / "scripts" / "simclaim_v4_scaffold" / "run_v4_pilot_small_baselines.py"
VALIDATION_AUDIT = ROOT / "data" / "simclaim_hardpair_v4b_pilot" / "audit" / "v4b_independent_validation_audit.csv"

spec = importlib.util.spec_from_file_location("v4_baselines", BASE_SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def strict_pass_groups():
    with VALIDATION_AUDIT.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return {r["v4_group_id"] for r in rows if str(r.get("validator_ok", "")).lower() == "true"}


PASS_GROUPS = strict_pass_groups()

mod.INPUT_CSV = ROOT / "data" / "simclaim_hardpair_v4b_pilot" / "candidates" / "simclaim_hardpair_v4b_pilot_candidates.csv"
mod.EXP_ROOT = ROOT / "experiments" / "simclaim_hardpair_v4b_pilot_strict_pass_baselines"
mod.METRIC_DIR = mod.EXP_ROOT / "metrics"
mod.PRED_DIR = mod.EXP_ROOT / "predictions"
mod.REPORT_DIR = mod.EXP_ROOT / "reports"
mod.METRICS_CSV = mod.METRIC_DIR / "v4b_pilot_strict_pass_baseline_metrics.csv"
mod.PER_CLASS_CSV = mod.METRIC_DIR / "v4b_pilot_strict_pass_baseline_per_class_f1.csv"
mod.PRED_CSV = mod.PRED_DIR / "v4b_pilot_strict_pass_baseline_predictions.csv"
mod.SUMMARY_JSON = mod.REPORT_DIR / "v4b_pilot_strict_pass_baseline_summary.json"
mod.REPORT_MD = mod.REPORT_DIR / "v4b_pilot_strict_pass_baseline_report.md"
mod.DATASET_NAME = "simclaim_hardpair_v4b_pilot_strict_pass_only"
mod.REPORT_TITLE = "v4b pilot strict-pass small-data baseline report"
mod.REPORT_NOTE = (
    "This report uses only rows from groups that passed the independent strict validator. "
    "It does not use LLM evaluation."
)
mod.ROW_FILTER = lambda row: row.get("v4_group_id") in PASS_GROUPS


if __name__ == "__main__":
    mod.run()
