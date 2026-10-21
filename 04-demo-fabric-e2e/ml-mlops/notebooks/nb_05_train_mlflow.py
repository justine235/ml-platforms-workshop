# %% [markdown]
# # nb_05_train_mlflow
#
# **What to say before you run this notebook:** this is the MLOps hinge point of the Fabric demo.
# We keep the model family simple on purpose and spend the time on tracking, comparison, signatures, artifacts, and repeatability.
# In Fabric notebooks, MLflow autologging is on by default. Here we switch to explicit logging so every nested run stays easy to explain live.

# %%
# Parameters
PARAMS = {
    "experiment_name": "fleet-failure-7d",
    "model_name": "fleet-failure-7d",
    "features_table": "ml.asset_day_features",
    "run_hyperparameter_search": False,
    "bootstrap_pointer_if_missing": True,
}

# %%
# Adapter
try:
    notebookutils  # noqa: B018 -- existence probe, not a useless expression
    IN_FABRIC = True
except NameError:
    IN_FABRIC = False

import json

import pandas as pd

from notebooks.notebook_common import (
    ProbabilityScoringClassifier,
    create_pr_curve_artifact,
    default_context,
    ensure_mlflow_experiment,
    feature_importance_frame,
    flatten_metrics,
    notebook_source_paths,
    read_model_pointer,
    upsert_model_pointer,
)
from notebooks.shared import fleet_ml_core

# %% [markdown]
# **What to say before the training block:** we log five child runs under one parent run.
# The audience sees the naive prevalence baseline, a rules-only baseline, two trained models, and one ablation.
# The registered model is the best architecture by validation PR-AUC, refit on every labelled day after the warm-up period.

# %%
def train_candidate(df: pd.DataFrame, *, kind: str, feature_cols: list[str], mlflow_module, run_name: str, context, client) -> dict:
    from mlflow.models import infer_signature

    valid_frame = fleet_ml_core.get_split(df, "valid")
    test_frame = fleet_ml_core.get_split(df, "test")
    train_frame = fleet_ml_core.get_split(df, *fleet_ml_core.TRAIN_SPLITS)

    with mlflow_module.start_run(run_name=run_name, nested=True) as child_run:
        mlflow_module.set_tags({"candidate_kind": run_name, "feature_count": len(feature_cols), "tracked_metrics": ",".join(fleet_ml_core.METRIC_KEYS)})
        if kind == "rule_baseline":
            valid_scores = fleet_ml_core.rule_baseline_scores(valid_frame)
            test_scores = fleet_ml_core.rule_baseline_scores(test_frame)
            metrics = {
                "valid": fleet_ml_core.eval_scores(valid_frame[fleet_ml_core.LABEL], valid_scores),
                "test": fleet_ml_core.eval_scores(test_frame[fleet_ml_core.LABEL], test_scores),
            }
            mlflow_module.log_params({"baseline": "rule", "rule_definition": "crit_cnt_7d > 0 or warn_cnt_7d >= 2"})
            artifact_path = context.write_json_artifact("rule-baseline-metrics.json", metrics)
            mlflow_module.log_artifact(str(artifact_path))
            return {"run_id": child_run.info.run_id, "metrics": metrics, "registered_version": None}

        estimator_kind = "hist_gradient_boosting" if kind == "hist_gradient_boosting_no_fault_codes" else kind
        model, metrics = fleet_ml_core.train_and_evaluate(df, kind=estimator_kind, features=feature_cols)
        final_estimator = fleet_ml_core.fit_final_model(df, kind=estimator_kind, features=feature_cols)
        wrapped = ProbabilityScoringClassifier(final_estimator)
        flat_metrics = flatten_metrics(metrics)
        mlflow_module.log_params({"estimator_kind": estimator_kind, "feature_subset": run_name, "feature_count": len(feature_cols)})
        mlflow_module.log_metrics(flat_metrics)

        valid_scores = model.predict_proba(valid_frame[feature_cols])[:, 1]
        pr_curve_path = create_pr_curve_artifact(
            valid_frame[fleet_ml_core.LABEL],
            valid_scores,
            context.artifact_dir / ("pr-curve-%s.png" % run_name),
        )
        mlflow_module.log_artifact(str(pr_curve_path), artifact_path="charts")

        importance = feature_importance_frame(model, valid_frame[feature_cols], valid_frame[fleet_ml_core.LABEL], feature_cols)
        importance_path = context.artifact_dir / ("importance-%s.csv" % run_name)
        importance.to_csv(importance_path, index=False, lineterminator="\n")
        mlflow_module.log_artifact(str(importance_path), artifact_path="importance")

        signature = infer_signature(train_frame[feature_cols].head(5), wrapped.predict(train_frame[feature_cols].head(5)))
        mlflow_module.sklearn.log_model(
            sk_model=wrapped,
            artifact_path="model",
            signature=signature,
            input_example=train_frame[feature_cols].head(5),
            code_paths=notebook_source_paths(),
        )
        return {"run_id": child_run.info.run_id, "metrics": metrics, "registered_version": None}


