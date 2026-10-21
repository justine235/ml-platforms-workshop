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
from pathlib import Path

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

try:
    notebookutils
    IS_FABRIC = True
except NameError:
    IS_FABRIC = False
NOTEBOOK_NAME = "nb_02_silver_clean_resolve"
NOTEBOOK_SUMMARY = {}
DAY_SECONDS = 86400.0
CUTOFF_EPOCH = 1790812800.0
NORM_REGEX = r"(?i)^\s*(?:EQ|E)?[\s_\-]*0*(\d{1,5})\s*$"
SENSOR_LIMITS = {
    "engine_temp_c": (0.0, 150.0),
    "oil_pressure_kpa": (0.0, 800.0),
    "hydraulic_pressure_bar": (0.0, 450.0),
    "vibration_mm_s": (0.0, 30.0),
    "fuel_rate_lph": (0.0, 200.0),
    "load_pct": (0.0, 100.0),
    "idle_pct": (0.0, 100.0),
}

if "__file__" in globals():
    ETL_ROOT = Path(__file__).resolve().parents[1]
else:
    ETL_ROOT = Path.cwd()

LOCAL_LAKEHOUSE_ROOT = ETL_ROOT / "local-validation" / "artifacts" / "lh_fleet"
spark.conf.set("spark.sql.session.timeZone", "UTC")


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


def table_exists(full_name: str) -> bool:
    """True when a bronze/silver table has already been written, Fabric or local."""
    schema_name, table_name = full_name.split(".", 1)
    if IS_FABRIC:
        return spark.catalog.tableExists(full_name)
    return local_table_path(schema_name, table_name).exists()


def json_exit(summary: dict) -> None:
    global NOTEBOOK_SUMMARY
    NOTEBOOK_SUMMARY = summary
    payload = json.dumps(summary, sort_keys=True)
    if IS_FABRIC:
        notebookutils.notebook.exit(payload)
    print(payload)


def apply_resolution(df: DataFrame, ref_col: str, serial_col: str, erp: DataFrame, crosswalk: DataFrame) -> DataFrame:
    erp_ids = F.broadcast(erp.select("erp_asset_id").dropDuplicates())
    erp_serials = F.broadcast(
        erp.select(
            F.regexp_replace(F.upper(F.col("serial_number")), "[^A-Z0-9]", "").alias("serial_norm"),
            F.col("erp_asset_id").alias("serial_erp_asset_id"),
        ).dropDuplicates(["serial_norm"])
    )
    xwalk = F.broadcast(
        crosswalk.select(
            F.upper(F.trim(F.col("legacy_ref"))).alias("crosswalk_ref"),
            F.col("erp_asset_id").alias("crosswalk_erp_asset_id"),
        ).dropDuplicates(["crosswalk_ref"])
    )

    digits = F.regexp_extract(F.coalesce(F.col(ref_col), F.lit("")), NORM_REGEX, 1)
    candidate = F.when(digits != "", F.format_string("EQ-%05d", digits.cast("int")))
    ref_norm = F.upper(F.trim(F.coalesce(F.col(ref_col), F.lit(""))))
    serial_norm = F.regexp_replace(F.upper(F.coalesce(F.col(serial_col), F.lit(""))), "[^A-Z0-9]", "")

    resolved = (
        df.withColumn("_candidate_exact_id", candidate)
        .withColumn("_serial_norm", serial_norm)
        .withColumn("_crosswalk_ref", ref_norm)
        .join(erp_ids.withColumnRenamed("erp_asset_id", "_exact_erp_asset_id"), F.col("_candidate_exact_id") == F.col("_exact_erp_asset_id"), "left")
        .join(erp_serials, F.col("_serial_norm") == F.col("serial_norm"), "left")
        .join(xwalk, F.col("_crosswalk_ref") == F.col("crosswalk_ref"), "left")
    )

    return (
        resolved.withColumn(
            "erp_asset_id",
            F.when(F.col("_exact_erp_asset_id").isNotNull(), F.col("_exact_erp_asset_id"))
            .when((F.col("_serial_norm") != "") & F.col("serial_erp_asset_id").isNotNull(), F.col("serial_erp_asset_id"))
            .when(F.col("crosswalk_erp_asset_id").isNotNull(), F.col("crosswalk_erp_asset_id")),
        )
        .withColumn(
            "resolution_method",
            F.when(F.col("_exact_erp_asset_id").isNotNull(), F.lit("EXACT_NORM"))
            .when((F.col("_serial_norm") != "") & F.col("serial_erp_asset_id").isNotNull(), F.lit("SERIAL"))
            .when(F.col("crosswalk_erp_asset_id").isNotNull(), F.lit("CROSSWALK"))
            .otherwise(F.lit("UNRESOLVED")),
        )
        .drop(
            "_candidate_exact_id",
            "_serial_norm",
            "_crosswalk_ref",
            "_exact_erp_asset_id",
            "serial_norm",
            "serial_erp_asset_id",
            "crosswalk_ref",
            "crosswalk_erp_asset_id",
        )
    )


