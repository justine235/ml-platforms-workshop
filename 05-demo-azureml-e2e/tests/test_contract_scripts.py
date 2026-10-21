from __future__ import annotations

import pathlib

import pandas as pd

from src import prep

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REF = ROOT / "02-demo-data" / "reference_out"


def test_prep_contract_validation() -> None:
    features = pd.read_csv(REF / "ml_asset_day_features.csv.gz")
    summary = prep.validate_features(features, strict=True)
    assert summary["rows"] == 50876
    assert summary["feature_count"] == 42
