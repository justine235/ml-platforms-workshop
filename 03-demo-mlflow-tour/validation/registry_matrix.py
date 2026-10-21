"""Validation matrix runner for the MLflow tour (B1).

Trains the fleet model once with a given MLflow install, then probes the
model registry's **open-source** stage and alias behavior: register two
versions, try aliases, try stages, load by every models:/ URI shape.

Writes one JSON result file per MLflow version. Never touches Fabric or
Azure ML; this is local/open-source MLflow only, with a local sqlite
registry backend (--backend-store-uri sqlite:///...).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from pathlib import Path
from typing import Any

CODE_DIR = Path(__file__).resolve().parents[1] / "code"
WS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CODE_DIR))

import mlflow
import train_fleet_model as train_script


def probe(label: str, fn, *args, **kwargs) -> dict[str, Any]:
    """Run one registry operation, capture success/error/warnings as data (never raise)."""
    record: dict[str, Any] = {"op": label}
    start = time.perf_counter()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            result = fn(*args, **kwargs)
            record["ok"] = True
            record["result"] = _jsonable(result)
        except Exception as exc:  # noqa: BLE001 - we want every failure captured as data
            record["ok"] = False
            record["error_type"] = type(exc).__name__
            record["error"] = str(exc)[:500]
        record["warnings"] = [str(w.message)[:300] for w in caught]
    record["seconds"] = round(time.perf_counter() - start, 3)
    return record


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    for attr in ("version", "name", "aliases", "current_stage", "run_id"):
        if hasattr(value, attr):
            return {a: _jsonable(getattr(value, a)) for a in ("version", "name", "aliases", "current_stage", "run_id") if hasattr(value, a)}
    return str(value)[:300]

def run_matrix(label: str, tracking_dir: Path, out_json: Path, features: Path) -> dict[str, Any]:
    tracking_dir.mkdir(parents=True, exist_ok=True)
    db_path = tracking_dir / f"mlflow-{label}.db"
    tracking_uri = f"sqlite:///{db_path.as_posix()}"
    registered_name = f"fleet-failure-7d-matrix-{label}"

    mlflow_version = mlflow.__version__
    env_info = {
        "label": label,
        "mlflow_version": mlflow_version,
        "tracking_uri": tracking_uri,
        "registered_name": registered_name,
    }

    # 1. Train once and register the first version from the training script
    # (same code path as the real workshop demo).
    cli_args = train_script.parse_args(
        [
            "--features", str(features),
            "--experiment", "fleet-validation-matrix",
            "--run-name", f"matrix-train-{label}",
            "--tracking-uri", tracking_uri,
            "--register-name", registered_name,
        ]
    )
    train_start = time.perf_counter()
    result = train_script.run_training(cli_args)
    train_seconds = round(time.perf_counter() - train_start, 3)
    payload = train_script.result_to_json(result)

    # 2. Register a second version pointing at the SAME run artifact, purely to
    # have two versions to compare stages/aliases across.
    client = mlflow.MlflowClient()
    second = probe("register_second_version", mlflow.register_model, result.model_uri, registered_name)
    v1 = result.model_version
    v2 = None
    if second["ok"] and isinstance(second["result"], dict):
        v2 = second["result"].get("version")

    registry_ops: list[dict[str, Any]] = [second]

    # 3. Aliases (MLflow >= 2.9 API surface; may not exist on older clients).
    if v1:
        registry_ops.append(probe("set_registered_model_alias(champion->v1)", client.set_registered_model_alias, registered_name, "champion", str(v1)))
        registry_ops.append(probe("get_model_version_by_alias(champion)", client.get_model_version_by_alias, registered_name, "champion"))
        registry_ops.append(probe("load_model(models:/name@champion)", mlflow.pyfunc.load_model, f"models:/{registered_name}@champion"))

    # 4. Stages (deprecated in MLflow >= 2.9, removed in MLflow 3 client surface).
    if v1:
        registry_ops.append(probe("transition_model_version_stage(v1->Staging)", client.transition_model_version_stage, registered_name, str(v1), "Staging"))
    if v2:
        registry_ops.append(probe("transition_model_version_stage(v2->Production)", client.transition_model_version_stage, registered_name, str(v2), "Production"))
    registry_ops.append(probe("load_model(models:/name/Production)", mlflow.pyfunc.load_model, f"models:/{registered_name}/Production"))
    registry_ops.append(probe("load_model(models:/name/Staging)", mlflow.pyfunc.load_model, f"models:/{registered_name}/Staging"))
    registry_ops.append(probe("load_model(models:/name/latest)", mlflow.pyfunc.load_model, f"models:/{registered_name}/latest"))

    # 5. MLflow 3 "LoggedModel" surface, probed defensively (new concept, may not
    # exist pre-3.0, and its exact API moved during the 3.x pre-releases).
    has_logged_model_api = hasattr(mlflow, "get_logged_model") or hasattr(mlflow, "search_logged_models")
    registry_ops.append({"op": "has_logged_model_api", "ok": True, "result": has_logged_model_api, "warnings": []})

    out = {
        "env": env_info,
        "train_seconds": train_seconds,
        "training_summary": payload,
        "versions": {"v1": v1, "v2": v2},
        "registry_ops": registry_ops,
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return out

def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", required=True, help="Short version label, e.g. 2122, 2162, 2222, 3x")
    parser.add_argument("--tracking-dir", required=True, help="Folder for the sqlite backend store")
    parser.add_argument("--out-json", required=True, help="Where to write the JSON result")
    parser.add_argument(
        "--features",
        default=str(WS / "02-demo-data" / "reference_out" / "ml_asset_day_features.csv.gz"),
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    out = run_matrix(args.label, Path(args.tracking_dir), Path(args.out_json), Path(args.features))
    print(json.dumps({"label": args.label, "mlflow_version": out["env"]["mlflow_version"], "versions": out["versions"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
