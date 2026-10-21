# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************

import os
import sys

IN_FABRIC = "notebookutils" in globals()
if IN_FABRIC:
    CODE_DIR = os.environ.get("FLEET_CODE_DIR", "/lakehouse/default/Files/code")
    if CODE_DIR not in sys.path:
        sys.path.insert(0, CODE_DIR)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# # nb_04_features
#
# **What to say before you run this notebook:** we already trust the medallion outputs from the ETL half.
# This notebook turns those reconciled daily tables into one ML feature row per asset-day, with the exact split contract used everywhere else in the workshop.
# The point is not fancy feature engineering. The point is showing a reproducible, governed hand-off from data engineering to machine learning.
#

# CELL ********************

# Parameters
PARAMS = {
    "telemetry_table": "silver.telemetry",
    "daily_table": "gold.fact_telemetry_daily",
    "work_order_table": "gold.fact_work_order",
    "asset_table": "gold.dim_asset",
    "fault_catalog_table": "bronze.fault_code_catalog",
    "output_table": "ml.asset_day_features",
    "reference_features_name": "ml_asset_day_features",
    "validate_against_reference": True,
}

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Adapter
try:
    notebookutils  # noqa: B018 -- existence probe, not a useless expression
    IN_FABRIC = True
except NameError:
    IN_FABRIC = False

import json

import pandas as pd

from notebooks.notebook_common import compare_frames_with_tolerance, compute_split_counts, default_context, next_day_cutoff_epoch
from notebooks.shared.fleet_ml_core import FEATURES
from notebooks.shared.fleet_reference_pipeline import build_features, fault_occurrences

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# **What to say before this section:** the feature logic is intentionally the same as the laptop reference pipeline.
# We are not forking logic between platforms. We are swapping the storage engine, not the business rules.
#

# CELL ********************

EPOCH_DAY_ZERO = pd.Timestamp("1970-01-01")


def _normalize_daily_frame(daily: pd.DataFrame) -> pd.DataFrame:
    normalized = daily.copy()
    if "day" not in normalized.columns:
        normalized["day"] = (pd.to_datetime(normalized["obs_date"]) - EPOCH_DAY_ZERO).dt.days.astype("int64")
    if "is_after_retirement" not in normalized.columns:
        normalized["is_after_retirement"] = False
    return normalized


def _normalize_work_orders(work_orders: pd.DataFrame) -> pd.DataFrame:
    normalized = work_orders.copy()
    if "opened_fix" not in normalized.columns and "opened_utc" in normalized.columns:
        normalized["opened_fix"] = pd.to_datetime(normalized["opened_utc"], utc=True).astype("int64") // 1_000_000_000
    return normalized


def _normalize_dim_asset(dim_asset: pd.DataFrame) -> pd.DataFrame:
    normalized = dim_asset.copy()
    if "acq_day" not in normalized.columns:
        normalized["acq_day"] = (pd.to_datetime(normalized["acquisition_date"]) - EPOCH_DAY_ZERO).dt.days.astype("int64")
    return normalized


def run(params: dict | None = None, context=None) -> dict:
    params = {**PARAMS, **(params or {})}
    context = context or default_context(globals())

    telemetry = context.read_table(params["telemetry_table"])
    daily = _normalize_daily_frame(context.read_table(params["daily_table"]))
    work_orders = _normalize_work_orders(context.read_table(params["work_order_table"]))
    dim_asset = _normalize_dim_asset(context.read_table(params["asset_table"]))
    fault_catalog = context.read_table(params["fault_catalog_table"])

    cutoff_epoch = next_day_cutoff_epoch(daily["obs_date"])
    occurrences = fault_occurrences(telemetry, fault_catalog)
    features = build_features(daily, work_orders, dim_asset, occurrences, cutoff_epoch)
    features[FEATURES] = features[FEATURES].round(4)

    context.write_table(params["output_table"], features)

    summary = {
        "rows": int(len(features)),
        "labelled_rows": int(features["fail_next_7d"].notna().sum()),
        "positive_rate_labelled": round(float(features.loc[features["fail_next_7d"].notna(), "fail_next_7d"].mean()), 4),
        "split_counts": compute_split_counts(features),
    }

    if params["validate_against_reference"]:
        # A real Fabric workspace normally has no reference_out files at all (they
        # are a local-validation fixture); skip the comparison cleanly instead of
        # raising FileNotFoundError.
        if context.has_reference(params["reference_features_name"]):
            reference = context.read_reference(params["reference_features_name"])
            summary["reference_comparison"] = compare_frames_with_tolerance(
                features,
                reference,
                key_cols=["erp_asset_id", "obs_date", "split"],
                numeric_cols=[*FEATURES, "fail_next_7d"],
                tolerance=1e-6,
            )
        else:
            summary["reference_comparison"] = {"skipped": "no reference files in this workspace"}

    return summary

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# **What to say after the write:** the acceptance check is deliberately boring.
# We want 50,876 rows, 49,028 labelled rows, a 5.47% positive rate, and the split counts from the contract.
# If those move, the model notebook is no longer teaching the same demo.
#

# CELL ********************

if __name__ == "__main__":
    RESULT = run()
    print(json.dumps(RESULT, indent=2, sort_keys=True))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
