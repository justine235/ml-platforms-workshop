# %% [markdown]
# # nb_08_promotion_gate
#
# **What to say before you run this notebook:** Fabric model items have versions, not stages or aliases.
# The supported workshop pattern is simple: keep the metadata on the model version, and keep the active champion in a small pointer table (`ml.model_pointer`).
# This notebook compares champion and challenger on their already-logged holdout metrics and returns a promotion decision as JSON.

# %%
# Parameters
PARAMS = {
    "experiment_name": "fleet-failure-7d",
    "model_name": "fleet-failure-7d",
    "pointer_table": "ml.model_pointer",
    "champion_version": None,
    "challenger_version": None,
    # Report-only by default: the pipeline computes a decision but never moves the
    # pointer unless a human (or an explicitly configured auto-promote activity
    # parameter) sets this to True. See README/rebuild-guide for the rationale.
    "apply_pointer_update": False,
    "emit_notebook_exit": True,
}

# %%
# Adapter
try:
    notebookutils  # noqa: B018 -- existence probe, not a useless expression
    IN_FABRIC = True
except NameError:
    IN_FABRIC = False

import json

from notebooks.notebook_common import (
    default_context,
    ensure_mlflow_experiment,
    gate_decision,
    get_holdout_metrics,
    get_model_versions,
    read_model_pointer,
    resolve_model_version,
    upsert_model_pointer,
)

# %% [markdown]
# **What to say before the gate logic:** the guardrail is intentionally small.
# We only promote when test PR-AUC improves by at least 0.01 and precision in the top 5% does not get worse by more than 0.02.
# That keeps the conversation concrete and honest for a live workshop.
#
# **Why this notebook does not re-score any model:** the registered model artifact is refit on
# every labelled split (train+gap+valid+test, see `fleet_ml_core.fit_final_model`) before it is
# used to score brand-new unlabeled days -- intentional, standard practice before scoring. Because
# that artifact has already seen the "test" rows, re-scoring it on the "test" split would be
# in-sample and would not measure generalization. The gate therefore reads the holdout metrics
# logged with the registered version instead of re-scoring the model on training data: the
# `test_pr_auc` / `test_precision_at_top5pct` metrics that `nb_05_train_mlflow` already logged on
# each model version's SOURCE run -- the architecture comparison run, evaluated BEFORE the final
# refit-on-everything -- are an honest holdout measurement. No model is loaded or scored here.

# %%
def run(params: dict | None = None, context=None) -> dict:
    params = {**PARAMS, **(params or {})}
    context = context or default_context(globals())
    _, client = ensure_mlflow_experiment(context, params["experiment_name"])
    pointer = read_model_pointer(context, table_name=params["pointer_table"])
    versions = get_model_versions(client, params["model_name"])
    if not versions:
        raise ValueError("No registered versions found for %s." % params["model_name"])

    challenger_version = params["challenger_version"] or str(versions[-1].version)
    champion_version = params["champion_version"]
    if champion_version is None:
        existing = pointer.loc[pointer["model_name"] == params["model_name"], "champion_version"]
        champion_version = None if existing.empty else str(existing.iloc[-1])

    if champion_version is None:
        bootstrap = {
            "decision": "promote",
            "passed": True,
            "reason": "no_existing_champion",
            "champion_version": None,
            "challenger_version": str(challenger_version),
            "metrics_source": "no champion yet -- nothing to compare against",
        }
        if params["apply_pointer_update"]:
            upsert_model_pointer(
                context,
                model_name=params["model_name"],
                champion_version=str(challenger_version),
                note="Bootstrap champion because none existed yet.",
            )
        if params["emit_notebook_exit"]:
            context.notebook_exit(bootstrap)
        return bootstrap

    champion_version = resolve_model_version(client, params["model_name"], champion_version, pointer)
    if champion_version == challenger_version and len(versions) > 1:
        challenger_version = str(versions[-1].version if str(versions[-1].version) != champion_version else versions[-2].version)

    champion_metrics = get_holdout_metrics(client, params["model_name"], str(champion_version))
    challenger_metrics = get_holdout_metrics(client, params["model_name"], str(challenger_version))

    decision = gate_decision(champion_metrics, challenger_metrics)
    decision.update(
        {
            "champion_version": str(champion_version),
            "challenger_version": str(challenger_version),
            "champion_metrics": champion_metrics,
            "challenger_metrics": challenger_metrics,
            "metrics_source": "logged holdout metrics of the source run; model fit on train splits only",
        }
    )

    if params["apply_pointer_update"] and decision["passed"]:
        upsert_model_pointer(
            context,
            model_name=params["model_name"],
            champion_version=str(challenger_version),
            note="Promoted by nb_08_promotion_gate: challenger beat the champion on logged holdout metrics.",
        )

    if params["emit_notebook_exit"]:
        context.notebook_exit(decision)
    return decision


# %%
if __name__ == "__main__":
    RESULT = run()
    print(json.dumps(RESULT, indent=2, sort_keys=True))
