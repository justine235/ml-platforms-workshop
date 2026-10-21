from __future__ import annotations

import argparse
from pathlib import Path

import mlflow.sklearn
import pandas as pd

import fleet_ml_core as core
from common import read_table, write_json, write_table


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Score the latest fleet asset-day rows and emit the ml.failure_risk_score contract.")
    parser.add_argument("--input-path", required=True, help="Prepared feature dataset file or folder")
    parser.add_argument("--dim-asset-path", required=True, help="Path to dim_asset.csv with site_code and equipment_class")
    parser.add_argument("--model-path", required=True, help="Local MLflow model folder or MLflow model URI")
    parser.add_argument("--model-version", default="dev")
    parser.add_argument("--output-dir", required=True, help="Folder for CSV/Parquet outputs and the summary JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    features = read_table(args.input_path)
    dim_asset = pd.read_csv(args.dim_asset_path, dtype={"erp_asset_id": str})
    model = mlflow.sklearn.load_model(args.model_path)
    scored = core.score_latest(features, model, model_version=args.model_version)
    enriched = scored.merge(
        dim_asset[["erp_asset_id", "site_code", "equipment_class"]],
        on="erp_asset_id",
        how="left",
    )
    enriched = enriched[
        [
            "score_date",
            "erp_asset_id",
            "site_code",
            "equipment_class",
            "risk_score",
            "risk_band",
            "risk_rank",
            "top_drivers",
            "model_version",
        ]
    ]
    written = write_table(enriched, args.output_dir, "ml_failure_risk_score")
    summary = {
        "rows": len(enriched),
        "risk_band_counts": {k: int(v) for k, v in enriched["risk_band"].value_counts().sort_index().to_dict().items()},
        "top_5": enriched.head(5).to_dict(orient="records"),
        "output_files": written,
    }
    write_json(Path(args.output_dir) / "score_summary.json", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
