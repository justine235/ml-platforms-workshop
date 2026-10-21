from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from pyspark.sql import Window
from pyspark.sql import functions as F


ETL_ROOT = Path(__file__).resolve().parents[1]
KIT_ROOT = ETL_ROOT.parents[1]
ARTIFACT_ROOT = ETL_ROOT / "local-validation" / "artifacts" / "lh_fleet"
GROUND_TRUTH_PATH = KIT_ROOT / "02-demo-data" / "reference_out" / "ground_truth.json"
RESULTS_DIR = ETL_ROOT / "local-validation" / "results"
OUTPUT_JSON = RESULTS_DIR / "ground-truth-compare.json"
OUTPUT_MD = RESULTS_DIR / "ground-truth-compare.md"
DATA_ROOT = Path(os.environ.get("FLEET_RAW_ROOT") or (KIT_ROOT / "02-demo-data" / "data"))
CUTOFF_EPOCH = 1790812800.0  # 2026-10-01T00:00:00Z, same constant as nb_02_silver_clean_resolve
SENSOR_LIMITS = {
    "engine_temp_c": (0.0, 150.0),
    "oil_pressure_kpa": (0.0, 800.0),
    "hydraulic_pressure_bar": (0.0, 450.0),
    "vibration_mm_s": (0.0, 30.0),
    "fuel_rate_lph": (0.0, 200.0),
    "load_pct": (0.0, 100.0),
    "idle_pct": (0.0, 100.0),
}

sys.path.insert(0, str(KIT_ROOT / "02-demo-data"))


def detect_storage_format() -> str:
    delta_log = ARTIFACT_ROOT / "Tables" / "gold" / "dim_asset" / "_delta_log"
    return "delta" if delta_log.exists() else "parquet"


def _prepend_env_bin(env_var: str) -> Path | None:
    home = os.environ.get(env_var)
    if not home:
        return None
    home_path = Path(home)
    bin_dir = home_path / "bin"
    if bin_dir.exists():
        os.environ["PATH"] = f"{bin_dir}{os.pathsep}{os.environ['PATH']}"
    return home_path


def build_spark(storage_format: str):
    from pyspark.sql import SparkSession

    java_home = _prepend_env_bin("JAVA_HOME")
    if java_home is None:
        raise SystemExit(
            "JAVA_HOME is not set. Install JDK 17 and set JAVA_HOME to its install "
            "folder before running this script. On Windows, also set HADOOP_HOME to "
            "a folder whose bin\\ contains winutils.exe and hadoop.dll."
        )
    hadoop_home = _prepend_env_bin("HADOOP_HOME")
    if hadoop_home is not None:
        os.environ.setdefault("hadoop.home.dir", str(hadoop_home))

    if storage_format == "delta":
        from delta import configure_spark_with_delta_pip

        builder = (
            SparkSession.builder.master("local[2]")
            .appName("fleet-ground-truth-compare")
            .config("spark.sql.session.timeZone", "UTC")
            .config("spark.sql.shuffle.partitions", "4")
            .config("spark.driver.memory", "1500m")
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        )
        return configure_spark_with_delta_pip(builder).getOrCreate()

    return (
        SparkSession.builder.master("local[2]")
        .appName("fleet-ground-truth-compare")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.driver.memory", "1500m")
        .getOrCreate()
    )


def read_table(spark, full_name: str, storage_format: str):
    schema_name, table_name = full_name.split(".", 1)
    path = ARTIFACT_ROOT / "Tables" / schema_name / table_name
    return spark.read.format(storage_format).load(str(path))


