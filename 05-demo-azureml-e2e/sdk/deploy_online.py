from __future__ import annotations

from pathlib import Path

from azure.ai.ml import MLClient, load_online_deployment, load_online_endpoint
from azure.identity import DefaultAzureCredential

ROOT = Path(__file__).resolve().parents[1]


def deploy_online(ml_client: MLClient):
    endpoint = load_online_endpoint(source=str(ROOT / "endpoints" / "online-endpoint.yml"))
    blue = load_online_deployment(source=str(ROOT / "endpoints" / "online-blue-deployment.yml"))
    green = load_online_deployment(source=str(ROOT / "endpoints" / "online-green-deployment.yml"))
    ml_client.online_endpoints.begin_create_or_update(endpoint).result()
    ml_client.online_deployments.begin_create_or_update(blue).result()
    ml_client.online_deployments.begin_create_or_update(green).result()
    endpoint.traffic = {"blue": 90, "green": 10}
    return ml_client.online_endpoints.begin_create_or_update(endpoint).result()


if __name__ == "__main__":
    client = MLClient.from_config(DefaultAzureCredential())
    deploy_online(client)
