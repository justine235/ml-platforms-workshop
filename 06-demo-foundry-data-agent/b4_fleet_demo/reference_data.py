from __future__ import annotations

import csv
import gzip
import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

B4_DIR = Path(__file__).resolve().parents[1]
WORKSHOP_DIR = B4_DIR.parent
REFERENCE_OUT_DIR = WORKSHOP_DIR / "02-demo-data" / "reference_out"
GROUND_TRUTH_PATH = REFERENCE_OUT_DIR / "ground_truth.json"


@dataclass(frozen=True)
class ColumnSpec:
    name: str
    spark_type: str
    business_description: str

    @property
    def duckdb_type(self) -> str:
        mapping = {
            "STRING": "VARCHAR",
            "INT": "INTEGER",
            "DOUBLE": "DOUBLE",
            "DATE": "DATE",
            "TIMESTAMP": "TIMESTAMP",
            "BOOLEAN": "BOOLEAN",
        }
        return mapping[self.spark_type]


@dataclass(frozen=True)
class TableSpec:
    schema_name: str
    table_name: str
    source_name: str
    columns: tuple[ColumnSpec, ...]
    business_purpose: str

    @property
    def fq_name(self) -> str:
        return f"{self.schema_name}.{self.table_name}"

    @property
    def source_path(self) -> Path:
        return REFERENCE_OUT_DIR / self.source_name

    @property
    def csv_reader_expression(self) -> str:
        return as_duckdb_path(self.source_path)

    @property
    def column_names(self) -> tuple[str, ...]:
        return tuple(column.name for column in self.columns)

    def spark_schema_expression(self) -> str:
        mapping = {
            "STRING": "StringType()",
            "INT": "IntegerType()",
            "DOUBLE": "DoubleType()",
            "DATE": "DateType()",
            "TIMESTAMP": "TimestampType()",
            "BOOLEAN": "BooleanType()",
        }
        inner = ",\n    ".join(
            f"StructField('{column.name}', {mapping[column.spark_type]}, True)"
            for column in self.columns
        )
        return f"StructType([\\n    {inner}\\n])"


def as_duckdb_path(path: Path) -> str:
    return str(path).replace("\\", "/")


def load_ground_truth() -> dict[str, Any]:
    return json.loads(GROUND_TRUTH_PATH.read_text(encoding="utf-8"))


GROUND_TRUTH = load_ground_truth()


