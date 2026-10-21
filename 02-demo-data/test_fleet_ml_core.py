"""Checks fleet_ml_core.py against reference_out (run: python -m pytest 02-demo-data/test_fleet_ml_core.py -q)."""
import json
import pathlib

import numpy as np
import pandas as pd
import pytest

import fleet_ml_core as core

HERE = pathlib.Path(__file__).parent
REF = HERE / "reference_out"


@pytest.fixture(scope="module")
def features():
    return core.load_features(REF / "ml_asset_day_features.csv.gz")


@pytest.fixture(scope="module")
def truth():
    return json.loads((REF / "ground_truth.json").read_text(encoding="utf-8"))


def test_table_shape_and_split_counts(features, truth):
    assert len(features) == 50876
    assert features["split"].value_counts().to_dict() == {"train": 28520, "test": 6111, "valid": 6591, "gap": 3830, "warmup": 3976, "unlabeled": 1584, "score": 264}
    lab = features[features["split"] != "unlabeled"][core.LABEL].dropna()
    assert len(core.get_split(features, "train", "gap", "valid", "test", "warmup")) == 49028
    assert abs(lab[features["split"].isin(["train", "gap", "valid", "test", "warmup"])].mean() - 0.0547) < 0.0005
    assert len(core.FEATURES) == 42 and len(set(core.FEATURES)) == 42


def test_hgb_matches_ground_truth_within_tolerance(features, truth):
    model, m = core.train_and_evaluate(features)
    ref = truth["ml"]["metrics_approximate"]["hist_gradient_boosting"]
    for split in ("valid", "test"):
        assert abs(m[split]["pr_auc"] - ref[split]["pr_auc"]) < 0.03
        assert abs(m[split]["roc_auc"] - ref[split]["roc_auc"]) < 0.03
    flat = core.mlflow_metrics(m)
    assert list(flat) == list(core.METRIC_KEYS)


def test_logistic_regression_and_baselines_are_stable(features, truth):
    _, m = core.train_and_evaluate(features, "logistic_regression")
    ref = truth["ml"]["metrics_approximate"]["logistic_regression"]
    assert abs(m["test"]["pr_auc"] - ref["test"]["pr_auc"]) < 0.005
    _, p = core.train_and_evaluate(features, "prevalence")
    assert abs(p["test"]["roc_auc"] - 0.5) < 1e-9
    rule = core.get_split(features, "test")
    s = core.rule_baseline_scores(rule)
    from sklearn.metrics import average_precision_score
    assert abs(average_precision_score(rule[core.LABEL], s) - truth["ml"]["metrics_approximate"]["rule_baseline"]["test"]["pr_auc"]) < 0.005


def test_reason_codes_equal_frozen_scores(features):
    frozen = pd.read_csv(REF / "ml_failure_risk_score.csv", dtype=str, keep_default_na=False)
    s = core.get_split(features, "score").copy()
    s["codes"] = core.reason_codes(s)
    got = dict(zip(s["erp_asset_id"], s["codes"]))
    assert len(frozen) == 264
    assert all(got[a] == c for a, c in zip(frozen["erp_asset_id"], frozen["top_drivers"]))


def test_score_latest_shape_and_bands(features):
    model = core.fit_final_model(features)
    sc = core.score_latest(features, model)
    assert len(sc) == 264 and sc["risk_rank"].tolist() == list(range(1, 265))
    assert set(sc["risk_band"]) <= {"High", "Medium", "Low"}
    assert (sc["risk_score"].diff().dropna() <= 1e-12).all()
    assert core.risk_band(0.30) == "High" and core.risk_band(0.0999) == "Low" and core.risk_band(0.10) == "Medium"


def test_psi_basics():
    rng = np.random.RandomState(0)
    a = rng.normal(0, 1, 5000)
    assert core.psi(a, rng.normal(0, 1, 5000)) < 0.05
    assert core.psi(a, rng.normal(2, 1, 5000)) > 0.25
    assert core.psi_status(0.05) == "stable" and core.psi_status(0.2) == "moderate" and core.psi_status(0.3) == "major"
