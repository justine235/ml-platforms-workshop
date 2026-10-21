from __future__ import annotations

import argparse
from pathlib import Path
from time import sleep

import mlflow
from mlflow.tracking import MlflowClient

from common import read_json, write_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Register the fleet model in the active MLflow registry.")
    parser.add_argument("--train-manifest", required=True, help="train_manifest.json written by train.py")
    parser.add_argument("--evaluation-json", required=True, help="evaluation.json written by evaluate.py")
    parser.add_argument("--gate-json", help="Optional gate_report.json written by gate.py")
    parser.add_argument("--output-path", required=True, help="Where to write registration.json")
    parser.add_argument("--model-name", default="fleet-failure-7d")
    parser.add_argument("--skip-if-gate-fails", action="store_true", default=True)
    parser.add_argument("--poll-seconds", type=float, default=1.0)
    parser.add_argument("--max-polls", type=int, default=30)
    return parser


def wait_for_version(client: MlflowClient, name: str, version: str, poll_seconds: float, max_polls: int) -> str:
    status = "PENDING_REGISTRATION"
    for _ in range(max_polls):
        status = client.get_model_version(name=name, version=version).status
        if status == "READY":
            return status
        sleep(poll_seconds)
    return status


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest = read_json(args.train_manifest)
    evaluation = read_json(args.evaluation_json)
    gate = read_json(args.gate_json) if args.gate_json else evaluation["gate"]
    if args.skip_if_gate_fails and not gate["approved"]:
        raise SystemExit("registration blocked by champion/challenger gate")

    result = mlflow.register_model(model_uri=manifest["model_uri"], name=args.model_name)
    client = MlflowClient()
    version = str(result.version)
    status = wait_for_version(client, args.model_name, version, args.poll_seconds, args.max_polls)
    tags = {
        "data_version": manifest["data_version"],
        "git_sha": manifest["git_sha"],
        "source_run_id": manifest["run_id"],
        "valid_pr_auc": str(evaluation["metrics"].get("valid_pr_auc", "")),
        "valid_roc_auc": str(evaluation["metrics"].get("valid_roc_auc", "")),
        "test_pr_auc": str(evaluation["metrics"]["test_pr_auc"]),
        "test_roc_auc": str(evaluation["metrics"]["test_roc_auc"]),
        "test_precision_at_top5pct": str(evaluation["metrics"]["test_precision_at_top5pct"]),
        "test_recall_at_top5pct": str(evaluation["metrics"]["test_recall_at_top5pct"]),
        "gate_approved": str(gate["approved"]).lower(),
    }
    for key, value in tags.items():
        client.set_model_version_tag(name=args.model_name, version=version, key=key, value=value)

    payload = {
        "name": args.model_name,
        "version": version,
        "status": status,
        "tags": tags,
    }
    write_json(Path(args.output_path), payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