TABLE_SPECS: tuple[TableSpec, ...] = (
    TableSpec(
        schema_name="gold",
        table_name="dim_asset",
        source_name="dim_asset.csv",
        business_purpose="Master asset dimension after ERP, telemetry, and site enrichment.",
        columns=(
            ColumnSpec("erp_asset_id", "STRING", "Golden asset identifier EQ-NNNNN."),
            ColumnSpec("asset_name", "STRING", "Human-readable asset name from ERP."),
            ColumnSpec("equipment_class", "STRING", "Equipment family such as Excavator or Generator."),
            ColumnSpec("equipment_class_code", "INT", "Stable numeric class code used by ML features."),
            ColumnSpec("manufacturer", "STRING", "Synthetic manufacturer name."),
            ColumnSpec("model", "STRING", "Synthetic model name."),
            ColumnSpec("serial_number", "STRING", "ERP serial number."),
            ColumnSpec("acquisition_date", "DATE", "ERP acquisition date."),
            ColumnSpec("acquisition_cost_eur", "DOUBLE", "Acquisition cost in EUR."),
            ColumnSpec("site_code", "STRING", "ERP site code."),
            ColumnSpec("cost_center", "STRING", "ERP cost center."),
            ColumnSpec("status", "STRING", "Asset lifecycle status Active, Retired, or Disposed."),
            ColumnSpec("retirement_date", "DATE", "Retirement date when present."),
            ColumnSpec("telematics_device_installed", "STRING", "Y or N flag from ERP."),
            ColumnSpec("device_id", "STRING", "Resolved telematics device id when present."),
            ColumnSpec("has_telemetry", "BOOLEAN", "Whether any telemetry resolved to the asset."),
            ColumnSpec("telemetry_rows", "INT", "Count of telemetry rows tied to the asset."),
            ColumnSpec("first_telemetry_utc", "TIMESTAMP", "First resolved telemetry timestamp in UTC."),
            ColumnSpec("last_telemetry_utc", "TIMESTAMP", "Last resolved telemetry timestamp in UTC."),
            ColumnSpec("last_engine_hours", "DOUBLE", "Latest reported engine-hour value."),
            ColumnSpec("asset_age_years", "DOUBLE", "Age of the asset at the cutoff date."),
        ),
    ),
    TableSpec(
        schema_name="gold",
        table_name="dim_site",
        source_name="dim_site.csv",
        business_purpose="Site reference dimension for timezone-aware operations and geography.",
        columns=(
            ColumnSpec("site_code", "STRING", "Stable site identifier."),
            ColumnSpec("site_name", "STRING", "Friendly site name."),
            ColumnSpec("country", "STRING", "Country name."),
            ColumnSpec("timezone", "STRING", "IANA timezone identifier."),
            ColumnSpec("latitude", "DOUBLE", "Site latitude."),
            ColumnSpec("longitude", "DOUBLE", "Site longitude."),
            ColumnSpec("project_type", "STRING", "Synthetic construction project type."),
        ),
    ),
    TableSpec(
        schema_name="gold",
        table_name="fact_telemetry_daily",
        source_name="fact_telemetry_daily.csv.gz",
        business_purpose="Daily telemetry aggregates per asset and UTC observation day.",
        columns=(
            ColumnSpec("erp_asset_id", "STRING", "Resolved asset identifier."),
            ColumnSpec("site_code", "STRING", "ERP site for the asset."),
            ColumnSpec("obs_date", "DATE", "UTC observation date."),
            ColumnSpec("n_readings", "INT", "Number of resolved telemetry readings that day."),
            ColumnSpec("n_run", "INT", "Number of RUN-state readings."),
            ColumnSpec("engine_hours", "DOUBLE", "Maximum engine hours seen that day."),
            ColumnSpec("temp_mean", "DOUBLE", "Average engine temperature over RUN readings."),
            ColumnSpec("temp_max", "DOUBLE", "Maximum engine temperature over RUN readings."),
            ColumnSpec("oil_mean", "DOUBLE", "Average oil pressure over RUN readings."),
            ColumnSpec("oil_min", "DOUBLE", "Minimum oil pressure over RUN readings."),
            ColumnSpec("hyd_mean", "DOUBLE", "Average hydraulic pressure over RUN readings."),
            ColumnSpec("hyd_min", "DOUBLE", "Minimum hydraulic pressure over RUN readings."),
            ColumnSpec("vib_mean", "DOUBLE", "Average vibration over RUN readings."),
            ColumnSpec("vib_max", "DOUBLE", "Maximum vibration over RUN readings."),
            ColumnSpec("fuel_mean", "DOUBLE", "Average fuel rate over RUN readings."),
            ColumnSpec("load_mean", "DOUBLE", "Average load percentage over RUN readings."),
            ColumnSpec("idle_mean", "DOUBLE", "Average idle percentage over RUN readings."),
            ColumnSpec("run_share", "DOUBLE", "Share of RUN readings within the day."),
            ColumnSpec("is_after_retirement", "BOOLEAN", "Whether the date is on or after the ERP retirement date."),
        ),
    ),
    TableSpec(
        schema_name="gold",
        table_name="fact_fault_episode",
        source_name="fact_fault_episode.csv",
        business_purpose="Resolved fault episodes grouped from telemetry fault-code bursts.",
        columns=(
            ColumnSpec("episode_id", "STRING", "Stable episode id within this dataset."),
            ColumnSpec("erp_asset_id", "STRING", "Resolved asset identifier."),
            ColumnSpec("site_code", "STRING", "ERP site for the asset."),
            ColumnSpec("fault_code", "STRING", "Fault code from the catalog."),
            ColumnSpec("system", "STRING", "Subsystem such as ENG or HYD."),
            ColumnSpec("severity", "STRING", "INFO, WARN, or CRIT."),
            ColumnSpec("start_utc", "TIMESTAMP", "First telemetry timestamp in the episode."),
            ColumnSpec("end_utc", "TIMESTAMP", "Last telemetry timestamp in the episode."),
            ColumnSpec("n_records", "INT", "Number of telemetry records in the episode."),
            ColumnSpec("is_significant", "BOOLEAN", "True for CRIT and WARN episodes with at least three records."),
            ColumnSpec("recon_status", "STRING", "NOT_APPLICABLE, MATCHED, UNMATCHED, or PENDING."),
            ColumnSpec("matched_wo_number", "STRING", "Best matched corrective work-order number when present."),
            ColumnSpec("month", "STRING", "Start month in YYYY-MM form."),
        ),
    ),
    TableSpec(
        schema_name="gold",
        table_name="fact_work_order",
        source_name="fact_work_order.csv",
        business_purpose="Resolved, non-duplicate work orders at the business-grain used by reconciliation and ML.",
        columns=(
            ColumnSpec("wo_number", "STRING", "Work-order identifier."),
            ColumnSpec("erp_asset_id", "STRING", "Resolved asset identifier."),
            ColumnSpec("site_code", "STRING", "ERP site for the asset."),
            ColumnSpec("wo_type", "STRING", "PM, CM, or INSP."),
            ColumnSpec("priority", "STRING", "CMMS priority P1 to P4."),
            ColumnSpec("status", "STRING", "Open or Closed status."),
            ColumnSpec("failure_code", "STRING", "CM failure code for corrective work."),
            ColumnSpec("failure_system", "STRING", "Subsystem for the corrective work."),
            ColumnSpec("description", "STRING", "Free-text work-order description."),
            ColumnSpec("opened_utc", "TIMESTAMP", "Opened timestamp normalized to UTC."),
            ColumnSpec("closed_utc", "TIMESTAMP", "Closed timestamp normalized to UTC."),
            ColumnSpec("duration_hours", "DOUBLE", "Elapsed hours between opened and closed."),
            ColumnSpec("labor_hours", "DOUBLE", "Labor hours recorded on the work order."),
            ColumnSpec("parts_cost_eur", "DOUBLE", "Parts cost in EUR."),
            ColumnSpec("technician_id", "STRING", "Synthetic technician identifier."),
            ColumnSpec("reported_by", "STRING", "Synthetic reporter when present."),
            ColumnSpec("id_resolution", "STRING", "Identity-resolution tier used for the asset."),
            ColumnSpec("times_corrected", "BOOLEAN", "True when swapped timestamps were corrected."),
        ),
    ),
    TableSpec(
        schema_name="gold",
        table_name="fact_recon_match",
        source_name="fact_recon_match.csv",
        business_purpose="Episode-to-work-order candidate matches inside the reconciliation window.",
        columns=(
            ColumnSpec("episode_id", "STRING", "Fault episode identifier."),
            ColumnSpec("wo_number", "STRING", "Corrective work-order identifier."),
            ColumnSpec("erp_asset_id", "STRING", "Resolved asset identifier."),
            ColumnSpec("delta_hours", "DOUBLE", "Work-order open time minus episode start, in hours."),
            ColumnSpec("same_system", "BOOLEAN", "Whether the fault and work order point to the same subsystem."),
            ColumnSpec("is_best_for_episode", "BOOLEAN", "Whether this row is the best match for the episode."),
        ),
    ),
    TableSpec(
        schema_name="gold",
        table_name="fact_recon_exception",
        source_name="fact_recon_exception.csv",
        business_purpose="Explicit reconciliation findings and operational exceptions.",
        columns=(
            ColumnSpec("exception_id", "STRING", "Stable exception identifier within this dataset."),
            ColumnSpec("exception_type", "STRING", "Primary exception category."),
            ColumnSpec("subtype", "STRING", "Subtype for categories that have one."),
            ColumnSpec("severity", "STRING", "LOW, MEDIUM, or HIGH."),
            ColumnSpec("erp_asset_id", "STRING", "Resolved asset when applicable."),
            ColumnSpec("site_code", "STRING", "Site when applicable."),
            ColumnSpec("reference_id", "STRING", "Business key such as device id, episode id, or WO number."),
            ColumnSpec("event_utc", "TIMESTAMP", "Anchor timestamp when applicable."),
            ColumnSpec("n_records", "INT", "Number of implicated records."),
            ColumnSpec("detail", "STRING", "Human-readable explanation."),
        ),
    ),
    TableSpec(
        schema_name="gold",
        table_name="agg_recon_monthly",
        source_name="agg_recon_monthly.csv",
        business_purpose="Monthly site-level reconciliation KPI rollup used for trends and match-rate questions.",
        columns=(
            ColumnSpec("month", "STRING", "Month in YYYY-MM form."),
            ColumnSpec("site_code", "STRING", "Site identifier."),
            ColumnSpec("crit_episodes", "INT", "CRIT episodes opened in the month."),
            ColumnSpec("crit_matched", "INT", "CRIT episodes matched to a corrective work order."),
            ColumnSpec("crit_unmatched", "INT", "CRIT episodes with no work order after the window closed."),
            ColumnSpec("crit_pending", "INT", "CRIT episodes still within the open match window."),
            ColumnSpec("crit_match_rate", "DOUBLE", "Matched divided by matched plus unmatched, pending excluded."),
            ColumnSpec("warn_episodes_3plus", "INT", "Significant WARN episodes with at least three records."),
            ColumnSpec("warn_matched", "INT", "WARN episodes matched to a corrective work order."),
            ColumnSpec("warn_unmatched", "INT", "WARN episodes without a work order after the window closed."),
            ColumnSpec("cm_work_orders", "INT", "Corrective work orders opened in the month."),
            ColumnSpec("cm_wo_with_fault_signal", "INT", "Corrective work orders with at least one matched episode."),
            ColumnSpec("cm_wo_without_fault_signal", "INT", "Corrective work orders with no matching episode."),
            ColumnSpec("avg_crit_fault_to_wo_hours", "DOUBLE", "Average hours from CRIT episode start to corrective work order."),
            ColumnSpec("cm_repair_hours", "DOUBLE", "Total corrective repair duration in hours."),
        ),
    ),
    TableSpec(
        schema_name="ml",
        table_name="asset_day_features",
        source_name="ml_asset_day_features.csv.gz",
        business_purpose="ML-ready daily feature table with labels, splits, and frozen score-day rows.",
        columns=(
            ColumnSpec("erp_asset_id", "STRING", "Resolved asset identifier."),
            ColumnSpec("obs_date", "DATE", "Feature observation date."),
            ColumnSpec("temp_mean", "DOUBLE", "Daily mean engine temperature."),
            ColumnSpec("temp_max", "DOUBLE", "Daily maximum engine temperature."),
            ColumnSpec("oil_mean", "DOUBLE", "Daily mean oil pressure."),
            ColumnSpec("oil_min", "DOUBLE", "Daily minimum oil pressure."),
            ColumnSpec("hyd_mean", "DOUBLE", "Daily mean hydraulic pressure."),
            ColumnSpec("hyd_min", "DOUBLE", "Daily minimum hydraulic pressure."),
            ColumnSpec("vib_mean", "DOUBLE", "Daily mean vibration."),
            ColumnSpec("vib_max", "DOUBLE", "Daily maximum vibration."),
            ColumnSpec("fuel_mean", "DOUBLE", "Daily mean fuel rate."),
            ColumnSpec("load_mean", "DOUBLE", "Daily mean load percentage."),
            ColumnSpec("idle_mean", "DOUBLE", "Daily mean idle percentage."),
            ColumnSpec("n_readings", "INT", "Daily reading count."),
            ColumnSpec("run_share", "DOUBLE", "Daily RUN reading share."),
            ColumnSpec("engine_hours", "DOUBLE", "Daily max engine hours."),
            ColumnSpec("warn_cnt_1d", "INT", "WARN fault-count feature over one day."),
            ColumnSpec("crit_cnt_1d", "INT", "CRIT fault-count feature over one day."),
            ColumnSpec("warn_cnt_7d", "DOUBLE", "WARN fault-count feature over seven days."),
            ColumnSpec("crit_cnt_7d", "DOUBLE", "CRIT fault-count feature over seven days."),
            ColumnSpec("warn_cnt_14d", "DOUBLE", "WARN fault-count feature over fourteen days."),
            ColumnSpec("temp_mean_3d", "DOUBLE", "Rolling 3-day temperature mean."),
            ColumnSpec("temp_mean_7d", "DOUBLE", "Rolling 7-day temperature mean."),
            ColumnSpec("temp_mean_14d", "DOUBLE", "Rolling 14-day temperature mean."),
            ColumnSpec("oil_mean_3d", "DOUBLE", "Rolling 3-day oil-pressure mean."),
            ColumnSpec("oil_mean_7d", "DOUBLE", "Rolling 7-day oil-pressure mean."),
            ColumnSpec("oil_mean_14d", "DOUBLE", "Rolling 14-day oil-pressure mean."),
            ColumnSpec("hyd_mean_3d", "DOUBLE", "Rolling 3-day hydraulic-pressure mean."),
            ColumnSpec("hyd_mean_7d", "DOUBLE", "Rolling 7-day hydraulic-pressure mean."),
            ColumnSpec("hyd_mean_14d", "DOUBLE", "Rolling 14-day hydraulic-pressure mean."),
            ColumnSpec("vib_mean_3d", "DOUBLE", "Rolling 3-day vibration mean."),
            ColumnSpec("vib_mean_7d", "DOUBLE", "Rolling 7-day vibration mean."),
            ColumnSpec("vib_mean_14d", "DOUBLE", "Rolling 14-day vibration mean."),
            ColumnSpec("temp_trend", "DOUBLE", "3-day minus 14-day engine-temperature mean."),
            ColumnSpec("oil_trend", "DOUBLE", "3-day minus 14-day oil-pressure mean."),
            ColumnSpec("hyd_trend", "DOUBLE", "3-day minus 14-day hydraulic-pressure mean."),
            ColumnSpec("vib_trend", "DOUBLE", "3-day minus 14-day vibration mean."),
            ColumnSpec("temp_max_7d", "DOUBLE", "Rolling 7-day max engine temperature."),
            ColumnSpec("vib_max_7d", "DOUBLE", "Rolling 7-day max vibration."),
            ColumnSpec("days_since_last_pm", "DOUBLE", "Days since the last preventive work order."),
            ColumnSpec("days_since_last_cm", "DOUBLE", "Days since the last corrective work order."),
            ColumnSpec("cm_count_90d", "DOUBLE", "Corrective work-order count over the trailing 90 days."),
            ColumnSpec("equipment_class_code", "INT", "Static class code."),
            ColumnSpec("asset_age_years", "DOUBLE", "Static asset age feature."),
            ColumnSpec("fail_next_7d", "DOUBLE", "Binary label for a corrective work order in the next 7 UTC days."),
            ColumnSpec("split", "STRING", "Purged split assignment."),
        ),
    ),
    TableSpec(
        schema_name="ml",
        table_name="failure_risk_score",
        source_name="ml_failure_risk_score.csv",
        business_purpose="Frozen failure-risk scores loaded for Part 4 so agent answers stay stable.",
        columns=(
            ColumnSpec("score_date", "DATE", "Scoring date."),
            ColumnSpec("erp_asset_id", "STRING", "Resolved asset identifier."),
            ColumnSpec("site_code", "STRING", "ERP site for the asset."),
            ColumnSpec("equipment_class", "STRING", "Equipment family."),
            ColumnSpec("risk_score", "DOUBLE", "Frozen probability-like risk score."),
            ColumnSpec("risk_band", "STRING", "Low, Medium, or High using frozen thresholds."),
            ColumnSpec("risk_rank", "INT", "Descending rank on the score date."),
            ColumnSpec("top_drivers", "STRING", "Semicolon-joined heuristic driver codes."),
            ColumnSpec("model_version", "STRING", "Frozen model version label."),
        ),
    ),
    TableSpec(
        schema_name="ml",
        table_name="drift_report",
        source_name="drift_report.csv",
        business_purpose="Feature-drift PSI summary used in the monitoring discussion.",
        columns=(
            ColumnSpec("equipment_class", "STRING", "Equipment family."),
            ColumnSpec("sensor", "STRING", "Sensor name."),
            ColumnSpec("psi", "DOUBLE", "Population stability index."),
            ColumnSpec("ref_mean", "DOUBLE", "Reference mean."),
            ColumnSpec("new_mean", "DOUBLE", "New-batch mean."),
            ColumnSpec("ref_rows", "INT", "Reference RUN-reading count."),
            ColumnSpec("new_rows", "INT", "New-batch RUN-reading count."),
            ColumnSpec("status", "STRING", "stable, moderate, or major."),
        ),
    ),
)


