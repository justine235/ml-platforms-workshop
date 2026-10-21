from __future__ import annotations

import sys
from pathlib import Path

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

CODE_DIR = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(CODE_DIR))

import mlflow_compat as compat


def test_model_log_path_kwargs_switches_between_2x_and_3x():
    assert compat.model_log_path_kwargs("model", "2.22.0") == {"artifact_path": "model"}
    assert compat.model_log_path_kwargs("model", "3.1.0") == {"name": "model"}


def test_detect_platform_prefers_explicit_backend_clues():
    assert compat.detect_platform({"FABRIC_WORKSPACE_ID": "abc"}) == "fabric"
    assert compat.detect_platform({"AZUREML_RUN_ID": "run-1"}) == "azureml"
    assert compat.detect_platform({}, "sds://api.fabric.microsoft.com/v1/workspaces/ws/mlflow") == "fabric"
    assert compat.detect_platform({}, "azureml://subscriptions/x") == "azureml"
    assert compat.detect_platform({}) == "local"


def test_build_pip_requirements_pins_runtime_versions():
    reqs = compat.build_pip_requirements(
        pandas_version="2.2.3",
        sklearn_version="1.6.1",
        mlflow_version="2.22.0",
        numpy_version="2.1.3",
    )
    assert "mlflow==2.22.0" in reqs
    assert "pandas==2.2.3" in reqs
    assert "scikit-learn==1.6.1" in reqs


def test_skops_trusted_types_for_hist_gradient_boosting():
    model = HistGradientBoostingClassifier()
    trusted = compat.skops_trusted_types_for(model)
    assert trusted == ["sklearn.ensemble._hist_gradient_boosting.predictor.TreePredictor"]


def test_skops_trusted_types_for_pipeline_wrapping_hist_gradient_boosting():
    pipeline = Pipeline([("scale", StandardScaler()), ("clf", HistGradientBoostingClassifier())])
    trusted = compat.skops_trusted_types_for(pipeline)
    assert trusted == ["sklearn.ensemble._hist_gradient_boosting.predictor.TreePredictor"]


def test_skops_trusted_types_for_logistic_regression_is_empty():
    model = LogisticRegression()
    assert compat.skops_trusted_types_for(model) == []