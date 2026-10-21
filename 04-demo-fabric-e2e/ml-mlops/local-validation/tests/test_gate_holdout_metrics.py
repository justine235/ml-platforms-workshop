from __future__ import annotations

import tempfile

import mlflow
from mlflow.tracking import MlflowClient

from notebooks.notebook_common import get_holdout_metrics


def test_get_holdout_metrics_reads_logged_metrics_from_source_run() -> None:
    """get_holdout_metrics must read the metrics logged on each version's SOURCE run,
    never load or score a model. Uses a throwaway temp MLflow file store so this test
    needs no heavy training run."""
    with tempfile.TemporaryDirectory() as tmp:
        mlflow.set_tracking_uri(f"file:{tmp}/mlruns")
        client = MlflowClient()
        experiment_id = client.create_experiment("gate-holdout-metrics-test")
        model_name = "gate_holdout_metrics_test_model"

        champion_metrics = {
            "valid_pr_auc": 0.41,
            "valid_roc_auc": 0.80,
            "test_pr_auc": 0.38,
            "test_roc_auc": 0.78,
            "test_precision_at_top5pct": 0.40,
            "test_recall_at_top5pct": 0.22,
        }
        challenger_metrics = {
            "valid_pr_auc": 0.43,
            "valid_roc_auc": 0.81,
            "test_pr_auc": 0.40,
            "test_roc_auc": 0.79,
            "test_precision_at_top5pct": 0.39,
            "test_recall_at_top5pct": 0.23,
        }

        versions = []
        for metrics in (champion_metrics, challenger_metrics):
            run = client.create_run(experiment_id)
            run_id = run.info.run_id
            for key, value in metrics.items():
                client.log_metric(run_id, key, value)
            client.set_terminated(run_id, "FINISHED")
            model_uri = f"runs:/{run_id}/model"
            try:
                client.create_registered_model(model_name)
            except Exception:
                pass
            mv = client.create_model_version(model_name, model_uri, run_id)
            versions.append(mv.version)

        champion_version, challenger_version = versions
        read_champion = get_holdout_metrics(client, model_name, champion_version)
        read_challenger = get_holdout_metrics(client, model_name, challenger_version)

        assert read_champion == champion_metrics
        assert read_challenger == challenger_metrics