def connect_duckdb() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(database=":memory:")


def register_reference_views(connection: duckdb.DuckDBPyConnection) -> duckdb.DuckDBPyConnection:
    connection.execute("CREATE SCHEMA IF NOT EXISTS gold")
    connection.execute("CREATE SCHEMA IF NOT EXISTS ml")
    for spec in TABLE_SPECS:
        path = as_duckdb_path(spec.source_path)
        connection.execute(
            f"CREATE OR REPLACE VIEW {spec.fq_name} AS SELECT * FROM read_csv_auto('{path}', header=true)"
        )
        connection.execute(
            f"CREATE OR REPLACE VIEW {spec.table_name} AS SELECT * FROM {spec.fq_name}"
        )
    return connection


def create_local_session() -> duckdb.DuckDBPyConnection:
    return register_reference_views(connect_duckdb())


def read_table_rows(table_name: str, limit: int = 5) -> list[dict[str, Any]]:
    connection = create_local_session()
    try:
        rows = connection.execute(f"SELECT * FROM {table_name} LIMIT {limit}").fetchdf()
    finally:
        connection.close()
    return rows.to_dict(orient="records")


def read_csv_header(source_name: str) -> list[str]:
    path = REFERENCE_OUT_DIR / source_name
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", newline="") as handle:
        return next(csv.reader(handle))


