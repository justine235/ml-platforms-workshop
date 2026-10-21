from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import mlflow.sklearn

import fleet_ml_core as core
from common import normalise_metrics, read_json, read_table, write_json
from gate import build_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate the fleet model on the test split and compare it with the champion.")
    parser.add_argument("--input-path", required=True, help="Prepared feature dataset file or folder")
    parser.add_argument("--model-path", required=True, help="Local MLflow model folder or MLflow model URI")
    parser.add_argument("--train-metrics-json", help="Optional metrics.json written by train.py")
    parser.add_argument("--champion-json", help="Optional current champion metrics JSON")
    parser.add_argument("--output-path", required=True, help="Where to write evaluation.json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    features = read_table(args.input_path)
    model = mlflow.sklearn.load_model(args.model_path)
    test_frame = core.get_split(features, "test")
    predictions = model.predict_proba(test_frame[core.FEATURES])[:, 1]
    test_metrics = core.eval_scores(test_frame[core.LABEL], predictions)
    train_metrics: dict[str, Any] = read_json(args.train_metrics_json) if args.train_metrics_json else {}
    combined_metrics = normalise_metrics(train_metrics.get("metrics", train_metrics))
    combined_metrics.update(
        {
            "test_pr_auc": float(test_metrics["pr_auc"]),
            "test_roc_auc": float(test_metrics["roc_auc"]),
            "test_precision_at_top5pct": float(test_metrics["precision_at_top5pct"]),
            "test_recall_at_top5pct": float(test_metrics["recall_at_top5pct"]),
        }
    )
    challenger_payload = {"metrics": combined_metrics}
    champion_payload = read_json(args.champion_json) if args.champion_json else None
    gate_report = build_report(challenger_payload, champion_payload)
    payload = {
        "metrics": combined_metrics,
        "test_details": test_metrics,
        "gate": gate_report,
    }
    write_json(Path(args.output_path), payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
