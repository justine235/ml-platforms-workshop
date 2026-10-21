from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
from pyspark.sql import functions as F


ETL_ROOT = Path(__file__).resolve().parents[1]
KIT_ROOT = ETL_ROOT.parents[1]
DATA_ROOT = Path(os.environ.get("FLEET_RAW_ROOT") or (KIT_ROOT / "02-demo-data" / "data"))
TRUTH_ROOT = Path(os.environ.get("FLEET_TRUTH_ROOT") or (KIT_ROOT / "02-demo-data" / "truth"))
ARTIFACT_ROOT = ETL_ROOT / "local-validation" / "artifacts"
LAKEHOUSE_ROOT = ARTIFACT_ROOT / "lh_fleet"
SUMMARY_PATH = ARTIFACT_ROOT / "validation-summary.json"
REFERENCE_ROOT = KIT_ROOT / "02-demo-data" / "reference_out"
GENERATOR = KIT_ROOT / "02-demo-data" / "fleet_data_generator.py"


def ensure_data() -> None:
    if DATA_ROOT.exists() and (DATA_ROOT / "_manifest.json").exists():
        return
    DATA_ROOT.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(GENERATOR),
        "--out",
        str(DATA_ROOT),
        "--truth-dir",
        str(TRUTH_ROOT),
        "--with-drift",
    ]
    subprocess.run(cmd, check=True)


def clean_artifacts() -> None:
    if ARTIFACT_ROOT.exists():
        shutil.rmtree(ARTIFACT_ROOT)
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)


def _prepend_env_bin(env_var: str) -> Path | None:
    home = os.environ.get(env_var)
    if not home:
        return None
    home_path = Path(home)
    bin_dir = home_path / "bin"
    if bin_dir.exists():
        os.environ["PATH"] = f"{bin_dir}{os.pathsep}{os.environ['PATH']}"
    return home_path


def build_spark():
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

    storage_format = "parquet"
    mode_notes: list[str] = []
    spark = None

    try:
        from delta import configure_spark_with_delta_pip

        builder = (
            SparkSession.builder.master("local[2]")
            .appName("fleet-local-validation")
            .config("spark.sql.session.timeZone", "UTC")
            .config("spark.sql.shuffle.partitions", "8")
            .config("spark.driver.memory", "1500m")
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        )
        spark = configure_spark_with_delta_pip(builder).getOrCreate()
        storage_format = "delta"
        mode_notes.append("delta_local_mode")
    except Exception as exc:  # noqa: BLE001
        mode_notes.append(f"delta_unavailable:{exc.__class__.__name__}")
        if spark is not None:
            spark.stop()
        spark = (
            SparkSession.builder.master("local[2]")
            .appName("fleet-local-validation")
            .config("spark.sql.session.timeZone", "UTC")
            .config("spark.sql.shuffle.partitions", "8")
            .config("spark.driver.memory", "1500m")
            .getOrCreate()
        )
        storage_format = "parquet"
        mode_notes.append("parquet_fallback_mode")

    return spark, storage_format, mode_notes


def run_notebook(path: Path, spark, storage_format: str) -> dict:
    code = compile(path.read_text(encoding="utf-8"), str(path), "exec")
    globals_dict = {
        "__file__": str(path),
        "__name__": "__main__",
        "spark": spark,
        "batch_id": "local-validation",
        "data_cutoff_utc": "2026-10-01T00:00:00Z",
        "mode": "full",
        "raw_root": str(DATA_ROOT),
        "local_storage_format": storage_format,
    }
    exec(code, globals_dict)  # noqa: S102
    return globals_dict.get("NOTEBOOK_SUMMARY", {})


def read_table(spark, name: str, storage_format: str):
    schema_name, table_name = name.split(".", 1)
    path = LAKEHOUSE_ROOT / "Tables" / schema_name / table_name
    return spark.read.format(storage_format).load(str(path))


def reference_count(file_name: str) -> int:
    path = REFERENCE_ROOT / file_name
    if path.suffix == ".gz":
        return len(pd.read_csv(path))
    return len(pd.read_csv(path))


def collect_set(df, columns: list[str]) -> set[tuple]:
    rows = df.select(*columns).collect()
    return {tuple(row[column] for column in columns) for row in rows}


