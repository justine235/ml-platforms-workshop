from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import mlflow
import pandas as pd

HERE = Path(__file__).resolve().parent
DEMO = HERE.parent
WORKSHOP = DEMO.parent
ROOT = WORKSHOP.parent
SRC = DEMO / "src"
REF = WORKSHOP / "02-demo-data" / "reference_out"
DATA_GENERATOR = WORKSHOP / "02-demo-data" / "fleet_data_generator.py"
PYTHON = Path(sys.executable)


def run(*args: str, env: dict[str, str] | None = None) -> None:
    subprocess.run([str(PYTHON), *args], check=True, env=env)


def main() -> int:
    out_root = HERE / "out"
    prep_out = out_root / "prep"
    train_out = out_root / "train"
    score_out = out_root / "score"
    drift_out = out_root / "drift"
    raw_out = out_root / "generated" / "data"
    truth_out = out_root / "generated" / "truth"
    mlruns_root = out_root / "mlruns-artifacts"
    db_path = out_root / "mlruns.db"
    for folder in (prep_out, train_out, score_out, drift_out, raw_out, truth_out, mlruns_root):
        folder.mkdir(parents=True, exist_ok=True)

    run(
        str(SRC / "prep.py"),
        "--input-path",
        str(REF / "ml_asset_day_features.csv.gz"),
        "--output-dir",
        str(prep_out),
    )

    tracking_uri = f"sqlite:///{db_path.as_posix()}"
    os.environ["MLFLOW_TRACKING_URI"] = tracking_uri
    os.environ["MLFLOW_REGISTRY_URI"] = tracking_uri
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_registry_uri(tracking_uri)
    experiment_name = "fleet-failure-7d-local"
    client = mlflow.MlflowClient()
    if not mlflow.get_experiment_by_name(experiment_name):
        client.create_experiment(experiment_name, artifact_location=mlruns_root.resolve().as_uri())

    # Champion: a previously-registered logistic regression run, trained for real (not a fabricated
    # number) so the gate comparison below reflects an achievable improvement. This mirrors the
    # "logistic regression" baseline row from the contract's section 8.
    champion_out = train_out / "champion"
    run(
        str(SRC / "train.py"),
        "--input-path",
        str(prep_out),
        "--model-output",
        str(champion_out / "model"),
        "--metrics-output",
        str(champion_out),
        "--experiment-name",
        experiment_name,
        "--model-kind",
        "logistic_regression",
        "--data-version",
        "reference_out",
        "--git-sha",
        "local-validation-champion",
        env=os.environ.copy(),
    )
    champion_path = champion_out / "metrics.json"

    # Challenger: the HistGradientBoosting model from the contract's section 8 (default model kind).
    run(
        str(SRC / "train.py"),
        "--input-path",
        str(prep_out),
        "--model-output",
        str(train_out / "model"),
        "--metrics-output",
        str(train_out),
        "--experiment-name",
        experiment_name,
        "--data-version",
        "reference_out",
        "--git-sha",
        "local-validation",
        env=os.environ.copy(),
    )

    run(
        str(SRC / "evaluate.py"),
        "--input-path",
        str(prep_out),
        "--model-path",
        str(train_out / "model"),
        "--train-metrics-json",
        str(train_out / "metrics.json"),
        "--champion-json",
        str(champion_path),
        "--output-path",
        str(train_out / "evaluation.json"),
    )

    run(
        str(SRC / "register.py"),
        "--train-manifest",
        str(train_out / "train_manifest.json"),
        "--evaluation-json",
        str(train_out / "evaluation.json"),
        "--output-path",
        str(train_out / "registration.json"),
        env=os.environ.copy(),
    )

    registration = pd.read_json(train_out / "registration.json", typ="series")
    run(
        str(SRC / "score.py"),
        "--input-path",
        str(prep_out),
        "--dim-asset-path",
        str(REF / "dim_asset.csv"),
        "--model-path",
        str(train_out / "model"),
        "--model-version",
        str(registration["version"]),
        "--output-dir",
        str(score_out),
    )

    subprocess.run(
        [str(PYTHON), str(DATA_GENERATOR), "--out", str(raw_out), "--truth-dir", str(truth_out), "--with-drift"],
        check=True,
    )
    run(
        str(SRC / "drift.py"),
        "--reference-dir",
        str(raw_out / "telematics"),
        "--current-dir",
        str(raw_out / "telematics_drift"),
        "--dim-asset-path",
        str(REF / "dim_asset.csv"),
        "--output-dir",
        str(drift_out),
    )

    eval_report = pd.read_json(train_out / "evaluation.json")
    score_summary = pd.read_json(score_out / "score_summary.json", typ="series")
    drift_summary = pd.read_json(drift_out / "drift_summary.json", typ="series")
    pr_auc = float(eval_report["metrics"]["test_pr_auc"])
    if abs(pr_auc - 0.385) > 0.03:
        raise AssertionError(f"test PR-AUC drifted too far from the contract: {pr_auc}")
    if int(score_summary["rows"]) != 264:
        raise AssertionError("expected 264 scored rows")
    if int(drift_summary["major_count"]) != 4:
        raise AssertionError("expected four major drift combinations")
    gate = eval_report["gate"]
    if not bool(gate["approved"]):
        raise AssertionError(f"expected the gate to approve the challenger: {gate}")
    print("Local pipeline OK")
    print(f"test_pr_auc={pr_auc:.4f}")
    print(f"scored_rows={int(score_summary['rows'])}")
    print(f"major_drift_pairs={int(drift_summary['major_count'])}")
    print(f"gate_approved={bool(gate['approved'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())