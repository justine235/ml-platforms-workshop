from __future__ import annotations

import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path

import mlflow

ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = ROOT / "03-demo-mlflow-tour" / "code"
sys.path.insert(0, str(CODE_DIR))

import fleet_ml_core as core
import train_fleet_model as train_script


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train locally, export the MLflow model folder, and zip it.")
    parser.add_argument("--features", default=str(ROOT / "02-demo-data" / "reference_out" / "ml_asset_day_features.csv.gz"))
    parser.add_argument("--out-dir", default=str(Path(__file__).resolve().parent / "out"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out_dir = Path(args.out_dir).resolve()
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    tracking_dir = out_dir / "tracking"
    summary_path = out_dir / "training-summary.json"
    cli_args = train_script.parse_args(
        [
            "--features",
            str(Path(args.features).resolve()),
            "--experiment",
            "fleet-portability-local",
            "--run-name",
            "export-portable-model",
            "--tracking-uri",
            tracking_dir.resolve().as_uri(),
            "--summary-json",
            str(summary_path),
        ]
    )
    result = train_script.run_training(cli_args)
    payload = train_script.result_to_json(result)
    summary_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    model_dir = out_dir / "model-folder"
    mlflow.artifacts.download_artifacts(result.model_uri, dst_path=str(model_dir))
    exported_model = next(model_dir.iterdir())
    sample = core.load_features(Path(args.features)).head(20)
    sample[core.FEATURES].to_csv(out_dir / "sample_input.csv", index=False)
    preds = mlflow.pyfunc.load_model(str(exported_model)).predict(sample[core.FEATURES]).tolist()
    (out_dir / "sample_predictions.json").write_text(json.dumps(preds, indent=2) + "\n", encoding="utf-8")

    zip_path = out_dir / "model-folder.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in exported_model.rglob("*"):
            if path.is_file():
                zf.write(path, arcname=path.relative_to(exported_model))

    print(json.dumps({"model_folder": str(exported_model), "zip_path": str(zip_path), "run_id": result.run_id}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

