from pathlib import Path

from azure.ai.ml import Input, MLClient, load_component
from azure.ai.ml.dsl import pipeline
from azure.identity import DefaultAzureCredential

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = ROOT / "jobs" / "components"
# train.py calls mlflow.set_experiment(); inside an AML job it must match the job's own experiment.
EXPERIMENT_NAME = "fleet-failure-7d"


def build_pipeline_job(raw_features_path: str, champion_metrics_path: str, git_sha: str = "local-dev"):
    prep = load_component(source=str(COMPONENTS / "prep.yml"))
    train = load_component(source=str(COMPONENTS / "train.yml"))
    evaluate = load_component(source=str(COMPONENTS / "evaluate.yml"))
    gate = load_component(source=str(COMPONENTS / "gate.yml"))
    register = load_component(source=str(COMPONENTS / "register.yml"))

    # No "from __future__ import annotations" in this module: the DSL reads __annotations__ as real types.
    @pipeline(default_compute="cpu-cluster")
    def fleet_pipeline(raw_features: Input, champion_metrics: Input, build_git_sha: str):
        prep_step = prep(input_data=raw_features)
        train_step = train(
            input_data=prep_step.outputs.prepared_data,
            experiment_name=EXPERIMENT_NAME,
            data_version="fleet-asset-day-features-reference:1",
            git_sha=build_git_sha,
            learning_rate=0.06,
            max_leaf_nodes=24,
            l2_regularization=1.0,
        )
        evaluate_step = evaluate(
            input_data=prep_step.outputs.prepared_data,
            model_path=train_step.outputs.model_output,
            train_metrics_json=train_step.outputs.metrics_output,
            champion_json=champion_metrics,
        )
        gate_step = gate(
            challenger_json=evaluate_step.outputs.evaluation_output,
            champion_json=champion_metrics,
        )
        register(
            train_manifest=train_step.outputs.metrics_output,
            evaluation_json=evaluate_step.outputs.evaluation_output,
            gate_json=gate_step.outputs.gate_output,
        )

    job = fleet_pipeline(
        raw_features=Input(path=raw_features_path, type="uri_file"),
        champion_metrics=Input(path=champion_metrics_path, type="uri_file"),
        build_git_sha=git_sha,
    )
    job.experiment_name = EXPERIMENT_NAME
    return job


def submit_pipeline(ml_client: MLClient, raw_features_path: str, champion_metrics_path: str, git_sha: str = "local-dev"):
    job = build_pipeline_job(raw_features_path, champion_metrics_path, git_sha=git_sha)
    return ml_client.jobs.create_or_update(job)


if __name__ == "__main__":
    client = MLClient.from_config(DefaultAzureCredential())
    submit_pipeline(
        client,
        "azureml:fleet-asset-day-features-reference:1",
        "azureml:fleet-champion-metrics:1",
    )
