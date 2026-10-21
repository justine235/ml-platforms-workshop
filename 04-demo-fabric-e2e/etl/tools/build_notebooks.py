from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook


ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "notebooks-src"
IPYNB_DIR = ROOT / "notebooks"
FABRIC_DIR = ROOT / "fabric-git"
PLATFORM_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json"

# Neutral seed for deterministic logicalIds: never the real customer name or the
# folder name this kit happens to live in.
LOGICAL_ID_SEED_PREFIX = "contoso-fleet-workshop"
ZERO_WORKSPACE_ID = "00000000-0000-0000-0000-000000000000"

NOTEBOOK_DESCRIPTIONS = {
    "nb_00_setup": "Create lakehouse schemas and validate raw landing files for the fleet demo.",
    "nb_01_bronze_ingest": "Load raw fleet files into bronze tables with explicit schemas and landing metadata.",
    "nb_02_silver_clean_resolve": "Clean bronze data, normalize timestamps, resolve identities, and flag data-quality issues.",
    "nb_03_gold_reconcile": "Build reconciled gold tables, monthly summaries, and reconciliation exceptions.",
}

PIPELINE_NAME = "pl_fleet_etl"
PIPELINE_DESCRIPTION = (
    "Sequential Fabric ETL pipeline for the fleet medallion demo. Each activity's "
    "notebookId is the real logicalId of that notebook in this folder (from its own "
    ".platform file) and workspaceId is the all-zero GUID Fabric uses for a "
    "same-workspace reference, the same pattern the public fabric-cicd sample uses. "
    "Fabric Git sync resolves each activity to the matching notebook automatically; "
    "if an activity still shows an unresolved notebook after import, re-pick the "
    "notebook in that activity."
)
PIPELINE_PARAMETERS = {
    "batch_id": {"value": "fleet-demo-live", "type": "string"},
    "data_cutoff_utc": {"value": "2026-10-01T00:00:00Z", "type": "string"},
    "mode": {"value": "full", "type": "string"},
}
ACTIVITY_POLICY = {
    "timeout": "0.12:00:00",
    "retry": 0,
    "retryIntervalInSeconds": 30,
    "secureInput": False,
    "secureOutput": False,
}
PIPELINE_ACTIVITIES = [
    {"name": "RunSetup", "notebook": "nb_00_setup", "depends_on": None},
    {"name": "RunBronzeIngest", "notebook": "nb_01_bronze_ingest", "depends_on": "RunSetup"},
    {"name": "RunSilverCleanResolve", "notebook": "nb_02_silver_clean_resolve", "depends_on": "RunBronzeIngest"},
    {"name": "RunGoldReconcile", "notebook": "nb_03_gold_reconcile", "depends_on": "RunSilverCleanResolve"},
]


