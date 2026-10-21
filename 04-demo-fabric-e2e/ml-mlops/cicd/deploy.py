from __future__ import annotations

import argparse
import os
from pathlib import Path

from azure.identity import AzureCliCredential
from fabric_cicd import deploy_with_config

VALID_ENVIRONMENTS = {"DEV", "TEST", "PROD"}
ROOT = Path(__file__).resolve().parent
CONFIG_TEMPLATE = ROOT / "config.yml"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deploy the Fabric ML workshop items with fabric-cicd.")
    parser.add_argument("--environment", required=True, choices=sorted(VALID_ENVIRONMENTS))
    parser.add_argument("--config-path", default=str(CONFIG_TEMPLATE), help="Path to the config.yml template")
    return parser


def render_config(template_text: str, *, workspace_id: str) -> str:
    return template_text.replace("__TARGET_WORKSPACE_ID__", workspace_id)


def main() -> int:
    args = build_parser().parse_args()
    workspace_id = os.environ.get("FABRIC_TARGET_WORKSPACE_ID", "").strip()
    if not workspace_id:
        raise SystemExit("FABRIC_TARGET_WORKSPACE_ID is required.")

    config_path = Path(args.config_path)
    template = config_path.read_text(encoding="utf-8")
    rendered_path = ROOT / ("rendered-%s-config.yml" % args.environment.lower())
    rendered_path.write_text(render_config(template, workspace_id=workspace_id), encoding="utf-8", newline="\n")

    deploy_with_config(
        config_file_path=str(rendered_path),
        token_credential=AzureCliCredential(),
        environment=args.environment,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
