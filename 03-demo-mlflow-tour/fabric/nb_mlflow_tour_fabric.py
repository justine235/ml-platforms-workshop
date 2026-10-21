# %% [markdown]
# # MLflow tour in Microsoft Fabric
#
# This notebook mirrors the local MLflow tour, but through Fabric's notebook,
# experiment, and ML model item experiences. It is written from verified docs
# plus clearly marked `⚠ UNVERIFIED` cells for tenant-specific or UI-specific
# checks that cannot be executed from this machine.
#
# Verified sources used directly in this notebook:
# - Runtime 2.0: https://learn.microsoft.com/en-us/fabric/data-engineering/runtime-2-0
# - MLflow 3 in Fabric: https://learn.microsoft.com/en-us/fabric/data-science/mlflow-3-overview
# - Autologging: https://learn.microsoft.com/en-us/fabric/data-science/mlflow-autologging
# - Experiment items: https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-experiment
# - ML model items: https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-model
# - Cross-workspace tracking: https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-cross-workspace-logging
# - Batch scoring with PREDICT / MLFlowTransformer: https://learn.microsoft.com/en-us/fabric/data-science/model-scoring-predict

# %% [markdown]
# ## 1. Check the preinstalled runtime and MLflow version
#
# Fabric Runtime 2.0 documents Python 3.13 and Runtime 1.3 remains the LTS path.
# The workshop callout is:
# - Runtime 1.3 LTS: `mlflow-skinny 2.12.2`
# - Runtime 2.0: `mlflow-skinny 2.22.0`
# - MLflow 3 is supported in Fabric, but must be installed explicitly

# %%
import mlflow
import pandas as pd
import sklearn

print(
    {
        "mlflow": mlflow.__version__,
        "pandas": pd.__version__,
        "sklearn": sklearn.__version__,
    }
)

# %% [markdown]
# ## 2. Optional notebook-scoped upgrade to MLflow 3
#
# Fabric docs say notebooks ship with MLflow 2.x by default and show this exact
# upgrade pattern for MLflow 3 / LoggedModels / Traces.

# %%
# %pip install "synapseml-mlflow[online-notebook]>=2.0.3" "mlflow-skinny==3.1.0" "opentelemetry-api<=1.40.0"
# NOTE: restart the Python session after a %pip install in Fabric.

# %% [markdown]
# ## 3. Experiments and autologging
#
# Verified Fabric behavior:
# - Data-science notebooks enable autologging by default
# - Experiment items are the run container in the UI
# - Manual logging still works; use it when you need a controlled signature,
#   input example, or explicit pip requirements

# %%
mlflow.set_experiment("fleet-failure-7d")
print("Experiment configured:", "fleet-failure-7d")

# %% [markdown]
# ## 4. Same code, different backend
#
# The workshop's main proof point is that the same training script can run
# unchanged on:
# - a laptop
# - a Fabric notebook
# - an Azure ML job
#
# `⚠ UNVERIFIED`: the exact lakehouse/repo path below depends on how you copy
# the workshop folder into Fabric. Rehearse the path before Friday.

# %%
# ⚠ UNVERIFIED: adjust this path to where you copied 03-demo-mlflow-tour/code.
import sys
from pathlib import Path

CODE_DIR = Path("/lakehouse/default/Files/workshop/03-demo-mlflow-tour/code")
FEATURES_PATH = Path("/lakehouse/default/Files/workshop/02-demo-data/reference_out/ml_asset_day_features.csv.gz")
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
        "--run-name",
        "fabric-notebook-hgb",
    ]
)
# result = train_script.run_training(args)

# %% [markdown]
# ## 5. Manual logging with model signature and input example
#
# This is the behavior to call out live:
# - params, metrics, tags, and artifacts show up in the run
# - the saved model carries a signature and input example
# - the run can then be promoted to an **ML model** item

# %%
# result = train_script.run_training(args)
# print(train_script.result_to_json(result))

# %% [markdown]
# ## 6. Fabric registration model
#
# Verified Fabric model-management facts:
# - Fabric ML model items are **versions only**
# - current docs do **not** document stages or aliases as a primary Fabric model-item pattern
# - registration still uses standard MLflow registration calls

# %%
# Example: register a model from a finished run.
# model_version = mlflow.register_model("runs:/<run-id>/model", "fleet-failure-7d")
# print(model_version)

# %% [markdown]
# ## 7. Load from the Fabric registry
#
# Verified path: `models:/<name>/<version>`.

# %%
# loaded = mlflow.pyfunc.load_model("models:/fleet-failure-7d/1")
# sample_predictions = loaded.predict(...)

# %% [markdown]
# ## 8. Compare runs in the UI
#
# In the Fabric demo, show:
# 1. the experiment item
# 2. multiple runs selected
# 3. **Compare** in the ribbon
# 4. params / metrics / artifacts / model signature
#
# `⚠ UNVERIFIED`: exact button placement can shift with monthly UI updates. Rehearse it in the target tenant.

# %% [markdown]
# ## 9. Minimal batch scoring examples
#
# `PREDICT` and `MLFlowTransformer` both require an MLflow-format model with a
# usable signature. The full end-to-end scoring chain lives in builder B2b's
# `nb_06_register_score`; keep this notebook to the minimal concept demo.

# %%
# SQL-style concept:
# PREDICT(
#   MODEL `fleet-failure-7d`,
#   VERSION 1,
#   INPUT TABLE `ml.asset_day_features`
# )

# %%
from synapse.ml.predict import MLFlowTransformer

# Minimal Spark scoring snippet for a registered Fabric model version.
# This is the same idea used in the end-to-end demo notebook.
scorer = MLFlowTransformer(
    inputCols=["temp_mean", "temp_max", "oil_mean"],  # trim for readability here
    outputCol="prediction",
    modelName="fleet-failure-7d",
    modelVersion=1,
)
# predictions = scorer.transform(spark_df)

# %% [markdown]
# ## 10. Cross-workspace tracking
#
# Verified Fabric tracking URI format:
# `sds://api.fabric.microsoft.com/v1/workspaces/<workspace-id>/mlflow`
#
# The key message: same MLflow client, different tracking URI.

# %%
# target_uri = "sds://api.fabric.microsoft.com/v1/workspaces/<target-workspace-id>/mlflow"
# mlflow.set_tracking_uri(target_uri)
# mlflow.set_experiment("fleet-failure-7d")

# %% [markdown]
# ## 11. What is unsupported or different in Fabric
#
# - MLflow 3 features require an explicit `%pip install`
# - Git/deployment pipeline support for experiments/models is metadata-only
# - current docs describe model **versions**, not stages/aliases, for ML model items
# - model endpoints are `⚠ PREVIEW`
# - `PREDICT` / `MLFlowTransformer` require a signature

# %% [markdown]
# ## 12. Live-demo fallback
#
# If Fabric is slow or unavailable:
# 1. show the local notebook first
# 2. switch to the Fabric experiment UI and a prebuilt run
# 3. point to builder B2b's `nb_06_register_score` for the full scoring chain
