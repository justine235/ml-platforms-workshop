"""Compatibility helpers for MLflow 2.12.x, 2.16.x, 2.22.x, and 3.x.

The workshop uses the same training script on a laptop, in Microsoft Fabric,
and in Azure Machine Learning. The core MLflow concepts stay the same, but a
few APIs move between MLflow 2.x and 3.x:

* `mlflow.<flavor>.log_model(..., artifact_path="model")` is the stable
  MLflow 2.x call pattern.
* MLflow 3 introduces `name="model"` for LoggedModel-centric workflows.
  The legacy `artifact_path` argument still works, but this helper uses the
  documented 3.x shape so the differences are explicit in code and tests.
* Fabric notebooks can be upgraded to MLflow 3, while Azure ML currently pins
  `azureml-mlflow` to MLflow 2.16.2 or earlier.
* MLflow 3's sklearn flavor serializes with `skops` by default instead of
  pickle/cloudpickle. `skops` refuses to reload a few scikit-learn internal
  types unless they are explicitly marked trusted. `HistGradientBoosting*`
  is one of them (empirically confirmed: see `validation/matrix.md`), so this
  module whitelists the specific type needed by this workshop's model core.
"""
from __future__ import annotations

import os
from typing import Any

import mlflow


def _parse_version(text: str) -> tuple[int, ...]:
    parts = []
    for piece in text.split("."):
        digits = "".join(ch for ch in piece if ch.isdigit())
        if not digits:
            break
        parts.append(int(digits))
    return tuple(parts or [0])


def current_version() -> str:
    return getattr(mlflow, "__version__", "0")


def is_mlflow_3(version_text: str | None = None) -> bool:
    return _parse_version(version_text or current_version()) >= (3, 0)


def model_log_path_kwargs(model_name: str, version_text: str | None = None) -> dict[str, str]:
    """Return the flavor-specific keyword used by log_model().

    MLflow 3 documents `name=...`; MLflow 2.x uses `artifact_path=...`.
    We isolate the switch here so callers keep one code path.
    """
    if is_mlflow_3(version_text):
        return {"name": model_name}
    return {"artifact_path": model_name}


def detect_platform(env: dict[str, str] | None = None, tracking_uri: str | None = None) -> str:
    env = env or os.environ
    uri = tracking_uri or env.get("MLFLOW_TRACKING_URI") or ""
    if uri.startswith("sds://") or env.get("FABRIC_WORKSPACE_ID") or env.get("FABRIC_ENVIRONMENT_NAME"):
        return "fabric"
    if env.get("AZUREML_RUN_ID") or env.get("AZUREML_ARM_SUBSCRIPTION") or uri.startswith("azureml://"):
        return "azureml"
    return "local"


def configure_tracking(tracking_uri: str | None = None) -> str | None:
    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)
    return mlflow.get_tracking_uri()


def set_experiment(name: str) -> Any:
    return mlflow.set_experiment(name)


# scikit-learn class name -> skops trusted-type strings it needs to reload.
# Empirically confirmed on MLflow 3.17.0 / scikit-learn 1.6.1: see
# `validation/matrix.md` for the exact error this avoids.
_SKOPS_TRUSTED_TYPES: dict[str, list[str]] = {
    "HistGradientBoostingClassifier": [
        "sklearn.ensemble._hist_gradient_boosting.predictor.TreePredictor",
    ],
    "HistGradientBoostingRegressor": [
        "sklearn.ensemble._hist_gradient_boosting.predictor.TreePredictor",
    ],
}


def skops_trusted_types_for(model: Any) -> list[str]:
    """Return the skops trusted-type names needed to reload this fitted model.

    Only matters on MLflow 3.x, where the sklearn flavor saves with skops by
    default. Returns an empty list for model kinds that do not need it (for
    example `prevalence` or `logistic_regression` in this workshop).
    """
    class_names = [type(model).__name__]
    steps = getattr(model, "steps", None)
    if steps:
        class_names.extend(type(step).__name__ for _, step in steps)
    trusted: list[str] = []
    for class_name in class_names:
        trusted.extend(_SKOPS_TRUSTED_TYPES.get(class_name, []))
    return trusted


def log_sklearn_model(
    *,
    model: Any,
    model_name: str,
    signature: Any,
    input_example: Any,
    pip_requirements: list[str],
) -> Any:
    import mlflow.sklearn

    kwargs: dict[str, Any] = {
        "sk_model": model,
        "signature": signature,
        "input_example": input_example,
        "pip_requirements": pip_requirements,
    }
    kwargs.update(model_log_path_kwargs(model_name))
    if is_mlflow_3():
        trusted = skops_trusted_types_for(model)
        if trusted:
            kwargs["skops_trusted_types"] = trusted
    return mlflow.sklearn.log_model(**kwargs)


def register_model(model_uri: str, registered_name: str) -> Any:
    return mlflow.register_model(model_uri=model_uri, name=registered_name)


def set_version_tags(model_name: str, version: str | int, tags: dict[str, str]) -> None:
    client = mlflow.tracking.MlflowClient()
    for key, value in sorted(tags.items()):
        client.set_model_version_tag(model_name, str(version), key, value)


def set_alias_if_supported(model_name: str, version: str | int, alias: str) -> bool:
    client = mlflow.tracking.MlflowClient()
    if not hasattr(client, "set_registered_model_alias"):
        return False
    client.set_registered_model_alias(model_name, alias, str(version))
    return True


def transition_stage_if_supported(model_name: str, version: str | int, stage: str) -> bool:
    client = mlflow.tracking.MlflowClient()
    if not hasattr(client, "transition_model_version_stage"):
        return False
    client.transition_model_version_stage(model_name, str(version), stage=stage)
    return True


def build_pip_requirements(
    *,
    pandas_version: str,
    sklearn_version: str,
    mlflow_version: str,
    numpy_version: str,
    extra_requirements: list[str] | None = None,
) -> list[str]:
    reqs = [
        f"mlflow=={mlflow_version}",
        f"numpy=={numpy_version}",
        f"pandas=={pandas_version}",
        f"scikit-learn=={sklearn_version}",
        "cloudpickle>=2.2,<4",
        "scipy>=1.11,<2",
    ]
    if extra_requirements:
        reqs.extend(extra_requirements)
    return reqs