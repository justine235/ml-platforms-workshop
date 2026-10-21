# %% [markdown]
# # Local MLflow tour: same concepts, local backend
#
# This notebook is the rehearsal path for the Part 1 demo. It uses the shared
# fleet feature table with a local SQLite tracking backend and local artifacts so
# the presenter can prove the end-to-end MLflow concepts before switching to
# Fabric or Azure Machine Learning.

# %%
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import mlflow
import pandas as pd
from mlflow import MlflowClient
from mlflow.models import infer_signature

try:
    CODE_DIR = Path(__file__).resolve().parent
except NameError:
    # __file__ is not defined when this cell runs inside a Jupyter/VS Code
    # notebook kernel; fall back to the notebook's working directory, which
    # must be the code/ folder (the run-of-show tells presenters to open the
    # notebook from 03-demo-mlflow-tour\code).
    CODE_DIR = Path.cwd().resolve()
if not (CODE_DIR / "fleet_ml_core.py").exists():
    raise FileNotFoundError(
        "fleet_ml_core.py not found next to this notebook/script "
        f"(looked in {CODE_DIR}). Open the notebook from "
        "03-demo-mlflow-tour/code so its working directory is the code folder."
    )
ROOT = CODE_DIR.parents[1]
sys.path.insert(0, str(CODE_DIR))

import fleet_ml_core as core
import mlflow_compat as compat

FEATURES_PATH = ROOT / "02-demo-data" / "reference_out" / "ml_asset_day_features.csv.gz"
TRACKING_DB = CODE_DIR / "mlflow.db"
ARTIFACT_ROOT = CODE_DIR / "mlartifacts"
EXPERIMENT_NAME = "fleet-failure-7d-local-tour"

mlflow.set_tracking_uri(f"sqlite:///{TRACKING_DB.as_posix()}")
ARTIFACT_ROOT.mkdir(exist_ok=True)

# %% [markdown]
# ## 1. Point MLflow at a local database and artifact store
#
# The important idea is identical to Fabric and Azure ML:
# - the tracking URI tells MLflow where experiments and runs live
# - model artifacts live in a separate location
# - the same client API works once the URI changes

# %%
client = MlflowClient()
experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
artifact_uri = ARTIFACT_ROOT.resolve().as_uri()
if experiment is None:
    experiment_id = client.create_experiment(EXPERIMENT_NAME, artifact_location=artifact_uri)
else:
    experiment_id = experiment.experiment_id
mlflow.set_experiment(EXPERIMENT_NAME)
print({"tracking_uri": mlflow.get_tracking_uri(), "experiment_id": experiment_id, "artifact_uri": artifact_uri})

# %% [markdown]
# ## 2. Load the shared feature table
#
# The same input file also feeds the Fabric notebook and the Azure ML job. That
# is the portability story for the workshop: same data contract, same model code,
# different tracking backends.

# %%
df = core.load_features(FEATURES_PATH)
df[["erp_asset_id", "obs_date", "split", "fail_next_7d"]].head()

# %% [markdown]
# ## 3. Parent/child runs for the three model families
#
# This is open-source MLflow behavior. The same idea shows up in Fabric and AML:
# experiments contain runs; runs can be nested; params/metrics/artifacts live on
# each run. Here we compare:
# 1. prevalence dummy
# 2. logistic regression
# 3. hist gradient boosting