def run_hyperparameter_search(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for learning_rate in (0.04, 0.06, 0.08):
        for max_leaf_nodes in (16, 24, 32):
            _, metrics = fleet_ml_core.train_and_evaluate(
                df,
                kind="hist_gradient_boosting",
                learning_rate=learning_rate,
                max_leaf_nodes=max_leaf_nodes,
            )
            rows.append(
                {
                    "learning_rate": learning_rate,
                    "max_leaf_nodes": max_leaf_nodes,
                    "valid_pr_auc": metrics["valid"]["pr_auc"],
                    "test_pr_auc": metrics["test"]["pr_auc"],
                }
            )
    return pd.DataFrame(rows).sort_values(["valid_pr_auc", "test_pr_auc"], ascending=[False, False], kind="stable").reset_index(drop=True)


def run(params: dict | None = None, context=None) -> dict:
    params = {**PARAMS, **(params or {})}
    context = context or default_context(globals())
    mlflow, client = ensure_mlflow_experiment(context, params["experiment_name"])
    mlflow.autolog(disable=True, silent=True)

    features = context.read_table(params["features_table"])
    candidate_specs = [
        ("prevalence", list(fleet_ml_core.FEATURES)),
        ("rule_baseline", list(fleet_ml_core.FEATURES)),
        ("logistic_regression", list(fleet_ml_core.FEATURES)),
        ("hist_gradient_boosting", list(fleet_ml_core.FEATURES)),
        ("hist_gradient_boosting_no_fault_codes", list(fleet_ml_core.NO_FAULT_FEATURES)),
    ]
    child_results = {}

    with mlflow.start_run(run_name="nb_05_train_mlflow", tags={"demo_notebook": "nb_05_train_mlflow"}):
        for run_name, feature_cols in candidate_specs:
            child_results[run_name] = train_candidate(
                features,
                kind=run_name,
                feature_cols=feature_cols,
                mlflow_module=mlflow,
                run_name=run_name,
                context=context,
                client=client,
            )

        comparable = {
            name: payload
            for name, payload in child_results.items()
            if payload["metrics"]["valid"]["pr_auc"] is not None
        }
        best_name = max(comparable, key=lambda name: comparable[name]["metrics"]["valid"]["pr_auc"])
        best_run_id = comparable[best_name]["run_id"]
        registered = mlflow.register_model(model_uri="runs:/%s/model" % best_run_id, name=params["model_name"])
        client.set_model_version_tag(params["model_name"], registered.version, "candidate_status", "pending_gate")
        client.set_model_version_tag(params["model_name"], registered.version, "selected_by", "valid_pr_auc")
        client.set_model_version_tag(params["model_name"], registered.version, "candidate_kind", best_name)
        client.set_model_version_tag(params["model_name"], registered.version, "source_run_id", best_run_id)
        comparable[best_name]["registered_version"] = str(registered.version)

        comparison_rows = []
        for name, payload in child_results.items():
            flat = flatten_metrics(payload["metrics"])
            comparison_rows.append({"candidate": name, **flat})
        comparison = pd.DataFrame(comparison_rows).sort_values(["valid_pr_auc", "test_pr_auc"], ascending=[False, False], kind="stable")
        comparison_path = context.artifact_dir / "run-comparison.csv"
        comparison.to_csv(comparison_path, index=False, lineterminator="\n")
        mlflow.log_artifact(str(comparison_path), artifact_path="comparison")
        mlflow.log_params({"registered_candidate": best_name, "registered_version": registered.version})
        mlflow.set_tags({"registered_model_name": params["model_name"], "registered_model_version": registered.version})

        search_summary = None
        if params["run_hyperparameter_search"]:
            search_summary = run_hyperparameter_search(features)
            search_path = context.artifact_dir / "hyperparameter-search.csv"
            search_summary.to_csv(search_path, index=False, lineterminator="\n")
            mlflow.log_artifact(str(search_path), artifact_path="search")

    pointer_before = read_model_pointer(context)
    if params["bootstrap_pointer_if_missing"] and pointer_before[pointer_before["model_name"] == params["model_name"]].empty:
        upsert_model_pointer(
            context,
            model_name=params["model_name"],
            champion_version=str(registered.version),
            note="Bootstrapped because no champion pointer existed yet.",
            updated_by="nb_05_train_mlflow",
        )

    return {
        "experiment_name": params["experiment_name"],
        "model_name": params["model_name"],
        "registered_version": str(registered.version),
        "best_candidate": best_name,
        "child_runs": {name: {"run_id": payload["run_id"], **flatten_metrics(payload["metrics"])} for name, payload in child_results.items()},
        "hyperparameter_search_rows": 0 if search_summary is None else int(len(search_summary)),
    }


# %% [markdown]
# **What to say before the optional sweep:** Fabric Runtime 2.0 ships FLAML, Optuna, and SynapseML.
# This workshop keeps the search cell as a plain Python loop so the same logic runs locally, on Fabric Runtime 1.3, and on Runtime 2.0 without extra setup.

# %%
if __name__ == "__main__":
    RESULT = run()
    print(json.dumps(RESULT, indent=2, sort_keys=True))