def expected_metrics(truth: dict) -> list[tuple[str, int | float]]:
    return [
        ("bronze.telematics_events rows", truth["silver"]["telematics"]["bronze_rows"]),
        ("bronze.telematics_events duplicates removed", truth["silver"]["telematics"]["duplicates_removed"]),
        ("bronze.telematics_events out_of_range_values_nulled", truth["silver"]["telematics"]["out_of_range_values_nulled"]),
        ("silver.telemetry rows", truth["silver"]["telematics"]["rows"]),
        ("silver.telemetry late_rows", truth["silver"]["telematics"]["late_rows"]),
        ("silver.telemetry EXACT_NORM", truth["silver"]["telematics"]["by_resolution"]["EXACT_NORM"]),
        ("silver.telemetry SERIAL", truth["silver"]["telematics"]["by_resolution"]["SERIAL"]),
        ("silver.telemetry CROSSWALK", truth["silver"]["telematics"]["by_resolution"]["CROSSWALK"]),
        ("silver.telemetry UNRESOLVED", truth["silver"]["telematics"]["by_resolution"]["UNRESOLVED"]),
        ("silver.work_orders rows", truth["silver"]["cmms"]["rows"]),
        ("silver.work_orders EXACT_NORM", truth["silver"]["cmms"]["by_resolution"]["EXACT_NORM"]),
        ("silver.work_orders SERIAL", truth["silver"]["cmms"]["by_resolution"]["SERIAL"]),
        ("silver.work_orders CROSSWALK", truth["silver"]["cmms"]["by_resolution"]["CROSSWALK"]),
        ("silver.work_orders UNRESOLVED", truth["silver"]["cmms"]["by_resolution"]["UNRESOLVED"]),
        ("gold.dim_asset rows", truth["gold_row_counts"]["dim_asset"]),
        ("gold.dim_site rows", truth["gold_row_counts"]["dim_site"]),
        ("gold.fact_telemetry_daily rows", truth["gold_row_counts"]["fact_telemetry_daily"]),
        ("gold.fact_fault_episode rows", truth["gold_row_counts"]["fact_fault_episode"]),
        ("gold.fact_work_order rows", truth["gold_row_counts"]["fact_work_order"]),
        ("gold.fact_recon_match rows", truth["gold_row_counts"]["fact_recon_match"]),
        ("gold.fact_recon_exception rows", truth["gold_row_counts"]["fact_recon_exception"]),
        ("gold.agg_recon_monthly rows", truth["gold_row_counts"]["agg_recon_monthly"]),
        ("gold.fact_recon_exception ACTIVE_ASSET_SILENT", truth["exceptions"]["by_type"]["ACTIVE_ASSET_SILENT"]),
        ("gold.fact_recon_exception DUPLICATE_WO", truth["exceptions"]["by_type"]["DUPLICATE_WO"]),
        ("gold.fact_recon_exception FAULT_WITHOUT_WO", truth["exceptions"]["by_type"]["FAULT_WITHOUT_WO"]),
        ("gold.fact_recon_exception RETIRED_ASSET_REPORTING", truth["exceptions"]["by_type"]["RETIRED_ASSET_REPORTING"]),
        ("gold.fact_recon_exception UNRESOLVED_ASSET_CMMS", truth["exceptions"]["by_type"]["UNRESOLVED_ASSET_CMMS"]),
        ("gold.fact_recon_exception UNRESOLVED_ASSET_TELEMATICS", truth["exceptions"]["by_type"]["UNRESOLVED_ASSET_TELEMATICS"]),
        ("gold.fact_recon_exception WO_TIME_ANOMALY", truth["exceptions"]["by_type"]["WO_TIME_ANOMALY"]),
        ("gold.fact_recon_exception WO_WITHOUT_FAULT", truth["exceptions"]["by_type"]["WO_WITHOUT_FAULT"]),
    ]


def compute_drift_reference() -> dict[str, object] | None:
    """Live expected numbers for the October drift batch, from the pandas reference
    pipeline (there is no static ground_truth.json row count for this table - see
    RESULTS.md). Returns None when the raw telematics_drift/ folder is not present
    under DATA_ROOT (base-only dataset, nothing to compare)."""
    drift_folder = DATA_ROOT / "telematics_drift"
    if not drift_folder.exists():
        return None

    import fleet_reference_pipeline as ref  # noqa: PLC0415 (optional, data-dependent import)

    erp = ref.read_csv(DATA_ROOT / "erp" / "erp_assets.csv")
    crosswalk = ref.read_csv(DATA_ROOT / "reference" / "asset_crosswalk.csv")
    resolve = ref.make_resolver(erp, crosswalk)
    raw = ref.load_telematics([str(drift_folder)])
    _, stats = ref.silver_telemetry(raw, resolve, CUTOFF_EPOCH)
    return stats


