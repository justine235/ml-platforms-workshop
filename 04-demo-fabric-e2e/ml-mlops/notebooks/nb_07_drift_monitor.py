# %% [markdown]
# # nb_07_drift_monitor
#
# **What to say before you run this notebook:** labels for October do not exist yet, so we cannot talk about accuracy drift.
# We can still monitor input drift.
# The notebook compares September RUN readings with a new October batch and exits machine-readable JSON so a pipeline can branch.

# %%
# Parameters
PARAMS = {
    "telemetry_table": "silver.telemetry",
    "new_telemetry_table": "silver.telemetry_drift",
    "asset_table": "gold.dim_asset",
    "output_table": "ml.drift_report",
    "reference_start": "2026-09-01",
    "reference_report_name": "drift_report",
    "emit_notebook_exit": True,
}

# %%
# Adapter
try:
    notebookutils  # noqa: B018 -- existence probe, not a useless expression
    IN_FABRIC = True
except NameError:
    IN_FABRIC = False

try:
    NOTEBOOKUTILS_OBJ = notebookutils
except NameError:
    NOTEBOOKUTILS_OBJ = None

import json

from notebooks.notebook_common import compare_frames_with_tolerance, default_context, get_env_setting, major_shift_summary
from notebooks.shared.fleet_ml_core import psi_table
from notebooks.shared.fleet_reference_pipeline import to_day

# %% [markdown]
# **What to say before the PSI table:** four major shifts are injected on purpose.
# Moderate engine-temperature drift on Paver, Compactor, and MobileCrane is expected seasonal cooling.
# The teaching point is that not every alert means a broken process.

# %%
def run(params: dict | None = None, context=None) -> dict:
    params = {**PARAMS, **(params or {})}
    context = context or default_context(globals())

    # psi_table() (notebooks/shared/fleet_ml_core.py) hardcodes 0.10/0.25 and is shared
    # across several demo folders, so its signature is not changed here. Instead this
    # notebook re-derives the status column with thresholds that MAY come from the
    # fleet_mlops Variable Library -- only these two values are read from it; everything
    # else the library stores (experiment/model/table names, IDs) is not consumed by code.
    moderate_threshold, moderate_source = get_env_setting(
        "driftModerateThreshold", 0.10, notebookutils_obj=NOTEBOOKUTILS_OBJ
    )
    major_threshold, major_source = get_env_setting(
        "driftMajorThreshold", 0.25, notebookutils_obj=NOTEBOOKUTILS_OBJ
    )
    thresholds_source = "variable library" if moderate_source == "variable library" and major_source == "variable library" else "default"
    print("thresholds source: %s" % thresholds_source)

    telemetry = context.read_table(params["telemetry_table"])
    new_batch = context.read_table(params["new_telemetry_table"])
    dim_asset = context.read_table(params["asset_table"])[["erp_asset_id", "equipment_class"]].drop_duplicates()

    reference = telemetry[(telemetry["is_run"]) & (telemetry["erp_asset_id"].notna()) & (telemetry["day"] >= to_day(params["reference_start"]))].copy()
    current = new_batch[(new_batch["is_run"]) & (new_batch["erp_asset_id"].notna())].copy()
    reference = reference.merge(dim_asset, on="erp_asset_id", how="left")
    current = current.merge(dim_asset, on="erp_asset_id", how="left")
    report = psi_table(reference, current)
    report["status"] = report["psi"].apply(
        lambda v: "major" if v > major_threshold else ("moderate" if v > moderate_threshold else "stable")
    )
    report = report.sort_values(["equipment_class", "sensor"], kind="stable").reset_index(drop=True)
    context.write_table(params["output_table"], report)

    major, expected_moderate = major_shift_summary(report)
    summary = {
        "status": "alert" if major else "ok",
        "major_shift_count": int((report["status"] == "major").sum()),
        "moderate_shift_count": int((report["status"] == "moderate").sum()),
        "major_shifts": major,
        "expected_moderate_shifts": expected_moderate,
    }

    # Unconditional in earlier drafts: a real Fabric workspace has no reference_out
    # files, so this used to raise FileNotFoundError on the very first live run.
    if context.has_reference(params["reference_report_name"]):
        reference_report = context.read_reference(params["reference_report_name"])
        summary["reference_comparison"] = compare_frames_with_tolerance(
            report,
            reference_report,
            key_cols=["equipment_class", "sensor"],
            numeric_cols=["psi", "ref_mean", "new_mean", "ref_rows", "new_rows"],
            tolerance=1e-6,
        )
    else:
        summary["reference_comparison"] = {"skipped": "no reference files in this workspace"}

    if params["emit_notebook_exit"]:
        context.notebook_exit(summary)
    return summary


# %%
if __name__ == "__main__":
    RESULT = run()
    print(json.dumps(RESULT, indent=2, sort_keys=True))
