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

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F
from pyspark.sql import types as T

try:
    notebookutils
    IS_FABRIC = True
except NameError:
    IS_FABRIC = False

NOTEBOOK_NAME = "nb_01_bronze_ingest"
NOTEBOOK_SUMMARY = {}

if "__file__" in globals():
    ETL_ROOT = Path(__file__).resolve().parents[1]
else:
    ETL_ROOT = Path.cwd()

LOCAL_LAKEHOUSE_ROOT = ETL_ROOT / "local-validation" / "artifacts" / "lh_fleet"

if not raw_root and not IS_FABRIC:
    raw_root = os.environ.get("FLEET_RAW_ROOT") or str(ETL_ROOT.parents[1] / "02-demo-data" / "data")

if IS_FABRIC:
    files_root = Path("/lakehouse/default/Files/raw")
else:
    files_root = Path(raw_root)

spark.conf.set("spark.sql.session.timeZone", "UTC")


def raw_path(relative_path: str) -> str:
    if IS_FABRIC:
        return f"Files/raw/{relative_path}"
    return str(Path(raw_root) / relative_path)


def local_table_path(schema_name: str, table_name: str) -> Path:
    return LOCAL_LAKEHOUSE_ROOT / "Tables" / schema_name / table_name


def write_table(df: DataFrame, full_name: str, save_mode: str = "overwrite") -> None:
    schema_name, table_name = full_name.split(".", 1)
    if IS_FABRIC:
        writer = df.write.format("delta").mode(save_mode)
        if save_mode == "overwrite":
            writer = writer.option("overwriteSchema", "true")
        writer.saveAsTable(full_name)
        return

    path = local_table_path(schema_name, table_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = df.write.format(local_storage_format).mode(save_mode)
    if local_storage_format == "delta":
        writer = writer.option("overwriteSchema", "true")
    writer.save(str(path))


def read_table(full_name: str) -> DataFrame:
    schema_name, table_name = full_name.split(".", 1)
    if IS_FABRIC:
        return spark.table(full_name)
    return spark.read.format(local_storage_format).load(str(local_table_path(schema_name, table_name)))


def json_exit(summary: dict) -> None:
    global NOTEBOOK_SUMMARY
    NOTEBOOK_SUMMARY = summary
    payload = json.dumps(summary, sort_keys=True)
    if IS_FABRIC:
        notebookutils.notebook.exit(payload)
    print(payload)


payload_schema = T.StructType(
    [
        T.StructField("engine_state", T.StringType()),
        T.StructField("engine_hours", T.DoubleType()),
        T.StructField("engine_temp_c", T.DoubleType()),
        T.StructField("oil_pressure_kpa", T.DoubleType()),
        T.StructField("hydraulic_pressure_bar", T.DoubleType()),
        T.StructField("vibration_mm_s", T.DoubleType()),
        T.StructField("fuel_rate_lph", T.DoubleType()),
        T.StructField("load_pct", T.DoubleType()),
        T.StructField("idle_pct", T.DoubleType()),
        T.StructField("fault_codes", T.ArrayType(T.StringType())),
        T.StructField("lat", T.DoubleType()),
        T.StructField("lon", T.DoubleType()),
        T.StructField("coolant_level_pct", T.DoubleType()),
    ]
)

telematics_schema_str = T.StructType(
    [
        T.StructField("event_id", T.StringType()),
        T.StructField("device_id", T.StringType()),
        T.StructField("asset_ref", T.StringType()),
        T.StructField("serial_no", T.StringType()),
        T.StructField("ts", T.StringType()),
        T.StructField("ingest_ts", T.StringType()),
        T.StructField("firmware", T.StringType()),
        T.StructField("payload", payload_schema),
    ]
)

telematics_schema_num = T.StructType(
    [
        T.StructField("event_id", T.StringType()),
        T.StructField("device_id", T.StringType()),
        T.StructField("asset_ref", T.StringType()),
        T.StructField("serial_no", T.StringType()),
        T.StructField("ts", T.DoubleType()),
        T.StructField("ingest_ts", T.StringType()),
        T.StructField("firmware", T.StringType()),
        T.StructField("payload", payload_schema),
    ]
)

cmms_schema = T.StructType(
    [
        T.StructField("wo_number", T.StringType()),
        T.StructField("asset_tag", T.StringType()),
        T.StructField("serial_number", T.StringType()),
        T.StructField("site_code", T.StringType()),
        T.StructField("wo_type", T.StringType()),
        T.StructField("priority", T.StringType()),
        T.StructField("status", T.StringType()),
        T.StructField("failure_code", T.StringType()),
        T.StructField("failure_system", T.StringType()),
        T.StructField("description", T.StringType()),
        T.StructField("opened_local", T.StringType()),
        T.StructField("closed_local", T.StringType()),
        T.StructField("labor_hours", T.DoubleType()),
        T.StructField("parts_cost_eur", T.DoubleType()),
        T.StructField("technician_id", T.StringType()),
        T.StructField("reported_by", T.StringType()),
    ]
)

erp_schema = T.StructType(
    [
        T.StructField("erp_asset_id", T.StringType()),
        T.StructField("asset_name", T.StringType()),
        T.StructField("equipment_class", T.StringType()),
        T.StructField("manufacturer", T.StringType()),
        T.StructField("model", T.StringType()),
        T.StructField("serial_number", T.StringType()),
        T.StructField("acquisition_date", T.StringType()),
        T.StructField("acquisition_cost_eur", T.DoubleType()),
        T.StructField("site_code", T.StringType()),
        T.StructField("cost_center", T.StringType()),
        T.StructField("status", T.StringType()),
        T.StructField("retirement_date", T.StringType()),
        T.StructField("telematics_device_installed", T.StringType()),
    ]
)

site_schema = T.StructType(
    [
        T.StructField("site_code", T.StringType()),
        T.StructField("site_name", T.StringType()),
        T.StructField("country", T.StringType()),
        T.StructField("timezone", T.StringType()),
        T.StructField("utc_offset_standard_h", T.DoubleType()),
        T.StructField("latitude", T.DoubleType()),
        T.StructField("longitude", T.DoubleType()),
        T.StructField("project_type", T.StringType()),
    ]
)

fault_schema = T.StructType(
    [
        T.StructField("fault_code", T.StringType()),
        T.StructField("system", T.StringType()),
        T.StructField("severity", T.StringType()),
        T.StructField("description", T.StringType()),
        T.StructField("recommended_action", T.StringType()),
    ]
)

crosswalk_schema = T.StructType(
    [
        T.StructField("legacy_ref", T.StringType()),
        T.StructField("erp_asset_id", T.StringType()),
        T.StructField("source_system", T.StringType()),
        T.StructField("note", T.StringType()),
    ]
)


def add_bronze_metadata(df: DataFrame) -> DataFrame:
    return (
        df.withColumn("_source_file", F.input_file_name())
        .withColumn("_ingest_ts", F.current_timestamp())
        .withColumn("_batch_id", F.lit(batch_id))
    )


def read_bronze_telematics(glob_relative_path: str) -> DataFrame:
    """Parse one telematics JSONL glob (base window or drift batch) into the bronze shape.

    Same schema parsing and metadata as the base load: this is the single place that
    defines what a telematics bronze row looks like, used for both telematics/*.jsonl
    and the optional telematics_drift/*.jsonl batch.
    """
    raw_text = spark.read.text(raw_path(glob_relative_path))
    parsed_str = F.from_json("value", telematics_schema_str)
    parsed_num = F.from_json("value", telematics_schema_num)

    return add_bronze_metadata(
        raw_text.select(
            parsed_str["event_id"].alias("event_id"),
            parsed_str["device_id"].alias("device_id"),
            parsed_str["asset_ref"].alias("asset_ref"),
            parsed_str["serial_no"].alias("serial_no"),
            F.coalesce(parsed_str["ts"], parsed_num["ts"].cast("long").cast("string")).alias("ts"),
            parsed_str["ingest_ts"].alias("ingest_ts"),
            parsed_str["firmware"].alias("firmware"),
            parsed_str["payload"]["engine_state"].alias("engine_state"),
            parsed_str["payload"]["engine_hours"].alias("engine_hours"),
            parsed_str["payload"]["engine_temp_c"].alias("engine_temp_c"),
            parsed_str["payload"]["oil_pressure_kpa"].alias("oil_pressure_kpa"),
            parsed_str["payload"]["hydraulic_pressure_bar"].alias("hydraulic_pressure_bar"),
            parsed_str["payload"]["vibration_mm_s"].alias("vibration_mm_s"),
            parsed_str["payload"]["fuel_rate_lph"].alias("fuel_rate_lph"),
            parsed_str["payload"]["load_pct"].alias("load_pct"),
            parsed_str["payload"]["idle_pct"].alias("idle_pct"),
            parsed_str["payload"]["fault_codes"].alias("fault_codes"),
            parsed_str["payload"]["lat"].alias("lat"),
            parsed_str["payload"]["lon"].alias("lon"),
            parsed_str["payload"]["coolant_level_pct"].alias("coolant_level_pct"),
        )
    )


# %%
bronze_telematics = read_bronze_telematics("telematics/*.jsonl")

bronze_cmms = add_bronze_metadata(
    spark.read.option("header", True).schema(cmms_schema).csv(raw_path("cmms/cmms_work_orders.csv"))
)
bronze_erp = add_bronze_metadata(
    spark.read.option("header", True).schema(erp_schema).csv(raw_path("erp/erp_assets.csv"))
)
bronze_sites = add_bronze_metadata(
    spark.read.option("header", True).schema(site_schema).csv(raw_path("reference/site_master.csv"))
)
bronze_faults = add_bronze_metadata(
    spark.read.option("header", True).schema(fault_schema).csv(raw_path("reference/fault_code_catalog.csv"))
)
bronze_crosswalk = add_bronze_metadata(
    spark.read.option("header", True).schema(crosswalk_schema).csv(raw_path("reference/asset_crosswalk.csv"))
)

write_table(bronze_telematics, "bronze.telematics_events")
write_table(bronze_cmms, "bronze.cmms_work_orders")
write_table(bronze_erp, "bronze.erp_assets")
write_table(bronze_sites, "bronze.site_master")
write_table(bronze_faults, "bronze.fault_code_catalog")
write_table(bronze_crosswalk, "bronze.asset_crosswalk")

# %%
bronze_counts = {
    "telematics_events": read_table("bronze.telematics_events").count(),
    "cmms_work_orders": read_table("bronze.cmms_work_orders").count(),
    "erp_assets": read_table("bronze.erp_assets").count(),
    "site_master": read_table("bronze.site_master").count(),
    "fault_code_catalog": read_table("bronze.fault_code_catalog").count(),
    "asset_crosswalk": read_table("bronze.asset_crosswalk").count(),
}

missing_asset_ref = read_table("bronze.telematics_events").where(
    F.col("asset_ref").isNull() | (F.trim(F.col("asset_ref")) == "")
).count()

mixed_ts_rows = read_table("bronze.telematics_events").where(
    F.col("ts").rlike(r"^[0-9]+$") | F.col("ts").contains("Z") | F.col("ts").rlike(r"[+-][0-9]{2}:[0-9]{2}$")
).count()

expected_counts = {
    "telematics_events": 208900,
    "cmms_work_orders": 2359,
    "erp_assets": 316,
    "site_master": 12,
    "fault_code_catalog": 20,
    "asset_crosswalk": 9,
}

for name, expected in expected_counts.items():
    actual = bronze_counts[name]
    if actual != expected:
        raise AssertionError(f"{name} row count mismatch: expected {expected}, got {actual}")

if mixed_ts_rows != bronze_counts["telematics_events"]:
    raise AssertionError(
        "Telematics ts parsing coverage mismatch: every bronze row should preserve an ISO or epoch-ms ts string."
    )

print(
    "Bronze ingest complete. Counts match the contract: "
    f"{bronze_counts['telematics_events']} telematics, {bronze_counts['cmms_work_orders']} CMMS, "
    f"{bronze_counts['erp_assets']} ERP."
)

# %%
# Optional drift batch: October rehearsal data used by the ML drift-monitor demo.
# Bronze keeps raw reality here too - nothing is fixed, deduped, or resolved in this step.
# A missing telematics_drift/ folder is normal (the base-only dataset) and must not fail the notebook.
drift_glob_rel = "telematics_drift/*.jsonl"
drift_folder_rel = "telematics_drift"
drift_present = (files_root / drift_folder_rel).exists()

drift_bronze_rows = 0
if drift_present:
    bronze_telematics_drift = read_bronze_telematics(drift_glob_rel)
    write_table(bronze_telematics_drift, "bronze.telematics_events_drift")
    drift_bronze_rows = read_table("bronze.telematics_events_drift").count()

    expected_drift_rows = None
    if not IS_FABRIC:
        manifest_path = files_root / "_manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            file_entry = manifest.get("files", {}).get("telematics_drift/telematics_2026-10.jsonl", {})
            expected_drift_rows = file_entry.get("rows")

    if expected_drift_rows is not None and drift_bronze_rows != expected_drift_rows:
        print(
            "WARNING: bronze.telematics_events_drift row count "
            f"({drift_bronze_rows}) does not match the manifest ({expected_drift_rows}). "
            "This is a non-fatal warning, not an assertion: rehearsal data may differ from the contract."
        )
    else:
        print(f"Drift batch ingested: bronze.telematics_events_drift = {drift_bronze_rows} rows.")
else:
    print("No telematics_drift/ folder found: drift bronze table skipped (base-only dataset).")

# %%
summary = {
    "notebook": NOTEBOOK_NAME,
    "status": "ok",
    "batch_id": batch_id,
    "mode": mode,
    "data_cutoff_utc": data_cutoff_utc,
    "is_fabric": IS_FABRIC,
    "storage_format": "delta" if IS_FABRIC else local_storage_format,
    "counts": bronze_counts,
    "telematics_missing_or_blank_asset_ref": missing_asset_ref,
    "telematics_ts_rows_preserved": mixed_ts_rows,
    "drift_bronze_rows": drift_bronze_rows,
}
json_exit(summary)