def parse_ts_to_epoch(col_name: str) -> F.Column:
    return F.when(
        F.col(col_name).rlike(r"^[0-9]+$"),
        F.col(col_name).cast("double") / F.lit(1000.0),
    ).otherwise(F.unix_timestamp(F.to_timestamp(F.col(col_name))).cast("double"))


def build_silver_telemetry(bronze_telematics: DataFrame, erp: DataFrame, crosswalk: DataFrame) -> tuple[DataFrame, int]:
    """One telemetry chain for both the base window and the optional October drift batch.

    Dedupe by event_id, parse timestamps, null out-of-range sensor spikes, resolve
    identity in four tiers, then derive is_late / is_in_window / event_ts_utc / day /
    is_run. Used unchanged for silver.telemetry (base) and silver.telemetry_drift
    (drift): same function, same code path, so the base output is guaranteed
    byte-for-byte identical to before this table was added.
    """
    telematics_rank = Window.partitionBy("event_id").orderBy(F.col("ingest_epoch").asc(), F.col("_source_file").asc())

    telemetry = (
        bronze_telematics.withColumn("ts_epoch", parse_ts_to_epoch("ts"))
        .withColumn("ingest_epoch", F.unix_timestamp(F.to_timestamp("ingest_ts")).cast("double"))
        .withColumn("row_rank", F.row_number().over(telematics_rank))
        .where(F.col("row_rank") == 1)
        .drop("row_rank")
    )

    telemetry_preclean = telemetry
    spike_count_expr = F.lit(0)
    for sensor_name, (lower_bound, upper_bound) in SENSOR_LIMITS.items():
        out_of_range = (
            F.col(sensor_name).isNotNull()
            & ((F.col(sensor_name) < F.lit(lower_bound)) | (F.col(sensor_name) > F.lit(upper_bound)))
        )
        spike_count_expr = spike_count_expr + F.when(out_of_range, F.lit(1)).otherwise(F.lit(0))
        telemetry = telemetry.withColumn(sensor_name, F.when(out_of_range, F.lit(None)).otherwise(F.col(sensor_name)))

    nulled_spikes = telemetry_preclean.select(spike_count_expr.alias("n")).agg(F.sum("n").alias("n")).first()["n"]

    telemetry = (
        apply_resolution(telemetry, "asset_ref", "serial_no", erp, crosswalk)
        .withColumn("is_late", (F.col("ingest_epoch") - F.col("ts_epoch")) > F.lit(3600.0))
        .withColumn("is_in_window", F.col("ts_epoch") < F.lit(CUTOFF_EPOCH))
        .withColumn("event_ts_utc", F.to_timestamp(F.from_unixtime(F.col("ts_epoch"))))
        .withColumn("day", F.floor(F.col("ts_epoch") / F.lit(DAY_SECONDS)).cast("long"))
        .withColumn("is_run", F.col("engine_state") == F.lit("RUN"))
    )

    return telemetry, nulled_spikes