def dataframe_for_table(table_name: str) -> pd.DataFrame:
    spec = next(spec for spec in TABLE_SPECS if spec.table_name == table_name)
    path = spec.source_path
    if path.suffix == ".gz":
        return pd.read_csv(path, compression="gzip")
    return pd.read_csv(path)


def expected_row_count(table_name: str) -> int:
    if table_name in GROUND_TRUTH["gold_row_counts"]:
        return int(GROUND_TRUTH["gold_row_counts"][table_name])
    prefixed_name = f"ml_{table_name}"
    if prefixed_name in GROUND_TRUTH["gold_row_counts"]:
        return int(GROUND_TRUTH["gold_row_counts"][prefixed_name])
    if table_name == "drift_report":
        return int(GROUND_TRUTH["drift"]["combinations"])
    raise KeyError(table_name)


def iter_table_specs(schema_name: str | None = None) -> Iterable[TableSpec]:
    for spec in TABLE_SPECS:
        if schema_name is None or spec.schema_name == schema_name:
            yield spec


def get_table_spec(table_name: str) -> TableSpec:
    return next(spec for spec in TABLE_SPECS if spec.table_name == table_name)


def row_count_map() -> dict[str, int]:
    counts = {spec.table_name: expected_row_count(spec.table_name) for spec in TABLE_SPECS}
    counts["drift_report"] = expected_row_count("drift_report")
    return counts
