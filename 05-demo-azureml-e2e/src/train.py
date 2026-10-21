from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature

import fleet_ml_core as core
from common import git_sha, read_table, write_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train the fleet AML model and log it to MLflow.")
    parser.add_argument("--input-path", required=True, help="Prepared feature dataset file or folder")
    parser.add_argument("--model-output", required=True, help="Folder where the MLflow model is exported")
    parser.add_argument("--metrics-output", required=True, help="Folder where metrics and manifests are written")
    parser.add_argument("--experiment-name", default="fleet-failure-7d", help="MLflow experiment name")
    parser.add_argument("--model-kind", default="hist_gradient_boosting", choices=core.MODEL_KINDS)
    parser.add_argument("--learning-rate", type=float, default=core.HGB_PARAMS["learning_rate"])
    parser.add_argument("--max-leaf-nodes", type=int, default=core.HGB_PARAMS["max_leaf_nodes"])
    parser.add_argument("--l2-regularization", type=float, default=core.HGB_PARAMS["l2_regularization"])
    parser.add_argument("--max-iter", type=int, default=core.HGB_PARAMS["max_iter"])
    parser.add_argument("--data-version", default="reference")
    parser.add_argument("--git-sha", default=git_sha())
    parser.add_argument("--model-name", default="fleet-failure-7d")
    parser.add_argument("--drop-fault-features", action="store_true", help="Run the ablation without warn/crit feature columns")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    features = read_table(args.input_path)
    feature_columns = core.NO_FAULT_FEATURES if args.drop_fault_features else core.FEATURES
    overrides: dict[str, Any] = {}
    if args.model_kind == "hist_gradient_boosting":
        overrides = {
            "learning_rate": args.learning_rate,
            "max_leaf_nodes": args.max_leaf_nodes,
            "l2_regularization": args.l2_regularization,
            "max_iter": args.max_iter,
        }

    mlflow.set_experiment(args.experiment_name)
    mlflow.autolog(log_models=False, silent=True)
    Path(args.model_output).mkdir(parents=True, exist_ok=True)
    Path(args.metrics_output).mkdir(parents=True, exist_ok=True)

    with mlflow.start_run(run_name=f"{args.model_kind}-fleet") as run:
        model, metrics = core.train_and_evaluate(features, kind=args.model_kind, features=feature_columns, **overrides)
        flat_metrics = core.mlflow_metrics(metrics)
        for key, value in flat_metrics.items():
            mlflow.log_metric(key, value)
        mlflow.log_params(
            {
                "model_kind": args.model_kind,
                "feature_variant": "no_fault_features" if args.drop_fault_features else "all_42_features",
                "feature_count": len(feature_columns),
                "learning_rate": overrides.get("learning_rate", ""),
                "max_leaf_nodes": overrides.get("max_leaf_nodes", ""),
                "l2_regularization": overrides.get("l2_regularization", ""),
                "max_iter": overrides.get("max_iter", ""),
            }
        )
        mlflow.set_tags(
            {
                "scenario": "fleet-failure-7d",
                "data_version": args.data_version,
                "git_sha": args.git_sha,
                "split_policy": "purged_time_splits_from_contract",
                "reason_codes": "rule_based_not_model_attribution",
                "registered_model_name": args.model_name,
            }
        )
        valid_frame = core.get_split(features, "valid")[list(feature_columns)]
        signature = infer_signature(valid_frame.head(20), model.predict_proba(valid_frame.head(20))[:, 1])
        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="model",
            signature=signature,
            input_example=valid_frame.head(3),
        )
        mlflow.sklearn.save_model(sk_model=model, path=args.model_output, signature=signature, input_example=valid_frame.head(3))
        manifest = {
            "run_id": run.info.run_id,
            "model_uri": f"runs:/{run.info.run_id}/model",
            "model_output_path": str(Path(args.model_output).resolve()),
            "metrics": flat_metrics,
            "model_kind": args.model_kind,
            "feature_count": len(feature_columns),
            "data_version": args.data_version,
            "git_sha": args.git_sha,
        }
        write_json(Path(args.metrics_output) / "metrics.json", {"metrics": flat_metrics, "full_metrics": metrics})
        write_json(Path(args.metrics_output) / "train_manifest.json", manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
