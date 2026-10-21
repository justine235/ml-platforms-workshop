# %% [markdown]
# # nb_10_load_gold_break_glass
#
# Break-glass loader for Part 4. It loads the frozen `reference_out` gold and ML tables into the
# `gold` and `ml` schemas of the default lakehouse, so that `nb_11_recon_walkthrough` and the data
# agent work even when the Part 3 ETL output is not available. Spark only: it needs a Spark
# session with a default lakehouse attached.
#
# ## Prerequisites (do this before running any cell below)
#
# 1. Upload the `*.csv` and `*.csv.gz` files of the published `02-demo-data/reference_out` folder
#    to the lakehouse `lh_fleet`, into the folder `Files/reference_out`. **Never** upload anything
#    from `02-demo-data/truth/`: it is the hidden answer key and must not reach a Fabric workspace.
# 2. Attach `lh_fleet` (schema-enabled) to this notebook as the **default lakehouse**, then restart
#    the session. Relative paths such as `Files/reference_out` and the table names below resolve
#    against the default lakehouse only.
# 3. If the first read below reports "path not found" right after an upload, wait about 2 minutes
#    and run it again (file-listing cache; the duration is `⚠ UNVERIFIED`).

# %%
import pandas as pd
from pyspark.errors import AnalysisException
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

REFERENCE_OUT_PATH = "Files/reference_out"

# %% [markdown]
# ## Explicit schemas, sources, and expected row counts
#
# The column types come from the scenario contract (section 7) and the expected row counts from
# its section 10 (`gold_row_counts` in `reference_out/ground_truth.json`). They are written out
# here, not imported, so the notebook has no dependency on anything else in this kit. A test in
# this kit's `tests/` folder parses these literals and fails when they drift from the reference
# data.

# %%
TABLE_DDL = {
    "gold.dim_asset": "erp_asset_id STRING, asset_name STRING, equipment_class STRING, equipment_class_code INT, manufacturer STRING, model STRING, serial_number STRING, acquisition_date DATE, acquisition_cost_eur DOUBLE, site_code STRING, cost_center STRING, status STRING, retirement_date DATE, telematics_device_installed STRING, device_id STRING, has_telemetry BOOLEAN, telemetry_rows INT, first_telemetry_utc TIMESTAMP, last_telemetry_utc TIMESTAMP, last_engine_hours DOUBLE, asset_age_years DOUBLE",
    "gold.dim_site": "site_code STRING, site_name STRING, country STRING, timezone STRING, latitude DOUBLE, longitude DOUBLE, project_type STRING",
    "gold.fact_telemetry_daily": "erp_asset_id STRING, site_code STRING, obs_date DATE, n_readings INT, n_run INT, engine_hours DOUBLE, temp_mean DOUBLE, temp_max DOUBLE, oil_mean DOUBLE, oil_min DOUBLE, hyd_mean DOUBLE, hyd_min DOUBLE, vib_mean DOUBLE, vib_max DOUBLE, fuel_mean DOUBLE, load_mean DOUBLE, idle_mean DOUBLE, run_share DOUBLE, is_after_retirement BOOLEAN",
    "gold.fact_fault_episode": "episode_id STRING, erp_asset_id STRING, site_code STRING, fault_code STRING, system STRING, severity STRING, start_utc TIMESTAMP, end_utc TIMESTAMP, n_records INT, is_significant BOOLEAN, recon_status STRING, matched_wo_number STRING, month STRING",
    "gold.fact_work_order": "wo_number STRING, erp_asset_id STRING, site_code STRING, wo_type STRING, priority STRING, status STRING, failure_code STRING, failure_system STRING, description STRING, opened_utc TIMESTAMP, closed_utc TIMESTAMP, duration_hours DOUBLE, labor_hours DOUBLE, parts_cost_eur DOUBLE, technician_id STRING, reported_by STRING, id_resolution STRING, times_corrected BOOLEAN",
    "gold.fact_recon_match": "episode_id STRING, wo_number STRING, erp_asset_id STRING, delta_hours DOUBLE, same_system BOOLEAN, is_best_for_episode BOOLEAN",
    "gold.fact_recon_exception": "exception_id STRING, exception_type STRING, subtype STRING, severity STRING, erp_asset_id STRING, site_code STRING, reference_id STRING, event_utc TIMESTAMP, n_records INT, detail STRING",
    "gold.agg_recon_monthly": "month STRING, site_code STRING, crit_episodes INT, crit_matched INT, crit_unmatched INT, crit_pending INT, crit_match_rate DOUBLE, warn_episodes_3plus INT, warn_matched INT, warn_unmatched INT, cm_work_orders INT, cm_wo_with_fault_signal INT, cm_wo_without_fault_signal INT, avg_crit_fault_to_wo_hours DOUBLE, cm_repair_hours DOUBLE",
    "ml.asset_day_features": "erp_asset_id STRING, obs_date DATE, temp_mean DOUBLE, temp_max DOUBLE, oil_mean DOUBLE, oil_min DOUBLE, hyd_mean DOUBLE, hyd_min DOUBLE, vib_mean DOUBLE, vib_max DOUBLE, fuel_mean DOUBLE, load_mean DOUBLE, idle_mean DOUBLE, n_readings INT, run_share DOUBLE, engine_hours DOUBLE, warn_cnt_1d INT, crit_cnt_1d INT, warn_cnt_7d DOUBLE, crit_cnt_7d DOUBLE, warn_cnt_14d DOUBLE, temp_mean_3d DOUBLE, temp_mean_7d DOUBLE, temp_mean_14d DOUBLE, oil_mean_3d DOUBLE, oil_mean_7d DOUBLE, oil_mean_14d DOUBLE, hyd_mean_3d DOUBLE, hyd_mean_7d DOUBLE, hyd_mean_14d DOUBLE, vib_mean_3d DOUBLE, vib_mean_7d DOUBLE, vib_mean_14d DOUBLE, temp_trend DOUBLE, oil_trend DOUBLE, hyd_trend DOUBLE, vib_trend DOUBLE, temp_max_7d DOUBLE, vib_max_7d DOUBLE, days_since_last_pm DOUBLE, days_since_last_cm DOUBLE, cm_count_90d DOUBLE, equipment_class_code INT, asset_age_years DOUBLE, fail_next_7d DOUBLE, split STRING",
    "ml.failure_risk_score": "score_date DATE, erp_asset_id STRING, site_code STRING, equipment_class STRING, risk_score DOUBLE, risk_band STRING, risk_rank INT, top_drivers STRING, model_version STRING",
    "ml.drift_report": "equipment_class STRING, sensor STRING, psi DOUBLE, ref_mean DOUBLE, new_mean DOUBLE, ref_rows INT, new_rows INT, status STRING",
}

