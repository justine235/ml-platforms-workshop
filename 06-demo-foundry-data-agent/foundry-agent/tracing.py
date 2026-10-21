from __future__ import annotations

import sys
from pathlib import Path

from azure.ai.projects.telemetry import AIProjectInstrumentor, trace_function

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import load_settings


def configure_tracing(project_client=None, connection_string: str | None = None) -> str | None:
    settings = load_settings()
    resolved = connection_string or settings.app_insights_connection_string
    if project_client is not None and not resolved:
        try:
            resolved = project_client.telemetry.get_application_insights_connection_string()
        except AttributeError:
            resolved = None
    if resolved:
        AIProjectInstrumentor().instrument(enable_content_recording=True, enable_trace_context_and_baggage=True)
    return resolved


@trace_function
def traced_guarded_sql(sql_text: str) -> dict[str, str]:
    return {"sql": sql_text}
