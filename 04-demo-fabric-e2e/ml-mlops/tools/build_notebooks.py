from __future__ import annotations

import json
import uuid
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]  # .../ml-mlops
E2E_DIR = ROOT.parent  # .../04-demo-fabric-e2e
SOURCE_DIR = ROOT / "notebooks"
IPYNB_DIR = SOURCE_DIR / "generated-ipynb"
FABRIC_DIR = ROOT / "fabric-git"
ETL_FABRIC_DIR = E2E_DIR / "etl" / "fabric-git"

PLATFORM_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json"
ZERO_WORKSPACE_ID = "00000000-0000-0000-0000-000000000000"
LOGICAL_ID_NAMESPACE = "https://contoso-fleet.local/%s"

# Fabric-only code-path shim: the generator injects this as the first code cell of
# every notebook so '/lakehouse/default/Files/code' (the uploaded `notebooks\` package)
# is importable in a real workspace. Outside Fabric 'IN_FABRIC' is False, so this is a
# no-op (the hand-authored percent source does NOT contain this cell; it relies on
# run_local.py's own sys.path setup instead).
FABRIC_CODE_DIR_CELL = (
    "import os\n"
    "import sys\n"
    "\n"
    'IN_FABRIC = "notebookutils" in globals()\n'
    "if IN_FABRIC:\n"
    '    CODE_DIR = os.environ.get("FLEET_CODE_DIR", "/lakehouse/default/Files/code")\n'
    "    if CODE_DIR not in sys.path:\n"
    "        sys.path.insert(0, CODE_DIR)\n"
)

NOTEBOOK_DESCRIPTIONS = {
    "nb_04_features": "Build the ML feature table (one row per asset-day) from the reconciled ETL gold/silver tables.",
    "nb_05_train_mlflow": "Train and compare candidate models with explicit MLflow tracking, then register the champion.",
    "nb_06_register_score": "Score the latest day with the registered champion model and write ml.failure_risk_score.",
    "nb_07_drift_monitor": "Compare September reference telemetry to the October batch with PSI and exit machine-readable drift status.",
    "nb_08_promotion_gate": "Evaluate champion vs challenger on the frozen test split and return a promotion decision.",
}

# Maps each placeholder still present in the committed pipeline-content.json template to
# the notebook whose real .platform logicalId should replace it. "self" = this folder's
# own fabric-git notebooks (ids computed by this script); "etl" = the ETL demo's
# fabric-git notebooks (ids read from their .platform files at build time, never
# hardcoded, so a later ETL regeneration is picked up automatically on the next build).
PIPELINE_NOTEBOOK_PLACEHOLDERS = {
    "__NB_01_BRONZE_INGEST_ID__": ("etl", "nb_01_bronze_ingest"),
    "__NB_02_SILVER_CLEAN_RESOLVE_ID__": ("etl", "nb_02_silver_clean_resolve"),
    "__NB_03_GOLD_RECONCILE_ID__": ("etl", "nb_03_gold_reconcile"),
    "__NB_04_FEATURES_ID__": ("self", "nb_04_features"),
    "__NB_05_TRAIN_MLFLOW_ID__": ("self", "nb_05_train_mlflow"),
    "__NB_06_REGISTER_SCORE_ID__": ("self", "nb_06_register_score"),
    "__NB_07_DRIFT_MONITOR_ID__": ("self", "nb_07_drift_monitor"),
    "__NB_08_PROMOTION_GATE_ID__": ("self", "nb_08_promotion_gate"),
}


def logical_id_for(name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, LOGICAL_ID_NAMESPACE % name))