def logical_id_for(name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{LOGICAL_ID_SEED_PREFIX}/{name}"))


def write_text_lf(path: Path, text: str) -> None:
    """Write UTF-8 text with LF line endings only, never the platform default."""
    path.write_text(text, encoding="utf-8", newline="\n")


def parse_percent_file(path: Path) -> list[dict[str, object]]:
    text = path.read_text(encoding="utf-8")
    header_re = re.compile(r"^# %% ?(.*)$", re.MULTILINE)
    matches = list(header_re.finditer(text))
    if not matches:
        raise ValueError(f"{path} does not contain any # %% cells")

    cells: list[dict[str, object]] = []
    for index, match in enumerate(matches):
        header = match.group(1).strip().lower()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        source = text[start:end].lstrip("\n").rstrip() + "\n"
        if not source.strip():
            continue
        cell_type = "markdown" if "markdown" in header else "code"
        tags = []
        if "parameters" in header:
            tags.append("parameters")
        cells.append({"cell_type": cell_type, "source": source, "tags": tags})
    return cells


def to_ipynb(cells: list[dict[str, object]], name: str) -> nbformat.NotebookNode:
    notebook_cells = []
    for cell in cells:
        if cell["cell_type"] == "markdown":
            notebook_cells.append(new_markdown_cell(source=str(cell["source"])))
        else:
            nb_cell = new_code_cell(source=str(cell["source"]))
            if cell["tags"]:
                nb_cell.metadata["tags"] = list(cell["tags"])
            notebook_cells.append(nb_cell)
    nb = new_notebook(
        cells=notebook_cells,
        metadata={
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python"},
            "fabric": {"kernel_info": {"name": "synapse_pyspark"}},
            "name": name,
        },
    )
    nbformat.validate(nb)
    return nb


def encode_meta_block(obj: dict[str, object]) -> str:
    payload = json.dumps(obj, indent=2)
    return "\n".join(f"# META {line}" for line in payload.splitlines())


def to_fabric_source(cells: list[dict[str, object]]) -> str:
    """Emit notebook-content.py with the exact spacing of the real fabric-cicd
    sample: a blank line after '# Fabric notebook source', after every
    '# METADATA ********************' marker, after each '# META {...}' block,
    and after every '# CELL ********************' marker, then the cell code,
    then one blank line before the next marker.
    """
    parts = [
        "# Fabric notebook source",
        "",
        "# METADATA ********************",
        "",
        encode_meta_block({"kernel_info": {"name": "synapse_pyspark"}, "dependencies": {}}),
        "",
    ]
    for cell in cells:
        if cell["cell_type"] != "code":
            raise ValueError("This workshop build script only emits code-cell Fabric sources.")
        parts.append("# CELL ********************")
        parts.append("")
        parts.extend(str(cell["source"]).rstrip("\n").splitlines())
        parts.append("")
        metadata: dict[str, object] = {
            "language": "python",
            "language_group": "synapse_pyspark",
        }
        if cell["tags"]:
            metadata["tags"] = list(cell["tags"])
        parts.append("# METADATA ********************")
        parts.append("")
        parts.append(encode_meta_block(metadata))
        parts.append("")
    return "\n".join(parts).rstrip("\n") + "\n"


def write_platform(target_dir: Path, name: str, item_type: str, description: str) -> None:
    logical_id = logical_id_for(name)
    platform = {
        "$schema": PLATFORM_SCHEMA,
        "metadata": {
            "type": item_type,
            "displayName": name,
            "description": description,
        },
        "config": {"version": "2.0", "logicalId": logical_id},
    }
    write_text_lf(target_dir / ".platform", json.dumps(platform, indent=2) + "\n")


def build_one(path: Path) -> None:
    name = path.stem
    cells = parse_percent_file(path)

    IPYNB_DIR.mkdir(parents=True, exist_ok=True)
    nb = to_ipynb(cells, name)
    write_text_lf(IPYNB_DIR / f"{name}.ipynb", nbformat.writes(nb))

    notebook_dir = FABRIC_DIR / f"{name}.Notebook"
    notebook_dir.mkdir(parents=True, exist_ok=True)
    write_text_lf(notebook_dir / "notebook-content.py", to_fabric_source(cells))
    write_platform(
        notebook_dir,
        name=name,
        item_type="Notebook",
        description=NOTEBOOK_DESCRIPTIONS.get(name, name),
    )


def build_pipeline() -> None:
    """Regenerate pl_fleet_etl.DataPipeline using the real notebook logicalIds.

    workspaceId is the all-zero GUID Fabric treats as "resolve in the importing
    workspace"; notebookId is each notebook's logicalId from its own .platform
    file (computed the same way here, from the same neutral seed) - the same
    pattern the public fabric-cicd sample uses for same-workspace notebooks, so
    a Git sync has a real reference to wire up instead of a dummy GUID.
    """
    pipeline_dir = FABRIC_DIR / f"{PIPELINE_NAME}.DataPipeline"
    pipeline_dir.mkdir(parents=True, exist_ok=True)

    write_platform(
        pipeline_dir,
        name=PIPELINE_NAME,
        item_type="DataPipeline",
        description="Sequential Fabric ETL pipeline for the fleet medallion demo.",
    )

    activities = []
    for activity in PIPELINE_ACTIVITIES:
        entry: dict[str, object] = {
            "name": activity["name"],
            "type": "TridentNotebook",
        }
        if activity["depends_on"]:
            entry["dependsOn"] = [
                {"activity": activity["depends_on"], "dependencyConditions": ["Succeeded"]}
            ]
        else:
            entry["dependsOn"] = []
        entry["policy"] = dict(ACTIVITY_POLICY)
        entry["typeProperties"] = {
            "notebookId": logical_id_for(activity["notebook"]),
            "workspaceId": ZERO_WORKSPACE_ID,
            "parameters": PIPELINE_PARAMETERS,
        }
        activities.append(entry)

    pipeline_content = {
        "properties": {
            "description": PIPELINE_DESCRIPTION,
            "activities": activities,
        }
    }
    write_text_lf(pipeline_dir / "pipeline-content.json", json.dumps(pipeline_content, indent=2) + "\n")


def main() -> None:
    for source in sorted(SRC_DIR.glob("nb_*.py")):
        build_one(source)
    build_pipeline()
    print(f"Built notebooks into {IPYNB_DIR} and {FABRIC_DIR}.")


if __name__ == "__main__":
    main()