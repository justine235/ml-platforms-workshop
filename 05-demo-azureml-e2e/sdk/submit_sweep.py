from __future__ import annotations

from pathlib import Path

from azure.ai.ml import MLClient, load_job
from azure.identity import DefaultAzureCredential

ROOT = Path(__file__).resolve().parents[1]


def submit_sweep(ml_client: MLClient):
    job = load_job(source=str(ROOT / "jobs" / "sweep-job.yml"))
    return ml_client.jobs.create_or_update(job)


if __name__ == "__main__":
    client = MLClient.from_config(DefaultAzureCredential())
    submit_sweep(client)