def write_text_lf(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def iter_source_files() -> list[Path]:
    return sorted(path for path in SOURCE_DIR.glob("nb_*.py") if path.is_file())


def markdown_from_comment_block(lines: list[str]) -> str:
    out = []
    for line in lines:
        if line.startswith("# "):
            out.append(line[2:])
        elif line.startswith("#"):
            out.append(line[1:])
        else:
            out.append(line)
    return "".join(out)


def parse_percent_source(text: str) -> list[dict]:
    """Split a '# %%' percent-format source into cells, keeping the ORIGINAL lines
    (including each markdown cell's leading '# ' comment prefix) so the same parse can
    feed both nbformat (which needs stripped markdown) and the Fabric Git format (which
    needs the comment-prefixed form unchanged -- Fabric's MARKDOWN block convention is
    exactly '# '-per-line, the same convention this repo already writes source in).
    """
    cells: list[dict] = []
    current_kind = "code"
    current_lines: list[str] = []

    def flush() -> None:
        if not any(line.strip() for line in current_lines):
            return
        cells.append({"cell_type": current_kind, "lines": list(current_lines)})

    for line in text.splitlines(keepends=True):
        if line.startswith("# %%"):
            flush()
            current_lines = []
            current_kind = "markdown" if "[markdown]" in line else "code"
            continue
        current_lines.append(line)
    flush()
    return cells


def to_ipynb_cells(cells: list[dict]) -> list:
    nb_cells = []
    for cell in cells:
        if cell["cell_type"] == "markdown":
            source = markdown_from_comment_block(cell["lines"]).rstrip() + "\n"
            nb_cells.append(nbformat.v4.new_markdown_cell(source=source))
        else:
            source = "".join(cell["lines"]).rstrip() + "\n"
            nb_cells.append(nbformat.v4.new_code_cell(source=source))
    return nb_cells


def encode_meta_block(obj: dict) -> str:
    payload = json.dumps(obj, indent=2)
    return "\n".join("# META %s" % line if line else "# META" for line in payload.splitlines())


def to_fabric_source(cells: list[dict]) -> str:
    """Emit notebook-content.py in the real Fabric Git format (verified against the
    public fabric-cicd sample and the kit's own check_fabric_git.py): a notebook-level
    '# METADATA' block with kernel_info/dependencies, then one '# CELL'/'# MARKDOWN'
    block per cell, each code cell followed by its own language '# METADATA' block.
    """
    parts = [
        "# Fabric notebook source",
        "",
        "# METADATA ********************",
        "",
        encode_meta_block({"kernel_info": {"name": "synapse_pyspark"}, "dependencies": {}}),
        "",
    ]

    def emit_code_cell(code_text: str) -> None:
        parts.append("# CELL ********************")
        parts.append("")
        parts.extend(code_text.rstrip("\n").splitlines())
        parts.append("")
        parts.append("# METADATA ********************")
        parts.append("")
        parts.append(encode_meta_block({"language": "python", "language_group": "synapse_pyspark"}))
        parts.append("")

    def emit_markdown_cell(raw_lines: list[str]) -> None:
        parts.append("# MARKDOWN ********************")
        parts.append("")
        for line in raw_lines:
            text = line.rstrip("\n")
            parts.append(text if text else "#")
        parts.append("")

    emit_code_cell(FABRIC_CODE_DIR_CELL)
    for cell in cells:
        if cell["cell_type"] == "markdown":
            emit_markdown_cell(cell["lines"])
        else:
            emit_code_cell("".join(cell["lines"]))

    return "\n".join(parts).rstrip("\n") + "\n"


def write_platform(target_dir: Path, name: str, item_type: str, description: str | None = None) -> str:
    logical_id = logical_id_for(name)
    metadata: dict = {"type": item_type, "displayName": name}
    if description:
        metadata["description"] = description
    platform = {
        "$schema": PLATFORM_SCHEMA,
        "metadata": metadata,
        "config": {"version": "2.0", "logicalId": logical_id},
    }
    write_text_lf(target_dir / ".platform", json.dumps(platform, indent=2) + "\n")
    return logical_id


def build_one(source_path: Path) -> str:
    name = source_path.stem
    text = source_path.read_text(encoding="utf-8")
    cells = parse_percent_source(text)

    notebook = nbformat.v4.new_notebook(
        metadata={
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "file_extension": ".py"},
            "fabric": {"kernel_info": {"name": "synapse_pyspark"}},
        }
    )
    notebook.cells = to_ipynb_cells(cells)
    nbformat.validate(notebook)

    IPYNB_DIR.mkdir(parents=True, exist_ok=True)
    with (IPYNB_DIR / ("%s.ipynb" % name)).open("w", encoding="utf-8", newline="\n") as handle:
        nbformat.write(notebook, handle)

    fabric_notebook_dir = FABRIC_DIR / ("%s.Notebook" % name)
    fabric_notebook_dir.mkdir(parents=True, exist_ok=True)
    write_text_lf(fabric_notebook_dir / "notebook-content.py", to_fabric_source(cells))
    logical_id = write_platform(
        fabric_notebook_dir,
        name=name,
        item_type="Notebook",
        description=NOTEBOOK_DESCRIPTIONS.get(name),
    )
    print("%s -> ipynb, fabric-git (logicalId %s)" % (name, logical_id))
    return logical_id