# %%
results = []
model_uris = {}
run_ids = {}
with mlflow.start_run(run_name="tour-parent") as parent:
    mlflow.set_tag("workshop", "fleet-mlflow-tour")
    mlflow.log_param("tour_mode", "manual_nested_runs")

    for kind in ("prevalence", "logistic_regression", "hist_gradient_boosting"):
        with mlflow.start_run(run_name=kind, nested=True) as child:
            model, metrics = core.train_and_evaluate(df, kind=kind)
            flat = core.mlflow_metrics(metrics)
            mlflow.log_param("model_kind", kind)
            mlflow.log_param("feature_count", len(core.FEATURES))
            mlflow.log_metrics(flat)
            for split_name, payload in metrics.items():
                for key, value in payload.items():
                    mlflow.log_metric(f"{split_name}_{key}", float(value))
            if kind in ("hist_gradient_boosting", "logistic_regression"):
                valid = core.get_split(df, "valid")
                signature = infer_signature(valid[core.FEATURES].head(20), model.predict(valid[core.FEATURES].head(20)))
                info = compat.log_sklearn_model(
                    model=model,
                    model_name="model",
                    signature=signature,
                    input_example=valid[core.FEATURES].head(5),
                    pip_requirements=compat.build_pip_requirements(
                        pandas_version=pd.__version__,
                        sklearn_version=__import__("sklearn").__version__,
                        mlflow_version=mlflow.__version__,
                        numpy_version=__import__("numpy").__version__,
                    ),
                )
                model_uris[kind] = getattr(info, "model_uri", f"runs:/{child.info.run_id}/model")
            results.append({"run_id": child.info.run_id, "model_kind": kind, **flat})
            run_ids[kind] = child.info.run_id

leaderboard = pd.DataFrame(results).sort_values(["test_pr_auc", "model_kind"], ascending=[False, True])
leaderboard

# %% [markdown]
# ## 4. Autologging versus manual logging
#
# Fabric enables autologging by default in data-science notebooks. Open-source
# MLflow and Azure ML make it opt-in. This cell shows the familiar OSS pattern:
# use `mlflow.autolog(log_models=False)` when you want framework capture, then
# call `log_model()` manually for a controlled model package.

# %%
mlflow.autolog(log_models=False, silent=True)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

train = core.get_split(df, "train")
valid = core.get_split(df, "valid")
with mlflow.start_run(run_name="autolog-logistic") as run:
    pipeline = make_pipeline(
        SimpleImputer(strategy="median", keep_empty_features=True),
        StandardScaler(),
        LogisticRegression(C=0.5, max_iter=2000),
    )
    pipeline.fit(train[core.FEATURES], train[core.LABEL])
    probs = pipeline.predict_proba(valid[core.FEATURES])[:, 1]
    mlflow.log_metric("valid_pr_auc_manual", core.eval_scores(valid[core.LABEL], probs)["pr_auc"])
    autolog_run_id = run.info.run_id
mlflow.autolog(disable=True, silent=True)
print({"autolog_run_id": autolog_run_id, "hint": "Inspect the run UI to see automatic params and estimator metadata."})

# %% [markdown]
# ## 5. Search runs and build a pandas leaderboard
#
# `search_runs` is the same core API everywhere. Only the backend changes.

# %%
search_df = mlflow.search_runs(
    experiment_ids=[experiment_id],
    output_format="pandas",
    order_by=["metrics.test_pr_auc DESC"],
)
search_df[["run_id", "tags.mlflow.runName", "metrics.test_pr_auc", "metrics.test_roc_auc"]].head(10)

# %% [markdown]
# ## 6. Inspect the saved model folder and explain `MLmodel`
#
# The MLflow model folder is the portable artifact. This is what you can move
# between local MLflow, Fabric, and Azure ML. Run history and lineage stay
# behind, but the `MLmodel` contract travels with the artifacts.

# %%
local_model_dir = CODE_DIR / "_tour_model_folder"
if local_model_dir.exists():
    shutil.rmtree(local_model_dir)
downloaded_path = mlflow.artifacts.download_artifacts(model_uris["hist_gradient_boosting"], dst_path=str(local_model_dir))
model_folder = Path(downloaded_path)
mlmodel_lines = (model_folder / "MLmodel").read_text(encoding="utf-8").splitlines()
pd.DataFrame(
    {
        "line": range(1, len(mlmodel_lines) + 1),
        "content": mlmodel_lines,
        "why_it_matters": [
            "Top-level metadata" if line.startswith("artifact_path:") else
            "Flavor section starts" if line.startswith("flavors:") else
            "Python function flavor lets any Python client load the model" if "python_function" in line else
            "sklearn flavor keeps native framework loading" if "sklearn" in line else
            "Dependencies are explicit" if "requirements.txt" in line else
            "Input/output contract is stored here" if "signature" in line else
            "Input example helps serving and testing" if "input_example" in line else
            ""
            for line in mlmodel_lines
        ],
    }
)

