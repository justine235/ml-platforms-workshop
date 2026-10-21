# %% [markdown]
# # MLflow tour in Azure Machine Learning
#
# This notebook mirrors the local tour, but through Azure ML's MLflow-compatible
# workspace tracking server and model registry. It uses verified AML docs and
# marks notebook cells that still require tenant rehearsal as `⚠ UNVERIFIED`.
#
# Verified sources:
# - MLflow tracking config: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-use-mlflow-configure-tracking?view=azureml-api-2
# - Log MLflow models: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-log-mlflow-models?view=azureml-api-2
# - Manage MLflow models: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-manage-models-mlflow?view=azureml-api-2
# - MLflow batch deployment: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-mlflow-batch?view=azureml-api-2
# - MLflow online deployment: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-deploy-mlflow-models-online-endpoints?view=azureml-api-2

# %% [markdown]
# ## 1. Pin the compatible MLflow stack
#
# Azure ML currently documents compatibility with MLflow 2.16.x and earlier.
# The workshop should say this plainly because it is one of the biggest
# Fabric-vs-AML differences in 2026.

# %%
# %pip install "mlflow<=2.16.2" azureml-mlflow "xgboost<=2.1.1" scikit-learn pandas==2.2.3 matplotlib

# %% [markdown]
# ## 2. Compute instance or local notebook: fetch the workspace tracking URI
#
# In command jobs, AML configures tracking automatically. In a notebook or on a
# laptop, you fetch the workspace tracking URI and set it explicitly.

# %%
import mlflow
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
ml_client = MLClient.from_config(credential=credential)
workspace = ml_client.workspaces.get(ml_client.workspace_name)
mlflow.set_tracking_uri(workspace.mlflow_tracking_uri)
print({"workspace": ml_client.workspace_name, "tracking_uri": mlflow.get_tracking_uri()})

# %% [markdown]
# ## 3. Jobs configure tracking for you
#
# In an AML command job, the same training script can run unchanged without
# calling `set_tracking_uri()` because the `azureml-mlflow` plugin injects the
# run context automatically.

# %%
print(
    {
        "AZUREML_RUN_ID": __import__("os").environ.get("AZUREML_RUN_ID"),
        "message": "If AZUREML_RUN_ID is populated, job tracking is already wired in.",
    }
)

# %% [markdown]
# ## 4. Same code, different backend
#
# `⚠ UNVERIFIED`: this relative path assumes the workshop code is present on the
# compute instance or in the checked-out job code folder.

# %%
import sys
from pathlib import Path

CODE_DIR = Path("../code").resolve()
FEATURES_PATH = Path("../data/ml_asset_day_features.csv.gz").resolve()
sys.path.insert(0, str(CODE_DIR))

import train_fleet_model as train_script

args = train_script.parse_args(
    [
        "--features",
        str(FEATURES_PATH),
        "--experiment",
        "fleet-failure-7d",
        "--model-kind",
        "hist_gradient_boosting",
        "--register-name",
        "fleet-failure-7d",
        "--run-name",
        "aml-hgb-notebook",
    ]
)
# result = train_script.run_training(args)

# %% [markdown]
# ## 5. Manual logging with signature and input example
#
# Same MLflow concept, different backend:
# - params / metrics / artifacts / model package all log the same way
# - AML stores the run in the workspace tracking server
# - the model package stays portable because it is a standard MLflow model folder

# %%
# result = train_script.run_training(args)
# print(train_script.result_to_json(result))

# %% [markdown]
# ## 6. Registration options
#
# AML supports two complementary patterns:
# 1. `mlflow.register_model(...)` for run-first MLflow workflows
# 2. `MLClient.models.create_or_update(type="mlflow_model")` when you already
#    have a local MLflow model folder

# %%
# from mlflow import register_model
# registered = register_model("runs:/<run-id>/model", "fleet-failure-7d")
# print(registered.version)

# %%

# local_model = Model(
#     path="./downloaded-mlflow-model",
#     name="fleet-failure-7d",
#     type=AssetTypes.MLFLOW_MODEL,
# )
# ml_client.models.create_or_update(local_model)

# %% [markdown]
# ## 7. Stages, tags, and aliases
#
# Verified AML nuance:
# - model **stages** exist only through the MLflow SDK
# - stages are not first-class in AML Studio / CLI / SDK v2
# - deployment from a specific stage is not supported
# - model version tags are supported
# - aliases are `⚠ UNVERIFIED` in current AML docs, so do not make them a live dependency

# %%
from mlflow import MlflowClient

client = MlflowClient()
# client.transition_model_version_stage("fleet-failure-7d", version=1, stage="Staging")
# client.set_model_version_tag("fleet-failure-7d", version=1, key="owner", value="workshop")

# %% [markdown]
# ## 8. Loading models
#
# AML supports `models:/...` registry URIs for MLflow loading. The broader AML
# SDK also uses `azureml://` URIs for workspace assets and datastores; keep those
# concepts separate in the narration.

# %%
# pyfunc_model = mlflow.pyfunc.load_model("models:/fleet-failure-7d/1")
# predictions = pyfunc_model.predict(sample_df)

# %% [markdown]
# ## 9. Why MLflow-format models matter in AML
#
# The workshop line to say out loud:
# "If we log an MLflow model instead of a loose pickle, AML can deploy it to a
# managed online endpoint or batch endpoint without us writing a scoring script."
#
# That is the no-code deployment benefit Microsoft documents for MLflow-format
# models in AML.

# %% [markdown]
# ## 10. AML-specific differences to call out
#
# - AML pins `azureml-mlflow` to MLflow <= 2.16.2
# - LoggedModel and tracing features from MLflow 3 are not supported
# - stages exist, but only through the MLflow SDK
# - deployment from a stage is not supported
# - run tracking is automatic inside AML jobs

# %% [markdown]
# ## 11. Live-demo fallback
#
# If the live workspace has permission or quota issues:
# 1. show a prebuilt run in AML Studio
# 2. switch to the local notebook for the API concepts
# 3. use `job-train-fleet.yml` as the reproducible command-job handoff
