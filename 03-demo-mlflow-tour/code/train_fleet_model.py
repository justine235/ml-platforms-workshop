"""Train the fleet failure model and log a portable MLflow run.

Works unchanged on:
* Local/open-source MLflow
* Microsoft Fabric (workspace-tracked MLflow)
* Azure Machine Learning jobs/workspaces with azureml-mlflow
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mlflow
import numpy as np
import pandas as pd
from mlflow.models import infer_signature
from sklearn.inspection import permutation_importance
from sklearn.metrics import PrecisionRecallDisplay

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import fleet_ml_core as core
import mlflow_compat as compat


@dataclass
class TrainingResult:
    metrics: dict[str, dict[str, float]]
    model_uri: str
    model_version: str | None
    registered_name: str | None
    run_id: str
    tracking_uri: str | None
    model_kind: str
    params: dict[str, Any]
    durations: dict[str, float]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features", required=True, help="Path to ml_asset_day_features.csv or .csv.gz")
    parser.add_argument("--model-kind", default="hist_gradient_boosting", choices=core.MODEL_KINDS)
    parser.add_argument("--experiment", required=True, help="MLflow experiment name")
    parser.add_argument("--register-name", help="Optional registered model name")
    parser.add_argument("--run-name", default="fleet-training")
    parser.add_argument("--tracking-uri", help="Optional MLflow tracking URI override")
    parser.add_argument("--seed", type=int, default=0, help="Seed for artifact sampling only")
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="Model hyper-parameter override. Can be repeated.",
    )
    parser.add_argument("--summary-json", help="Optional path to write a machine-readable summary")
    parser.add_argument("--artifact-subpath", default="model", help="Model artifact folder inside the run")
    return parser.parse_args(argv)


def coerce_value(text: str) -> Any:
    lowered = text.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"none", "null"}:
        return None
    for caster in (int, float):
        try:
            return caster(text)
        except ValueError:
            pass
    return text


def parse_overrides(pairs: list[str]) -> dict[str, Any]:
    overrides: dict[str, Any] = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"override must be NAME=VALUE, got {pair!r}")
        key, value = pair.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"override key is empty in {pair!r}")
        overrides[key] = coerce_value(value.strip())
    return overrides


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def split_summary(df: pd.DataFrame) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for split_name, part in df.groupby(core.SPLIT_COL, sort=False):
        payload: dict[str, Any] = {"rows": len(part)}
        labels = part[core.LABEL].dropna()
        if len(labels):
            payload["positives"] = int(labels.sum())
            payload["prevalence"] = round(float(labels.mean()), 4)
        summary[str(split_name)] = payload
    return summary


def evaluate_split_metrics(model: Any, df: pd.DataFrame, feature_names: list[str]) -> dict[str, dict[str, float]]:
    metrics: dict[str, dict[str, float]] = {}
    for split_name in ("train", "valid", "test"):
        part = core.get_split(df, split_name)
        metrics[split_name] = core.eval_scores(part[core.LABEL], model.predict_proba(part[feature_names])[:, 1])
    return metrics


def plot_precision_recall(model: Any, valid: pd.DataFrame, feature_names: list[str], out_path: Path) -> None:
    scores = model.predict_proba(valid[feature_names])[:, 1]
    display = PrecisionRecallDisplay.from_predictions(valid[core.LABEL], scores)
    display.ax_.set_title("Validation precision-recall curve")
    display.ax_.figure.tight_layout()
    display.ax_.figure.savefig(out_path, dpi=150)
    plt.close(display.ax_.figure)


def create_permutation_importance_artifacts(
    *,
    model: Any,
    valid: pd.DataFrame,
    feature_names: list[str],
    seed: int,
    csv_path: Path,
    png_path: Path,
) -> pd.DataFrame:
    sample = valid.sample(n=min(len(valid), 1500), random_state=seed).reset_index(drop=True)
    scoring = "average_precision" if len(sample[core.LABEL].unique()) > 1 else None
    importance = permutation_importance(
        model,
        sample[feature_names],
        sample[core.LABEL],
        n_repeats=5,
        random_state=seed,
        scoring=scoring,
    )
    frame = pd.DataFrame(
        {
            "feature": feature_names,
            "importance_mean": importance.importances_mean,
            "importance_std": importance.importances_std,
        }
    ).sort_values(["importance_mean", "feature"], ascending=[False, True], kind="stable")
    frame.to_csv(csv_path, index=False)

    top = frame.head(15).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(top["feature"], top["importance_mean"], xerr=top["importance_std"], color="#0F6CBD")
    ax.set_title("Permutation importance (validation sample)")
    ax.set_xlabel("Mean importance")
    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)
    return frame


def write_feature_list(feature_names: list[str], out_path: Path) -> None:
    out_path.write_text(json.dumps(feature_names, indent=2) + "\n", encoding="utf-8")


def write_data_card(
    *,
    df: pd.DataFrame,
    features_path: Path,
    features_sha256: str,
    feature_names: list[str],
    out_path: Path,
) -> None:
    labeled = df[df[core.LABEL].notna()]
    lines = [
        "# Data card",
        "",
        f"- Source file: `{features_path.name}`",
        f"- Absolute source path: `{features_path}`",
        f"- SHA256: `{features_sha256}`",
        f"- Rows: {len(df):,}",
        f"- Labelled rows: {len(labeled):,}",
        f"- Positive rate: {labeled[core.LABEL].mean():.4f}",
        f"- Feature count: {len(feature_names)}",
        f"- Splits: {', '.join(sorted(df[core.SPLIT_COL].unique()))}",
        "- Contract target: HGB test PR-AUC about 0.385 and ROC-AUC about 0.75 (+/- 0.03).",
        "- Caveat: labels come from CMMS corrective work orders, so silent failures and late work orders create label noise.",
        "",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")


def ensure_clean_dir(path: Path) -> Path:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def summarize_params(
    *,
    features_path: Path,
    features_sha256: str,
    df: pd.DataFrame,
    feature_names: list[str],
    overrides: dict[str, Any],
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "data_file_name": features_path.name,
        "data_file_sha256": features_sha256,
        "feature_count": len(feature_names),
        "python_version": platform.python_version(),
        "platform_name": compat.detect_platform(tracking_uri=mlflow.get_tracking_uri()),
        "mlflow_version": mlflow.__version__,
        "pandas_version": pd.__version__,
        "numpy_version": np.__version__,
    }
    try:
        import sklearn

        params["sklearn_version"] = sklearn.__version__
    except Exception as exc:  # pragma: no cover - informational and explicit
        raise RuntimeError("scikit-learn must be installed for this script") from exc

    for split_name, payload in split_summary(df).items():
        for key, value in payload.items():
            params[f"{split_name}_{key}"] = value
    for key, value in overrides.items():
        params[f"hp_{key}"] = value
    return params


def run_training(args: argparse.Namespace) -> TrainingResult:
    features_path = Path(args.features).resolve()
    overrides = parse_overrides(args.override)
    compat.configure_tracking(args.tracking_uri)
    compat.set_experiment(args.experiment)

    start = time.perf_counter()
    df = core.load_features(features_path)
    feature_names = list(core.FEATURES)
    model, metrics = core.train_and_evaluate(df, kind=args.model_kind, features=feature_names, **overrides)
    split_metrics = evaluate_split_metrics(model, df, feature_names)
    durations = {"train_seconds": round(time.perf_counter() - start, 3)}
    features_sha256 = sha256_file(features_path)

    params = summarize_params(
        features_path=features_path,
        features_sha256=features_sha256,
        df=df,
        feature_names=feature_names,
        overrides=overrides,
    )
    valid = core.get_split(df, "valid")
    work_root = ensure_clean_dir(Path.cwd() / "train_fleet_model_artifacts")
    try:
        pr_curve_path = work_root / "precision_recall_valid.png"
        importance_csv = work_root / "permutation_importance_valid.csv"
        importance_png = work_root / "permutation_importance_valid.png"
        feature_list_path = work_root / "feature_list.json"
        data_card_path = work_root / "data_card.md"

        plot_precision_recall(model, valid, feature_names, pr_curve_path)
        create_permutation_importance_artifacts(
            model=model,
            valid=valid,
            feature_names=feature_names,
            seed=args.seed,
            csv_path=importance_csv,
            png_path=importance_png,
        )
        write_feature_list(feature_names, feature_list_path)
        write_data_card(
            df=df,
            features_path=features_path,
            features_sha256=features_sha256,
            feature_names=feature_names,
            out_path=data_card_path,
        )

        with mlflow.start_run(run_name=args.run_name) as run:
            mlflow.set_tags(
                {
                    "workshop": "fleet-mlflow-tour",
                    "model_kind": args.model_kind,
                    "platform": compat.detect_platform(tracking_uri=mlflow.get_tracking_uri()),
                }
            )
            mlflow.log_params({key: str(value) if value is None else value for key, value in sorted(params.items())})
            mlflow.log_metrics(core.mlflow_metrics(metrics))
            for split_name, payload in split_metrics.items():
                for key, value in payload.items():
                    mlflow.log_metric(f"{split_name}_{key}", float(value))

            mlflow.log_artifact(str(pr_curve_path), artifact_path="reports")
            mlflow.log_artifact(str(importance_csv), artifact_path="reports")
            mlflow.log_artifact(str(importance_png), artifact_path="reports")
            mlflow.log_artifact(str(feature_list_path), artifact_path="reports")
            mlflow.log_artifact(str(data_card_path), artifact_path="reports")

            sklearn_version = str(params["sklearn_version"])
            pip_requirements = compat.build_pip_requirements(
                pandas_version=pd.__version__,
                sklearn_version=sklearn_version,
                mlflow_version=mlflow.__version__,
                numpy_version=np.__version__,
            )
            signature = infer_signature(valid[feature_names].head(20), model.predict(valid[feature_names].head(20)))
            model_info = compat.log_sklearn_model(
                model=model,
                model_name=args.artifact_subpath,
                signature=signature,
                input_example=valid[feature_names].head(5),
                pip_requirements=pip_requirements,
            )
            model_uri = f"runs:/{run.info.run_id}/{args.artifact_subpath}"
            model_version: str | None = None
            if args.register_name:
                registered = compat.register_model(model_uri=model_uri, registered_name=args.register_name)
                model_version = str(getattr(registered, "version", ""))
                if model_version:
                    compat.set_version_tags(
                        args.register_name,
                        model_version,
                        {
                            "source_run_id": run.info.run_id,
                            "workshop": "fleet-mlflow-tour",
                            "model_kind": args.model_kind,
                        },
                    )

            return TrainingResult(
                metrics=metrics,
                model_uri=getattr(model_info, "model_uri", model_uri),
                model_version=model_version,
                registered_name=args.register_name,
                run_id=run.info.run_id,
                tracking_uri=mlflow.get_tracking_uri(),
                model_kind=args.model_kind,
                params=params,
                durations=durations,
            )
    finally:
        if work_root.exists():
            shutil.rmtree(work_root)


def result_to_json(result: TrainingResult) -> dict[str, Any]:
    return {
        "run_id": result.run_id,
        "tracking_uri": result.tracking_uri,
        "model_uri": result.model_uri,
        "registered_name": result.registered_name,
        "model_version": result.model_version,
        "model_kind": result.model_kind,
        "metrics": result.metrics,
        "params": result.params,
        "durations": result.durations,
        "mlflow_metric_names": core.mlflow_metrics(result.metrics),
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = run_training(args)
    payload = result_to_json(result)
    text = json.dumps(payload, indent=2, sort_keys=True)
    print(text)
    if args.summary_json:
        summary_path = Path(args.summary_json)
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
