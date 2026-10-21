from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    FabricDataAgentToolParameters,
    FabricIQPreviewTool,
    FunctionTool,
    MCPTool,
    MicrosoftFabricPreviewTool,
    PromptAgentDefinition,
    ToolProjectConnection,
)
from azure.identity import DefaultAzureCredential

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import load_settings, require_live_settings

DATA_AGENT_DIR = Path(__file__).resolve().parents[1] / "data-agent"


def _read_text(name: str) -> str:
    return (DATA_AGENT_DIR / name).read_text(encoding="utf-8")


def build_tools(settings):
    function_tool = FunctionTool(
        name="run_readonly_sql",
        description="Plan-B read-only SQL runner against the lakehouse SQL analytics endpoint. Use only for SELECT queries over the approved gold and ml tables.",
        strict=True,
        parameters={
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "A single SELECT statement over the approved demo tables."}
            },
            "required": ["sql"],
            "additionalProperties": False,
        },
    )

    tools = [
        FabricIQPreviewTool(
            project_connection_id=settings.fabric_iq_project_connection_id,
            server_label="da_fleet_recon",
            server_url=settings.mcp_server_url,
            require_approval="never",
        ),
        MCPTool(
            server_label="da_fleet_recon_mcp",
            server_url=settings.mcp_server_url,
            allowed_tools=["ask_fabric_data_agent"],
            require_approval="never",
        ),
        function_tool,
    ]
    if settings.legacy_fabric_connection_id:
        tools.append(
            MicrosoftFabricPreviewTool(
                fabric_dataagent_preview=FabricDataAgentToolParameters(
                    project_connections=[
                        ToolProjectConnection(project_connection_id=settings.legacy_fabric_connection_id)
                    ]
                )
            )
        )
    return tools


def build_definition(settings) -> PromptAgentDefinition:
    instructions = (
        "You are fleet-recon-agent for the Contoso Fleet workshop. "
        "Prefer the published Fabric data agent over direct SQL. "
        "Stay read-only, cite the SQL when you can, refuse out-of-scope or write requests, "
        "and use the frozen 2026-09-30 failure-risk scores for all risk answers.\n\n"
        f"{_read_text('agent-instructions.md')}"
    )
    return PromptAgentDefinition(
        model=settings.model_deployment,
        instructions=instructions,
        temperature=0.0,
        tools=build_tools(settings),
        tool_choice="auto",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or preview the fleet-recon Foundry prompt agent.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    settings = load_settings()
    definition = build_definition(settings)
    if args.dry_run:
        print(json.dumps(definition.as_dict(), indent=2))
        return 0

    require_live_settings(settings)
    credential = DefaultAzureCredential()
    project = AIProjectClient(endpoint=settings.project_endpoint, credential=credential, allow_preview=True)
    result = project.agents.create_version(agent_name=settings.agent_name, definition=definition)
    print(json.dumps(result.as_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
