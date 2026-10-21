from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
WORKSHOP_DIR = ROOT.parents[1]
# Kit-relative defaults, same convention as the ETL demo's run_local.py: FLEET_RAW_ROOT /
# FLEET_TRUTH_ROOT let a session point this at an already-generated data cache instead of
# paying for a fresh fleet_data_generator.py run. No session-specific path is hardcoded here.
DATA_ROOT = Path(os.environ.get("FLEET_RAW_ROOT") or (WORKSHOP_DIR / "02-demo-data" / "data"))
TRUTH_ROOT = Path(os.environ.get("FLEET_TRUTH_ROOT") or (WORKSHOP_DIR / "02-demo-data" / "truth"))
REFERENCE_DIR = WORKSHOP_DIR / "02-demo-data" / "reference_out"
GENERATOR_PATH = WORKSHOP_DIR / "02-demo-data" / "fleet_data_generator.py"

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "notebooks" / "shared"))

from notebooks import nb_04_features, nb_05_train_mlflow, nb_06_register_score, nb_07_drift_monitor, nb_08_promotion_gate
from notebooks.notebook_common import make_local_context, sqlite_tracking_uri
from notebooks.shared import fleet_reference_pipeline as ref

EXPECTED_SPLITS = {
    "warmup": {"rows": 3976, "positives": 196},
    "train": {"rows": 28520, "positives": 1639},
    "gap": {"rows": 3830, "positives": 219},
    "valid": {"rows": 6591, "positives": 353},
    "test": {"rows": 6111, "positives": 274},
    "unlabeled": {"rows": 1584, "positives": 0},
    "score": {"rows": 264, "positives": 0},
}


def ensure_demo_data() -> tuple[Path, Path]:
    data_dir = DATA_ROOT
    truth_dir = TRUTH_ROOT
    if data_dir.exists() and truth_dir.exists():
        return data_dir, truth_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    truth_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(GENERATOR_PATH),
        "--out",
        str(data_dir),
        "--truth-dir",
        str(truth_dir),
        "--with-drift",
    ]
    subprocess.run(cmd, check=True)
    return data_dir, truth_dir


def build_local_tables(data_dir: Path) -> dict[str, pd.DataFrame]:
    manifest = json.loads((data_dir / "_manifest.json").read_text(encoding="utf-8"))
    cutoff_epoch = ref.to_epoch(manifest["window"]["cutoff_utc"])
    erp = ref.read_csv(data_dir / "erp" / "erp_assets.csv")
    xw = ref.read_csv(data_dir / "reference" / "asset_crosswalk.csv")
    ref.read_csv(data_dir / "reference" / "site_master.csv")
    catalog = ref.read_csv(data_dir / "reference" / "fault_code_catalog.csv")
    resolve = ref.make_resolver(erp, xw)

    silver, _ = ref.silver_telemetry(ref.load_telematics([str(data_dir / "telematics")]), resolve, cutoff_epoch)
    silver_drift, _ = ref.silver_telemetry(ref.load_telematics([str(data_dir / "telematics_drift")]), resolve, cutoff_epoch)
    dim = ref.build_dim_asset(erp, silver, cutoff_epoch)
    daily = ref.build_daily(silver, dim)
    return {
        "silver.telemetry": silver,
        "silver.telemetry_drift": silver_drift,
        "gold.fact_telemetry_daily": daily,
        "gold.fact_work_order": pd.read_csv(REFERENCE_DIR / "fact_work_order.csv"),
        "gold.dim_asset": dim,
        "bronze.fault_code_catalog": catalog,
    }


def assert_equal(actual, expected, message: str) -> None:
    if actual != expected:
        raise AssertionError(f"{message}: expected {expected!r}, got {actual!r}")


def main() -> None:
    data_dir, _truth_dir = ensure_demo_data()
    # Override escape hatch: on a deeply nested checkout path (e.g. some OneDrive or
    # sandboxed layouts) the default output dir can push MLflow artifact copies past
    # Windows MAX_PATH (260 chars). Set ML_MLOPS_LOCAL_OUT_DIR to a short path if needed.
    output_dir = Path(os.environ.get("ML_MLOPS_LOCAL_OUT_DIR", str(ROOT / "local-validation" / "out")))
    mlflow_dir = output_dir / "mlflow"
    mlflow_dir.mkdir(parents=True, exist_ok=True)
    context = make_local_context(
        reference_dir=REFERENCE_DIR,
        output_dir=output_dir,
        artifact_dir=output_dir / "artifacts",
        tracking_uri=sqlite_tracking_uri(mlflow_dir / "mlruns.db"),
        tables=build_local_tables(data_dir),
    )

    features_summary = nb_04_features.run(context=context)
    assert_equal(features_summary["rows"], 50876, "feature rows")
    assert_equal(features_summary["labelled_rows"], 49028, "labelled rows")
    assert_equal(features_summary["positive_rate_labelled"], 0.0547, "positive rate")
    assert_equal(features_summary["split_counts"], EXPECTED_SPLITS, "split counts")
    assert_equal(features_summary["reference_comparison"]["ok"], True, "feature reference comparison")

    train_summary_1 = nb_05_train_mlflow.run(context=context)
    train_summary_2 = nb_05_train_mlflow.run(context=context)
    hgb_metrics = train_summary_2["child_runs"]["hist_gradient_boosting"]
    if not (0.316 <= hgb_metrics["valid_pr_auc"] <= 0.356):
        raise AssertionError("valid PR-AUC out of expected range: {!r}".format(hgb_metrics["valid_pr_auc"]))
    if not (0.365 <= hgb_metrics["test_pr_auc"] <= 0.405):
        raise AssertionError("test PR-AUC out of expected range: {!r}".format(hgb_metrics["test_pr_auc"]))

    score_summary = nb_06_register_score.run(context=context)
    assert_equal(score_summary["rows"], 264, "scored assets")
    assert_equal(score_summary["frozen_reference_comparison"]["reason_code_matches"], 264, "reason-code matches")
    reference_bands = pd.read_csv(REFERENCE_DIR / "ml_failure_risk_score.csv")["risk_band"].value_counts().sort_index().to_dict()
    assert_equal(reference_bands, {"High": 9, "Low": 248, "Medium": 7}, "frozen risk bands")

    drift_summary = nb_07_drift_monitor.run(context=context)
    assert_equal(drift_summary["major_shift_count"], 4, "major drift combinations")
    assert_equal(drift_summary["reference_comparison"]["ok"], True, "drift reference comparison")

    gate_summary = nb_08_promotion_gate.run(
        params={"champion_version": train_summary_1["registered_version"], "challenger_version": train_summary_2["registered_version"]},
        context=context,
    )
    if gate_summary["decision"] not in {"hold", "promote"}:
        raise AssertionError("unexpected gate decision: {!r}".format(gate_summary["decision"]))

    summary = {
        "features": features_summary,
        "training_first": train_summary_1,
        "training_second": train_summary_2,
        "score": score_summary,
        "drift": drift_summary,
        "gate": gate_summary,
    }
    target = output_dir / "validation-summary.json"
    target.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "summary_file": str(target)}, indent=2))


if __name__ == "__main__":
    main()
