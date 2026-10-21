from __future__ import annotations

from pathlib import Path

from azure.ai.ml import Input, MLClient, load_batch_deployment, load_batch_endpoint
from azure.identity import DefaultAzureCredential

ROOT = Path(__file__).resolve().parents[1]


def deploy_batch(ml_client: MLClient):
    endpoint = load_batch_endpoint(source=str(ROOT / "endpoints" / "batch-endpoint.yml"))
    deployment = load_batch_deployment(source=str(ROOT / "endpoints" / "batch-deployment.yml"))
    ml_client.batch_endpoints.begin_create_or_update(endpoint).result()
    return ml_client.batch_deployments.begin_create_or_update(deployment).result()


def invoke_batch(ml_client: MLClient, input_path: str):
    return ml_client.batch_endpoints.invoke(
        endpoint_name="fleet-risk-batch",
        deployment_name="default",
        input=Input(path=input_path, type="uri_file"),
    )


if __name__ == "__main__":
    client = MLClient.from_config(DefaultAzureCredential())
    deploy_batch(client)