def spike_count(df, dedup_window) -> int:
    deduped = (
        df.withColumn("_row_rank", F.row_number().over(dedup_window))
        .where(F.col("_row_rank") == 1)
        .drop("_row_rank")
    )
    spike_expr = F.lit(0)
    for sensor_name, (lower_bound, upper_bound) in SENSOR_LIMITS.items():
        spike_expr = spike_expr + F.when(
            F.col(sensor_name).isNotNull()
            & ((F.col(sensor_name) < F.lit(lower_bound)) | (F.col(sensor_name) > F.lit(upper_bound))),
            F.lit(1),
        ).otherwise(F.lit(0))
    return int(deduped.select(spike_expr.alias("spikes")).agg(F.sum("spikes").alias("spikes")).first()["spikes"])


def main() -> None:
    truth = json.loads(GROUND_TRUTH_PATH.read_text(encoding="utf-8"))
    storage_format = detect_storage_format()
    spark = build_spark(storage_format)
    try:
        bronze = read_table(spark, "bronze.telematics_events", storage_format)
        silver_telemetry = read_table(spark, "silver.telemetry", storage_format)
        silver_work_orders = read_table(spark, "silver.work_orders", storage_format)

        gold_tables = {
            "gold.dim_asset rows": read_table(spark, "gold.dim_asset", storage_format).count(),
            "gold.dim_site rows": read_table(spark, "gold.dim_site", storage_format).count(),
            "gold.fact_telemetry_daily rows": read_table(spark, "gold.fact_telemetry_daily", storage_format).count(),
            "gold.fact_fault_episode rows": read_table(spark, "gold.fact_fault_episode", storage_format).count(),
            "gold.fact_work_order rows": read_table(spark, "gold.fact_work_order", storage_format).count(),
            "gold.fact_recon_match rows": read_table(spark, "gold.fact_recon_match", storage_format).count(),
            "gold.fact_recon_exception rows": read_table(spark, "gold.fact_recon_exception", storage_format).count(),
            "gold.agg_recon_monthly rows": read_table(spark, "gold.agg_recon_monthly", storage_format).count(),
        }

        # nb_02_silver_clean_resolve dedups bronze telematics on event_id (ordered by
        # ingest_epoch, then _source_file) BEFORE counting/nulling out-of-range spikes.
        # Ground truth's "out_of_range_values_nulled" is this post-dedup count, not a
        # raw-bronze count, so reproduce the identical dedup here for an exact compare.
        dedup_window = Window.partitionBy("event_id").orderBy(
            F.unix_timestamp(F.to_timestamp("ingest_ts")).cast("double").asc(),
            F.col("_source_file").asc(),
        )
        spike_count_base = spike_count(bronze, dedup_window)

        actual = {
            "bronze.telematics_events rows": bronze.count(),
            "bronze.telematics_events duplicates removed": bronze.count() - silver_telemetry.count(),
            "bronze.telematics_events out_of_range_values_nulled": spike_count_base,
            "silver.telemetry rows": silver_telemetry.count(),
            "silver.telemetry late_rows": silver_telemetry.where(F.col("is_late") & F.col("is_in_window")).count(),
            "silver.work_orders rows": silver_work_orders.count(),
            **gold_tables,
        }

        for row in silver_telemetry.groupBy("resolution_method").count().collect():
            actual[f"silver.telemetry {row['resolution_method']}"] = row["count"]
        for row in silver_work_orders.groupBy("resolution_method").count().collect():
            actual[f"silver.work_orders {row['resolution_method']}"] = row["count"]
        for row in read_table(spark, "gold.fact_recon_exception", storage_format).groupBy("exception_type").count().collect():
            actual[f"gold.fact_recon_exception {row['exception_type']}"] = row["count"]

        rows = []
        for metric, expected in expected_metrics(truth):
            got = actual.get(metric)
            rows.append({"metric": metric, "expected": expected, "got": got, "ok": got == expected})

        # Optional drift batch (nb_01/nb_02): bronze.telematics_events_drift and
        # silver.telemetry_drift only exist when the rehearsal data was generated
        # with --with-drift. Compare them live against the pandas reference pipeline
        # run on the same telematics_drift/ folder, since ground_truth.json carries no
        # static row-count entry for this table.
        bronze_drift_path = ARTIFACT_ROOT / "Tables" / "bronze" / "telematics_events_drift"
        silver_drift_path = ARTIFACT_ROOT / "Tables" / "silver" / "telemetry_drift"
        drift_tables_present = bronze_drift_path.exists() and silver_drift_path.exists()

        if drift_tables_present:
            drift_reference = compute_drift_reference()
            if drift_reference is None:
                print(
                    "WARNING: bronze.telematics_events_drift / silver.telemetry_drift exist "
                    "but the raw telematics_drift/ folder was not found under DATA_ROOT "
                    f"({DATA_ROOT}); skipping the drift checks. Set FLEET_RAW_ROOT if the "
                    "raw data lives elsewhere."
                )
            else:
                bronze_drift = read_table(spark, "bronze.telematics_events_drift", storage_format)
                silver_drift = read_table(spark, "silver.telemetry_drift", storage_format)
                spike_count_drift = spike_count(bronze_drift, dedup_window)

                actual["bronze.telematics_events_drift rows"] = bronze_drift.count()
                actual["bronze.telematics_events_drift duplicates removed"] = bronze_drift.count() - silver_drift.count()
                actual["bronze.telematics_events_drift out_of_range_values_nulled"] = spike_count_drift
                actual["silver.telemetry_drift rows"] = silver_drift.count()
                actual["silver.telemetry_drift late_rows"] = silver_drift.where(
                    F.col("is_late") & F.col("is_in_window")
                ).count()
                for row in silver_drift.groupBy("resolution_method").count().collect():
                    actual[f"silver.telemetry_drift {row['resolution_method']}"] = row["count"]

                drift_metrics = [
                    ("bronze.telematics_events_drift rows", drift_reference["bronze_rows"]),
                    ("bronze.telematics_events_drift duplicates removed", drift_reference["duplicates_removed"]),
                    ("bronze.telematics_events_drift out_of_range_values_nulled", drift_reference["out_of_range_values_nulled"]),
                    ("silver.telemetry_drift rows", drift_reference["rows"]),
                    ("silver.telemetry_drift late_rows", drift_reference["late_rows"]),
                    ("silver.telemetry_drift EXACT_NORM", drift_reference["by_resolution"].get("EXACT_NORM", 0)),
                    ("silver.telemetry_drift SERIAL", drift_reference["by_resolution"].get("SERIAL", 0)),
                    ("silver.telemetry_drift CROSSWALK", drift_reference["by_resolution"].get("CROSSWALK", 0)),
                    ("silver.telemetry_drift UNRESOLVED", drift_reference["by_resolution"].get("UNRESOLVED", 0)),
                ]
                for metric, expected in drift_metrics:
                    got = actual.get(metric)
                    rows.append({"metric": metric, "expected": expected, "got": got, "ok": got == expected})
        else:
            print("No drift tables found: base-only run, 9 drift checks skipped (generate with --with-drift to add them).")

        result = {
            "storage_format": storage_format,
            "all_ok": all(row["ok"] for row in rows),
            "rows": rows,
        }

        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_JSON, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(result, indent=2) + "\n")

        md_lines = ["| Metric | Expected | Got | OK |", "|---|---:|---:|:---:|"]
        for row in rows:
            md_lines.append(f"| {row['metric']} | {row['expected']} | {row['got']} | {'OK' if row['ok'] else 'FAIL'} |")
        markdown = "\n".join(md_lines) + "\n"
        with open(OUTPUT_MD, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(markdown)
        print(markdown)

        if not result["all_ok"]:
            raise SystemExit(1)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()