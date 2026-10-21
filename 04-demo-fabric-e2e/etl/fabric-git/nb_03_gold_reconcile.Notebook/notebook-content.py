# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************

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

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "tags": [
# META     "parameters"
# META   ]
# META }

# CELL ********************

import json
from pathlib import Path

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

try:
    notebookutils
    IS_FABRIC = True
except NameError:
    IS_FABRIC = False
NOTEBOOK_NAME = "nb_03_gold_reconcile"
NOTEBOOK_SUMMARY = {}
DAY_SECONDS = 86400.0
MATCH_BEFORE_SECONDS = DAY_SECONDS
MATCH_AFTER_SECONDS = 7.0 * DAY_SECONDS
SILENT_DAYS = 14.0
CUTOFF_EPOCH = 1790812800.0
EXCEPTION_ORDER = [
    "UNRESOLVED_ASSET_TELEMATICS",
    "UNRESOLVED_ASSET_CMMS",
    "RETIRED_ASSET_REPORTING",
    "ACTIVE_ASSET_SILENT",
    "FAULT_WITHOUT_WO",
    "WO_WITHOUT_FAULT",
    "WO_TIME_ANOMALY",
    "DUPLICATE_WO",
]
CLASS_CODES = {
    "Excavator": 1,
    "WheelLoader": 2,
    "Bulldozer": 3,
    "DumpTruck": 4,
    "MobileCrane": 5,
    "Compactor": 6,
    "Paver": 7,
    "Generator": 8,
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


def json_exit(summary: dict) -> None:
    global NOTEBOOK_SUMMARY
    NOTEBOOK_SUMMARY = summary
    payload = json.dumps(summary, sort_keys=True)
    if IS_FABRIC:
        notebookutils.notebook.exit(payload)
    print(payload)


def iso_utc_from_epoch(epoch_col: str) -> F.Column:
    return F.when(F.col(epoch_col).isNull(), F.lit("")).otherwise(
        F.date_format(F.to_timestamp(F.from_unixtime(F.col(epoch_col))), "yyyy-MM-dd'T'HH:mm:ss'Z'")
    )


class_map_expr = F.create_map([value for pair in CLASS_CODES.items() for value in (F.lit(pair[0]), F.lit(pair[1]))])
exception_order_expr = F.create_map([value for index, name in enumerate(EXCEPTION_ORDER) for value in (F.lit(name), F.lit(index))])

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

telemetry = read_table("silver.telemetry")
work_orders = read_table("silver.work_orders")
erp = read_table("bronze.erp_assets")
sites = read_table("bronze.site_master")
faults = read_table("bronze.fault_code_catalog")

resolved_telemetry = telemetry.where(F.col("erp_asset_id").isNotNull() & F.col("is_in_window"))
resolved_work_orders = work_orders.where(F.col("erp_asset_id").isNotNull() & (~F.col("is_duplicate")))
asset_site = erp.select("erp_asset_id", "site_code")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

dim_summary = (
    resolved_telemetry.groupBy("erp_asset_id")
    .agg(
        F.min_by("device_id", F.struct(F.col("ts_epoch"), F.col("ingest_epoch"))).alias("device_id"),
        F.count("*").alias("telemetry_rows"),
        F.min("ts_epoch").alias("first_epoch"),
        F.max("ts_epoch").alias("last_epoch"),
    )
)

last_hours_window = Window.partitionBy("erp_asset_id").orderBy(F.col("ts_epoch").desc(), F.col("ingest_epoch").desc())
last_hours = (
    resolved_telemetry.withColumn("_rn", F.row_number().over(last_hours_window))
    .where(F.col("_rn") == 1)
    .select("erp_asset_id", F.col("engine_hours").alias("last_engine_hours"))
)

dim_asset = (
    erp.join(dim_summary, "erp_asset_id", "left")
    .join(last_hours, "erp_asset_id", "left")
    .withColumn("equipment_class_code", class_map_expr[F.col("equipment_class")])
    .withColumn("telemetry_rows", F.coalesce(F.col("telemetry_rows"), F.lit(0)))
    .withColumn("first_telemetry_utc", iso_utc_from_epoch("first_epoch"))
    .withColumn("last_telemetry_utc", iso_utc_from_epoch("last_epoch"))
    .withColumn(
        "asset_age_years",
        F.round(
            (
                F.datediff(F.to_date(F.lit(data_cutoff_utc[:10])), F.to_date("acquisition_date")).cast("double")
                / F.lit(365.25)
            ),
            2,
        ),
    )
    .withColumn("has_telemetry", F.col("telemetry_rows") > F.lit(0))
    .select(
        "erp_asset_id",
        "asset_name",
        "equipment_class",
        "equipment_class_code",
        "manufacturer",
        "model",
        "serial_number",
        "acquisition_date",
        "acquisition_cost_eur",
        "site_code",
        "cost_center",
        "status",
        "retirement_date",
        "telematics_device_installed",
        "device_id",
        "has_telemetry",
        "telemetry_rows",
        "first_telemetry_utc",
        "last_telemetry_utc",
        "last_engine_hours",
        "asset_age_years",
    )
)

dim_site = sites.select(
    "site_code",
    "site_name",
    "country",
    "timezone",
    "latitude",
    "longitude",
    "project_type",
).dropDuplicates(["site_code"])

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

fault_occurrences = (
    resolved_telemetry.select("erp_asset_id", "ts_epoch", "day", F.explode_outer("fault_codes").alias("fault_code"))
    .where(F.col("fault_code").isNotNull())
    .join(F.broadcast(faults.select("fault_code", "severity", "system")), "fault_code", "left")
)

episode_window = Window.partitionBy("erp_asset_id", "fault_code").orderBy(F.col("ts_epoch").asc())
episode_grouped = (
    fault_occurrences.withColumn("prev_ts", F.lag("ts_epoch").over(episode_window))
    .withColumn(
        "episode_break",
        F.when(F.col("prev_ts").isNull() | ((F.col("ts_epoch") - F.col("prev_ts")) > F.lit(DAY_SECONDS)), F.lit(1)).otherwise(F.lit(0)),
    )
    .withColumn("episode_seq", F.sum("episode_break").over(episode_window))
    .groupBy("erp_asset_id", "fault_code", "severity", "system", "episode_seq")
    .agg(
        F.min("ts_epoch").alias("start"),
        F.max("ts_epoch").alias("end"),
        F.count("*").alias("n_records"),
    )
)

episode_id_window = Window.orderBy(F.col("start").asc(), F.col("erp_asset_id").asc(), F.col("fault_code").asc())
episodes = (
    episode_grouped.withColumn("episode_id", F.format_string("EP-%06d", F.row_number().over(episode_id_window)))
    .withColumn(
        "is_significant",
        (F.col("severity") == F.lit("CRIT"))
        | ((F.col("severity") == F.lit("WARN")) & (F.col("n_records") >= F.lit(3))),
    )
    .join(F.broadcast(asset_site), "erp_asset_id", "left")
)

fact_work_order = (
    resolved_work_orders.drop("site_code").join(F.broadcast(asset_site), "erp_asset_id", "left")
    .withColumn("opened_utc", iso_utc_from_epoch("opened_fix"))
    .withColumn("closed_utc", iso_utc_from_epoch("closed_fix"))
    .withColumn("duration_hours", F.round((F.col("closed_fix") - F.col("opened_fix")) / F.lit(3600.0), 2))
    .select(
        "wo_number",
        "erp_asset_id",
        "site_code",
        "wo_type",
        "priority",
        "status",
        "failure_code",
        "failure_system",
        "description",
        "opened_utc",
        "closed_utc",
        "duration_hours",
        "labor_hours",
        "parts_cost_eur",
        "technician_id",
        "reported_by",
        F.col("resolution_method").alias("id_resolution"),
        F.col("is_time_anomaly").alias("times_corrected"),
        "opened_fix",
    )
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

cm_work_orders = fact_work_order.where(F.col("wo_type") == "CM")
matches = (
    episodes.where(F.col("is_significant"))
    .select("episode_id", "erp_asset_id", "fault_code", "system", "severity", "start", "end")
    .join(cm_work_orders.select("wo_number", "erp_asset_id", "opened_fix", "failure_system"), "erp_asset_id", "inner")
    .where(
        (F.col("opened_fix") >= (F.col("start") - F.lit(MATCH_BEFORE_SECONDS)))
        & (F.col("opened_fix") <= (F.col("end") + F.lit(MATCH_AFTER_SECONDS)))
    )
    .withColumn("delta_hours", F.round((F.col("opened_fix") - F.col("start")) / F.lit(3600.0), 2))
    .withColumn("same_system", F.col("system") == F.col("failure_system"))
)

best_match_window = Window.partitionBy("episode_id").orderBy(F.abs(F.col("delta_hours")).asc(), F.col("wo_number").asc())
fact_recon_match = (
    matches.withColumn("_rn", F.row_number().over(best_match_window))
    .withColumn("is_best_for_episode", F.col("_rn") == F.lit(1))
    .drop("_rn", "fault_code", "system", "severity", "start", "end", "opened_fix", "failure_system")
    .select("episode_id", "wo_number", "erp_asset_id", "delta_hours", "same_system", "is_best_for_episode")
)

best_match_lookup = fact_recon_match.where(F.col("is_best_for_episode")).select(
    "episode_id",
    F.col("wo_number").alias("matched_wo_number"),
)
matched_episode_ids = fact_recon_match.select("episode_id").dropDuplicates()

fact_fault_episode = (
    episodes.join(best_match_lookup, "episode_id", "left")
    .join(matched_episode_ids.withColumn("has_match", F.lit(True)), "episode_id", "left")
    .withColumn(
        "recon_status",
        F.when(~F.col("is_significant"), F.lit("NOT_APPLICABLE"))
        .when(F.col("has_match") == F.lit(True), F.lit("MATCHED"))
        .when(F.col("end") <= F.lit(CUTOFF_EPOCH - MATCH_AFTER_SECONDS), F.lit("UNMATCHED"))
        .otherwise(F.lit("PENDING")),
    )
    .withColumn("matched_wo_number", F.coalesce(F.col("matched_wo_number"), F.lit("")))
    .withColumn("start_utc", iso_utc_from_epoch("start"))
    .withColumn("end_utc", iso_utc_from_epoch("end"))
    .withColumn("month", F.date_format(F.to_timestamp(F.from_unixtime(F.col("start"))), "yyyy-MM"))
    .select(
        "episode_id",
        "erp_asset_id",
        "site_code",
        "fault_code",
        "system",
        "severity",
        "start_utc",
        "end_utc",
        "n_records",
        "is_significant",
        "recon_status",
        "matched_wo_number",
        "month",
        "start",
        "end",
    )
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

run_daily = (
    resolved_telemetry.where(F.col("is_run"))
    .groupBy("erp_asset_id", "day")
    .agg(
        F.avg("engine_temp_c").alias("temp_mean"),
        F.max("engine_temp_c").alias("temp_max"),
        F.avg("oil_pressure_kpa").alias("oil_mean"),
        F.min("oil_pressure_kpa").alias("oil_min"),
        F.avg("hydraulic_pressure_bar").alias("hyd_mean"),
        F.min("hydraulic_pressure_bar").alias("hyd_min"),
        F.avg("vibration_mm_s").alias("vib_mean"),
        F.max("vibration_mm_s").alias("vib_max"),
        F.avg("fuel_rate_lph").alias("fuel_mean"),
        F.avg("load_pct").alias("load_mean"),
        F.avg("idle_pct").alias("idle_mean"),
    )
)

retire_days = dim_asset.select(
    "erp_asset_id",
    "site_code",
    F.datediff(F.to_date("retirement_date"), F.to_date(F.lit("1970-01-01"))).cast("double").alias("retire_day"),
)

fact_telemetry_daily = (
    resolved_telemetry.groupBy("erp_asset_id", "day")
    .agg(
        F.count("*").alias("n_readings"),
        F.sum(F.when(F.col("is_run"), F.lit(1)).otherwise(F.lit(0))).alias("n_run"),
        F.max("engine_hours").alias("engine_hours"),
    )
    .join(run_daily, ["erp_asset_id", "day"], "left")
    .join(retire_days, "erp_asset_id", "left")
    .withColumn("run_share", F.col("n_run") / F.col("n_readings"))
    .withColumn(
        "is_after_retirement",
        F.when(F.col("retire_day").isNotNull() & (F.col("day") >= F.col("retire_day")), F.lit(True)).otherwise(F.lit(False)),
    )
    .withColumn("obs_date", F.date_format(F.to_timestamp(F.from_unixtime(F.col("day") * F.lit(DAY_SECONDS))), "yyyy-MM-dd"))
    .select(
        "erp_asset_id",
        "site_code",
        "obs_date",
        "n_readings",
        "n_run",
        "engine_hours",
        "temp_mean",
        "temp_max",
        "oil_mean",
        "oil_min",
        "hyd_mean",
        "hyd_min",
        "vib_mean",
        "vib_max",
        "fuel_mean",
        "load_mean",
        "idle_mean",
        "run_share",
        "is_after_retirement",
    )
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

unresolved_telematics = (
    telemetry.where((F.col("resolution_method") == "UNRESOLVED") & F.col("is_in_window"))
    .groupBy("device_id")
    .agg(
        F.min("ts_epoch").alias("event_epoch"),
        F.count("*").alias("n_records"),
        F.min_by("asset_ref", F.struct(F.col("ts_epoch"), F.col("ingest_epoch"))).alias("first_asset_ref"),
    )
    .select(
        F.lit("UNRESOLVED_ASSET_TELEMATICS").alias("exception_type"),
        F.lit("").alias("subtype"),
        F.lit("MEDIUM").alias("severity"),
        F.lit("").alias("erp_asset_id"),
        F.lit("").alias("site_code"),
        F.col("device_id").alias("reference_id"),
        "event_epoch",
        "n_records",
        F.concat(F.lit("asset_ref="), F.coalesce(F.col("first_asset_ref"), F.lit("null")), F.lit(" matches no ERP asset, serial or crosswalk row")).alias("detail"),
    )
)

unresolved_cmms = (
    work_orders.where(F.col("resolution_method") == "UNRESOLVED")
    .groupBy("asset_tag")
    .agg(F.min_by("site_code", F.col("opened_fix")).alias("site_code"), F.min("opened_fix").alias("event_epoch"), F.count("*").alias("n_records"))
    .select(
        F.lit("UNRESOLVED_ASSET_CMMS").alias("exception_type"),
        F.lit("").alias("subtype"),
        F.lit("MEDIUM").alias("severity"),
        F.lit("").alias("erp_asset_id"),
        "site_code",
        F.col("asset_tag").alias("reference_id"),
        "event_epoch",
        "n_records",
        F.concat(F.col("n_records").cast("string"), F.lit(" work order(s) carry an asset tag that matches nothing in ERP")).alias("detail"),
    )
)

retired_reporting = (
    telemetry.join(
        dim_asset.select(
            "erp_asset_id",
            "site_code",
            "status",
            "retirement_date",
            F.datediff(F.to_date("retirement_date"), F.to_date(F.lit("1970-01-01"))).cast("double").alias("retire_day"),
        ),
        "erp_asset_id",
        "inner",
    )
    .where(F.col("is_in_window") & F.col("status").isin("Retired", "Disposed") & F.col("retire_day").isNotNull() & (F.col("day") >= F.col("retire_day")))
    .groupBy("erp_asset_id", "site_code", "status", "retirement_date")
    .agg(F.min("ts_epoch").alias("event_epoch"), F.count("*").alias("n_records"))
    .select(
        F.lit("RETIRED_ASSET_REPORTING").alias("exception_type"),
        F.lit("").alias("subtype"),
        F.lit("MEDIUM").alias("severity"),
        "erp_asset_id",
        "site_code",
        F.col("erp_asset_id").alias("reference_id"),
        "event_epoch",
        "n_records",
        F.concat(F.lit("ERP status "), F.col("status"), F.lit(" since "), F.col("retirement_date"), F.lit(" but the device keeps sending data")).alias("detail"),
    )
)

activity_silence = (
    dim_asset.where((F.col("status") == "Active") & (F.col("telematics_device_installed") == "Y"))
    .withColumn(
        "subtype",
        F.when(F.col("last_telemetry_utc") == "", F.lit("NO_LINKED_TELEMETRY")).when(
            F.unix_timestamp(F.to_timestamp("last_telemetry_utc")) < F.lit(CUTOFF_EPOCH - SILENT_DAYS * DAY_SECONDS),
            F.lit("STOPPED_REPORTING"),
        ),
    )
    .where(F.col("subtype").isNotNull())
    .withColumn(
        "event_epoch",
        F.when(F.col("subtype") == "STOPPED_REPORTING", F.unix_timestamp(F.to_timestamp("last_telemetry_utc")).cast("double")),
    )
    .withColumn(
        "detail",
        F.when(
            F.col("subtype") == "NO_LINKED_TELEMETRY",
            F.lit("ERP says a device is installed but no telemetry resolves to it"),
        ).otherwise(
            F.concat(
                F.lit("no telemetry for "),
                F.floor((F.lit(CUTOFF_EPOCH) - F.unix_timestamp(F.to_timestamp("last_telemetry_utc")).cast("double")) / F.lit(DAY_SECONDS)).cast("int").cast("string"),
                F.lit(" days"),
            )
        ),
    )
    .select(
        F.lit("ACTIVE_ASSET_SILENT").alias("exception_type"),
        "subtype",
        F.lit("MEDIUM").alias("severity"),
        "erp_asset_id",
        "site_code",
        F.col("erp_asset_id").alias("reference_id"),
        "event_epoch",
        F.lit(0).alias("n_records"),
        "detail",
    )
)

fault_without_wo = (
    fact_fault_episode.where(
        F.col("is_significant") & (F.col("recon_status") == "UNMATCHED")
    ).select(
        F.lit("FAULT_WITHOUT_WO").alias("exception_type"),
        F.col("severity").alias("subtype"),
        F.when(F.col("severity") == "CRIT", F.lit("HIGH")).otherwise(F.lit("MEDIUM")).alias("severity"),
        "erp_asset_id",
        "site_code",
        F.col("episode_id").alias("reference_id"),
        F.col("start").alias("event_epoch"),
        "n_records",
        F.concat(F.col("fault_code"), F.lit(" episode with no corrective work order within 7 days")).alias("detail"),
    )
)

telemetry_coverage = resolved_telemetry.groupBy("erp_asset_id").agg(F.max("ts_epoch").alias("last_ts_epoch"))
matched_wo_numbers = fact_recon_match.select("wo_number").dropDuplicates()
wo_without_fault = (
    cm_work_orders.join(matched_wo_numbers.withColumn("matched", F.lit(True)), "wo_number", "left")
    .join(telemetry_coverage, "erp_asset_id", "left")
    .where(F.col("matched").isNull())
    .withColumn(
        "subtype",
        F.when(F.col("last_ts_epoch").isNull(), F.lit("NO_TELEMETRY"))
        .when(F.col("last_ts_epoch") < (F.col("opened_fix") - F.lit(DAY_SECONDS)), F.lit("TELEMETRY_STOPPED"))
        .otherwise(F.lit("NO_FAULT_SIGNAL")),
    )
    .select(
        F.lit("WO_WITHOUT_FAULT").alias("exception_type"),
        "subtype",
        F.lit("LOW").alias("severity"),
        "erp_asset_id",
        "site_code",
        F.col("wo_number").alias("reference_id"),
        F.col("opened_fix").alias("event_epoch"),
        F.lit(1).alias("n_records"),
        F.concat(F.lit("corrective WO "), F.col("failure_code"), F.lit(" without a matching fault episode")).alias("detail"),
    )
)

wo_time_anomaly = (
    work_orders.where(F.col("is_time_anomaly"))
    .select(
        F.lit("WO_TIME_ANOMALY").alias("exception_type"),
        F.lit("").alias("subtype"),
        F.lit("LOW").alias("severity"),
        F.coalesce("erp_asset_id", F.lit("")).alias("erp_asset_id"),
        "site_code",
        F.col("wo_number").alias("reference_id"),
        F.col("opened_fix").alias("event_epoch"),
        F.lit(1).alias("n_records"),
        F.lit("closed before opened in the CMMS (timestamps swapped)").alias("detail"),
    )
)

duplicate_wo = (
    work_orders.where(F.col("is_duplicate"))
    .select(
        F.lit("DUPLICATE_WO").alias("exception_type"),
        F.lit("").alias("subtype"),
        F.lit("LOW").alias("severity"),
        "erp_asset_id",
        "site_code",
        F.col("wo_number").alias("reference_id"),
        F.col("opened_fix").alias("event_epoch"),
        F.lit(1).alias("n_records"),
        F.concat(F.lit("duplicate of "), F.col("duplicate_of"), F.lit(" (same asset + failure code within 60 min)")).alias("detail"),
    )
)

fact_recon_exception = (
    unresolved_telematics.unionByName(unresolved_cmms)
    .unionByName(retired_reporting)
    .unionByName(activity_silence)
    .unionByName(fault_without_wo)
    .unionByName(wo_without_fault)
    .unionByName(wo_time_anomaly)
    .unionByName(duplicate_wo)
    .withColumn("_order", exception_order_expr[F.col("exception_type")])
)

exception_id_window = Window.orderBy(F.col("_order").asc(), F.col("event_epoch").asc_nulls_last(), F.col("reference_id").asc())
fact_recon_exception = (
    fact_recon_exception.withColumn("exception_id", F.format_string("EXC-%05d", F.row_number().over(exception_id_window)))
    .withColumn("event_utc", iso_utc_from_epoch("event_epoch"))
    .select(
        "exception_id",
        "exception_type",
        "subtype",
        "severity",
        "erp_asset_id",
        "site_code",
        "reference_id",
        "event_utc",
        "n_records",
        "detail",
        "event_epoch",
    )
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

significant = fact_fault_episode.where(F.col("is_significant"))
best_delta = fact_recon_match.where(F.col("is_best_for_episode")).select("episode_id", "delta_hours")
summary_base = (
    significant.withColumn("crit_episodes", F.when(F.col("severity") == "CRIT", 1).otherwise(0))
    .withColumn("crit_matched", F.when((F.col("severity") == "CRIT") & (F.col("recon_status") == "MATCHED"), 1).otherwise(0))
    .withColumn("crit_unmatched", F.when((F.col("severity") == "CRIT") & (F.col("recon_status") == "UNMATCHED"), 1).otherwise(0))
    .withColumn("crit_pending", F.when((F.col("severity") == "CRIT") & (F.col("recon_status") == "PENDING"), 1).otherwise(0))
    .withColumn("warn_episodes_3plus", F.when(F.col("severity") == "WARN", 1).otherwise(0))
    .withColumn("warn_matched", F.when((F.col("severity") == "WARN") & (F.col("recon_status") == "MATCHED"), 1).otherwise(0))
    .withColumn("warn_unmatched", F.when((F.col("severity") == "WARN") & (F.col("recon_status") == "UNMATCHED"), 1).otherwise(0))
    .join(best_delta, "episode_id", "left")
    .withColumn("crit_delta", F.when(F.col("severity") == "CRIT", F.col("delta_hours")))
)

summary_episodes = (
    summary_base.groupBy("month", "site_code")
    .agg(
        F.sum("crit_episodes").alias("crit_episodes"),
        F.sum("crit_matched").alias("crit_matched"),
        F.sum("crit_unmatched").alias("crit_unmatched"),
        F.sum("crit_pending").alias("crit_pending"),
        F.sum("warn_episodes_3plus").alias("warn_episodes_3plus"),
        F.sum("warn_matched").alias("warn_matched"),
        F.sum("warn_unmatched").alias("warn_unmatched"),
        F.avg("crit_delta").alias("avg_crit_fault_to_wo_hours"),
    )
)

summary_work_orders = (
    cm_work_orders.withColumn("month", F.substring("opened_utc", 1, 7))
    .join(fact_recon_match.select("wo_number").dropDuplicates().withColumn("with_fault", F.lit(1)), "wo_number", "left")
    .groupBy("month", "site_code")
    .agg(
        F.count("*").alias("cm_work_orders"),
        F.sum(F.coalesce(F.col("with_fault"), F.lit(0))).alias("cm_wo_with_fault_signal"),
        F.sum("duration_hours").alias("cm_repair_hours"),
    )
)

agg_recon_monthly = (
    summary_episodes.join(summary_work_orders, ["month", "site_code"], "full_outer")
    .fillna(
        {
            "crit_episodes": 0,
            "crit_matched": 0,
            "crit_unmatched": 0,
            "crit_pending": 0,
            "warn_episodes_3plus": 0,
            "warn_matched": 0,
            "warn_unmatched": 0,
            "cm_work_orders": 0,
            "cm_wo_with_fault_signal": 0,
            "cm_repair_hours": 0.0,
        }
    )
    .withColumn(
        "crit_match_rate",
        F.round(
            F.when(
                (F.col("crit_matched") + F.col("crit_unmatched")) > 0,
                F.col("crit_matched") / (F.col("crit_matched") + F.col("crit_unmatched")),
            ),
            4,
        ),
    )
    .withColumn("cm_wo_without_fault_signal", F.col("cm_work_orders") - F.col("cm_wo_with_fault_signal"))
    .withColumn("avg_crit_fault_to_wo_hours", F.round(F.col("avg_crit_fault_to_wo_hours"), 2))
    .withColumn("cm_repair_hours", F.round(F.col("cm_repair_hours"), 2))
    .select(
        "month",
        "site_code",
        "crit_episodes",
        "crit_matched",
        "crit_unmatched",
        "crit_pending",
        "crit_match_rate",
        "warn_episodes_3plus",
        "warn_matched",
        "warn_unmatched",
        "cm_work_orders",
        "cm_wo_with_fault_signal",
        "cm_wo_without_fault_signal",
        "avg_crit_fault_to_wo_hours",
        "cm_repair_hours",
    )
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

write_table(dim_asset, "gold.dim_asset")
write_table(dim_site, "gold.dim_site")
write_table(fact_telemetry_daily, "gold.fact_telemetry_daily")
write_table(fact_fault_episode.drop("start", "end"), "gold.fact_fault_episode")
write_table(fact_work_order.drop("opened_fix"), "gold.fact_work_order")
write_table(fact_recon_match, "gold.fact_recon_match")
write_table(fact_recon_exception.drop("event_epoch"), "gold.fact_recon_exception")
write_table(agg_recon_monthly, "gold.agg_recon_monthly")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

gold_counts = {
    "dim_asset": read_table("gold.dim_asset").count(),
    "dim_site": read_table("gold.dim_site").count(),
    "fact_telemetry_daily": read_table("gold.fact_telemetry_daily").count(),
    "fact_fault_episode": read_table("gold.fact_fault_episode").count(),
    "fact_work_order": read_table("gold.fact_work_order").count(),
    "fact_recon_match": read_table("gold.fact_recon_match").count(),
    "fact_recon_exception": read_table("gold.fact_recon_exception").count(),
    "agg_recon_monthly": read_table("gold.agg_recon_monthly").count(),
}

severity_counts = {
    row["severity"]: row["count"]
    for row in read_table("gold.fact_fault_episode").groupBy("severity").count().collect()
}
significant_status = {
    row["recon_status"]: row["count"]
    for row in read_table("gold.fact_fault_episode").where(F.col("is_significant")).groupBy("recon_status").count().collect()
}
crit_status = {
    row["recon_status"]: row["count"]
    for row in read_table("gold.fact_fault_episode").where(F.col("severity") == "CRIT").groupBy("recon_status").count().collect()
}
exception_counts = {
    row["exception_type"]: row["count"]
    for row in read_table("gold.fact_recon_exception").groupBy("exception_type").count().collect()
}

best_crit_matches = (
    read_table("gold.fact_recon_match").where(F.col("is_best_for_episode"))
    .join(read_table("gold.fact_fault_episode").select("episode_id", "severity"), "episode_id", "inner")
    .where(F.col("severity") == "CRIT")
)

crit_match_rate = round(
    crit_status["MATCHED"] / (crit_status["MATCHED"] + crit_status["UNMATCHED"]),
    4,
)
median_crit_delay = best_crit_matches.agg(F.expr("percentile_approx(delta_hours, 0.5, 100000)").alias("median")).first()["median"]
corrective_work_orders = read_table("gold.fact_work_order").where(F.col("wo_type") == "CM").count()
matched_work_orders = read_table("gold.fact_recon_match").select("wo_number").dropDuplicates().count()
assets_with_telemetry = read_table("gold.dim_asset").where(F.col("has_telemetry")).count()
active_with_telemetry = read_table("gold.dim_asset").where(F.col("has_telemetry") & (F.col("status") == "Active")).count()

expected_gold_counts = {
    "dim_asset": 316,
    "dim_site": 12,
    "fact_telemetry_daily": 51353,
    "fact_fault_episode": 3459,
    "fact_work_order": 2345,
    "fact_recon_match": 468,
    "fact_recon_exception": 211,
    "agg_recon_monthly": 72,
}
expected_severity_counts = {"CRIT": 399, "WARN": 1406, "INFO": 1654}
expected_significant_status = {"MATCHED": 455, "UNMATCHED": 91, "PENDING": 11}
expected_crit_status = {"MATCHED": 367, "UNMATCHED": 30, "PENDING": 2}
expected_exception_counts = {
    "ACTIVE_ASSET_SILENT": 12,
    "DUPLICATE_WO": 6,
    "FAULT_WITHOUT_WO": 91,
    "RETIRED_ASSET_REPORTING": 6,
    "UNRESOLVED_ASSET_CMMS": 3,
    "UNRESOLVED_ASSET_TELEMATICS": 6,
    "WO_TIME_ANOMALY": 8,
    "WO_WITHOUT_FAULT": 79,
}

for metric_name, expected_value in expected_gold_counts.items():
    if gold_counts[metric_name] != expected_value:
        raise AssertionError(f"{metric_name} row count mismatch: expected {expected_value}, got {gold_counts[metric_name]}")

if severity_counts != expected_severity_counts:
    raise AssertionError(f"Fault severity mismatch: expected {expected_severity_counts}, got {severity_counts}")
if significant_status != expected_significant_status:
    raise AssertionError(f"Significant episode status mismatch: expected {expected_significant_status}, got {significant_status}")
if crit_status != expected_crit_status:
    raise AssertionError(f"CRIT status mismatch: expected {expected_crit_status}, got {crit_status}")
if exception_counts != expected_exception_counts:
    raise AssertionError(f"Exception count mismatch: expected {expected_exception_counts}, got {exception_counts}")
if round(float(median_crit_delay), 2) != 5.58:
    raise AssertionError(f"Median CRIT delay mismatch: expected 5.58, got {median_crit_delay}")
if crit_match_rate != 0.9244:
    raise AssertionError(f"CRIT match rate mismatch: expected 0.9244, got {crit_match_rate}")
if corrective_work_orders != 445 or matched_work_orders != 366:
    raise AssertionError(
        f"Corrective work order coverage mismatch: expected 445/366, got {corrective_work_orders}/{matched_work_orders}"
    )
if assets_with_telemetry != 284 or active_with_telemetry != 274:
    raise AssertionError(
        f"Telemetry asset coverage mismatch: expected 284/274, got {assets_with_telemetry}/{active_with_telemetry}"
    )

print(
    "Gold reconciliation matches the contract: "
    f"{gold_counts['fact_fault_episode']} episodes, {gold_counts['fact_recon_match']} matches, "
    f"{gold_counts['fact_recon_exception']} exceptions, CRIT match rate {crit_match_rate:.4f}, "
    f"median CRIT delay {float(median_crit_delay):.2f} hours."
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

summary = {
    "notebook": NOTEBOOK_NAME,
    "status": "ok",
    "batch_id": batch_id,
    "mode": mode,
    "data_cutoff_utc": data_cutoff_utc,
    "is_fabric": IS_FABRIC,
    "storage_format": "delta" if IS_FABRIC else local_storage_format,
    "gold_counts": gold_counts,
    "severity_counts": severity_counts,
    "significant_status": significant_status,
    "crit_status": crit_status,
    "exception_counts": exception_counts,
    "crit_match_rate": crit_match_rate,
    "median_crit_delay_hours": round(float(median_crit_delay), 2),
    "corrective_work_orders": corrective_work_orders,
    "matched_work_orders": matched_work_orders,
}
json_exit(summary)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