def main() -> None:
    ensure_data()
    clean_artifacts()
    spark, storage_format, mode_notes = build_spark()
    try:
        notebook_summaries = {}
        for notebook_name in (
            "nb_00_setup.py",
            "nb_01_bronze_ingest.py",
            "nb_02_silver_clean_resolve.py",
            "nb_03_gold_reconcile.py",
        ):
            notebook_summaries[notebook_name] = run_notebook(
                ETL_ROOT / "notebooks-src" / notebook_name,
                spark,
                storage_format,
            )

        silver_telemetry = read_table(spark, "silver.telemetry", storage_format)
        silver_work_orders = read_table(spark, "silver.work_orders", storage_format)
        fact_fault_episode = read_table(spark, "gold.fact_fault_episode", storage_format)
        fact_work_order = read_table(spark, "gold.fact_work_order", storage_format)
        fact_recon_match = read_table(spark, "gold.fact_recon_match", storage_format)
        fact_recon_exception = read_table(spark, "gold.fact_recon_exception", storage_format)

        actual_counts = {
            "silver.telemetry": silver_telemetry.count(),
            "silver.work_orders": silver_work_orders.count(),
            "gold.dim_asset": read_table(spark, "gold.dim_asset", storage_format).count(),
            "gold.dim_site": read_table(spark, "gold.dim_site", storage_format).count(),
            "gold.fact_telemetry_daily": read_table(spark, "gold.fact_telemetry_daily", storage_format).count(),
            "gold.fact_fault_episode": fact_fault_episode.count(),
            "gold.fact_work_order": fact_work_order.count(),
            "gold.fact_recon_match": fact_recon_match.count(),
            "gold.fact_recon_exception": fact_recon_exception.count(),
            "gold.agg_recon_monthly": read_table(spark, "gold.agg_recon_monthly", storage_format).count(),
        }
        expected_counts = {
            "silver.telemetry": 207691,
            "silver.work_orders": 2359,
            "gold.dim_asset": reference_count("dim_asset.csv"),
            "gold.dim_site": reference_count("dim_site.csv"),
            "gold.fact_telemetry_daily": reference_count("fact_telemetry_daily.csv.gz"),
            "gold.fact_fault_episode": reference_count("fact_fault_episode.csv"),
            "gold.fact_work_order": reference_count("fact_work_order.csv"),
            "gold.fact_recon_match": reference_count("fact_recon_match.csv"),
            "gold.fact_recon_exception": reference_count("fact_recon_exception.csv"),
            "gold.agg_recon_monthly": reference_count("agg_recon_monthly.csv"),
        }

        exception_counts = {
            row["exception_type"]: row["count"]
            for row in fact_recon_exception.groupBy("exception_type").count().collect()
        }
        status_counts = {
            row["recon_status"]: row["count"]
            for row in fact_fault_episode.where("is_significant").groupBy("recon_status").count().collect()
        }
        crit_status_counts = {
            row["recon_status"]: row["count"]
            for row in fact_fault_episode.where("severity = 'CRIT'").groupBy("recon_status").count().collect()
        }
        crit_matches = (
            fact_recon_match.where("is_best_for_episode")
            .join(fact_fault_episode.select("episode_id", "severity"), "episode_id", "inner")
            .where("severity = 'CRIT'")
        )
        median_crit_delay = crit_matches.agg(
            F.expr("percentile_approx(delta_hours, 0.5, 100000)").alias("median")
        ).first()["median"]
        crit_match_rate = round(
            crit_status_counts["MATCHED"] / (crit_status_counts["MATCHED"] + crit_status_counts["UNMATCHED"]),
            4,
        )

        expected_episode_ids = set(pd.read_csv(REFERENCE_ROOT / "fact_fault_episode.csv")["episode_id"].tolist())
        actual_episode_ids = {row["episode_id"] for row in fact_fault_episode.select("episode_id").collect()}
        expected_wo_ids = set(pd.read_csv(REFERENCE_ROOT / "fact_work_order.csv")["wo_number"].tolist())
        actual_wo_ids = {row["wo_number"] for row in fact_work_order.select("wo_number").collect()}
        expected_exception_pairs = {
            (row["exception_type"], row["reference_id"])
            for _, row in pd.read_csv(REFERENCE_ROOT / "fact_recon_exception.csv").iterrows()
        }
        actual_exception_pairs = collect_set(fact_recon_exception, ["exception_type", "reference_id"])

        mismatches = []
        for name, expected in expected_counts.items():
            actual = actual_counts[name]
            if actual != expected:
                mismatches.append(f"{name}: expected {expected}, got {actual}")
        if exception_counts != {
            "ACTIVE_ASSET_SILENT": 12,
            "DUPLICATE_WO": 6,
            "FAULT_WITHOUT_WO": 91,
            "RETIRED_ASSET_REPORTING": 6,
            "UNRESOLVED_ASSET_CMMS": 3,
            "UNRESOLVED_ASSET_TELEMATICS": 6,
            "WO_TIME_ANOMALY": 8,
            "WO_WITHOUT_FAULT": 79,
        }:
            mismatches.append(f"exception_counts: {exception_counts}")
        if status_counts != {"MATCHED": 455, "UNMATCHED": 91, "PENDING": 11}:
            mismatches.append(f"significant_status: {status_counts}")
        if crit_match_rate != 0.9244:
            mismatches.append(f"crit_match_rate: {crit_match_rate}")
        if round(float(median_crit_delay), 2) != 5.58:
            mismatches.append(f"median_crit_delay: {median_crit_delay}")
        if actual_episode_ids != expected_episode_ids:
            mismatches.append("episode_id set differs from reference")
        if actual_wo_ids != expected_wo_ids:
            mismatches.append("wo_number set differs from reference")
        if actual_exception_pairs != expected_exception_pairs:
            mismatches.append("exception_type/reference_id pairs differ from reference")

        result = {
            "status": "ok" if not mismatches else "failed",
            "storage_format": storage_format,
            "mode_notes": mode_notes,
            "notebooks": notebook_summaries,
            "counts": actual_counts,
            "exception_counts": exception_counts,
            "significant_status": status_counts,
            "crit_status": crit_status_counts,
            "crit_match_rate": crit_match_rate,
            "median_crit_delay_hours": round(float(median_crit_delay), 2),
            "key_equality": {
                "episode_ids": actual_episode_ids == expected_episode_ids,
                "wo_numbers": actual_wo_ids == expected_wo_ids,
                "exception_pairs": actual_exception_pairs == expected_exception_pairs,
            },
            "mismatches": mismatches,
        }
        SUMMARY_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True))
        if mismatches:
            raise SystemExit(1)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()