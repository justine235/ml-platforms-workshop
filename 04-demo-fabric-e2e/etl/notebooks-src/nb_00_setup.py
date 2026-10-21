# %% parameters
try:
    batch_id
except NameError:
    batch_id = "fleet-demo-batch-001"

try:
    data_cutoff_utc
except NameError:
    data_cutoff_utc = "2026-10-01T00:00:00Z"

try:
    mode
except NameError:
    mode = "full"

try:
    raw_root
except NameError:
    raw_root = ""

try:
    local_storage_format
except NameError:
    local_storage_format = "parquet"

# %% 
import json
import os
from pathlib import Path

from pyspark.sql import functions as F

try:
    notebookutils
    IS_FABRIC = True
except NameError:
    IS_FABRIC = False

NOTEBOOK_NAME = "nb_00_setup"
NOTEBOOK_SUMMARY = {}

if "__file__" in globals():
    ETL_ROOT = Path(__file__).resolve().parents[1]
else:
    ETL_ROOT = Path.cwd()

LOCAL_LAKEHOUSE_ROOT = ETL_ROOT / "local-validation" / "artifacts" / "lh_fleet"

if not raw_root and not IS_FABRIC:
    raw_root = os.environ.get("FLEET_RAW_ROOT") or str(ETL_ROOT.parents[1] / "02-demo-data" / "data")

spark.conf.set("spark.sql.session.timeZone", "UTC")


def local_table_path(schema_name: str, table_name: str) -> Path:
    return LOCAL_LAKEHOUSE_ROOT / "Tables" / schema_name / table_name


def ensure_local_schema(schema_name: str) -> None:
    (LOCAL_LAKEHOUSE_ROOT / "Tables" / schema_name).mkdir(parents=True, exist_ok=True)


def write_local_marker() -> None:
    (LOCAL_LAKEHOUSE_ROOT / "Files" / "raw").mkdir(parents=True, exist_ok=True)


def json_exit(summary: dict) -> None:
    global NOTEBOOK_SUMMARY
    NOTEBOOK_SUMMARY = summary
    payload = json.dumps(summary, sort_keys=True)
    if IS_FABRIC:
        notebookutils.notebook.exit(payload)
    print(payload)


# %%
LANDING_OPTIONS = [
    {
        "option": "Fabric notebook generation",
        "action": (
            "Upload fleet_data_generator.py into Files/workshop-src/, open a Python or PySpark notebook, "
            "and run: !python /lakehouse/default/Files/workshop-src/fleet_data_generator.py "
            "--out /lakehouse/default/Files/raw --with-drift"
        ),
    },
    {
        "option": "OneLake File Explorer",
        "action": (
            "Generate the raw files locally, open the lakehouse in OneLake File Explorer, and copy "
            "the folders raw/reference, raw/erp, raw/cmms, raw/telematics, and raw/telematics_drift."
        ),
    },
    {
        "option": "Lakehouse upload UI",
        "action": (
            "In the lakehouse Files pane create Files/raw, then upload _manifest.json and the reference, erp, "
            "cmms, telematics, and telematics_drift folders with the Fabric upload dialog."
        ),
    },
]

print(json.dumps({"cutoff_utc": data_cutoff_utc, "landing_options": LANDING_OPTIONS}, indent=2))

# %%
for schema_name in ("bronze", "silver", "gold", "ml"):
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
    if not IS_FABRIC:
        ensure_local_schema(schema_name)

if not IS_FABRIC:
    write_local_marker()

# %%
expected_files = [
    "_manifest.json",
    "reference/site_master.csv",
    "reference/fault_code_catalog.csv",
    "reference/asset_crosswalk.csv",
    "erp/erp_assets.csv",
    "cmms/cmms_work_orders.csv",
    "telematics/telematics_2026-04.jsonl",
    "telematics/telematics_2026-05.jsonl",
    "telematics/telematics_2026-06.jsonl",
    "telematics/telematics_2026-07.jsonl",
    "telematics/telematics_2026-08.jsonl",
    "telematics/telematics_2026-09.jsonl",
]

optional_files = [
    "telematics_drift/telematics_2026-10.jsonl",
]

manifest_rows = None

if IS_FABRIC:
    # Reading through the /lakehouse/default mount right after an upload can hit Fabric's
    # ~120 s file-listing cache (a just-uploaded file can briefly look missing). Use
    # notebookutils.fs (OneLake-aware, not the local mount) for existence checks, and read
    # the manifest through Spark instead of pathlib so neither check depends on the mount.
    files_root = "Files/raw"
    try:
        present_required = [rel for rel in expected_files if notebookutils.fs.exists(f"{files_root}/{rel}")]
        missing_required = [rel for rel in expected_files if rel not in present_required]
        present_optional = [rel for rel in optional_files if notebookutils.fs.exists(f"{files_root}/{rel}")]
        if "_manifest.json" in present_required:
            manifest_text = spark.read.option("wholetext", True).text(f"{files_root}/_manifest.json").first()[0]
            manifest_rows = json.loads(manifest_text).get("counts", {})
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "Could not list Files/raw in the attached lakehouse. If you just uploaded the raw "
            "files, Fabric's file-listing cache can take about 2 minutes to refresh after an "
            "upload: wait and re-run this cell. Otherwise confirm lh_fleet is attached as the "
            "default lakehouse and that raw/ was uploaded under Files/."
        ) from exc
else:
    files_root = Path(raw_root)
    present_required = []
    missing_required = []
    for rel_path in expected_files:
        path_obj = files_root / rel_path
        if path_obj.exists():
            present_required.append(rel_path)
        else:
            missing_required.append(rel_path)

    present_optional = []
    for rel_path in optional_files:
        if (files_root / rel_path).exists():
            present_optional.append(rel_path)

    if not missing_required:
        manifest_rows = json.loads((files_root / "_manifest.json").read_text(encoding="utf-8")).get("counts", {})

# %%
summary = {
    "notebook": NOTEBOOK_NAME,
    "status": "ok" if not missing_required else "failed",
    "batch_id": batch_id,
    "mode": mode,
    "data_cutoff_utc": data_cutoff_utc,
    "is_fabric": IS_FABRIC,
    "raw_root": str(files_root),
    "required_files_found": len(present_required),
    "optional_files_found": len(present_optional),
    "missing_required_files": missing_required,
    "manifest_counts_local": manifest_rows,
}

if missing_required:
    raise AssertionError(f"Missing required raw files: {missing_required}")

print(
    "Validated raw landing files. Expected 12 required files and found "
    f"{summary['required_files_found']}. Drift file present: {bool(present_optional)}."
)
json_exit(summary)