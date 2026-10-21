from __future__ import annotations


def test_fabric_mode_does_not_create_experiment_with_artifact_location(tmp_path, monkeypatch):
    """Fabric's MLflow artifact store is managed by the service: ensure_mlflow_experiment
    must not pass an explicit local-mode artifact_location to client.create_experiment
    when context.mode == "fabric" (mlflow.set_experiment may still create the Experiment
    item itself -- that is the documented, Fabric-correct path)."""
    import mlflow

    from notebooks.notebook_common import NotebookContext, ensure_mlflow_experiment

    mlflow.set_tracking_uri("sqlite:///%s" % (tmp_path / "mlflow.db").as_posix())

    calls = []
    real_create_experiment = mlflow.MlflowClient.create_experiment

    def spy_create_experiment(self, *args, **kwargs):
        calls.append(kwargs)
        return real_create_experiment(self, *args, **kwargs)

    monkeypatch.setattr(mlflow.MlflowClient, "create_experiment", spy_create_experiment)

    context = NotebookContext(
        mode="fabric",
        reference_dir=tmp_path,
        artifact_dir=tmp_path / "artifacts",
        output_dir=tmp_path / "output",
    )
    ensure_mlflow_experiment(context, "fleet-failure-7d-fabric-test")

    assert all("artifact_location" not in kwargs for kwargs in calls)
    assert mlflow.get_experiment_by_name("fleet-failure-7d-fabric-test") is not None