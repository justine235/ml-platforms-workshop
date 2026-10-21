from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

CODE_DIR = Path(__file__).resolve().parents[1] / "code"
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CODE_DIR))

import fleet_ml_core as core
import train_fleet_model as train_script


def make_smoke_dataset(source: Path, target: Path) -> None:
    df = core.load_features(source)
    pieces = []
    quotas = {
        "warmup": 150,
        "train": 1600,
        "gap": 250,
        "valid": 500,
        "test": 400,
        "unlabeled": 50,
        "score": 50,
    }
    for split_name, n_rows in quotas.items():
        part = core.get_split(df, split_name).head(n_rows)
        pieces.append(part)
    sample = pd.concat(pieces, ignore_index=True)
    sample.to_csv(target, index=False)


def test_training_script_smoke(tmp_path: Path):
    sample_csv = tmp_path / "sample.csv"
    summary_json = tmp_path / "summary.json"
    make_smoke_dataset(ROOT / "02-demo-data" / "reference_out" / "ml_asset_day_features.csv.gz", sample_csv)
    rc = train_script.main(
        [
            "--features",
            str(sample_csv),
            "--model-kind",
            "logistic_regression",
            "--experiment",
            "fleet-smoke-test",
            "--run-name",
            "pytest-smoke",
            "--tracking-uri",
            tmp_path.joinpath("mlruns").as_uri(),
            "--summary-json",
            str(summary_json),
        ]
    )
    assert rc == 0
    payload = json.loads(summary_json.read_text(encoding="utf-8"))
    assert payload["model_kind"] == "logistic_regression"
    assert set(payload["mlflow_metric_names"]) == set(core.METRIC_KEYS)
    assert payload["params"]["feature_count"] == 42
