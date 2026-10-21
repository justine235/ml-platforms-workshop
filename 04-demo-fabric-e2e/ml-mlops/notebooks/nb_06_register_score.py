# %% [markdown]
# # nb_06_register_score
#
# **What to say before you run this notebook:** in Fabric the registered model is versions-only.
# There are no built-in stages or aliases in the workshop contract, so we keep the active champion in a small pointer table (`ml.model_pointer`).
# This notebook reads that pointer, scores the latest day, and writes the operational risk table that downstream reporting can consume.

# %%
# Parameters
PARAMS = {
    "experiment_name": "fleet-failure-7d",
    "model_name": "fleet-failure-7d",
    "model_version": None,
    "features_table": "ml.asset_day_features",
    "asset_table": "gold.dim_asset",
    "pointer_table": "ml.model_pointer",
    "output_table": "ml.failure_risk_score",
    "compare_to_frozen_reference": True,
    "reference_scores_name": "ml_failure_risk_score",
    "run_spark_transformer": False,
}

# %%
# Adapter
try:
    notebookutils  # noqa: B018 -- existence probe, not a useless expression
    IN_FABRIC = True
except NameError:
    IN_FABRIC = False

import json

import numpy as np

from notebooks.notebook_common import (
    default_context,
    ensure_mlflow_experiment,
    load_pyfunc_scores,
    load_sklearn_model,
    read_model_pointer,
    resolve_model_version,
)
from notebooks.shared import fleet_ml_core

# %% [markdown]
# **What to say before the scoring block:** we use two paths.
# The live path here is local pandas plus the registered MLflow model.
# A second Fabric-only cell shows the `MLFlowTransformer` pattern on Spark.
# `PREDICT` uses the same model-signature idea and is why the training notebook logged a signature.

# %%
def score_with_mlflow_transformer(context, score_frame, model_name: str, model_version: str) -> dict:
    if context.mode != "fabric":
        return {"executed": False, "reason": "local_context"}
    if not score_frame.empty:
        try:
            from synapse.ml.predict import MLFlowTransformer
        except ImportError as exc:
            return {"executed": False, "reason": "synapseml_missing", "detail": str(exc)}
        transformer = MLFlowTransformer(
            inputCols=list(fleet_ml_core.FEATURES),
            outputCol="risk_score",
            modelName=model_name,
            modelVersion=int(model_version),
        )
        spark_input = context.spark.createDataFrame(score_frame[["erp_asset_id", "obs_date", *fleet_ml_core.FEATURES]])
        transformed = transformer.transform(spark_input).toPandas()
        return {"executed": True, "rows": int(len(transformed)), "columns": list(transformed.columns)}
    return {"executed": False, "reason": "empty_score_frame"}


def run(params: dict | None = None, context=None) -> dict:
    params = {**PARAMS, **(params or {})}
    context = context or default_context(globals())
    _, client = ensure_mlflow_experiment(context, params["experiment_name"])

    features = context.read_table(params["features_table"])
    dim_asset = context.read_table(params["asset_table"])
    pointer = read_model_pointer(context, table_name=params["pointer_table"])
    model_version = resolve_model_version(client, params["model_name"], params["model_version"], pointer)
    model_uri = "models:/%s/%s" % (params["model_name"], model_version)

    scoring_model = load_sklearn_model(model_uri)
    score_frame = fleet_ml_core.get_split(features, "score").copy()
    pyfunc_scores = load_pyfunc_scores(model_uri, score_frame[fleet_ml_core.FEATURES])
    sklearn_scores = scoring_model.predict_proba(score_frame[fleet_ml_core.FEATURES])[:, 1]
    score_frame["risk_score"] = pyfunc_scores.round(4)
    score_frame["risk_band"] = [fleet_ml_core.risk_band(score) for score in score_frame["risk_score"]]
    score_frame["top_drivers"] = fleet_ml_core.reason_codes(score_frame)
    result_table = score_frame.merge(
        dim_asset[["erp_asset_id", "site_code", "equipment_class"]].drop_duplicates(),
        on="erp_asset_id",
        how="left",
    )
    result_table = result_table.rename(columns={"obs_date": "score_date"})
    result_table["model_version"] = str(model_version)
    result_table = result_table[["score_date", "erp_asset_id", "site_code", "equipment_class", "risk_score", "risk_band", "top_drivers", "model_version"]]
    result_table = result_table.sort_values(["risk_score", "erp_asset_id"], ascending=[False, True], kind="stable").reset_index(drop=True)
    result_table["risk_rank"] = np.arange(1, len(result_table) + 1)
    result_table = result_table[
        ["score_date", "erp_asset_id", "site_code", "equipment_class", "risk_score", "risk_band", "risk_rank", "top_drivers", "model_version"]
    ]
    context.write_table(params["output_table"], result_table)

    summary = {
        "model_version": str(model_version),
        "rows": int(len(result_table)),
        "bands": {str(k): int(v) for k, v in result_table["risk_band"].value_counts().sort_index().items()},
        "pyfunc_vs_sklearn_max_abs_diff": round(float(np.max(np.abs(pyfunc_scores - sklearn_scores))), 8),
        "spark_transformer": score_with_mlflow_transformer(context, score_frame, params["model_name"], str(model_version))
        if params["run_spark_transformer"]
        else {"executed": False, "reason": "disabled"},
    }

    if params["compare_to_frozen_reference"]:
        if context.has_reference(params["reference_scores_name"]):
            reference = context.read_reference(params["reference_scores_name"])
            merged = result_table.merge(reference, on="erp_asset_id", suffixes=("_actual", "_expected"))
            reason_code_match = int((merged["top_drivers_actual"] == merged["top_drivers_expected"]).sum())
            band_match = int((merged["risk_band_actual"] == merged["risk_band_expected"]).sum())
            summary["frozen_reference_comparison"] = {
                "rows": int(len(merged)),
                "reason_code_matches": reason_code_match,
                "reason_code_total": int(len(merged)),
                "risk_band_matches": band_match,
                "risk_band_total": int(len(merged)),
                "note": "Bands can move across library versions; rule-based reason codes must stay exact.",
            }
        else:
            # A real Fabric workspace has no reference_out files; this comparison only
            # ever runs against the local-validation fixture.
            summary["frozen_reference_comparison"] = {"skipped": "no reference files in this workspace"}

    return summary


# %% [markdown]
# **What to say before you move on:** Part 4 does not consume this live table.
# It loads the frozen `reference_out/ml_failure_risk_score.csv` so the agent answers stay stable across runtimes.
# That is honest MLOps: live scoring for the workshop, frozen downstream fixtures for reproducible question answering.

# %%
if __name__ == "__main__":
    RESULT = run()
    print(json.dumps(RESULT, indent=2, sort_keys=True))