# %% [markdown]
# ## 7. Signature enforcement with `pyfunc`
#
# The signature is the contract that Fabric's `PREDICT` and many serving paths
# rely on. The easiest way to show its value live is to provoke a schema error.

# %%
pyfunc_model = mlflow.pyfunc.load_model(model_uris["hist_gradient_boosting"])
good_input = valid[core.FEATURES].head(3)
good_predictions = pyfunc_model.predict(good_input)
print("Good predictions:", good_predictions.tolist())

bad_input = good_input.drop(columns=["temp_mean"])
try:
    pyfunc_model.predict(bad_input)
except Exception as exc:
    print("Expected schema error:")
    print(type(exc).__name__, str(exc)[:400])

# %% [markdown]
# ## 8. Register model versions, tags, aliases, and stages
#
# This section intentionally shows the **open-source MLflow** registry surface:
# versions, aliases, tags, and stages all exist. Fabric and Azure ML differ:
# - Fabric documents **versions only** for ML model items
# - Azure ML supports stages through the MLflow SDK, but not as a first-class
#   Studio/CLI/SDK-v2 experience

# %%
registered_name = "fleet-failure-7d-local"
versions = []
for kind in ("hist_gradient_boosting", "logistic_regression"):
    version = mlflow.register_model(f"runs:/{run_ids[kind]}/model", registered_name)
    versions.append({"model_kind": kind, "version": version.version})
    client.set_model_version_tag(registered_name, version.version, "source_model_kind", kind)

alias_supported = compat.set_alias_if_supported(registered_name, versions[0]["version"], "champion")
stage_supported = compat.transition_stage_if_supported(registered_name, versions[0]["version"], "Staging")
registry_versions = client.search_model_versions(f"name = '{registered_name}'")
pd.DataFrame(
    [
        {
            "version": item.version,
            "current_stage": getattr(item, "current_stage", ""),
            "aliases": ",".join(getattr(item, "aliases", []) or []),
            "run_id": item.run_id,
            "source_model_kind": item.tags.get("source_model_kind", ""),
        }
        for item in registry_versions
    ]
).sort_values("version")

# %% [markdown]
# ## 9. Load by `models:/` URI and compare with run-based loading
#
# The `models:/` URI is the stable registry contract. The exact extra semantics
# differ by backend, but the core loading experience remains the same.

# %%
latest_model = mlflow.pyfunc.load_model(f"models:/{registered_name}/latest")
print("Registry prediction sample:", latest_model.predict(good_input).tolist())
if alias_supported:
    alias_model = mlflow.pyfunc.load_model(f"models:/{registered_name}@champion")
    print("Alias prediction sample:", alias_model.predict(good_input).tolist())
print({"alias_supported": alias_supported, "stage_supported": stage_supported})

# %% [markdown]
# ## 10. Same code, different backend
#
# The Python training script under `code/train_fleet_model.py` is the workshop's
# "same code, different backend" proof point:
# - local/open-source: `sqlite:///mlflow.db`
# - Fabric: workspace default or `sds://api.fabric.microsoft.com/v1/workspaces/<ws>/mlflow`
# - Azure ML: workspace `azureml://...` tracking URI, or automatic job context
#
# Only the tracking URI, auth, and registry semantics change.

# %%
backend_map = pd.DataFrame(
    [
        {"backend": "Open-source MLflow", "tracking_uri": "sqlite:///mlflow.db", "model_uri_example": "runs:/<run-id>/model"},
        {"backend": "Microsoft Fabric", "tracking_uri": "sds://api.fabric.microsoft.com/v1/workspaces/<workspace-id>/mlflow", "model_uri_example": "models:/fleet-failure-7d/1"},
        {"backend": "Azure Machine Learning", "tracking_uri": "azureml://subscriptions/.../workspaces/<name>", "model_uri_example": "models:/fleet-failure-7d/Staging"},
    ]
)
backend_map

# %% [markdown]
# ## 11. Cleanup note
#
# The local SQLite database and `mlartifacts` folder are safe to delete and
# recreate. That is deliberate: the live workshop can always fall back to this
# local rehearsal path if Fabric or AML is unavailable.