# %%
bronze_telematics = read_table("bronze.telematics_events")
bronze_cmms = read_table("bronze.cmms_work_orders")
bronze_erp = read_table("bronze.erp_assets")
bronze_sites = read_table("bronze.site_master")
bronze_crosswalk = read_table("bronze.asset_crosswalk")

telemetry, telemetry_out_of_range_count = build_silver_telemetry(bronze_telematics, bronze_erp, bronze_crosswalk)

sites_with_tz = bronze_sites.select("site_code", "timezone")
work_orders = (
    bronze_cmms.join(F.broadcast(sites_with_tz), "site_code", "left")
    .withColumn("opened_local_ts", F.to_timestamp("opened_local", "yyyy-MM-dd HH:mm"))
    .withColumn(
        "closed_local_ts",
        F.when(F.trim(F.coalesce(F.col("closed_local"), F.lit(""))) == "", F.lit(None)).otherwise(
            F.to_timestamp("closed_local", "yyyy-MM-dd HH:mm")
        ),
    )
    .withColumn("opened_epoch", F.unix_timestamp(F.to_utc_timestamp(F.col("opened_local_ts"), F.col("timezone"))).cast("double"))
    .withColumn("closed_epoch", F.unix_timestamp(F.to_utc_timestamp(F.col("closed_local_ts"), F.col("timezone"))).cast("double"))
    .drop("opened_local_ts", "closed_local_ts")
    .withColumn("is_time_anomaly", F.col("closed_epoch") < F.col("opened_epoch"))
    .withColumn("opened_fix", F.when(F.col("is_time_anomaly"), F.col("closed_epoch")).otherwise(F.col("opened_epoch")))
    .withColumn("closed_fix", F.when(F.col("is_time_anomaly"), F.col("opened_epoch")).otherwise(F.col("closed_epoch")))
)

work_orders = apply_resolution(work_orders, "asset_tag", "serial_number", bronze_erp, bronze_crosswalk)

dup_window = Window.partitionBy("erp_asset_id", "failure_code").orderBy(F.col("opened_fix").asc(), F.col("wo_number").asc())
work_orders = (
    work_orders.withColumn(
        "_cm_rank_source",
        F.when((F.col("wo_type") == "CM") & F.col("erp_asset_id").isNotNull(), F.lit(1)).otherwise(F.lit(0)),
    )
    .withColumn("prev_opened_fix", F.when(F.col("_cm_rank_source") == 1, F.lag("opened_fix").over(dup_window)))
    .withColumn("prev_wo_number", F.when(F.col("_cm_rank_source") == 1, F.lag("wo_number").over(dup_window)))
    .withColumn(
        "is_duplicate",
        (
            (F.col("wo_type") == "CM")
            & F.col("erp_asset_id").isNotNull()
            & F.col("prev_opened_fix").isNotNull()
            & ((F.col("opened_fix") - F.col("prev_opened_fix")) <= F.lit(3600.0))
        ),
    )
    .withColumn("duplicate_of", F.when(F.col("is_duplicate"), F.col("prev_wo_number")).otherwise(F.lit("")))
    .withColumn("status_open", F.col("status") == F.lit("Open"))
    .drop("_cm_rank_source", "prev_opened_fix", "prev_wo_number")
)

write_table(telemetry, "silver.telemetry")
write_table(work_orders, "silver.work_orders")

# %%
telemetry_counts = (
    read_table("silver.telemetry")
    .groupBy("resolution_method")
    .count()
    .collect()
)
telemetry_resolution_counts = {row["resolution_method"]: row["count"] for row in telemetry_counts}

work_order_counts = (
    read_table("silver.work_orders")
    .groupBy("resolution_method")
    .count()
    .collect()
)
work_order_resolution_counts = {row["resolution_method"]: row["count"] for row in work_order_counts}

