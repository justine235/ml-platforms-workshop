from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent


@dataclass(frozen=True)
class Settings:
    project_endpoint: str = ""
    model_deployment: str = ""
    agent_name: str = "fleet-recon-agent"
    fabric_iq_project_connection_id: str = ""
    fabric_iq_server_url: str = ""
    fabric_workspace_id: str = ""
    fabric_data_agent_id: str = ""
    legacy_fabric_connection_id: str = ""
    sql_endpoint_server: str = ""
    sql_endpoint_database: str = ""
    sql_max_rows: int = 200
    app_insights_connection_string: str = ""
    extra_metadata: dict[str, str] = field(default_factory=dict)

    @property
    def mcp_server_url(self) -> str:
        if self.fabric_iq_server_url:
            return self.fabric_iq_server_url
        return (
            "https://api.fabric.microsoft.com/v1/mcp/workspaces/"
            f"{self.fabric_workspace_id}/dataagents/{self.fabric_data_agent_id}/agent"
        )


def load_settings(env_path: Path | None = None) -> Settings:
    load_dotenv(env_path or BASE_DIR / ".env")
    metadata = {
        "workshop_part": "part4",
        "demo_name": "fleet-recon-agent",
    }
    return Settings(
        project_endpoint=os.getenv("AZURE_AI_PROJECT_ENDPOINT", ""),
        model_deployment=os.getenv("AZURE_OPENAI_MODEL_DEPLOYMENT", ""),
        agent_name=os.getenv("FLEET_RECON_AGENT_NAME", "fleet-recon-agent"),
        fabric_iq_project_connection_id=os.getenv("FABRIC_IQ_PROJECT_CONNECTION_ID", ""),
        fabric_iq_server_url=os.getenv("FABRIC_IQ_SERVER_URL", ""),
        fabric_workspace_id=os.getenv("FABRIC_WORKSPACE_ID", ""),
        fabric_data_agent_id=os.getenv("FABRIC_DATA_AGENT_ID", ""),
        legacy_fabric_connection_id=os.getenv("LEGACY_FABRIC_CONNECTION_ID", ""),
        sql_endpoint_server=os.getenv("LAKEHOUSE_SQL_SERVER", ""),
        sql_endpoint_database=os.getenv("LAKEHOUSE_SQL_DATABASE", ""),
        sql_max_rows=int(os.getenv("SQL_MAX_ROWS", "200")),
        app_insights_connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", ""),
        extra_metadata=metadata,
    )


def require_live_settings(settings: Settings) -> None:
    required = {
        "AZURE_AI_PROJECT_ENDPOINT": settings.project_endpoint,
        "AZURE_OPENAI_MODEL_DEPLOYMENT": settings.model_deployment,
        "FABRIC_IQ_PROJECT_CONNECTION_ID": settings.fabric_iq_project_connection_id,
        "FABRIC_WORKSPACE_ID": settings.fabric_workspace_id,
        "FABRIC_DATA_AGENT_ID": settings.fabric_data_agent_id,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Missing required live settings: {joined}")