TABLE_SOURCES = {
    "gold.dim_asset": "dim_asset.csv",
    "gold.dim_site": "dim_site.csv",
    "gold.fact_telemetry_daily": "fact_telemetry_daily.csv.gz",
    "gold.fact_fault_episode": "fact_fault_episode.csv",
    "gold.fact_work_order": "fact_work_order.csv",
    "gold.fact_recon_match": "fact_recon_match.csv",
    "gold.fact_recon_exception": "fact_recon_exception.csv",
    "gold.agg_recon_monthly": "agg_recon_monthly.csv",
    "ml.asset_day_features": "ml_asset_day_features.csv.gz",
    "ml.failure_risk_score": "ml_failure_risk_score.csv",
    "ml.drift_report": "drift_report.csv",
}

EXPECTED_ROW_COUNTS = {
    "dim_asset": 316,
    "dim_site": 12,
    "fact_telemetry_daily": 51353,
    "fact_fault_episode": 3459,
    "fact_work_order": 2345,
    "fact_recon_match": 468,
    "fact_recon_exception": 211,
    "agg_recon_monthly": 72,
    "asset_day_features": 50876,
    "failure_risk_score": 264,
    "drift_report": 47,
}

# %% [markdown]
# ## Fail loudly if the prerequisite upload is missing

# %%
def _csv_path(source_name: str) -> str:
    return f"{REFERENCE_OUT_PATH}/{source_name}"


def _assert_reference_out_present() -> None:
    first_source = next(iter(TABLE_SOURCES.values()))
    try:
        spark.read.text(_csv_path(first_source)).limit(1).count()
    except AnalysisException as exc:
        raise RuntimeError(
            f"Could not read {REFERENCE_OUT_PATH}/{first_source}. Upload the published "
            "02-demo-data/reference_out folder (CSV files only, never 02-demo-data/truth/) into "
            "this lakehouse's Files/reference_out folder, attach lh_fleet as the default "
            "lakehouse, and re-run. If you just uploaded the files, wait about 2 minutes for "
            "the Fabric file-listing cache to refresh and try again."
        ) from exc


_assert_reference_out_present()

# %% [markdown]
# ## Load every gold and ML table
#
# Each CSV is read with its literal DDL schema (so the data agent sees stable, typed columns) and
# saved as a Delta table, overwriting any previous version.

# %%
def load_table(fq_name: str) -> int:
    schema_name, table_name = fq_name.split(".", 1)
    frame = (
        spark.read.option("header", True)
        .schema(TABLE_DDL[fq_name])
        .csv(_csv_path(TABLE_SOURCES[fq_name]))
    )
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
    (
        frame.write.mode("overwrite")
        .format("delta")
        .option("overwriteSchema", "true")
        .saveAsTable(f"{schema_name}.{table_name}")
    )
    return spark.table(fq_name).count()


load_results = pd.DataFrame(
    [{"table": fq_name, "rows": load_table(fq_name)} for fq_name in TABLE_DDL]
)
print(load_results.to_string(index=False))

# %% [markdown]
# ## Verify row counts against the scenario contract

# %%
verification = pd.DataFrame(
    [
        {
            "table": fq_name,
            "expected_rows": EXPECTED_ROW_COUNTS[fq_name.split(".", 1)[1]],
            "actual_rows": spark.table(fq_name).count(),
        }
        for fq_name in TABLE_DDL
    ]
)
verification["matches_contract"] = verification["expected_rows"] == verification["actual_rows"]
print(verification.to_string(index=False))

# %%
if not verification["matches_contract"].all():
    raise AssertionError(verification.loc[~verification["matches_contract"]].to_string(index=False))

print("Loaded tables match the scenario-contract row counts.")

# %% [markdown]
# ## Smoke-test the frozen failure-risk table
#
# Part 4 must use the frozen scores from `reference_out` so the Q&A numbers stay stable. The
# expected risk-band set and the asset total (264, from the scenario contract's
# `gold_row_counts.ml_failure_risk_score`) are literal checks here, not an import from the
# hidden truth package.

# %%
risk_summary = spark.sql(
    """
    SELECT
        score_date,
        risk_band,
        COUNT(*) AS assets
    FROM ml.failure_risk_score
    GROUP BY score_date, risk_band
    ORDER BY score_date, CASE risk_band WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END
    """
).toPandas()
print(risk_summary.to_string(index=False))

# %%
EXPECTED_RISK_BANDS = {"High", "Medium", "Low"}
EXPECTED_TOTAL_ASSETS = 264

assert set(risk_summary["risk_band"]) == EXPECTED_RISK_BANDS
assert int(risk_summary["assets"].sum()) == EXPECTED_TOTAL_ASSETS
print("Frozen risk table is loaded and ready for the data-agent demo.")