def etl_notebook_logical_id(name: str) -> str | None:
    platform_path = ETL_FABRIC_DIR / ("%s.Notebook" % name) / ".platform"
    if not platform_path.exists():
        print("WARNING: %s not found; pl_fleet_daily keeps a placeholder for %s (re-run this build once the ETL folder regenerates it)" % (platform_path, name))
        return None
    data = json.loads(platform_path.read_text(encoding="utf-8-sig"))
    logical_id = (data.get("config") or {}).get("logicalId")
    if not logical_id:
        print("WARNING: %s has no config.logicalId" % platform_path)
    return logical_id


def build_pipeline(self_logical_ids: dict[str, str]) -> None:
    """Patch the committed pl_fleet_daily pipeline-content.json template in place:
    replace '__WORKSPACE_ID__' with the Fabric same-workspace zero-GUID and every
    '__NB_0X_..._ID__' placeholder with the real logicalId of the matching notebook
    (own fabric-git for nb_04-08, the ETL demo's fabric-git for nb_01-03, looked up by
    displayName at build time, never hardcoded). The activity names, retry policy,
    Office365Email notify branches and IfDriftAlert expression are hand-maintained in
    the template itself and are left untouched by this script.
    """
    pipeline_dir = FABRIC_DIR / "pl_fleet_daily.DataPipeline"
    content_path = pipeline_dir / "pipeline-content.json"
    text = content_path.read_text(encoding="utf-8")

    before = text
    text = text.replace('"__WORKSPACE_ID__"', '"%s"' % ZERO_WORKSPACE_ID)
    for placeholder, (scope, name) in PIPELINE_NOTEBOOK_PLACEHOLDERS.items():
        resolved = self_logical_ids.get(name) if scope == "self" else etl_notebook_logical_id(name)
        if resolved:
            text = text.replace('"%s"' % placeholder, '"%s"' % resolved)
        else:
            print("WARNING: leaving placeholder %s unresolved in pipeline-content.json" % placeholder)

    data = json.loads(text)  # fail fast if a replacement broke the JSON
    write_text_lf(content_path, json.dumps(data, indent=2) + "\n")
    if text == before:
        print("pipeline-content.json: no placeholders replaced (already resolved?)")
    else:
        print("pipeline-content.json: patched notebookId/workspaceId placeholders")

    write_platform(
        pipeline_dir,
        name="pl_fleet_daily",
        item_type="DataPipeline",
        description="Daily Fabric ML + MLOps orchestration: ETL refresh, features, train, register/score, drift monitor, promotion gate, alert on major drift.",
    )


def normalize_variable_library() -> None:
    """The fleet_mlops.VariableLibrary content files (variables.json, settings.json,
    valueSets\\*.json) are hand-authored, not generated from a percent source. This
    only fixes their .platform schema and normalizes line endings/BOM; it does not
    change any variable name or value.
    """
    vl_dir = FABRIC_DIR / "fleet_mlops.VariableLibrary"
    if not vl_dir.exists():
        print("WARNING: %s not found; skipping Variable Library normalization" % vl_dir)
        return
    write_platform(vl_dir, name="fleet_mlops", item_type="VariableLibrary", description="Per-environment value sets for the Fabric ML + MLOps demo.")
    json_files = [vl_dir / "variables.json", vl_dir / "settings.json"]
    value_sets_dir = vl_dir / "valueSets"
    if value_sets_dir.exists():
        json_files.extend(sorted(value_sets_dir.glob("*.json")))
    for path in json_files:
        if not path.exists():
            continue
        data = json.loads(path.read_bytes().decode("utf-8-sig"))
        write_text_lf(path, json.dumps(data, indent=2) + "\n")


def main() -> None:
    self_logical_ids: dict[str, str] = {}
    for source_path in iter_source_files():
        self_logical_ids[source_path.stem] = build_one(source_path)
    build_pipeline(self_logical_ids)
    normalize_variable_library()
    print("Built notebooks into %s and %s." % (IPYNB_DIR, FABRIC_DIR))


if __name__ == "__main__":
    main()