silver_telematics = read_table("silver.telemetry")
silver_work_orders = read_table("silver.work_orders")

actual_metrics = {
    "silver_telemetry_rows": silver_telematics.count(),
    "silver_work_order_rows": silver_work_orders.count(),
    "late_rows": silver_telematics.where(F.col("is_late") & F.col("is_in_window")).count(),
    "duplicate_work_orders": silver_work_orders.where(F.col("is_duplicate")).count(),
    "time_anomalies": silver_work_orders.where(F.col("is_time_anomaly")).count(),
    "nulled_spikes": telemetry_out_of_range_count,
}

expected_resolution_telematics = {
    "EXACT_NORM": 196810,
    "SERIAL": 4350,
    "CROSSWALK": 2180,
    "UNRESOLVED": 4351,
}
expected_resolution_cmms = {
    "EXACT_NORM": 2305,
    "SERIAL": 28,
    "CROSSWALK": 18,
    "UNRESOLVED": 8,
}

expected_metrics = {
    "silver_telemetry_rows": 207691,
    "silver_work_order_rows": 2359,
    "late_rows": 2066,
    "duplicate_work_orders": 6,
    "time_anomalies": 8,
    "nulled_spikes": 217,
}

for metric_name, expected_value in expected_metrics.items():
    actual_value = actual_metrics[metric_name]
    if actual_value != expected_value:
        raise AssertionError(f"{metric_name} mismatch: expected {expected_value}, got {actual_value}")

if telemetry_resolution_counts != expected_resolution_telematics:
    raise AssertionError(
        f"Telematics resolution mismatch: expected {expected_resolution_telematics}, got {telemetry_resolution_counts}"
    )

if work_order_resolution_counts != expected_resolution_cmms:
    raise AssertionError(
        f"CMMS resolution mismatch: expected {expected_resolution_cmms}, got {work_order_resolution_counts}"
    )

print(
    "Silver layer matches the contract: "
    f"{actual_metrics['silver_telemetry_rows']} telemetry rows, "
    f"{actual_metrics['duplicate_work_orders']} duplicate CM work orders flagged, and "
    f"{actual_metrics['time_anomalies']} swapped CMMS timestamps corrected."
)

# %%
# Optional drift batch: same silver function, applied to bronze.telematics_events_drift
# when nb_01 landed it. Every October timestamp is >= CUTOFF_EPOCH by construction, so
# is_in_window is False for all drift rows - that is a per-row cutoff flag, unrelated to
# which table a row lives in. No new assertion here: compare_ground_truth.py validates
# silver.telemetry_drift against the reference pipeline.
drift_bronze_rows = 0
drift_silver_rows = 0
if table_exists("bronze.telematics_events_drift"):
    bronze_telematics_drift = read_table("bronze.telematics_events_drift")
    drift_bronze_rows = bronze_telematics_drift.count()
    telemetry_drift, _ = build_silver_telemetry(bronze_telematics_drift, bronze_erp, bronze_crosswalk)
    write_table(telemetry_drift, "silver.telemetry_drift")
    drift_silver_rows = read_table("silver.telemetry_drift").count()
    print(
        "Drift silver layer built: "
        f"silver.telemetry_drift = {drift_silver_rows} rows (from {drift_bronze_rows} bronze rows)."
    )
else:
    print("No bronze.telematics_events_drift table found: silver.telemetry_drift skipped (base-only dataset).")

# %%
summary = {
    "notebook": NOTEBOOK_NAME,
    "status": "ok",
    "batch_id": batch_id,
    "mode": mode,
    "data_cutoff_utc": data_cutoff_utc,
    "is_fabric": IS_FABRIC,
    "storage_format": "delta" if IS_FABRIC else local_storage_format,
    "metrics": actual_metrics,
    "telematics_resolution": telemetry_resolution_counts,
    "cmms_resolution": work_order_resolution_counts,
    "drift_bronze_rows": drift_bronze_rows,
    "drift_silver_rows": drift_silver_rows,
}
json_exit(summary)